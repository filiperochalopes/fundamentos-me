#!/usr/bin/env python3
"""Build the Fundamentos cycle/lesson archive and download transcript PDFs."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def safe_component(value: str) -> str:
    value = re.sub(r"[/:\\\x00]", " - ", value)
    value = re.sub(r"\s+", " ", value).strip().rstrip(".")
    return value or "Sem título"


def migrate_legacy_directory(legacy: Path, desired: Path) -> None:
    if not legacy.exists() or legacy == desired:
        return
    if desired.exists():
        raise FileExistsError(
            f"cannot migrate {legacy}: destination already exists: {desired}"
        )
    legacy.rename(desired)


def markdown_link(label: str, url: str | None) -> str | None:
    return f"[{label}]({url})" if url else None


def preserved_enrichment(existing_readme: str | None) -> str | None:
    if not existing_readme or "## Referências e Textos Bíblicos" not in existing_readme:
        return None
    lines = existing_readme.splitlines()
    materials = next((i for i, line in enumerate(lines) if line == "## Materiais"), None)
    if materials is None:
        return None
    content = "\n".join(lines[1:materials]).strip()
    return content or None


def lesson_readme(lesson: dict, pdf_name: str, existing_readme: str | None = None) -> str:
    number = lesson["number"]
    title = lesson["title"]
    links = lesson["links"]
    video = links["video"]
    lines = [f"# {number} - {title}", ""]
    enrichment = preserved_enrichment(existing_readme)
    if enrichment:
        lines.extend([enrichment, ""])
    lines.extend(["## Materiais", ""])

    video_items = [
        ("Vídeo principal", video.get("primary")),
        ("YouTube — versão resumida", video.get("youtube_summary")),
        ("Vídeo completo", video.get("full_video")),
        ("Transmissão original", video.get("original_live")),
        ("Vídeo em Libras", video.get("sign_language")),
    ]
    for label, url in video_items:
        link = markdown_link("abrir", url)
        if link:
            lines.append(f"- {label}: {link}")

    pdf_url = links.get("transcript_pdf")
    if pdf_url:
        lines.append(
            f"- Transcrição (PDF): [arquivo local](<{pdf_name}>) · "
            f"[link original]({pdf_url})"
        )

    podcasts = links.get("podcasts", [])
    if podcasts:
        lines.extend(["", "## Podcasts", ""])
        for podcast in podcasts:
            variants = []
            if podcast.get("summary"):
                variants.append(markdown_link("resumo", podcast["summary"]))
            if podcast.get("full"):
                variants.append(markdown_link("completo", podcast["full"]))
            lines.append(f"- {podcast['platform']}: " + " · ".join(variants))

    return "\n".join(lines) + "\n"


def is_pdf(path: Path) -> bool:
    try:
        if path.stat().st_size <= 4:
            return False
        with path.open("rb") as stream:
            return stream.read(5) == b"%PDF-"
    except OSError:
        return False


def download_pdf(url: str, destination: Path, attempts: int = 3) -> str:
    if is_pdf(destination):
        return "existing"

    temporary = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Codex-Fundamentos-Archive/1.0"},
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                temporary.write_bytes(response.read())
            if not is_pdf(temporary):
                raise ValueError("downloaded content is not a PDF")
            temporary.replace(destination)
            return "downloaded"
        except Exception:
            if attempt == attempts:
                raise
            time.sleep(attempt)
        finally:
            if temporary.exists():
                temporary.unlink()

    raise RuntimeError("unreachable")


def build_archive(catalog_path: Path, root: Path, workers: int) -> None:
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    downloads: list[tuple[str, Path]] = []
    readme_count = 0

    for cycle in catalog["cycles"]:
        cycle_number = cycle["number"]
        cycle_dir = root / f"{cycle_number} - {safe_component(cycle['title'])}"
        legacy_cycle_dir = root / f"{cycle_number} - Ciclo {cycle_number}"
        migrate_legacy_directory(legacy_cycle_dir, cycle_dir)
        cycle_dir.mkdir(parents=True, exist_ok=True)

        for lesson in cycle["lessons"]:
            lesson_number = lesson["number"]
            lesson_dir = cycle_dir / f"{lesson_number} - {safe_component(lesson['title'])}"
            legacy_lesson_dir = cycle_dir / f"{lesson_number} - Lição {lesson_number}"
            migrate_legacy_directory(legacy_lesson_dir, lesson_dir)
            lesson_dir.mkdir(parents=True, exist_ok=True)

            pdf_name = f"{lesson_number} - {safe_component(lesson['title'])}.pdf"
            readme_path = lesson_dir / "README.md"
            existing_readme = (
                readme_path.read_text(encoding="utf-8") if readme_path.exists() else None
            )
            readme = lesson_readme(lesson, pdf_name, existing_readme)
            readme_path.write_text(readme, encoding="utf-8")
            readme_count += 1

            pdf_url = lesson["links"].get("transcript_pdf")
            if pdf_url:
                downloads.append((pdf_url, lesson_dir / pdf_name))

    failures: list[str] = []
    downloaded = 0
    existing = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(download_pdf, url, destination): destination
            for url, destination in downloads
        }
        for future in as_completed(future_map):
            destination = future_map[future]
            try:
                status = future.result()
                downloaded += status == "downloaded"
                existing += status == "existing"
            except Exception as exc:  # report every failed lesson together
                failures.append(f"{destination}: {exc}")

    print(
        f"cycles={len(catalog['cycles'])} readmes={readme_count} "
        f"pdfs_downloaded={downloaded} pdfs_existing={existing} failures={len(failures)}"
    )
    if failures:
        print("\n".join(failures), file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("fundamentos-links.json"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    build_archive(args.catalog.resolve(), args.root.resolve(), max(1, args.workers))


if __name__ == "__main__":
    main()
