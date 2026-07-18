#!/usr/bin/env python3
"""Download a YouTube lesson as M4A and transcribe it with MLX Whisper."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_YTDLP = Path(
    "/Users/filipelopes/Desktop/Development/youtube-downloader-mcp-server/.venv/bin/yt-dlp"
)
DEFAULT_MODEL = "mlx-community/whisper-large-v3-mlx"


def executable(explicit: Path | None, name: str, fallback: Path | None = None) -> str:
    if explicit:
        if not explicit.is_file():
            raise SystemExit(f"Executável não encontrado: {explicit}")
        return str(explicit)
    discovered = shutil.which(name)
    if discovered:
        return discovered
    if fallback and fallback.is_file():
        return str(fallback)
    raise SystemExit(f"Executável não encontrado: {name}")


def video_id(source: str) -> str:
    if "/" not in source and "?" not in source:
        return source
    parsed = urlparse(source)
    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        return parsed.path.strip("/").split("/")[0]
    value = parse_qs(parsed.query).get("v", [])
    if value:
        return value[0]
    raise SystemExit("Não foi possível extrair o ID do vídeo da URL")


def run(command: list[str], dry_run: bool) -> None:
    print(" ".join(command))
    if not dry_run:
        subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="URL pública do YouTube ou ID do vídeo")
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/fundamentos-youtube-ingest"))
    parser.add_argument("--yt-dlp", type=Path)
    parser.add_argument("--node", type=Path)
    parser.add_argument("--mlx-whisper", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--language", default="pt")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-transcription", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    identifier = video_id(args.source)
    url = f"https://www.youtube.com/watch?v={identifier}"
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    audio = output_dir / f"{identifier}.m4a"

    if not args.skip_download:
        ytdlp = executable(args.yt_dlp, "yt-dlp", DEFAULT_YTDLP)
        node = executable(args.node, "node")
        run(
            [
                ytdlp,
                "--js-runtimes",
                f"node:{node}",
                "--extractor-args",
                "youtube:player_client=android",
                "--extract-audio",
                "--audio-format",
                "m4a",
                "--audio-quality",
                "0",
                "--no-overwrites",
                "--no-playlist",
                "--output",
                str(output_dir / "%(id)s.%(ext)s"),
                url,
            ],
            args.dry_run,
        )

    if not args.dry_run and not audio.is_file():
        raise SystemExit(f"Áudio esperado não encontrado: {audio}")

    if not args.skip_transcription:
        whisper = executable(args.mlx_whisper, "mlx_whisper")
        run(
            [
                whisper,
                str(audio),
                "--model",
                args.model,
                "--language",
                args.language,
                "--condition-on-previous-text",
                "False",
                "--word-timestamps",
                "True",
                "--hallucination-silence-threshold",
                "2",
                "--output-dir",
                str(output_dir),
                "--output-name",
                identifier,
                "--output-format",
                "txt",
                "--verbose",
                "False",
            ],
            args.dry_run,
        )

    print(f"Áudio: {audio}")
    print(f"Transcrição: {output_dir / f'{identifier}.txt'}")


if __name__ == "__main__":
    main()
