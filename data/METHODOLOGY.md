# Global compute demand: data and methodology

Version 1.1, built 2026-11-19 (v1.1 adds trade, construction and grid data). Regenerate everything with `python3 data/build_data.py`.

## What is in this folder

| File | Contents |
|---|---|
| `observations.csv` / `observations.json` | 147 cited data points in tidy format (one row per value). Every row has `source_id`, `source_url` and `source_date`. |
| `sources.json` | 44 sources: SEC filings, earnings calls, industry and agency reports, alternative data. |
| `model.json` | Model output series (low / base / high, 2024-2030), the assumptions behind them (with ranges for sliders), the formulas, and benchmarks to plot against. |
| `build_data.py` | Single source of truth. All hand-entered numbers and the model live here. |

Categories in `observations`: `capex`, `accelerators`, `semis`, `power`, `datacenter`, `grid`, `trade`, `forecast`. Metric names are stable; new metrics will be added, not renamed.

## The question

How much AI compute is the world building, and what does it need in power? We measure compute in **H100-equivalents (H100e)**, meaning the number of NVIDIA H100 GPUs that would deliver the same dense BF16 throughput (989 TFLOP/s each). This is the unit Epoch AI uses, so our model can be checked against theirs.

## Three independent lenses

1. **Money (filings).** Hyperscaler capex from 10-Qs/10-Ks: Microsoft, Alphabet, Amazon, Meta and Oracle, plus Tencent and Alibaba. The Big 4 spent $376bn in 2025 and $497bn in the first nine months of 2026, and guide to roughly $730bn for full 2026. This is what buyers pay.
2. **Chips (supplier revenue).** NVIDIA data center revenue (most recently $108bn in the quarter to October 2026, guiding to $130bn total revenue next quarter), AMD Data Center, TSMC HPC revenue and its AI accelerator growth target (mid-to-high 50s % CAGR, 2024-29). This is what sellers receive, and it cross-checks lens 1.
3. **Physical (alternative data).** Epoch AI's chip-stock estimates (6.3M H100e added in Q2 2026 alone; additions doubling every ~9 months), IEA and Berkeley Lab electricity estimates, PJM load forecasts, ERCOT large-load interconnection requests (438 GW, mostly speculative), and JLL leasing data (25 GW absorbed in North America in H1 2026; 66 GW under construction).

## The model

A spend-driven chain, run per year (full formulas in `model.json.formula`):

1. **Capex.** 2025 = $550bn global AI data center capex (Big 4 $376bn + Oracle, China, neoclouds, labs, sovereign, enterprise). 2026 = $1,000bn from company guidance. After 2026, grow at `capex_growth_pct` (base 15%).
2. **Accelerator spend** = capex x 45%. Calibrated: calendar 2025 NVIDIA DC revenue (~$194bn) plus AMD, Google TPU, Trainium and others (~$55bn) is about 45% of $550bn.
3. **Compute added** = spend / cost per H100e. Cost is $21k per H100e in 2025 (chip plus networking), falling 20% a year. Calibrated so 2025 additions (~11.8M) match Epoch's quarterly series.
4. **Installed base** = additions over the last 5 years (older vintages retire).
5. **Power.** Each vintage keeps the watts it was installed with: ~1,400 W per H100e for 2023 and earlier, 1,350 W for 2024 (H100/H200 servers), 800 W for 2025 (Blackwell systems), then 25% less each year. Multiply by PUE 1.25 for facility power.
6. **Energy** = facility GW x 65% average utilization x 8,760 h.
7. **Inference vs training.** Inference is 45% of installed compute in 2025, rising 5 points a year (cap 85%).

**Scenarios.** Low and high move the demand-sensitive assumptions together (2026 capex, growth, accelerator share, price decline, efficiency gain, utilization). They are deliberately wide, so read them as a range of plausible outcomes rather than a confidence interval.

## Base-case results (2030)

- Installed AI compute: ~315M H100e (about 17x end-2025; range ~145-700M).
- AI data center power capacity: ~117 GW facility (range ~50-300 GW).
- AI data center electricity: ~670 TWh (range ~240-1,960 TWh).

## How this compares to benchmarks

- **Epoch AI (Jan 2026): 15M+ H100e and >10 GW.** We have 18M H100e at end-2025, which is close. Our power is higher (18 GW IT, 23 GW facility) because we count full server and cluster power, not chip power alone.
- **IEA Base Case: 945 TWh for *all* data centres in 2030.** Our AI-only base (~670 TWh) would mean AI is about 70% of IEA's total. The IEA scenario was published in April 2025, before the 2026 capex step-up, so our base sits closer to IEA's "Lift-Off" path. This is the biggest open question in the model. If capex flattens after 2026, the low case (~240 TWh) is consistent with IEA.
- **Grid signals.** PJM expects summer peak to reach 183 GW by 2030, driven by data centers. ERCOT's 438 GW of large-load requests far exceeds any plausible build, so we treat queues as an upper bound on intent, not as demand.

## Caveats

- Some Q1 FY27 NVIDIA data center revenue ($75.4bn) is derived from reported sequential growth (flagged `is_estimate=true`).
- A few figures come from secondary reporting of filings (noted in `sources.json`; the type is `report`). Primary SEC links are used where available.
- Hyperscaler capex includes non-AI items (for example Amazon logistics). The 45% accelerator share absorbs that.
- China is under-observed. Domestic chips (Huawei Ascend, Cambricon) are in Epoch's stock but not in our capex series.
- Nothing here uses paid data. SemiAnalysis, TrendForce, Synergy and Dell'Oro would sharpen chip unit and capacity figures if you decide to buy access.

## Alternative data (v1.1)

These series don't feed the model directly. They are independent checks that the spending is turning into physical hardware and grid load.

**Trade flows: the hardware is physically shipping.**
- Taiwan's exports hit a record $96.8bn in October 2026 (+59% YoY). ICT and audio-video products, mostly AI servers, were $47.6bn (+73%).
- South Korea's chip exports were $56.4bn in October 2026 (+259% YoY), driven by memory prices and HBM.
- US imports of AI servers from Taiwan ($72bn) and Mexico ($60bn) in H1 2026 imply roughly $175bn from all countries in six months, a similar scale to NVIDIA's data center revenue.
- The Fed's HS-code definition (8471.50, 8471.80, 8473.30) is the standard way to pull this from Census/UN Comtrade.

**Construction: shells are being built.**
- US Census data center construction spending reached a $96.5bn annual rate in September 2026, up 90% YoY.
- ConstructConnect counts $84bn of starts in the first seven months of 2026 (~3x a year earlier).
- Loudoun County's 12-month pause on new applications (September 2026) is a supply constraint signal.

**Grid: utilities report contracts, not just queues.**
- Dominion has >53 GW in contracting, of which 12 GW is under electric service agreements.
- Southern Company has 17 GW contracted.
- MISO expects 8 to 14 GW online in 2026-27. Malaysia's TNB has 8.3 GW under supply agreements (4.5 GW connected). Ireland's data centres used 23% of the country's electricity in 2025.
- **How to read these:** signed contracts (ESAs, commitments) are much firmer than request queues. ERCOT's 438 GW and Georgia Power's 51 GW pipeline include a lot of speculative and duplicate requests. The model's ~43 GW of global AI facility power in 2026 sits well inside the sum of contracted US loads alone, which supports the near-term numbers.

## Next data to add

Quarterly updates from Q4 2026 earnings (late Jan to Feb 2027), CoreWeave/Nebius 10-Qs, SK hynix and Micron HBM revenue, EIA-861 utility sales to data centers, a monthly US Census HS 8471/8473 import series (needs a free Census API key), Maricopa and Texas county permits, and European grid data (EirGrid, Netherlands, Frankfurt).
