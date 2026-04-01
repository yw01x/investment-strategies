const MIN_SLIDER_VALUE = 100;
const MAX_SLIDER_VALUE = 5000;
const DEFAULT_SLIDER_VALUE = 830;
const X_TICKS = [0.01, 0.1, 0.2, 0.3, 0.4, 0.5];

const FORMULAS = [
  {
    id: "exact",
    label: "Exact",
    formulaText: "n = ln(2) / ln(1 + r)",
    approxText: "No approximation. This is the reference curve obtained directly from (1+r)^n = 2.",
    color: "#1f77b4",
    marker: "circle",
    lineDash: [],
    lineWidth: 3.6,
    isReference: true,
    compute: (r) => Math.log(2) / Math.log(1 + r),
  },
  {
    id: "approx1",
    label: "Approx 1",
    formulaText: "n = 69 / (100r)",
    approxText: "Equivalent to 0.69 / r. Writing it as 69 / (100r) makes it directly comparable to 72 / (100r).",
    color: "#ff7f0e",
    marker: "diamond",
    lineDash: [12, 8],
    lineWidth: 2.8,
    compute: (r) => 0.69 / r,
  },
  {
    id: "approx2",
    label: "Approx 2",
    formulaText: "n = 69 / (100(r - r^2 / 2))",
    approxText: "Equivalent to 0.69 / (r - r^2 / 2). The 69 / 100 form makes comparison with Rule of 72 easier.",
    color: "#2ca02c",
    marker: "square",
    lineDash: [7, 5],
    lineWidth: 2.8,
    compute: (r) => 0.69 / (r - (r * r) / 2),
  },
  {
    id: "approx3",
    label: "Approx 3",
    formulaText: "n = 70 / (100(r - r^2 / 2))",
    approxText: "Equivalent to 0.70 / (r - r^2 / 2). The numerator becomes the integer 70, which lines up cleanly against 72.",
    color: "#d62728",
    marker: "triangle",
    lineDash: [3, 5],
    lineWidth: 2.8,
    compute: (r) => 0.70 / (r - (r * r) / 2),
  },
  {
    id: "approx4",
    label: "Approx 4",
    formulaText: "n = 6931 / (10000(r - r^2 / 2))",
    approxText: "Equivalent to 0.6931 / (r - r^2 / 2). Keeping the numerator integer requires 6931 / 10000, so this one is the exception to the 100-denominator comparison form.",
    color: "#9467bd",
    marker: "oval",
    lineDash: [14, 5, 2, 5],
    lineWidth: 2.8,
    compute: (r) => 0.6931 / (r - (r * r) / 2),
  },
  {
    id: "rule72",
    label: "Rule of 72",
    formulaText: "n = 72 / (100r)",
    approxText: "Rule-of-thumb shortcut. It is not derived by reusing the exact logarithm expression directly.",
    color: "#8c564b",
    marker: "cross",
    lineDash: [18, 7],
    lineWidth: 2.8,
    compute: (r) => 72 / (100 * r),
  },
];

const ERROR_FORMULAS = FORMULAS.filter((formula) => !formula.isReference);

const state = {
  sliderValue: DEFAULT_SLIDER_VALUE,
};

const canvas = document.getElementById("chartCanvas");
const slider = document.getElementById("rateSlider");
const rateInput = document.getElementById("rateInput");
const rateOutput = document.getElementById("rateOutput");
const formulaCards = document.getElementById("formulaCards");
const legendList = document.getElementById("legendList");
const downloadButton = document.getElementById("downloadButton");

const sampleRates = buildSampleRates();
const sampledValues = buildSampledValues();
const sampledErrors = buildSampledErrors(sampledValues);
const chartBounds = {
  xMin: sampleRates[0],
  xMax: sampleRates[sampleRates.length - 1],
  main: {
    yMin: 0,
    yMax: computeMainMax(sampledValues),
  },
  error: computeErrorBounds(sampledErrors),
};

renderLegend();
updateAll();

slider.addEventListener("input", () => {
  setSliderValue(Number(slider.value));
});

rateInput.addEventListener("input", () => {
  if (rateInput.value === "") {
    return;
  }

  const parsedValue = Number(rateInput.value);
  if (!Number.isFinite(parsedValue)) {
    return;
  }

  setRate(parsedValue);
});

rateInput.addEventListener("blur", () => {
  rateInput.value = formatDecimal(sliderValueToRate(state.sliderValue));
});

downloadButton.addEventListener("click", () => {
  const link = document.createElement("a");
  link.href = canvas.toDataURL("image/png");
  link.download = "rule_of_72_comparison_web.png";
  link.click();
});

window.addEventListener("resize", updateChart);

function updateAll() {
  const rate = sliderValueToRate(state.sliderValue);
  const values = calculateValues(rate);
  const errors = calculateErrors(values);

  slider.value = String(state.sliderValue);
  rateInput.value = formatDecimal(rate);
  rateOutput.textContent = `r = ${formatDecimal(rate)} (${formatPercent(rate)})`;
  slider.style.setProperty("--fill-percent", `${sliderPercent(state.sliderValue).toFixed(2)}%`);
  renderFormulaCards(values, errors);
  updateChart(values, errors);
}

function updateChart(currentValues, currentErrors) {
  const rect = canvas.getBoundingClientRect();
  const cssWidth = Math.max(360, Math.floor(rect.width || canvas.parentElement.clientWidth || 920));
  const cssHeight = cssWidth < 680 ? Math.round(cssWidth * 1.12) : Math.round(cssWidth * 0.88);
  const dpr = window.devicePixelRatio || 1;

  canvas.width = Math.floor(cssWidth * dpr);
  canvas.height = Math.floor(cssHeight * dpr);
  canvas.style.height = `${cssHeight}px`;

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  drawChart(ctx, cssWidth, cssHeight, currentValues, currentErrors);
}

function drawChart(ctx, width, height, currentValues, currentErrors) {
  const layout = buildPlotLayout(width, height);
  const mainTicks = createTicks(chartBounds.main.yMin, chartBounds.main.yMax, 6);
  const errorTicks = createTicks(chartBounds.error.yMin, chartBounds.error.yMax, 5);
  const rate = sliderValueToRate(state.sliderValue);

  ctx.clearRect(0, 0, width, height);
  drawOuterCanvas(ctx, width, height);

  drawPlotBackground(ctx, layout.main, "Doubling-Time Curves");
  drawPlotBackground(ctx, layout.error, "Percent Error vs Exact");

  drawGrid(ctx, layout.main, chartBounds.main, mainTicks, false);
  drawGrid(ctx, layout.error, chartBounds.error, errorTicks, true);
  drawAxes(ctx, layout.main, chartBounds.main, mainTicks, false, "n (doubling time)");
  drawAxes(ctx, layout.error, chartBounds.error, errorTicks, true, "percent error", "r (interest rate)");

  drawSelectionGuide(ctx, layout.main, rate);
  drawSelectionGuide(ctx, layout.error, rate);
  drawZeroLine(ctx, layout.error);

  for (const formula of FORMULAS) {
    drawSeries(ctx, layout.main, sampledValues[formula.id], formula, chartBounds.main);
  }

  for (const formula of ERROR_FORMULAS) {
    drawSeries(ctx, layout.error, sampledErrors[formula.id], formula, chartBounds.error);
  }

  for (const formula of FORMULAS) {
    drawMarker(
      ctx,
      formula.marker,
      scaleX(rate, layout.main, chartBounds),
      scaleY(currentValues[formula.id], layout.main, chartBounds.main),
      formula.color
    );
  }

  for (const formula of ERROR_FORMULAS) {
    drawMarker(
      ctx,
      formula.marker,
      scaleX(rate, layout.error, chartBounds),
      scaleY(currentErrors[formula.id], layout.error, chartBounds.error),
      formula.color
    );
  }
}

function buildPlotLayout(width, height) {
  const frame = {
    left: width < 700 ? 70 : 84,
    right: width < 700 ? 20 : 28,
    top: 26,
    bottom: 50,
  };

  const plotWidth = width - frame.left - frame.right;
  const totalHeight = height - frame.top - frame.bottom;
  const gap = width < 700 ? 52 : 60;
  const mainHeight = Math.round((totalHeight - gap) * 0.62);
  const errorHeight = totalHeight - gap - mainHeight;

  return {
    main: {
      x: frame.left,
      y: frame.top,
      width: plotWidth,
      height: mainHeight,
    },
    error: {
      x: frame.left,
      y: frame.top + mainHeight + gap,
      width: plotWidth,
      height: errorHeight,
    },
  };
}

function drawOuterCanvas(ctx, width, height) {
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, "#ffffff");
  gradient.addColorStop(1, "#f7f5ef");
  ctx.fillStyle = gradient;
  roundRect(ctx, 0, 0, width, height, 18);
  ctx.fill();
}

function drawPlotBackground(ctx, plot, title) {
  const gradient = ctx.createLinearGradient(0, plot.y, 0, plot.y + plot.height);
  gradient.addColorStop(0, "rgba(255, 255, 255, 0.92)");
  gradient.addColorStop(1, "rgba(246, 248, 252, 0.94)");
  ctx.fillStyle = gradient;
  roundRect(ctx, plot.x, plot.y, plot.width, plot.height, 18);
  ctx.fill();

  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(213, 219, 230, 0.95)";
  ctx.stroke();

  ctx.fillStyle = "#121521";
  ctx.font = "600 13px \"Space Grotesk\", ui-sans-serif, sans-serif";
  ctx.fillText(title, plot.x + 16, plot.y + 22);
}

function drawGrid(ctx, plot, yBounds, ticks, drawXTicks) {
  ctx.save();
  ctx.strokeStyle = "rgba(17, 24, 39, 0.08)";
  ctx.lineWidth = 1;

  for (const tick of X_TICKS) {
    const x = scaleX(tick, plot, chartBounds);
    ctx.beginPath();
    ctx.moveTo(x, plot.y);
    ctx.lineTo(x, plot.y + plot.height);
    ctx.stroke();
  }

  for (const tick of ticks) {
    const y = scaleY(tick, plot, yBounds);
    ctx.beginPath();
    ctx.moveTo(plot.x, y);
    ctx.lineTo(plot.x + plot.width, y);
    ctx.stroke();
  }

  if (drawXTicks) {
    ctx.strokeStyle = "rgba(17, 24, 39, 0.12)";
    for (const tick of X_TICKS) {
      const x = scaleX(tick, plot, chartBounds);
      ctx.beginPath();
      ctx.moveTo(x, plot.y + plot.height);
      ctx.lineTo(x, plot.y + plot.height + 6);
      ctx.stroke();
    }
  }

  ctx.restore();
}

function drawAxes(ctx, plot, yBounds, ticks, includeXLabels, yLabel, xLabel = "") {
  ctx.save();
  ctx.strokeStyle = "rgba(23, 74, 103, 0.95)";
  ctx.fillStyle = "#223042";
  ctx.lineWidth = 1.4;
  ctx.font = '500 12px "Space Grotesk", ui-sans-serif, sans-serif';

  ctx.beginPath();
  ctx.moveTo(plot.x, plot.y);
  ctx.lineTo(plot.x, plot.y + plot.height);
  ctx.lineTo(plot.x + plot.width, plot.y + plot.height);
  ctx.stroke();

  for (const tick of ticks) {
    const y = scaleY(tick, plot, yBounds);
    ctx.beginPath();
    ctx.moveTo(plot.x - 6, y);
    ctx.lineTo(plot.x, y);
    ctx.stroke();
    ctx.fillText(formatTickLabel(tick, yBounds), plot.x - 50, y + 4);
  }

  if (includeXLabels) {
    for (const tick of X_TICKS) {
      const x = scaleX(tick, plot, chartBounds);
      ctx.fillText(`${(tick * 100).toFixed(0)}%`, x - 12, plot.y + plot.height + 22);
    }

    ctx.font = '600 13px "Space Grotesk", ui-sans-serif, sans-serif';
    ctx.fillText(xLabel, plot.x + plot.width - 116, plot.y + plot.height + 42);
  }

  ctx.save();
  ctx.translate(plot.x - 60, plot.y + plot.height / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.font = '600 13px "Space Grotesk", ui-sans-serif, sans-serif';
  ctx.fillText(yLabel, 0, 0);
  ctx.restore();

  ctx.restore();
}

function drawZeroLine(ctx, plot) {
  if (chartBounds.error.yMin > 0 || chartBounds.error.yMax < 0) {
    return;
  }

  const y = scaleY(0, plot, chartBounds.error);
  ctx.save();
  ctx.strokeStyle = "rgba(17, 24, 39, 0.32)";
  ctx.lineWidth = 1.6;
  ctx.setLineDash([6, 6]);
  ctx.beginPath();
  ctx.moveTo(plot.x, y);
  ctx.lineTo(plot.x + plot.width, y);
  ctx.stroke();
  ctx.restore();
}

function drawSelectionGuide(ctx, plot, rate) {
  const x = scaleX(rate, plot, chartBounds);
  ctx.save();
  ctx.strokeStyle = "rgba(23, 74, 103, 0.34)";
  ctx.lineWidth = 1.4;
  ctx.setLineDash([8, 8]);
  ctx.beginPath();
  ctx.moveTo(x, plot.y);
  ctx.lineTo(x, plot.y + plot.height);
  ctx.stroke();
  ctx.restore();
}

function drawSeries(ctx, plot, series, formula, bounds) {
  ctx.save();
  ctx.strokeStyle = formula.color;
  ctx.lineWidth = formula.lineWidth;
  ctx.setLineDash(formula.lineDash);
  ctx.beginPath();

  series.forEach((point, index) => {
    const x = scaleX(point.r, plot, chartBounds);
    const y = scaleY(point.value, plot, bounds);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });

  ctx.stroke();
  ctx.restore();
}

function drawMarker(ctx, marker, x, y, color) {
  ctx.save();
  ctx.translate(x, y);
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2.2;

  if (marker === "circle") {
    ctx.beginPath();
    ctx.arc(0, 0, 6, 0, Math.PI * 2);
    ctx.fill();
  } else if (marker === "diamond") {
    ctx.beginPath();
    ctx.moveTo(0, -7);
    ctx.lineTo(7, 0);
    ctx.lineTo(0, 7);
    ctx.lineTo(-7, 0);
    ctx.closePath();
    ctx.fill();
  } else if (marker === "square") {
    ctx.fillRect(-6, -6, 12, 12);
  } else if (marker === "triangle") {
    ctx.beginPath();
    ctx.moveTo(0, -8);
    ctx.lineTo(7, 6);
    ctx.lineTo(-7, 6);
    ctx.closePath();
    ctx.fill();
  } else if (marker === "oval") {
    ctx.beginPath();
    ctx.ellipse(0, 0, 8, 5.5, 0, 0, Math.PI * 2);
    ctx.fill();
  } else if (marker === "cross") {
    ctx.beginPath();
    ctx.moveTo(-7, -7);
    ctx.lineTo(7, 7);
    ctx.moveTo(7, -7);
    ctx.lineTo(-7, 7);
    ctx.stroke();
  }

  ctx.beginPath();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.9)";
  ctx.lineWidth = 1.2;
  ctx.arc(0, 0, 10, 0, Math.PI * 2);
  ctx.stroke();
  ctx.restore();
}

function buildSampleRates() {
  const rates = [];
  for (let value = MIN_SLIDER_VALUE; value <= MAX_SLIDER_VALUE; value += 1) {
    rates.push(sliderValueToRate(value));
  }
  return rates;
}

function buildSampledValues() {
  const map = {};
  for (const formula of FORMULAS) {
    map[formula.id] = sampleRates.map((r) => ({
      r,
      value: formula.compute(r),
    }));
  }
  return map;
}

function buildSampledErrors(allValues) {
  const exactSeries = allValues.exact;
  const exactByRate = new Map(exactSeries.map((point) => [point.r, point.value]));
  const errorMap = {};

  for (const formula of ERROR_FORMULAS) {
    errorMap[formula.id] = allValues[formula.id].map((point) => ({
      r: point.r,
      value: percentError(point.value, exactByRate.get(point.r)),
    }));
  }

  return errorMap;
}

function calculateValues(rate) {
  const values = {};
  for (const formula of FORMULAS) {
    values[formula.id] = formula.compute(rate);
  }
  return values;
}

function calculateErrors(values) {
  const exact = values.exact;
  const errors = {};
  for (const formula of ERROR_FORMULAS) {
    errors[formula.id] = percentError(values[formula.id], exact);
  }
  return errors;
}

function percentError(value, exact) {
  return ((value - exact) / exact) * 100;
}

function computeMainMax(allValues) {
  let maxValue = 0;
  for (const formula of FORMULAS) {
    for (const point of allValues[formula.id]) {
      maxValue = Math.max(maxValue, point.value);
    }
  }
  return roundUpToStep(maxValue * 1.03, 5);
}

function computeErrorBounds(allErrors) {
  let maxAbs = 0;
  for (const formula of ERROR_FORMULAS) {
    for (const point of allErrors[formula.id]) {
      maxAbs = Math.max(maxAbs, Math.abs(point.value));
    }
  }

  const padded = maxAbs * 1.12;
  const step = padded < 2 ? 0.5 : padded < 8 ? 1 : 2;
  const bound = Math.max(step, roundUpToStep(padded, step));
  return {
    yMin: -bound,
    yMax: bound,
  };
}

function createTicks(min, max, targetCount) {
  if (min === max) {
    return [min];
  }

  const range = niceNumber(max - min, false);
  const step = niceNumber(range / Math.max(targetCount - 1, 1), true);
  const tickMin = Math.ceil(min / step) * step;
  const tickMax = Math.floor(max / step) * step;
  const ticks = [];

  for (let value = tickMin; value <= tickMax + step * 0.5; value += step) {
    ticks.push(roundTo(value, 6));
  }

  if (ticks.length === 0) {
    return [min, max];
  }

  return ticks;
}

function niceNumber(value, round) {
  const exponent = Math.floor(Math.log10(value));
  const fraction = value / Math.pow(10, exponent);
  let niceFraction;

  if (round) {
    if (fraction < 1.5) {
      niceFraction = 1;
    } else if (fraction < 3) {
      niceFraction = 2;
    } else if (fraction < 7) {
      niceFraction = 5;
    } else {
      niceFraction = 10;
    }
  } else if (fraction <= 1) {
    niceFraction = 1;
  } else if (fraction <= 2) {
    niceFraction = 2;
  } else if (fraction <= 5) {
    niceFraction = 5;
  } else {
    niceFraction = 10;
  }

  return niceFraction * Math.pow(10, exponent);
}

function renderLegend() {
  legendList.innerHTML = FORMULAS.map((formula) => `
    <span class="legend-pill">
      <span class="legend-line" style="${lineStyleForLegend(formula)}"></span>
      <span class="legend-label">${formula.label}</span>
    </span>
  `).join("");
}

function renderFormulaCards(values, errors) {
  formulaCards.innerHTML = FORMULAS.map((formula) => {
    const currentValue = values[formula.id].toFixed(4);
    const deltaMarkup = formula.isReference
      ? '<span class="delta-pill">Reference baseline</span>'
      : buildDeltaMarkup(errors[formula.id]);

    return `
      <article class="formula-card ${formula.isReference ? "is-reference" : ""}">
        <div class="formula-head">
          <div>
            <div class="formula-title-row">
              <span class="swatch" style="--formula-color: ${formula.color}"></span>
              <span class="formula-name">${formula.label}</span>
            </div>
            <div class="formula-role">${formula.isReference ? "Exact reference" : "Approximation"}</div>
          </div>
          <div class="formula-metric">
            <div class="metric-label">Current n</div>
            <div class="metric-value">${currentValue}</div>
            ${deltaMarkup}
          </div>
        </div>
        <div class="equation-block">${formula.formulaText}</div>
        <p class="formula-note"><strong>Approximation:</strong> ${formula.approxText}</p>
      </article>
    `;
  }).join("");
}

function buildDeltaMarkup(errorValue) {
  const direction = errorValue > 0 ? "positive" : errorValue < 0 ? "negative" : "";
  const prefix = errorValue > 0 ? "+" : "";
  return `<span class="delta-pill ${direction}">${prefix}${errorValue.toFixed(2)}% vs Exact</span>`;
}

function lineStyleForLegend(formula) {
  if (!formula.lineDash.length) {
    return `background: ${formula.color};`;
  }

  const [dash = 0, gap = 0] = formula.lineDash;
  return `background: repeating-linear-gradient(to right, ${formula.color} 0 ${dash}px, transparent ${dash}px ${dash + gap}px);`;
}

function sliderValueToRate(sliderValue) {
  return sliderValue / 10000;
}

function rateToSliderValue(rate) {
  return Math.round(rate * 10000);
}

function setSliderValue(sliderValue) {
  state.sliderValue = clampSliderValue(sliderValue);
  updateAll();
}

function setRate(rate) {
  setSliderValue(rateToSliderValue(rate));
}

function clampSliderValue(sliderValue) {
  return Math.min(MAX_SLIDER_VALUE, Math.max(MIN_SLIDER_VALUE, Math.round(sliderValue)));
}

function sliderPercent(sliderValue) {
  return ((sliderValue - MIN_SLIDER_VALUE) / (MAX_SLIDER_VALUE - MIN_SLIDER_VALUE)) * 100;
}

function scaleX(value, plot, bounds) {
  const normalized = (value - bounds.xMin) / (bounds.xMax - bounds.xMin);
  return plot.x + normalized * plot.width;
}

function scaleY(value, plot, yBounds) {
  const normalized = (value - yBounds.yMin) / (yBounds.yMax - yBounds.yMin);
  return plot.y + plot.height - normalized * plot.height;
}

function formatDecimal(rate) {
  return rate.toFixed(4);
}

function formatPercent(rate) {
  return `${(rate * 100).toFixed(4)}%`;
}

function formatTickLabel(value, bounds) {
  if (bounds === chartBounds.error) {
    return `${value.toFixed(1)}%`;
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function roundUpToStep(value, step) {
  return Math.ceil(value / step) * step;
}

function roundTo(value, decimals) {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}

function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}
