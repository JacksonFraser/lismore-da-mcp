"""DA fee scale, EP&A Regulation 2021 Schedule 4.

Transcribed 2026-08-01 from `documents/fees/fees-and-charges-2026-27.pdf` p30,
the row group headed "Development Application (Lodgement Fee)", which states it
is "fixed by Schedule 4 Part 2 Item 2.1 of the EP & A Regulations".

**These fees are re-set every July.** The scale had been left on 2024-25 until
2026-08-01, by which point it had missed two resets and was quoting figures
about 6.5% low — a business budgeting from it would have been wrong on the one
number it came here for. `schedule_status()` below now says so in the tool's own
answer rather than relying on anybody noticing, and
`tests/test_fees.py::TestScheduleCurrency` fails if it falls two years behind
again.

Reading that page needs care, and the care is the point: it carries both a
"Year 25/26" and a "Year 26/27" column, but only the first row has a value in
each. Every other row has a single figure, and which column it belongs to is not
recoverable from extracted text. Two independent checks put it in 26/27:

  * by position — in the one two-value row, 25/26 sits at x≈465 and 26/27 at
    x≈530; every single value sits at x≈512–524, with 26/27.
  * by arithmetic — all seven brackets are ~6.5% above their 2024-25 values,
    i.e. two years of indexation, while the known 25/26 figure for the first
    bracket ($147.00) is only 2.1% above its 2024-25 one.

The per-$1,000 increments are fixed dollar amounts and did **not** change; only
the base fees are indexed. The bases are stepped rather than continuous, which
is how the schedule is written, so the fee jumps at each bracket boundary.
"""

import math
from datetime import date

DA_FEE_SCHEDULE_YEAR = "2026-27"

# (upper bound of estimated cost, base fee, increment per $1,000 above the
#  bracket floor, bracket floor)
DA_FEE_BRACKETS = [
    (5_000,          153.00, 0.00,          0),
    (50_000,         235.00, 3.00,      5_000),
    (250_000,        488.00, 3.64,     50_000),
    (500_000,      1_608.00, 2.34,    250_000),
    (1_000_000,    2_420.00, 1.64,    500_000),
    (10_000_000,   3_625.00, 1.44,  1_000_000),
    (math.inf,    22_009.00, 1.19, 10_000_000),
]

# Kept for the record, so the next refresh can sanity-check its own arithmetic
# the same way: every base should move by roughly one year of indexation.
PREVIOUS_SCHEDULES = {
    "2024-25": [144.00, 220.00, 459.00, 1_509.00, 2_272.00, 3_404.00, 20_667.00],
}


# ---------------------------------------------------------------------------
# The rest of what Council charges on a DA
#
# Added 2026-08-02 for PLAN.md item 2.1, from the same document (pp30-32). The
# brackets above answer "what is the DA lodgement fee"; a business asking "what
# will this cost me" also meets every charge below, and the first of them is a
# straight defect rather than an omission:
#
#   Schedule 4 item 2.7 sets a **flat fee for development that does not involve
#   building work** — no erection of a building, no carrying out of a work, no
#   subdivision, no demolition. That is a pure change of use, which is the
#   commonest business DA there is. Priced off the cost brackets above with a
#   $0 cost of works it returned $153; the fee is $395.
#
# Every figure here is from the "Year 26/27" column. Unlike p30 — where only the
# first row carries both years and the column had to be established by position
# and arithmetic (see the module docstring) — pp31-32 print both years on every
# row, so which column a figure belongs to is unambiguous.
# ---------------------------------------------------------------------------

# Schedule 4 Part 2 Item 2.7. Fees PDF p31.
DA_FEE_NO_BUILDING_WORK = 395.00

# Fees PDF p30. Applies below $100,000; above that the cost brackets apply.
DA_FEE_DWELLING_UNDER_100K = 631.00
DA_FEE_DWELLING_THRESHOLD = 100_000

# Fees PDF p32, "Information & Technology Service Charge": 0.1% of estimated
# cost, on every DA and CDC. Small proportionally, invisible in every discussion
# of DA fees, and charged on top.
IT_SERVICE_CHARGE_RATE = 0.001

# Fees PDF p32, "Advertising & Notification Fees for DA's/Modifications
# (Additional to DA Fees) - Community Engagement Strategy". Which tier applies is
# Council's call under its Community Participation Plan, so all are returned.
NOTIFICATION_FEES = {
    "expected": 365.00,
    "moderate": 537.00,
    "significant": 1_334.00,
    "designated_development": 1_334.00,
    "nominated_integrated_development": 537.00,
}

# Fees PDF p32, "Advertising of DAs - Prescribed Fees (Additional to DA Fees)",
# given under Schedule 4 Part 3 of the EP&A Regulation 2021. These are the
# statutory notice fees, separate from the engagement strategy fees above.
PRESCRIBED_NOTICE_FEES = {
    "designated_development": 3_078.00,
    "nominated_integrated_threatened_species_or_class_1_aquaculture": 1_532.00,
    "prohibited_development": 1_532.00,
    "other_development_requiring_notice": 1_532.00,
}

# Fees PDF p31. The per-input amount is charged for each approval body the
# application is referred to, so an integrated development touching two agencies
# pays it twice — which is why check_referrals matters to the budget.
INTEGRATED_DEVELOPMENT_FEE = {"processing": 194.00, "per_approval_body": 1_100.00}

DESIGNATED_DEVELOPMENT_FEE = 1_276.00
DESIGN_REVIEW_PANEL_FEE = 4_159.00

# Fees PDF p30. Not a lodgement cost — the cost of getting it wrong, which is
# the number worth showing a business up front.
AMENDED_PLAN_FEE_RATE = 0.30

# Charges that are real, that a business will meet, and that this repo holds no
# authoritative figure for. Named without numbers on purpose: a made-up figure
# in a budget is worse than a named unknown, and each of these has a source the
# applicant can go to directly.
UNQUANTIFIED_CHARGES = [
    {
        "charge": "Long service levy",
        "who": "Long Service Corporation (NSW), not Council",
        "when": "Building and construction work above a threshold, paid before the "
                "Construction Certificate is issued",
        "why_no_figure": "The rate and threshold are set by the Long Service Corporation "
                         "and are not in Council's fees and charges. Confirm both at "
                         "longservice.nsw.gov.au.",
    },
    {
        "charge": "Construction Certificate, inspections and Occupation Certificate",
        "who": "Council or a private certifier",
        "when": "After consent, before work starts and before the premises can be occupied",
        "why_no_figure": "A private certifier quotes its own fees; Council's are charged "
                         "per inspection at urban or rural rates.",
    },
    {
        "charge": "Section 68 approval (water, sewer, stormwater, on-site sewage)",
        "who": "Council, under the Local Government Act 1993",
        "when": "Commonly needed alongside a food premises fitout",
        "why_no_figure": "Charged per application ($570.50 urban / $597.50 rural in "
                         "2026-27) plus inspection fees that depend on the work.",
    },
]


def current_financial_year(today: date | None = None) -> str:
    """The NSW financial year as the fee schedules label it, e.g. '2026-27'."""
    today = today or date.today()
    start = today.year if today.month >= 7 else today.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def financial_years_behind(today: date | None = None) -> int:
    """How many July resets the transcribed scale has missed. 0 means current."""
    current_start = int(current_financial_year(today).split("-")[0])
    schedule_start = int(DA_FEE_SCHEDULE_YEAR.split("-")[0])
    return max(0, current_start - schedule_start)


def schedule_status(today: date | None = None) -> dict | None:
    """A warning to put in the answer when the scale is out of date, else None.

    A caveat printed on every answer is invisible; one that appears only when
    the figure is actually wrong is not. That distinction is why the two missed
    resets went unnoticed for a year — the standing caveat was already there,
    saying to confirm the figure, on every single response.
    """
    behind = financial_years_behind(today)
    if behind == 0:
        return None
    return {
        "status": "OUT OF DATE",
        "schedule_used": DA_FEE_SCHEDULE_YEAR,
        "current_financial_year": current_financial_year(today),
        "financial_years_behind": behind,
        "what_this_means": (
            f"This figure comes from the {DA_FEE_SCHEDULE_YEAR} scale, which is {behind} "
            f"July reset(s) behind. Statutory fees are indexed annually — historically "
            f"about 3% a year — so the real fee is likely higher than the number above. "
            "Do not budget from it. Get the current figure from Council or the NSW "
            "planning fees fact sheet."
        ),
    }
