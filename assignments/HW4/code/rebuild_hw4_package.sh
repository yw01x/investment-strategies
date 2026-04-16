#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PRICES_DIR="${1:-$ROOT/q1a_data/prices}"
YAHOO_WORKBOOK="${2:-}"

python3 "$ROOT/code/hw4_analysis.py" \
  --prices-dir "$PRICES_DIR" \
  --exhibits-dir "$ROOT/exhibits"

if [[ -n "$YAHOO_WORKBOOK" ]]; then
  python3 "$ROOT/code/hw4_data_source_comparison.py" \
    --yahoo-workbook "$YAHOO_WORKBOOK" \
    --prices-dir "$PRICES_DIR" \
    --exhibits-dir "$ROOT/exhibits"
fi

python3 "$ROOT/code/generate_hw4_figures.py"
bash "$ROOT/code/export_hw4_pdf.sh"

echo "HW4 package rebuilt under $ROOT"
