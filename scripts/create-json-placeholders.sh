#!/usr/bin/env bash
set -euo pipefail

CONTENT_DIR="${1:-content}"

if [[ ! -d "$CONTENT_DIR" ]]; then
  echo "Content directory not found: $CONTENT_DIR" >&2
  exit 1
fi

created=0

while IFS= read -r -d '' markdown_file; do
  json_file="${markdown_file%.md}.json"

  if [[ -e "$json_file" ]]; then
    continue
  fi

  printf '{}\n' > "$json_file"
  echo "Created: $json_file"
  created=$((created + 1))
done < <(find "$CONTENT_DIR" -type f -name '*.md' -print0)

echo "Created $created JSON placeholder file(s)."
