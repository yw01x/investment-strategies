#!/bin/zsh
set -euo pipefail

BASE="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$BASE/writeup/Investment Strategy HW5.md"
HTML="$BASE/writeup/Investment Strategy HW5.print.html"
OUT="$BASE/writeup/Investment Strategy HW5.pdf"
HEADER="$BASE/code/pdf_header.html"
CSS="$BASE/code/pdf_print.css"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

pandoc "$SRC" \
  --standalone \
  --from markdown+tex_math_dollars \
  --to html5 \
  --mathml \
  --include-before-body="$HEADER" \
  --css="$CSS" \
  -o "$HTML"

HTML_URL="file://$(python3 -c 'import sys, urllib.parse, pathlib; print(urllib.parse.quote(str(pathlib.Path(sys.argv[1]).resolve())))' "$HTML")"

"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT" \
  "$HTML_URL"
