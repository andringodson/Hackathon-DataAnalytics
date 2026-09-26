# %% [markdown]
# ## 7. Core Question 3 — Station and geographic patterns
# *How do charger generation, location type and commissioning timing relate to service performance, battery turnaround time and complaints?*

# %%
display(pd.crosstab(st.city, st.charger_generation, margins=True))
display(pd.crosstab(st.expansion_wave, [st.charger_generation]).join(pd.crosstab(st.expansion_wave, st.location_type)))

# %% [markdown]
# Gen1 cabinets are **only** in the Launch wave and are unevenly spread: 36 of the 51 are in Delhi NCR, Hyderabad and Jaipur, the three cities with the hottest summers (daily highs up to 46–49 °C). Mumbai has two.
#
# ### The mechanism: Gen1 cabinets cannot charge in the heat
# Hourly telemetry (`ok` rows only) shows what happens inside the cabinet as ambient temperature rises.

# %%
ok = hs[hs.telemetry_status == "ok"].copy()
ok["temp_band"] = pd.cut(ok.ambient_temp_c, [-10, 25, 30, 35, 40, 55], labels=["<25°C", "25–30", "30–35", "35–40", ">40°C"])
ok["stockout_2w"] = ok.charged_2w_min.eq(0)
tb = ok.groupby(["temp_band", "charger_generation"], observed=True).agg(charge_minutes=("avg_charge_minutes", "mean"), stockout_hours=("stockout_2w", "mean"),
                                                                       quarantined=("packs_quarantined", "mean"), hours=("station_id", "size")).reset_index()
fig, axes = plt.subplots(1, 2, figsize=(14, 4.2))
sns.barplot(data=tb, x="temp_band", y="charge_minutes", hue="charger_generation", palette=GEN_PAL, ax=axes[0])
axes[0].set_title("Battery turnaround: Gen1 charge time doubles above 40°C"); axes[0].set_xlabel("ambient temperature"); axes[0].set_ylabel("avg charge minutes")
sns.barplot(data=tb, x="temp_band", y="stockout_hours", hue="charger_generation", palette=GEN_PAL, ax=axes[1])
axes[1].set_title("Share of hours with zero charged 2W packs"); axes[1].set_xlabel("ambient temperature"); pct(axes[1], decimals=0)
save(fig, "07_gen_heat_mechanism")
tb.pivot(index="temp_band", columns="charger_generation", values=["charge_minutes", "stockout_hours"]).round(3)

# %%
d = se.groupby(["city", "date"], observed=True).agg(fail=("service_failure", "mean"), attempts=("event_id", "size")).reset_index().merge(cx, on=["city", "date"])
d["temp_band"] = pd.cut(d.max_temp_c, [0, 30, 35, 38, 41, 55], labels=["<30°C", "30–35", "35–38", "38–41", ">41°C"])
fig, ax = plt.subplots(figsize=(8, 3.6))
sns.barplot(data=d, x="temp_band", y="fail", color=PAL["bad"], ax=ax, errorbar=None)
pct(ax, decimals=0); ax.set_title("City-day failure rate by daily maximum temperature"); ax.set_xlabel("max temperature")
save(fig, "07_failure_vs_temp")
print(f"Heat-alert days: {d[d.heat_alert].fail.mean():.1%} vs other days {d[~d.heat_alert].fail.mean():.1%}")
print(f"Grid outage >1h days: {d[d.grid_outage_hours > 1].fail.mean():.1%} vs {d[d.grid_outage_hours <= 1].fail.mean():.1%}")
print(f"Flood-disruption days: {d[d.flood_disruption].fail.mean():.1%} (rain does not drive failures)")
print(d[["fail", "max_temp_c", "rainfall_mm", "grid_outage_hours"]].corr().fail.round(3).to_dict())

# %% [markdown]
# ### Controlling for everything at once
# Station-day OLS of failure rate on station attributes plus the day's max temperature, with the key **generation × heat** interaction. Standard errors are clustered by station.

# %%
sd = se.groupby(["station_id", "date"], observed=True).agg(fail=("service_failure", "mean"), attempts=("event_id", "size")).reset_index()
sd = sd.merge(st[["station_id", "city", "charger_generation", "location_type", "expansion_wave", "connectivity_tier", "host_type"]], on="station_id")
sd = sd.merge(cx[["city", "date", "max_temp_c", "grid_outage_hours"]], on=["city", "date"])
sd["hot"] = (sd.max_temp_c > 38).astype(int)
ols = smf.wls("fail ~ C(charger_generation, Treatment('Gen2')) * hot + C(city) + C(location_type) + C(connectivity_tier) + C(host_type) + grid_outage_hours",
              data=sd, weights=sd.attempts).fit(cov_type="cluster", cov_kwds={"groups": sd.station_id.astype(str)})
coef = ols.summary2().tables[1][["Coef.", "Std.Err.", "P>|z|"]]
coef[coef.index.str.contains("charger|hot|connectivity|location|grid|host")].round(4)

# %% [markdown]
# Holding city, site type, host and connectivity constant:
# * On a normal day a Gen1 cabinet fails only **~0.4 pp** more often than Gen2.
# * A >38 °C day adds **~5 pp** at a Gen2 station, and **a further ~9 pp at Gen1** (the interaction term), so Gen1 on a hot day is ~14 pp worse than a normal day. Gen3 largely cancels the heat effect (−3.7 pp).
# * Each hour of city-wide grid outage adds ~0.7 pp.
# * Location type, host type and connectivity are all within ±0.1 pp and mostly not significant.
#
# The city differences are almost entirely "how many Gen1 cabinets does it have, and how hot does it get".

# %%
tks = tk.dropna(subset=["station_id"]).merge(st[["station_id", "charger_generation", "city", "expansion_wave"]], on="station_id")
per1k = pd.DataFrame({col: (tks.groupby(col).size() / comp.groupby(col, observed=True).size() * 1000) for col in ["charger_generation"]})
city1k = (tks.groupby("city").size() / comp.groupby("city", observed=True).size() * 1000).sort_values(ascending=False)
fig, axes = plt.subplots(1, 2, figsize=(14, 3.8))
city1k.plot.bar(ax=axes[0], color=PAL["primary"]); axes[0].set_title("Station-linked tickets per 1,000 completed swaps"); axes[0].set_xlabel("")
mix = pd.crosstab(tks.charger_generation, tks.category, normalize="index")
mix.plot.barh(stacked=True, ax=axes[1], colormap="tab20c"); axes[1].set_title("Ticket mix by charger generation"); pct(axes[1], "x")
axes[1].legend(fontsize=7, loc="lower center", bbox_to_anchor=(.5, -.45), ncol=3); axes[1].set_ylabel("")
save(fig, "07_tickets")
display(mix.style.format("{:.0%}"))

# %% [markdown]
# ### Answer to Q3
# * **Charger generation is the station attribute that matters.** Gen1 turnaround is ~88 min vs 64 (Gen2) and 42 (Gen3) on normal days. Above 40 °C Gen1 slows to ~174 min and runs out of charged 2W packs in **~58% of hours**, while Gen2/3 barely change (≤1%).
# * **Geography is a proxy for Gen1 × heat.** Delhi NCR, Jaipur and Hyderabad have the most Gen1 cabinets *and* the hottest summers, so they carry the summer failure spikes and the highest complaint rates (13–15 tickets per 1,000 swaps vs ~9 in Mumbai, Bengaluru and Pune). Heat-alert days fail at ~16% vs 5%. Rain and floods do not raise failures.
# * **Location type, host type and connectivity matter little** once generation and heat are controlled. Connectivity affects *data quality* (missing telemetry, offline sync) rather than service.
# * **Complaints follow the mechanism.** Gen1 tickets are dominated by *no battery available*. Gen3 stations (opened later, when the fleet's packs were older) skew towards *low range* and vehicle-performance tickets — a battery problem, not a station problem (Q4).

# %% [markdown]
# ## 8. Core Question 4 — Battery and equipment performance
# *How do SoH, charge cycles, supplier and manufacturing lot relate to delivered range and swap frequency? Do any cohorts stand out?*

# %%
bt["cohort"] = np.where(bt.manufacturing_lot.isin(["KY-2407", "KY-2408", "KY-2409"]), "Kyron KY-2407..09", bt.supplier)
display(pd.crosstab(bt.commission_date.dt.to_period("Q"), bt.supplier).T)
cohort_tbl = bt.groupby(["cohort", "pack_type"]).agg(packs=("battery_id", "size"), purchase_cost=("purchase_cost_inr", "mean"), initial_soh=("initial_soh_pct", "mean"),
                                                     current_soh=("current_soh_pct", "mean"), soh_loss_per_100_swaps=("soh_loss_per_100_swaps", "mean"),
                                                     wear_inr_per_swap=("wear_inr_per_swap", "mean"), retired_share=("retired_date", lambda s: s.notna().mean()))
cohort_tbl.round(2)

# %%
lot = bt.groupby(["supplier", "manufacturing_lot"]).agg(loss=("soh_loss_per_100_swaps", "mean"), packs=("battery_id", "size"),
                                                        commissioned=("commission_date", "min")).reset_index().sort_values("commissioned")
fig, ax = plt.subplots(figsize=(15, 4))
colors = [PAL["bad"] if l in ("KY-2407", "KY-2408", "KY-2409") else {"Cellora": PAL["primary"], "Amptek": PAL["good"], "Kyron": PAL["accent"]}[s]
          for s, l in zip(lot.supplier, lot.manufacturing_lot)]
ax.bar(lot.manufacturing_lot, lot.loss, color=colors)
ax.set_title("SoH points lost per 100 swaps, by manufacturing lot (ordered by commissioning): three Kyron lots degrade ~3× faster")
ax.set_ylabel("SoH pts / 100 swaps"); ax.tick_params(axis="x", rotation=90, labelsize=7)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=PAL["primary"], label="Cellora"), Patch(color=PAL["good"], label="Amptek"), Patch(color=PAL["accent"], label="Kyron (other lots)"),
                   Patch(color=PAL["bad"], label="Kyron KY-2407/08/09")], fontsize=8)
save(fig, "08_lot_degradation")
print(bt.groupby("bms_firmware").soh_loss_per_100_swaps.mean().round(2).to_dict(), "<- BMS firmware makes no difference")

# %%
rng = comp.dropna(subset=["km_valid", "soh_in_pct"])[["battery_in_id", "soh_in_pct", "km_valid", "energy_to_recharge_kwh", "month"]].copy()
rng = rng.merge(bt[["battery_id", "cohort", "pack_type"]].rename(columns={"battery_id": "battery_in_id"}), on="battery_in_id")
rng["soh_band"] = pd.cut(rng.soh_in_pct, [50, 70, 75, 80, 85, 90, 95, 100.01], labels=["<70", "70–75", "75–80", "80–85", "85–90", "90–95", "95–100"])
fig, axes = plt.subplots(1, 3, figsize=(17, 4))
for ax, pt in zip(axes[:2], ["2W_2.1kWh", "3W_4.8kWh"]):
    sns.pointplot(data=rng[rng.pack_type == pt], x="soh_band", y="km_valid", hue="cohort", ax=ax, errorbar=None,
                  palette={"Cellora": PAL["primary"], "Amptek": PAL["good"], "Kyron": PAL["accent"], "Kyron KY-2407..09": PAL["bad"]})
    ax.set_title(f"{pt}: km delivered per swap vs SoH"); ax.set_xlabel("SoH of returned pack"); ax.set_ylabel("km since last swap")
    ax.legend(title="cohort (Cellora and Amptek overlap)", fontsize=8, title_fontsize=8)
mt = rng.groupby("month").agg(soh=("soh_in_pct", "mean"), km=("km_valid", "mean"))
mt["bad_lot_share"] = comp.assign(bad=comp.battery_out_id.astype(str).isin(bt.loc[bt.cohort == "Kyron KY-2407..09", "battery_id"])).groupby("month").bad.mean()
ax = axes[2]
ax.plot(mt.index, mt.km, color=PAL["primary"], lw=2.2, label="km per swap"); ax.set_ylabel("km per swap")
ax2 = ax.twinx(); ax2.plot(mt.index, mt.soh, color=PAL["accent"], lw=2.2, label="mean SoH of returned packs"); ax2.grid(False); ax2.set_ylabel("SoH %")
ax.set_title("Network: delivered range fell 30% as the fleet aged"); ax.tick_params(axis="x", rotation=45)
ax.legend(ax.get_lines() + ax2.get_lines(), ["km per swap", "mean SoH of returned packs"], loc="lower left", fontsize=8)
save(fig, "08_range_vs_soh")
mt.iloc[[0, 6, 9, 12, 17]].round(2)

# %%
rdd = comp.groupby(["rider_id", "date"], observed=True).agg(swaps=("event_id", "size"), soh=("soh_out_pct", "mean"))
rdd["soh_band"] = pd.cut(rdd.soh, [50, 70, 75, 80, 85, 90, 95, 100.01], labels=["<70", "70–75", "75–80", "80–85", "85–90", "90–95", "95–100"])
freq = rdd.groupby("soh_band", observed=True).swaps.agg(["mean", "size"]).rename(columns={"mean": "swaps per rider-day", "size": "rider-days"})
freq

# %% [markdown]
# ### Answer to Q4
# * **SoH drives delivered range almost linearly.** A 2W pack returned at 95–100% SoH has covered ~67 km; at <70% SoH, ~38 km. Riders on degraded packs come back sooner: rider-days on 70–80% SoH packs average **~1.55 swaps vs ~1.3** on healthy packs. Degradation therefore *adds load* to the stations that are already stocking out.
# * **One cohort stands out: Kyron lots KY-2407, KY-2408 and KY-2409** (1,461 packs commissioned Jul–Sep 2024, the new supplier's first deliveries). They lose **~9.6 SoH points per 100 swaps (2W) and ~7.9 (3W) vs ~3** for every other lot. Every Kyron 2W pack came from these lots. Kyron's later lots (small 3W batches from Oct 2024) degrade normally, which points to a **batch defect** rather than a bad supplier. The 2W packs reached ~61% SoH within a year and were all marked retired on 15 Jun 2025. They make up ~22% of all swaps from October 2024 onwards.
# * At the *same* SoH, the bad Kyron lots also deliver less range (2W at 90–100% SoH: ~58 km vs ~66 km for Cellora/Amptek), so riders felt them before SoH showed it.
# * **Cost impact:** the bad lots' wear cost is ~₹106 per swap vs ~₹30–33 for 2W packs from other cohorts. This is the September 2024 step in battery wear seen in Q1.
# * **BMS firmware makes no difference** (4.3–4.5 SoH pts per 100 swaps across versions). Network-wide, mean SoH of returned packs fell from 99% to 76% and delivered range from ~74 km to ~51 km per swap. Range complaints followed (§11.4).
