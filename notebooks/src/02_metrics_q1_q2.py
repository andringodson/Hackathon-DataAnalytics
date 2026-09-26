# %% [markdown]
# ## 4. Metric definitions and unit-economics model
#
# | Metric | Definition |
# |---|---|
# | **Attempt** | Any `swap_events` row |
# | **Completed swap** | `event_type == swap_completed` |
# | **Service failure** | `failed_no_charged_battery`, `failed_system_error` or `abandoned_queue`. `cancelled_by_rider` is excluded: those riders leave within 90 s, before the station has failed them. |
# | **Failure rate** | Service failures ÷ attempts |
# | **Revenue** | `amount_charged_inr` on completed swaps (non-completed attempts are ₹0) |
# | **Contribution before wear (CM1)** | Revenue − energy cost − station fixed cost |
# | **Contribution after wear (CM2)** | CM1 − battery wear cost |
#
# **Cost model (per completed swap).** The brief names the three costs to include: energy, battery wear and station costs.
# * **Energy** = `energy_to_recharge_kwh` × the station's `grid_tariff_inr_kwh`.
# * **Station fixed cost** = the station's (monthly rent + maintenance) ÷ its completed swaps that month.
# * **Battery wear** = pack purchase cost × the share of its useful life (initial SoH → 70% retirement threshold) consumed per swap. SoH lost *inside* the observation window is estimated by prorating lifetime loss by days in service within the window, then divided by the number of times the pack was issued. Fast-degrading packs therefore carry a proportionally higher wear cost.
#
# Battery wear rests on the most assumptions, so every margin chart shows CM1 and CM2 side by side. The conclusions below hold under both.

# %%
se = se.merge(st[["station_id", "city", "zone", "grid_tariff_inr_kwh", "charger_generation", "location_type", "expansion_wave",
                  "connectivity_tier", "host_type", "monthly_rent_inr", "monthly_maintenance_inr"]], on="station_id", how="left")
se = se.merge(rd[["rider_id", "vehicle_class", "partner_id", "plan_type"]], on="rider_id", how="left")
se["date"] = se.event_ts.dt.normalize()
se["month"] = se.event_ts.dt.to_period("M").dt.to_timestamp()
se["hour"] = se.event_ts.dt.hour
se["completed"] = se.event_type.eq("swap_completed")
se["service_failure"] = se.event_type.isin(["failed_no_charged_battery", "failed_system_error", "abandoned_queue"])
se["no_charge"] = se.event_type.eq("failed_no_charged_battery")

issues = se.loc[se.completed, "battery_out_id"].astype(str).value_counts().rename("issues")
bt = bt.merge(issues, left_on="battery_id", right_index=True, how="left")
bt["soh_loss"] = (bt.initial_soh_pct - bt.current_soh_pct).clip(lower=0)
end = bt.retired_date.fillna(pd.Timestamp("2025-06-30"))
life_days = (end - bt.commission_date).dt.days.clip(lower=1)
window_days = (end - bt.commission_date.clip(lower=pd.Timestamp("2024-01-01"))).dt.days.clip(lower=0)
bt["soh_loss_window"] = bt.soh_loss * window_days / life_days
bt["soh_loss_per_100_swaps"] = 100 * bt.soh_loss_window / bt.issues
bt["wear_inr_per_swap"] = bt.purchase_cost_inr * (bt.soh_loss_window / (bt.initial_soh_pct - 70)) / bt.issues

wear = bt.set_index("battery_id").wear_inr_per_swap
se["wear_inr"] = se.battery_out_id.astype(str).map(wear).where(se.completed)
se["energy_cost_inr"] = se.energy_to_recharge_kwh * se.grid_tariff_inr_kwh
sm = se[se.completed].groupby(["station_id", "month"], observed=True).size().rename("n").reset_index()
sm = sm.merge(st[["station_id", "monthly_rent_inr", "monthly_maintenance_inr"]], on="station_id")
sm["fixed_per_swap"] = (sm.monthly_rent_inr + sm.monthly_maintenance_inr) / sm.n
se = se.merge(sm[["station_id", "month", "fixed_per_swap"]], on=["station_id", "month"], how="left")
se.loc[~se.completed, "fixed_per_swap"] = np.nan
se["cm1"] = (se.amount_charged_inr - se.energy_cost_inr - se.fixed_per_swap).where(se.completed)
se["cm2"] = (se.cm1 - se.wear_inr).where(se.completed)
comp = se[se.completed]
comp[["amount_charged_inr", "energy_cost_inr", "fixed_per_swap", "wear_inr", "cm1", "cm2"]].describe().T[["mean", "25%", "50%", "75%"]]

# %% [markdown]
# ## 5. Core Question 1 — Network performance over time
# *How have completed swaps, revenue, failure rates and contribution margin per swap trended? Do they tell the same story?*

# %%
m = se.groupby("month").agg(attempts=("event_id", "size"), completed=("completed", "sum"), failures=("service_failure", "sum"),
                            revenue=("amount_charged_inr", "sum"), stations=("station_id", "nunique"), riders=("rider_id", "nunique"))
m["failure_rate"] = m.failures / m.attempts
m = m.join(comp.groupby("month")[["amount_charged_inr", "energy_cost_inr", "fixed_per_swap", "wear_inr", "cm1", "cm2"]].mean().add_prefix("per_swap_"))
monthly = m.copy()
m[["attempts", "completed", "failures", "failure_rate", "revenue", "stations", "per_swap_amount_charged_inr", "per_swap_cm1", "per_swap_cm2"]]

# %%
first, last = m.iloc[:3].mean(), m.iloc[-3:].mean()
growth = pd.DataFrame({"Q1 2024 (monthly avg)": first, "Q2 2025 (monthly avg)": last})
growth["change"] = growth.iloc[:, 1] / growth.iloc[:, 0] - 1
growth.loc[["completed", "revenue", "failures", "failure_rate", "riders", "stations", "per_swap_amount_charged_inr", "per_swap_cm1", "per_swap_cm2"]]

# %%
EVENTS = [("2024-07-01", "price rise"), ("2024-08-01", "Kyron lots KY-2407..09"), ("2024-10-01", "peak pilot"), ("2024-11-01", "ZipDrop 12%→28%")]


def mark(ax, events=EVENTS, top=0.60, step=0.07):
    tr = ax.get_xaxis_transform()
    for i, (d, lbl) in enumerate(events):
        ax.axvline(pd.Timestamp(d), color=PAL["muted"], ls=":", lw=1)
        ax.text(pd.Timestamp(d), top - i * step, " " + lbl, transform=tr, fontsize=8, color="#444", va="top", ha="left",
                bbox=dict(facecolor="white", edgecolor="none", alpha=.8, pad=1))


fig, axes = plt.subplots(2, 2, figsize=(15, 8.5))
idx = m[["completed", "revenue", "failures"]] / m[["completed", "revenue", "failures"]].iloc[0] * 100
ax = axes[0, 0]
idx.plot(ax=ax, color=[PAL["primary"], PAL["good"], PAL["bad"]], lw=2.2)
ax.set_title("Growth index (Jan 2024 = 100): failures grew fastest"); ax.set_xlabel("")
ax = axes[0, 1]
ax.plot(m.index, m.failure_rate, color=PAL["bad"], lw=2.2, marker="o", ms=4)
ax.set_title("Service-failure rate: flat ~4% except two summer spikes"); pct(ax, decimals=0)
ax = axes[1, 0]
ax.bar(m.index, m.revenue / 1e6, width=20, color=PAL["good"])
ax.set_title("Monthly revenue (₹ million)")
ax = axes[1, 1]
ax.plot(m.index, m.per_swap_cm1, color=PAL["primary"], lw=2.2, marker="o", ms=4, label="CM1: before battery wear")
ax.plot(m.index, m.per_swap_cm2, color=PAL["accent"], lw=2.2, marker="o", ms=4, label="CM2: after battery wear")
ax.axhline(0, color="black", lw=.8)
ax.set_title("Contribution margin per completed swap (₹)"); ax.legend(loc="center left", fontsize=8); mark(ax)
fig.tight_layout()
save(fig, "05_network_trends")

# %%
comp_cols = ["per_swap_amount_charged_inr", "per_swap_energy_cost_inr", "per_swap_fixed_per_swap", "per_swap_wear_inr"]
w = m[comp_cols].rename(columns=dict(zip(comp_cols, ["Revenue", "Energy", "Station fixed", "Battery wear"])))
fig, ax = plt.subplots(figsize=(13, 4.2))
ax.stackplot(w.index, w["Energy"], w["Station fixed"], w["Battery wear"], labels=["Energy", "Station fixed", "Battery wear"],
             colors=["#f2c14e", "#9aa5b1", PAL["accent"]], alpha=.85)
ax.plot(w.index, w["Revenue"], color=PAL["good"], lw=2.5, label="Revenue per swap")
ax.set_title("Per-swap revenue vs cost stack (₹): the price rise was absorbed by battery wear within two months")
ax.legend(loc="upper left", ncol=2, fontsize=8); ax.set_ylim(0, 125); mark(ax, top=0.97)
save(fig, "05_cost_stack")
w.round(2).iloc[[0, 5, 6, 8, 9, 10, 17]]

# %% [markdown]
# ### Answer to Q1
# **No — the metrics tell four different stories.**
# * **Volume and revenue**: completed swaps grew **2.8×** and revenue **3.0×** between Q1 2024 and Q2 2025, as stations grew from 90 to 150 and monthly active riders grew 2.6×.
# * **Failures grew faster than volume.** Monthly service failures rose **5.7×** (vs 2.8× for completions). The rate is not drifting up steadily: it sits at ~4% most of the year and **spikes every summer**, to 11.9% in May 2024 and 9.5% in May 2025. Growth simply puts more swaps into those summer months.
# * **Margin moved against revenue.** The July 2024 base-price rise lifted revenue per swap by ~₹5 and briefly more than halved the per-swap loss (CM2 −₹14 → −₹7). From September 2024, **battery wear per swap jumped ~₹16 (+44%)** and the ZipDrop renegotiation (Nov 2024) added ~₹2 of network-wide discount per swap. Together these wiped out the price rise, and CM2 has sat near −₹16 to −₹20 since.
# * Energy and station fixed costs per swap actually **fell** (better station utilisation; lower energy per swap as packs age). Battery wear is the cost that moved the margin.

# %% [markdown]
# ## 6. Core Question 2 — Service failures and customer experience
# *How do queue wait, failed and abandoned swaps relate to station, hour, season and vehicle class? Is service quality even, or concentrated?*

# %%
fail_mix = pd.crosstab(se.month, se.event_type, normalize="index")
fig, ax = plt.subplots(figsize=(13, 3.8))
fail_mix.drop(columns="swap_completed").plot.area(ax=ax, color=["#e07a1f", "#9aa5b1", "#c0392b", "#6c3483"], alpha=.85)
ax.set_title("Non-completed attempts by type: summer spikes are stockouts ('no charged battery') plus the abandonment they cause")
pct(ax, decimals=0); ax.set_xlabel(""); ax.legend(fontsize=8, loc="upper center", ncol=4)
save(fig, "06_failure_mix")

# %%
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
h = se.groupby("hour").agg(fail=("service_failure", "mean"), attempts=("event_id", "size"))
ax = axes[0]
ax.plot(h.index, h.fail, color=PAL["bad"], marker="o", lw=2); pct(ax, decimals=1)
ax.axvspan(18.5, 22.5, color=PAL["muted"], alpha=.12, lw=0)
ax.set_title("By hour: evening peak (shaded) fails most"); ax.set_xlabel("hour (corrected)"); ax.set_ylabel("failure rate")
mv = se.pivot_table(index="month", columns="vehicle_class", values="service_failure", aggfunc="mean")
ax = axes[1]
mv.plot(ax=ax, color=[PAL["primary"], PAL["accent"]], lw=2.2, marker="o", ms=3)
ax.set_title("By vehicle class: 3W fails 2× as often"); pct(ax, decimals=0); ax.set_xlabel("")
city_m = se.pivot_table(index="city", columns="month", values="service_failure", aggfunc="mean")
ax = axes[2]
sns.heatmap(city_m, ax=ax, cmap="Reds", cbar_kws={"format": mtick.PercentFormatter(1.0, decimals=0)}, xticklabels=3)
ax.set_xticklabels([pd.Timestamp(t.get_text()).strftime("%b-%y") for t in ax.get_xticklabels()], rotation=45)
ax.set_title("By city × month: summer spikes hit Delhi, Jaipur, Hyderabad"); ax.set_xlabel(""); ax.set_ylabel("")
fig.tight_layout()
save(fig, "06_failure_hour_class_city")

# %%
se["season"] = se.month.dt.month.map({12: "Winter (Dec-Feb)", 1: "Winter (Dec-Feb)", 2: "Winter (Dec-Feb)", 3: "Summer (Mar-May)", 4: "Summer (Mar-May)",
                                      5: "Summer (Mar-May)", 6: "Monsoon (Jun-Sep)", 7: "Monsoon (Jun-Sep)", 8: "Monsoon (Jun-Sep)", 9: "Monsoon (Jun-Sep)",
                                      10: "Post-monsoon (Oct-Nov)", 11: "Post-monsoon (Oct-Nov)"})
display(se.groupby(["season", "vehicle_class"]).service_failure.mean().unstack().style.format("{:.1%}"))

# %% [markdown]
# **Queue wait is not where the experience breaks.** Mean wait for completed swaps is ~243 s in every hour, city and station generation, with no link to load. Failure shows up as *no battery at all*, not as a longer queue. Abandoned attempts are the exception: riders give up after a median ~11 minutes.

# %%
display(se[se.completed].groupby("charger_generation").queue_wait_sec.describe()[["mean", "50%", "75%"]])
display(se.groupby("event_type", observed=True).queue_wait_sec.median().rename("median wait (s)").to_frame().T)
print("Correlation of station-day mean wait with station-day failure rate:",
      round(se.groupby(["station_id", "date"], observed=True).agg(w=("queue_wait_sec", "mean"), f=("service_failure", "mean")).corr().iloc[0, 1], 3))

# %% [markdown]
# ### Is failure concentrated?

# %%
sf = se.groupby("station_id", observed=True).agg(attempts=("event_id", "size"), failures=("service_failure", "sum"), fail=("service_failure", "mean")).join(
    st.set_index("station_id")[["city", "charger_generation", "location_type", "expansion_wave", "connectivity_tier"]])
sf = sf.sort_values("fail", ascending=False)
lor = sf.sort_values("failures", ascending=False)
fig, axes = plt.subplots(1, 2, figsize=(14, 4.3))
ax = axes[0]
ax.plot(np.arange(1, len(lor) + 1) / len(lor), lor.failures.cumsum() / lor.failures.sum(), color=PAL["bad"], lw=2.2, label="failures")
ax.plot(np.arange(1, len(lor) + 1) / len(lor), lor.attempts.cumsum() / lor.attempts.sum(), color=PAL["primary"], lw=2.2, label="attempts (same stations)")
ax.plot([0, 1], [0, 1], color=PAL["muted"], ls=":")
pct(ax); pct(ax, "x"); ax.legend(); ax.set_xlabel("share of stations (worst first)"); ax.set_title("Top 20% of stations: 43% of failures, 31% of attempts")
ax = axes[1]
sns.stripplot(data=sf.reset_index(), x="city", y="fail", hue="charger_generation", palette=GEN_PAL, ax=ax, size=6, jitter=.25,
              order=["Jaipur", "Delhi NCR", "Hyderabad", "Pune", "Bengaluru", "Mumbai"])
pct(ax, decimals=0); ax.set_title("Station failure rate: the high tail is Gen1 in three cities"); ax.set_xlabel("")
save(fig, "06_station_concentration")
top = sf.head(25)
print(f"25 worst stations: {top.charger_generation.value_counts().to_dict()} | {top.expansion_wave.value_counts().to_dict()} | {top.city.value_counts().to_dict()}")
k = int(len(lor) * .2)
print(f"Top 20% of stations by failures hold {lor.failures.iloc[:k].sum() / lor.failures.sum():.1%} of failures and {lor.attempts.iloc[:k].sum() / lor.attempts.sum():.1%} of attempts")

# %%
ct = pd.crosstab(se.charger_generation == "Gen1", se.service_failure)
chi2, pval, *_ = stats.chi2_contingency(ct)
g1 = se[se.charger_generation == "Gen1"].service_failure.mean()
g23 = se[se.charger_generation != "Gen1"].service_failure.mean()
print(f"Gen1 failure {g1:.2%} vs Gen2/3 {g23:.2%}  (chi-square={chi2:,.0f}, p={pval:.1e})")

# %% [markdown]
# ### Answer to Q2
# * **Not evenly spread.** Failures concentrate at **Gen1 charger stations in Delhi NCR, Jaipur and Hyderabad**. All 25 worst stations are Gen1 launch-era sites in those three cities (13 Delhi NCR, 10 Jaipur, 2 Hyderabad); the worst 20% of stations carry 43% of failures on 31% of attempts. Gen1 fails at 6.8% vs 4.4% for Gen2/3 (p ≈ 0).
# * **Season beats hour.** Evening peaks (19–22 h) fail slightly more (6.2% vs ~5.0%), but the dominant pattern is **summer**: failure more than doubles from April to June, and the extra failures are stockouts plus the abandonment that follows.
# * **3W riders fail twice as often as 2W riders** in every month (8–15% vs 3–11%). 3W slots are scarce, and 3W riders cannot fall back on 2W stock.
# * **Queue wait is flat** (~4 minutes) and uninformative. The customer experience fails through *empty cabinets*, not slow queues.
