# Three-minute video script

**Rendered video:** [VoltRelay_3min_video.mp4](https://github.com/andringodson/Hackathon-DataAnalytics26/releases/download/video-v1/VoltRelay_3min_video.mp4), a narrated walkthrough of the live dashboard built from this script (see [`video/`](../video/README.md)).

Presented as if to VoltRelay's operations and customer-experience leadership. About 430 words, roughly 3 minutes at a natural pace. Suggested visuals in *italics*. All charts are in `report/figures/`.

---

### 1. The business problem (0:00 – 0:30)

*Visual: `05_network_trends.png`*

Over the last eighteen months VoltRelay nearly tripled: completed swaps up 2.8 times, revenue up 3 times. But monthly service failures grew almost six times, new riders are not coming back, and after battery wear we still lose money on every swap. Before we commit the next budget, we need to know what is actually driving this.

### 2. Our approach (0:30 – 1:00)

*Visual: cleaning summary table from the notebook*

We joined all eight datasets, 3.9 million swap attempts plus hourly station telemetry, battery records, tickets and weather. First we fixed the data: a firmware clock bug on 140 thousand events, test stations booking real revenue, and 21 spellings of six cities. Then we traced each symptom to its mechanism, and tested our conclusions with regression, a difference-in-differences on the pricing pilot, and a churn model.

### 3. The most important insights (1:00 – 2:10)

*Visual: `07_gen_heat_mechanism.png`*

First: service failures are not a network-wide capacity problem. They are our oldest Gen1 cabinets overheating. Above 40 degrees, a Gen1 cabinet takes twice as long to charge and is completely empty in 58 percent of hours. Gen2 and Gen3 are fine. Thirty-six of those cabinets sit in Delhi, Jaipur and Hyderabad, so every summer our failure rate triples in exactly those places.

*Visual: `08_lot_degradation.png`*

Second: margin erosion is a battery problem. Three Kyron lots delivered in mid-2024 wear out three times faster than everything else. They wiped out the July price increase within two months, cost about 45 million rupees in extra wear, and cut the range riders get per swap.

*Visual: `10_cohort_retention.png`*

Third: these two problems are why new riders leave. Riders who hit an empty cabinet or a short-range pack in their first two weeks are far less likely to return. Competitors, sign-up channel and KYC barely matter.

### 4. Recommendations (2:10 – 3:00)

*Visual: budget-decision table from the report*

On the four budget proposals: do not fund generic new stations. Upgrade or cool the 36 hot-city Gen1 cabinets before next summer. Do not buy a bigger fleet: replace the bad Kyron lots and claim the warranty. Keep peak pricing targeted at genuinely congested hubs, not network-wide. And do not sign an exclusive with ZipDrop. It is our largest partner but our least profitable one, so renegotiate its 28 percent discount and surcharge exemption instead.

Finally, protect every new rider's first two weeks. That is where retention is won or lost.

Thank you.
