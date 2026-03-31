const MIN_SLIDER_VALUE = 10;
const MAX_SLIDER_VALUE = 200;
const DEFAULT_SLIDER_VALUE = 83;

const FORMULAS = [
  {
    id: "exact",
    label: "Exact",
    description: "n = ln(2) / ln(1 + r)",
    color: "#1f77b4",
    marker: "circle",
    compute: (r) => Math.log(2) / Math.log(1 + r),
  },
  {
    id: "approx1",
    label: "Approx 1",
    description: "n = 0.69 / r",
    color: "#ff7f0e",
    marker: "diamond",
    compute: (r) => 0.69 / r,
  },
  {
    id: "approx2",
    label: "Approx 2",
    description: "n = 0.69 / (r - r^2 / 2)",
    color: "#2ca02c",
    marker: "square",
    compute: (r) => 0.69 / (r - (r * r) / 2),
  },
  {
    id: "approx3",
    label: "Approx 3",
    description: "n = 0.70 / (r - r^2 / 2)",
    color: "#d62728",
    marker: "triangle",
    compute: (r) => 0.70 / (r - (r * r) / 2),
  },
  {
    id: "approx4",
    label: "Approx 4",
    description: "n = 0.6931 / (r - r^2 / 2)",
    color: "#9467bd",
    marker: "oval",
    compute: (r) => 0.6931 / (r - (r * r) / 2),
  },
  {
    id: "rule72",
    label: "Rule of 72",
    description: "n = 72 / (100r)",
    color: "#8c564b",
    marker: "cross",
    compute: (r) => 72 / (100 * r),
  },
];

const state = {
  sliderValue: DEFAULT_SLIDER_VALUE,
};

const canvas = document.getElementById("chartCanvas");
const slider = document.getElementById("rateSlider");
const rateOutput = document.getElementById("rateOutput");
const valueList = document.getElementById("valueList");
const formulaList = document.getElementById("formulaList");
const downloadButton = document.getElementById("downloadButton");

const sampleRates = buildSampleRates();
const sampledSeries = buildSampledSeries();
const chartBounds = {
  xMin: sampleRates[0],
  xMax: sampleRates[sampleRates.length - 1],
  yMin: 0,
  yMax: computeMaxValue(),
};

populateFormulaList();
updateAll();

slider.addEventListener("input", () => {
  state.sliderValue = Number(slider.value);
  updateAll();
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
  rateOutput.textContent = `r = ${formatDecimal(rate)} (${formatPercent(rate)})`;
  renderValueList(values);
  updateChart();
}

function updateChart() {
  const rect = canvas.getBoundingClientRect();
  const cssWidth = Math.max(320, Math.floor(rect.width || canvas.parentElement.clientWidth || 900));
  const cssHeight = Math.round(cssWidth * 0.65);
  const dpr = window.devicePixelRatio || 1;

  canvas.width = Math.floor(cssWidth * dpr);
  canvas.height = Math.floor(cssHeight * dpr);
  canvas.style.height = `${cssHeight}px`;

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  drawChart(ctx, cssWidth, cssHeight);
}

function drawChart(ctx, width, height) {
  const plot = {
    left: 72,
    right: 26,
    top: 28,
    bottom: 58,
  };
  const plotWidth = width - plot.left - plot.right;
  const plotHeight = height - plot.top - plot.bottom;
  const rate = sliderValueToRate(state.sliderValue);
  const currentValues = calculateValues(rate);

  ctx.clearRect(0, 0, width, height);
  drawChartBackground(ctx, width, height);
  drawGrid(ctx, plot, plotWidth, plotHeight);
  drawAxes(ctx, plot, plotWidth, plotHeight);

  for (const formula of FORMULAS) {
    drawCurve(ctx, plot, plotWidth, plotHeight, formula);
  }

  for (const formula of FORMULAS) {
    const pointX = scaleX(rate, plot.left, plotWidth);
    const pointY = scaleY(currentValues[formula.id], plot.top, plotHeight);
    drawMarker(ctx, formula.marker, pointX, pointY, formula.color);
  }
}

function drawChartBackground(ctx, width, height) {
  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, "#fffdf8");
  gradient.addColorStop(1, "#f7f0e4");
  ctx.fillStyle = gradient;
  roundRect(ctx, 0, 0, width, height, 16);
  ctx.fill();
}

function drawGrid(ctx, plot, plotWidth, plotHeight) {
  ctx.save();
  ctx.strokeStyle = "rgba(31, 41, 51, 0.10)";
  ctx.lineWidth = 1;

  const xTicks = [0.01, 0.05, 0.10, 0.15, 0.20];
  for (const tick of xTicks) {
    const x = scaleX(tick, plot.left, plotWidth);
    ctx.beginPath();
    ctx.moveTo(x, plot.top);
    ctx.lineTo(x, plot.top + plotHeight);
    ctx.stroke();
  }

  const yTicks = [0, 15, 30, 45, 60, 75];
  for (const tick of yTicks) {
    const y = scaleY(tick, plot.top, plotHeight);
    ctx.beginPath();
    ctx.moveTo(plot.left, y);
    ctx.lineTo(plot.left + plotWidth, y);
    ctx.stroke();
  }

  ctx.restore();
}

function drawAxes(ctx, plot, plotWidth, plotHeight) {
  ctx.save();
  ctx.strokeStyle = "rgba(20, 80, 93, 0.9)";
  ctx.fillStyle = "#33404b";
  ctx.lineWidth = 1.4;
  ctx.font = "12px \"Avenir Next\", \"Segoe UI\", sans-serif";

  ctx.beginPath();
  ctx.moveTo(plot.left, plot.top);
  ctx.lineTo(plot.left, plot.top + plotHeight);
  ctx.lineTo(plot.left + plotWidth, plot.top + plotHeight);
  ctx.stroke();

  const xTicks = [0.01, 0.05, 0.10, 0.15, 0.20];
  for (const tick of xTicks) {
    const x = scaleX(tick, plot.left, plotWidth);
    const y = plot.top + plotHeight;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x, y + 6);
    ctx.stroke();
    ctx.fillText(`${(tick * 100).toFixed(0)}%`, x - 12, y + 22);
  }

  const yTicks = [0, 15, 30, 45, 60, 75];
  for (const tick of yTicks) {
    const x = plot.left;
    const y = scaleY(tick, plot.top, plotHeight);
    ctx.beginPath();
    ctx.moveTo(x - 6, y);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.fillText(String(tick), x - 30, y + 4);
  }

  ctx.font = "13px \"Avenir Next\", \"Segoe UI\", sans-serif";
  ctx.fillText("r (interest rate)", plot.left + plotWidth - 104, plot.top + plotHeight + 42);

  ctx.save();
  ctx.translate(24, plot.top + plotHeight / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("n (doubling time)", 0, 0);
  ctx.restore();

  ctx.restore();
}

function drawCurve(ctx, plot, plotWidth, plotHeight, formula) {
  const series = sampledSeries[formula.id];
  ctx.save();
  ctx.strokeStyle = formula.color;
  ctx.lineWidth = 2.4;
  ctx.beginPath();

  series.forEach((point, index) => {
    const x = scaleX(point.r, plot.left, plotWidth);
    const y = scaleY(point.n, plot.top, plotHeight);
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
  ctx.lineWidth = 2.1;

  if (marker === "circle") {
    ctx.beginPath();
    ctx.arc(0, 0, 5.8, 0, Math.PI * 2);
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
    ctx.moveTo(0, -7);
    ctx.lineTo(7, 6);
    ctx.lineTo(-7, 6);
    ctx.closePath();
    ctx.fill();
  } else if (marker === "oval") {
    ctx.beginPath();
    ctx.ellipse(0, 0, 8, 5.2, 0, 0, Math.PI * 2);
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
  ctx.strokeStyle = "rgba(255, 255, 255, 0.85)";
  ctx.lineWidth = 1.3;
  ctx.arc(0, 0, 9, 0, Math.PI * 2);
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

function buildSampledSeries() {
  const seriesMap = {};
  for (const formula of FORMULAS) {
    seriesMap[formula.id] = sampleRates.map((r) => ({
      r,
      n: formula.compute(r),
    }));
  }
  return seriesMap;
}

function calculateValues(rate) {
  const values = {};
  for (const formula of FORMULAS) {
    values[formula.id] = formula.compute(rate);
  }
  return values;
}

function computeMaxValue() {
  let maxValue = 0;
  for (const formula of FORMULAS) {
    for (const point of sampledSeries[formula.id]) {
      maxValue = Math.max(maxValue, point.n);
    }
  }
  return Math.ceil(maxValue / 5) * 5;
}

function renderValueList(values) {
  valueList.innerHTML = FORMULAS.map((formula) => `
    <div class="value-row">
      <span class="swatch" style="--formula-color: ${formula.color}"></span>
      <dt class="label-text">${formula.label}</dt>
      <dd class="value-text">${values[formula.id].toFixed(4)}</dd>
    </div>
  `).join("");
}

function populateFormulaList() {
  formulaList.innerHTML = FORMULAS.map((formula) => `
    <li class="formula-item">
      <span class="swatch" style="--formula-color: ${formula.color}"></span>
      <div class="formula-copy">
        <strong>${formula.label}</strong>
        <span>${formula.description}</span>
      </div>
    </li>
  `).join("");
}

function sliderValueToRate(sliderValue) {
  return sliderValue / 1000;
}

function scaleX(value, left, width) {
  const normalized = (value - chartBounds.xMin) / (chartBounds.xMax - chartBounds.xMin);
  return left + normalized * width;
}

function scaleY(value, top, height) {
  const normalized = (value - chartBounds.yMin) / (chartBounds.yMax - chartBounds.yMin);
  return top + height - normalized * height;
}

function formatDecimal(rate) {
  return rate.toFixed(3);
}

function formatPercent(rate) {
  return `${(rate * 100).toFixed(1)}%`;
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
