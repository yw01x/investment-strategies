#!/usr/bin/env python3

import argparse
import csv
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from posixpath import normpath


NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
TICKERS = ["SPY", "VOO", "JNJ", "PEP", "AMZN"]


def load_shared_strings(archive):
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    out = []
    for si in root.findall("a:si", NS):
        text = "".join(node.text or "" for node in si.iterfind(".//a:t", NS))
        out.append(text)
    return out


def sheet_name_map(archive):
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    rel_map = {
        rel.attrib["Id"]: rel.attrib["Target"]
        for rel in rels
        if rel.tag.endswith("Relationship")
    }
    out = {}
    for sheet in workbook.find("a:sheets", NS):
        rel_id = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = rel_map[rel_id]
        out[sheet.attrib["name"]] = normpath(f"xl/{target}")
    return out


def read_sheet_rows(archive, sheet_path, shared_strings):
    root = ET.fromstring(archive.read(sheet_path))
    rows = []
    for row in root.find("a:sheetData", NS).findall("a:row", NS):
        values = {}
        for cell in row.findall("a:c", NS):
            ref = cell.attrib["r"]
            col = "".join(ch for ch in ref if ch.isalpha())
            value = cell.find("a:v", NS)
            if value is None:
                values[col] = ""
            elif cell.attrib.get("t") == "s":
                values[col] = shared_strings[int(value.text)]
            else:
                values[col] = value.text
        rows.append(values)
    return rows


def load_yahoo_table(workbook_path):
    with zipfile.ZipFile(workbook_path) as archive:
        shared_strings = load_shared_strings(archive)
        sheets = sheet_name_map(archive)
        rows = read_sheet_rows(archive, sheets["All Data"], shared_strings)

    header = rows[2]
    col_to_ticker = {col: val for col, val in header.items() if col != "A" and val}
    ticker_to_col = {ticker: col for col, ticker in col_to_ticker.items()}
    data = {}
    for row in rows[3:]:
        date = row.get("A")
        if not date:
            continue
        data[date] = {
            ticker: float(row.get(ticker_to_col[ticker], "")) if row.get(ticker_to_col[ticker], "") != "" else None
            for ticker in ticker_to_col
        }
    return data


def load_tiingo_prices(prices_dir, ticker):
    out = {}
    with open(prices_dir / f"{ticker}.csv", newline="") as f:
        for row in csv.DictReader(f):
            out[row["date"]] = {
                "close": float(row["close"]),
                "adjClose": float(row["adjClose"]),
            }
    return out


def compute_return(start_value, end_value):
    return end_value / start_value - 1.0


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args():
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Compare Yahoo split-adjusted workbook data against Tiingo prices.")
    parser.add_argument(
        "--yahoo-workbook",
        default=str(base / "data" / "yahoo" / "52_Securities_Daily_Close_Yahoo_Finance.xlsx"),
        help="Path to the Yahoo Finance workbook used for comparison.",
    )
    parser.add_argument(
        "--prices-dir",
        default=str(base / "data" / "tiingo_prices"),
        help="Directory containing Tiingo per-ticker CSV files.",
    )
    parser.add_argument(
        "--exhibits-dir",
        default=str(base / "exhibits"),
        help="Directory where the comparison exhibit should be written.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    workbook_path = Path(args.yahoo_workbook)
    prices_dir = Path(args.prices_dir)
    exhibits_dir = Path(args.exhibits_dir)

    yahoo = load_yahoo_table(workbook_path)
    tiingo = {ticker: load_tiingo_prices(prices_dir, ticker) for ticker in TICKERS}

    comparison_rows = []
    sample_date = "2020-04-13"
    end_date = "2026-04-07"
    for ticker in TICKERS:
        yahoo_start = yahoo[sample_date][ticker]
        yahoo_end = yahoo[end_date][ticker]
        tiingo_start = tiingo[ticker][sample_date]
        tiingo_end = tiingo[ticker][end_date]
        comparison_rows.append({
            "Ticker": ticker,
            "Yahoo Sample Date": sample_date,
            "Yahoo Sample Value": f"{yahoo_start:.5f}",
            "Tiingo Close Sample Value": f"{tiingo_start['close']:.5f}",
            "Tiingo AdjClose Sample Value": f"{tiingo_start['adjClose']:.5f}",
            "Yahoo Return 2020-04-13 to 2026-04-07": f"{100.0 * compute_return(yahoo_start, yahoo_end):.5f}%",
            "Tiingo Close Return 2020-04-13 to 2026-04-07": f"{100.0 * compute_return(tiingo_start['close'], tiingo_end['close']):.5f}%",
            "Tiingo AdjClose Return 2020-04-13 to 2026-04-07": f"{100.0 * compute_return(tiingo_start['adjClose'], tiingo_end['adjClose']):.5f}%",
        })

    write_csv(exhibits_dir / "hw4_q1a_data_source_comparison.csv", comparison_rows)
    print(f"Wrote {exhibits_dir / 'hw4_q1a_data_source_comparison.csv'}")


if __name__ == "__main__":
    main()
