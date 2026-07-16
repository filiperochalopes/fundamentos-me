#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
root_dir="$(cd -- "$script_dir/.." && pwd)"
output="${1:-$root_dir/fundamentos-pdfs.zip}"

if [[ "$output" != /* ]]; then
  output="$PWD/$output"
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "Erro: o comando 'zip' não está instalado." >&2
  exit 1
fi

pdf_count="$({ find "$root_dir" -mindepth 3 -maxdepth 3 -type f -iname '*.pdf' -print0 || true; } | tr -cd '\0' | wc -c | tr -d ' ')"

if [[ "$pdf_count" -eq 0 ]]; then
  echo "Erro: nenhum PDF foi encontrado em $root_dir." >&2
  exit 1
fi

mkdir -p -- "$(dirname -- "$output")"
temporary="${output}.part.zip"
trap 'rm -f -- "$temporary"' EXIT
rm -f -- "$temporary"

(
  cd -- "$root_dir"
  pdfs=()
  while IFS= read -r -d '' pdf; do
    pdfs+=("$pdf")
  done < <(find . -mindepth 3 -maxdepth 3 -type f -iname '*.pdf' -print0 | LC_ALL=C sort -z)
  zip -jq "$temporary" "${pdfs[@]}"
)

mv -f -- "$temporary" "$output"
trap - EXIT

echo "ZIP criado: $output"
echo "PDFs incluídos: $pdf_count"
