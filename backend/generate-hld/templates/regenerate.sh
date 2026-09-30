#!/usr/bin/env bash
# Regenerate HLD.docx from HLD.md and the .drawio source files.
# Pipeline: .drawio -> .svg, .md -> .docx, add table borders, swap PNG fallbacks with high-res renders.
#
# Usage:
#   ./regenerate.sh                # uses current working directory
#   bash regenerate.sh /path/to/HLD   # explicit target directory

set -euo pipefail

TARGET_DIR="${1:-$(pwd)}"
if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: target directory does not exist: $TARGET_DIR" >&2
  exit 1
fi
cd "$TARGET_DIR"

if ! ls *.md >/dev/null 2>&1; then
  echo "Error: no .md file in $TARGET_DIR (expected HLD.md)" >&2
  exit 1
fi

PNG_ZOOM=4   # PNG fallback resolution multiplier

# Locate the drawio CLI across platforms
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

for cmd in pandoc rsvg-convert python3 zip unzip; do
  command -v "$cmd" >/dev/null || { echo "Error: $cmd not installed" >&2; exit 1; }
done

echo "==> Exporting .drawio -> .svg"
for f in *.drawio; do
  echo "    $f"
  "$DRAWIO_BIN" --export --format svg --output "${f}.svg" "$f" >/dev/null 2>&1
done

echo "==> Generating high-res PNG fallbacks (${PNG_ZOOM}x)"
TMP_PNG=$(mktemp -d)
trap 'rm -rf "$TMP_PNG"' EXIT
for f in *.drawio.svg; do
  base="${f%.drawio.svg}"
  rsvg-convert -z "$PNG_ZOOM" "$f" -o "$TMP_PNG/${base}.png"
done

echo "==> Building HLD.docx from HLD.md"
pandoc HLD.md -o HLD.docx --from markdown --to docx

echo "==> Adding borders to all tables"
python3 <<'PY'
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def set_cell_borders(cell):
    tc = cell._tc
    tcPr = tc.find(qn('w:tcPr'))
    if tcPr is None:
        tcPr = OxmlElement('w:tcPr'); tc.insert(0, tcPr)
    for existing in tcPr.findall(qn('w:tcBorders')):
        tcPr.remove(existing)
    tcBorders = OxmlElement('w:tcBorders')
    for b in ['top','left','bottom','right']:
        bd = OxmlElement(f'w:{b}')
        bd.set(qn('w:val'),'single'); bd.set(qn('w:sz'),'4')
        bd.set(qn('w:space'),'0'); bd.set(qn('w:color'),'000000')
        tcBorders.append(bd)
    tcPr.append(tcBorders)

doc = Document('HLD.docx')
for t in doc.tables:
    for r in t.rows:
        for c in r.cells:
            set_cell_borders(c)
doc.save('HLD.docx')
PY

echo "==> Swapping low-res PNG fallbacks with high-res renders"
WORK=$(mktemp -d)
unzip -q HLD.docx -d "$WORK"

# Map embedded PNGs to source diagrams by aspect ratio (width x height of the source SVG render)
python3 <<PY
import os, glob, struct

def png_size(path):
    with open(path, 'rb') as f:
        f.seek(16)
        return struct.unpack('>II', f.read(8))

src_pngs = {f: png_size(f) for f in glob.glob('$TMP_PNG/*.png')}
for embedded in glob.glob('$WORK/word/media/*.png'):
    ew, eh = png_size(embedded)
    e_ratio = ew / eh
    # Find the source PNG with the closest aspect ratio
    best = min(src_pngs.items(), key=lambda kv: abs(kv[1][0]/kv[1][1] - e_ratio))
    print(f'  {os.path.basename(embedded)} ({ew}x{eh}) <- {os.path.basename(best[0])} ({best[1][0]}x{best[1][1]})')
    os.replace(best[0], embedded)
PY

(cd "$WORK" && zip -qr "$OLDPWD/HLD.docx" . -x ".*")
rm -rf "$WORK"

echo "==> Done. HLD.docx regenerated."
