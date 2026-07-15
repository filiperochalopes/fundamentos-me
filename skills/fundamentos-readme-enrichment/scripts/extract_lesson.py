#!/usr/bin/env python3
"""Extract PDF text/reference candidates and build biblia.filipelopes.me links."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote_plus


ALIASES = {
    "gênesis": "Gn", "genesis": "Gn", "gn": "Gn", "êxodo": "Ex",
    "exodo": "Ex", "êx": "Ex", "ex": "Ex", "levítico": "Lv", "lv": "Lv",
    "números": "Nm", "nm": "Nm", "deuteronômio": "Dt", "dt": "Dt",
    "salmos": "Sl", "salmo": "Sl", "sl": "Sl", "isaías": "Is", "is": "Is",
    "mateus": "Mt", "mt": "Mt", "marcos": "Mc", "mc": "Mc", "lucas": "Lc",
    "lc": "Lc", "joão": "Jo", "jo": "Jo", "atos": "At", "at": "At",
    "romanos": "Rm", "rm": "Rm", "1 coríntios": "1Co", "1co": "1Co",
    "2 coríntios": "2Co", "2co": "2Co", "gálatas": "Gl", "gl": "Gl",
    "efésios": "Ef", "ef": "Ef", "filipenses": "Fp", "fp": "Fp",
    "colossenses": "Cl", "cl": "Cl", "1 tessalonicenses": "1Ts", "1ts": "1Ts",
    "2 tessalonicenses": "2Ts", "2ts": "2Ts", "1 timóteo": "1Tm", "1tm": "1Tm",
    "2 timóteo": "2Tm", "2tm": "2Tm", "tito": "Tt", "tt": "Tt",
    "hebreus": "Hb", "hb": "Hb", "tiago": "Tg", "tg": "Tg",
    "1 pedro": "1Pe", "1pe": "1Pe", "2 pedro": "2Pe", "2pe": "2Pe",
    "1 joão": "1Jo", "1jo": "1Jo", "2 joão": "2Jo", "2jo": "2Jo",
    "3 joão": "3Jo", "3jo": "3Jo", "judas": "Jd", "jd": "Jd",
    "apocalipse": "Ap", "ap": "Ap",
    "josué": "Js", "juízes": "Jz", "rute": "Rt", "1 samuel": "1Sm",
    "2 samuel": "2Sm", "1 reis": "1Rs", "2 reis": "2Rs", "1 crônicas": "1Cr",
    "2 crônicas": "2Cr", "esdras": "Ed", "neemias": "Ne", "ester": "Et",
    "jó": "Jó", "provérbios": "Pv", "eclesiastes": "Ec", "cantares": "Ct",
    "cântico dos cânticos": "Ct", "jeremias": "Jr", "lamentações": "Lm",
    "ezequiel": "Ez", "daniel": "Dn", "oseias": "Os", "joel": "Jl",
    "amós": "Am", "obadias": "Ob", "jonas": "Jn", "miqueias": "Mq",
    "naum": "Na", "habacuque": "Hc", "sofonias": "Sf", "ageu": "Ag",
    "zacarias": "Zc", "malaquias": "Ml", "filemom": "Fm",
}
# Abreviações menos frequentes que não precisam de aliases por extenso.
for abbreviation in (
    "Js", "Jz", "Rt", "1Sm", "2Sm", "1Rs", "2Rs", "1Cr", "2Cr", "Ed",
    "Ne", "Et", "Jó", "Pv", "Ec", "Ct", "Jr", "Lm", "Ez", "Dn", "Os",
    "Jl", "Am", "Ob", "Jn", "Mq", "Na", "Hc", "Sf", "Ag", "Zc", "Ml", "Fm",
):
    ALIASES.setdefault(abbreviation.casefold(), abbreviation)

BOOKS = "|".join(
    re.escape(alias).replace(r"\ ", r"\s*")
    for alias in sorted(ALIASES, key=len, reverse=True)
)
REFERENCE_RE = re.compile(
    rf"(?<![\w])(?P<book>{BOOKS})\.?\s+(?P<body>\d{{1,3}}\s*:\s*\d{{1,3}}(?:\s*[-–—]\s*\d{{1,3}})?(?:\s*,\s*\d{{1,3}}(?:\s*[-–—]\s*\d{{1,3}})?)*(?:\s*;\s*(?:\d{{1,3}}\s*:\s*)?\d{{1,3}}(?:\s*[-–—]\s*\d{{1,3}})?(?:\s*,\s*\d{{1,3}}(?:\s*[-–—]\s*\d{{1,3}})?)*)*)",
    re.IGNORECASE,
)


def normalize_reference(book: str, body: str) -> str:
    alias_key = re.sub(r"\s+", " ", book).strip().casefold()
    compact_key = alias_key.replace(" ", "")
    book = ALIASES.get(alias_key, ALIASES.get(compact_key, re.sub(r"\s+", "", book)))
    body = re.sub(r"\s*([:;,])\s*", r"\1", body)
    body = re.sub(r"\s*[-–—]\s*", "-", body)
    return f"{book} {body}"


def ordered_references(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in REFERENCE_RE.finditer(text):
        # Evitar que "João" seja capturado isoladamente dentro de "1 João".
        if match.start() >= 2 and text[match.start() - 2].isdigit() and text[match.start() - 1].isspace():
            continue
        value = normalize_reference(match.group("book"), match.group("body"))
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            found.append(value)
    return found


def reading_link(references: list[str]) -> str:
    query = ";".join(references)
    return "https://biblia.filipelopes.me/?q=" + quote_plus(query, safe="")


def extract_pages(pdf_path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit(
            "pypdf não está instalado; use o Python empacotado pelo Codex ou instale pypdf"
        ) from exc
    reader = PdfReader(str(pdf_path))
    return [(page.extract_text() or "").strip() for page in reader.pages]


def write_outputs(pdf_path: Path, output_dir: Path) -> None:
    pages = extract_pages(pdf_path)
    text = "\n\n".join(
        f"--- Página {number} ---\n{page}" for number, page in enumerate(pages, 1)
    )
    references = ordered_references(text)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf_path.stem
    (output_dir / f"{stem}.txt").write_text(text + "\n", encoding="utf-8")
    payload = {
        "pdf": str(pdf_path),
        "pages": len(pages),
        "references": references,
        "reading_link": reading_link(references),
    }
    (output_dir / f"{stem}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    draft = (
        "<Resumo editorial em um único parágrafo.>\n\n"
        "## Referências e Textos Bíblicos\n\n"
        "**👉🏼  <Tema extraído da lição>**\n"
        + " | ".join(references)
        + "\n\n"
        + f"[Link para leitura]({payload['reading_link']})\n"
    )
    (output_dir / f"{stem}.md").write_text(draft, encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="?", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/fundamentos-extract"))
    parser.add_argument("--link", nargs="+", metavar="REF")
    args = parser.parse_args()
    if args.link:
        print(reading_link(args.link))
        return
    if not args.pdf:
        parser.error("informe um PDF ou use --link REF [REF ...]")
    if not args.pdf.is_file():
        parser.error(f"PDF não encontrado: {args.pdf}")
    write_outputs(args.pdf, args.output_dir)


if __name__ == "__main__":
    main()
