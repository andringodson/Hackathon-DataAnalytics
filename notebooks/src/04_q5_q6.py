# %% [markdown]
# ## 9. Core Question 5 — Pricing and partner economics
# *How do the base price change, the peak/off-peak pilot and fleet contract terms relate to swap timing, revenue and margin? Do they affect every segment the same way?*
#
# **What the data says happened** (reconstructed from `list_price_inr` and `tariff_code`, since the brief gives no dates):
# * **Base price rise on 1 Jul 2024:** 2W ₹60 → ₹65, 3W ₹100 → ₹110.
# * **Peak/off-peak pilot from 1 Oct 2024 in Bengaluru and Pune**, Independent riders see PEAK ₹80 (12–14 h, 19–23 h) and OFFPEAK ₹57 (23–06 h, 14–17 h). Partner riders keep the `PARTNER` tariff code, but the surcharge is added to their employer's invoice where `peak_surcharge_billable = Y`. ZipDrop and Swiggle Go are exempt.

# %%
comp = se[se.completed].copy()
comp["segment"] = np.where(comp.plan_type == "partner_billed", "partner", "independent")
comp["peak_hour"] = comp.hour.isin([12, 13, 19, 20, 21, 22])
print(pd.crosstab(comp.segment, comp.tariff_code))
rm = comp.groupby(["rider_id", "month"], observed=True).size().rename("swaps").reset_index().merge(rd[["rider_id", "plan_type"]], on="rider_id")
pr = rm.pivot_table(index="month", columns="plan_type", values="swaps", aggfunc="mean")
pr.loc["2024-04-01":"2024-10-01"].round(2)

# %% [markdown]
# **Base price rise:** no visible demand penalty. Swaps per active rider rose in July for all plan types (the dip in May–June is the summer stockout, not price), and the July 2024 new-rider cohort retained at 88%, above the pre-rise average (§10). Revenue per completed swap rose ~₹5 (+8.6%).
#
# ### Peak pilot — difference-in-differences
# Treatment: Bengaluru + Pune stations after 1 Oct 2024. Control: the other four cities. Window: Jul–Dec 2024 (after the base-price change, before 2025 expansion). Outcome: share of each station-day's completed swaps that fall in peak hours. Station and date fixed effects; SEs clustered by station.

# %%
fpm = fp.set_index("partner_id").peak_surcharge_billable
comp["exposure"] = np.select([comp.segment == "independent", comp.partner_id.map(fpm).eq("Y")], ["independent (pays PEAK)", "partner, surcharge billed"], "partner, surcharge exempt")
win = comp[(comp.date >= "2024-07-01") & (comp.date < "2025-01-01")].copy()
win["pilot"] = win.city.isin(["Bengaluru", "Pune"]).astype(int)
win["post"] = (win.date >= "2024-10-01").astype(int)
did_rows = []
for grp, g in win.groupby("exposure"):
    sdd = g.groupby(["station_id", "date"], observed=True).agg(peak=("peak_hour", "mean"), n=("event_id", "size"), rev=("amount_charged_inr", "mean"),
                                                           pilot=("pilot", "first"), post=("post", "first")).reset_index()
    sdd["station_id"] = sdd.station_id.astype(str)
    for y in ["peak", "rev"]:
        r = smf.wls(f"{y} ~ pilot:post + C(station_id) + C(date)", data=sdd, weights=sdd.n).fit(cov_type="cluster", cov_kwds={"groups": sdd.station_id})
        did_rows.append({"segment": grp, "outcome": {"peak": "peak-hour share (pp)", "rev": "revenue per swap (₹)"}[y],
                         "DiD estimate": r.params["pilot:post"] * (100 if y == "peak" else 1), "CI low": r.conf_int().loc["pilot:post", 0] * (100 if y == "peak" else 1),
                         "CI high": r.conf_int().loc["pilot:post", 1] * (100 if y == "peak" else 1), "p": r.pvalues["pilot:post"]})
did = pd.DataFrame(did_rows)
did.round(3)

# %%
fig, axes = plt.subplots(1, 2, figsize=(15, 4))
wk = comp[(comp.date >= "2024-06-01") & (comp.date < "2025-03-01") & (comp.segment == "independent")].copy()
wk["group"] = np.where(wk.city.isin(["Bengaluru", "Pune"]), "Pilot cities (BLR, PUN)", "Control cities")
wk["week"] = wk.date.dt.to_period("W").dt.start_time
ws = wk.groupby(["week", "group"]).peak_hour.mean().unstack()
ws.plot(ax=axes[0], color=[PAL["muted"], PAL["accent"]], lw=2.2)
axes[0].axvline(pd.Timestamp("2024-10-01"), color="black", ls=":"); pct(axes[0], decimals=0)
axes[0].set_title("Independent riders: share of swaps in peak hours"); axes[0].set_xlabel("")
peak_fail = se[(se.date >= "2024-07-01") & (se.date < "2025-01-01") & se.hour.isin([12, 13, 19, 20, 21, 22])].copy()
peak_fail["group"] = np.where(peak_fail.city.isin(["Bengaluru", "Pune"]), "Pilot", "Control")
peak_fail["period"] = np.where(peak_fail.date >= "2024-10-01", "After 1 Oct", "Before")
pf = peak_fail.groupby(["group", "period"]).service_failure.mean().unstack()[["Before", "After 1 Oct"]]
pf.plot.bar(ax=axes[1], color=[PAL["muted"], PAL["accent"]], rot=0); pct(axes[1], decimals=1)
axes[1].set_title("Peak-hour failure rate: unchanged by the pilot"); axes[1].set_xlabel("")
save(fig, "09_peak_pilot")
pf.round(4)

# %% [markdown]
# **The pilot shifted demand a little, but not where it was needed.**
# * Riders whose swaps carry the surcharge moved **2.5 pp (independents) to 3.5 pp (billable partners)** of their swaps out of peak hours (independents: ~60% → ~57%). Exempt partners (ZipDrop, Swiggle Go) did not move (−0.5 pp, not significant).
# * Revenue per swap rose **~₹8 for independents and ~₹6 for billable partners** relative to control cities, and not at all for exempt partners. The pilot is **revenue-accretive**.
# * **Peak-hour reliability did not change**, because Bengaluru and Pune were already the two most reliable cities (few Gen1 cabinets, mild summers). The pilot tested congestion pricing where there was little congestion to relieve.
#
# ### Fleet partner economics

# %%
comp["pid"] = comp.partner_id.fillna("Independent")
pe = comp.groupby("pid").agg(swaps=("event_id", "size"), revenue_m=("amount_charged_inr", lambda s: s.sum() / 1e6), rev_per_swap=("amount_charged_inr", "mean"),
                             discount_per_swap=("discount_inr", "mean"), energy=("energy_cost_inr", "mean"), wear=("wear_inr", "mean"),
                             station=("fixed_per_swap", "mean"), cm1=("cm1", "mean"), cm2=("cm2", "mean"), cm2_total_m=("cm2", lambda s: s.sum() / 1e6),
                             peak_share=("peak_hour", "mean"))
pe = pe.join(fp.set_index("partner_id")[["partner_name", "partner_segment", "contract_type", "discount_pct", "discount_pct_after_amendment", "peak_surcharge_billable", "payment_terms_days"]])
pe["partner_name"] = pe.partner_name.fillna("Independent riders")
pe = pe.sort_values("swaps", ascending=False)
partner_econ = pe.copy()
pe.round(2)

# %%
fig, axes = plt.subplots(1, 2, figsize=(15, 4.6))
p2 = pe.drop("Independent")
ax = axes[0]
colors = [PAL["bad"] if n == "ZipDrop" else (PAL["accent"] if s == "cargo_3w" else PAL["primary"]) for n, s in zip(p2.partner_name, p2.partner_segment)]
ax.scatter(p2.revenue_m, p2.cm1, s=p2.swaps / 2500, c=colors, alpha=.85, edgecolor="white")
for _, r in p2.iterrows():
    ax.annotate(r.partner_name, (r.revenue_m, r.cm1), fontsize=8, xytext=(5, 3), textcoords="offset points")
ax.set_xlabel("total revenue (₹ million)"); ax.set_ylabel("CM1 per swap (₹, before wear)")
ax.set_title("Largest partner, lowest 2W margin: ZipDrop")
z = comp[comp.pid == "FP-03"].groupby("month").agg(discount=("discount_inr", "mean"), cm1=("cm1", "mean"), swaps=("event_id", "size"))
ax = axes[1]
ax.plot(z.index, z.discount, color=PAL["bad"], lw=2.2, marker="o", ms=3, label="discount per swap (₹)")
ax.plot(z.index, z.cm1, color=PAL["primary"], lw=2.2, marker="o", ms=3, label="CM1 per swap (₹)")
ax.axvline(pd.Timestamp("2024-11-01"), color="black", ls=":"); ax.legend(fontsize=8)
ax.set_title("ZipDrop: the Nov 2024 amendment cut ~₹11 per swap overnight")
save(fig, "09_partners")
zz = comp[comp.pid.isin(["FP-03", "FP-01"]) & comp.month.between("2024-09-01", "2024-12-01")]
zz = zz.pivot_table(index="month", columns="pid", values=["discount_inr", "amount_charged_inr", "cm1"], aggfunc="mean")
zz.columns = [f"{'ZipDrop' if p == 'FP-03' else 'FeastFly'} {m}" for m, p in zz.columns]
print("Oct -> Nov 2024 change in ZipDrop CM1 per swap:", round(zz.loc["2024-11-01", "ZipDrop cm1"] - zz.loc["2024-10-01", "ZipDrop cm1"], 2),
      "| FeastFly (control):", round(zz.loc["2024-11-01", "FeastFly cm1"] - zz.loc["2024-10-01", "FeastFly cm1"], 2))
zz.round(2)

# %% [markdown]
# ### Answer to Q5
# * **Base price rise (Jul 2024):** +₹5 per 2W swap with no detectable volume or retention penalty. It was the single best margin lever in the period, and battery wear absorbed it within two months.
# * **Peak/off-peak pilot:** statistically significant but modest demand shifting (~3 pp) and ~₹8 more revenue per exposed swap. **No reliability gain**, because it ran in the two least-congested cities. It affects segments unequally: independents and surcharge-billable partners respond; exempt partners do not.
# * **Partner terms decide partner value.** ZipDrop is the **largest partner by volume (549K swaps) but the least profitable 2W partner.** Its Nov 2024 amendment raised its discount from 12% to 28% (≈ ₹7.8 → ₹18.9 per swap). It is exempt from the peak surcharge while doing most of its swaps at peak (see `peak_share`), and it has the longest payment terms (45 days). Between October and November 2024 its revenue and CM1 per swap fell by **~₹11 overnight** (₹59.5 → ₹48.6), while FeastFly and Swiggle Go were flat. Its volume kept growing, so every extra ZipDrop swap now earns ~₹10 less contribution than a FeastFly swap before wear. After wear it is negative. The 3W cargo partners (CargoTuk, HaulKing) earn high revenue per swap but carry ~₹83 of wear, so they have the weakest after-wear margins.

# %% [markdown]
# ## 10. Core Question 6 — Root cause of new-rider churn
#
# **Definitions**
# * **New rider**: signed up on or after 1 Jan 2024 (so their whole history is observed), first attempt before 1 May 2025 (so a 60-day follow-up exists). n ≈ 13.8K.
# * **Retained**: at least one swap attempt in days 30–59 after the first attempt. **Churned** = did not come back in that window.
# * **Early-experience features** use only the first 14 days (before the outcome window), so they cannot be caused by the churn itself.

# %%
first = se.groupby("rider_id", observed=True).event_ts.min().rename("first_ts")
riders = rd.join(first, on="rider_id")
bad_lot_ids = set(bt.loc[bt.cohort == "Kyron KY-2407..09", "battery_id"])
ev = se[["rider_id", "event_ts", "event_id", "service_failure", "completed", "soh_out_pct", "km_valid", "amount_charged_inr", "tariff_code", "station_id",
         "queue_wait_sec", "battery_out_id"]].merge(riders[["rider_id", "first_ts"]], on="rider_id")
ev["d"] = (ev.event_ts - ev.first_ts).dt.days
new = riders[(riders.signup_date >= "2024-01-01") & (riders.first_ts < "2025-05-01")].copy()
ev = ev[ev.rider_id.isin(new.rider_id)]
new["retained"] = new.rider_id.isin(ev.loc[(ev.d >= 30) & (ev.d < 60), "rider_id"]).astype(int)

e14 = ev[ev.d < 14]
c14 = e14[e14.completed]
f = e14.groupby("rider_id", observed=True).agg(attempts_14d=("event_id", "size"), fail_rate_14d=("service_failure", "mean"))
f = f.join(c14.groupby("rider_id", observed=True).agg(soh_14d=("soh_out_pct", "mean"), km_per_swap_14d=("km_valid", "mean"), price_14d=("amount_charged_inr", "mean"),
                                                    bad_lot_share_14d=("battery_out_id", lambda s: s.astype(str).isin(bad_lot_ids).mean()),
                                                    peak_tariff_share_14d=("tariff_code", lambda s: (s == "PEAK").mean())))
f["first_attempt_failed"] = ev.sort_values("event_ts").groupby("rider_id", observed=True).service_failure.first().astype(int)
home = e14.groupby("rider_id", observed=True).station_id.agg(lambda s: s.astype(str).mode().iloc[0]).rename("home_station")
f = f.join(home)
new = new.merge(f, left_on="rider_id", right_index=True, how="left")
new = new.merge(st[["station_id", "charger_generation", "competitor_within_1_5km_since"]].rename(columns={"station_id": "home_station", "charger_generation": "home_station_gen"}),
                on="home_station", how="left")
new["competitor_nearby"] = (new.competitor_within_1_5km_since.notna() & (new.competitor_within_1_5km_since <= new.first_ts)).astype(int)
t30 = tk.merge(new[["rider_id", "first_ts"]], on="rider_id")
t30 = t30[(t30.created_ts >= t30.first_ts) & (t30.created_ts < t30.first_ts + pd.Timedelta(days=30))]
new = new.merge(t30.groupby("rider_id").size().rename("tickets_30d"), on="rider_id", how="left")
new["tickets_30d"] = new.tickets_30d.fillna(0)
promo = cx[cx.competitor_promo_active][["city", "date"]]
new["competitor_promo_days_30d"] = [((promo.city == c) & (promo.date >= t.normalize()) & (promo.date < t.normalize() + pd.Timedelta(days=30))).sum()
                                    for c, t in zip(new.home_city, new.first_ts)]
new["first_month"] = new.first_ts.dt.to_period("M").dt.to_timestamp()
print(f"New riders: {len(new):,} | 30-59 day retention: {new.retained.mean():.1%}")

# %%
coh = new.groupby("first_month").agg(riders=("rider_id", "size"), retention=("retained", "mean"), early_fail=("fail_rate_14d", "mean"), early_km=("km_per_swap_14d", "mean"))
fig, ax = plt.subplots(figsize=(13, 4))
ax.plot(coh.index, coh.retention, color=PAL["primary"], lw=2.5, marker="o", label="30–59 day retention (left)")
pct(ax, decimals=0); ax.set_ylabel("retention"); ax.set_ylim(.74, .93)
ax2 = ax.twinx(); ax2.bar(coh.index, coh.early_fail, width=18, color=PAL["bad"], alpha=.35, label="failure rate in first 14 days (right)")
pct(ax2, decimals=0); ax2.grid(False); ax2.set_ylim(0, .35)
ax.set_title("New-rider cohorts: retention falls exactly when early failures spike")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax.legend(h1 + h2, l1 + l2, loc="upper center", ncol=2, fontsize=8)
save(fig, "10_cohort_retention")
print("Correlation across monthly cohorts, retention vs early failure:", round(coh.retention.corr(coh.early_fail), 3))
coh.round(3)

# %%
def lift(col, bins=None, labels=None):
    g = new.groupby(pd.cut(new[col], bins, labels=labels) if bins is not None else new[col], observed=True)
    return g.agg(riders=("rider_id", "size"), retention=("retained", "mean"))


tables = {
    "Failure rate, first 14 days": lift("fail_rate_14d", [-.01, 0, .05, .1, .2, 1], ["0%", "0–5%", "5–10%", "10–20%", ">20%"]),
    "First attempt failed": lift("first_attempt_failed"),
    "km per swap, first 14 days": lift("km_per_swap_14d", [0, 45, 55, 65, 75, 500], ["<45", "45–55", "55–65", "65–75", ">75"]),
    "Vehicle class": lift("vehicle_class"), "Plan type": lift("plan_type"), "Signup channel": lift("signup_channel"),
    "Home station generation": lift("home_station_gen"), "Competitor within 1.5 km": lift("competitor_nearby"),
}
fig, axes = plt.subplots(2, 4, figsize=(18, 7), sharey=True)
for ax, (name, t) in zip(axes.flat, tables.items()):
    ax.bar(t.index.astype(str), t.retention, color=PAL["primary"]); ax.set_ylim(.6, .95); pct(ax, decimals=0)
    ax.axhline(new.retained.mean(), color=PAL["bad"], ls=":", lw=1)
    ax.set_title(name, fontsize=10); ax.tick_params(axis="x", rotation=30, labelsize=8)
    for i, (r, n) in enumerate(zip(t.retention, t.riders)):
        ax.text(i, r + .005, f"n={n:,}", ha="center", fontsize=7, color="#555")
fig.suptitle("30–59 day retention by early experience and rider attributes (dotted = overall)", fontweight="bold")
fig.tight_layout()
save(fig, "10_retention_lifts")

# %% [markdown]
# ### Multivariate model
# A logistic regression separates overlapping factors. For example, 3W riders both fail more *and* are a different business. Numeric features are standardised, so each coefficient is the change in log-odds of retention per one standard deviation. `attempts_14d` is included as an **engagement control**, not as a driver: riders who swap more early are mechanically more likely to still be around.

# %%
m = new.dropna(subset=["fail_rate_14d", "km_per_swap_14d", "soh_14d", "price_14d"]).copy()
num = ["fail_rate_14d", "km_per_swap_14d", "soh_14d", "bad_lot_share_14d", "price_14d", "peak_tariff_share_14d", "tickets_30d", "competitor_promo_days_30d", "attempts_14d"]
for c in num:
    m[c + "_z"] = (m[c] - m[c].mean()) / m[c].std()
formula = ("retained ~ " + " + ".join(c + "_z" for c in num) +
           " + first_attempt_failed + competitor_nearby + kyc_verified + C(vehicle_class) + C(plan_type, Treatment('partner_billed'))"
           " + C(signup_channel) + C(home_city, Treatment('Bengaluru')) + C(home_station_gen, Treatment('Gen2'))")
logit = smf.logit(formula, data=m).fit(disp=0)
res = logit.summary2().tables[1].rename(columns={"Coef.": "coef", "P>|z|": "p", "[0.025": "lo", "0.975]": "hi"})[["coef", "lo", "hi", "p"]]
res = res.drop("Intercept")
res["odds_ratio"] = np.exp(res.coef)
print(f"Pseudo R² = {logit.prsquared:.3f}, n = {int(logit.nobs):,}")
res.sort_values("coef").round(3)

# %%
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

feat_cols = num + ["first_attempt_failed", "competitor_nearby", "kyc_verified", "vehicle_class", "plan_type", "signup_channel", "home_city", "home_station_gen"]
X = pd.get_dummies(m[feat_cols], drop_first=False).astype(float)
Xtr, Xte, ytr, yte = train_test_split(X, m.retained, test_size=.3, random_state=7, stratify=m.retained)
gb = GradientBoostingClassifier(random_state=7, max_depth=3, n_estimators=250, learning_rate=.05).fit(Xtr, ytr)
print(f"Hold-out AUC: {roc_auc_score(yte, gb.predict_proba(Xte)[:, 1]):.3f}")
pi = permutation_importance(gb, Xte, yte, n_repeats=8, random_state=7, scoring="roc_auc")
imp = pd.Series(pi.importances_mean, X.columns)
groups = {c: c for c in num + ["first_attempt_failed", "competitor_nearby", "kyc_verified"]}
for c in X.columns:
    for g in ["vehicle_class", "plan_type", "signup_channel", "home_city", "home_station_gen"]:
        if c.startswith(g + "_"):
            groups[c] = g
imp = imp.groupby(imp.index.map(groups)).sum().sort_values()

fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))
show = res[~res.index.str.contains("attempts_14d")].sort_values("coef")
ax = axes[0]
ax.errorbar(show.coef, range(len(show)), xerr=[show.coef - show.lo, show.hi - show.coef], fmt="o",
            color=PAL["primary"], ecolor="#9aa5b1", capsize=2)
sig = show.p < .05
ax.scatter(show.coef[sig], np.arange(len(show))[sig.values], color=PAL["bad"], zorder=3, s=25)
ax.set_yticks(range(len(show))); ax.set_yticklabels(show.index.str.replace("C\\(|\\)|Treatment\\('.*?'\\)|, ", "", regex=True).str.replace("_z", " (per SD)"), fontsize=8)
ax.axvline(0, color="black", lw=.8); ax.set_title("Logistic regression: effect on log-odds of retention (red = p<0.05)")
ax = axes[1]
imp.drop("attempts_14d").plot.barh(ax=ax, color=PAL["accent"]); ax.set_title("Gradient boosting: permutation importance (hold-out AUC drop)")
fig.tight_layout()
save(fig, "10_drivers")
imp.sort_values(ascending=False).round(4)

# %% [markdown]
# ### Answer to Q6 — primary vs secondary drivers
#
# | Tier | Factor | Evidence |
# |---|---|---|
# | **Primary** | **Early service failure** (stockouts in the first 14 days) | Largest behavioural effect in both models (logit z-statistic ≈ −13; second in permutation importance after the engagement control). Retention falls from ~87% at 0% early failure to ~65% above 20%. A failed *first* attempt alone is associated with ~8 pp lower retention (78% vs 86%). In the model this is absorbed by the 14-day failure rate. Monthly cohort retention tracks the summer failure spikes almost exactly. |
# | **Primary** | **Delivered range** (km per swap in the first 14 days) | Second-largest behavioural effect (z-statistic ≈ +9). Riders getting <45 km per swap retain at ~80%. Its effect runs *through* range: bad-lot share and SoH lose significance once range is in the model. |
# | Secondary | Vehicle class (3W) | ~3 pp lower retention; strongly negative once failure is controlled, so 3W riders are also less sticky for other reasons (fewer 3W slots, fleet churn). |
# | Secondary | Home city (Delhi, Hyderabad, Jaipur, Pune vs Bengaluru) | Significant but smaller. It partly reflects heat and Gen1 exposure beyond the first 14 days. |
# | Secondary | Partner-billed plan | Partner-billed riders retain ~2.5 pp less than pay-as-you-go. Their stickiness depends on the employer contract. |
# | Minor | Peak-tariff exposure | Small negative effect, significant at p<0.01. Worth watching before any network-wide rollout. |
# | **Not a driver** | Competitor within 1.5 km, competitor promo days, signup channel, KYC, home-station generation *per se*, unresolved tickets | Not significant. Raising a ticket is *positively* associated with retention (an engaged rider), so ticket counts are not a churn signal. |
#
# **Bottom line:** new riders leave when the network fails them early, by being empty when they arrive or by handing them a pack that does not last the shift. Both trace back to the two operational causes found in Q2–Q4: Gen1 cabinets in the heat, and degraded (especially bad-lot Kyron) batteries.
