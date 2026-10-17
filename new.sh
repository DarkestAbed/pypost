#!/bin/sh
# Start a new blog from the pypost template.
# Usage: sh new.sh [destination-dir]
set -eu

REPO="${PYPOST_REPO:-gh:GH-USER/pypost}"   # TODO: replace GH-USER when pypost is published
DEST="${1:-my-blog}"

if command -v uvx >/dev/null 2>&1; then
  exec uvx copier copy --trust "$REPO" "$DEST"
elif command -v pipx >/dev/null 2>&1; then
  exec pipx run copier copy --trust "$REPO" "$DEST"
elif python3 -c 'import copier' >/dev/null 2>&1; then
  exec python3 -m copier copy --trust "$REPO" "$DEST"
else
  echo "You need uv (https://docs.astral.sh/uv/) or pipx to start a pypost blog." >&2
  exit 1
fi
