#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PRICES_DIR="${1:-$ROOT/data/tiingo_prices}"

python3 "$ROOT/code/hw5_analysis.py" \
  --prices-dir "$PRICES_DIR" \
  --exhibits-dir "$ROOT/exhibits"

python3 "$ROOT/code/generate_hw5_figures.py"
bash "$ROOT/code/export_hw5_pdf.sh"

echo "HW5 package rebuilt under $ROOT"
