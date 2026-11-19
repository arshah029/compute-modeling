import { runModel, scenarioValues, DEFAULT_ASSUMPTIONS, YEARS } from "./model.js";

/* global Chart, marked */

const state = {
  obs: [],
  sources: [],
  srcById: {},
  model: { series: [], assumptions: [] },
  assumptions: [],
  drivers: {},
  scenario: "base",
  charts: {},
  tables: {},
};

// ---------- helpers ----------
const $ = (s, el = document) => el.querySelector(s);
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const seriesColor = (i) => css(`--series-${(i % 8) + 1}`);
const fmt = (v, digits) => {
  if (v === null || v === undefined || v === "" || Number.isNaN(Number(v))) return "–";
  v = Number(v);
  const d = digits ?? (Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 10 ? 1 : 2);
  return v.toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: 0 });
};
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const UNIT_LABELS = { USD_bn: "USD bn", USD_k: "USD k", RMB_bn: "RMB bn", GW: "GW", GWh: "GWh", TWh: "TWh", units_m: "M", H100e_m: "M H100e", pct: "%", pp: "pp", ratio: "ratio", zettaFLOP_s: "zettaFLOP/s" };
const unitLabel = (u) => UNIT_LABELS[u] ?? String(u ?? "").replace(/_/g, " ");
const ACRONYMS = { gw: "GW", twh: "TWh", usd: "USD", rmb: "RMB", us: "US", ai: "AI", pue: "PUE", h100e: "H100e", dc: "DC", tsmc: "TSMC", amd: "AMD", hpc: "HPC", nvidia: "NVIDIA", cagr: "CAGR", pct: "%", eff: "efficiency", ict: "ICT", av: "AV", esa: "ESA", saar: "SAAR", gwh: "GWh", miso: "MISO", pjm: "PJM", tnb: "TNB" };
const titleCase = (s) => String(s).split("_").map((w, i) => ACRONYMS[w.toLowerCase()] ?? (i === 0 ? w.charAt(0).toUpperCase() + w.slice(1) : w)).join(" ");
const periodSort = (a, b) => String(a).localeCompare(String(b), "en", { numeric: true });
const isTrue = (v) => v === true || v === "true" || v === "TRUE" || v === 1;
const fmtDriver = (v, u) => {
  switch (u) {
    case "USD_bn": return `$${fmt(v, 0)}bn`;
    case "USD_k": return `$${fmt(v, 1)}k`;
    case "pct": return `${fmt(v, 1)}%`;
    case "pp": return `${fmt(v, 1)} pp`;
    case "ratio": return fmt(v, 2);
    case "W": return `${fmt(v, 0)} W`;
    case "years": return `${fmt(v, 0)} yrs`;
    default: return `${fmt(v)} ${unitLabel(u)}`;
  }
};

async function loadJSON(path, fallback) {
  try {
    const r = await fetch(path, { cache: "no-cache" });
    if (!r.ok) throw new Error(r.status);
    return await r.json();
  } catch {
    return fallback;
  }
}
async function loadText(path) {
  try {
    const r = await fetch(path, { cache: "no-cache" });
    return r.ok ? await r.text() : "";
  } catch {
    return "";
  }
}

// ---------- Chart.js defaults ----------
function applyChartTheme() {
  Chart.defaults.font.family = css("--font");
  Chart.defaults.font.size = 12;
  Chart.defaults.color = css("--text-secondary");
  Chart.defaults.borderColor = css("--grid");
}
function baseOptions({ stacked = false, unit = "" } = {}) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 250 },
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        position: "top",
        align: "start",
        labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true, color: css("--text-secondary"), filter: (i) => !i.text.startsWith("_") },
      },
      tooltip: {
        backgroundColor: css("--surface-1"),
        titleColor: css("--text-primary"),
        bodyColor: css("--text-secondary"),
        borderColor: css("--border"),
        borderWidth: 1,
        padding: 10,
        boxPadding: 4,
        usePointStyle: true,
        filter: (i) => !i.dataset.label.startsWith("_") && i.parsed.y !== null,
        callbacks: { label: (c) => ` ${c.dataset.label}: ${fmt(c.parsed.y)} ${unit}` },
      },
    },
    scales: {
      x: { stacked, grid: { display: false }, ticks: { color: css("--text-muted") } },
      y: {
        stacked,
        beginAtZero: true,
        grid: { color: css("--grid") },
        border: { display: false },
        ticks: { color: css("--text-muted"), callback: (v) => fmt(v) },
        title: { display: !!unit, text: unit, color: css("--text-muted") },
      },
    },
  };
}
function mountChart(id, config) {
  state.charts[id]?.destroy();
  state.charts[id] = new Chart(document.getElementById(id), config);
}
const lineDS = (label, data, color, extra = {}) => ({
  label, data, borderColor: color, backgroundColor: color, borderWidth: 2, pointRadius: 3, pointHoverRadius: 6,
  pointBorderColor: css("--surface-1"), pointBorderWidth: 2, tension: 0.25, spanGaps: true, fill: false, ...extra,
});

// ---------- table views ----------
function renderTable(id, header, rows) {
  state.tables[id] = { header, rows };
  const el = document.getElementById(`${id}-table`);
  if (!el || el.hidden) return;
  el.innerHTML = `<table class="data-table"><thead><tr>${header.map((h, i) => `<th class="${i ? "num" : ""}">${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows
    .map((r) => `<tr>${r.map((c, i) => `<td class="${i ? "num" : ""}">${typeof c === "number" ? fmt(c) : esc(c)}</td>`).join("")}</tr>`)
    .join("")}</tbody></table>`;
}
document.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-table-toggle]");
  if (!btn) return;
  const id = btn.dataset.tableToggle;
  const el = document.getElementById(`${id}-table`);
  el.hidden = !el.hidden;
  btn.setAttribute("aria-pressed", String(!el.hidden));
  btn.textContent = el.hidden ? "Table" : "Hide table";
  const t = state.tables[id];
  if (t) renderTable(id, t.header, t.rows);
});

// ---------- data shaping ----------
const select = (category, metric) => state.obs.filter((o) => o.category === category && o.metric === metric);
function pivot(rows) {
  const periods = [...new Set(rows.map((r) => r.period))].sort(periodSort);
  const entities = [...new Set(rows.map((r) => r.entity))];
  const total = (e) => rows.filter((r) => r.entity === e).reduce((s, r) => s + r.value, 0);
  entities.sort((a, b) => total(b) - total(a)); // stable colour by size, independent of filters
  const grid = entities.map((e) => periods.map((p) => rows.find((r) => r.entity === e && r.period === p)?.value ?? null));
  return { periods, entities, grid };
}
const latest = (cat, metric, entity) =>
  state.obs.filter((o) => o.category === cat && o.metric === metric && (!entity || o.entity === entity)).sort((a, b) => periodSort(a.period, b.period)).at(-1);
const modelSeries = (name) => state.model.series?.find((s) => s.name === name);
const sourceName = (o) => state.srcById[o?.source_id]?.publisher || state.srcById[o?.source_id]?.name || o?.source_name || "";

// ---------- overview ----------
const kpiHTML = (t) => `<div class="kpi"><div class="label">${esc(t.label)}</div><div class="value">${esc(t.value)}<small>${esc(t.unit)}</small></div><div class="note">${esc(t.note || " ")}</div></div>`;

function renderOverviewKpis() {
  const tiles = [];
  const big4 = state.obs.filter((o) => o.category === "capex" && o.metric === "capex_usd" && o.entity === "Big4" && /^\d{4}$/.test(o.period)).sort((a, b) => periodSort(a.period, b.period)).at(-1);
  if (big4) tiles.push({ label: `Big 4 hyperscaler capex, ${big4.period}`, value: `$${fmt(big4.value, 0)}`, unit: "bn", note: "Microsoft, Alphabet, Amazon, Meta" });
  const stock = latest("accelerators", "ai_compute_stock_h100e");
  if (stock) tiles.push({ label: `Installed AI compute, ${stock.period}`, value: fmt(stock.value, 1), unit: "M H100e", note: sourceName(stock) });
  const chipPower = latest("power", "ai_chip_power_gw");
  if (chipPower) tiles.push({ label: `Power for AI chips, ${chipPower.period}`, value: fmt(chipPower.value, 0), unit: "GW", note: sourceName(chipPower) });
  const fac = modelSeries("facility_gw")?.points?.find((p) => p.year === 2030);
  if (fac) tiles.push({ label: "AI data center power, 2030 (model)", value: fmt(fac.base, 0), unit: "GW", note: `Range ${fmt(fac.low, 0)} to ${fmt(fac.high, 0)} GW` });
  $("#overviewKpis").innerHTML = tiles.map(kpiHTML).join("");
}

function renderCapexChart() {
  // calendar quarters only, one series per company (Big4 is a total, not a company)
  const rows = select("capex", "capex_usd").filter((o) => /^\d{4}Q[1-4]$/.test(o.period) && o.entity !== "Big4");
  const { periods, entities, grid } = pivot(rows);
  const surface = css("--surface-1");
  const opts = baseOptions({ stacked: true, unit: "USD bn" });
  opts.plugins.tooltip.callbacks.footer = (items) => `Total: ${fmt(items.reduce((s, i) => s + (i.parsed.y || 0), 0), 1)} USD bn`;
  mountChart("capexChart", {
    type: "bar",
    data: {
      labels: periods,
      datasets: entities.map((e, i) => ({
        label: e, data: grid[i], backgroundColor: seriesColor(i), borderColor: surface,
        borderWidth: { top: 2 }, borderSkipped: false, maxBarThickness: 48,
      })),
    },
    options: opts,
  });
  renderTable("capexChart", ["Company", ...periods], entities.map((e, i) => [e, ...grid[i]]));
}

function renderGridChart() {
  // latest GW value per entity+metric from grid and datacenter categories (forecasts of peak load excluded)
  const latestBy = {};
  state.obs
    .filter((o) => (o.category === "grid" || o.category === "datacenter") && o.unit === "GW")
    .forEach((o) => {
      const k = `${o.entity}|${o.metric}`;
      if (!latestBy[k] || periodSort(latestBy[k].period, o.period) < 0) latestBy[k] = o;
    });
  const rows = Object.values(latestBy).sort((a, b) => b.value - a.value);
  const card = $("#gridCard");
  card.hidden = rows.length === 0;
  if (!rows.length) return;
  const labels = rows.map((o) => `${o.entity}: ${titleCase(o.metric).replace(/ GW$/, "")} (${o.period})`);
  const opts = baseOptions({ unit: "GW" });
  opts.indexAxis = "y";
  opts.interaction = { mode: "nearest", axis: "y", intersect: false };
  opts.plugins.legend.display = false;
  opts.plugins.tooltip.callbacks.label = (c) => ` ${fmt(c.parsed.x)} GW · ${sourceName(rows[c.dataIndex])}`;
  opts.scales = {
    x: { beginAtZero: true, grid: { color: css("--grid") }, border: { display: false }, ticks: { color: css("--text-muted"), callback: (v) => fmt(v) }, title: { display: true, text: "GW", color: css("--text-muted") } },
    y: { grid: { display: false }, ticks: { color: css("--text-secondary"), autoSkip: false, callback: function (v) { const l = this.getLabelForValue(v); const max = this.chart.width < 520 ? 24 : 48; return l.length > max ? l.slice(0, max - 1) + "…" : l; } } },
  };
  $("#gridChart").parentElement.style.height = `${Math.max(240, rows.length * 30 + 60)}px`;
  mountChart("gridChart", {
    type: "bar",
    data: { labels, datasets: [{ label: "GW", data: rows.map((o) => o.value), backgroundColor: seriesColor(0), borderRadius: { topRight: 4, bottomRight: 4 }, borderSkipped: "left", maxBarThickness: 18 }] },
    options: opts,
  });
  renderTable("gridChart", ["Signal", "GW", "Source"], rows.map((o, i) => [labels[i], o.value, sourceName(o)]));
}

function renderExplorer() {
  const cat = $("#explorerCategory").value;
  const metric = $("#explorerMetric").value;
  const rows = select(cat, metric);
  // one axis and one time grain: never mix units, or annual with quarterly periods
  const groupKey = (r) => `${r.unit}|${r.period_type}`;
  const groups = {};
  rows.forEach((r) => (groups[groupKey(r)] ||= []).push(r));
  const ordered = Object.keys(groups).sort((a, b) => groups[b].length - groups[a].length);
  const unitRows = groups[ordered[0]] || [];
  const units = [unitRows[0]?.unit, ...ordered.slice(1).map((k) => k.split("|")[0])];
  const { periods, entities, grid } = pivot(unitRows);
  const unit = unitLabel(units[0]);
  const capped = entities.slice(0, 8);
  $("#explorerSub").textContent = `${titleCase(metric)}, ${unit}. ${unitRows.length} data point${unitRows.length === 1 ? "" : "s"}${entities.length > 8 ? `; top 8 of ${entities.length} entities shown` : ""}${ordered.length > 1 ? `; ${rows.length - unitRows.length} more in other units or periods are on the Data tab` : ""}.`;
  const asLine = periods.length > 2;
  mountChart("explorerChart", {
    type: asLine ? "line" : "bar",
    data: {
      labels: periods,
      datasets: capped.map((e, i) =>
        asLine
          ? lineDS(e, grid[i], seriesColor(i), { pointRadius: 4 })
          : { label: e, data: grid[i], backgroundColor: seriesColor(i), borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: "bottom", maxBarThickness: 48 }
      ),
    },
    options: baseOptions({ unit }),
  });
  renderTable("explorerChart", ["Entity", ...periods], entities.map((e, i) => [e, ...grid[i]]));
}

function setupExplorer() {
  const catSel = $("#explorerCategory");
  const metSel = $("#explorerMetric");
  const cats = [...new Set(state.obs.map((o) => o.category))];
  catSel.innerHTML = cats.map((c) => `<option value="${esc(c)}">${esc(titleCase(c))}</option>`).join("");
  const fillMetrics = () => {
    const counts = {};
    state.obs.filter((o) => o.category === catSel.value).forEach((o) => (counts[o.metric] = (counts[o.metric] || 0) + 1));
    const metrics = Object.keys(counts).sort((a, b) => counts[b] - counts[a]); // richest metric first
    metSel.innerHTML = metrics.map((m) => `<option value="${esc(m)}">${esc(titleCase(m))} (${counts[m]})</option>`).join("");
  };
  catSel.addEventListener("change", () => { fillMetrics(); renderExplorer(); });
  metSel.addEventListener("change", renderExplorer);
  if (cats.includes("accelerators")) catSel.value = "accelerators";
  fillMetrics();
}

// ---------- model ----------
function stepFor(a) {
  const span = Math.abs(a.high - a.low);
  if (span <= 1) return 0.01;
  if (span <= 12) return 0.5;
  if (span <= 60) return 1;
  if (span <= 300) return 5;
  return 10;
}
function renderSliders() {
  $("#sliders").innerHTML = state.assumptions
    .map((a) => {
      const srcs = (a.source_ids || []).map((id) => state.srcById[id]).filter(Boolean);
      const srcHTML = srcs.length
        ? `<div class="desc">Sources: ${srcs.map((s) => (s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.publisher || s.name)}</a>` : esc(s.publisher || s.name))).join(", ")}</div>`
        : "";
      return `
    <div class="slider">
      <div class="slider-top"><label class="name" for="s-${esc(a.key)}">${esc(a.label)}</label><span class="val" id="v-${esc(a.key)}"></span></div>
      <input type="range" id="s-${esc(a.key)}" data-key="${esc(a.key)}" min="${Math.min(a.low, a.high)}" max="${Math.max(a.low, a.high)}" step="${stepFor(a)}" value="${state.drivers[a.key]}">
      <div class="range"><span>${fmtDriver(Math.min(a.low, a.high), a.unit)}</span><span>${fmtDriver(Math.max(a.low, a.high), a.unit)}</span></div>
      <details><summary>Why this value</summary>${a.description ? `<div class="desc">${esc(a.description)}</div>` : ""}${srcHTML}</details>
    </div>`;
    })
    .join("");
  $("#sliders").addEventListener("input", (e) => {
    const k = e.target.dataset.key;
    if (!k) return;
    state.drivers[k] = Number(e.target.value);
    setScenarioButton(null);
    updateSliderLabels();
    updateModel();
  });
  updateSliderLabels();
}
function updateSliderLabels() {
  for (const a of state.assumptions) {
    const v = state.drivers[a.key];
    $(`#v-${CSS.escape(a.key)}`).textContent = fmtDriver(v, a.unit);
    $(`#s-${CSS.escape(a.key)}`).value = v;
  }
}
function setScenarioButton(which) {
  state.scenario = which;
  document.querySelectorAll("[data-scenario]").forEach((b) => b.classList.toggle("active", b.dataset.scenario === which));
}
const baseDrivers = () => Object.fromEntries(state.assumptions.map((a) => [a.key, Number(a.value)]));
function scenarioDrivers(which) {
  const base = baseDrivers();
  const preset = state.model.scenarios?.[which];
  if (preset) return { ...base, ...Object.fromEntries(Object.entries(preset).map(([k, v]) => [k, Number(v)])) };
  return which === "base" ? base : scenarioValues(state.assumptions, base, state.model.history, which);
}
function setupScenarios() {
  document.querySelectorAll("[data-scenario]").forEach((b) =>
    b.addEventListener("click", () => {
      state.drivers = scenarioDrivers(b.dataset.scenario);
      setScenarioButton(b.dataset.scenario);
      updateSliderLabels();
      updateModel();
    })
  );
  $("#copyLink").addEventListener("click", async () => {
    const q = new URLSearchParams(Object.entries(state.drivers).map(([k, v]) => [k, String(+v.toFixed(4))])).toString();
    const url = `${location.origin}${location.pathname}?${q}#model`;
    history.replaceState(null, "", `?${q}#model`);
    try { await navigator.clipboard.writeText(url); $("#copyLink").textContent = "Link copied"; } catch { $("#copyLink").textContent = "Link is in the address bar"; }
    setTimeout(() => ($("#copyLink").textContent = "Copy link to this scenario"), 2000);
  });
}

function bandDatasets(name, label) {
  const s = modelSeries(name);
  if (!s) return [];
  const by = Object.fromEntries(s.points.map((p) => [p.year, p]));
  return [
    { label: "_low", data: YEARS.map((y) => by[y]?.low ?? null), borderWidth: 0, pointRadius: 0, pointHoverRadius: 0, fill: false, spanGaps: true, order: 5 },
    { label, data: YEARS.map((y) => by[y]?.high ?? null), borderWidth: 0, pointRadius: 0, pointHoverRadius: 0, backgroundColor: css("--band"), fill: "-1", spanGaps: true, order: 5 },
  ];
}
function benchmarkDatasets(seriesNames) {
  const marks = (state.model.benchmarks || []).filter((b) => seriesNames.includes(b.series));
  const shapes = ["rectRot", "triangle", "rect", "star"];
  return marks.map((b, i) => ({
    label: b.label,
    type: "line",
    data: YEARS.map((y) => (y === b.year ? b.value : null)),
    showLine: false,
    pointStyle: shapes[i % shapes.length],
    pointRadius: 7,
    pointHoverRadius: 9,
    borderColor: css("--surface-1"),
    borderWidth: 2,
    backgroundColor: css("--text-primary"),
    order: 0,
  }));
}
const researchRow = (name, y) => modelSeries(name)?.points?.find((p) => p.year === y);

function updateModel() {
  const rows = runModel(state.drivers, state.model.history);
  const r30 = rows.at(-1);
  const r25 = rows.find((r) => r.year === 2025);
  $("#modelKpis").innerHTML = [
    { label: "AI data center power, 2030", value: fmt(r30.facilityGW, 0), unit: "GW", note: `${fmt(r30.facilityGW / r25.facilityGW, 1)}× 2025 · incl. cooling` },
    { label: "AI electricity use, 2030", value: fmt(r30.energyTWh, 0), unit: "TWh", note: `${fmt(r30.energyTWh / r25.energyTWh, 1)}× 2025` },
    { label: "Installed AI compute, 2030", value: fmt(r30.stock, 0), unit: "M H100e", note: `${fmt(r30.zettaflops, 0)} zettaFLOP/s · ${fmt(r30.inferenceShare * 100, 0)}% inference` },
    { label: "AI capex, 2030", value: `$${fmt(r30.capex / 1000, 2)}`, unit: "trn", note: `$${fmt(r30.accelSpend, 0)}bn on accelerators` },
  ].map(kpiHTML).join("");

  const labels = YEARS.map(String);

  // power
  mountChart("powerChart", {
    type: "line",
    data: {
      labels,
      datasets: [
        lineDS("Facility power (this scenario)", rows.map((r) => r.facilityGW), seriesColor(0), { order: 1 }),
        lineDS("IT power (this scenario)", rows.map((r) => r.itGW), seriesColor(1), { order: 1 }),
        ...bandDatasets("facility_gw", "Research range, facility power"),
        ...benchmarkDatasets(["it_gw", "facility_gw"]),
      ],
    },
    options: baseOptions({ unit: "GW" }),
  });
  renderTable("powerChart", ["Year", "IT GW", "Facility GW", "Research low", "Research base", "Research high"],
    rows.map((r) => { const p = researchRow("facility_gw", r.year); return [String(r.year), r.itGW, r.facilityGW, p?.low ?? "–", p?.base ?? "–", p?.high ?? "–"]; }));

  // energy
  mountChart("energyChart", {
    type: "line",
    data: {
      labels,
      datasets: [
        lineDS("AI data centers (this scenario)", rows.map((r) => r.energyTWh), seriesColor(0), { order: 1 }),
        ...bandDatasets("energy_twh", "Research range"),
        ...benchmarkDatasets(["energy_twh"]),
      ],
    },
    options: baseOptions({ unit: "TWh" }),
  });
  renderTable("energyChart", ["Year", "Scenario TWh", "Research low", "Research base", "Research high"],
    rows.map((r) => { const p = researchRow("energy_twh", r.year); return [String(r.year), r.energyTWh, p?.low ?? "–", p?.base ?? "–", p?.high ?? "–"]; }));

  // compute: areas stacked by hand so the band and benchmarks share the same unstacked axis
  const parts = { Training: rows.map((r) => r.trainingStock), Inference: rows.map((r) => r.inferenceStock) };
  const computeOpts = baseOptions({ unit: "M H100e" });
  computeOpts.plugins.tooltip.callbacks.label = (c) => ` ${c.dataset.label}: ${fmt(parts[c.dataset.label]?.[c.dataIndex] ?? c.parsed.y)} M H100e`;
  mountChart("computeChart", {
    type: "line",
    data: {
      labels,
      datasets: [
        { label: "Training", data: parts.Training, borderColor: seriesColor(0), backgroundColor: seriesColor(0), fill: "origin", borderWidth: 2, pointRadius: 0, tension: 0.25, order: 2 },
        { label: "Inference", data: rows.map((r) => r.stock), borderColor: seriesColor(1), backgroundColor: seriesColor(1), fill: "-1", borderWidth: 2, pointRadius: 0, tension: 0.25, order: 2 },
        lineDS("Research base, total", YEARS.map((y) => researchRow("stock", y)?.base ?? null), css("--text-primary"), { borderDash: [5, 4], pointRadius: 0, order: 1 }),
        ...benchmarkDatasets(["stock"]),
      ],
    },
    options: computeOpts,
  });
  renderTable("computeChart", ["Year", "Training", "Inference", "Total", "Research base"],
    rows.map((r) => [String(r.year), r.trainingStock, r.inferenceStock, r.stock, researchRow("stock", r.year)?.base ?? "–"]));

  // additions
  const shipOpts = baseOptions({ unit: "M H100e", stacked: true });
  mountChart("shipChart", {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Historical estimate", data: rows.map((r) => (r.reported ? r.additions : null)), backgroundColor: css("--text-muted"), borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: "bottom", maxBarThickness: 44 },
        { label: "Modeled from capex", data: rows.map((r) => (r.reported ? null : r.additions)), backgroundColor: seriesColor(0), borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: "bottom", maxBarThickness: 44 },
      ],
    },
    options: shipOpts,
  });
  renderTable("shipChart", ["Year", "Added (M H100e)", "Basis", "Cost per H100e (USD k)", "IT W per H100e"],
    rows.map((r) => [String(r.year), r.additions, r.reported ? "Historical" : "Modeled", r.price ?? "–", r.watts]));
}

function setupModel() {
  const fromData = Array.isArray(state.model.assumptions) ? state.model.assumptions.filter((a) => a && a.key) : [];
  const byKey = Object.fromEntries(fromData.map((a) => [a.key, a]));
  // data order wins; any key the math needs but the data lacks falls back to defaults
  const keys = [...fromData.map((a) => a.key), ...DEFAULT_ASSUMPTIONS.map((a) => a.key).filter((k) => !byKey[k])];
  const defaults = Object.fromEntries(DEFAULT_ASSUMPTIONS.map((a) => [a.key, a]));
  state.assumptions = keys
    .map((k) => ({ ...(defaults[k] || {}), ...(byKey[k] || {}) }))
    .filter((a) => [a.value, a.low, a.high].every((x) => Number.isFinite(Number(x))))
    .map((a) => ({ ...a, value: Number(a.value), low: Number(a.low), high: Number(a.high) }));
  state.drivers = scenarioDrivers("base");
  const params = new URLSearchParams(location.search);
  let fromUrl = false;
  for (const a of state.assumptions) {
    if (params.has(a.key) && Number.isFinite(Number(params.get(a.key)))) { state.drivers[a.key] = Number(params.get(a.key)); fromUrl = true; }
  }
  if (fromUrl) setScenarioButton(null);
  renderSliders();
  setupScenarios();

  const f = state.model.formula;
  $("#formulaList").innerHTML = Array.isArray(f) && f.length ? f.map((x) => `<li><code>${esc(x)}</code></li>`).join("") : "<li>Formulas will appear here when the dataset includes them.</li>";
}

// ---------- data tab ----------
function setupDataTab() {
  const cats = [...new Set(state.obs.map((o) => o.category))];
  $("#dataCategory").insertAdjacentHTML("beforeend", cats.map((c) => `<option value="${esc(c)}">${esc(titleCase(c))}</option>`).join(""));
  const render = () => {
    const c = $("#dataCategory").value;
    const q = $("#dataSearch").value.trim().toLowerCase();
    const rows = state.obs.filter((o) => (!c || o.category === c) && (!q || [o.entity, o.metric, o.source_name, o.notes, o.period].join(" ").toLowerCase().includes(q)));
    $("#dataCount").textContent = `${rows.length} of ${state.obs.length} rows`;
    $("#dataTable tbody").innerHTML = rows
      .slice(0, 2000)
      .map((o) => {
        const s = state.srcById[o.source_id];
        const url = o.source_url || s?.url;
        const name = s?.publisher || s?.name || o.source_name || "";
        const src = url ? `<a href="${esc(url)}" target="_blank" rel="noopener" title="${esc(o.source_name || s?.name)}">${esc(name)}</a>` : esc(name);
        return `<tr class="${isTrue(o.is_estimate) ? "est" : ""}" title="${esc(o.notes)}"><td>${esc(titleCase(o.category))}</td><td>${esc(titleCase(o.metric))}</td><td>${esc(o.entity)}</td><td>${esc(o.period)}</td><td class="num">${fmt(o.value)}</td><td>${esc(unitLabel(o.unit))}</td><td>${src}</td></tr>`;
      })
      .join("");
  };
  $("#dataCategory").addEventListener("change", render);
  $("#dataSearch").addEventListener("input", render);
  render();
  const byType = {};
  state.sources.forEach((s) => (byType[s.type || "other"] ||= []).push(s));
  const TYPE_LABELS = { filing: "Filings", earnings_call: "Earnings calls", report: "Reports", alt_data: "Alternative data" };
  $("#sourcesList").innerHTML = Object.entries(byType)
    .map(([t, list]) => `<li class="source-group"><strong>${esc(TYPE_LABELS[t] || titleCase(t))}</strong><ul>${list
      .map((s) => `<li>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a>` : esc(s.name)} <span class="meta">${esc([s.publisher, s.accessed && `accessed ${s.accessed}`].filter(Boolean).join(" · "))}</span></li>`)
      .join("")}</ul></li>`)
    .join("");
}

// ---------- tabs & theme ----------
const TABS = ["overview", "model", "data", "methodology"];
function showTab() {
  const t = TABS.includes(location.hash.slice(1)) ? location.hash.slice(1) : "overview";
  document.querySelectorAll("[data-panel]").forEach((p) => (p.hidden = p.dataset.panel !== t));
  document.querySelectorAll("[data-tab]").forEach((a) => a.classList.toggle("active", a.dataset.tab === t));
  window.scrollTo(0, 0);
  // charts in a hidden panel have zero size; resize once visible
  requestAnimationFrame(() => Object.values(state.charts).forEach((c) => c.resize()));
}
function renderAllCharts() {
  applyChartTheme();
  if (state.obs.length) { renderCapexChart(); renderGridChart(); renderExplorer(); }
  updateModel();
}
function setupTheme() {
  let saved = null;
  try { saved = localStorage.getItem("theme"); } catch {}
  if (saved) document.documentElement.dataset.theme = saved;
  $("#themeToggle").addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme
      ? document.documentElement.dataset.theme === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch {}
    renderAllCharts();
  });
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", renderAllCharts);
}

// ---------- boot ----------
async function boot() {
  setupTheme();
  const [obs, sources, model, md] = await Promise.all([
    loadJSON("data/observations.json", []),
    loadJSON("data/sources.json", []),
    loadJSON("data/model.json", { series: [], assumptions: [] }),
    loadText("data/METHODOLOGY.md"),
  ]);
  state.obs = (Array.isArray(obs) ? obs : []).map((o) => ({ ...o, value: Number(o.value) })).filter((o) => Number.isFinite(o.value));
  state.sources = Array.isArray(sources) ? sources : [];
  state.srcById = Object.fromEntries(state.sources.map((s) => [s.source_id, s]));
  state.model = model || { series: [], assumptions: [] };

  const placeholder = state.model.placeholder === true || state.obs.some((o) => o.source_name === "PLACEHOLDER");
  $("#placeholderBanner").hidden = !placeholder;
  const built = state.model.generated || state.obs.map((o) => o.source_date).filter(Boolean).sort().at(-1);
  $("#footerUpdated").textContent = built ? `Data as of ${built} · ${state.obs.length} data points from ${state.sources.length} sources` : "";

  $("#methodologyBody").innerHTML = md ? marked.parse(md) : "<p>Methodology coming soon.</p>";

  renderOverviewKpis();
  setupExplorer();
  setupModel();
  setupDataTab();
  showTab();
  renderAllCharts();
  window.addEventListener("hashchange", showTab);
}
boot();
