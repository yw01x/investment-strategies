# Investment Strategy HW5

This directory contains a cleaned repository package for the Investment Strategy HW5 submission.

## Contents

- `writeup/Investment Strategy HW5.pdf`
  - Final write-up PDF with proofs, tables, and figures.
- `writeup/Investment Strategy HW5.md`
  - Source markdown used to generate the final write-up.
- `writeup/figures/`
  - SVG figures referenced in the write-up.
- `data/`
  - Original source data used in the homework package:
    - `data/tiingo_prices/` contains the local adjusted-price CSV files reused from HW4
- `exhibits/`
  - Supporting CSV exhibits used in the submission:
    - stock-by-stock growth-rate table for Q2(a)
    - growth-stability summary for Q2(a)
    - equal-weight portfolio metrics for Q2(b)
    - equal-weight versus HW4 GMV comparison for Q2(c)
    - compact HW5 summary metrics
- `code/hw5_analysis.py`
  - Consolidated analysis script covering the main HW5 calculations:
    - annualized stock growth-rate stability across the two 3-year windows
    - 50-stock daily rebalanced equal-weight portfolio evaluation
    - comparison versus the HW4 long-only GMV portfolio
- `code/generate_hw5_figures.py`
  - Script used to generate the SVG figures included in the write-up from the same analysis outputs.
- `code/export_hw5_pdf.sh`
  - Script used to regenerate the write-up PDF from markdown.
- `code/rebuild_hw5_package.sh`
  - One-command wrapper that rebuilds exhibits, regenerates figures, and exports the PDF.
- `code/pdf_header.html`
  - Header fragment used when exporting the PDF.
- `code/pdf_print.css`
  - Print stylesheet used when exporting the PDF.

## Notes

- This package is intentionally cleaner than the original local homework working directory.
- Temporary files, intermediate HTML previews, `.DS_Store`, and duplicate outputs are omitted.
- The committed `data/` directory preserves the adjusted-price files used in the HW5 calculations.
- `code/hw5_analysis.py` is self-contained and uses the same 50-stock universe and the same 3-year windows as HW4.
- `code/rebuild_hw5_package.sh` runs the full local pipeline from exhibits to figures to PDF.
