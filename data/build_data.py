#!/usr/bin/env python3
"""Builds observations.csv/json, sources.json and model.json for the compute demand site.

Run:  python3 data/build_data.py   (writes next to this file)
All hand-entered numbers live in SOURCES / OBS / ASSUMPTIONS below, each tied to a source_id.
"""
import csv, json, os, copy

HERE = os.path.dirname(os.path.abspath(__file__))
ACCESSED = "2026-11-19"

# ---------------------------------------------------------------- sources
SOURCES = [
    # filings / earnings
    ("msft_10q_2026q3", "Microsoft 10-Q, quarter ended 2026-09-30 (FY27 Q1)", "Microsoft / SEC EDGAR", "https://www.sec.gov/Archives/edgar/data/789019/000119312526436133/msft-20260930.htm", "filing"),
    ("msft_call_fy27q1", "Microsoft FY27 Q1 earnings call (2026-10-28)", "Microsoft", "https://www.microsoft.com/en-us/investor/events/fy-2027/earnings-fy-2027-q1", "earnings_call"),
    ("googl_10q_2026q3", "Alphabet 10-Q, quarter ended 2026-09-30", "Alphabet / SEC EDGAR", "https://www.sec.gov/Archives/edgar/data/1652044/000165204426000084/goog-20260930.htm", "filing"),
    ("googl_call_2026q3", "Alphabet Q3 2026 earnings call (2026-10-28)", "Alphabet", "https://abc.xyz/investor/events/event-details/2026/2026-Q3-Earnings-Call-2026-Ujou16CTw9/default.aspx", "earnings_call"),
    ("amzn_10q_2026q3", "Amazon 10-Q, quarter ended 2026-09-30", "Amazon / SEC EDGAR", "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000040/amzn-20260930.htm", "filing"),
    ("amzn_pr_2026q3", "Amazon Q3 2026 earnings release (2026-10-29)", "Amazon / SEC EDGAR", "https://www.sec.gov/Archives/edgar/data/1018724/000101872426000038/amzn-20260930xex991.htm", "filing"),
    ("meta_10q_2026q3", "Meta 10-Q, quarter ended 2026-09-30", "Meta / SEC EDGAR", "https://www.sec.gov/Archives/edgar/data/1326801/000162828026066773/meta-20260930.htm", "filing"),
    ("meta_pr_2026q3", "Meta Q3 2026 earnings release", "Meta / SEC EDGAR", "https://www.sec.gov/Archives/edgar/data/1326801/000162828026066700/meta-09302026xexhibit991.htm", "filing"),
    ("orcl_10q_fy27q1", "Oracle 10-Q, quarter ended 2026-08-31 (FY27 Q1)", "Oracle / SEC EDGAR", "https://www.sec.gov/Archives/edgar/data/1341439/000119312526389274/orcl-20260831.htm", "filing"),
    ("orcl_fy27_guide", "Reuters via The Star: Oracle FY26 Q4 results and FY27 capex outlook (2026-06-11)", "Reuters", "https://www.thestar.com.my/tech/tech-news/2026/06/11/oracle-beats-fourth-quarter-revenue-estimates-amid-ai-spending-worries", "report"),
    ("capex_tracker", "AI Capex Tracker: hyperscaler capex by quarter (compiled from 10-Q/10-K cash flow statements)", "Walnut Invest", "https://walnutinvest.com/stats/ai-capex-statistics", "report"),
    ("uao_q3_capex", "Hyperscaler Q3 capex, debt, equity and leases", "Universal Asset Owners", "https://www.universalassetowners.com/newsroom/hyperscaler-q3-capex-debt-equity-leases/", "report"),
    ("nvda_call_fy27q3", "NVIDIA Q3 FY2027 earnings call transcript (2026-11-17)", "Investing.com", "https://www.investing.com/news/transcripts/earnings-call-transcript-nvidia-tops-q3-2026-estimates-and-lifts-outlook-93CH-5034300", "earnings_call"),
    ("nvda_tc_fy27q3", "Nvidia promises that revenue will keep soaring (2026-11-17)", "TechCrunch", "https://techcrunch.com/2026/11/17/nvidia-promises-that-revenue-will-keep-soaring-for-now/", "report"),
    ("nvda_fy27q2", "Nvidia posts $96.2B quarter as data center revenue hits $89B (2026-08-26)", "Unite.AI", "https://www.unite.ai/nvidia-posts-96-2b-quarter-as-data-center-revenue-hits-89b/", "report"),
    ("nvda_fy26q3", "Nvidia's Q3 data center sales soar 56% (FY2026 Q3)", "Zacks", "https://www.zacks.com/stock/news/2798118/nvidias-q3-data-center-sales-soar-56-can-nvda-sustain-the-momentum", "report"),
    ("nvda_ir", "NVIDIA quarterly results (investor relations; FY2025 and FY2026 data center revenue)", "NVIDIA", "https://investor.nvidia.com/financial-info/quarterly-results/default.aspx", "filing"),
    ("amd_8k_2026q3", "AMD Q3 2026 earnings release, Form 8-K Ex.99.1 (2026-11-03)", "AMD / SEC EDGAR", "https://www.sec.gov/Archives/edgar/data/0000002488/000000248826000188/q32026991.htm", "filing"),
    ("tsmc_2026q3", "TSMC Q3 FY2026 earnings beat and raise on AI and HPC demand (2026-10-20)", "Futurum Group", "https://futurumgroup.com/insights/tsmc-q3-fy-2026-earnings-beat-and-raise-on-ai-and-hpc-demand/", "report"),
    ("tencent_2026q1", "Tencent and Alibaba accelerate AI spending (2026-05-15)", "GMT8 Press", "https://gmt8press.com/content/detail/390099", "report"),
    # alternative / power data
    ("epoch_additions", "AI computing capacity additions are doubling every 9 months (data to 2026-10-19)", "Epoch AI", "https://epoch.ai/data-insights/ai-computing-capacity-additions-doubling", "alt_data"),
    ("epoch_chip_owners", "AI Chip Owners / Users explorer (15M+ H100e, >10 GW; 2026-01-08)", "Epoch AI via The Decoder", "https://the-decoder.com/global-ai-compute-hits-15-million-h100-equivalents-epoch-ai-finds/", "alt_data"),
    ("iea_energy_ai", "Energy and AI: Energy demand from AI", "International Energy Agency", "https://iea.org/reports/energy-and-ai/energy-demand-from-ai", "report"),
    ("lbnl_2024", "2024 United States Data Center Energy Usage Report (Berkeley Lab / DOE)", "Lawrence Berkeley National Laboratory", "https://energyanalysis.lbl.gov/news/berkeley-lab-report-evaluates-increase-electricity-demand-data-centers", "report"),
    ("pjm_2026_forecast", "PJM 2026 long-term load forecast (released 2026-01-14)", "PJM Interconnection", "https://insidelines.pjm.com/pjms-updated-20-year-forecast-continues-to-see-significant-long-term-load-growth/", "alt_data"),
    ("ercot_large_load", "ERCOT large-load requests climb to 438 GW (ERCOT data 2026-05-24)", "New Project Media", "https://newprojectmedia.com/origination-ercot-large-load-requests-climb-to-438-gw-17-new-gas-generation-filings-in-last-60-days/", "alt_data"),
    ("jll_na_h1_2026", "JLL North America Data Center Report, Midyear 2026 (2026-08-11)", "JLL", "https://www.jll.com/en-us/newsroom/data-center-demand-exceeds-expectations-in-h1-2026", "alt_data"),
    ("nvidia_specs", "NVIDIA DGX H100 / DGX B200 / GB300 NVL72 published system power and FLOPs specs", "NVIDIA", "https://www.nvidia.com/en-us/data-center/dgx-b200/", "report"),
    # alternative data v1.1: trade, construction, grid
    ("twn_mof_2026_10", "Taiwan's October exports hit high, jump nearly 60% on AI demand (Ministry of Finance data, 2026-11-09)", "Focus Taiwan / CNA", "https://focustaiwan.tw/business/202611090020", "alt_data"),
    ("twn_mof_2026_06", "Taiwan June 2026 exports (Ministry of Finance data, 2026-07-10)", "Taipei Times", "https://www.taipeitimes.com/News/biz/archives/2026/07/10/2003860490", "alt_data"),
    ("kor_motir_2026_10", "Korea's monthly exports hit $115.3 bil. in Oct. on record chip sales (MOTIR data, 2026-11-01)", "Korea Times", "https://www.koreatimes.co.kr/economy/20261101/koreas-monthly-exports-hit-1153-bil-in-oct-on-record-chip-sales", "alt_data"),
    ("mex_banamex_servers", "Mexico moves past Taiwan as top AI server exporter to the US (Banamex analysis of US import data)", "Mexico News Daily", "https://mexiconewsdaily.com/business/mexico-moves-past-taiwan-as-top-ai-server-exporter-to-united-states/", "alt_data"),
    ("fed_ai_trade", "The global trade effects of the AI infrastructure boom (FEDS Notes, 2026-02-13)", "Federal Reserve Board", "https://www.federalreserve.gov/econres/notes/feds-notes/the-global-trade-effects-of-the-ai-infrastructure-boom-20260213.html", "report"),
    ("census_c30_2026_09", "US Census construction spending (C30), data center category, September 2026 release (2026-11-02)", "US Census Bureau via FourWeekMBA", "https://fourweekmba.com/ai-us-data-center-construction-hit-a-record-96-5b-rate/", "alt_data"),
    ("constructconnect_2026_09", "September 2026 Data Center Report: YTD spending nearly 3x a year ago", "ConstructConnect", "https://news.constructconnect.com/september-2026-data-center-report-year-to-date-spending-nearly-three-times-a-year-ago", "alt_data"),
    ("loudoun_pause", "Loudoun County board votes to pause new data center applications (2026-09-18)", "Baxtel", "https://baxtel.com/news/loudoun-county-board-votes-to-pause-new-data-center-applications", "alt_data"),
    ("dominion_q2_2026", "Dominion Energy Q2 2026 earnings call highlights (2026-07-31)", "Nasdaq", "https://www.nasdaq.com/articles/dominion-energy-q2-earnings-call-highlights", "earnings_call"),
    ("southern_q2_2026", "Southern Co. contracted large load reaches 17 GW (2026-08-04)", "Utility Dive", "https://www.utilitydive.com/news/southern-co-contracted-large-load-data-centers/826919/", "earnings_call"),
    ("gpc_q3_2025_large_load", "Georgia Power Q3 2025 large load report to Georgia PSC (2025-11-24)", "Utility Dive", "https://www.utilitydive.com/news/georgia-power-large-load-data-centers/806300/", "alt_data"),
    ("miso_2026_forecast", "MISO long-range load forecast (workshop 2026-04-13)", "Utility Dive", "https://www.utilitydive.com/news/miso-long-range-forecast-data-center/817917/", "alt_data"),
    ("rto_large_load_survey", "RTOs and ISOs answer: how all six grid operators plan to respond to the large load surge (2026-07)", "Climate Solutions Law (Sheppard Mullin)", "https://www.climatesolutionslaw.com/2026/07/rtos-and-isos-answer-a-national-preview-of-how-all-six-grid-operators-plan-to-respond-to-the-large-load-surge/", "report"),
    ("tnb_dc_2026", "TNB locks in growth securing 59 data centre projects with 8.3GW capacity (2026-07-11)", "Business Today Malaysia", "https://www.businesstoday.com.my/2026/07/11/tnb-locks-in-growth-securing-59-data-centre-projects-with-8-3gw-capacity/", "alt_data"),
    ("cso_ireland_2025", "Data centres account for almost a quarter of Irish electricity usage in 2025 (CSO data, 2026-07-07)", "Irish Times", "https://www.irishtimes.com/business/2026/07/07/data-centres-account-for-almost-one-quarter-of-irish-electricity-usage-in-2025/", "alt_data"),
    ("analyst_estimate", "Model assumption or derived estimate by this project (see METHODOLOGY.md)", "compute-modeling project", "", "estimate"),
]

# ---------------------------------------------------------------- observations
# (category, metric, entity, period, period_type, value, unit, is_estimate, source_id, source_date, notes)
OBS = []
def o(*a): OBS.append(a)

# Hyperscaler quarterly capex (USD bn, cash purchases/additions of PP&E; calendar quarters)
q = ["2024Q3","2024Q4","2025Q1","2025Q2","2025Q3","2025Q4","2026Q1","2026Q2","2026Q3"]
capex_q = {
    "Microsoft": [14.9,15.8,16.7,17.1,19.4,29.9,30.9,35.8,39.4],
    "Alphabet":  [13.1,14.3,17.2,22.4,24.0,27.9,35.7,44.9,51.4],
    "Amazon":    [22.6,27.8,25.0,32.2,35.1,39.5,44.2,54.2,77.3],
    "Meta":      [8.3,14.4,12.9,16.5,18.8,21.4,19.0,30.1,33.9],
}
tenq = {"Microsoft":"msft_10q_2026q3","Alphabet":"googl_10q_2026q3","Amazon":"amzn_10q_2026q3","Meta":"meta_10q_2026q3"}
for co, vals in capex_q.items():
    for p, v in zip(q, vals):
        sid = tenq[co] if p == "2026Q3" else "capex_tracker"
        note = "Cash purchases of property and equipment (Microsoft: additions to P&E). Single quarters derived from YTD cash flow statements."
        if co == "Microsoft": note += " Microsoft fiscal year ends June; calendar quarter shown."
        o("capex","capex_usd",co,p,"quarter",v,"USD_bn",False,sid,"2026-11-01" if p=="2026Q3" else ACCESSED,note)
o("capex","capex_incl_finance_leases_usd","Microsoft","2026Q3","quarter",45.2,"USD_bn",False,"uao_q3_capex","2026-10-28","Including finance leases.")

# Annual
for co, y, v, sid, n in [
    ("Alphabet","2025",91.4,"capex_tracker","Sum of 2025 quarters per 10-K."),
    ("Amazon","2025",131.8,"capex_tracker","Cash capex."),
    ("Meta","2025",69.7,"capex_tracker","Purchases of P&E; $72.2bn incl. finance lease principal."),
    ("Microsoft","2025",83.1,"capex_tracker","Calendar 2025 sum of quarterly cash additions to P&E (derived)."),
    ("Big4","2025",376.1,"capex_tracker","Microsoft+Alphabet+Amazon+Meta, calendar 2025."),
    ("Big4","2026_9M",496.7,"capex_tracker","First nine months of 2026."),
]:
    o("capex","capex_usd",co,y,"CY",v,"USD_bn",False,sid,ACCESSED,n)
o("capex","capex_usd","Oracle","FY2025","FY",21.2,"USD_bn",False,"capex_tracker",ACCESSED,"Fiscal year ended May 2025.")
o("capex","capex_usd","Oracle","FY2026","FY",55.7,"USD_bn",False,"capex_tracker",ACCESSED,"Fiscal year ended May 2026.")
for p, v in [("FY2026Q1",8.5),("FY2026Q2",12.0),("FY2026Q3",18.6),("FY2026Q4",16.5),("FY2027Q1",28.5)]:
    o("capex","capex_usd","Oracle",p,"quarter",v,"USD_bn",False,"orcl_10q_fy27q1" if p=="FY2027Q1" else "capex_tracker",ACCESSED,"Oracle fiscal quarters (FY ends May).")

# Oracle mapped to nearest calendar quarter (fiscal quarters end Aug/Nov/Feb/May, one month after calendar quarter ends)
for p_cal, p_fy, v in [("2024Q3","FY2025Q1",2.3),("2024Q4","FY2025Q2",4.0),("2025Q1","FY2025Q3",5.9),("2025Q2","FY2025Q4",9.1),
                       ("2025Q3","FY2026Q1",8.5),("2025Q4","FY2026Q2",12.0),("2026Q1","FY2026Q3",18.6),("2026Q2","FY2026Q4",16.5),("2026Q3","FY2027Q1",28.5)]:
    o("capex","capex_usd","Oracle",p_cal,"quarter",v,"USD_bn",False,"orcl_10q_fy27q1" if p_fy=="FY2027Q1" else "capex_tracker",ACCESSED,
      f"Oracle fiscal {p_fy} shown at nearest calendar quarter; Oracle quarters end one month later (Aug/Nov/Feb/May).")

# Guidance (forecast category)
for co, p, v, sid, d, n in [
    ("Microsoft","2026","170","msft_call_fy27q1","2026-10-28","CFO: calendar 2026 spending 'approximately $170 billion' incl. finance leases."),
    ("Microsoft","2026Q4","50","msft_call_fy27q1","2026-10-28","'Over $50 billion' for Oct-Dec 2026 quarter (lower bound)."),
    ("Alphabet","2026","200","googl_call_2026q3","2026-10-28","Guidance range $195-205bn; midpoint shown."),
    ("Amazon","2026","220","amzn_pr_2026q3","2026-10-29","About $220bn cash capex."),
    ("Meta","2026","140","meta_pr_2026q3","2026-10-21","Guidance $135-145bn incl. finance lease principal; midpoint shown."),
    ("Oracle","FY2027","95","orcl_fy27_guide","2026-06-11","'Up to ~$95bn' for FY ending May 2027 (secondary report)."),
    ("Alibaba","FY2026-FY2028","380","tencent_2026q1","2026-05-15","RMB 380bn three-year AI/cloud infrastructure commitment (announced Feb 2025); value in RMB_bn."),
]:
    o("forecast","capex_guidance_usd",co,p,"FY" if p.startswith("FY") else ("quarter" if "Q" in p else "CY"),float(v),"RMB_bn" if co=="Alibaba" else "USD_bn",False,sid,d,n)
o("capex","capex_rmb","Tencent","2026Q1","quarter",31.94,"RMB_bn",False,"tencent_2026q1","2026-05-15","Up 16% YoY; management guided higher AI spend in H2 2026.")

# Accelerators: NVIDIA data center revenue (fiscal quarters; FY ends late January)
nv = [
    ("FY2026Q1",39.1,"nvda_ir","2025-05-28","Quarter ended Apr 2025."),
    ("FY2026Q2",41.1,"nvda_ir","2025-08-27","Quarter ended Jul 2025."),
    ("FY2026Q3",51.2,"nvda_fy26q3","2025-11-19","Quarter ended Oct 2025; +66% YoY."),
    ("FY2026Q4",62.3,"nvda_ir","2026-02-25","Quarter ended Jan 2026."),
    ("FY2027Q1",75.4,"nvda_fy27q2","2026-08-26","Implied from Q2 FY27 $89.0bn being +18% QoQ; derived, not reported directly."),
    ("FY2027Q2",89.0,"nvda_fy27q2","2026-08-26","Quarter ended 2026-07-26."),
    ("FY2027Q3",108.0,"nvda_call_fy27q3","2026-11-17","+21% QoQ. Vera Rubin ~$20bn in first production quarter."),
]
for p, v, sid, d, n in nv:
    o("accelerators","nvidia_dc_revenue_usd","NVIDIA",p,"quarter",v,"USD_bn",p=="FY2027Q1",sid,d,n)
o("accelerators","nvidia_dc_revenue_usd","NVIDIA","FY2025","FY",115.2,"USD_bn",False,"nvda_ir","2025-02-26","FY ended Jan 2025.")
o("accelerators","nvidia_dc_revenue_usd","NVIDIA","FY2026","FY",193.7,"USD_bn",False,"nvda_ir","2026-02-25","Sum of FY26 quarters (~calendar 2025).")
o("accelerators","nvidia_total_revenue_usd","NVIDIA","FY2027Q3","quarter",115.8,"USD_bn",False,"nvda_tc_fy27q3","2026-11-17","+103% YoY; above $108bn guide.")
o("accelerators","nvidia_total_revenue_usd","NVIDIA","FY2027Q2","quarter",96.2,"USD_bn",False,"nvda_fy27q2","2026-08-26","")
o("forecast","nvidia_revenue_guidance_usd","NVIDIA","FY2027Q4","quarter",130.0,"USD_bn",False,"nvda_tc_fy27q3","2026-11-17","Guide $130bn +/-3% for quarter ending Jan 2027.")
o("accelerators","amd_dc_revenue_usd","AMD","2026Q3","quarter",8.546,"USD_bn",False,"amd_8k_2026q3","2026-11-03","Data Center segment (EPYC + Instinct), +97% YoY.")
o("accelerators","amd_dc_revenue_usd","AMD","2025Q3","quarter",4.341,"USD_bn",False,"amd_8k_2026q3","2026-11-03","")
o("forecast","amd_revenue_guidance_usd","AMD","2026Q4","quarter",17.0,"USD_bn",False,"amd_8k_2026q3","2026-11-03","Total revenue guide +/-3%.")

# Semis supply chain
o("semis","tsmc_revenue_usd","TSMC","2026Q3","quarter",46.72,"USD_bn",False,"tsmc_2026q3","2026-10-20","+50.9% YoY in NT$.")
o("semis","tsmc_hpc_share_pct","TSMC","2026Q3","quarter",68,"pct",False,"tsmc_2026q3","2026-10-20","HPC platform share of revenue.")
o("semis","tsmc_capex_guidance_usd","TSMC","2026","CY",62,"USD_bn",False,"tsmc_2026q3","2026-10-20","Guide $60-64bn; midpoint.")
o("forecast","tsmc_ai_accel_revenue_cagr_pct","TSMC","2024-2029","CY",55,"pct",False,"tsmc_2026q3","2026-10-20","'Mid-to-high 50s' % CAGR, management said may be conservative; 55 shown as lower bound.")

# AI compute stock (Epoch)
o("accelerators","ai_compute_additions_h100e","Global","2024Q1","quarter",0.8,"units_m",True,"epoch_additions","2026-10-29","Quarterly AI compute additions, millions of H100-equivalents.")
o("accelerators","ai_compute_additions_h100e","Global","2026Q2","quarter",6.3,"units_m",True,"epoch_additions","2026-10-29","Additions growing ~2.5x/yr since 2024; doubling ~9 months.")
o("accelerators","ai_compute_stock_h100e","Global","2026-01","CY",15.0,"units_m",True,"epoch_chip_owners","2026-01-08","'Exceeds 15 million H100 equivalents' (lower bound).")
o("power","ai_chip_power_gw","Global","2026-01","CY",10.0,"GW",True,"epoch_chip_owners","2026-01-08","'Over 10 GW' required by installed AI chips (lower bound).")

# Power / energy
o("power","dc_electricity_twh","Global","2024","CY",415,"TWh",True,"iea_energy_ai",ACCESSED,"~1.5% of global electricity.")
o("forecast","dc_electricity_twh","Global","2030","CY",945,"TWh",True,"iea_energy_ai",ACCESSED,"IEA Base Case; just under 3% of global electricity.")
o("forecast","dc_electricity_twh_liftoff","Global","2035","CY",1700,"TWh",True,"iea_energy_ai",ACCESSED,"IEA Lift-Off scenario (>1,700).")
o("forecast","dc_electricity_twh_high_eff","Global","2035","CY",970,"TWh",True,"iea_energy_ai",ACCESSED,"IEA High Efficiency scenario.")
o("forecast","dc_electricity_twh_headwinds","Global","2035","CY",700,"TWh",True,"iea_energy_ai",ACCESSED,"IEA Headwinds scenario plateau.")
o("forecast","dc_electricity_increase_twh","US","2024-2030","CY",240,"TWh",True,"iea_energy_ai",ACCESSED,"IEA Base Case increase (+130%).")
o("forecast","dc_electricity_increase_twh","China","2024-2030","CY",175,"TWh",True,"iea_energy_ai",ACCESSED,"IEA Base Case increase (+170%).")
o("forecast","dc_electricity_increase_twh","Europe","2024-2030","CY",45,"TWh",True,"iea_energy_ai",ACCESSED,"IEA Base Case increase (+70%), lower bound.")
o("power","dc_electricity_twh","US","2023","CY",176,"TWh",False,"lbnl_2024","2024-12-20","4.4% of US electricity.")
o("forecast","dc_electricity_twh_low","US","2028","CY",325,"TWh",True,"lbnl_2024","2024-12-20","LBNL low scenario (6.7% of US electricity).")
o("forecast","dc_electricity_twh_high","US","2028","CY",580,"TWh",True,"lbnl_2024","2024-12-20","LBNL high scenario (12%).")
o("forecast","summer_peak_gw","PJM","2030","CY",183.0,"GW",True,"pjm_2026_forecast","2026-01-14","2026 load forecast; large loads (mainly data centers) drive growth.")
o("forecast","summer_peak_gw","PJM","2036","CY",222.0,"GW",True,"pjm_2026_forecast","2026-01-14","Approximate.")
o("datacenter","large_load_requests_gw","ERCOT","2026-05","CY",438,"GW",False,"ercot_large_load","2026-05-24","Large-load interconnection requests; >300 GW lack submitted studies, so mostly speculative.")
o("datacenter","large_load_requests_gw","ERCOT","2026-04","CY",410,"GW",True,"ercot_large_load","2026-05-24","Implied (+28 GW since April board meeting).")
o("datacenter","absorption_gw","North America","2026H1","CY",25,"GW",False,"jll_na_h1_2026","2026-08-11","Record; 2x year earlier, 5x two years earlier.")
o("datacenter","under_construction_gw","North America","2026H1","CY",66,"GW",False,"jll_na_h1_2026","2026-08-11","95% pre-committed.")

# ---- v1.1 alternative data: trade flows (category "trade")
o("trade","exports_total_usd","Taiwan","2026-10","month",96.76,"USD_bn",False,"twn_mof_2026_10","2026-11-09","Record; +58.9% YoY.")
o("trade","exports_ict_av_usd","Taiwan","2026-10","month",47.60,"USD_bn",False,"twn_mof_2026_10","2026-11-09","ICT and audio-video products (mostly AI servers); +72.9% YoY.")
o("trade","exports_electronic_components_usd","Taiwan","2026-10","month",32.68,"USD_bn",False,"twn_mof_2026_10","2026-11-09","Mainly semiconductors; +61.4% YoY.")
o("trade","exports_to_us_usd","Taiwan","2026-10","month",32.93,"USD_bn",False,"twn_mof_2026_10","2026-11-09","+55.9% YoY; 34% of total exports.")
o("trade","exports_total_usd","Taiwan","2026_10M","CY",758.29,"USD_bn",False,"twn_mof_2026_10","2026-11-09","Jan-Oct 2026; +47.7% YoY.")
o("trade","exports_total_usd","Taiwan","2026-06","month",74.83,"USD_bn",False,"twn_mof_2026_06","2026-07-10","+40.3% YoY.")
o("trade","exports_ict_av_usd","Taiwan","2026-06","month",33.92,"USD_bn",False,"twn_mof_2026_06","2026-07-10","+72.3% YoY.")
o("trade","exports_electronic_components_usd","Taiwan","2026-06","month",25.39,"USD_bn",False,"twn_mof_2026_06","2026-07-10","+32.8% YoY.")
o("trade","exports_to_us_usd","Taiwan","2026-06","month",23.28,"USD_bn",False,"twn_mof_2026_06","2026-07-10","+34.8% YoY.")
o("trade","exports_semiconductor_usd","South Korea","2026-10","month",56.4,"USD_bn",False,"kor_motir_2026_10","2026-11-01","+259% YoY (memory prices and HBM); ~49% of Korea's exports.")
o("trade","exports_total_usd","South Korea","2026-10","month",115.3,"USD_bn",False,"kor_motir_2026_10","2026-11-01","Record; +93.7% YoY.")
o("trade","us_ai_server_imports_usd","Taiwan","2026H1","CY",72.2,"USD_bn",False,"mex_banamex_servers",ACCESSED,"US imports of AI servers and related components from Taiwan; 36% share.")
o("trade","us_ai_server_imports_usd","Mexico","2026H1","CY",60.4,"USD_bn",False,"mex_banamex_servers",ACCESSED,"34.5% share; Mexico passed Taiwan monthly in May 2026 (Foxconn/Flex assembly).")
o("trade","us_ai_server_imports_usd","All countries","2026H1","CY",175,"USD_bn",True,"mex_banamex_servers",ACCESSED,"Derived: Mexico $60.4bn / 34.5% share.")
o("trade","global_ai_goods_trade_usd","Global","2025H1","CY",272,"USD_bn",False,"fed_ai_trade","2026-02-13","Servers, GPUs and parts (HS 8471.50, 8471.80, 8473.30), +65% YoY; lower bound.")

# ---- construction and permits (category "datacenter")
o("datacenter","construction_spending_saar_usd","US","2026-09","month",96.5,"USD_bn",False,"census_c30_2026_09","2026-11-02","Census C30 data center category, seasonally adjusted annual rate; +90% YoY vs $50.7bn.")
o("datacenter","construction_spending_saar_usd","US","2026-08","month",88.8,"USD_bn",False,"census_c30_2026_09","2026-11-02","Revised.")
o("datacenter","construction_spending_saar_usd","US","2026-07","month",80.7,"USD_bn",False,"census_c30_2026_09","2026-11-02","Revised.")
o("datacenter","construction_spending_saar_usd","US","2025-09","month",50.7,"USD_bn",False,"census_c30_2026_09","2026-11-02","")
o("datacenter","construction_starts_usd","US","2026_7M","CY",84.1,"USD_bn",False,"constructconnect_2026_09","2026-09","Jan-Jul 2026 starts (136 projects); ~3x a year earlier.")
o("datacenter","construction_pipeline_usd","US","2026","CY",78.7,"USD_bn",False,"constructconnect_2026_09","2026-09","85 preconstruction projects slated to start by end-2026 (not guaranteed).")
o("datacenter","avg_project_cost_usd","US","2026_7M","CY",1.06,"USD_bn",False,"constructconnect_2026_09","2026-09","vs $0.35bn in 2025.")
o("datacenter","application_moratorium_months","Loudoun County VA","2026-09","CY",12,"months",False,"loudoun_pause","2026-09-18","12-month pause on new data center applications (vote 7-1); by-right zoning removed. Supply-side constraint signal.")

# ---- grid: utility pipelines and operator forecasts (category "grid")
o("grid","dc_pipeline_gw","Dominion Energy","2026Q2","quarter",53,"GW",False,"dominion_q2_2026","2026-07-31","Data center capacity 'in various stages of contracting' (>53 GW).")
o("grid","dc_contracted_esa_gw","Dominion Energy","2026Q2","quarter",12,"GW",False,"dominion_q2_2026","2026-07-31","Under electric service agreements.")
o("grid","contracted_large_load_gw","Southern Company","2026Q2","quarter",17,"GW",False,"southern_q2_2026","2026-08-04","+6 GW since Q1 2026; includes 3.2 GW OpenAI contract near Savannah (service from 2028).")
o("grid","advanced_pipeline_gw","Southern Company","2026Q2","quarter",8,"GW",False,"southern_q2_2026","2026-08-04","Advanced stages of contracting.")
o("grid","dc_electricity_growth_pct","Southern Company","2026Q2","quarter",55,"pct",False,"southern_q2_2026","2026-08-04","YoY growth in data center electricity usage.")
o("grid","large_load_pipeline_gw","Georgia Power","2025Q3","quarter",50.9,"GW",False,"gpc_q3_2025_large_load","2025-11-24","Economic development pipeline, down 6 GW QoQ (speculative requests dropping out).")
o("grid","committed_large_load_gw","Georgia Power","2025Q3","quarter",11,"GW",False,"gpc_q3_2025_large_load","2025-11-24","28 customers.")
o("grid","summer_peak_gw","MISO","2025","CY",121,"GW",False,"miso_2026_forecast","2026-04-20","")
o("forecast","summer_peak_gw","MISO","2035","CY",163,"GW",True,"miso_2026_forecast","2026-04-20","+35%, data centers the main driver.")
o("forecast","dc_online_gw","MISO","2026-2027","CY",11,"GW",True,"miso_2026_forecast","2026-04-20","8-14 GW of data centers expected online in 2026-27; midpoint.")
o("forecast","dc_load_growth_gw","CAISO","2030","CY",1.8,"GW",True,"rto_large_load_survey","2026-07","California Energy Commission forecast; 4.9 GW by 2040.")
o("grid","generation_queue_gw","PJM","2026-05","CY",212,"GW",False,"rto_large_load_survey","2026-05-15","New generation under review (Cycle 1, 829 applications), the supply response to load.")
o("grid","dc_supply_agreements_gw","TNB (Malaysia)","2026","CY",8.3,"GW",False,"tnb_dc_2026","2026-07-11","59 data centre projects with electricity supply agreements; 4.5 GW from 36 completed projects.")
o("grid","dc_connected_gw","TNB (Malaysia)","2026","CY",4.5,"GW",False,"tnb_dc_2026","2026-07-11","Max capacity of completed projects.")
o("power","dc_electricity_gwh","Ireland","2025","CY",7663,"GWh",False,"cso_ireland_2025","2026-07-07","23% of metered electricity; +10% YoY.")
o("power","dc_electricity_gwh","Ireland","2024","CY",6973,"GWh",False,"cso_ireland_2025","2026-07-07","Just over 21%.")
o("power","dc_electricity_share_pct","Ireland","2025","CY",23,"pct",False,"cso_ireland_2025","2026-07-07","Highest national share in the world; grid moratorium in Dublin.")

# ---------------------------------------------------------------- model assumptions
A = [
 # key, label, value, low, high, unit, description, source_ids
 ("ai_capex_usd_bn_2025","Global AI data center capex, 2025",550,480,650,"USD_bn",
  "All AI/cloud data center capex worldwide in 2025. Big 4 hyperscalers were $376bn; add Oracle (~$40bn CY), China big tech (~$60bn), neoclouds, labs, sovereign and enterprise (~$75bn).",
  ["capex_tracker","orcl_10q_fy27q1","tencent_2026q1","analyst_estimate"]),
 ("ai_capex_usd_bn_2026","Global AI data center capex, 2026",1000,900,1100,"USD_bn",
  "2026 is largely known from guidance: Big 4 ~$730bn (MSFT ~170, GOOGL 195-205, AMZN ~220, META 135-145) plus Oracle, China and others.",
  ["msft_call_fy27q1","googl_call_2026q3","amzn_pr_2026q3","meta_pr_2026q3","analyst_estimate"]),
 ("capex_growth_pct","Capex growth per year after 2026",15,0,30,"pct",
  "Annual growth in global AI capex from 2027. TSMC's mid-to-high-50s% AI accelerator CAGR (2024-29) implies ~25-35% late-decade growth; financing and power limits argue lower.",
  ["tsmc_2026q3","analyst_estimate"]),
 ("accel_share_of_capex_pct","Share of capex spent on accelerators",45,35,55,"pct",
  "Fraction of capex going to AI accelerators and attached networking. Calibrated: CY2025 NVIDIA DC revenue ~$194bn plus AMD/TPU/Trainium/others ~$55bn is ~45% of $550bn.",
  ["nvda_ir","amd_8k_2026q3","analyst_estimate"]),
 ("avg_accel_price_usd_k","Cost per H100-equivalent, 2025",21,17,26,"USD_k",
  "All-in spend per H100-equivalent of compute added in 2025 (chip + networking). Calibrated so 2025 spend matches Epoch AI's ~11-12M H100e added in 2025.",
  ["epoch_additions","analyst_estimate"]),
 ("price_decline_pct","Annual decline in cost per H100e",20,10,30,"pct",
  "Price-performance improvement per year for new accelerators (Blackwell to Rubin roadmap).",
  ["analyst_estimate"]),
 ("watts_per_accel","IT power per H100e, 2025 vintage",800,600,1000,"W",
  "Server-level IT power per H100-equivalent for chips installed in 2025 (DGX B200 ~14.3 kW for 8 GPUs at ~2.25x H100 FLOPs, plus ~10% cluster networking/storage). 2024 vintage ~1,350 W, older ~1,400 W.",
  ["nvidia_specs","analyst_estimate"]),
 ("perf_per_watt_gain_pct","Annual efficiency gain per vintage",25,15,35,"pct",
  "Yearly drop in watts per H100e for each new vintage.",["nvidia_specs","analyst_estimate"]),
 ("pue","Power usage effectiveness",1.25,1.1,1.4,"ratio",
  "Facility power divided by IT power for AI data centers (liquid-cooled new builds ~1.1-1.2; fleet average higher).",["lbnl_2024","iea_energy_ai"]),
 ("utilization_pct","Average power draw vs nameplate",65,50,80,"pct",
  "Average IT draw as a share of nameplate, used to turn capacity (GW) into energy (TWh).",["lbnl_2024","analyst_estimate"]),
 ("inference_share_pct","Inference share of compute, 2025",45,35,55,"pct",
  "Share of installed AI compute used for inference (vs training) in 2025.",["analyst_estimate"]),
 ("inference_share_gain_pp","Inference share gain per year",5,2,8,"pp",
  "Percentage-point increase in inference share each year, capped at 85%.",["analyst_estimate"]),
 ("accel_lifetime_years","Accelerator service life",5,4,6,"years",
  "Years before a vintage is retired from the installed base.",["analyst_estimate"]),
]
ASSUMPTIONS = [dict(key=k,label=l,value=v,low=lo,high=hi,unit=u,description=d,source_ids=s) for k,l,v,lo,hi,u,d,s in A]

# Pre-2025 additions (millions of H100e) from Epoch quarterly additions (0.8M in 2024Q1, ~2.5x/yr; ~6x/yr in 2023)
HIST_ADDS = {2020:0.1, 2021:0.15, 2022:0.25, 2023:1.3, 2024:4.7}
HIST_WATTS = {2020:1400, 2021:1400, 2022:1400, 2023:1400, 2024:1350}
YEARS = list(range(2024, 2031))
H100_FLOPS = 989e12  # dense BF16 FLOP/s

def run(p):
    adds, watts = dict(HIST_ADDS), dict(HIST_WATTS)
    out = {k: {} for k in ["capex","accel_spend","additions","stock","it_gw","facility_gw","energy_twh","inference_stock","training_stock","zettaflops"]}
    for y in range(2025, 2031):
        if y == 2025: capex = p["ai_capex_usd_bn_2025"]
        elif y == 2026: capex = p["ai_capex_usd_bn_2026"]
        else: capex = p["ai_capex_usd_bn_2026"] * (1 + p["capex_growth_pct"]/100) ** (y-2026)
        spend = capex * p["accel_share_of_capex_pct"]/100
        price = p["avg_accel_price_usd_k"] * (1 - p["price_decline_pct"]/100) ** (y-2025)
        adds[y] = spend / price  # USD bn / USD k = millions of units
        watts[y] = p["watts_per_accel"] * (1 - p["perf_per_watt_gain_pct"]/100) ** (y-2025)
        out["capex"][y] = capex; out["accel_spend"][y] = spend
    L = int(round(p["accel_lifetime_years"]))
    for y in YEARS:
        live = [v for v in adds if y-L < v <= y]
        stock = sum(adds[v] for v in live)
        it_gw = sum(adds[v]*watts[v] for v in live) / 1000  # M units * W = MW -> /1000 GW
        fac = it_gw * p["pue"]
        inf = min(85, p["inference_share_pct"] + p["inference_share_gain_pp"]*(y-2025)) / 100
        out["additions"][y] = adds[y]; out["stock"][y] = stock
        out["it_gw"][y] = it_gw; out["facility_gw"][y] = fac
        out["energy_twh"][y] = fac * p["utilization_pct"]/100 * 8.76
        out["inference_stock"][y] = stock*inf; out["training_stock"][y] = stock*(1-inf)
        out["zettaflops"][y] = stock*1e6*H100_FLOPS/1e21
    return out

base = {a["key"]: a["value"] for a in ASSUMPTIONS}
# Scenario sets: low = demand-dampening ends of each range, high = demand-boosting ends
low = dict(base, ai_capex_usd_bn_2026=900, capex_growth_pct=0, accel_share_of_capex_pct=40, price_decline_pct=15, perf_per_watt_gain_pct=30, utilization_pct=55)
high = dict(base, ai_capex_usd_bn_2026=1100, capex_growth_pct=30, accel_share_of_capex_pct=50, price_decline_pct=25, perf_per_watt_gain_pct=20, utilization_pct=75)
R = {s: run(p) for s, p in [("low",low),("base",base),("high",high)]}

SERIES = [
 ("capex","Global AI data center capex","USD_bn"),
 ("accel_spend","Spend on AI accelerators","USD_bn"),
 ("additions","AI compute added per year","H100e_m"),
 ("stock","Installed AI compute","H100e_m"),
 ("inference_stock","Installed AI compute used for inference","H100e_m"),
 ("training_stock","Installed AI compute used for training","H100e_m"),
 ("zettaflops","Installed AI compute (peak dense BF16)","zettaFLOP_s"),
 ("it_gw","AI IT power capacity","GW"),
 ("facility_gw","AI data center power capacity (incl. cooling)","GW"),
 ("energy_twh","AI data center electricity use","TWh"),
]
def pts(key):
    ys = [y for y in YEARS if y in R["base"][key]]
    return [dict(year=y, low=round(R["low"][key][y],2), base=round(R["base"][key][y],2), high=round(R["high"][key][y],2)) for y in ys]

model = dict(
    version="1.0", generated=ACCESSED, placeholder=False,
    description="Spend-driven model of global AI compute demand: capex -> accelerator spend -> H100-equivalents added -> installed base (with retirement) -> power and energy.",
    series=[dict(name=k, label=l, unit=u, points=pts(k)) for k,l,u in SERIES],
    assumptions=ASSUMPTIONS,
    scenarios=dict(low=low, base=base, high=high),
    history=dict(additions_h100e_m=HIST_ADDS, watts_per_h100e=HIST_WATTS),
    formula=[
        "capex[2025]=ai_capex_usd_bn_2025; capex[2026]=ai_capex_usd_bn_2026; capex[y>2026]=capex[2026]*(1+capex_growth_pct/100)^(y-2026)",
        "accel_spend[y]=capex[y]*accel_share_of_capex_pct/100",
        "price[y]=avg_accel_price_usd_k*(1-price_decline_pct/100)^(y-2025)  (USD k per H100e)",
        "additions[y] (millions H100e)=accel_spend[y]/price[y]; years<=2024 from history.additions_h100e_m",
        "watts[y]=watts_per_accel*(1-perf_per_watt_gain_pct/100)^(y-2025); years<=2024 from history.watts_per_h100e",
        "stock[y]=sum of additions[v] for v in (y-accel_lifetime_years, y]",
        "it_gw[y]=sum(additions[v]*watts[v])/1000 over live vintages; facility_gw=it_gw*pue",
        "energy_twh[y]=facility_gw*utilization_pct/100*8.76",
        "inference share[y]=min(85, inference_share_pct+inference_share_gain_pp*(y-2025))",
        "zettaflops=stock*1e6*989e12/1e21 (H100 dense BF16)",
    ],
    benchmarks=[
        dict(label="Epoch AI: installed AI compute, Jan 2026", value=15.0, unit="H100e_m", year=2025, series="stock", source_id="epoch_chip_owners"),
        dict(label="Epoch AI: power for installed AI chips, Jan 2026", value=10.0, unit="GW", year=2025, series="it_gw", source_id="epoch_chip_owners"),
        dict(label="IEA: all data centres, 2024", value=415, unit="TWh", year=2024, series="energy_twh", source_id="iea_energy_ai"),
        dict(label="IEA Base Case: all data centres, 2030", value=945, unit="TWh", year=2030, series="energy_twh", source_id="iea_energy_ai"),
    ],
)

# ---------------------------------------------------------------- write
cols = ["id","category","metric","entity","period","period_type","value","unit","is_estimate","source_id","source_name","source_url","source_date","notes"]
smap = {s[0]: s for s in SOURCES}
rows = []
for i, (cat, met, ent, per, pt, val, unit, est, sid, sdate, notes) in enumerate(OBS, 1):
    s = smap[sid]
    rows.append(dict(id=f"obs_{i:04d}", category=cat, metric=met, entity=ent, period=per, period_type=pt, value=val, unit=unit,
                     is_estimate=est, source_id=sid, source_name=s[1], source_url=s[3], source_date=sdate, notes=notes))
with open(os.path.join(HERE,"observations.csv"),"w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
    for r in rows: w.writerow({**r, "is_estimate": str(r["is_estimate"]).lower()})
json.dump(rows, open(os.path.join(HERE,"observations.json"),"w"), indent=1)
json.dump([dict(source_id=a, name=b, publisher=c, url=d, type=e, accessed=ACCESSED) for a,b,c,d,e in SOURCES],
          open(os.path.join(HERE,"sources.json"),"w"), indent=1)
json.dump(model, open(os.path.join(HERE,"model.json"),"w"), indent=1)

if __name__ == "__main__":
    print(f"{len(rows)} observations, {len(SOURCES)} sources")
    for k,l,u in SERIES:
        print(f"{k:16s}", " ".join(f"{y}:{R['base'][k][y]:.1f}" for y in YEARS if y in R['base'][k]))
    print("2030 energy low/base/high", [round(R[s]['energy_twh'][2030]) for s in ("low","base","high")])
