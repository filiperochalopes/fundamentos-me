#!/usr/bin/env python3
"""Archive a plain-text or YouTube JSON3 automatic transcription."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def source_text(path: Path) -> str:
    if path.suffix.casefold() != ".json3":
        return path.read_text(encoding="utf-8")

    payload = json.loads(path.read_text(encoding="utf-8"))
    fragments: list[str] = []
    for event in payload.get("events", []):
        value = "".join(
            segment.get("utf8", "")
            for segment in event.get("segs", [])
        ).strip()
        if value:
            fragments.append(value)
    return " ".join(fragments)


def paragraphs(text: str, target_length: int = 850) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9\[])",
        normalized,
    )

    result: list[str] = []
    buffer = ""
    for sentence in sentences:
        if buffer and len(buffer) + len(sentence) + 1 > target_length:
            result.append(buffer)
            buffer = sentence
        else:
            buffer = f"{buffer} {sentence}".strip()
    if buffer:
        result.append(buffer)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--youtube-url", required=True)
    parser.add_argument("--method", required=True)
    args = parser.parse_args()

    if not args.source.is_file():
        raise SystemExit(f"Fonte não encontrada: {args.source}")

    body = paragraphs(source_text(args.source))
    if not body:
        raise SystemExit(f"Transcrição vazia: {args.source}")

    header = [
        f"Título: {args.title}",
        f"Fonte: {args.youtube_url}",
        f"Método: {args.method}",
        "Aviso: transcrição automática; pode conter erros de reconhecimento.",
        "",
        "---",
        "",
    ]
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(
        "\n".join(header + ["\n\n".join(body)]) + "\n",
        encoding="utf-8",
    )
    print(f"Transcrição arquivada: {args.destination}")


if __name__ == "__main__":
    main()
