# %% [markdown]
# ## 11. Optional deep dives
#
# ### 11.1 Sizing the problems (inputs to the budget decision)

# %%
# Excess failures at Gen1: failures above what Gen2/3 stations in the same city and month experienced
rate23 = se[se.charger_generation != "Gen1"].groupby(["city", "month"]).service_failure.mean().rename("rate_gen23")
g1 = se[se.charger_generation == "Gen1"].groupby(["city", "month"]).agg(attempts=("event_id", "size"), failures=("service_failure", "sum")).join(rate23)
g1["excess"] = (g1.failures - g1.attempts * g1.rate_gen23).clip(lower=0)
excess_gen1 = g1.excess.sum()
print(f"Excess Gen1 failures over 18 months: {excess_gen1:,.0f} ({excess_gen1 / se.service_failure.sum():.0%} of all service failures)")
print("  by city:", g1.groupby("city").excess.sum().sort_values(ascending=False).round(-2).to_dict())
print(f"  Gen1 cabinets: {len(st[st.charger_generation == 'Gen1'])}, of which in Delhi/Jaipur/Hyderabad: {st[(st.charger_generation == 'Gen1') & st.city.isin(['Delhi NCR', 'Jaipur', 'Hyderabad'])].shape[0]}")

# Excess battery wear from the three bad Kyron lots vs the wear rate of healthy packs of the same type
bl = comp.assign(bad=comp.battery_out_id.astype(str).isin(bad_lot_ids), pack=np.where(comp.vehicle_class == "3W", "3W", "2W"))
normal_wear = bl[~bl.bad].groupby("pack").wear_inr.mean()
bad = bl[bl.bad]
excess_wear = (bad.wear_inr - bad.pack.map(normal_wear)).sum()
print(f"\nBad-lot swaps: {len(bad):,} | excess wear cost: ₹{excess_wear / 1e6:,.1f}M "
      f"(≈ ₹{excess_wear / len(comp):.1f} on every completed swap in the network)")

# ZipDrop amendment: revenue given up since Nov 2024
zd = comp[(comp.pid == "FP-03") & (comp.date >= "2024-11-01")]
lost = (zd.discount_inr - zd.list_price_inr * 0.12).sum()
print(f"\nZipDrop discount above its original 12% since Nov 2024: ₹{lost / 1e6:,.1f}M in 8 months (~₹{lost / 8 * 12 / 1e6:,.1f}M a year)")

# %% [markdown]
# ### 11.2 The budget decision
#
# | Proposal | What the evidence says | Verdict |
# |---|---|---|
# | **More stations** | Wave 1 (2024 H2) went mostly to highway fuel pumps and residential sites that run at ~55 swaps/day vs ~77 at launch commercial hubs (§11.3). Failure is not a network-wide capacity shortfall. Gen1 cabinets alone account for ~35K excess failures (17% of all failures) over what Gen2/3 stations in the same city and month experienced, and 94% of that excess is in Delhi NCR, Hyderabad and Jaipur, which hold 36 of the 51 Gen1 cabinets. | **Not as proposed.** Re-direct capex to *upgrading* Gen1 cabinets in Delhi NCR, Jaipur and Hyderabad to Gen3 (or retrofitting cooling) before summer 2026. Add new sites only in the zones where those cabinets saturate. |
# | **More batteries** | The Gen1 stockout is a *charging-throughput* problem (charge time doubles in the heat), so extra packs sitting in a hot Gen1 cabinet do not charge any faster. However, 1,461 bad-lot packs (~22% of swaps) need replacing. They cost ~₹45M in excess wear (≈ ₹12 on every swap in the network), and degraded packs drive riders to swap ~20% more often. | **Replace, don't expand.** Fund replacement of the bad Kyron lots (pursue a warranty claim) and retire packs below ~75% SoH faster. A net-new fleet is not needed. |
# | **Network-wide pricing rollout** | The pilot is revenue-positive (+₹6–8 per exposed swap) and shifts ~3 pp of demand, but it produced **no reliability gain**, and peak-price exposure is weakly negative for new-rider retention. | **Targeted, not network-wide.** Use peak pricing where congestion is real (hot-city hubs in summer), give new riders a 30-day grace period, and close the surcharge exemptions first. |
# | **Long-term exclusive with the largest partner (ZipDrop)** | Largest by volume, lowest 2W margin: 28% discount since Nov 2024, exempt from the peak surcharge, 45-day payment terms. The amendment costs roughly ₹5.5M a year. | **Do not lock in.** Renegotiate towards volume-tiered discounts with a floor, surcharge billing and 30-day terms. Grow the better-margin partners (FeastFly, QuickCart, RideMitra, DabbaXpress) instead. |

# %% [markdown]
# ### 11.3 Did the expansion waves go where riders needed them?

# %%
h1 = comp[comp.date >= "2025-03-01"]
util = (h1.groupby("station_id", observed=True).size() / h1.groupby("station_id", observed=True).date.nunique()).rename("swaps_per_day")
sx = st.set_index("station_id").join(util).join(se[se.date >= "2025-03-01"].groupby("station_id", observed=True).service_failure.mean().rename("fail_2025"))
wave = sx.groupby("expansion_wave").agg(stations=("city", "size"), swaps_per_day=("swaps_per_day", "mean"), fail_mar_jun_2025=("fail_2025", "mean"))
wave["top_location_types"] = sx.groupby("expansion_wave").location_type.agg(lambda s: ", ".join(f"{k} {v}" for k, v in s.value_counts().head(2).items()))
display(wave.round(3))

zone_need = se[(se.date >= "2024-04-01") & (se.date < "2024-07-01")].groupby("zone").service_failure.mean().rename("summer_2024_fail")
zone_new = st[st.expansion_wave != "Launch"].groupby("zone").size().rename("new_stations")
zn = pd.concat([zone_need, zone_new], axis=1).fillna({"new_stations": 0})
zn["city"] = zn.index.str.split("-").str[0]
fig, axes = plt.subplots(1, 2, figsize=(15, 4.3))
ax = axes[0]
ax.scatter(zn.summer_2024_fail, zn.new_stations, s=60, color=PAL["primary"], alpha=.8)
for z, r in zn[(zn.summer_2024_fail > .1) | (zn.new_stations >= 4)].iterrows():
    ax.annotate(z, (r.summer_2024_fail, r.new_stations), fontsize=7, xytext=(3, 2), textcoords="offset points")
pct(ax, "x", decimals=0); ax.set_xlabel("zone failure rate, summer 2024"); ax.set_ylabel("new stations added (Wave 1 + 2)")
ax.set_title(f"New stations vs where service was failing (r = {zn.summer_2024_fail.corr(zn.new_stations):.2f})")
lg = se[(se.expansion_wave == "Launch") & (se.charger_generation == "Gen1") & se.month.dt.month.isin([4, 5, 6])]
yy = lg.groupby([lg.month.dt.year, "city"]).service_failure.mean().unstack(0)
yy.plot.bar(ax=axes[1], color=[PAL["muted"], PAL["bad"]], rot=0); pct(axes[1], decimals=0)
axes[1].set_title("Launch Gen1 stations, Apr–Jun failure rate: no improvement in 2025"); axes[1].set_xlabel("")
save(fig, "11_expansion")
yy.round(3)

# %% [markdown]
# **Answer:** mainly where sites were easiest to open. New stations show essentially **no relationship** with where service was failing in summer 2024. Wave 1 went mostly to highway fuel pumps and residential sites with below-average demand. Wave 2 (all Gen3, mostly markets) was better targeted and busier. But the Gen1 launch hubs that cause the failures were left as they were: their Apr–Jun failure rate in 2025 is **unchanged** from 2024 (Delhi NCR 16.3% → 16.6%, Jaipur 17.1% → 16.6%). The network-wide average improved mainly because new, cooler Gen2/3 capacity diluted the Gen1 share of traffic, not because the busiest failing stations got better.
#
# ### 11.4 Fleet partner value beyond revenue

# %%
pv = partner_econ.drop("Independent").copy()
pv["cm1_total_m"] = pv.cm1 * pv.swaps / 1e6
pv["working_capital_cost_m"] = pv.revenue_m * pv.payment_terms_days / 365 * 0.12
pv["value_rank"] = pv.cm1_total_m.rank(ascending=False).astype(int)
pv["volume_rank"] = pv.swaps.rank(ascending=False).astype(int)
pv[["partner_name", "partner_segment", "swaps", "volume_rank", "revenue_m", "rev_per_swap", "discount_per_swap", "cm1", "cm2", "cm1_total_m", "value_rank",
    "peak_share", "peak_surcharge_billable", "payment_terms_days", "working_capital_cost_m"]].sort_values("cm1_total_m", ascending=False).round(2)

# %% [markdown]
# Per swap, ZipDrop earns the lowest before-wear contribution of any 2W partner (~₹20 vs ₹30–32 for FeastFly, QuickCart, RideMitra and DabbaXpress). **FeastFly, not ZipDrop, is the most valuable partner in total.** It generates more revenue on fewer swaps and pays the peak surcharge. ZipDrop's 45-day terms also tie up the most working capital (at a 12% cost of capital). The 3W cargo partners look attractive on revenue per swap (~₹100) but carry the highest battery wear (~₹83 per swap).
#
# ### 11.5 Support-ticket text: what the categories miss
# Comments are templated English/Hinglish with deliberate misspellings (`staion`, `battry`, `rnage`). Normalising spelling and mapping keywords to the *underlying* issue gives a text theme for every ticket.

# %%
def theme(c):
    t = c.lower().replace("staion", "station").replace("battry", "battery").replace("rnage", "range")
    if any(k in t for k in ["no battery", "charged battery", "empty station", "batteries discharge the"]):
        return "stockout"
    if any(k in t for k in ["range", "dying at", "discharge fast"]):
        return "range / battery"
    if any(k in t for k in ["vehicle performance", "bike problem lag", "scooter weak"]):
        return "vehicle 'performance' (vague)"
    if any(k in t for k in ["queue", "line thi"]):
        return "queue"
    if any(k in t for k in ["amount", "charged extra", "surcharge"]):
        return "billing"
    if any(k in t for k in ["app", "qr"]):
        return "app"
    return "unmatched"


tk["text_theme"] = tk.rider_comment.fillna("").map(theme)
display(pd.crosstab(tk.category, tk.text_theme))
tkb = tk.merge(bt[["battery_id", "current_soh_pct", "cohort"]], on="battery_id", how="left")
tkb["bad_lot"] = tkb.cohort.eq("Kyron KY-2407..09")
tkb.loc[tkb.battery_id.isna(), "bad_lot"] = np.nan
bt_prof = tkb.groupby("text_theme").agg(tickets=("ticket_id", "size"), with_battery=("battery_id", lambda s: s.notna().mean()),
                                        bad_lot_share=("bad_lot", "mean"), battery_current_soh=("current_soh_pct", "mean"))
print(f"Fleet-wide bad-lot share of packs: {(bt.cohort == 'Kyron KY-2407..09').mean():.1%}")
bt_prof.round(3)

# %%
tk["quarter"] = tk.created_ts.dt.to_period("Q").astype(str)
tq = tk[tk.created_ts >= "2024-01-01"].pivot_table(index="quarter", columns="text_theme", values="ticket_id", aggfunc="size").drop(columns="unmatched", errors="ignore")
fig, ax = plt.subplots(figsize=(12, 3.8))
tq.plot(ax=ax, marker="o", lw=2)
ax.set_title("Tickets by underlying theme: range and vague 'vehicle' complaints grew fastest"); ax.set_xlabel("")
save(fig, "11_ticket_themes")
tq

# %% [markdown]
# **The free text adds real information.**
# * **Every one of the 9,385 tickets filed as `other` is a vague vehicle-performance complaint** ("scooter weak lag raha hai", "bike problem lag raha hai"). The packs referenced in these tickets are disproportionately from the bad Kyron lots (34% vs 22% of the fleet) with low current SoH (~73%), the same profile as explicit range complaints. Riders were describing a **battery problem as a vehicle problem**. `app_issue` tickets carry the same battery signature (33% bad-lot packs, SoH ~74%), even though their text is about the app, which is consistent with the brief's warning that some range issues are filed as app issues. Billing tickets, by contrast, reference bad-lot packs only 10% of the time. Combined, range-type complaints are the **largest complaint theme** from 2024 Q4, not the 15% the `low_range` category alone suggests.
# * "scooter dying at NN km" comments embed the distance at which the pack ran out, a free field-range measurement.
# * Structured categories undercount battery issues. A simple keyword re-classification like the one above could be added to the ticketing flow.
#
# ### 11.6 Anomalies worth flagging separately

# %%
retired_ids = set(bt.loc[bt.retired_date.notna(), "battery_id"])
post = comp[comp.date > "2025-06-15"]
pre_commission = comp[["date"]].assign(commission_date=comp.battery_out_id.astype(str).map(bt.set_index("battery_id").commission_date))
anom = pd.DataFrame([
    ["Test stations STN-TST-01/02", "62K events, ₹3.9M revenue over 18 months at 'inactive' test sites", "Reconcile revenue; confirm whether these are live sites"],
    ["Firmware v3.2.0 clock bug", f"{int(se.ts_corrected.sum()):,} events logged 5h30m early (10 Mar–14 Apr 2025)", "Corrected here; audit any hour-based billing (PEAK) in that window"],
    ["Kyron lots KY-2407/08/09", "~3× normal degradation; ~61% SoH within a year", "Warranty claim; inspect the remaining packs"],
    ["'Retired' packs still in service", f"{post.battery_out_id.astype(str).isin(retired_ids).mean():.0%} of swaps after 15 Jun 2025 issued a pack the ledger marks retired",
     "Asset-ledger error or end-of-life packs in circulation (safety risk)"],
    ["Battery IDs in two places at once", "Same pack issued at different stations minutes apart; packs issued before their commission date "
     f"({(pre_commission.date < pre_commission.commission_date).mean():.1%} of swaps)", "Fix pack-ID capture at the cabinet"],
    ["Gen1 cabinets above 40 °C", "Stocked out in ~58% of hot hours; charge time ~174 min", "Priority equipment upgrade"],
], columns=["Anomaly", "Evidence", "Suggested action"])
anom

# %% [markdown]
# ## 12. Key findings and recommendations
#
# ### What is really going on
# 1. **Growth masked two operational failures.** Swaps (2.8×) and revenue (3.0×) grew strongly, but failures grew 5.7× and per-swap contribution after battery wear did not improve.
# 2. **Service failures are a Gen1-in-the-heat problem.** Gen1 cabinets double their charge time above 40 °C and run dry in over half of those hours. Delhi NCR, Jaipur and Hyderabad hold most Gen1 cabinets and the hottest summers, so failure more than doubles there every April–June. It is concentrated, seasonal and predictable.
# 3. **Margin erosion is a battery problem.** Three bad Kyron lots (1,461 packs, ~22% of swaps from Oct 2024) degrade ~3× faster. They pushed wear cost per swap up ~₹16 in two months and wiped out the July 2024 price rise. ZipDrop's 28% discount compounded it.
# 4. **New riders leave because the network fails them early.** Early stockouts and short delivered range are the primary churn drivers. City, 3W and plan type are secondary. Competitors, signup channel and KYC are not drivers.
# 5. **The fixes so far missed the target.** Expansion went to easy sites rather than failing ones, the pricing pilot ran where there was no congestion, and the largest partner contract was renegotiated in the partner's favour.
#
# ### What VoltRelay should prioritise
# | # | Action | Addresses | Evidence |
# |---|---|---|---|
# | 1 | **Upgrade or cool the ~36 Gen1 cabinets in Delhi NCR, Jaipur and Hyderabad before summer 2026**, and pre-position charged stock at those sites in April–June | Failures, churn | §7, §11.1 |
# | 2 | **Replace the bad Kyron lots and claim warranty.** Set an SoH retirement threshold (~75%) and fix the asset ledger | Margin, range, churn | §8, §11.6 |
# | 3 | **Renegotiate ZipDrop** (discount floor, surcharge billing, 30-day terms); **no exclusivity** | Margin | §9, §11.4 |
# | 4 | **Protect new riders' first 14 days**: route them to reliable stations and healthy packs, add a 30-day peak-price grace period, and follow up after any failed first attempt | Retention | §10 |
# | 5 | **Targeted peak pricing** only at congested hot-city hubs in summer, not a network-wide rollout | Revenue, congestion | §9 |
# | 6 | **Site new stations by unmet demand** (failure and saturation by zone), not by ease of lease | Growth quality | §11.3 |
# | 7 | **Data fixes**: cabinet clock sync, pack-ID capture, test-station revenue, ticket re-classification from text | Decision quality | §3, §11.5–11.6 |
#
# *Caveat: this is observational data. The evidence is associational, but the mechanisms (heat → charge time → stockout → failure → churn; bad lot → degradation → wear cost and short range) are consistent across independent tables: telemetry, events, the battery ledger and tickets.*

# %% [markdown]
# ## 13. Export aggregated tables for the dashboard
# The deployed dashboard reads only these small aggregates, not the 830 MB of raw data.

# %%
ex = {}
ex["monthly_network"] = monthly.reset_index()
ex["monthly_city"] = se.groupby(["month", "city"]).agg(attempts=("event_id", "size"), completed=("completed", "sum"), failure_rate=("service_failure", "mean"),
                                                      revenue=("amount_charged_inr", "sum")).reset_index()
ex["event_mix_monthly"] = pd.crosstab(se.month, se.event_type, normalize="index").reset_index()
ex["hourly_failure"] = se.groupby(["hour", "vehicle_class"]).agg(attempts=("event_id", "size"), failure_rate=("service_failure", "mean")).reset_index()
ex["stations"] = sx.reset_index()[["station_id", "city", "zone", "latitude", "longitude", "location_type", "host_type", "expansion_wave", "charger_generation",
                                   "connectivity_tier", "slots_2w", "slots_3w", "swaps_per_day", "fail_2025"]].merge(
    sf[["attempts", "failures", "fail"]].reset_index().rename(columns={"fail": "failure_rate_all"}), on="station_id")
ex["gen_heat"] = tb
ex["battery_cohorts"] = cohort_tbl.reset_index()
ex["battery_lots"] = lot
ex["range_vs_soh"] = rng.groupby(["pack_type", "cohort", "soh_band"], observed=True).km_valid.agg(["mean", "size"]).reset_index()
ex["fleet_monthly"] = mt.reset_index()
ex["pilot_weekly"] = ws.reset_index()
ex["pilot_did"] = did
ex["partners"] = partner_econ.reset_index()
ex["cohort_retention"] = coh.reset_index()
ex["retention_lifts"] = pd.concat([t.reset_index().rename(columns={t.index.name or "index": "level"}).assign(factor=n) for n, t in tables.items()])
ex["retention_logit"] = res.reset_index().rename(columns={"index": "term"})
ex["ticket_themes_quarterly"] = tq.reset_index()
ex["anomalies"] = anom
for name, df in ex.items():
    df.to_csv(OUT_DIR / f"{name}.csv", index=False)
pd.Series({k: f"{len(v):,} rows" for k, v in ex.items()})
