---
name: fundamentos-content-archive
description: Build, refresh, audit, or repair the local Fundamentos lesson archive from the public Fundamentos API or fundamentos-links.json. Use when Codex needs to organize lessons by cycle, download transcript PDFs, generate per-lesson Markdown link indexes, reconcile missing media, or update this workspace's Fundamentos content.
---

# Fundamentos content archive

## Use the canonical source

Prefer `https://api.fundamentos.me/api/edge/cycles` because it returns lessons already grouped by cycle. Use the flat `/lessons/fundamentos/listAll` endpoint only for cross-checking.

Use `fundamentos-links.json` when the user wants a rebuild without refreshing remote metadata. Preserve these normalized fields per lesson:

- `links.video`: primary, YouTube summary, full video, original live, and sign language.
- `links.transcript_pdf`: transcript PDF URL.
- `links.podcasts`: summary and full URLs grouped by platform.

## Build or repair the archive

Run from the workspace root:

```bash
python3 scripts/build_lesson_archive.py
```

Pass `--catalog <path>`, `--root <path>`, or `--workers <n>` only when needed. Rerun the same command after transient connection failures; it skips valid PDFs and safely replaces incomplete downloads.

Generate this exact hierarchy:

```text
1 - Temas Panorâmicos/
  1 - O conselho de Deus/
    README.md
    1 - O conselho de Deus.pdf
```

Name cycle and lesson directories as `<number> - <title>`. Never use generic names such as `1 - Ciclo 1` or `1 - Lição 1`. Use global lesson numbers for directories and files. Keep cycle 15 even when it has zero lessons.

## Generate lesson indexes

Write one `README.md` per lesson containing:

1. The global lesson number and title.
2. Every non-empty video link.
3. Both the local PDF link and its original URL.
4. Every podcast platform, separating summary and full versions.

Do not invent unavailable links. Omit empty variants.

## Validate the result

Run:

```bash
jq empty fundamentos-links.json
python3 -m py_compile scripts/build_lesson_archive.py
find . -type f -name README.md | wc -l
find . -type f -name '*.pdf' | wc -l
find . -type f -name '*.part' | wc -l
```

Open a representative `README.md` and confirm that its local PDF link matches the actual filename. Validate downloaded files by the `%PDF-` signature, not only by extension.

Read `AGENTS.md` before changing naming, pruning files, or refreshing the catalog.
