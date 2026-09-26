from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

DATA = Path(__file__).resolve().parent.parent / "data" / "processed"
REPO = "https://github.com/andringodson/Hackathon-DataAnalytics26"
COLAB = "https://colab.research.google.com/github/andringodson/Hackathon-DataAnalytics26/blob/main/notebooks/VoltRelay_Analysis.ipynb"

st.set_page_config(page_title="VoltRelay Network Analysis", page_icon=":material/battery_charging_full:", layout="wide")

try:
    DARK_MODE = st.context.theme.type == "dark"
except Exception:
    DARK_MODE = False

# Validated categorical slots (first three pass all-pairs CVD checks in both modes)
C = {"s1": "#3987e5", "s2": "#d95926", "s3": "#199e70", "muted": "#898781", "grid": "#2c2c2a"} if DARK_MODE else \
    {"s1": "#2a78d6", "s2": "#eb6834", "s3": "#1baf7a", "muted": "#898781", "grid": "#e1e0d9"}
GEN = {"Gen1": C["s2"], "Gen2": C["s1"], "Gen3": C["s3"]}
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


@st.cache_data
def load(name, dates=()):
    return pd.read_csv(DATA / f"{name}.csv", parse_dates=list(dates))


AXIS_NAMES = {"month": None, "week": None, "quarter": None, "first_month": None, "inr": "₹ per swap", "index": "index (Jan 2024 = 100)",
              "failure_rate": "failure rate", "share": "share of attempts", "peak_share": "share of swaps in peak hours", "hour": "hour of day",
              "temp_band": "ambient temperature", "charge_minutes": "minutes", "stockout_hours": "share of hours", "retention": "retention"}


def style(fig, height=360, pct_y=False, legend=True):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=85, b=10), hovermode="x unified" if legend else "closest",
                      title=dict(y=0.98, yanchor="top", x=0, xanchor="left"), showlegend=legend,
                      legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0, title=None), font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif"))
    fig.update_xaxes(showgrid=False, linecolor=C["grid"])
    fig.update_yaxes(gridcolor=C["grid"], zeroline=False)
    fig.for_each_xaxis(lambda a: a.update(title_text=AXIS_NAMES.get(a.title.text, a.title.text)) if a.title.text in AXIS_NAMES else None)
    fig.for_each_yaxis(lambda a: a.update(title_text=AXIS_NAMES.get(a.title.text, a.title.text)) if a.title.text in AXIS_NAMES else None)
    if pct_y:
        fig.update_yaxes(tickformat=".0%")
    return fig


def show(fig, table, key):
    st.plotly_chart(fig, width="stretch", theme="streamlit", key=key)
    with st.expander("Table view"):
        st.dataframe(table, width="stretch", hide_index=True)


monthly = load("monthly_network", ["month"])
q1, q6 = monthly.iloc[:3].mean(numeric_only=True), monthly.iloc[-3:].mean(numeric_only=True)

st.title("VoltRelay Energy: what's driving failures, churn and margin")
st.caption(f"Battery-swap network · 6 cities · Jan 2024 – Jun 2025 · 3.9M swap attempts · "
           f"[Report]({REPO}/blob/main/report/analysis_report.md) · [Notebook]({COLAB}) · [Code]({REPO})")

k = st.columns(4)
k[0].metric("Completed swaps / month", f"{q6.completed / 1e3:,.0f}K", f"{q6.completed / q1.completed:.1f}× vs Q1 2024")
k[1].metric("Revenue / month", f"₹{q6.revenue / 1e6:,.1f}M", f"{q6.revenue / q1.revenue:.1f}× vs Q1 2024")
k[2].metric("Service failures / month", f"{q6.failures / 1e3:,.1f}K", f"{q6.failures / q1.failures:.1f}× vs Q1 2024", delta_color="inverse")
def inr(v, sign=False):
    s = "−" if v < 0 else ("+" if sign else "")
    return f"{s}₹{abs(v):,.1f}"


k[3].metric("Contribution / swap after wear", inr(q6.per_swap_cm2), f"{inr(q6.per_swap_cm2 - q1.per_swap_cm2, sign=True)} vs Q1 2024")
st.caption("Monthly averages, Q2 2025 vs Q1 2024.")

tabs = st.tabs(["Overview", "Service failures", "Stations & heat", "Batteries", "Pricing & partners", "New-rider retention", "Anomalies"])

# ---------------------------------------------------------------- Overview
with tabs[0]:
    st.markdown("""
**The short version.** Growth masked two operational problems:
1. **Gen1 cabinets fail in the heat.** Above 40 °C they take twice as long to charge and are empty in 58% of hours. They are concentrated in Delhi NCR, Jaipur and Hyderabad, so failures triple every summer there.
2. **Three bad Kyron battery lots** (KY-2407/08/09) degrade ~3× faster. They wiped out the July 2024 price rise in wear cost and cut delivered range.

**New riders churn when the network fails them early**, through empty cabinets or short-range packs. Competitors are not the driver.
""")
    c1, c2 = st.columns(2)
    idx = monthly.set_index("month")[["completed", "revenue", "failures"]]
    idx = (idx / idx.iloc[0] * 100).reset_index().melt("month", var_name="series", value_name="index")
    fig = px.line(idx, x="month", y="index", color="series", color_discrete_map={"completed": C["s1"], "revenue": C["s3"], "failures": C["s2"]},
                  title="Growth index (Jan 2024 = 100)")
    fig.update_traces(line_width=2)
    with c1:
        show(style(fig), monthly[["month", "completed", "revenue", "failures"]], "ov_idx")
    fig = px.line(monthly, x="month", y="failure_rate", title="Service-failure rate by month", markers=True, color_discrete_sequence=[C["s1"]])
    fig.update_traces(line_width=2, marker_size=8)
    with c2:
        show(style(fig, pct_y=True, legend=False), monthly[["month", "attempts", "failures", "failure_rate"]], "ov_fail")

    c1, c2 = st.columns(2)
    cm = monthly.melt("month", ["per_swap_cm1", "per_swap_cm2"], var_name="measure", value_name="inr")
    cm["measure"] = cm.measure.map({"per_swap_cm1": "CM1: before battery wear", "per_swap_cm2": "CM2: after battery wear"})
    fig = px.line(cm, x="month", y="inr", color="measure", markers=True, color_discrete_sequence=[C["s1"], C["s2"]], title="Contribution per completed swap (₹)")
    fig.add_hline(y=0, line_color=C["muted"], line_width=1)
    for d, lbl in [("2024-07-01", "price rise"), ("2024-08-01", "Kyron lots"), ("2024-11-01", "ZipDrop 28%")]:
        fig.add_vline(x=pd.Timestamp(d).timestamp() * 1000, line_color=C["muted"], line_width=1, annotation_text=lbl, annotation_font_size=10)
    fig.update_traces(line_width=2, marker_size=8)
    with c1:
        show(style(fig), monthly[["month", "per_swap_cm1", "per_swap_cm2"]].round(2), "ov_cm")
    cost = monthly.melt("month", ["per_swap_energy_cost_inr", "per_swap_fixed_per_swap", "per_swap_wear_inr"], var_name="cost", value_name="inr")
    cost["cost"] = cost.cost.map({"per_swap_energy_cost_inr": "Energy", "per_swap_fixed_per_swap": "Station fixed", "per_swap_wear_inr": "Battery wear"})
    fig = px.bar(cost, x="month", y="inr", color="cost", color_discrete_sequence=[C["s1"], C["s3"], C["s2"]], title="Cost per swap vs revenue per swap (₹)")
    fig.add_scatter(x=monthly.month, y=monthly.per_swap_amount_charged_inr, name="Revenue per swap", mode="lines+markers", line=dict(color=C["muted"], width=2))
    fig.update_layout(bargap=0.25)
    with c2:
        show(style(fig), monthly[["month", "per_swap_amount_charged_inr", "per_swap_energy_cost_inr", "per_swap_fixed_per_swap", "per_swap_wear_inr"]].round(2), "ov_cost")

# ---------------------------------------------------------------- Service failures
with tabs[1]:
    mc = load("monthly_city", ["month"])
    cities = st.multiselect("Cities", sorted(mc.city.unique()), default=sorted(mc.city.unique()), key="city_filter")
    sel = mc[mc.city.isin(cities)]
    heat = sel.pivot(index="city", columns="month", values="failure_rate")
    fig = px.imshow(heat, color_continuous_scale=BLUES, aspect="auto", title="Failure rate by city and month",
                    labels=dict(color="failure rate", x="", y=""))
    fig.update_coloraxes(colorbar_tickformat=".0%")
    fig.update_xaxes(tickformat="%b %y")
    show(style(fig, 330, legend=False), sel[["month", "city", "attempts", "failure_rate"]].round(4), "sf_heat")

    c1, c2 = st.columns(2)
    hf = load("hourly_failure")
    fig = px.line(hf, x="hour", y="failure_rate", color="vehicle_class", markers=True, color_discrete_map={"2W": C["s1"], "3W": C["s2"]},
                  title="Failure rate by hour of day (timestamps corrected)")
    fig.update_traces(line_width=2, marker_size=8)
    with c1:
        show(style(fig, pct_y=True), hf.round(4), "sf_hour")
    mix = load("event_mix_monthly", ["month"])
    mm = mix.melt("month", [c for c in mix.columns if c not in ("month", "swap_completed")], var_name="outcome", value_name="share")
    fig = px.bar(mm, x="month", y="share", color="outcome", title="Non-completed attempts by type (share of all attempts)",
                 color_discrete_sequence=[C["s1"], C["muted"], C["s2"], C["s3"]])
    fig.update_layout(bargap=0.25)
    with c2:
        show(style(fig, pct_y=True), mix.round(4), "sf_mix")

    stn = load("stations")
    stn = stn[stn.city.isin(cities)]
    fig = px.scatter_map(stn, lat="latitude", lon="longitude", color="charger_generation", size="failure_rate_all", size_max=16, zoom=3.6,
                         color_discrete_map=GEN, hover_name="station_id",
                         hover_data={"city": True, "location_type": True, "expansion_wave": True, "failure_rate_all": ":.1%", "swaps_per_day": ":.0f",
                                     "latitude": False, "longitude": False}, map_style="carto-darkmatter" if DARK_MODE else "carto-positron",
                         title="Stations: colour = charger generation, size = failure rate")
    show(style(fig, 520).update_layout(hovermode="closest"), stn[["station_id", "city", "zone", "charger_generation", "location_type", "expansion_wave", "swaps_per_day", "failure_rate_all"]]
         .sort_values("failure_rate_all", ascending=False).round(3), "sf_map")

# ---------------------------------------------------------------- Stations & heat
with tabs[2]:
    gh = load("gen_heat")
    order = ["<25°C", "25–30", "30–35", "35–40", ">40°C"]
    c1, c2 = st.columns(2)
    fig = px.bar(gh, x="temp_band", y="charge_minutes", color="charger_generation", barmode="group", color_discrete_map=GEN,
                 category_orders={"temp_band": order}, title="Average charge time (minutes) by ambient temperature")
    fig.update_layout(bargap=0.25, bargroupgap=0.08)
    with c1:
        show(style(fig), gh.round(3), "sh_charge")
    fig = px.bar(gh, x="temp_band", y="stockout_hours", color="charger_generation", barmode="group", color_discrete_map=GEN,
                 category_orders={"temp_band": order}, title="Share of hours with zero charged 2W packs")
    fig.update_layout(bargap=0.25, bargroupgap=0.08)
    with c2:
        show(style(fig, pct_y=True), gh.round(3), "sh_stock")
    st.info("Gen1 cabinets double their charge time above 40 °C and are empty in 58% of those hours. Gen2 and Gen3 are unaffected. "
            "A station-day regression controlling for city, site type, host and connectivity puts the Gen1 × hot-day effect at +9 pp of failure.")
    stn_all = load("stations")
    w = stn_all.groupby("expansion_wave").agg(stations=("station_id", "size"), swaps_per_day=("swaps_per_day", "mean"), failure_rate_2025=("fail_2025", "mean")).round(3)
    w["main location types"] = stn_all.groupby("expansion_wave").location_type.agg(lambda s: ", ".join(s.value_counts().head(2).index))
    st.subheader("Expansion waves (Mar–Jun 2025)")
    st.dataframe(w, width="stretch")
    st.caption("Wave 1 went mostly to highway fuel pumps and residential sites with below-average demand. The Gen1 launch hubs behind the failures were not upgraded.")

# ---------------------------------------------------------------- Batteries
with tabs[3]:
    lots = load("battery_lots", ["commissioned"]).sort_values("commissioned")
    lots["group"] = lots.manufacturing_lot.isin(["KY-2407", "KY-2408", "KY-2409"]).map({True: "Kyron KY-2407/08/09", False: "all other lots"})
    fig = px.bar(lots, x="manufacturing_lot", y="loss", color="group", color_discrete_map={"Kyron KY-2407/08/09": C["s2"], "all other lots": C["muted"]},
                 hover_data=["supplier", "packs", "commissioned"], title="SoH points lost per 100 swaps, by manufacturing lot (in commissioning order)")
    fig.update_layout(bargap=0.2, xaxis_title=None, yaxis_title="SoH pts / 100 swaps")
    show(style(fig, 380, legend=True), lots.round(3), "bt_lots")

    c1, c2 = st.columns(2)
    rv = load("range_vs_soh")
    pack = c1.radio("Pack type", ["2W_2.1kWh", "3W_4.8kWh"], horizontal=True)
    rsel = rv[rv.pack_type == pack]
    fig = px.line(rsel, x="soh_band", y="mean", color="cohort", markers=True, title=f"{pack}: km delivered per swap vs SoH",
                  color_discrete_map={"Cellora": C["s1"], "Amptek": C["s3"], "Kyron": C["muted"], "Kyron KY-2407..09": C["s2"]},
                  category_orders={"soh_band": ["<70", "70–75", "75–80", "80–85", "85–90", "90–95", "95–100"]})
    fig.update_traces(line_width=2, marker_size=8)
    fig.update_layout(yaxis_title="km per swap", xaxis_title="SoH of returned pack")
    with c1:
        show(style(fig), rsel.round(2), "bt_range")
    fm = load("fleet_monthly", ["month"])
    fi = fm.assign(**{"km per swap": fm.km / fm.km.iloc[0] * 100, "mean SoH": fm.soh / fm.soh.iloc[0] * 100}).melt("month", ["km per swap", "mean SoH"],
                                                                                                                     var_name="series", value_name="index")
    fig = px.line(fi, x="month", y="index", color="series", color_discrete_sequence=[C["s1"], C["s2"]], title="Fleet ageing: range fell faster than SoH (Jan 2024 = 100)")
    fig.update_traces(line_width=2)
    with c2:
        c2.write("")
        c2.write("")
        show(style(fig), fm.round(3), "bt_fleet")
    st.subheader("Battery cohorts")
    st.dataframe(load("battery_cohorts").round(2), width="stretch", hide_index=True)

# ---------------------------------------------------------------- Pricing & partners
with tabs[4]:
    c1, c2 = st.columns(2)
    pw = load("pilot_weekly", ["week"])
    pwm = pw.melt("week", var_name="group", value_name="peak_share")
    fig = px.line(pwm, x="week", y="peak_share", color="group", color_discrete_sequence=[C["muted"], C["s2"]],
                  title="Independent riders: share of swaps in peak hours")
    fig.add_vline(x=pd.Timestamp("2024-10-01").timestamp() * 1000, line_color=C["muted"], annotation_text="pilot starts", annotation_font_size=10)
    fig.update_traces(line_width=2)
    with c1:
        show(style(fig, pct_y=True), pw.round(4), "pp_weekly")
    did = load("pilot_did")
    shift = did[did.outcome.str.startswith("peak")]
    fig = go.Figure(go.Scatter(x=shift["DiD estimate"], y=shift.segment, mode="markers", marker=dict(size=11, color=C["s1"]),
                               error_x=dict(type="data", symmetric=False, array=shift["CI high"] - shift["DiD estimate"],
                                            arrayminus=shift["DiD estimate"] - shift["CI low"], color=C["muted"])))
    fig.add_vline(x=0, line_color=C["muted"], line_width=1)
    fig.update_layout(title="Pilot effect on peak-hour share (pp, 95% CI)", xaxis_title="difference-in-differences, pp")
    with c2:
        show(style(fig, legend=False), did.round(3), "pp_did")
    st.info("Riders who pay the surcharge shifted 2.5–3.5 pp of swaps out of peak hours, and revenue per exposed swap rose ₹6–8. "
            "Surcharge-exempt partners did not respond. Peak-hour reliability did not change: the pilot ran in the two least-congested cities.")

    pe = load("partners")
    p2 = pe[pe.pid != "Independent"].copy()
    p2["highlight"] = p2.partner_name.eq("ZipDrop").map({True: "ZipDrop", False: "other partners"})
    fig = px.scatter(p2, x="revenue_m", y="cm1", size="swaps", color="highlight", text="partner_name", size_max=40,
                     color_discrete_map={"ZipDrop": C["s2"], "other partners": C["s1"]},
                     hover_data={"discount_per_swap": ":.1f", "cm2": ":.1f", "payment_terms_days": True, "peak_surcharge_billable": True, "highlight": False},
                     title="Fleet partners: total revenue vs contribution per swap before wear (bubble = swaps)")
    fig.update_traces(textposition="top center", textfont_size=10, marker=dict(line=dict(width=2, color="rgba(0,0,0,0)")))
    fig.update_layout(xaxis_title="revenue (₹ million)", yaxis_title="CM1 per swap (₹)")
    show(style(fig, 440, legend=False), pe.round(2), "pp_partners")
    st.caption("ZipDrop is the largest partner by volume but the least profitable 2W partner: 28% discount since Nov 2024, "
               "exempt from the peak surcharge, 45-day payment terms. FeastFly generates more total contribution on fewer swaps.")

# ---------------------------------------------------------------- Retention
with tabs[5]:
    coh = load("cohort_retention", ["first_month"])
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[.6, .4], vertical_spacing=.08,
                        subplot_titles=("30–59 day retention of new riders", "Failure rate in their first 14 days"))
    fig.add_scatter(x=coh.first_month, y=coh.retention, mode="lines+markers", line=dict(color=C["s1"], width=2), marker_size=8, name="retention", row=1, col=1)
    fig.add_bar(x=coh.first_month, y=coh.early_fail, marker_color=C["s2"], name="early failure rate", row=2, col=1)
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(title="New-rider cohorts by month of first swap", showlegend=False)
    show(style(fig, 480, legend=False), coh.round(3), "rt_cohort")

    c1, c2 = st.columns(2)
    lifts = load("retention_lifts")
    factor = c1.selectbox("Break retention down by", lifts.factor.unique())
    ls = lifts[lifts.factor == factor]
    fig = px.bar(ls, x="level", y="retention", text=ls.riders.map(lambda n: f"n={n:,}"), color_discrete_sequence=[C["s1"]], title=f"Retention by: {factor}")
    fig.update_traces(textposition="outside", textfont_size=10)
    fig.update_yaxes(range=[.6, .95])
    fig.update_layout(bargap=0.3, xaxis_title=None)
    with c1:
        show(style(fig, pct_y=True, legend=False), ls, "rt_lift")
    lg = load("retention_logit")
    lg = lg[~lg.term.str.contains("attempts_14d")].sort_values("coef")
    lg["label"] = lg.term.str.replace(r"C\(|\)|Treatment\('.*?'\)|, ", "", regex=True).str.replace("_z", " (per SD)")
    lg["significant"] = lg.p.lt(.05).map({True: "p < 0.05", False: "not significant"})
    fig = px.scatter(lg, x="coef", y="label", color="significant", error_x=lg.hi - lg.coef, error_x_minus=lg.coef - lg.lo,
                     color_discrete_map={"p < 0.05": C["s2"], "not significant": C["muted"]}, title="Logistic regression: effect on log-odds of retention")
    fig.update_traces(marker_size=9)
    fig.add_vline(x=0, line_color=C["muted"], line_width=1)
    fig.update_layout(yaxis_title=None, xaxis_title="coefficient (95% CI)")
    fig.update_yaxes(categoryorder="array", categoryarray=lg.label.tolist())
    with c2:
        show(style(fig, 560).update_layout(hovermode="closest"), lg[["term", "coef", "lo", "hi", "p", "odds_ratio"]].round(3), "rt_logit")
    st.markdown("""
| Tier | Driver |
|---|---|
| **Primary** | Early service failure (first 14 days); delivered range per swap |
| Secondary | 3W vehicle; hot, Gen1-heavy home city; partner-billed plan |
| Minor | Peak-tariff exposure |
| Not drivers | Competitor nearby, competitor promotions, signup channel, KYC |
""")

# ---------------------------------------------------------------- Anomalies
with tabs[6]:
    st.dataframe(load("anomalies"), width="stretch", hide_index=True)
    tq = load("ticket_themes_quarterly")
    tq = tq[~tq.quarter.str.startswith("2025Q3")]
    tm = tq.melt("quarter", var_name="theme", value_name="tickets")
    tm["theme"] = tm.theme.where(tm.theme.isin(["range / battery", "vehicle 'performance' (vague)", "stockout"]), "other themes")
    tm = tm.groupby(["quarter", "theme"], as_index=False).tickets.sum()
    fig = px.line(tm, x="quarter", y="tickets", color="theme", markers=True,
                  color_discrete_map={"range / battery": C["s2"], "vehicle 'performance' (vague)": C["s1"], "stockout": C["s3"], "other themes": C["muted"]},
                  title="Support tickets by theme from the rider's own words")
    fig.update_traces(line_width=2, marker_size=8)
    show(style(fig), tq, "an_tickets")
    st.caption("Every ticket filed as 'other' is a vague vehicle complaint ('scooter weak lag raha hai'). These tickets reference the bad Kyron packs "
               "as often as explicit range complaints do, so riders were describing a battery problem as a vehicle problem.")
