#!/usr/bin/env bash
# Export the 3 solution architecture .drawio files to .drawio.svg.
#
# Usage:
#   ./export.sh                       # uses current working directory
#   bash export.sh /path/to/dir       # explicit target directory
#   bash export.sh /path/to/dir --png # also render quick local preview PNGs (not part of the deliverable)

set -euo pipefail

TARGET_DIR="${1:-$(pwd)}"
WITH_PNG="${2:-}"

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: target directory does not exist: $TARGET_DIR" >&2
  exit 1
fi
cd "$TARGET_DIR"

if ! ls *.drawio >/dev/null 2>&1; then
  echo "Error: no .drawio files in $TARGET_DIR" >&2
  exit 1
fi

if [[ -x "/Applications/draw.io.app/Contents/MacOS/draw.io" ]]; then
  DRAWIO_BIN="/Applications/draw.io.app/Contents/MacOS/draw.io"
elif command -v drawio >/dev/null 2>&1; then
  DRAWIO_BIN="$(command -v drawio)"
else
  echo "Error: drawio CLI not found." >&2
  echo "  macOS:   brew install --cask drawio" >&2
  echo "  Linux:   download from https://github.com/jgraph/drawio-desktop/releases" >&2
  exit 1
fi

echo "==> Exporting .drawio -> .svg"
for f in *.drawio; do
  echo "    $f"
  "$DRAWIO_BIN" --export --format svg --output "${f}.svg" "$f" >/dev/null 2>&1
done

if [[ "$WITH_PNG" == "--png" ]]; then
  command -v rsvg-convert >/dev/null || { echo "Error: rsvg-convert not installed (needed for --png)" >&2; exit 1; }
  echo "==> Rendering preview PNGs (not part of the deliverable)"
  for f in *.drawio.svg; do
    base="${f%.drawio.svg}"
    rsvg-convert -z 2 "$f" -o "${base}.preview.png"
    echo "    ${base}.preview.png"
  done
fi

echo "==> Done."
