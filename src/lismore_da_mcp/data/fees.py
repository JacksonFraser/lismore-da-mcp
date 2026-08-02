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
