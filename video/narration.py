"""Narration for the 3-minute video: one entry per sentence, grouped into the script's four sections.

Spoken wording follows report/video_script.md, with small edits so a speech engine reads it naturally
("Gen 1" rather than "Gen1").
"""

SECTIONS = [
    ("The business problem", [
        "Over the last eighteen months, VoltRelay nearly tripled: completed swaps up 2.8 times, revenue up 3 times.",
        "But monthly service failures grew almost six times, new riders are not coming back, and after battery wear we still lose money on every swap.",
        "Before we commit the next budget, we need to know what is actually driving this.",
    ]),
    ("Our approach", [
        "We joined all eight datasets: 3.9 million swap attempts, plus hourly station telemetry, battery records, tickets and weather.",
        "First, we fixed the data: a firmware clock bug on 140 thousand events, test stations booking real revenue, and 21 spellings of six cities.",
        "Then we traced each symptom to its mechanism, and tested our conclusions with regression, a difference-in-differences on the pricing pilot, and a churn model.",
    ]),
    ("The most important insights", [
        "First: service failures are not a network-wide capacity problem. They are our oldest Gen 1 cabinets overheating.",
        "Above 40 degrees, a Gen 1 cabinet takes twice as long to charge, and is completely empty in 58 percent of hours. Gen 2 and Gen 3 are fine.",
        "Thirty-six of those cabinets sit in Delhi, Jaipur and Hyderabad, so every summer our failure rate triples in exactly those places.",
        "Second: margin erosion is a battery problem. Three Kyron lots delivered in mid-2024 wear out three times faster than everything else.",
        "They wiped out the July price increase within two months, cost about 45 million rupees in extra wear, and cut the range riders get per swap.",
        "Third: these two problems are why new riders leave.",
        "Riders who hit an empty cabinet or a short-range pack in their first two weeks are far less likely to return. Competitors, sign-up channel and KYC barely matter.",
    ]),
    ("Recommendations", [
        "On the four budget proposals: do not fund generic new stations. Upgrade or cool the 36 hot-city Gen 1 cabinets before next summer.",
        "Do not buy a bigger fleet: replace the bad Kyron lots, and claim the warranty.",
        "Keep peak pricing targeted at genuinely congested hubs, not network-wide.",
        "And do not sign an exclusive with ZipDrop. It is our largest partner but our least profitable one, so renegotiate its 28 percent discount and surcharge exemption instead.",
        "Finally, protect every new rider's first two weeks. That is where retention is won or lost.",
        "Thank you.",
    ]),
]
