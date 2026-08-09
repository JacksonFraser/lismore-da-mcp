# Scenario Suite — 100 business situations

> **Written 2026-08-09.** The gap this closes: `PLAN.md` established that the *data* is verified
> against source documents, and that the server has never been used by a real business. Between
> those two facts sits everything this suite tests — whether the tools, **composed the way an
> applicant actually composes them**, produce an answer a business could act on.
>
> The audits check transcription. The 1,346 tests check behaviour unit by unit. Neither asks the
> question a café owner asks, which is never one tool wide.
>
> **This is a living document.** Status columns are filled in as batches run. A failing scenario is
> not a bug report — it is a candidate, and it earns its place on `ROADMAP.md` only if the failure
> would cost a business money, time or a rejection.

## How a scenario is judged

Most scenarios have no external ground truth — we have no planner and no Council relationship. So
verdicts rest on checks that do not need one:

| Check | What it catches |
|---|---|
| **Internal consistency** | Tool A contradicts tool B for the same situation (permissibility answers, parking refuses) |
| **Source grounding** | A cited clause, page or figure that is not in `documents/` |
| **Correct refusal** | Guessing where the source cannot settle it (flood area, CBD boundary, catchment) — *or* refusing where it can |
| **Silent wrongness** | A confident number with no signal that a reading was chosen |
| **Robustness** | Crash, traceback, or nonsense on input a real caller would send |
| **First contact** | A natural-phrasing call that fails before it starts |

**Verdicts:** `PASS` · `PARTIAL` (right answer, poor delivery) · `FAIL` · `BLOCKED` (could not run).

**Risk** is what a wrong answer costs the business: `HIGH` (money, rejection, or a wrong "yes"),
`MED` (delay or rework), `LOW` (friction).

---

## A. Change of use — the commonest business DA (15)

| ID | Status |
|---|---|
| CU-01 | ☐ |

### CU-01 — Shop becomes a café, CBD
**Asks:** "I'm taking over a vacant shop at 12 Keen Street and opening a café. What do I need?"
**Path:** `lookup_zone_by_address` → `check_permissibility` → `get_parking_rates(location=CBD)` → `calculate_da_fees(existing_use=shop)` → `get_flood_requirements(is_change_of_use=True)`
**Passes if:** contribution is **nil** (§2.7 charges only the increase); CBD fixed parking rate applied, not Schedule 1; flood §8.3 exemption surfaces.
**Fails if:** full contribution charged; Schedule 1 rate in the CBD; 25%-above-FPL demanded. **Risk: HIGH**

### CU-02 — Office becomes a café, CBD
**Asks:** same, but the tenancy was an office.
**Passes if:** contribution is charged on the increase (~$12,310 at 80m²), and the difference from CU-01 is explained rather than just different. **Risk: HIGH**

### CU-03 — Shop becomes a hairdresser
**Passes if:** permissibility and parking both answer. The LEP Dictionary names hairdressers inside `business premises` and Chapter 7 has that rate.
**Fails if:** permissibility answers and parking refuses (the known A2 asymmetry). **Risk: MED**

### CU-04 — Warehouse becomes a gym, E3
**Passes if:** permissibility resolves via the hierarchy; parking rate for a gym; the floor-area basis is stated. **Risk: MED**

### CU-05 — Café adds a liquor licence
**Passes if:** `get_other_approvals` names the liquor licence as **not** part of the DA, and says who issues it. **Risk: MED**

### CU-06 — Retail becomes a medical centre
**Passes if:** the parking rate jumps and the jump is visible; the LEP definition of `business premises` **excluding** medical centre is respected rather than folded in. **Risk: HIGH**

### CU-07 — Dwelling becomes a home business
**Passes if:** the home business / home occupation definitions are distinguished, and exempt-development possibility is raised before a DA is recommended. **Risk: MED**

### CU-08 — Shop becomes a takeaway food premises
**Passes if:** trade waste, grease trap and food premises registration all surface as separate approvals; waste management plan flagged. **Risk: MED**

### CU-09 — Industrial unit becomes a craft brewery
**Passes if:** the definitional ambiguity (light industry vs food and drink premises vs artisan food and drink industry) is *surfaced*, not silently resolved. **Risk: HIGH**

### CU-10 — Vacant tenancy becomes a childcare centre
**Passes if:** LEP cl 5.22 (sensitive development between flood planning area and PMF) is raised; centre-based child care definition includes out-of-school-hours care. **Risk: HIGH**

### CU-11 — Shop becomes a tattoo studio
**Passes if:** answers or refuses cleanly; if it resolves to a category, the derivation is shown. **Risk: LOW**

### CU-12 — Office becomes co-working
**Passes if:** treated as office/business premises without inventing a category. **Risk: LOW**

### CU-13 — Bank becomes a restaurant, likely heritage
**Passes if:** heritage is raised **and** something is said about what heritage requires — not only that a Heritage Impact Statement is needed. **Risk: HIGH** *(known gap — Phase C)*

### CU-14 — Change of use with no building work at all
**Asks:** "There's no construction. Do I still need a DA, and what's the fee on nothing?"
**Passes if:** the fee behaviour at nil/near-nil cost is coherent, and whether consent is needed at all is addressed. **Risk: MED**

### CU-15 — Change of use that also adds floor area
**Passes if:** §8.3's exemption is **not** extended to the added floor space — the DCP sends that to merit assessment. **Risk: HIGH**

---

## B. Fitout and building work (8)

### FO-01 — 80m² café fitout, $150,000
**Passes if:** fee, IT charge, contribution and the unquantifiable parts are separated; `budget_at_least` is not presented as the total. **Risk: HIGH**

### FO-02 — Fitout under $5,000
**Passes if:** the $153 floor applies and exempt/complying pathways are raised. **Risk: LOW**

### FO-03 — Fitout triggering BCA and access compliance
**Passes if:** access report and fire safety schedule appear in the checklist for a commercial fitout. **Risk: MED**

### FO-04 — Shopfront alteration in a heritage conservation area
**Passes if:** conservation-area status changes the answer, not just adds a warning. **Risk: HIGH**

### FO-05 — Adding a mezzanine
**Passes if:** floor area increase is recognised; flood implications of a mezzanine addressed (the High Flood Risk refuge control is *about* mezzanines). **Risk: MED**

### FO-06 — Kitchen extension to an existing restaurant
**Passes if:** parking is assessed on the *increase*, not the whole premises. **Risk: MED**

### FO-07 — New awning over the footpath
**Passes if:** DCP Ch 2 weather protection surfaces **and** the separate footpath/roads approval is named. **Risk: MED**

### FO-08 — External cool room and plant
**Passes if:** acoustic assessment raised where near residential. **Risk: MED**

---

## C. Signage (8)

### SG-01 — Shopfront business identification sign
**Passes if:** exempt development is checked **before** a DA is recommended. **Risk: MED** *(a wrongly-recommended DA is weeks and dollars)*

### SG-02 — A-frame sign on the footpath
**Passes if:** reported as generally **not** permissible on the footpath — the reverse of SG-01. **Risk: MED**

### SG-03 — Illuminated sign
**Passes if:** the illumination standards from Ch 9 are quoted, not summarised. **Risk: LOW**

### SG-04 — Sign on a heritage item
**Passes if:** the §9.2 heritage exception is applied, and turns on `business identification sign` / `building identification sign`. **Risk: HIGH**

### SG-05 — Pylon sign
**Passes if:** dimensional standards quoted with source. **Risk: LOW**

### SG-06 — Sign above the awning line
**Passes if:** answered or cleanly refused; no invented dimension. **Risk: MED**

### SG-07 — Window graphics covering most of the glazing
**Passes if:** CPTED / passive surveillance considerations surface, or a clean refusal. **Risk: LOW**

### SG-08 — Sign in a conservation area (not an item)
**Passes if:** distinguishes item from conservation area. **Risk: MED**

---

## D. Parking (10)

### PK-01 — 80m² café, CBD
**Passes if:** 3.3/100m² fixed rate → 3 spaces, with the Schedule 1 rate shown as *not applied* and why. **Risk: HIGH**

### PK-02 — 80m² café, outside the CBD
**Passes if:** Schedule 1 applies (~17), and the difference from PK-01 is explicable. **Risk: HIGH**

### PK-03 — Location not stated
**Passes if:** does **not** infer CBD from the zone; either asks or returns both. **Risk: HIGH**

### PK-04 — 200m² gym
**Passes if:** rate applied to the right floor-area basis. **Risk: MED**

### PK-05 — Medical centre
**Passes if:** per-consulting-room or GFA basis stated correctly. **Risk: MED**

### PK-06 — Shortfall of 6 spaces
**Passes if:** the DCP's named remedies appear, not just the deficit. **Risk: HIGH**

### PK-07 — Existing on-site spaces on a change of use
**Passes if:** existing spaces reduce the requirement, and the basis is stated. **Risk: HIGH**

### PK-08 — Barber
**Passes if:** resolves via `business premises`. **Risk: MED** *(known gap — A2)*

### PK-09 — Restaurant, 40 seats vs 150m² GFA
**Passes if:** the "(whichever is greater)" reading is applied *and* flagged as a reading. **Risk: HIGH**

### PK-10 — Shop top housing in the CBD
**Passes if:** no parking required. **Risk: MED**

---

## E. Flood (10)

### FL-01 — Flood area not stated
**Passes if:** returns all areas and declines to pick. Map 1 is a bitmap; the zone is not a proxy. **Risk: HIGH**

### FL-02 — Change of use, commercial, High Flood Risk
**Passes if:** §8.3 lifts the commercial controls. **Risk: HIGH** *(the commonest business DA in the flood-affected CBD)*

### FL-03 — New commercial build, High Flood Risk
**Passes if:** 25% GFA above FPL **plus** the mezzanine refuge above the 1-in-500 level. **Risk: HIGH**

### FL-04 — Commercial, Flood Fringe
**Passes if:** 25% GFA above FPL, **no** refuge requirement. **Risk: HIGH**

### FL-05 — Low Flood Risk Area
**Passes if:** reports that the chapter sets no controls there — rather than reaching for another area's. **Risk: MED**

### FL-06 — CBD Flood Liable
**Passes if:** §8.3 gives it the Flood Fringe controls. **Risk: HIGH**

### FL-07 — "What's the freeboard?"
**Passes if:** **300mm**. **Risk: HIGH** *(was wrong by 200mm until 2026-08-06)*

### FL-08 — ePlanning flood layer returns nothing
**Passes if:** reported as `unknown` with an explicit "this is not evidence the site is unaffected". The state layer holds **zero** features for the whole Lismore LGA.
**Fails if:** any wording suggesting the site is not flood affected. **Risk: HIGH** *(the CBD flooded in 2022)*

### FL-09 — $40,000 of work in the Flood Fringe
**Passes if:** the §8.6.4 structural-adequacy exemption under $50,000 applies, and the restumping carve-out is stated. **Risk: MED**

### FL-10 — Flood answer without the LEP
**Passes if:** cl 5.21(2) as a bar on consent, and cl 5.21(3)(a) climate change, accompany the DCP controls. **Risk: HIGH**

---

## F. Heritage (6) — expected weak, that is the point

### HE-01 — "My site is a heritage item. What can I do?"
**Passes if:** something beyond "you need a Heritage Impact Statement". **Risk: HIGH** *(known gap)*

### HE-02 — Site in a conservation area
**Passes if:** distinguishes item from area. **Risk: MED**

### HE-03 — Repainting in different colours
**Passes if:** identified as requiring consent. **Risk: MED**

### HE-04 — Timber windows to aluminium
**Passes if:** identified as an external change requiring consent. **Risk: MED**

### HE-05 — Heritage plus signage
**Passes if:** SG-04's §9.2 exception and heritage controls agree with each other. **Risk: MED**

### HE-06 — When is a Heritage Impact Statement required?
**Passes if:** the trigger is stated, not just the document name. **Risk: MED**

---

## G. Cost (10)

### CO-01 — Full cost, 80m² café change of use
**Passes if:** lodgement fee, IT charge, contribution, and `not_estimated` are all distinct. **Risk: HIGH**

### CO-02 — Catchment not stated
**Passes if:** the contribution is **left out of the total** rather than defaulted to urban. **Risk: HIGH**

### CO-03 — Rural vs urban catchment
**Passes if:** rural retail is ~20% above urban, and the figures reconcile. **Risk: HIGH**

### CO-04 — "What about water and sewer connection?"
**Passes if:** Section 64 is **named but not quantified**, with the reason (2016 dollars, no non-residential ET table). **Risk: HIGH**

### CO-05 — $250,000 of works
**Passes if:** $1,608 + $2.34/$1,000 over $250,000 → correct arithmetic on the 2026-27 scale. **Risk: MED**

### CO-06 — $12,000,000 of works
**Passes if:** top bracket applied correctly. **Risk: LOW**

### CO-07 — Fee schedule currency
**Passes if:** 2026-27 with no stale warning on 2026-08-09; the warning appears if the clock is moved forward two years. **Risk: HIGH**

### CO-08 — IT service charge
**Passes if:** 0.1% of development cost, on every DA. **Risk: LOW**

### CO-09 — Advertising and notification
**Passes if:** all tiers shown because Council chooses, not one picked. **Risk: MED**

### CO-10 — New build contribution vs change of use
**Passes if:** the increase-only rule visibly changes the number. **Risk: HIGH**

---

## H. Zoning and permissibility (10)

### ZO-01 — Café in E2
**Passes if:** permitted with consent, via `Commercial premises`. **Risk: LOW**

### ZO-02 — Business in Nimbin (RU5)
**Passes if:** RU5 table used; Part B Ch 6 Nimbin raised if relevant. **Risk: MED**

### ZO-03 — Manufacturing in E4
**Passes if:** E4 table used correctly. **Risk: LOW**

### ZO-04 — A prohibited use
**Passes if:** the SEPP caveat fires — `check_permissibility` reads the LEP table only and must not report a settled refusal. **Risk: HIGH**

### ZO-05 — A use absent from the table
**Passes if:** same caveat; no invented permissibility. **Risk: HIGH**

### ZO-06 — "It's zoned B3"
**Passes if:** redirected to **E2**; the B-series no longer exists. **Risk: MED**

### ZO-07 — RU4
**Passes if:** reported as not applying in Lismore. **Risk: MED**

### ZO-08 — C4
**Passes if:** reported as not applying in Lismore. **Risk: MED**

### ZO-09 — Secondary dwelling in a zone whose table omits it
**Passes if:** the Housing SEPP caveat fires. **Risk: HIGH**

### ZO-10 — Address on a zone boundary
**Passes if:** the point-query caveat appears — only the zone under the address point is returned. **Risk: HIGH**

---

## I. Timing, process and readiness (8)

### TM-01 — "How long will this take?"
**Passes if:** **40 calendar days**, framed as a deemed-refusal threshold, not a delivery date. **Risk: MED**

### TM-02 — Council asks for more information
**Passes if:** the 25-day limit on a clock-stopping request (s94(3)) is stated. **Risk: HIGH**

### TM-03 — Application rejected at lodgement
**Passes if:** s39, 14 days, taken never to have been made, fee refunded. **Risk: HIGH**

### TM-04 — Readiness check on a well-prepared proposal
**Passes if:** **never says "ready"** — the best verdict is that nothing checkable is outstanding. **Risk: MED**

### TM-05 — Readiness check listing documents by name
**Passes if:** words that matched nothing are reported rather than dropped; no document reported as *verified*. **Risk: HIGH**

### TM-06 — Pre-lodgement brief
**Passes if:** the Duty Planner questions are ranked by cost of leaving them unresolved, and already-answered questions are excluded. **Risk: MED**

### TM-07 — Integrated development timing
**Passes if:** 60 days, distinguished from the standard 40. **Risk: MED**

### TM-08 — "When does the clock start?"
**Passes if:** at lodgement — completeness check passed and fee paid — not at submission. **Risk: MED**

---

## J. Approvals that are not the DA (6)

### OA-01 — Food premises registration **Risk: MED**
### OA-02 — Footpath dining approval **Risk: MED**
### OA-03 — Trade waste agreement **Risk: MED**
### OA-04 — Liquor licence (not Council) **Risk: MED**
### OA-05 — CC and OC sequencing — cannot be applied for until consent exists **Risk: MED**
### OA-06 — s68 on-site sewage, unsewered site **Risk: MED**

Each passes if the approval is named, attributed to the right body, and placed correctly relative
to the DA in time.

---

## K. Robustness and adversarial (9)

### RB-01 — Natural-phrasing argument names
**Sends:** `floor_area`, `cost_of_works`, `zone`, `estimated_cost`.
**Passes if:** accepted or resolved. **Fails if:** refused. **Risk: HIGH** *(this is first contact — A1)*

### RB-02 — Empty string in a required argument
**Passes if:** refused, not defaulted. An empty `land_use` once returned "permitted without consent". **Risk: HIGH**

### RB-03 — Wrong type (string where a number belongs)
**Passes if:** a clean validation error, no raw `MCPError` or traceback text. **Risk: MED**

### RB-04 — Nonsense address
**Passes if:** `_verify_match` rejects it; no zone returned for a property that does not exist. **Risk: HIGH**

### RB-05 — Address outside the Lismore LGA
**Passes if:** does not silently answer with Lismore controls for a Byron or Ballina address. **Risk: HIGH**

### RB-06 — Unknown enum value
**Passes if:** refused with the accepted values listed. **Risk: LOW**

### RB-07 — Implausibly large floor area (e.g. 500,000m²)
**Passes if:** no overflow, no absurd unflagged figure. **Risk: LOW**

### RB-08 — Zero and negative numbers
**Passes if:** rejected or handled; no negative fee or negative parking requirement. **Risk: MED**

### RB-09 — Free text with markup or instructions in an address field
**Passes if:** echoed safely, no injection into the SEE output, no crash. **Risk: MED**

---

## Running a batch

```bash
.venv/bin/python -c "
import asyncio
from lismore_da_mcp.server import call_tool
print(asyncio.run(call_tool('get_parking_rates', {'development_type':'cafe','floor_area_sqm':80,'location':'CBD'}))[0].text)"
```

Record the **actual output**, not a summary of it. A scenario that passes on a reading of the code
and fails when run is the exact failure this suite exists to catch — two shipped bugs were visible
only to a real client.

---

# Results — run 1, 2026-08-09

All 100 scenarios run, 99 discrete verdicts (ZO-07/08 were judged jointly). Executed by 11 parallel
agents against the real server; every finding below was then **re-verified by hand against the
source documents** before being recorded here. Three agent claims did not survive that check and
are marked as corrected.

**Tally: 56 PASS · 28 PARTIAL · 15 FAIL**

## The one-line summary

**The data is not the problem. The layer that decides which stored fact applies is.**

Every audit passes. All 21 zone tables match the LEP verbatim. Every dollar figure traces to its
page. Not one invented figure was found — the failure mode that dominated Phase 0 is genuinely
gone. All 12 failures are in *selection, matching and application*, a layer no audit covers and
which `ROADMAP.md` did not name as a phase.

## Confirmed defects, ranked

### D1 — Singularisation cannot pair `-ies` with `-y`, and answers wrongly in both directions · **CRITICAL**
`landuse.py:40` — `re.sub(r"\b(\w{3,}?)s\b", r"\1", text)` strips a trailing `-s` only, so
`"Industries"` → `"industrie"` never meets `"industry"`. 40 land use table terms end in `-ies`.
Separately, `match_land_use(..., "hierarchy")` looks the *canonicalised* term up against the *raw*
`LAND_USE_HIERARCHY` keys, making the whole `premises` family unreachable.

Verified wrong **yes** (use falls through to the "any other development" catchall):
- `E1` + `industry` → `likely_permitted_with_consent`. LEP line 705, E1 item 4 **Prohibited**,
  contains `Industries` among its 48 terms.
- `E4` + `business premises` and `E4` + `hairdresser` → `likely_permitted_with_consent`. E4 item 4
  prohibits `Commercial premises`, and the LEP's own note makes business premises a type of it.
- `E2` + `industry` → `likely_permitted_with_consent`. E2 prohibits `Industries`.

Verified wrong **no**:
- `R2` + `home business` → `likely_prohibited`. R2 item 3 permits `Home businesses` with consent
  (31 terms, confirmed). **The same payload's `similar_uses` lists `"Home businesses"`** — it
  contradicts itself in one response, and contradicts `get_definition`.

The SEPP caveat (`scope_of_this_answer`) is gated to prohibited-shaped answers at
`tools/zoning.py:251`, so **every wrong "yes" ships entirely unhedged**. A wrong yes is a signed
lease; a wrong no talks a business out of something the LEP expressly permits, and nobody appeals
advice they never questioned. `data/definitions.py` already carries `land_use_table_term` for
exactly this problem and `landuse.py` never consults it.

**The cleanest demonstration, all four verified against LEP lines 745 and 747:**

| asked | tool answers | LEP says |
|---|---|---|
| `centre-based child care facility` | `likely_permitted_with_consent` (catchall) | **prohibited** in E4 (item 4) |
| `Centre-based child care facilities` | `prohibited` (exact) | prohibited ✓ |
| `light industry` | `likely_permitted_with_consent` (catchall) | permitted with consent ✓ *by accident* |
| `Light industries` | `permitted_with_consent` (exact) | permitted with consent ✓ |

**The same tool gives opposite answers for the singular and plural of one term**, and whether a
business gets the right answer is an accident of which form it typed. The catchall path also emits
a false statement of fact — *"'light industry' is not listed in the Zone E4 land use table"* — when
it is item 3, line 745.

*Agent-reported sweep of 115 wrong-yes / 75 wrong-no across 21 zones is not independently
re-derived — treat the count as indicative, the mechanism as confirmed.*

### D2 — `validate_arguments()` checks type but not domain · **CRITICAL**
`CLAUDE.md` already states this ("`_JSON_TYPES` covers the type keyword only"). The consequences
are now measured:
- `gross_floor_area_m2: -80` → `contribution: None`, `budget_at_least: 420.0`. With `+80`:
  `16081.24` / `16501.24`. **A sign flip silently deletes a $16,081 charge** — and `why_not` reads
  *"Supply gross_floor_area_m2 to get a figure"*, which the caller did.
- `development_cost: inf` → **uncaught `OverflowError`** at `fees.py:68`; `nan` → uncaught
  `UnboundLocalError`. `json.loads` accepts `Infinity`/`NaN`, so both are reachable over the wire.
  `-inf` returns `budget_at_least: -Infinity`, which is not valid JSON.
- `floor_area_sqm: -80` → `spaces_required: -12`. Negative page numbers mislabel real content.

One fix location, matching the repo's existing "one gate" design: domain constraints beside the
type check.

### D3 — A floor-area increase is charged nil contribution, unfixably · **HIGH**
`restaurant → restaurant, 100m² → 140m²` returns `contribution: {"urban": 28142.17}`,
`net_contribution: {"urban": 0.0}`, `budget_at_least: 862.80`, with `section_7_11_contributions`
listed under `what_that_covers` — i.e. settled, not omitted. The module assumes the previous use
occupies the same floor area as the proposal, and **accepts no argument to say otherwise**:
`existing_gross_floor_area_m2` returns `Unrecognised argument(s)`.

The contrast is the finding. The same module's stated rule is that **the catchment is never
assumed**, and without one the contribution is left *out of the total*. The existing floor area is
assumed silently, and puts **$0 into the total**. Estimated real charge ≈ $8,000.

### D4 — A mandatory requirement that is in neither the document cited nor the modality stated · **HIGH**
`readiness.py:431` and `tools/see.py:109` state *"A Heritage Impact Statement is required (DCP
Chapter 12)"*. Verified: Chapter 12 (21 pages) mentions "impact statement" **twice, both in
definitions, and requires nothing**. The real provision is LEP cl 5.10(5) and it is discretionary —
*"The consent authority **may** … require a **heritage management document**"* — of which a HIS is
one of three acceptable forms. Cost: a $2–5k consultant report presented as compulsory, with the
two cheaper alternatives hidden.

The repo is inconsistent here, which is the tell: `addresses.py:630` says *"likely to be required"*
and `signage.py:237` says *"may"*. The correct hedge exists in two modules and is missing from the
two that write documents Council reads.

Related, same clause: **cl 5.10(5)(c) reaches land "within the vicinity of"** a heritage item.
Every tool keys off the site's own flag and the lookup is a point query, so the business *next
door* gets a clean all-clear. `grep -rn "5\.10" src/` returns nothing — the heritage clause is
cited nowhere, including cl 5.10(10), the route by which a café opens in a heritage building in a
zone that would otherwise prohibit it.

### D5 — `lookup_site_constraints` has no LGA gate · **HIGH**
`1 Jonson Street, Byron Bay NSW 2481` returns a full constraints report with Lismore-specific
reasoning and **no out-of-area warning** (six phrasings checked, none present). Its sibling
`lookup_zone_by_address` refuses correctly with `lga: BYRON`. One of the two knows; the other does
not ask. *Corrected from the agent report: the flood layer does say `mapped_for_lismore: false`;
four other layers say `true`.*

### D6 — The signage fallback is biased toward "exempt" by construction · **HIGH**
`awning_sign_above` = **development consent required, 2.5m²**. `awning_sign_below` = **Exempt
Development, 2m²**. Five natural phrasings of the former fail to resolve, and **all eight
suggestions returned are exempt-pathway**, including the below-awning one. A business asking about
an above-awning sign is steered to "no application needed" for a sign that needs consent.
*Corrected from the agent report: the suggestion list is not identical across terms; it varies. All
entries being exempt is the sharper problem.*

### D7 — Confident numbers from inputs the schema cannot express · **HIGH**
`data/parking.py` recognises `practitioners, children, beds, rooms, dwellings, accommodation_units,
work_bays`; `get_parking_rates` exposes only `seats` and `num_employees`. So the *dominant term* of
many rates cannot be supplied and a confident integer still returns: medical centre, 5 employees →
**5 spaces**, against a rate of *"4 per practitioner, plus 1 per employee"* (real ≈ 17–18).
`"not counted: practitioners"` sits three levels down in `calculation.basis`. The safe behaviour
already exists — the tool omits `calculation` entirely when *no* countable is given — it just is
not triggered by a *partial* one.

### D8 — `shop top housing` is missing from the parking data · **HIGH**
DCP Schedule 1 p14: *"CBD (defined in Map 1) – No carparking requirements"*. The tool errors and
suggests `shop` (4.4/100m² GFA), telling a CBD business to build parking the DCP expressly does not
require. `CLAUDE.md` already states the correct fact. **`audit_parking_rates.py` reports "27
entries checked, 0 not matching" while this is absent** — its completeness check does not cover
this case, which revises the credit given to it in `ROADMAP.md`'s *What is already fine*.

### D9 — First contact fails 13 times in 14 · **HIGH (usability)**
Natural first guesses at argument names were refused by **13 of 14 tools; 19 of 20 attempts**.
Floor area is spelled three ways, address two, zone two, the use four. A caller who learns
`zone_code` is refused by `get_setback_requirements`; one who learns `floor_area_sqm` is refused by
`calculate_da_fees`. Every refusal returns `accepted_arguments`, so recovery costs one round trip —
but this is the only usability evidence the repo has, now measured rather than anecdotal.

### D10 — The fee schema recommends the under-quoting path · **MED**
`development_cost`'s own description says *"Use 0 for a change of use with no works"* → **$153**
(Item 2.1). The correct provision is Item 2.7, flat **$395**, already stored as
`DA_FEE_NO_BUILDING_WORK` but reachable only via the separate `involves_building_work=False`.
The schema recommends the path that under-quotes by $242 on the archetypal business DA.

### D11 — A deleted phantom is still live · **MED**
*"CBD exemption precinct"* survives at `data/readiness.py:239` and `tools/see.py:82`; confirmed
**absent** from Chapter 8's full text, and recorded in `CLAUDE.md` as invented and removed on
2026-08-06. It reaches the Duty Planner brief and SEE drafts Council reads.

### D12 — Smaller confirmed defects
- **Trade waste contradicts its own trigger.** `data/approvals.py:120` names *"butcher, hairdresser,
  mechanic or car wash"*; the approval attaches to the `food` activity only. `cafe` gets a real
  `approval` entry, `hairdresser`/`mechanic`/`car wash` get a passing mention in `advice`. MED
- **`check_da_readiness` prints a basis that contradicts its own number** — `"80m² at 15 per 100m²"`
  beside `spaces_required: 3` (`tools/readiness.py:129`, Schedule 1 basis emitted unconditionally
  even on the CBD reading). MED
- **Flood §8.6.4 exemption delivered wider than its constant.** The wire key is
  `all_development_controls_exemption`; the constant is `STRUCTURAL_ADEQUACY_EXEMPTION`, and only
  the structural certificate is exempt. MED
- **Flood area headline is commercial-only** and returned unchanged for industrial, where the body
  correctly includes a mezzanine the headline denies. MED
- **s39(1)(d) cited as applying to every application** when it reads *"for an application for
  integrated development"*. MED
- **Document matcher subset shortcut** (`readiness.py:216`) — bare `"management plan"` cleared both
  the Waste and Stormwater requirements. MED
- **`get_other_approvals` preamble contradicts its own CC entry** on whether a CC can be *applied
  for* before consent. The entry is right. MED
- **Three verified fee figures reach no output** — `PRESCRIBED_NOTICE_FEES`,
  `DESIGNATED_DEVELOPMENT_FEE`, `DESIGN_REVIEW_PANEL_FEE` have no consumer outside `data/fees.py`.
  One is a $1,532 notice fee, ~3× a small café's entire quoted total. MED
- **LEP cl 5.22 is unreachable on the natural path.** `get_flood_requirements(development_type=
  "childcare centre")` errors with only `[commercial, industrial, residential]` and no redirect,
  and `check_da_readiness` never raises 5.22 despite being told the use *and* that flood applies —
  though the definition limb (out-of-school-hours care at (a)(iii)) is correct. Sensitive
  development between the flood planning area and the PMF is exactly the case 5.22 exists for. MED
- **"Do I need a DA at all?" is never answered.** A shop→shop change returns the full 14-document
  "not ready" workup. No tool raises existing use rights or the point that the same defined term
  may need no consent. MED
- **`check_da_readiness` hardens a heritage "no" when given an address** — the point query returns
  `heritage: "no"`, dropping the conservation-area caveat the same tool supplies when given no
  address. More input produces a *less* hedged answer. MED
- **`available_flood_areas` omits `cbd_flood_liable`** from the error menu though the handler
  accepts it. LOW
- **Zone-not-found for RU4/C4/E5 reads as a data gap**, not the legal fact that the zone has no
  Lismore table. `list_zones` mis-groups `rural` (drops RU1–RU3) and `waterways` (drops W2). LOW

## What held up

Worth recording, because these were the things most likely to fail and did not:

- **FL-08, the most dangerous output this server can produce, is solid and survives composition.**
  A CBD address returns flood `answer: "unknown"`, `mapped_for_lismore: false`, *"This is not
  evidence the site is unaffected"* and *"Do not read this as 'not flood affected'"*. The token
  value differs from the other layers, so a machine consumer cannot conflate them, and
  `check_da_readiness` escalates rather than flattens it. No sentence anywhere reads as a clean
  bill of health.
- **No invented figures anywhere.** 300mm freeboard, 1.03m, 25%, the $50,000 threshold, every
  Chapter 9 quote including the chapter's own typos, all 17 dollar figures in `get_other_approvals`,
  Table E2 — all located in source. Phase 0's failure mode is gone.
- **`_verify_match` is the strongest control in the repo.** `99999 Keen Street` rejected with
  `closest_match_rejected: "387 Keen Street East Lismore 2480"`, `differs_by: "street number"`.
- **`check_da_readiness` never says "ready"**, and the document matcher reports unrecognised words
  rather than dropping them.
- **The refusals are principled**: no cash-in-lieu rate quoted against a repealed Act, Section 64
  named but not quantified, flood area never inferred, catchment never assumed.

## What this changes in ROADMAP.md

Phase A was built on the theory that the vocabulary layer *refuses when it could answer*. That is
true (D9, D8, D6) but it is the smaller half. It also **answers when it should refuse** (D1), and
**computes when it lacks the input** (D7, D3, D2). Those are correctness, not friction.

The re-rank: **D1 and D2 precede everything currently in Phase A**, D3/D4 join them, and the
content phases (C, D) move down — transcribing DCP Chapter 12 matters less than not asserting a
requirement Chapter 12 does not contain.
