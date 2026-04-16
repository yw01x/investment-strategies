#!/usr/bin/env python3

import argparse
import csv
import math
import os
import random
from pathlib import Path


STOCKS = [
    "AMZN", "ADBE", "CF", "DVN", "ALLE", "CALM", "DECK", "GOOG", "INCY", "META",
    "NEM", "NFLX", "NVDA", "PFE", "VC", "QCOM", "ANF", "ARLP", "BMY", "CAH",
    "CBT", "CGAU", "CPRX", "EOG", "EXEL", "GNTX", "HCA", "HRB", "ICLR", "JNJ",
    "MCK", "MGY", "ORCL", "PEGA", "PYPL", "RNR", "SYF", "TROW", "TSM", "UBER",
    "UHS", "YELP", "AAPL", "AMGN", "LLY", "MRK", "MSFT", "PEP", "UPS",
]

ETFS = ["SPY", "VOO"]


def load_adj_prices(prices_dir, ticker):
    out = {}
    path = prices_dir / f"{ticker}.csv"
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            out[row["date"]] = float(row["adjClose"])
    return out


def load_adj_returns(prices_dir, ticker):
    out = {}
    path = prices_dir / f"{ticker}.csv"
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        prev = None
        for row in reader:
            date = row["date"]
            adj = float(row["adjClose"])
            if prev is not None:
                out[date] = adj / prev - 1.0
            prev = adj
    return out


def means(rows):
    t = len(rows)
    n = len(rows[0])
    out = [0.0] * n
    for row in rows:
        for j, x in enumerate(row):
            out[j] += x
    return [x / t for x in out]


def cov_matrix(rows, mu):
    t = len(rows)
    n = len(mu)
    out = [[0.0] * n for _ in range(n)]
    for row in rows:
        d = [row[j] - mu[j] for j in range(n)]
        for i in range(n):
            di = d[i]
            for j in range(i, n):
                out[i][j] += di * d[j]
    denom = t - 1
    for i in range(n):
        for j in range(i, n):
            out[i][j] /= denom
            out[j][i] = out[i][j]
    return out


def matvec(matrix, vec):
    return [sum(matrix[i][j] * vec[j] for j in range(len(vec))) for i in range(len(matrix))]


def norm2(vec):
    return math.sqrt(sum(x * x for x in vec))


def dot(xs, ys):
    return sum(xs[i] * ys[i] for i in range(len(xs)))


def quad_form(weights, sigma):
    total = 0.0
    for i in range(len(weights)):
        wi = weights[i]
        for j in range(len(weights)):
            total += wi * sigma[i][j] * weights[j]
    return total


def proj_simplex(vec):
    u = sorted(vec, reverse=True)
    running = 0.0
    theta = 0.0
    for i, ui in enumerate(u, 1):
        running += ui
        if ui - (running - 1.0) / i > 0.0:
            theta = (running - 1.0) / i
    return [max(x - theta, 0.0) for x in vec]


def dominant_eigenvalue(sigma, power_iters=150):
    n = len(sigma)
    x = [1.0 / n] * n
    for _ in range(power_iters):
        y = matvec(sigma, x)
        y_norm = norm2(y)
        if y_norm == 0.0:
            return 0.0
        x = [yi / y_norm for yi in y]
    y = matvec(sigma, x)
    return max(dot(x, y), 0.0)


def solve_gmv(sigma, iters=100000, tol=1e-14):
    n = len(sigma)
    w = [1.0 / n] * n
    lam = dominant_eigenvalue(sigma)
    step = 1.0 / max(2.0 * lam, 1e-12)
    for _ in range(iters):
        grad = [2.0 * g for g in matvec(sigma, w)]
        nw = proj_simplex([w[i] - step * grad[i] for i in range(n)])
        if norm2([nw[i] - w[i] for i in range(n)]) < tol:
            w = nw
            break
        w = nw
    total = sum(w)
    return [0.0 if abs(x / total) < 1e-14 else x / total for x in w]


def solve_mean_variance(mu, sigma, gamma, initial=None, iters=6000, tol=1e-10):
    n = len(mu)
    w = initial[:] if initial is not None else [1.0 / n] * n
    lam = dominant_eigenvalue(sigma)
    step = 1.0 / max(2.0 * gamma * lam + 1e-8, 1e-8)
    for _ in range(iters):
        sigma_w = matvec(sigma, w)
        grad = [2.0 * gamma * sigma_w[i] - mu[i] for i in range(n)]
        nw = proj_simplex([w[i] - step * grad[i] for i in range(n)])
        if norm2([nw[i] - w[i] for i in range(n)]) < tol:
            w = nw
            break
        w = nw
    total = sum(w)
    return [0.0 if abs(x / total) < 1e-14 else x / total for x in w]


def portfolio_returns(rows, weights):
    return [sum(row[j] * weights[j] for j in range(len(weights))) for row in rows]


def variance(xs):
    mu = sum(xs) / len(xs)
    return sum((x - mu) * (x - mu) for x in xs) / (len(xs) - 1)


def covariance(xs, ys):
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    return sum((xs[i] - mx) * (ys[i] - my) for i in range(len(xs))) / (len(xs) - 1)


def corr(xs, ys):
    return covariance(xs, ys) / math.sqrt(variance(xs) * variance(ys))


def metrics(xs):
    t = len(xs)
    avg = sum(xs) / t
    var = variance(xs)
    vol = math.sqrt(var)
    wealth = 1.0
    peak = 1.0
    mdd = 0.0
    for x in xs:
        wealth *= 1.0 + x
        peak = max(peak, wealth)
        mdd = min(mdd, wealth / peak - 1.0)
    return {
        "obs": t,
        "cum": wealth - 1.0,
        "ann_mean": 252.0 * avg,
        "ann_vol": math.sqrt(252.0) * vol,
        "sharpe": (252.0 * avg) / (math.sqrt(252.0) * vol),
        "mdd": mdd,
        "cagr": wealth ** (252.0 / t) - 1.0,
    }


def annualized_vols(rows):
    mu = means(rows)
    return [
        math.sqrt(252.0 * sum((row[j] - mu[j]) ** 2 for row in rows) / (len(rows) - 1))
        for j in range(len(mu))
    ]


def pairwise_corrs(rows):
    cols = list(zip(*rows))
    out = []
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            out.append(corr(cols[i], cols[j]))
    return out


def annualized_portfolio_stats(weights, mu, sigma):
    ann_mean = 252.0 * dot(weights, mu)
    ann_vol = math.sqrt(252.0 * quad_form(weights, sigma))
    return ann_mean, ann_vol


def frontier_diagnostics(mu_est, sigma_est, mu_real, sigma_real, count=21):
    # Descend in risk aversion from GMV-like to aggressive allocations.
    gammas = [10 ** (6.0 - 12.0 * i / (count - 1)) for i in range(count)]
    rows = []
    current = None
    for gamma in gammas:
        weights = solve_mean_variance(mu_est, sigma_est, gamma, initial=current)
        current = weights
        est_mean, est_vol = annualized_portfolio_stats(weights, mu_est, sigma_est)
        real_mean, real_vol = annualized_portfolio_stats(weights, mu_real, sigma_real)
        rows.append({
            "gamma": gamma,
            "est_mean": est_mean,
            "est_vol": est_vol,
            "real_mean": real_mean,
            "real_vol": real_vol,
            "gap": est_mean - real_mean,
            "weights": weights,
        })

    avg_gap = sum(row["gap"] for row in rows) / len(rows)
    low_split = max(len(rows) // 2, 1)
    low_gap = sum(row["gap"] for row in rows[:low_split]) / low_split
    high_gap = sum(row["gap"] for row in rows[low_split:]) / (len(rows) - low_split)
    under_count = sum(1 for row in rows if row["real_mean"] < row["est_mean"])
    return {
        "rows": rows,
        "avg_gap": avg_gap,
        "low_gap": low_gap,
        "high_gap": high_gap,
        "under_count": under_count,
    }


def monte_carlo_q2(draws=100000, seed=0):
    rng = random.Random(seed)
    mu_M = 0.00050
    sigma_M = 0.02000
    beta_X = 0.80000
    beta_Y = 1.20000
    sigma_X = 0.03000
    sigma_Y = 0.01500

    r_x = []
    r_y = []
    for _ in range(draws):
        r_m = rng.gauss(mu_M, sigma_M)
        eps_x = rng.gauss(0.0, sigma_X)
        eps_y = rng.gauss(0.0, sigma_Y)
        r_x.append(beta_X * r_m + eps_x)
        r_y.append(beta_Y * r_m + eps_y)

    beta_claim = -beta_Y / beta_X
    beta_star = -(beta_Y * beta_X * sigma_M ** 2) / (beta_X ** 2 * sigma_M ** 2 + sigma_X ** 2)
    return {
        "mu_M": mu_M,
        "sigma_M": sigma_M,
        "beta_X": beta_X,
        "beta_Y": beta_Y,
        "sigma_X": sigma_X,
        "sigma_Y": sigma_Y,
        "beta_claim": beta_claim,
        "beta_star": beta_star,
        "var_unhedged": variance(r_y),
        "var_claim": variance([r_y[i] + beta_claim * r_x[i] for i in range(draws)]),
        "var_star": variance([r_y[i] + beta_star * r_x[i] for i in range(draws)]),
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def format_pct(x):
    return f"{100.0 * x:.5f}%"


def build_analysis(prices_dir):
    prices = {ticker: load_adj_prices(prices_dir, ticker) for ticker in STOCKS + ETFS}
    rets = {ticker: load_adj_returns(prices_dir, ticker) for ticker in STOCKS + ETFS}

    first_dates = sorted(d for d in rets[STOCKS[0]].keys() if d <= "2023-04-12")
    second_dates = sorted(d for d in rets[STOCKS[0]].keys() if d >= "2023-04-13")
    for ticker in STOCKS + ETFS:
        first_dates = [d for d in first_dates if d in rets[ticker]]
        second_dates = [d for d in second_dates if d in rets[ticker]]

    r1 = [[rets[ticker][d] for ticker in STOCKS] for d in first_dates]
    r2 = [[rets[ticker][d] for ticker in STOCKS] for d in second_dates]
    mu1 = means(r1)
    mu2 = means(r2)
    sigma1 = cov_matrix(r1, mu1)
    sigma2 = cov_matrix(r2, mu2)
    w1 = solve_gmv(sigma1)
    w2 = solve_gmv(sigma2)

    rp_first = portfolio_returns(r1, w1)
    rp_second = portfolio_returns(r2, w1)
    rg = portfolio_returns(r1, w2)

    spy_first = [rets["SPY"][d] for d in first_dates]
    spy_second = [rets["SPY"][d] for d in second_dates]
    voo_first = [rets["VOO"][d] for d in first_dates]
    voo_second = [rets["VOO"][d] for d in second_dates]

    beta_spy = -covariance(rp_first, spy_first) / variance(spy_first)
    beta_voo = -covariance(rp_first, voo_first) / variance(voo_first)

    hedged_spy = [rp_second[i] + beta_spy * spy_second[i] for i in range(len(rp_second))]
    hedged_voo = [rp_second[i] + beta_voo * voo_second[i] for i in range(len(rp_second))]

    sharpe_frontier = frontier_diagnostics(mu1, sigma1, mu2, sigma2)
    q2 = monte_carlo_q2()

    return {
        "prices": prices,
        "returns": rets,
        "first_dates": first_dates,
        "second_dates": second_dates,
        "r1": r1,
        "r2": r2,
        "mu1": mu1,
        "mu2": mu2,
        "sigma1": sigma1,
        "sigma2": sigma2,
        "w1": w1,
        "w2": w2,
        "rp_first": rp_first,
        "rp_second": rp_second,
        "rg": rg,
        "beta_spy": beta_spy,
        "beta_voo": beta_voo,
        "hedged_spy": hedged_spy,
        "hedged_voo": hedged_voo,
        "metrics_d": metrics(rp_second),
        "metrics_g": metrics(rg),
        "metrics_spy": metrics(hedged_spy),
        "metrics_voo": metrics(hedged_voo),
        "sharpe_frontier": sharpe_frontier,
        "q2": q2,
    }


def export_exhibits(result, exhibits_dir):
    amzn_dates = ["2020-04-13", "2020-04-14", "2020-04-15"]
    amzn_prices = result["prices"]["AMZN"]
    amzn_rows = []
    prev = None
    for date in amzn_dates:
        px = amzn_prices[date]
        row = {"Date": date, "Adj Close": f"{px:.4f}"}
        if prev is None:
            row["Return"] = ""
        else:
            row["Return"] = f"{(px / prev - 1.0):.6f}"
        prev = px
        amzn_rows.append(row)
    write_csv(exhibits_dir / "hw4_q1b_amzn_return_example.csv", amzn_rows)

    parameter_rows = [
        {
            "Window": "First Three Years",
            "Return Start": result["first_dates"][0],
            "Return End": result["first_dates"][-1],
            "Stocks Used": len(STOCKS),
            "Observations": len(result["first_dates"]),
            "Mean Vector Size": f"{len(STOCKS)} x 1",
            "Covariance Matrix Size": f"{len(STOCKS)} x {len(STOCKS)}",
        },
        {
            "Window": "Last Three Years",
            "Return Start": result["second_dates"][0],
            "Return End": result["second_dates"][-1],
            "Stocks Used": len(STOCKS),
            "Observations": len(result["second_dates"]),
            "Mean Vector Size": f"{len(STOCKS)} x 1",
            "Covariance Matrix Size": f"{len(STOCKS)} x {len(STOCKS)}",
        },
    ]
    write_csv(exhibits_dir / "hw4_q1b_parameter_summary.csv", parameter_rows)

    nonzero_c = [
        {"Ticker": STOCKS[i], "Weight": f"{result['w1'][i]:.8f}"}
        for i in range(len(STOCKS))
        if result["w1"][i] > 1e-12
    ]
    nonzero_f = [
        {"Ticker": STOCKS[i], "Weight": f"{result['w2'][i]:.8f}"}
        for i in range(len(STOCKS))
        if result["w2"][i] > 1e-12
    ]
    nonzero_c.sort(key=lambda row: float(row["Weight"]), reverse=True)
    nonzero_f.sort(key=lambda row: float(row["Weight"]), reverse=True)
    write_csv(exhibits_dir / "hw4_q1c_gmv_weights_nonzero.csv", nonzero_c)
    write_csv(exhibits_dir / "hw4_q1f_gmv_weights_nonzero.csv", nonzero_f)

    metrics_d = result["metrics_d"]
    metrics_g = result["metrics_g"]
    metrics_spy = result["metrics_spy"]
    metrics_voo = result["metrics_voo"]
    q2 = result["q2"]

    summary_rows = [
        {"Item": "Primary data source", "Value": "Tiingo"},
        {"Item": "Q1(d) cumulative return", "Value": format_pct(metrics_d["cum"])},
        {"Item": "Q1(d) annualized return", "Value": format_pct(metrics_d["ann_mean"])},
        {"Item": "Q1(d) annualized volatility", "Value": format_pct(metrics_d["ann_vol"])},
        {"Item": "Q1(d) Sharpe ratio", "Value": f"{metrics_d['sharpe']:.5f}"},
        {"Item": "Q1(g) cumulative return", "Value": format_pct(metrics_g["cum"])},
        {"Item": "Q1(g) annualized return", "Value": format_pct(metrics_g["ann_mean"])},
        {"Item": "Q1(g) annualized volatility", "Value": format_pct(metrics_g["ann_vol"])},
        {"Item": "Q1(g) Sharpe ratio", "Value": f"{metrics_g['sharpe']:.5f}"},
        {"Item": "Q1(i) SPY hedge ratio", "Value": f"{result['beta_spy']:.8f}"},
        {"Item": "Q1(i) VOO hedge ratio", "Value": f"{result['beta_voo']:.8f}"},
        {
            "Item": "Q1(j) SPY variance reduction",
            "Value": format_pct(1.0 - variance(result["hedged_spy"]) / variance(result["rp_second"])),
        },
        {
            "Item": "Q1(j) VOO variance reduction",
            "Value": format_pct(1.0 - variance(result["hedged_voo"]) / variance(result["rp_second"])),
        },
        {"Item": "Q2 claimed hedge ratio", "Value": f"{q2['beta_claim']:.5f}"},
        {"Item": "Q2 optimal hedge ratio", "Value": f"{q2['beta_star']:.5f}"},
    ]
    write_csv(exhibits_dir / "hw4_summary_metrics.csv", summary_rows)

    hedge_rows = []
    for label, metric in [
        ("Unhedged", metrics_d),
        ("SPY Hedge", metrics_spy),
        ("VOO Hedge", metrics_voo),
    ]:
        hedge_rows.append({
            "Portfolio": label,
            "Cumulative Return": format_pct(metric["cum"]),
            "Annualized Return": format_pct(metric["ann_mean"]),
            "Annualized Volatility": format_pct(metric["ann_vol"]),
            "Sharpe Ratio": f"{metric['sharpe']:.5f}",
            "Max Drawdown": format_pct(metric["mdd"]),
        })
    write_csv(exhibits_dir / "hw4_q1j_hedge_performance.csv", hedge_rows)

    frontier = result["sharpe_frontier"]
    sharpe_rows = [
        {"Metric": "Volatility Stability Corr", "Value": f"{corr(annualized_vols(result['r1']), annualized_vols(result['r2'])):.5f}"},
        {"Metric": "Pairwise Correlation Stability Corr", "Value": f"{corr(pairwise_corrs(result['r1']), pairwise_corrs(result['r2'])):.5f}"},
        {"Metric": "Mean Return Stability Corr", "Value": f"{corr([252.0 * x for x in result['mu1']], [252.0 * x for x in result['mu2']]):.5f}"},
        {"Metric": "Average Estimated-minus-Realized Return Gap", "Value": format_pct(frontier['avg_gap'])},
        {"Metric": "Low-Risk Frontier Gap", "Value": format_pct(frontier['low_gap'])},
        {"Metric": "High-Risk Frontier Gap", "Value": format_pct(frontier['high_gap'])},
        {"Metric": "Frontier Portfolios with Realized Return Below Estimate", "Value": frontier["under_count"]},
    ]
    write_csv(exhibits_dir / "hw4_q1k_sharpe_replication_summary.csv", sharpe_rows)

    q2_rows = [{
        "mu_M": f"{q2['mu_M']:.5f}",
        "sigma_M": f"{q2['sigma_M']:.5f}",
        "beta_X": f"{q2['beta_X']:.5f}",
        "beta_Y": f"{q2['beta_Y']:.5f}",
        "sigma_X": f"{q2['sigma_X']:.5f}",
        "sigma_Y": f"{q2['sigma_Y']:.5f}",
        "beta_claim": f"{q2['beta_claim']:.5f}",
        "beta_star": f"{q2['beta_star']:.5f}",
        "var_unhedged": f"{q2['var_unhedged']:.8f}",
        "var_claim": f"{q2['var_claim']:.8f}",
        "var_star": f"{q2['var_star']:.8f}",
    }]
    write_csv(exhibits_dir / "hw4_q2_monte_carlo_summary.csv", q2_rows)


def parse_args():
    base = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Rebuild HW4 calculation exhibits from Tiingo price CSVs.")
    parser.add_argument(
        "--prices-dir",
        default=str(base / "q1a_data" / "prices"),
        help="Directory containing per-ticker Tiingo CSV files.",
    )
    parser.add_argument(
        "--exhibits-dir",
        default=str(base / "exhibits"),
        help="Directory where exhibit CSV files should be written.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    prices_dir = Path(args.prices_dir)
    exhibits_dir = Path(args.exhibits_dir)

    if not prices_dir.exists():
        raise SystemExit(
            f"Price directory not found: {prices_dir}\n"
            "Run download_hw4_q1a_data.py first, or pass --prices-dir to an existing local dataset."
        )

    result = build_analysis(prices_dir)
    export_exhibits(result, exhibits_dir)

    print("Rebuilt HW4 exhibits:")
    for name in [
        "hw4_q1b_amzn_return_example.csv",
        "hw4_q1b_parameter_summary.csv",
        "hw4_q1c_gmv_weights_nonzero.csv",
        "hw4_q1f_gmv_weights_nonzero.csv",
        "hw4_summary_metrics.csv",
        "hw4_q1j_hedge_performance.csv",
        "hw4_q1k_sharpe_replication_summary.csv",
        "hw4_q2_monte_carlo_summary.csv",
    ]:
        print(f" - {exhibits_dir / name}")


if __name__ == "__main__":
    main()
