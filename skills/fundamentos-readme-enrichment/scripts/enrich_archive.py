#!/usr/bin/env python3
"""Enrich every Fundamentos lesson README from its local transcript PDF."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

from extract_lesson import REFERENCE_RE, extract_pages, normalize_reference, reading_link


HEADER_RE = re.compile(
    r"^(?:pág\s*\d+|fundamentos\s*\|.*|lição\s*\d+|por\s+.+)$", re.I
)
SECTION_RE = re.compile(
    r"^(?:(?:\d+[.)]|[a-z][.)])\s+.+|(?:primeir[ao]|segund[ao]|terceir[ao]|"
    r"quart[ao]|quint[ao]|sext[ao]|sétim[ao]|oitav[ao]|non[ao]|décim[ao])\s+"
    r"(?:e\s+(?:maior|última)\s+)?(?:evidência|aspecto|razão|princípio|parte|passo).+|introdução|conclusão|"
    r"considerações finais)$", re.I
)
SECTION_START_RE = re.compile(
    r"^(?:\d+[.)]\s+|(?:primeir[ao]|segund[ao]|terceir[ao]|quart[ao]|quint[ao]|"
    r"sext[ao]|sétim[ao]|oitav[ao]|non[ao]|décim[ao])\s+(?:e\s+(?:maior|última)\s+)?"
    r"(?:evidência|aspecto|razão|princípio|parte|passo)|introdução$|conclusão$|"
    r"considerações finais$)", re.I
)


def normalize_text(text: str) -> str:
    text = text.replace("\u00ad", "").replace("–", "-").replace("—", "-")
    text = re.sub(r"(?<=\w)\s*-\s*\n\s*(?=\w)", "", text)
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        line = re.sub(r"^pág\s*\d+", "", line, flags=re.I).strip()
        if not line or HEADER_RE.match(line):
            continue
        lines.append(line)
    return "\n".join(lines)


def summary_from_text(text: str, title: str) -> str:
    lines = [line for line in text.splitlines() if line.casefold() != title.casefold()]
    prose = " ".join(lines)
    prose = re.sub(r"\s+", " ", prose).strip()
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", prose)
    selected: list[str] = []
    cursor = 0
    for sentence in sentences:
        sentence = sentence.strip(" -\t")
        sentence = re.split(r"(?<=[.!?])\s+(?=[a-záéíóúâêôãõç])", sentence, maxsplit=1)[0]
        position = prose.find(sentence, cursor)
        cursor = max(cursor, position + len(sentence))
        words = sentence.split()
        if not 9 <= len(words) <= 55:
            continue
        lowered = sentence.casefold()
        if any(marker in lowered for marker in (
            "pág ", "clique", "youtube", "simply.fly", "programa de ensino",
            "plataformas e mídias", "para cada lição", "todas as lições e mídias",
            "introdução ",
        )):
            continue
        if (
            sentence.casefold().startswith(title.casefold())
            or sentence.endswith("?")
            or not re.match(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ]", sentence)
            or lowered.startswith(("com isso,", "e sim ", "porque um ", "ide, "))
        ):
            continue
        if sentence.count(":") or sentence.count(";") or "“" in sentence or "”" in sentence or '"' in sentence:
            continue
        following = prose[position + len(sentence):position + len(sentence) + 50] if position >= 0 else ""
        if REFERENCE_RE.search(following):
            continue
        sentence = REFERENCE_RE.sub("", sentence)
        sentence = re.sub(r"\(\s*\)", "", sentence)
        sentence = re.sub(r"\s+", " ", sentence).strip()
        selected.append(sentence)
        if len(selected) == 4:
            break
    if len(selected) < 3:
        chunks = [line for line in lines if 10 <= len(line.split()) <= 55]
        for chunk in chunks:
            if chunk not in selected:
                selected.append(chunk.rstrip(".") + ".")
            if len(selected) == 3:
                break
    summary = " ".join(selected[:4])
    summary = re.sub(r"\s+", " ", summary).strip()
    if summary and summary[-1] not in ".!?":
        summary += "."
    return summary


def clean_heading(line: str) -> str:
    heading = re.sub(r"^(?:\d+[.)]|[a-z][.)])\s*", "", line).strip()
    heading = heading.rstrip(":. ")
    if heading.casefold() == "introdução":
        return "Textos introdutórios e fundamento da lição"
    if heading.casefold() in {"conclusão", "considerações finais"}:
        return "Conclusão e aplicação"
    return heading[0].upper() + heading[1:] if heading else "Textos bíblicos abordados"


def themed_references(text: str) -> list[tuple[str, list[str]]]:
    events: list[tuple[int, str]] = []
    raw_lines = text.splitlines(keepends=True)
    offsets: list[int] = []
    offset = 0
    for line in raw_lines:
        offsets.append(offset)
        offset += len(line)
    index = 0
    while index < len(raw_lines):
        stripped = raw_lines[index].strip()
        if SECTION_START_RE.match(stripped):
            parts = [stripped]
            lookahead = index + 1
            can_wrap = len(stripped.split()) >= 6 and bool(
                re.match(r"^(?:\d+[.)])", stripped)
                or re.search(r"\b(?:a|ao|à|as|aos|de|do|da|dos|das|e|que)$", stripped, re.I)
            ) and stripped.casefold() not in {"introdução", "conclusão", "considerações finais"}
            while can_wrap and lookahead < len(raw_lines) and len(parts) < 3:
                candidate = raw_lines[lookahead].strip()
                if not candidate or REFERENCE_RE.search(candidate) or SECTION_START_RE.match(candidate):
                    break
                if len(" ".join(parts + [candidate])) > 110:
                    break
                if len(candidate) > 70 or candidate.endswith((".", "!", "?", ":")):
                    if len(candidate.split()) <= 14:
                        parts.append(candidate)
                    break
                if len(candidate.split()) <= 12:
                    parts.append(candidate)
                    lookahead += 1
                else:
                    break
            heading = " ".join(parts)
            if len(heading) <= 180:
                events.append((offsets[index], clean_heading(heading)))
        elif 2 <= len(stripped.split()) <= 12 and len(stripped) <= 100 and stripped.isupper():
            events.append((offsets[index], clean_heading(stripped)))
        index += 1

    groups: OrderedDict[str, list[str]] = OrderedDict()
    current = "Textos introdutórios e fundamento da lição"
    event_index = 0
    seen_by_group: dict[str, set[str]] = {}
    for match in REFERENCE_RE.finditer(text):
        while event_index < len(events) and events[event_index][0] <= match.start():
            current = events[event_index][1]
            event_index += 1
        if match.start() >= 2 and text[match.start() - 2].isdigit() and text[match.start() - 1].isspace():
            continue
        reference = normalize_reference(match.group("book"), match.group("body"))
        if re.search(r":\d{3,}$", reference):
            continue
        key = reference.casefold()
        seen = seen_by_group.setdefault(current, set())
        if key not in seen:
            groups.setdefault(current, []).append(reference)
            seen.add(key)

    populated = [(heading, refs) for heading, refs in groups.items() if refs]
    if len(populated) > 10:
        kept = populated[:9]
        overflow = [ref for _, refs in populated[9:] for ref in refs]
        kept.append(("Outros textos e aplicações", list(dict.fromkeys(overflow))))
        return kept
    return populated


def all_unique(groups: list[tuple[str, list[str]]]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for _, references in groups:
        for reference in references:
            key = reference.casefold()
            if key not in seen:
                seen.add(key)
                result.append(reference)
    return result


def enrichment_markdown(summary: str, groups: list[tuple[str, list[str]]]) -> str:
    lines = [summary, "", "## Referências e Textos Bíblicos", ""]
    for heading, references in groups:
        lines.extend([f"**👉🏼  {heading}**", " | ".join(references), ""])
    lines.append(f"[Link para leitura]({reading_link(all_unique(groups))})")
    return "\n".join(lines)


def replace_enrichment(readme: str, enrichment: str) -> str:
    lines = readme.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("README sem título H1")
    materials = next((i for i, line in enumerate(lines) if line == "## Materiais"), None)
    if materials is None:
        raise ValueError("README sem seção Materiais")
    suffix = "\n".join(lines[materials:]).rstrip() + "\n"
    return f"{lines[0]}\n\n{enrichment.rstrip()}\n\n{suffix}"


def process(root: Path, write: bool, report_path: Path) -> int:
    records = []
    failures = []
    for readme_path in sorted(root.glob("* - */* - */README.md")):
        pdfs = list(readme_path.parent.glob("*.pdf"))
        if len(pdfs) != 1:
            failures.append(f"{readme_path}: esperava 1 PDF, encontrou {len(pdfs)}")
            continue
        try:
            old = readme_path.read_text(encoding="utf-8")
            title = old.splitlines()[0].removeprefix("# ").split(" - ", 1)[-1]
            pages = extract_pages(pdfs[0])
            text = normalize_text("\n\n".join(pages))
            summary = summary_from_text(text, title)
            groups = themed_references(text)
            if not summary or len(summary.split()) < 25:
                raise ValueError("resumo curto ou vazio")
            if not groups or not all_unique(groups):
                raise ValueError("nenhuma referência encontrada")
            new = replace_enrichment(old, enrichment_markdown(summary, groups))
            if write:
                readme_path.write_text(new, encoding="utf-8")
            records.append({
                "readme": str(readme_path), "pdf": str(pdfs[0]),
                "summary": summary, "groups": groups,
                "reference_count": len(all_unique(groups)),
            })
        except Exception as exc:
            failures.append(f"{readme_path}: {exc}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps({"records": records, "failures": failures}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"processed={len(records)} failures={len(failures)} write={write}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--report", type=Path, default=Path("/tmp/fundamentos-enrichment-report.json"))
    args = parser.parse_args()
    raise SystemExit(process(args.root.resolve(), args.write, args.report))


if __name__ == "__main__":
    main()
