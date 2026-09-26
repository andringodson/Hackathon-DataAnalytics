"""Narration for the 3-minute video, written to be spoken rather than read.

One entry per line, grouped into the script's four sections (report/video_script.md). Markup, stripped from captions:
  " | "   a breath (short pause)          " || "  a deliberate, dramatic pause
  "~"     at the start of a phrase: deliver it slower and lower, for emphasis
"""

SECTIONS = [
    ("The business problem", [
        "Over the last eighteen months, VoltRelay nearly tripled. | Completed swaps, up 2.8 times. | Revenue, up three times.",
        "But here's what worried us. || Service failures grew almost six-fold, | new riders weren't coming back, | and after battery wear, | ~we were still losing money on every single swap.",
        "So before we commit the next budget, | we need to know what's really driving this.",
    ]),
    ("Our approach", [
        "We brought all eight datasets together: | 3.9 million swap attempts, hourly station telemetry, battery records, support tickets, | even the weather.",
        "First, we fixed the data: | a firmware clock bug on 140 thousand events, | test stations booking real revenue, | and 21 spellings of six cities.",
        "Then we traced every symptom back to its mechanism, | and tested it properly: | regression, a difference-in-differences on the pricing pilot, and a churn model.",
    ]),
    ("The most important insights", [
        "First: | this is not a network-wide capacity problem. || ~It's our oldest Gen 1 cabinets, overheating.",
        "Above 40 degrees, a Gen 1 cabinet takes twice as long to charge, | and it's completely empty in 58 percent of hours. || Gen 2 and Gen 3? | They're fine.",
        "Thirty-six of those cabinets sit in Delhi, Jaipur and Hyderabad. | So every summer, our failure rate triples, | ~in exactly those places.",
        "Second: | the margin problem is a battery problem. | Three Kyron lots, delivered in mid-2024, wear out three times faster than everything else.",
        "They wiped out the July price increase within two months, | cost us around 45 million rupees in extra wear, | and cut the range our riders get from every swap.",
        "And third: || ~these two problems are exactly why new riders leave.",
        "When a rider hits an empty cabinet, or a short-range pack, in their first two weeks, | they're far less likely to come back. || Competitors, sign-up channel, KYC? | They barely matter.",
    ]),
    ("Recommendations", [
        "So, | on the four budget proposals. | Don't fund generic new stations. | Upgrade, or cool, the 36 hot-city Gen 1 cabinets, before next summer.",
        "Don't buy a bigger fleet. | Replace the bad Kyron lots, | and claim the warranty.",
        "Keep peak pricing targeted at the hubs that are genuinely congested, | not network-wide.",
        "And please, | don't sign an exclusive with ZipDrop. | It's our largest partner, but our least profitable one. | Renegotiate that 28 percent discount, and the surcharge exemption, instead.",
        "Finally: | protect every new rider's first two weeks. || ~That's where retention is won, or lost.",
        "~Thank you.",
    ]),
]


def caption(line):
    """The line as it should read on screen."""
    return " ".join(line.replace("||", " ").replace("|", " ").replace("~", "").split())
