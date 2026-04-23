#!/usr/bin/env python3
"""Generate SVG figures for the Investment Strategy HW5 write-up."""

from __future__ import annotations

from html import escape
from pathlib import Path

from hw5_analysis import build_analysis


BASE = Path(__file__).resolve().parents[1]
FIGURES = BASE / "writeup" / "figures"

PALETTE = {
    "blue": "#1756a9",
    "green": "#2d8f5b",
    "orange": "#c9791a",
    "red": "#a83d3d",
    "gray": "#5f6975",
    "grid": "#d7dde5",
    "text": "#243040",
    "muted": "#6b7280",
    "bg": "#ffffff",
    "light": "#edf2f7",
}


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{PALETTE["bg"]}"/>',
    ]


def svg_footer() -> list[str]:
    return ["</svg>"]


def add_text(parts: list[str], x: float, y: float, text: str, size: int = 16, weight: str = "400",
             fill: str | None = None, anchor: str = "start") -> None:
    parts.append(
        f'<text x="{x}" y="{y}" font-family="Helvetica, Arial, sans-serif" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill or PALETTE["text"]}" text-anchor="{anchor}">{escape(text)}</text>'
    )


def add_line(parts: list[str], x1: float, y1: float, x2: float, y2: float, stroke: str,
             width: float = 2.0, dash: str | None = None) -> None:
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    parts.append(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"{extra}/>'
    )


def add_rect(parts: list[str], x: float, y: float, width: float, height: float, fill: str,
             stroke: str = "none", rx: float = 0.0) -> None:
    parts.append(
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" rx="{rx}"/>'
    )


def add_circle(parts: list[str], cx: float, cy: float, r: float, fill: str, stroke: str = "none") -> None:
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}"/>')


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def draw_growth_scatter(result: dict[str, object], path: Path) -> None:
    rows = result["growth_rows"]
    width, height = 1100, 760
    left, right, top, bottom = 110, 70, 110, 110
    plot_w = width - left - right
    plot_h = height - top - bottom

    xs = [row["FirstPeriodCAGR"] for row in rows]
    ys = [row["SecondPeriodCAGR"] for row in rows]
    lo = min(min(xs), min(ys))
    hi = max(max(xs), max(ys))
    pad = 0.08 * (hi - lo if hi > lo else 1.0)
    lo -= pad
    hi += pad

    def sx(value: float) -> float:
        return left + plot_w * (value - lo) / (hi - lo)

    def sy(value: float) -> float:
        return top + plot_h * (1.0 - (value - lo) / (hi - lo))

    parts = svg_header(width, height)
    add_text(parts, left, 42, "Figure 1. Growth-Rate Stability Across the Two 3-Year Windows", size=28, weight="700")
    add_text(parts, left, 72, "Each dot is one stock. The dashed diagonal is the line of perfect stability.", size=14, fill=PALETTE["muted"])

    ticks = [lo + (hi - lo) * frac / 4.0 for frac in range(5)]
    for tick in ticks:
        x = sx(tick)
        y = sy(tick)
        add_line(parts, left, y, left + plot_w, y, PALETTE["grid"], width=1)
        add_line(parts, x, top, x, top + plot_h, PALETTE["grid"], width=1)
        add_text(parts, left - 14, y + 5, pct(tick), size=12, fill=PALETTE["muted"], anchor="end")
        add_text(parts, x, top + plot_h + 28, pct(tick), size=12, fill=PALETTE["muted"], anchor="middle")

    add_line(parts, left, top + plot_h, left + plot_w, top, PALETTE["gray"], width=2, dash="6 6")
    add_line(parts, left, top, left, top + plot_h, PALETTE["gray"], width=1.5)
    add_line(parts, left, top + plot_h, left + plot_w, top + plot_h, PALETTE["gray"], width=1.5)

    for row in rows:
        color = PALETTE["green"] if row["Difference"] >= 0 else PALETTE["orange"]
        add_circle(parts, sx(row["FirstPeriodCAGR"]), sy(row["SecondPeriodCAGR"]), 5.5, color)

    notable = sorted(rows, key=lambda row: abs(row["Difference"]), reverse=True)[:8]
    for row in notable:
        x = sx(row["FirstPeriodCAGR"])
        y = sy(row["SecondPeriodCAGR"])
        add_text(parts, x + 8, y - 8, row["Ticker"], size=12, fill=PALETTE["text"])

    add_text(parts, left + plot_w / 2, height - 34, "First-period annualized stock growth (CAGR)", size=14, anchor="middle")
    add_text(parts, 28, top + plot_h / 2, "Second-period annualized stock growth (CAGR)", size=14, fill=PALETTE["text"], anchor="middle")
    parts.append(
        f'<g transform="translate(28,{top + plot_h / 2}) rotate(-90)"></g>'
    )
    # Visible rotated label
    parts.append(
        f'<text x="28" y="{top + plot_h / 2}" font-family="Helvetica, Arial, sans-serif" font-size="14" '
        f'fill="{PALETTE["text"]}" text-anchor="middle" transform="rotate(-90 28 {top + plot_h / 2})">Second-period annualized stock growth (CAGR)</text>'
    )

    legend_y = height - 68
    add_circle(parts, left, legend_y, 5.5, PALETTE["green"])
    add_text(parts, left + 14, legend_y + 5, "Improved versus first period", size=13)
    add_circle(parts, left + 250, legend_y, 5.5, PALETTE["orange"])
    add_text(parts, left + 264, legend_y + 5, "Deteriorated versus first period", size=13)

    with open(path, "w") as handle:
        handle.write("\n".join(parts + svg_footer()))


def draw_portfolio_comparison(result: dict[str, object], path: Path) -> None:
    rows = result["comparison_rows"]
    eq_row = rows[0]
    gmv_row = rows[1]

    width, height = 1280, 820
    parts = svg_header(width, height)
    add_text(parts, 60, 42, "Figure 2. Equal-Weight vs. HW4 GMV Portfolio", size=28, weight="700")
    add_text(parts, 60, 72, "Second 3-year evaluation window. Green means 'more' and orange means 'more defensive / lower'.", size=14, fill=PALETTE["muted"])

    add_rect(parts, 60, 110, 520, 640, PALETTE["light"], rx=18)
    add_rect(parts, 640, 110, 580, 640, PALETTE["light"], rx=18)
    add_text(parts, 90, 145, "Performance", size=20, weight="700")
    add_text(parts, 670, 145, "Risk, Market Exposure, and Implementation", size=20, weight="700")

    left_metrics = [
        ("Cumulative Return", eq_row["Cumulative Return"], gmv_row["Cumulative Return"], True),
        ("Annualized Return", eq_row["Annualized Return"], gmv_row["Annualized Return"], True),
        ("Sharpe Ratio", eq_row["Sharpe Ratio"], gmv_row["Sharpe Ratio"], True),
        ("CAGR", eq_row["CAGR"], gmv_row["CAGR"], True),
    ]
    right_metrics = [
        ("Annualized Volatility", eq_row["Annualized Volatility"], gmv_row["Annualized Volatility"], False),
        ("Max Drawdown Magnitude", abs(eq_row["Max Drawdown"]), abs(gmv_row["Max Drawdown"]), False),
        ("Beta to SPY", eq_row["Beta to SPY"], gmv_row["Beta to SPY"], False),
        ("Annualized Turnover", eq_row["Annualized Turnover"], gmv_row["Annualized Turnover"], False),
        ("Top-5 Weight Sum", eq_row["Top-5 Weight Sum"], gmv_row["Top-5 Weight Sum"], False),
    ]

    def draw_metric_block(x0: float, y0: float, label: str, eq_value: float, gmv_value: float, higher_is_better: bool) -> None:
        add_text(parts, x0, y0, label, size=14, weight="700")
        max_value = max(eq_value, gmv_value, 1e-12)
        bar_x = x0
        bar_y = y0 + 18
        bar_w = 420
        bar_h = 22
        add_rect(parts, bar_x, bar_y, bar_w, bar_h, "#ffffff", stroke=PALETTE["grid"], rx=8)
        add_rect(parts, bar_x, bar_y, bar_w * eq_value / max_value, bar_h, PALETTE["green"], rx=8)
        add_rect(parts, bar_x, bar_y + 36, bar_w, bar_h, "#ffffff", stroke=PALETTE["grid"], rx=8)
        add_rect(parts, bar_x, bar_y + 36, bar_w * gmv_value / max_value, bar_h, PALETTE["orange"], rx=8)
        add_text(parts, bar_x + bar_w + 14, bar_y + 16, f"EW: {eq_value:.4f}", size=13, fill=PALETTE["text"])
        add_text(parts, bar_x + bar_w + 14, bar_y + 52, f"GMV: {gmv_value:.4f}", size=13, fill=PALETTE["text"])
        winner = "Equal Weight" if (eq_value >= gmv_value if higher_is_better else eq_value <= gmv_value) else "HW4 GMV"
        add_text(parts, bar_x, bar_y + 78, f"Preferred on this metric: {winner}", size=12, fill=PALETTE["muted"])

    y = 190
    for label, eq_value, gmv_value, higher_is_better in left_metrics:
        draw_metric_block(90, y, label, eq_value, gmv_value, higher_is_better)
        y += 125

    y = 190
    for label, eq_value, gmv_value, higher_is_better in right_metrics:
        draw_metric_block(670, y, label, eq_value, gmv_value, higher_is_better)
        y += 105

    add_text(parts, 90, 722, "Green bars: daily rebalanced 50-stock equal-weight portfolio", size=13, fill=PALETTE["muted"])
    add_text(parts, 90, 744, "Orange bars: fixed-weight HW4 global minimum-variance portfolio", size=13, fill=PALETTE["muted"])

    with open(path, "w") as handle:
        handle.write("\n".join(parts + svg_footer()))


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    result = build_analysis(BASE / "data" / "tiingo_prices")
    draw_growth_scatter(result, FIGURES / "hw5_figure_1_growth_scatter.svg")
    draw_portfolio_comparison(result, FIGURES / "hw5_figure_2_portfolio_comparison.svg")
    print("Generated HW5 figures:")
    print(f" - {FIGURES / 'hw5_figure_1_growth_scatter.svg'}")
    print(f" - {FIGURES / 'hw5_figure_2_portfolio_comparison.svg'}")


if __name__ == "__main__":
    main()
