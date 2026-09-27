---
description: Grade the tools against Council's real decisions on the DA Tracker, and grow the case set
argument-hint: "[grade | harvest | fetch <DA> | freeze <DA>]  (empty = the full loop)"
allowed-tools: Bash(.venv/bin/python scripts/validate_against_tracker.py:*), Read, Edit, Agent
---

Run the tracker validation loop — ROADMAP.md Phase T. If `$ARGUMENTS` names a mode, run just that
mode with `.venv/bin/python scripts/validate_against_tracker.py $ARGUMENTS` and report. With no
arguments, run the whole loop below.

## Why this exists

Every other check here is graded by us: the audits compare the data with documents we hold, and
the scenario suites are scored by whoever wrote them. This one is graded by Lismore City Council —
its Notices of Determination. The first run (2026-09-27, 21 business DAs) found a bug 1,346 tests
missed (T1), the Section 64 charge the repo never sized (T3), and Council practice no document
records (a Flood Evacuation Plan on 9 of 15 consents, T4). It is also the only evidence that the
figures are *right*, not just unchanged: Section 7.11 matched Council to the cent where the tool
answered.

## The loop

1. **Baseline.** `grade` on the existing cases in `tests/fixtures/tracker_cases.json`. Compare the
   summary with the last report in `tracker-cache/` (or ROADMAP.md Phase T's table if there is
   none). A verdict that got *worse* is a regression — stop and report it before anything else.
2. **Find new cases.** `harvest`. It lists business DAs lodged since 2024-07-01 that are not yet
   cases, marking the undetermined ones.
3. **Add them — use the `tracker-validator` agent** for more than two or three, since writing
   inputs means reading lodged documents:
   - determined → `fetch <DA...> --update`, then write `address`, `inputs` and `input_notes`;
   - undetermined → `fetch <DA...>`, write the inputs from the lodged documents, then
     **`freeze <DA...>`** so the tools' answer is recorded *before* Council decides. Frozen
     predictions are the most valuable cases in the file: they are the only ones graded without
     hindsight.
4. **Grade again** and report: the summary counts, what changed since the baseline, every FAIL,
   and any new *pattern* across cases (a condition Council keeps imposing, a charge the tools keep
   missing, a use they keep failing to recognise).
5. **Write findings down where they will be acted on.** A defect or gap → an item in ROADMAP.md
   Phase T with the DA numbers as evidence. A single notice showing how Council *reads* something →
   B1 (the interpretation register), not the data: one notice is an observation, not a rule.

## Rules

- **Inputs come from what the applicant knew at lodgement** — the tracker's description and the
  lodged documents. Never the consent. A figure worked back from Council's decision (the floor area
  implied by a contribution, say) is allowed only when nothing else exists, and must be marked
  `HINDSIGHT` in `input_notes`.
- **Never write a name, email or phone number into the case file**, and never stage
  `tracker-cache/` — notices carry applicants' personal details. The hook will block it; do not
  work around it. Cite DA numbers.
- **Do not change the tools to make a case pass** during this loop. Report; fixes are separate
  work, one ROADMAP item per branch.
- An address that will not resolve is a finding (ROADMAP.md T7), not something to paper over. Use
  `zone_override` only with a note saying where the zone came from.
- The tracker ignores date filters and caps results near 150, which is why `harvest` goes street
  by street. If it finds nothing new for a street you expected, add the street to
  `BUSINESS_STREETS` rather than widening the search.
