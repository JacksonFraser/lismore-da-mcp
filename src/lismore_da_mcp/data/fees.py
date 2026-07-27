"""DA fee scale, EP&A Regulation 2021 Schedule 4.

Published for 2024-25 in documents/fees/nsw-planning-fees-2024-25.pdf (p2)."""

import math

# Fee calculation based on NSW EP&A Regulation Schedule 4
# EP&A Regulation 2021 Schedule 4, as published for 2024-25 in
# documents/fees/nsw-planning-fees-2024-25.pdf (p2). Each bracket is
# (upper bound of estimated cost, base fee, increment per $1,000 above the
# bracket floor). Bases are stepped, not continuous — that is how the schedule
# is written, so the fee jumps at each boundary.
DA_FEE_SCHEDULE_YEAR = "2024-25"

DA_FEE_BRACKETS = [
    (5_000,      144.00, 0.00,       0),
    (50_000,     220.00, 3.00,       5_000),
    (250_000,    459.00, 3.64,      50_000),
    (500_000,  1_509.00, 2.34,     250_000),
    (1_000_000, 2_272.00, 1.64,    500_000),
    (10_000_000, 3_404.00, 1.44, 1_000_000),
    (math.inf, 20_667.00, 1.19,  10_000_000),
]
