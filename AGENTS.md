# Fundamentos Content Archive

## Purpose

Maintain a local archive of the Fundamentos lessons, organized by cycle and lesson, with one transcript PDF and one link index per lesson.

## Canonical inputs

- Use `fundamentos-links.json` as the normalized local catalog.
- Refresh the source data from `https://api.fundamentos.me/api/edge/cycles` when the user requests an update.
- Do not manually copy every link from the iPhone UI. Use the public API for exact values and validate representative records against the app.
- The flat website endpoint is `https://api.fundamentos.me/api/edge/lessons/fundamentos/listAll`, but `/cycles` is preferred because it preserves cycle membership.

## Archive layout

Use this exact structure:

```text
<cycle number> - <cycle title>/
  <lesson number> - <lesson title>/
    README.md
    <lesson number> - <lesson title>.pdf
```

For example, use `1 - Temas Panorâmicos/1 - O conselho de Deus/`. Keep global lesson numbers. Sanitize `/`, `:`, `\\`, NUL, repeated whitespace, and trailing periods only in filesystem names; preserve the original title inside Markdown and JSON.

## Rebuild command

Run:

```bash
python3 scripts/build_lesson_archive.py
```

The script is idempotent. It rewrites generated lesson READMEs, keeps PDFs that already pass the `%PDF-` signature check, downloads missing or invalid PDFs, uses temporary `.part` files, and retries transient network failures.

## Validation

After rebuilding, verify all of the following:

```bash
jq empty fundamentos-links.json
python3 -m py_compile scripts/build_lesson_archive.py
find . -type f -name README.md | wc -l
find . -type f -name '*.pdf' | wc -l
find . -type f -name '*.part' | wc -l
```

Expected for the catalog captured on 2026-07-15: 15 cycle directories, 139 lesson READMEs, 139 PDFs, and zero `.part` files. Cycle 15 is present but inactive and has no lessons in that snapshot.

## Safety

- Do not delete user files or unrelated directories.
- Treat new catalog records as additive unless the user explicitly requests pruning.
- If a download fails, rerun the idempotent script before changing URLs or filenames.
- Preserve `fundamentos-links.json`, `extract-links.jq`, `AGENTS.md`, `SKILL.md`, and `scripts/build_lesson_archive.py` at the repository root.
