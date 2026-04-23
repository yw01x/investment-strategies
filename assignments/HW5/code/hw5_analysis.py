#!/usr/bin/env python3
"""Rebuild the numerical exhibits for Investment Strategy HW5."""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from pathlib import Path


FIRST_PERIOD_END = "2023-04-12"
SECOND_PERIOD_START = "2023-04-13"
GEHC_TICKER = "GEHC"
SPY_TICKER = "SPY"
ALL_STOCKS = [
    "AMZN", "ADBE", "CF", "DVN", "ALLE", "CALM", "DECK", "GOOG", "INCY", "META",
    "NEM", "NFLX", "NVDA", "PFE", "VC", "QCOM", "ANF", "ARLP", "BMY", "CAH",
    "CBT", "CGAU", "CPRX", "EOG", "EXEL", "GNTX", "HCA", "HRB", "ICLR", "JNJ",
    "MCK", "MGY", "ORCL", "PEGA", "PYPL", "RNR", "SYF", "TROW", "TSM", "UBER",
    "UHS", "YELP", "AAPL", "AMGN", "GEHC", "LLY", "MRK", "MSFT", "PEP", "UPS",
]


def parse_args() -> argparse.Namespace:
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Rebuild HW5 calculation exhibits.")
    parser.add_argument(
        "--workbook",
        type=Path,
        default=None,
        help="Optional path to the HW4 workbook containing the 50 stock tickers.",
    )
    parser.add_argument(
        "--prices-dir",
        type=Path,
        default=base / "data" / "tiingo_prices",
        help="Directory containing the local per-ticker adjusted-price CSV files.",
    )
    parser.add_argument(
        "--exhibits-dir",
        type=Path,
        default=base / "exhibits",
        help="Directory where HW5 CSV exhibits should be written.",
    )
    return parser.parse_args()


def load_adj_returns(prices_dir: Path, ticker: str) -> dict[str, float]:
    out: dict[str, float] = {}
    prev = None
    with open(prices_dir / f"{ticker}.csv", newline="") as handle:
        for row in csv.DictReader(handle):
            date = row["date"]
            adj_close = float(row["adjClose"])
            if prev is not None:
                out[date] = adj_close / prev - 1.0
            prev = adj_close
    return out


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def variance(values: list[float]) -> float:
    mu = mean(values)
    return sum((value - mu) * (value - mu) for value in values) / (len(values) - 1)


def covariance(xs: list[float], ys: list[float]) -> float:
    mx = mean(xs)
    my = mean(ys)
    return sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs))) / (len(xs) - 1)


def correlation(xs: list[float], ys: list[float]) -> float:
    return covariance(xs, ys) / math.sqrt(variance(xs) * variance(ys))


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            out[order[k]] = avg_rank
        i = j + 1
    return out


def compounded_annual_growth(returns: list[float]) -> float:
    gross = 1.0
    for ret in returns:
        gross *= 1.0 + ret
    return gross ** (252.0 / len(returns)) - 1.0


def metrics(returns: list[float]) -> dict[str, float]:
    avg = mean(returns)
    vol = math.sqrt(variance(returns))
    wealth = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for ret in returns:
        wealth *= 1.0 + ret
        peak = max(peak, wealth)
        max_drawdown = min(max_drawdown, wealth / peak - 1.0)
    return {
        "Observations": float(len(returns)),
        "Cumulative Return": wealth - 1.0,
        "Annualized Return": 252.0 * avg,
        "Annualized Volatility": math.sqrt(252.0) * vol,
        "Sharpe Ratio": (252.0 * avg) / (math.sqrt(252.0) * vol),
        "Max Drawdown": max_drawdown,
        "CAGR": wealth ** (252.0 / len(returns)) - 1.0,
    }


def means(rows: list[list[float]]) -> list[float]:
    total_rows = len(rows)
    total_cols = len(rows[0])
    out = [0.0] * total_cols
    for row in rows:
        for idx, value in enumerate(row):
            out[idx] += value
    return [value / total_rows for value in out]


def cov_matrix(rows: list[list[float]], mu: list[float]) -> list[list[float]]:
    total_rows = len(rows)
    total_cols = len(mu)
    out = [[0.0] * total_cols for _ in range(total_cols)]
    for row in rows:
        centered = [row[idx] - mu[idx] for idx in range(total_cols)]
        for i in range(total_cols):
            ci = centered[i]
            for j in range(i, total_cols):
                out[i][j] += ci * centered[j]
    denom = total_rows - 1
    for i in range(total_cols):
        for j in range(i, total_cols):
            out[i][j] /= denom
            out[j][i] = out[i][j]
    return out


def matvec(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(matrix[i][j] * vector[j] for j in range(len(vector))) for i in range(len(matrix))]


def dot(xs: list[float], ys: list[float]) -> float:
    return sum(xs[i] * ys[i] for i in range(len(xs)))


def norm2(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def proj_simplex(vector: list[float]) -> list[float]:
    sorted_values = sorted(vector, reverse=True)
    running = 0.0
    theta = 0.0
    for idx, value in enumerate(sorted_values, start=1):
        running += value
        if value - (running - 1.0) / idx > 0.0:
            theta = (running - 1.0) / idx
    return [max(value - theta, 0.0) for value in vector]


def dominant_eigenvalue(matrix: list[list[float]], power_iters: int = 150) -> float:
    size = len(matrix)
    vector = [1.0 / size] * size
    for _ in range(power_iters):
        nxt = matvec(matrix, vector)
        nxt_norm = norm2(nxt)
        if nxt_norm == 0.0:
            return 0.0
        vector = [value / nxt_norm for value in nxt]
    return max(dot(vector, matvec(matrix, vector)), 0.0)


def solve_gmv(sigma: list[list[float]], iters: int = 100000, tol: float = 1e-14) -> list[float]:
    size = len(sigma)
    weights = [1.0 / size] * size
    lam = dominant_eigenvalue(sigma)
    step = 1.0 / max(2.0 * lam, 1e-12)
    for _ in range(iters):
        grad = [2.0 * value for value in matvec(sigma, weights)]
        new_weights = proj_simplex([weights[i] - step * grad[i] for i in range(size)])
        if norm2([new_weights[i] - weights[i] for i in range(size)]) < tol:
            weights = new_weights
            break
        weights = new_weights
    total = sum(weights)
    return [0.0 if abs(weight / total) < 1e-14 else weight / total for weight in weights]


def effective_names(weights: list[float]) -> float:
    return 1.0 / sum(weight * weight for weight in weights)


def equal_weight_turnover(day_returns: list[float]) -> float:
    n_assets = len(day_returns)
    target = 1.0 / n_assets
    post_weights_unnormalized = [target * (1.0 + ret) for ret in day_returns]
    gross_return = sum(post_weights_unnormalized)
    post_weights = [weight / gross_return for weight in post_weights_unnormalized]
    return 0.5 * sum(abs(weight - target) for weight in post_weights)


def fmt_decimal(value: float, places: int = 8) -> str:
    return f"{value:.{places}f}"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_analysis(prices_dir: Path, all_stocks: list[str] | None = None) -> dict[str, object]:
    all_stocks = list(all_stocks or ALL_STOCKS)
    stocks_49 = [ticker for ticker in all_stocks if ticker != GEHC_TICKER]

    returns = {ticker: load_adj_returns(prices_dir, ticker) for ticker in all_stocks + [SPY_TICKER]}

    first_dates = sorted(date for date in returns[stocks_49[0]] if date <= FIRST_PERIOD_END)
    second_dates_49 = sorted(date for date in returns[stocks_49[0]] if date >= SECOND_PERIOD_START)
    second_dates_50 = sorted(date for date in returns[all_stocks[0]] if date >= SECOND_PERIOD_START)

    for ticker in stocks_49:
        first_dates = [date for date in first_dates if date in returns[ticker]]
        second_dates_49 = [date for date in second_dates_49 if date in returns[ticker]]
    for ticker in all_stocks:
        second_dates_50 = [date for date in second_dates_50 if date in returns[ticker]]

    growth_rows: list[dict[str, object]] = []
    first_growth = []
    second_growth = []
    for ticker in stocks_49:
        g1 = compounded_annual_growth([returns[ticker][date] for date in first_dates])
        g2 = compounded_annual_growth([returns[ticker][date] for date in second_dates_49])
        first_growth.append(g1)
        second_growth.append(g2)
        growth_rows.append(
            {
                "Ticker": ticker,
                "FirstPeriodCAGR": g1,
                "SecondPeriodCAGR": g2,
                "Difference": g2 - g1,
                "SameSign": "Yes" if (g1 >= 0 and g2 >= 0) or (g1 < 0 and g2 < 0) else "No",
            }
        )

    r1_49 = [[returns[ticker][date] for ticker in stocks_49] for date in first_dates]
    r2_49 = [[returns[ticker][date] for ticker in stocks_49] for date in second_dates_49]
    r2_50 = [[returns[ticker][date] for ticker in all_stocks] for date in second_dates_50]

    mu1_49 = means(r1_49)
    mu2_49 = means(r2_49)
    sigma1_49 = cov_matrix(r1_49, mu1_49)
    gmv_weights = solve_gmv(sigma1_49)

    eq_returns = [sum(row) / len(row) for row in r2_50]
    eq_metrics = metrics(eq_returns)
    eq_turnovers = [equal_weight_turnover(row) for row in r2_50]

    gmv_returns = [
        sum(row[idx] * gmv_weights[idx] for idx in range(len(gmv_weights)))
        for row in r2_49
    ]
    gmv_metrics = metrics(gmv_returns)

    spy_second = [returns[SPY_TICKER][date] for date in second_dates_50]

    growth_summary = {
        "Stock Count": float(len(stocks_49)),
        "First-Period Observations": float(len(first_dates)),
        "Second-Period Observations": float(len(second_dates_49)),
        "Growth Pearson Correlation": correlation(first_growth, second_growth),
        "Growth Spearman Correlation": correlation(ranks(first_growth), ranks(second_growth)),
        "Same-Sign Count": float(
            sum(
                1
                for g1, g2 in zip(first_growth, second_growth)
                if (g1 >= 0 and g2 >= 0) or (g1 < 0 and g2 < 0)
            )
        ),
        "Average First-Period CAGR": mean(first_growth),
        "Average Second-Period CAGR": mean(second_growth),
        "Median First-Period CAGR": statistics.median(first_growth),
        "Median Second-Period CAGR": statistics.median(second_growth),
        "Average Absolute CAGR Change": mean([abs(g2 - g1) for g1, g2 in zip(first_growth, second_growth)]),
        "HW4 Mean-Return Stability Corr": correlation(
            [252.0 * value for value in mu1_49],
            [252.0 * value for value in mu2_49],
        ),
    }

    comparison_rows = [
        {
            "Portfolio": "Equal Weight 1/n",
            "AssetsIncluded": "50",
            "RebalancedDaily": "Yes",
            "Cumulative Return": eq_metrics["Cumulative Return"],
            "Annualized Return": eq_metrics["Annualized Return"],
            "Annualized Volatility": eq_metrics["Annualized Volatility"],
            "Sharpe Ratio": eq_metrics["Sharpe Ratio"],
            "Max Drawdown": eq_metrics["Max Drawdown"],
            "CAGR": eq_metrics["CAGR"],
            "Beta to SPY": covariance(eq_returns, spy_second) / variance(spy_second),
            "Correlation to SPY": correlation(eq_returns, spy_second),
            "Effective Names": 50.0,
            "Top-5 Weight Sum": 0.10000000,
            "Average Daily Turnover": mean(eq_turnovers),
            "Annualized Turnover": 252.0 * mean(eq_turnovers),
        },
        {
            "Portfolio": "HW4 GMV",
            "AssetsIncluded": "49",
            "RebalancedDaily": "No",
            "Cumulative Return": gmv_metrics["Cumulative Return"],
            "Annualized Return": gmv_metrics["Annualized Return"],
            "Annualized Volatility": gmv_metrics["Annualized Volatility"],
            "Sharpe Ratio": gmv_metrics["Sharpe Ratio"],
            "Max Drawdown": gmv_metrics["Max Drawdown"],
            "CAGR": gmv_metrics["CAGR"],
            "Beta to SPY": covariance(gmv_returns, spy_second) / variance(spy_second),
            "Correlation to SPY": correlation(gmv_returns, spy_second),
            "Effective Names": effective_names(gmv_weights),
            "Top-5 Weight Sum": sum(sorted(gmv_weights, reverse=True)[:5]),
            "Average Daily Turnover": 0.0,
            "Annualized Turnover": 0.0,
        },
    ]

    return {
        "all_stocks": all_stocks,
        "stocks_49": stocks_49,
        "first_dates": first_dates,
        "second_dates_49": second_dates_49,
        "second_dates_50": second_dates_50,
        "growth_rows": growth_rows,
        "growth_summary": growth_summary,
        "first_growth": first_growth,
        "second_growth": second_growth,
        "eq_metrics": eq_metrics,
        "eq_turnovers": eq_turnovers,
        "eq_returns": eq_returns,
        "gmv_metrics": gmv_metrics,
        "gmv_returns": gmv_returns,
        "gmv_weights": gmv_weights,
        "comparison_rows": comparison_rows,
    }


def export_exhibits(result: dict[str, object], exhibits_dir: Path) -> None:
    growth_rows = result["growth_rows"]
    growth_export = [
        {
            "Ticker": row["Ticker"],
            "FirstPeriodCAGR": fmt_decimal(row["FirstPeriodCAGR"]),
            "SecondPeriodCAGR": fmt_decimal(row["SecondPeriodCAGR"]),
            "Difference": fmt_decimal(row["Difference"]),
            "SameSign": row["SameSign"],
        }
        for row in growth_rows
    ]
    growth_export.sort(key=lambda row: row["Ticker"])
    write_csv(exhibits_dir / "hw5_q2a_growth_rates.csv", growth_export)

    growth_summary = result["growth_summary"]
    growth_summary_rows = [
        {"Metric": key, "Value": fmt_decimal(value, 8)}
        for key, value in growth_summary.items()
    ]
    write_csv(exhibits_dir / "hw5_q2a_growth_summary.csv", growth_summary_rows)

    eq_metrics = result["eq_metrics"]
    eq_turnovers = result["eq_turnovers"]
    eq_rows = [
        {
            "Observations": str(int(eq_metrics["Observations"])),
            "Cumulative Return": fmt_decimal(eq_metrics["Cumulative Return"]),
            "Annualized Return": fmt_decimal(eq_metrics["Annualized Return"]),
            "Annualized Volatility": fmt_decimal(eq_metrics["Annualized Volatility"]),
            "Sharpe Ratio": fmt_decimal(eq_metrics["Sharpe Ratio"]),
            "Max Drawdown": fmt_decimal(eq_metrics["Max Drawdown"]),
            "CAGR": fmt_decimal(eq_metrics["CAGR"]),
            "Average Daily Turnover": fmt_decimal(mean(eq_turnovers)),
            "Annualized Turnover": fmt_decimal(252.0 * mean(eq_turnovers)),
        }
    ]
    write_csv(exhibits_dir / "hw5_q2b_equal_weight_metrics.csv", eq_rows)

    comparison_export = []
    for row in result["comparison_rows"]:
        comparison_export.append(
            {
                "Portfolio": row["Portfolio"],
                "AssetsIncluded": row["AssetsIncluded"],
                "RebalancedDaily": row["RebalancedDaily"],
                "Cumulative Return": fmt_decimal(row["Cumulative Return"]),
                "Annualized Return": fmt_decimal(row["Annualized Return"]),
                "Annualized Volatility": fmt_decimal(row["Annualized Volatility"]),
                "Sharpe Ratio": fmt_decimal(row["Sharpe Ratio"]),
                "Max Drawdown": fmt_decimal(row["Max Drawdown"]),
                "CAGR": fmt_decimal(row["CAGR"]),
                "Beta to SPY": fmt_decimal(row["Beta to SPY"]),
                "Correlation to SPY": fmt_decimal(row["Correlation to SPY"]),
                "Effective Names": fmt_decimal(row["Effective Names"]),
                "Top-5 Weight Sum": fmt_decimal(row["Top-5 Weight Sum"]),
                "Average Daily Turnover": fmt_decimal(row["Average Daily Turnover"]),
                "Annualized Turnover": fmt_decimal(row["Annualized Turnover"]),
            }
        )
    write_csv(exhibits_dir / "hw5_q2c_portfolio_comparison.csv", comparison_export)

    summary_rows = [
        {"Item": "Q2(a) growth Pearson correlation", "Value": fmt_decimal(growth_summary["Growth Pearson Correlation"])},
        {"Item": "Q2(a) growth Spearman correlation", "Value": fmt_decimal(growth_summary["Growth Spearman Correlation"])},
        {"Item": "Q2(a) same-sign count", "Value": str(int(growth_summary["Same-Sign Count"]))},
        {"Item": "Q2(b) cumulative return", "Value": fmt_decimal(eq_metrics["Cumulative Return"])},
        {"Item": "Q2(b) annualized return", "Value": fmt_decimal(eq_metrics["Annualized Return"])},
        {"Item": "Q2(b) annualized volatility", "Value": fmt_decimal(eq_metrics["Annualized Volatility"])},
        {"Item": "Q2(b) Sharpe ratio", "Value": fmt_decimal(eq_metrics["Sharpe Ratio"])},
        {"Item": "Q2(b) max drawdown", "Value": fmt_decimal(eq_metrics["Max Drawdown"])},
        {"Item": "Q2(c) equal-weight minus GMV annualized return", "Value": fmt_decimal(eq_metrics["Annualized Return"] - result["gmv_metrics"]["Annualized Return"])},
        {"Item": "Q2(c) equal-weight minus GMV Sharpe ratio", "Value": fmt_decimal(eq_metrics["Sharpe Ratio"] - result["gmv_metrics"]["Sharpe Ratio"])},
    ]
    write_csv(exhibits_dir / "hw5_summary_metrics.csv", summary_rows)


def main() -> None:
    args = parse_args()
    if not args.prices_dir.exists():
        raise SystemExit(f"Price directory not found: {args.prices_dir}")

    all_stocks = ALL_STOCKS
    if args.workbook is not None:
        raise SystemExit(
            "The packaged HW5 analysis is self-contained and does not require a workbook. "
            "Omit --workbook."
        )

    result = build_analysis(args.prices_dir, all_stocks=all_stocks)
    export_exhibits(result, args.exhibits_dir)

    print("Rebuilt HW5 exhibits:")
    for name in (
        "hw5_q2a_growth_rates.csv",
        "hw5_q2a_growth_summary.csv",
        "hw5_q2b_equal_weight_metrics.csv",
        "hw5_q2c_portfolio_comparison.csv",
        "hw5_summary_metrics.csv",
    ):
        print(f" - {args.exhibits_dir / name}")


if __name__ == "__main__":
    main()
