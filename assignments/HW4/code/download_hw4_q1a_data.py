#!/usr/bin/env python3
"""Download and validate HW4 Q1(a) daily data from Tiingo."""

from __future__ import annotations

import argparse
import csv
import getpass
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

DEFAULT_START_DATE = "2020-04-13"
DEFAULT_END_DATE = "2026-04-10"
GEHC_FIRST_TRADING_DAY = "2023-01-04"
BENCHMARK_TICKERS = ("SPY", "VOO")
TOKEN_ENV_CANDIDATES = ("TIINGO_API_KEY", "TIINGO_TOKEN", "TIINGO_API_TOKEN")
DEFAULT_KEYCHAIN_SERVICE = "tiingo-api"
CSV_COLUMNS = (
    "date",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "adjOpen",
    "adjHigh",
    "adjLow",
    "adjClose",
    "adjVolume",
    "divCash",
    "splitFactor",
)
TIINGO_ENDPOINT = "https://api.tiingo.com/tiingo/daily/{ticker}/prices"


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Download HW4 Q1(a) daily stock and ETF data from Tiingo."
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        default=script_dir / "hw4.50StockValuePortoflio.xlsx",
        help="Path to the homework workbook that contains the 50 stock tickers.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=script_dir / "q1a_data",
        help="Directory where CSV files and validation artifacts will be written.",
    )
    parser.add_argument(
        "--start-date",
        default=DEFAULT_START_DATE,
        help=f"Inclusive sample start date in YYYY-MM-DD format. Default: {DEFAULT_START_DATE}.",
    )
    parser.add_argument(
        "--end-date",
        default=DEFAULT_END_DATE,
        help=f"Inclusive sample end date in YYYY-MM-DD format. Default: {DEFAULT_END_DATE}.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Tiingo API token. If omitted, the script checks common TIINGO_* environment variables.",
    )
    parser.add_argument(
        "--token-env",
        default=None,
        help="Specific environment variable name to read the Tiingo token from.",
    )
    parser.add_argument(
        "--keychain-service",
        default=DEFAULT_KEYCHAIN_SERVICE,
        help=(
            "macOS Keychain service name to read the Tiingo token from. "
            f"Default: {DEFAULT_KEYCHAIN_SERVICE}."
        ),
    )
    parser.add_argument(
        "--keychain-account",
        default=getpass.getuser(),
        help=(
            "macOS Keychain account name to read the Tiingo token from. "
            "Default: current macOS username."
        ),
    )
    parser.add_argument(
        "--skip-keychain",
        action="store_true",
        help="Do not attempt to read the Tiingo token from macOS Keychain.",
    )
    parser.add_argument(
        "--max-new-downloads",
        type=int,
        default=None,
        help=(
            "Optional cap on newly fetched tickers for the current run. "
            "Useful if you want to stay inside the Tiingo free-plan hourly limit and resume later."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Refetch CSV files even if they already exist.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the download plan without making network calls or writing files.",
    )
    return parser.parse_args()


def validate_iso_date(text: str) -> str:
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise SystemExit(f"Invalid date '{text}'. Expected YYYY-MM-DD.") from exc


def find_token(args: argparse.Namespace) -> str | None:
    if args.token:
        return args.token.strip()
    if args.token_env:
        value = os.environ.get(args.token_env, "").strip()
        return value or None
    for name in TOKEN_ENV_CANDIDATES:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    if not args.skip_keychain:
        value = find_token_in_keychain(
            service=args.keychain_service,
            account=args.keychain_account,
        )
        if value:
            return value
    return None


def find_token_in_keychain(service: str, account: str) -> str | None:
    command = [
        "/usr/bin/security",
        "find-generic-password",
        "-w",
        "-s",
        service,
        "-a",
        account,
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def load_shared_strings(xlsx_path: Path) -> List[str]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(xlsx_path) as workbook_zip:
        root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
    strings: List[str] = []
    for item in root.findall("a:si", ns):
        text = "".join(node.text or "" for node in item.iterfind(".//a:t", ns))
        strings.append(text)
    return strings


def load_sheet_cells(xlsx_path: Path) -> Dict[str, str]:
    ns = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    shared_strings = load_shared_strings(xlsx_path)
    with zipfile.ZipFile(xlsx_path) as workbook_zip:
        root = ET.fromstring(workbook_zip.read("xl/worksheets/sheet1.xml"))
    cells: Dict[str, str] = {}
    for cell in root.findall(".//a:sheetData/a:row/a:c", ns):
        ref = cell.attrib.get("r", "")
        value_node = cell.find("a:v", ns)
        if value_node is None:
            cells[ref] = ""
            continue
        if cell.attrib.get("t") == "s":
            cells[ref] = shared_strings[int(value_node.text)]
        else:
            cells[ref] = value_node.text or ""
    return cells


def load_portfolio_tickers(workbook_path: Path) -> List[str]:
    if not workbook_path.exists():
        raise SystemExit(f"Workbook not found: {workbook_path}")
    cells = load_sheet_cells(workbook_path)
    tickers: List[str] = []
    for column in ("B", "G"):
        for row_number in range(2, 27):
            ticker = cells.get(f"{column}{row_number}", "").strip().upper()
            if ticker:
                tickers.append(ticker)
    deduped = []
    seen = set()
    for ticker in tickers:
        if ticker not in seen:
            seen.add(ticker)
            deduped.append(ticker)
    if len(deduped) != 50:
        raise SystemExit(
            f"Expected 50 portfolio tickers in {workbook_path.name}, found {len(deduped)}."
        )
    return deduped


def build_universe(workbook_path: Path) -> List[str]:
    tickers = load_portfolio_tickers(workbook_path)
    for benchmark in BENCHMARK_TICKERS:
        if benchmark not in tickers:
            tickers.append(benchmark)
    return tickers


def normalize_row(row: Dict[str, object]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}
    for column in CSV_COLUMNS:
        value = row.get(column, "")
        if column == "date" and value:
            normalized[column] = str(value)[:10]
        elif value is None:
            normalized[column] = ""
        else:
            normalized[column] = str(value)
    return normalized


def fetch_ticker_prices(
    ticker: str,
    start_date: str,
    end_date: str,
    token: str,
) -> List[Dict[str, str]]:
    query = urllib.parse.urlencode(
        {
            "startDate": start_date,
            "endDate": end_date,
            "resampleFreq": "daily",
            "format": "json",
            "token": token,
        }
    )
    url = TIINGO_ENDPOINT.format(ticker=ticker.lower()) + "?" + query
    request = urllib.request.Request(
        url,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "hw4-q1a-tiingo-downloader/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{ticker}: HTTP {exc.code} from Tiingo. {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{ticker}: unable to reach Tiingo. {exc.reason}") from exc

    data = json.loads(payload)
    if isinstance(data, dict):
        message = data.get("detail") or data.get("message") or json.dumps(data)
        raise RuntimeError(f"{ticker}: Tiingo returned an error payload: {message}")
    if not isinstance(data, list):
        raise RuntimeError(f"{ticker}: unexpected Tiingo payload type: {type(data)!r}")
    return [normalize_row(row) for row in data]


def write_price_csv(path: Path, rows: Sequence[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def read_price_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def nontrivial_close_adjustment_days(rows: Iterable[Dict[str, str]]) -> int:
    count = 0
    for row in rows:
        close_text = row.get("close", "")
        adj_text = row.get("adjClose", "")
        if not close_text or not adj_text:
            continue
        if abs(float(close_text) - float(adj_text)) > 1e-9:
            count += 1
    return count


def describe_event_rows(
    rows: Iterable[Dict[str, str]],
    column: str,
    predicate,
    value_transform,
    limit: int = 5,
) -> List[Dict[str, object]]:
    events = []
    for row in rows:
        text = row.get(column, "")
        if text == "":
            continue
        value = float(text)
        if predicate(value):
            events.append({"date": row["date"], column: value_transform(value)})
        if len(events) >= limit:
            break
    return events


def build_manifest(
    workbook_path: Path,
    output_dir: Path,
    universe: Sequence[str],
    start_date: str,
    end_date: str,
    pending_tickers: Sequence[str],
) -> Dict[str, object]:
    return {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "provider": "Tiingo historical end-of-day API",
            "endpointTemplate": TIINGO_ENDPOINT,
            "priceColumns": list(CSV_COLUMNS),
        },
        "sampleWindow": {
            "startDate": start_date,
            "endDate": end_date,
        },
        "universe": {
            "portfolioTickerCount": 50,
            "benchmarkTickers": list(BENCHMARK_TICKERS),
            "allTickers": list(universe),
            "workbook": str(workbook_path.resolve()),
        },
        "exceptions": [
            {
                "ticker": "GEHC",
                "reason": (
                    "GE HealthCare became a separately traded company on 2023-01-04. "
                    "The dataset keeps GEHC's real standalone trading history and does not splice GE."
                ),
                "expectedFirstTradingDay": GEHC_FIRST_TRADING_DAY,
            }
        ],
        "output": {
            "directory": str(output_dir.resolve()),
            "pricesDirectory": str((output_dir / "prices").resolve()),
            "validationReport": str((output_dir / "validation_report.json").resolve()),
        },
        "pendingTickers": list(pending_tickers),
    }


def build_validation_report(
    output_dir: Path,
    universe: Sequence[str],
    start_date: str,
    end_date: str,
) -> Dict[str, object]:
    prices_dir = output_dir / "prices"
    data_by_ticker: Dict[str, List[Dict[str, str]]] = {}
    for ticker in universe:
        csv_path = prices_dir / f"{ticker}.csv"
        if csv_path.exists():
            rows = read_price_csv(csv_path)
            if rows:
                data_by_ticker[ticker] = rows

    missing = [ticker for ticker in universe if ticker not in data_by_ticker]
    report: Dict[str, object] = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "sampleWindow": {"startDate": start_date, "endDate": end_date},
        "coverage": {
            "expectedTickerCount": len(universe),
            "downloadedTickerCount": len(data_by_ticker),
            "missingTickers": missing,
            "complete": not missing,
        },
    }

    per_ticker = {}
    for ticker, rows in data_by_ticker.items():
        per_ticker[ticker] = {
            "rows": len(rows),
            "firstDate": rows[0]["date"],
            "lastDate": rows[-1]["date"],
        }
    report["perTicker"] = per_ticker

    if "SPY" in data_by_ticker:
        spy_dates = [row["date"] for row in data_by_ticker["SPY"]]
        spy_date_set = set(spy_dates)
        alignment = {}
        for ticker, rows in data_by_ticker.items():
            first_date = rows[0]["date"]
            actual_dates = {row["date"] for row in rows}
            expected_dates = [date for date in spy_dates if date >= first_date]
            missing_dates = [date for date in expected_dates if date not in actual_dates]
            extra_dates = [date for date in actual_dates if date not in spy_date_set]
            alignment[ticker] = {
                "alignedToSpyFromOwnStart": not missing_dates and not extra_dates,
                "missingVsSpyCount": len(missing_dates),
                "missingVsSpyExamples": missing_dates[:5],
                "extraVsSpyCount": len(extra_dates),
                "extraVsSpyExamples": sorted(extra_dates)[:5],
            }
        report["dateAlignmentVsSpy"] = alignment

    dividend_sample = next(
        (ticker for ticker in ("VOO", "JNJ") if ticker in data_by_ticker),
        None,
    )
    split_sample = next(
        (ticker for ticker in ("NVDA", "AAPL") if ticker in data_by_ticker),
        None,
    )
    adjusted_checks: Dict[str, object] = {}
    if dividend_sample:
        rows = data_by_ticker[dividend_sample]
        adjusted_checks["dividendSample"] = {
            "ticker": dividend_sample,
            "dividendEvents": describe_event_rows(
                rows,
                "divCash",
                predicate=lambda value: value > 0,
                value_transform=lambda value: round(value, 8),
            ),
            "daysWhereCloseDiffersFromAdjClose": nontrivial_close_adjustment_days(rows),
        }
    if split_sample:
        rows = data_by_ticker[split_sample]
        adjusted_checks["splitSample"] = {
            "ticker": split_sample,
            "splitEvents": describe_event_rows(
                rows,
                "splitFactor",
                predicate=lambda value: abs(value - 1.0) > 1e-9,
                value_transform=lambda value: round(value, 8),
            ),
            "daysWhereCloseDiffersFromAdjClose": nontrivial_close_adjustment_days(rows),
        }
    if adjusted_checks:
        report["adjustedSeriesChecks"] = adjusted_checks

    if "GEHC" in data_by_ticker:
        gehc_first_date = data_by_ticker["GEHC"][0]["date"]
        report["gehcExceptionCheck"] = {
            "ticker": "GEHC",
            "expectedFirstTradingDay": GEHC_FIRST_TRADING_DAY,
            "actualFirstTradingDay": gehc_first_date,
            "matchesExpectation": gehc_first_date == GEHC_FIRST_TRADING_DAY,
        }

    return report


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def planned_queue(
    output_dir: Path,
    universe: Sequence[str],
    overwrite: bool,
) -> List[str]:
    queue = []
    for ticker in universe:
        csv_path = output_dir / "prices" / f"{ticker}.csv"
        if overwrite or not csv_path.exists():
            queue.append(ticker)
    return queue


def main() -> int:
    args = parse_args()
    start_date = validate_iso_date(args.start_date)
    end_date = validate_iso_date(args.end_date)
    if end_date < start_date:
        raise SystemExit("The end date must be on or after the start date.")

    universe = build_universe(args.workbook)
    queue = planned_queue(args.output_dir, universe, args.overwrite)
    capped_queue = (
        queue[: args.max_new_downloads]
        if args.max_new_downloads is not None
        else queue
    )
    pending_after_run = queue[len(capped_queue) :]

    if args.dry_run:
        print("Dry run only. No files written and no network requests made.")
        print(f"Workbook: {args.workbook.resolve()}")
        print(f"Output dir: {args.output_dir.resolve()}")
        print(f"Sample window: {start_date} -> {end_date}")
        print(f"Universe size: {len(universe)}")
        print("Tickers: " + ", ".join(universe))
        if args.max_new_downloads is not None and len(queue) > len(capped_queue):
            print(
                f"New downloads capped at {args.max_new_downloads}; "
                f"{len(pending_after_run)} ticker(s) would remain pending."
            )
        return 0

    token = find_token(args)
    if not token:
        env_hint = ", ".join(TOKEN_ENV_CANDIDATES)
        raise SystemExit(
            "No Tiingo token found. Set one of "
            f"{env_hint}, store it in macOS Keychain under service "
            f"'{args.keychain_service}' and account '{args.keychain_account}', "
            "or pass --token/--token-env."
        )

    prices_dir = args.output_dir / "prices"
    prices_dir.mkdir(parents=True, exist_ok=True)
    failures = []

    print(
        f"Downloading {len(capped_queue)} ticker(s) from Tiingo "
        f"for {start_date} -> {end_date}..."
    )
    for index, ticker in enumerate(capped_queue, start=1):
        try:
            rows = fetch_ticker_prices(ticker, start_date, end_date, token)
            if not rows:
                raise RuntimeError(f"{ticker}: Tiingo returned no rows.")
            write_price_csv(prices_dir / f"{ticker}.csv", rows)
            print(f"[{index:02d}/{len(capped_queue):02d}] {ticker}: {len(rows)} rows")
        except Exception as exc:  # pragma: no cover - network errors are data-dependent
            failures.append(str(exc))
            print(f"[{index:02d}/{len(capped_queue):02d}] {ticker}: FAILED", file=sys.stderr)
            print(f"    {exc}", file=sys.stderr)

    all_pending = pending_after_run + [
        message.split(":", 1)[0] for message in failures if ":" in message
    ]
    manifest = build_manifest(
        workbook_path=args.workbook,
        output_dir=args.output_dir,
        universe=universe,
        start_date=start_date,
        end_date=end_date,
        pending_tickers=all_pending,
    )
    report = build_validation_report(args.output_dir, universe, start_date, end_date)
    write_json(args.output_dir / "manifest.json", manifest)
    write_json(args.output_dir / "validation_report.json", report)

    if failures:
        print("\nSome downloads failed. See validation_report.json and the messages above.", file=sys.stderr)
        return 1
    if pending_after_run:
        print(
            "\nDownload queue capped before the full universe finished. "
            "Re-run the same command after the Tiingo rate-limit window resets."
        )
    else:
        print("\nDownload complete. Wrote CSVs, manifest.json, and validation_report.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
