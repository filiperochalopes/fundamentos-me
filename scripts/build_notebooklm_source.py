#!/usr/bin/env python3
"""Combine every lesson PDF or provisional TMP.md into one NotebookLM source."""

from __future__ import annotations

import argparse
import re
from html import escape
from pathlib import Path

import reportlab
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


THEME = colors.HexColor("#637A32")
TEXT = colors.HexColor("#272727")
HEADER_RE = re.compile(r"Fundamentos\s*\|\s*Li[cç][aã]o\s*\d+", re.I)
PAGE_RE = re.compile(r"^p[aá]g\s*\d+\s*$", re.I)
LESSON_RE = re.compile(r"^LI[CÇ][AÃ]O\s*\d+\s*$", re.I)
SECTION_RE = re.compile(r"^(?:\d+[.)]|[a-z][.)])\s+", re.I)
REFERENCE_RE = re.compile(
    r"^(?:(?:[1-3]\s*)?[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wáéíóúâêôãõç.]*"
    r"(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç.]+){0,3})\s+"
    r"\d{1,3}:\d{1,3}(?:\s*[-,;]\s*\d{1,3})*(?:\s*[-–]\s*\d{1,3}:\d{1,3})?$"
)
MARKDOWN_HEADING = "\x1e"


def register_fonts() -> None:
    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    pdfmetrics.registerFont(TTFont("Vera", font_dir / "Vera.ttf"))
    pdfmetrics.registerFont(TTFont("Vera-Bold", font_dir / "VeraBd.ttf"))
    pdfmetrics.registerFont(TTFont("Vera-Italic", font_dir / "VeraIt.ttf"))


def lesson_sources(root: Path) -> list[Path]:
    """Return one canonical source per lesson, preferring PDF over TMP.md."""
    sources: list[Path] = []
    for lesson_dir in root.glob("*/*"):
        if not lesson_dir.is_dir():
            continue
        if not lesson_dir.parent.name[:1].isdigit() or not lesson_dir.name[:1].isdigit():
            continue
        pdfs = sorted(lesson_dir.glob("*.pdf"))
        temporary = lesson_dir / "TMP.md"
        if pdfs:
            sources.append(pdfs[0])
        elif temporary.is_file():
            sources.append(temporary)
    return sorted(sources, key=lambda path: lesson_number(path.parent.name))


def lesson_number(value: str) -> int:
    match = re.match(r"(\d+)", value)
    return int(match.group(1)) if match else 10**9


def strip_number(value: str) -> str:
    return re.sub(r"^\d+\s*-\s*", "", value).strip()


def clean_lines(text: str, lesson_title: str) -> list[str]:
    lines: list[str] = []
    normalized_title = re.sub(r"\s+", " ", lesson_title).casefold()
    for raw in text.replace("\u00ad", "").splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        line = re.sub(r"^(?:p[aá]g\s*\d+)\s*", "", line, flags=re.I)
        if not line:
            lines.append("")
            continue
        if HEADER_RE.search(line) or PAGE_RE.match(line) or LESSON_RE.match(line):
            continue
        if line.casefold() == normalized_title:
            continue
        lines.append(line)
    return lines


def paragraphs_from_pdf(path: Path, lesson_title: str) -> list[str]:
    paragraphs: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        if not buffer:
            return
        value = buffer[0]
        for line in buffer[1:]:
            if value.endswith("-") and line[:1].islower():
                value = value[:-1] + line
            else:
                value += " " + line
        value = re.sub(r"\s+", " ", value).strip()
        if value:
            paragraphs.append(value)
        buffer.clear()

    reader = PdfReader(path)
    for page in reader.pages:
        text = page.extract_text(extraction_mode="layout") or ""
        for line in clean_lines(text, lesson_title):
            if not line:
                flush()
            else:
                buffer.append(line)
        flush()
    return paragraphs


def paragraphs_from_markdown(path: Path, lesson_title: str) -> list[str]:
    """Read the simplified Markdown source while retaining its section headings."""
    paragraphs: list[str] = []
    buffer: list[str] = []
    normalized_title = re.sub(r"\s+", " ", lesson_title).casefold()

    def flush() -> None:
        value = re.sub(r"\s+", " ", " ".join(buffer)).strip()
        if value:
            paragraphs.append(value)
        buffer.clear()

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if line.startswith("# "):
            heading = re.sub(r"^#\s+", "", line).strip()
            if re.sub(r"^Li[cç][aã]o\s+\d+\s*[-–—:]\s*", "", heading, flags=re.I).casefold() == normalized_title:
                continue
            flush()
            paragraphs.append(heading)
            continue
        if line.startswith("##"):
            flush()
            heading = re.sub(r"^#{2,6}\s+", "", line).strip()
            paragraphs.append(MARKDOWN_HEADING + heading)
            continue
        line = re.sub(r"^>\s*", "", line)
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"`([^`]*)`", r"\1", line)
        if re.match(r"^[-*+]\s+", line):
            flush()
            paragraphs.append(re.sub(r"^[-*+]\s+", "• ", line))
            continue
        if re.match(r"^\d+[.)]\s+", line):
            flush()
            paragraphs.append(line)
            continue
        buffer.append(line)
    flush()
    return paragraphs


def is_heading(text: str) -> bool:
    if text.startswith(MARKDOWN_HEADING):
        return True
    if len(text) > 110 or text.endswith(('.', '?', '!', ';', ':')):
        return False
    return (
        text.casefold() in {"introdução", "conclusão", "considerações finais"}
        or bool(SECTION_RE.match(text))
        or (text.isupper() and len(text.split()) <= 12)
    )


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "LessonTitle",
            parent=base["Heading1"],
            fontName="Vera-Bold",
            fontSize=18,
            leading=22,
            textColor=THEME,
            spaceAfter=5 * mm,
        ),
        "cycle": ParagraphStyle(
            "Cycle",
            parent=base["Normal"],
            fontName="Vera-Bold",
            fontSize=9,
            leading=12,
            textColor=THEME,
            spaceAfter=2 * mm,
            textTransform="uppercase",
        ),
        "heading": ParagraphStyle(
            "ContentHeading",
            parent=base["Heading2"],
            fontName="Vera-Bold",
            fontSize=12,
            leading=15,
            textColor=THEME,
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Vera",
            fontSize=9.5,
            leading=13.5,
            textColor=TEXT,
            spaceAfter=2.2 * mm,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Vera-Italic",
            fontSize=9.3,
            leading=13.2,
            textColor=TEXT,
            leftIndent=3 * mm,
            rightIndent=2 * mm,
            spaceAfter=1.5 * mm,
        ),
        "reference": ParagraphStyle(
            "Reference",
            parent=base["BodyText"],
            fontName="Vera-Bold",
            fontSize=8.5,
            leading=11,
            textColor=THEME,
            leftIndent=3 * mm,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontName="Vera",
            fontSize=7.5,
            textColor=colors.HexColor("#687064"),
            alignment=TA_CENTER,
        ),
    }


def quote_block(text: str, reference: str, style: dict[str, ParagraphStyle]) -> Table:
    content = [
        Paragraph(escape(text), style["quote"]),
        Paragraph(escape(reference), style["reference"]),
    ]
    table = Table([["", content]], colWidths=[1.5 * mm, 160 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), THEME),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 0),
                ("TOPPADDING", (0, 0), (0, 0), 0),
                ("BOTTOMPADDING", (0, 0), (0, 0), 0),
                ("LEFTPADDING", (1, 0), (1, 0), 3 * mm),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
                ("TOPPADDING", (1, 0), (1, 0), 1.5 * mm),
                ("BOTTOMPADDING", (1, 0), (1, 0), 1.5 * mm),
            ]
        )
    )
    return table


def page_footer(canvas, doc) -> None:  # reportlab callback signature
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#C6CEB8"))
    canvas.setLineWidth(0.5)
    canvas.line(25 * mm, 13 * mm, A4[0] - 25 * mm, 13 * mm)
    canvas.setFont("Vera", 7.5)
    canvas.setFillColor(colors.HexColor("#687064"))
    canvas.drawCentredString(A4[0] / 2, 8.5 * mm, f"Fundamentos - NotebookLM | {doc.page}")
    canvas.restoreState()


def build(root: Path, output: Path) -> None:
    register_fonts()
    sources = lesson_sources(root)
    if not sources:
        raise SystemExit(f"Nenhum PDF ou TMP.md de aula encontrado em {root}")

    style = styles()
    frame = Frame(22 * mm, 18 * mm, A4[0] - 44 * mm, A4[1] - 36 * mm, id="content")
    document = BaseDocTemplate(
        str(output),
        pagesize=A4,
        title="Fundamentos - Fonte consolidada para NotebookLM",
        author="Fundamentos",
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    document.addPageTemplates(PageTemplate(id="lesson", frames=[frame], onPage=page_footer))
    story = []

    for index, path in enumerate(sources):
        cycle_number = lesson_number(path.parent.parent.name)
        lesson_no = lesson_number(path.parent.name)
        cycle_title = strip_number(path.parent.parent.name)
        lesson_title = strip_number(path.parent.name)
        if index:
            story.append(PageBreak())
        story.extend(
            [
                Paragraph(f"Ciclo {cycle_number} - {escape(cycle_title)}", style["cycle"]),
                Paragraph(f"Lição {lesson_no} - {escape(lesson_title)}", style["title"]),
                Table(
                    [[""]],
                    colWidths=[166 * mm],
                    rowHeights=[0.7 * mm],
                    style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), THEME)]),
                ),
                Spacer(1, 5 * mm),
            ]
        )

        paragraphs = (
            paragraphs_from_pdf(path, lesson_title)
            if path.suffix.casefold() == ".pdf"
            else paragraphs_from_markdown(path, lesson_title)
        )
        i = 0
        while i < len(paragraphs):
            text = paragraphs[i]
            if i + 1 < len(paragraphs) and REFERENCE_RE.match(paragraphs[i + 1]):
                story.append(quote_block(text, paragraphs[i + 1], style))
                story.append(Spacer(1, 2 * mm))
                i += 2
                continue
            display_text = text.removeprefix(MARKDOWN_HEADING)
            story.append(
                Paragraph(
                    escape(display_text),
                    style["heading"] if is_heading(text) else style["body"],
                )
            )
            i += 1

        source_label = "PDF" if path.suffix.casefold() == ".pdf" else "TMP"
        print(f"[{index + 1:03d}/{len(sources):03d}] {path.parent.name} [{source_label}]")

    output.parent.mkdir(parents=True, exist_ok=True)
    document.build(story)
    print(f"PDF criado: {output}")
    print(f"Aulas incluídas: {len(sources)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("NotebookLMSource.pdf"))
    args = parser.parse_args()
    build(args.root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
