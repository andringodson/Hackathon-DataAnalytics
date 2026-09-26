# %% [markdown]
# # VoltRelay Energy — What is really driving service quality, retention and margin?
#
# **Gradient Learnings Data Analytics Hackathon** · Battery-swap network, 6 Indian cities, Jan 2024 – Jun 2025
#
# [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/andringodson/Hackathon-DataAnalytics/blob/main/notebooks/VoltRelay_Analysis.ipynb)
#
# This notebook runs top to bottom in Google Colab. The first code cell downloads the eight organiser CSVs (~830 MB) from Google Drive.
#
# | Section | Contents |
# |---|---|
# | 1 | Setup and data loading |
# | 2 | Data understanding |
# | 3 | Data cleaning — every documented quality issue tested, plus three undocumented ones |
# | 4 | Metric definitions and unit-economics model |
# | 5–10 | The six Core Questions |
# | 11 | Optional deep dives: budget decision, expansion waves, partner value, ticket text, anomalies |
# | 12 | Key findings and recommendations |
# | 13 | Export of aggregated tables for the dashboard |

# %% [markdown]
# ## 1. Setup and data loading

# %%
import os, sys, subprocess, warnings
from pathlib import Path

warnings.filterwarnings("ignore")
IN_COLAB = "google.colab" in sys.modules
try:
    import gdown  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gdown"], check=True)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
import statsmodels.formula.api as smf
from scipy import stats

pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")

DATA_DIR = Path(os.environ.get("VOLTRELAY_DATA", "data/raw"))
FIG_DIR = Path(os.environ.get("VOLTRELAY_FIGS", "figures"))
OUT_DIR = Path(os.environ.get("VOLTRELAY_OUT", "processed"))
FIG_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

TABLES = ["swap_events", "station_hourly_status", "riders", "batteries", "support_tickets", "stations", "city_daily_context", "fleet_partners"]
DRIVE_FOLDER = "https://drive.google.com/drive/folders/1qsjGWrgmEvOaf2Is2fh7RgVEkKd1V3df"


def find(name):
    hits = sorted(DATA_DIR.rglob(f"{name}.csv*"))
    return hits[0] if hits else None


if any(find(t) is None for t in TABLES):
    import gdown
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    gdown.download_folder(DRIVE_FOLDER, output=str(DATA_DIR), quiet=True, remaining_ok=True)
missing = [t for t in TABLES if find(t) is None]
assert not missing, f"Missing files: {missing}"
print({t: f"{find(t).stat().st_size / 1e6:,.1f} MB" for t in TABLES})

# %%
sns.set_theme(style="whitegrid", context="notebook")
PAL = {"primary": "#1f5f8b", "accent": "#e07a1f", "bad": "#c0392b", "good": "#2e8b57", "muted": "#8c8c8c"}
GEN_PAL = {"Gen1": "#c0392b", "Gen2": "#1f5f8b", "Gen3": "#2e8b57"}
plt.rcParams.update({"figure.dpi": 90, "savefig.dpi": 130, "axes.titleweight": "bold", "axes.titlesize": 12})


def save(fig, name):
    fig.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight")
    plt.show()


def pct(ax, axis="y", decimals=0):
    fmt = mtick.PercentFormatter(1.0, decimals=decimals)
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)

# %%
cat = "category"
se = pd.read_csv(find("swap_events"), parse_dates=["event_ts"], dtype={
    "rider_id": cat, "station_id": cat, "event_type": cat, "battery_in_id": cat, "battery_out_id": cat,
    "tariff_code": cat, "payment_mode": cat, "station_firmware": cat, "sync_mode": cat})
hs = pd.read_csv(find("station_hourly_status"), parse_dates=["hour_start"], dtype={"station_id": cat, "telemetry_status": cat})
rd = pd.read_csv(find("riders"), parse_dates=["signup_date"])
bt = pd.read_csv(find("batteries"), parse_dates=["manufacture_date", "commission_date", "retired_date"])
tk = pd.read_csv(find("support_tickets"), parse_dates=["created_ts"])
st = pd.read_csv(find("stations"), parse_dates=["commissioned_date", "decommissioned_date", "firmware_updated_date", "competitor_within_1_5km_since"])
cx = pd.read_csv(find("city_daily_context"), parse_dates=["date"])
fp = pd.read_csv(find("fleet_partners"), parse_dates=["contract_start_date", "amendment_date"])
raw = {"swap_events": se, "station_hourly_status": hs, "riders": rd, "batteries": bt, "support_tickets": tk,
       "stations": st, "city_daily_context": cx, "fleet_partners": fp}
pd.DataFrame({k: {"rows": len(v), "columns": v.shape[1]} for k, v in raw.items()}).T

# %% [markdown]
# ## 2. Data understanding
#
# The core fact table is `swap_events` — one row per swap *attempt*, completed or not. Everything else hangs off it:
#
# ```
# fleet_partners -> riders -> swap_events -> stations -> station_hourly_status
#                                  |   \-> batteries (battery_in_id, battery_out_id)
#                                  \-> support_tickets -> stations / batteries (optional)
# stations.city + date -> city_daily_context
# ```

# %%
se.head(3).T

# %%
print("Event outcomes:")
display(se.event_type.value_counts(normalize=True).rename("share").to_frame())
print("Tariff codes:", se.tariff_code.value_counts().to_dict())
print("Payment modes:", se.payment_mode.value_counts().to_dict())
print("Date range:", se.event_ts.min(), "->", se.event_ts.max())

# %% [markdown]
# **Referential integrity.** Every foreign key resolves:

# %%
checks = {
    "swap_events.rider_id in riders": se.rider_id.isin(rd.rider_id).mean(),
    "swap_events.station_id in stations": se.station_id.isin(st.station_id).mean(),
    "swap_events.battery_out_id in batteries": se.battery_out_id.dropna().isin(bt.battery_id).mean(),
    "support_tickets.rider_id in riders": tk.rider_id.isin(rd.rider_id).mean(),
    "riders.partner_id in fleet_partners": rd.partner_id.dropna().isin(fp.partner_id).mean(),
}
pd.Series(checks, name="share matched").to_frame()

# %% [markdown]
# **Which fields are populated for which outcome.** Pricing, energy and outgoing-battery fields exist only for completed swaps; non-completed attempts carry ₹0. Revenue and unit-economics analysis therefore uses completed swaps only, while service-quality analysis uses all attempts.

# %%
se.groupby("event_type", observed=True)[["battery_in_id", "battery_out_id", "km_since_last_swap", "energy_to_recharge_kwh", "amount_charged_inr"]].agg(
    lambda s: s.notna().mean() if s.name != "amount_charged_inr" else s.mean()).rename(columns={"amount_charged_inr": "mean ₹ charged"})

# %% [markdown]
# ## 3. Data cleaning
#
# Each documented data-quality issue is **detected with evidence, then handled deliberately**. The analysis also found three undocumented issues (3.8).

# %% [markdown]
# ### 3.1 Test stations — excluded, but they are not "small"
# The brief describes `STN-TST-*` as inactive test stations with a few zero-value transactions. In this export they are anything but.

# %%
tst_ids = st.loc[st.station_id.str.startswith("STN-TST"), "station_id"].tolist()
tst = se[se.station_id.isin(tst_ids)]
real_avg = se[~se.station_id.isin(tst_ids)].groupby("station_id", observed=True).size().mean()
display(tst.groupby("station_id", observed=True).agg(events=("event_id", "size"), revenue_inr=("amount_charged_inr", "sum"),
        zero_value_share=("amount_charged_inr", lambda s: (s == 0).mean()), first=("event_ts", "min"), last=("event_ts", "max")))
print(f"Average real station: {real_avg:,.0f} events")

# %% [markdown]
# **Decision:** exclude both test stations (62K events, ₹3.9M) from every network metric, as the brief instructs. **Flag:** the test stations handle more traffic than an average real station and book real revenue for all 18 months. Either they are live sites that were mislabelled, or revenue is being recorded on test infrastructure. Finance should reconcile this.

# %%
se = se[~se.station_id.isin(tst_ids)].copy()
hs = hs[~hs.station_id.isin(tst_ids)].copy()
tk = tk[~tk.station_id.isin(tst_ids)].copy()
st = st[~st.station_id.isin(tst_ids)].copy()
for df in (se, hs):
    df["station_id"] = df.station_id.cat.remove_unused_categories()
print("Stations remaining:", st.shape[0])

# %% [markdown]
# ### 3.2 Firmware timezone bug (v3.2.0, 10 Mar – 14 Apr 2025)
# The strongest proof: the **PEAK tariff only applies at 12–14h and 19–22h**, yet affected events show PEAK prices charged at 06–08h and 13–16h. That is exactly 5 h 30 m earlier than the true time (IST vs UTC).

# %%
bug = (se.station_firmware == "v3.2.0") & (se.event_ts >= "2025-03-10") & (se.event_ts < "2025-04-15")
fig, axes = plt.subplots(1, 2, figsize=(13, 3.6), sharey=True)
for ax, (label, mask) in zip(axes, [("v3.2.0 during bug window", bug), ("All other events", ~bug)]):
    se.loc[mask, "event_ts"].dt.hour.value_counts(normalize=True).sort_index().plot.bar(ax=ax, color=PAL["bad"] if "bug" in label else PAL["primary"])
    ax.set_title(label); ax.set_xlabel("logged hour of day"); pct(ax)
axes[0].set_ylabel("share of events")
save(fig, "03_firmware_bug_hours")
peak_hours_logged = se.loc[bug & (se.tariff_code == "PEAK"), "event_ts"].dt.hour.value_counts().sort_index()
print("PEAK-tariff events by *logged* hour in the bug window:", peak_hours_logged[peak_hours_logged > 0].to_dict())

# %%
se["ts_corrected"] = bug
se.loc[bug, "event_ts"] = se.loc[bug, "event_ts"] + pd.Timedelta(hours=5, minutes=30)
chk = se.loc[bug & (se.tariff_code == "PEAK"), "event_ts"].dt.hour.value_counts()
print(f"Corrected {bug.sum():,} timestamps. PEAK events now fall in hours: {sorted(chk[chk > 0].index.tolist())}")

# %% [markdown]
# ### 3.3 Offline-sync near-duplicates — tested, none present
# Definition from the brief: same rider, station and batteries, a few seconds to two minutes apart, concentrated in `offline_batch` rows at poor-connectivity stations.

# %%
s = se.sort_values(["rider_id", "station_id", "event_ts"])
p = s.shift()
gap = (s.event_ts - p.event_ts).dt.total_seconds()
same_rs = s.rider_id.astype(str).eq(p.rider_id.astype(str)) & s.station_id.astype(str).eq(p.station_id.astype(str))
same_batt = (s.battery_in_id.astype(str).eq(p.battery_in_id.astype(str)) & s.battery_out_id.astype(str).eq(p.battery_out_id.astype(str)))
exact_dups = same_rs & same_batt & (gap <= 120)
close = same_rs & (gap <= 120)
print(f"Exact near-duplicates (same rider+station+batteries, <=2 min): {exact_dups.sum()}")
print(f"Same rider+station within 2 min (any batteries): {close.sum():,}")
print(f"  offline_batch share among them: {(s.sync_mode[close] == 'offline_batch').mean():.1%}  vs network baseline {(se.sync_mode == 'offline_batch').mean():.1%}")
conn = se[["station_id", "sync_mode"]].merge(st[["station_id", "connectivity_tier"]], on="station_id")
print(pd.crosstab(conn.connectivity_tier, conn.sync_mode, normalize="index").round(3))
del s, p, gap

# %% [markdown]
# **Decision:** no rows removed. Close same-rider pairs always involve *different* battery packs, and `offline_batch` is no more common among them than in the network overall. They are genuine back-to-back attempts, not sync retries. The check stays in the pipeline so a future export with real duplicates would be caught. `offline_batch` itself does behave as documented: it only occurs at fair and poor-connectivity stations.

# %% [markdown]
# ### 3.4 Distance and charge-reading outliers

# %%
km = se.km_since_last_swap
print(km.describe(percentiles=[.001, .01, .99, .999]).round(1).to_dict())
km_bad = (km < 0) | (km > 250)
print(f"Negative (odometer reset): {(km < 0).sum():,} | >250 km (implausible for a 2.1/4.8 kWh pack): {(km > 250).sum():,}")
se["km_valid"] = km.where(~km_bad)
for c in ["soc_in_pct", "soh_in_pct", "soc_out_pct", "soh_out_pct"]:
    n = (se[c] > 100).sum()
    se[c] = se[c].clip(upper=100)
    print(f"{c}: {n:,} readings >100% clipped to 100 (sensor drift)")

# %% [markdown]
# ### 3.5 Inconsistent city spellings in `riders.home_city`

# %%
city_map = {"bengaluru": "Bengaluru", "bangalore": "Bengaluru", "blr": "Bengaluru",
            "delhi ncr": "Delhi NCR", "delhi": "Delhi NCR", "new delhi": "Delhi NCR", "gurgaon": "Delhi NCR",
            "hyderabad": "Hyderabad", "hyd": "Hyderabad", "pune": "Pune", "pun": "Pune",
            "mumbai": "Mumbai", "bombay": "Mumbai", "mum": "Mumbai", "jaipur": "Jaipur", "jai": "Jaipur"}
print("Raw variants:", rd.home_city.nunique())
rd["home_city"] = rd.home_city.str.strip().str.lower().map(city_map)
assert rd.home_city.notna().all()
rd.home_city.value_counts().to_frame().T

# %% [markdown]
# ### 3.6 Missing telemetry — kept as missing, never zero
# Blank telemetry fields line up exactly with `telemetry_status` ∈ {partial, missing}, concentrated at poor-connectivity stations. Hourly aggregates use only `ok` rows, so a blank is never read as "0 charged packs" (which would fake a stockout).

# %%
hs = hs.merge(st[["station_id", "connectivity_tier", "charger_generation", "city", "expansion_wave"]], on="station_id")
display(pd.crosstab(hs.connectivity_tier, hs.telemetry_status, normalize="index").round(3))
print("Null charged_2w_min where status == ok:", hs.loc[hs.telemetry_status == "ok", "charged_2w_min"].isna().sum())

# %% [markdown]
# ### 3.7 CSAT is missing not-at-random
# CSAT exists **only for resolved tickets**, and half as often when resolution takes more than 24 h. A naive average therefore describes the happiest subset only. We report CSAT with its coverage and never as a stand-alone satisfaction metric.

# %%
display(tk.groupby("resolution_status").csat_score.agg(coverage=lambda s: s.notna().mean(), mean="mean"))
display(tk.groupby(pd.cut(tk.resolution_hours, [0, 4, 12, 24, 48, 1000]), observed=True).csat_score.agg(coverage=lambda s: s.notna().mean(), mean="mean"))

# %% [markdown]
# ### 3.8 Three undocumented issues found during profiling
# 1. **`payment_mode` is always `partner_invoice`**, even for independent pay-as-you-go riders. It carries no information, so rider segments come from `riders.plan_type` and `partner_id`.
# 2. **Tariffs `PREPAID` and `PROMO_FREE` never occur.** Prepaid riders are billed on `STD`/`PEAK`/`OFFPEAK`.
# 3. **Battery IDs are not physically consistent across events.** The same pack is "issued" in different cities minutes apart (below). Batteries are therefore analysed as *cohorts* (supplier, lot, SoH at swap time), not by tracing individual packs through the event log.

# %%
b = se.dropna(subset=["battery_out_id"]).sort_values(["battery_out_id", "event_ts"])[["battery_out_id", "event_ts", "station_id", "rider_id"]]
bp = b.shift()
impossible = b.battery_out_id.astype(str).eq(bp.battery_out_id.astype(str)) & ((b.event_ts - bp.event_ts).dt.total_seconds() < 900) & b.station_id.astype(str).ne(bp.station_id.astype(str))
print(f"Same pack issued at two different stations <15 min apart: {impossible.sum():,} times")
display(pd.concat([bp[impossible].head(2), b[impossible].head(2)]).sort_values(["battery_out_id", "event_ts"]))
del b, bp

# %% [markdown]
# ### 3.9 Cleaning summary

# %%
pd.DataFrame([
    ["Test stations STN-TST-01/02", "62,031 events, ₹3.9M", "Excluded; flagged as anomaly"],
    ["Firmware v3.2.0 timezone bug", f"{bug.sum():,} events", "+5h30m correction"],
    ["Offline-sync near-duplicates", "0 found", "Check retained; nothing removed"],
    ["km_since_last_swap <0 or >250", f"{km_bad.sum():,} values", "Set to missing for range analysis"],
    ["SoC/SoH > 100%", "~13K readings", "Clipped to 100"],
    ["home_city spellings", "21 variants", "Mapped to 6 cities"],
    ["Missing telemetry", "46K hours", "Excluded from averages, never zero-filled"],
    ["CSAT MNAR", "66% missing", "Reported with coverage only"],
    ["Ticket categories", "'other' = vehicle complaints", "Re-classified with text rules (§11.4)"],
], columns=["Issue", "Scale", "Treatment"])
