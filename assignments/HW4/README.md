# Investment Strategy HW4

This directory contains a cleaned repository package for the Investment Strategy HW4 submission.

## Contents

- `writeup/Investment Strategy HW4.pdf`
  - Final write-up PDF with tables, figures, and appendices.
- `writeup/Investment Strategy HW4.md`
  - Source markdown used to generate the final write-up.
- `writeup/figures/`
  - SVG figures referenced in the write-up.
- `data/`
  - Original source data used in the homework package:
    - `data/tiingo_prices/` contains the raw per-ticker Tiingo CSV downloads
    - `data/yahoo/` contains the Yahoo workbook used for the Q1(a) comparison
- `exhibits/`
  - Supporting CSV exhibits used in the submission:
    - Tiingo-versus-Yahoo comparison for Q1(a)
    - parameter summaries
    - nonzero GMV weights
    - hedge performance
    - Sharpe-style replication summary
- `code/download_hw4_q1a_data.py`
  - Script used to download and validate the Tiingo end-of-day dataset for Q1(a).
- `code/hw4_analysis.py`
  - Consolidated analysis script covering the main homework calculations:
    - adjusted-return construction
    - first-window and second-window parameter estimation
    - long-only GMV portfolio optimization
    - out-of-sample and hypothetical out-of-sample evaluation
    - SPY / VOO hedge-ratio estimation and hedge-performance summaries
    - Sharpe-style replication diagnostics
    - Question 2 Monte Carlo verification
- `code/hw4_data_source_comparison.py`
  - Rebuilds the Q1(a) Tiingo-versus-Yahoo comparison used in the write-up, including the sample-date price checks and the cumulative-return gap table for dividend-paying securities.
- `code/generate_hw4_figures.py`
  - Script used to generate the SVG figures included in the write-up from the same analysis outputs.
- `code/export_hw4_pdf.sh`
  - Script used to regenerate the write-up PDF from markdown.
- `code/rebuild_hw4_package.sh`
  - One-command wrapper that rebuilds exhibits, optionally rebuilds the Yahoo/Tiingo comparison exhibit, regenerates figures, and exports the PDF.
- `code/pdf_header.html`
  - Header fragment used when exporting the PDF.
- `code/pdf_print.css`
  - Print stylesheet used when exporting the PDF.

## Notes

- This package is intentionally cleaner than the original local homework working directory.
- Temporary files, intermediate HTML previews, `.DS_Store`, and duplicate PDFs are omitted.
- The committed `data/` directory preserves the original Tiingo CSV files and the Yahoo workbook used during the homework.
- To refresh or rebuild the Tiingo raw-price data locally, use `code/download_hw4_q1a_data.py`.
- After local price files are available, `code/hw4_analysis.py` can be used to rebuild the supporting CSV exhibits.
- If you also have the Yahoo workbook locally, `code/hw4_data_source_comparison.py` rebuilds the data-source comparison exhibit used in Q1(a).
- `code/rebuild_hw4_package.sh` runs the full local pipeline from exhibits to figures to PDF.
- The derived figures and supporting exhibits included here show the implementation workflow used in the homework submission.
