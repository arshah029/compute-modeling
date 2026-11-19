# Global Compute Demand

A static website that models global compute demand (AI capex → accelerators → installed compute → power) and shows the source data behind it.

No build step. Everything is plain HTML, CSS and JavaScript, with Chart.js and marked vendored in `assets/vendor/`.

## Run locally

```bash
cd compute-modeling
python3 -m http.server 8000
# open http://localhost:8000
```

(Opening `index.html` directly from disk will not load the data files, because browsers block `fetch` on `file://`.)

## Layout

```
index.html            page shell: Overview, Model, Data, Methodology tabs
assets/app.js         loads data/, renders charts, tables and sliders
assets/model.js       the demand model (pure functions, no DOM)
assets/style.css      styles, light and dark themes
assets/vendor/        Chart.js 4.4.1, marked 12.0.2
data/                 the dataset (see contract below)
```

## Data contract (`data/`)

| File | Shape |
|---|---|
| `observations.json` (+ `.csv`) | array of `{id, category, metric, entity, period, period_type, value, unit, is_estimate, source_id, source_name, source_url, source_date, notes}`. `category` is one of `capex, accelerators, power, datacenter, semis, ai_usage, forecast`. |
| `sources.json` | array of `{source_id, name, publisher, url, type, accessed}` |
| `model.json` | `{series: [{name, unit, points: [{year, low, base, high}]}], assumptions: [{key, label, value, low, high, unit, description, source_ids}]}` |
| `METHODOLOGY.md` | Markdown, rendered on the Methodology tab |

What the site reads by name:

- Overview capex chart: `category=capex, metric=capex_usd`, one series per `entity`.
- Overview tiles: `power/datacenter_power_gw/Global`, `accelerators/shipments_units/Global`, first `model.json` series.
- Model: reported history from `accelerators/shipments_units/Global`; the research band from the `model.json` series whose name contains "power" and "compute".
- Model sliders: `model.json` assumptions with these keys (defaults in `assets/model.js` fill any gap): `ai_capex_usd_bn_2025, capex_growth_pct, accel_share_of_capex_pct, avg_accel_price_usd_k, price_growth_pct, perf_gain_pct, watts_per_accel, pue, utilization_pct, useful_life_years, inference_share_pct`.
- Everything else shows up in the "Explore the dataset" chart and the Data tab automatically.

A yellow "Preview data" banner shows while `model.json` has `"placeholder": true` or any row has `source_name: "PLACEHOLDER"`.

## Deploy

It is a static folder, so any static host works with no build command and the repo root as the output directory: GitHub Pages, Netlify, Vercel or Cloudflare Pages.
