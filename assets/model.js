// Pure demand model: drivers in, yearly series out. No DOM access here.
// Mirrors data/model.json "formula" (written by data/build_data.py), so the
// sliders reproduce the published base case exactly at default values.

export const YEARS = [2024, 2025, 2026, 2027, 2028, 2029, 2030];

// Fallbacks used only when data/model.json lacks a key.
export const DEFAULT_ASSUMPTIONS = [
  { key: "ai_capex_usd_bn_2025", label: "Global AI data center capex, 2025", value: 550, low: 480, high: 650, unit: "USD_bn" },
  { key: "ai_capex_usd_bn_2026", label: "Global AI data center capex, 2026", value: 1000, low: 900, high: 1100, unit: "USD_bn" },
  { key: "capex_growth_pct", label: "Capex growth per year after 2026", value: 15, low: 0, high: 30, unit: "pct" },
  { key: "accel_share_of_capex_pct", label: "Share of capex spent on accelerators", value: 45, low: 35, high: 55, unit: "pct" },
  { key: "avg_accel_price_usd_k", label: "Cost per H100-equivalent, 2025", value: 21, low: 17, high: 26, unit: "USD_k" },
  { key: "price_decline_pct", label: "Annual decline in cost per H100e", value: 20, low: 10, high: 30, unit: "pct" },
  { key: "watts_per_accel", label: "IT power per H100e, 2025 vintage", value: 800, low: 600, high: 1000, unit: "W" },
  { key: "perf_per_watt_gain_pct", label: "Annual efficiency gain per vintage", value: 25, low: 15, high: 35, unit: "pct" },
  { key: "pue", label: "Power usage effectiveness", value: 1.25, low: 1.1, high: 1.4, unit: "ratio" },
  { key: "utilization_pct", label: "Average power draw vs nameplate", value: 65, low: 50, high: 80, unit: "pct" },
  { key: "inference_share_pct", label: "Inference share of compute, 2025", value: 45, low: 35, high: 55, unit: "pct" },
  { key: "inference_share_gain_pp", label: "Inference share gain per year", value: 5, low: 2, high: 8, unit: "pp" },
  { key: "accel_lifetime_years", label: "Accelerator lifetime", value: 5, low: 4, high: 6, unit: "years" },
];

const DEFAULT_HISTORY = {
  additions_h100e_m: { 2020: 0.1, 2021: 0.15, 2022: 0.25, 2023: 1.3, 2024: 4.7 },
  watts_per_h100e: { 2020: 1400, 2021: 1400, 2022: 1400, 2023: 1400, 2024: 1350 },
};

/**
 * @param {Record<string, number>} d driver values by key
 * @param {{additions_h100e_m: Record<string, number>, watts_per_h100e: Record<string, number>}} history pre-2025 vintages
 */
export function runModel(d, history = DEFAULT_HISTORY) {
  const hist = { ...DEFAULT_HISTORY, ...(history || {}) };
  const histYears = Object.keys(hist.additions_h100e_m).map(Number).sort((a, b) => a - b);
  const firstYear = Math.min(histYears[0] ?? 2020, YEARS[0]);
  const life = Math.max(1, Math.round(d.accel_lifetime_years));

  // per-vintage additions and watts, from the first history year to 2030
  const vintages = [];
  for (let y = firstYear; y <= YEARS.at(-1); y++) {
    let capex = null, accelSpend = null, price = null, additions, watts, reported = false;
    if (y <= 2024) {
      additions = Number(hist.additions_h100e_m[y] ?? 0);
      watts = Number(hist.watts_per_h100e[y] ?? 1400);
      reported = true;
    } else {
      capex = y === 2025 ? d.ai_capex_usd_bn_2025 : d.ai_capex_usd_bn_2026 * Math.pow(1 + d.capex_growth_pct / 100, y - 2026);
      accelSpend = (capex * d.accel_share_of_capex_pct) / 100;
      price = d.avg_accel_price_usd_k * Math.pow(1 - d.price_decline_pct / 100, y - 2025);
      additions = accelSpend / price; // USD bn / USD k = millions of H100e
      watts = d.watts_per_accel * Math.pow(1 - d.perf_per_watt_gain_pct / 100, y - 2025);
    }
    vintages.push({ year: y, capex, accelSpend, price, additions, watts, reported });
  }

  return YEARS.map((y) => {
    const v = vintages.find((x) => x.year === y);
    const live = vintages.filter((x) => x.year > y - life && x.year <= y);
    const stock = live.reduce((s, x) => s + x.additions, 0);
    const itGW = live.reduce((s, x) => s + x.additions * x.watts, 0) / 1000;
    const facilityGW = itGW * d.pue;
    const energyTWh = ((facilityGW * d.utilization_pct) / 100) * 8.76;
    const inferenceShare = Math.min(85, d.inference_share_pct + d.inference_share_gain_pp * (y - 2025)) / 100;
    return {
      year: y,
      capex: v.capex,
      accelSpend: v.accelSpend,
      price: v.price,
      additions: v.additions,
      reported: v.reported,
      watts: v.watts,
      stock,
      inferenceStock: stock * inferenceShare,
      trainingStock: stock * (1 - inferenceShare),
      inferenceShare,
      zettaflops: (stock * 1e6 * 989e12) / 1e21,
      itGW,
      facilityGW,
      energyTWh,
    };
  });
}

/** Fallback Low/High when model.json has no scenarios: move each driver halfway toward the end of its range that lowers / raises 2030 facility power. */
export function scenarioValues(assumptions, base, history, which) {
  const out = { ...base };
  for (const a of assumptions) {
    const lo = runModel({ ...base, [a.key]: a.low }, history).at(-1).facilityGW;
    const hi = runModel({ ...base, [a.key]: a.high }, history).at(-1).facilityGW;
    const lowerIsLow = lo <= hi;
    const target = which === "low" ? (lowerIsLow ? a.low : a.high) : (lowerIsLow ? a.high : a.low);
    out[a.key] = base[a.key] + (target - base[a.key]) * 0.5;
  }
  return out;
}
