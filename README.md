# VoltRelay Energy — Battery-Swap Network Analysis

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/andringodson/Hackathon-DataAnalytics26/blob/main/notebooks/VoltRelay_Analysis.ipynb)
[![Dashboard](https://img.shields.io/badge/dashboard-live-2a78d6)](https://andringodson.github.io/Hackathon-DataAnalytics26/)

Submission for the **Gradient Learnings Data Analytics Hackathon**: an investigation of what drives service failures, new-rider churn and eroding margins on VoltRelay's battery-swapping network for electric 2W/3W riders (6 Indian cities, Jan 2024 – Jun 2025, 3.9M swap attempts).

## Deliverables

| Deliverable | Link |
|---|---|
| **Colab notebook**: data understanding, cleaning, EDA, analysis of all six core questions and five deep dives; runs top to bottom | [`notebooks/VoltRelay_Analysis.ipynb`](notebooks/VoltRelay_Analysis.ipynb) · [open in Colab](https://colab.research.google.com/github/andringodson/Hackathon-DataAnalytics26/blob/main/notebooks/VoltRelay_Analysis.ipynb) |
| **Analysis report**: problem, approach, insights, visuals, findings, recommendations | [`report/analysis_report.md`](report/analysis_report.md) · [PDF](report/analysis_report.pdf) |
| **Three-minute video**: script and suggested visuals | [`report/video_script.md`](report/video_script.md) |
| **Interactive dashboard** (bonus) | [andringodson.github.io/Hackathon-DataAnalytics26](https://andringodson.github.io/Hackathon-DataAnalytics26/) (interactive web app on GitHub Pages: OLED-black royal design with editorial serif typography and a cursor-reactive background, story-led sections with smooth transitions, filters that morph charts in place, 3D station map, table view and CSV export for every chart; accessible (zero axe violations), installable and cached for instant repeat visits) |

## Key findings

1. **Growth masked a quality problem.** Completed swaps grew 2.8× and revenue 3.0×, but service failures grew 5.7×, and contribution per swap after battery wear did not improve.
2. **Failures are Gen1 cabinets in the heat.** Above 40 °C, Gen1 charge time doubles (88 → 174 min) and cabinets are empty in 58% of hours. Gen2/3 are unaffected. Delhi NCR, Jaipur and Hyderabad hold 36 of the 51 Gen1 cabinets, so failures triple there every summer.
3. **Three bad battery lots eroded margin.** Kyron lots KY-2407/08/09 degrade ~3× faster than every other lot. They wiped out the July 2024 price rise in wear cost (~₹45M in excess wear) and cut delivered range.
4. **New riders churn when the network fails them early.** Early stockouts and short range are the primary drivers. City, 3W and plan type are secondary. Competitors are not a driver.
5. **The fixes missed the target.** Expansion went to easy sites rather than failing ones, the pricing pilot ran where there was no congestion, and the largest partner (ZipDrop) is the least profitable 2W partner after its 28% discount.

**Top recommendations:** upgrade or cool the 36 hot-city Gen1 cabinets before summer 2026 · replace the bad Kyron lots and claim warranty · renegotiate ZipDrop rather than signing an exclusive · protect new riders' first 14 days · use peak pricing only where congestion is real.

## Repository layout

```
notebooks/
  VoltRelay_Analysis.ipynb   executed Colab notebook (the main deliverable)
  src/*.py                   notebook source in percent-format cells (readable diffs)
  build_notebook.py          assembles src/*.py into the .ipynb
report/
  analysis_report.md / .pdf  written report
  video_script.md            three-minute presentation script
  figures/                   all charts, exported by the notebook
dashboard/app.py             Streamlit dashboard
site/                        hosted dashboard (HTML/CSS/JS, ECharts, MapLibre GL with free OpenFreeMap vector tiles, no API keys); build.py packs data/processed into data.json
.github/workflows/pages.yml  deploys the dashboard to GitHub Pages on every push
data/
  download_data.py           fetches the eight raw CSVs (~830 MB) from the organiser's Drive
  processed/                 small aggregated tables exported by the notebook (dashboard input)
```

The raw data is never committed: `swap_events.csv` alone is 729 MB, above GitHub's 100 MB file limit.

## Reproducing

**In Colab:** click the badge above and choose *Runtime → Run all*. The first cell downloads the data (~2 min) and a full run takes about 10 minutes.

**Locally:**

```bash
pip install -r requirements.txt gdown seaborn statsmodels scikit-learn scipy matplotlib nbformat nbconvert ipykernel
python data/download_data.py                        # -> data/raw/
cd notebooks && VOLTRELAY_DATA=../data/raw VOLTRELAY_FIGS=../report/figures VOLTRELAY_OUT=../data/processed \
  jupyter nbconvert --to notebook --execute VoltRelay_Analysis.ipynb --inplace
streamlit run dashboard/app.py                     # Python version of the dashboard
python site/build.py && python -m http.server -d _site   # the hosted web dashboard, at localhost:8000
```

## Data-quality handling at a glance

Every documented issue was tested before it was handled, and three undocumented ones were found:

- **Firmware v3.2.0 clock bug:** 139,490 events shifted +5 h 30 m. Proven by PEAK tariffs appearing at off-tariff hours.
- **Test stations:** excluded. They carry 62K events and ₹3.9M revenue, not "a few zero-value rows", so this is flagged.
- **Offline-sync duplicates:** tested, none present in this export.
- **City spellings:** 21 variants of 6 cities standardised. **Outliers:** odometer and sensor readings nulled or clipped.
- **Telemetry gaps:** never zero-filled. **CSAT:** missing not at random, so it is not used as a KPI.
- **Undocumented:** `payment_mode` is constant; PREPAID/PROMO tariffs never occur; battery IDs are physically inconsistent (analysed as cohorts); packs marked retired are still being issued.
