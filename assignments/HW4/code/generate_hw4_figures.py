import math
from html import escape
from pathlib import Path

from hw4_analysis import (
    STOCKS,
    annualized_vols,
    build_analysis,
    corr,
    pairwise_corrs,
)

BASE = Path(__file__).resolve().parents[1]
FIGURES = BASE / "writeup" / "figures"

PALETTE = {
    "blue": "#1756a9",
    "green": "#2d8f5b",
    "orange": "#c9791a",
    "red": "#a83d3d",
    "gray": "#5f6975",
    "light": "#edf2f7",
    "grid": "#d7dde5",
    "text": "#243040",
    "muted": "#6b7280",
    "bg": "#ffffff",
}
def wealth_series(returns):
    wealth = []
    cur = 1.0
    for r in returns:
        cur *= 1.0 + r
        wealth.append(cur)
    return wealth


def metrics(xs):
    t = len(xs)
    m = sum(xs) / t
    var = variance(xs)
    vol = math.sqrt(var)
    cur = 1.0
    peak = 1.0
    mdd = 0.0
    for x in xs:
        cur *= 1.0 + x
        peak = max(peak, cur)
        mdd = min(mdd, cur / peak - 1.0)
    return {
        "obs": t,
        "cum": cur - 1.0,
        "ann_mean": 252.0 * m,
        "ann_vol": math.sqrt(252.0) * vol,
        "sharpe": (252.0 * m) / (math.sqrt(252.0) * vol),
        "mdd": mdd,
        "cagr": cur ** (252.0 / t) - 1.0,
    }
def fmt_pct(x):
    return f"{100.0 * x:.2f}%"


def svg_header(width, height):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{PALETTE["bg"]}"/>',
    ]


def svg_footer():
    return ["</svg>"]


def add_text(parts, x, y, text, size=16, weight="400", fill=None, anchor="start"):
    fill = fill or PALETTE["text"]
    parts.append(
        f'<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(text)}</text>'
    )


def add_line(parts, x1, y1, x2, y2, stroke, width=2, dash=None):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"{extra}/>'
    )


def add_rect(parts, x, y, width, height, fill, stroke="none", rx=0):
    parts.append(
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" rx="{rx}"/>'
    )


def add_polyline(parts, points, stroke, width=3, fill="none"):
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    parts.append(
        f'<polyline points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
        'stroke-linejoin="round" stroke-linecap="round"/>'
    )


def draw_line_chart(title, subtitle, series, path):
    width, height = 1200, 720
    left, right, top, bottom = 90, 40, 110, 80
    plot_w = width - left - right
    plot_h = height - top - bottom

    max_len = max(len(s["values"]) for s in series)
    ymin = min(min(s["values"]) for s in series)
    ymax = max(max(s["values"]) for s in series)
    pad = 0.05 * (ymax - ymin if ymax > ymin else 1.0)
    ymin -= pad
    ymax += pad

    def sx(i):
        if max_len == 1:
            return left
        return left + plot_w * i / (max_len - 1)

    def sy(v):
        return top + plot_h * (1.0 - (v - ymin) / (ymax - ymin))

    parts = svg_header(width, height)
    add_text(parts, left, 44, title, size=28, weight="700")
    add_text(parts, left, 72, subtitle, size=14, fill=PALETTE["muted"])

    for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
        val = ymin + frac * (ymax - ymin)
        y = sy(val)
        add_line(parts, left, y, left + plot_w, y, PALETTE["grid"], width=1)
        add_text(parts, left - 12, y + 5, f"{val:.2f}", size=12, fill=PALETTE["muted"], anchor="end")

    for frac, label in [(0.0, "0"), (0.25, "25%"), (0.5, "50%"), (0.75, "75%"), (1.0, "100%")]:
        x = left + plot_w * frac
        add_line(parts, x, top, x, top + plot_h, PALETTE["grid"], width=1)
        add_text(parts, x, top + plot_h + 26, label, size=12, fill=PALETTE["muted"], anchor="middle")

    add_line(parts, left, top, left, top + plot_h, PALETTE["gray"], width=1.5)
    add_line(parts, left, top + plot_h, left + plot_w, top + plot_h, PALETTE["gray"], width=1.5)

    for s in series:
        pts = [(sx(i), sy(v)) for i, v in enumerate(s["values"])]
        add_polyline(parts, pts, s["color"], width=3)

    legend_x = left + 20
    legend_y = height - 28
    step = 250
    for i, s in enumerate(series):
        x = legend_x + i * step
        add_line(parts, x, legend_y, x + 30, legend_y, s["color"], width=4)
        add_text(parts, x + 40, legend_y + 5, s["label"], size=14)

    with open(path, "w") as f:
        f.write("\n".join(parts + svg_footer()))


def draw_weights_chart(title, left_title, left_rows, right_title, right_rows, path):
    width, height = 1300, 860
    parts = svg_header(width, height)
    add_text(parts, 60, 44, title, size=28, weight="700")
    add_text(parts, 60, 72, "Nonzero weights only; weights sorted from largest to smallest.", size=14, fill=PALETTE["muted"])

    panels = [
        (60, 120, 520, 680, left_title, left_rows, PALETTE["blue"]),
        (700, 120, 520, 680, right_title, right_rows, PALETTE["green"]),
    ]

    for x0, y0, w, h, panel_title, rows, color in panels:
        add_text(parts, x0, y0 - 12, panel_title, size=18, weight="700")
        max_val = max(weight for _, weight in rows)
        bar_h = h / len(rows)
        for idx, (ticker, weight) in enumerate(rows):
            y = y0 + idx * bar_h + 4
            label_y = y + bar_h * 0.65
            add_text(parts, x0, label_y, ticker, size=12)
            bar_x = x0 + 72
            usable = w - 180
            bw = usable * weight / max_val
            add_rect(parts, bar_x, y, bw, bar_h * 0.7, color, rx=2)
            add_text(parts, bar_x + bw + 8, label_y, f"{weight:.4f}", size=12, fill=PALETTE["muted"])

    with open(path, "w") as f:
        f.write("\n".join(parts + svg_footer()))


def draw_dual_bar_chart(title, left_title, left_rows, right_title, right_rows, path):
    width, height = 1300, 760
    parts = svg_header(width, height)
    add_text(parts, 60, 44, title, size=28, weight="700")
    add_text(parts, 60, 72, "Compact summary of stability and estimated-versus-realized disappointment.", size=14, fill=PALETTE["muted"])

    panels = [
        (60, 120, 520, 520, left_title, left_rows, PALETTE["blue"]),
        (700, 120, 520, 520, right_title, right_rows, PALETTE["orange"]),
    ]

    for x0, y0, w, h, panel_title, rows, color in panels:
        add_text(parts, x0, y0 - 12, panel_title, size=18, weight="700")
        max_val = max(value for _, value in rows)
        n = len(rows)
        bar_w = (w - 40) / n
        for i, (label, value) in enumerate(rows):
            x = x0 + 20 + i * bar_w
            bh = h * value / max_val if max_val else 0
            y = y0 + h - bh
            add_rect(parts, x, y, bar_w * 0.6, bh, color, rx=2)
            add_text(parts, x + bar_w * 0.3, y - 8, f"{value:.5f}", size=12, fill=PALETTE["muted"], anchor="middle")
            add_text(parts, x + bar_w * 0.3, y0 + h + 20, label, size=12, fill=PALETTE["text"], anchor="middle")

        add_line(parts, x0, y0 + h, x0 + w, y0 + h, PALETTE["gray"], width=1.5)

    with open(path, "w") as f:
        f.write("\n".join(parts + svg_footer()))


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)

    result = build_analysis(BASE / "q1a_data" / "prices")
    r1 = result["r1"]
    r2 = result["r2"]
    w1 = result["w1"]
    w2 = result["w2"]
    beta_spy = result["beta_spy"]
    beta_voo = result["beta_voo"]
    rp2 = result["rp_second"]
    rg = result["rg"]
    hedge_spy = result["hedged_spy"]
    hedge_voo = result["hedged_voo"]

    nonzero1 = [(STOCKS[i], w1[i]) for i in range(len(STOCKS)) if w1[i] > 1e-12]
    nonzero2 = [(STOCKS[i], w2[i]) for i in range(len(STOCKS)) if w2[i] > 1e-12]
    nonzero1.sort(key=lambda x: x[1], reverse=True)
    nonzero2.sort(key=lambda x: x[1], reverse=True)

    wealth_d = wealth_series(rp2)
    wealth_g = wealth_series(rg)
    draw_line_chart(
        "Figure 1. Q1(d) vs Q1(g) Wealth Paths",
        "Normalized wealth over each evaluation window; x-axis is trading-day progress within the window.",
        [
            {"label": "Q1(d) True Out-of-Sample", "values": wealth_d, "color": PALETTE["blue"]},
            {"label": "Q1(g) Hypothetical Out-of-Sample", "values": wealth_g, "color": PALETTE["green"]},
        ],
        FIGURES / "hw4_figure_1_q1dg_wealth.svg",
    )

    draw_line_chart(
        "Figure 2. Q1(j) Hedge Comparison",
        f"Hedge ratios estimated from the first window: SPY {beta_spy:.5f}, VOO {beta_voo:.5f}.",
        [
            {"label": "Unhedged", "values": wealth_d, "color": PALETTE["blue"]},
            {"label": "SPY Hedge", "values": wealth_series(hedge_spy), "color": PALETTE["orange"]},
            {"label": "VOO Hedge", "values": wealth_series(hedge_voo), "color": PALETTE["green"]},
        ],
        FIGURES / "hw4_figure_2_q1j_hedge_wealth.svg",
    )

    draw_weights_chart(
        "Figure 3. GMV Portfolio Weights",
        "Q1(c) First-Window GMV",
        nonzero1,
        "Q1(f) Second-Window GMV",
        nonzero2,
        FIGURES / "hw4_figure_3_gmv_weights.svg",
    )

    vol1 = annualized_vols(r1)
    vol2 = annualized_vols(r2)
    mean1 = [252.0 * x for x in result["mu1"]]
    mean2 = [252.0 * x for x in result["mu2"]]
    frontier = result["sharpe_frontier"]
    stability_rows = [
        ("Vol", corr(vol1, vol2)),
        ("Pair Corr", corr(pairwise_corrs(r1), pairwise_corrs(r2))),
        ("Mean", corr(mean1, mean2)),
    ]
    frontier_rows = [
        ("Avg Gap", frontier["avg_gap"]),
        ("Low-Risk", frontier["low_gap"]),
        ("High-Risk", frontier["high_gap"]),
    ]
    draw_dual_bar_chart(
        "Figure 4. Sharpe-Style Replication Summary",
        "Stability Across Subperiods",
        stability_rows,
        "Estimated-minus-Realized Frontier Gaps",
        frontier_rows,
        FIGURES / "hw4_figure_4_sharpe_summary.svg",
    )


if __name__ == "__main__":
    main()
