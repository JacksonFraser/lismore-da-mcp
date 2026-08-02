# Lismore DA Assistant — Plan

> **Written 2026-08-01. Supersedes `IMPROVEMENT_PLAN.md`**, which was a technical evaluation of the
> server as a piece of software. It is deleted, not archived — `git show 4ded0a8:IMPROVEMENT_PLAN.md`
> if you want it. That document did its job: 500 tests, CI, a module split, an address lookup, a
> search index. It is superseded because it kept generating *engineering* work, and the thing that
> now limits this tool is not engineering.
>
> Everything marked **[verified]** below was checked by running the tools on 2026-08-01, not by
> reading the code. Claims about planning law rather than code are marked **[verify with planner]**.

## Who this is for

**Local businesses in the Lismore LGA going through a DA** — someone opening a café, a gym, a
workshop; an existing business changing use, fitting out, expanding, or adding signage. The
friction being addressed is between *businesses and Council*: applications that stall, get knocked
back, or come back with requests for information that cost weeks.

It is **not** primarily for householders. That matters, because the server was largely built as
though it were.

### What follows from that

A business applicant differs from a homeowner in ways that change what this tool should do:

- **Time is rent.** A homeowner waiting eight weeks is inconvenienced; a business paying rent on a
  tenancy it cannot open is losing money every week. Anything that prevents a delay is worth more
  than anything that produces a nicer document.
- **The most common business DA is a change of use**, not a building. Often no construction at all
  — a shop becoming a café. The whole assessment turns on use, parking, hours, waste and amenity.
- **They are in the zones this server knows least about** — E1, E2, E3, E4, MU1, and RU5 for the
  villages — while the residential standards, setback and SEE-form tooling all target R zones.
- **They get blindsided by adjacent approvals.** The DA is one of several permissions: trade waste,
  food premises registration, footpath dining, signage, a Construction Certificate. Businesses
  discover these one at a time, late.
- **They are disproportionately exposed to flood and heritage**, because the commercial centre is
  the flood-affected, heritage-listed part of the LGA.

## Where the server stands against that, today

Walked as a business would: *"I want to open a café in a vacant shop at 12 Keen Street, Lismore."*

| Step | Result | |
|---|---|---|
| Find the zone from the address | `E2 Commercial Centre` | ✅ **[verified]** |
| Is a café allowed there? | `permitted_with_consent` | ✅ **[verified]** |
| Parking required? | 8 spaces for 80m², DCP Ch 7 rate, with shortfall maths | ✅ **[verified]** |
| What referrals apply? | Flood and heritage correctly triggered, with the documents each needs | ✅ **[verified]** |
| What do I submit? | **Refused.** `change of use` is rejected; only `change_of_use` works | ❌ **[verified]** |
| Write the SEE | 8,394-character draft, correct structure | ⚠️ **[verified]** |
| …does the SEE mention flood, on a CBD site? | **No — zero mentions** | ❌ **[verified]** |
| What will it cost me? | ~~DA lodgement fee only~~ → fee, contributions and the parts that cannot be estimated (item 2.1) | ✅ |

The shape of that is worth stating plainly: **the retrieval half works well and the business half
is where it stops.** Zone, permissibility, parking and referrals are solid. The three things a
business actually needs to *act* — what to submit, what it costs, and a document that engages with
its site — are the three that fail.

> The table above is left as the record of what the walk-through found on 2026-08-01. All three of
> those have since been closed — the first two by Phase 1, the cost answer by item 2.1 — and the
> parking row now reads 17 spaces rather than 8, because item 0.3 found the rate itself was wrong.
> `tests/test_business_path.py` walks the whole journey, cost included, as one test.

---

# Phase 0 — Make the data trustworthy

Nothing else on this plan matters if the numbers are wrong. Each item is concrete and checkable,
and none needs a planner.

0.1, 0.2 and 0.3 are done. The zone tables came back **clean**; the parking rates did not, and
0.3 is the one to read — most of the 22 entries were wrong, in both directions, on the numbers a
CBD assessment argues about.

### 0.1 Refresh the fee schedule — ✅ **DONE 2026-08-01**

Was `DA_FEE_SCHEDULE_YEAR = "2024-25"`, having missed the July 2025 **and** July 2026 resets, and
quoting figures about 6.5% low on the one number a business comes here for.

Now on **2026-27**, transcribed from `documents/fees/fees-and-charges-2026-27.pdf` p30 — the row
group that states it is "fixed by Schedule 4 Part 2 Item 2.1 of the EP & A Regulations".

| Estimated cost | was (2024-25) | now (2026-27) |
|---|---|---|
| Up to $5,000 | $144 | **$153** |
| $5,001–$50,000 | $220 + $3.00/$1,000 | **$235** + $3.00/$1,000 |
| $50,001–$250,000 | $459 + $3.64/$1,000 | **$488** + $3.64/$1,000 |
| $250,001–$500,000 | $1,509 + $2.34/$1,000 | **$1,608** + $2.34/$1,000 |
| $500,001–$1m | $2,272 + $1.64/$1,000 | **$2,420** + $1.64/$1,000 |
| $1m–$10m | $3,404 + $1.44/$1,000 | **$3,625** + $1.44/$1,000 |
| Over $10m | $20,667 + $1.19/$1,000 | **$22,009** + $1.19/$1,000 |

Only the base fees are indexed; the per-$1,000 increments are fixed dollar amounts and did not
change. A $250,000 development now returns $1,216 (was $1,187).

**Reading that page needed care, and the care is the finding.** It carries both a "Year 25/26" and
a "Year 26/27" column, but only the first row has a value in each — every other row has a single
figure, and which column it belongs to is not recoverable from extracted text. Two independent
checks put it in 26/27: by position, the one two-value row places 25/26 at x≈465 and 26/27 at
x≈530, and every single value sits at x≈512–524; and by arithmetic, all seven brackets are ~6.5%
above their 2024-25 values (two years of indexation) while the known 25/26 figure is only 2.1%
above. Guessing here would have put a wrong number in front of a business.

**The reason it went stale is the more useful lesson.** A standing "confirm this figure" caveat was
already on every single answer while the scale sat two years out of date. A warning that is always
present carries no information. So `schedule_status()` now adds a loud, specific warning **only**
when the scale is actually behind — naming both years and the gap — and `TestScheduleCurrency`
fails once it is two years behind, with the fix written into the assertion message. One year of lag
is tolerated, because the new schedule is not always published the moment the year turns.

`calculate_da_fees` also now says plainly that the lodgement fee is not what approval costs, naming
the advertising fees, long service levy, Section 7.11 contributions, and Section 64 water and
wastewater charges a business should expect — the documents for which are now in the repo. Item 2.1
remains: turning that from a list into numbers.

### 0.2 Mechanically audit the transcriptions against the LEP text — ✅ **DONE 2026-08-02**

`scripts/audit_zone_tables.py` parses every zone land use table out of
`documents/lep/lep-2012-nsw-full.txt` and diffs it against `data/zones.py`, entry by entry across
permitted-without-consent, permitted-with-consent and prohibited.

**The zone tables are correct. All 21 match the LEP exactly, including every business zone.** That
is worth stating plainly, because the risk was real and unmeasured: the tests pinned that the data
had not *changed*, never that it was *right*, and the 21-zone list in `tests/test_tools.py` is
itself a second hand copy.

Three differences turned out to be defects in the **scraped source text**, not the transcription —
`lep-2012-nsw-full.txt` lost the semicolon between two land uses in three places, so
"Oyster aquaculture Research stations" reads as one invented use. They are listed explicitly in
`SOURCE_TEXT_DEFECTS` rather than absorbed by a heuristic, and the literal "Nil" that Zone C1
prints for an empty list is likewise named. An audit that always reports the same ten differences
teaches its reader to ignore it — the same failure that let the fee scale sit two years stale
behind a standing caveat.

`tests/test_zone_transcription.py` re-runs the comparison, so it holds against future edits to
either side, and includes tests that the audit *can* fail — a checker that cannot detect a fault
manufactures confidence rather than providing it.

### 0.3 Correct the parking rates — ✅ **DONE 2026-08-02**

`data/parking.py` did not match the DCP, and the errors were not marginal. Every one of the 22
entries has been re-transcribed from Chapter 7 Schedule 1 (pp. 11-15), and the file now carries
each requirement **verbatim** alongside the Schedule 1 land use name and page.

What was wrong:

| | DCP | was | |
|---|---|---|---|
| Restaurant or cafe | 1 per 3 seats + 1 per 2 employees, **or** 15 per 100m² GFA (greater) | "1 per 10m² dining area" | a basis appearing nowhere in Schedule 1 |
| Warehouse | 1 per 300m² | 1 per 100m² | **overstated 3×** |
| Dwelling house | 2 per dwelling (1 undercover) | 1 per dwelling, 2 if >125m² | that is the **dual occupancy** rule |
| Dual occupancy | 1 per dwelling <125m², 2 per dwelling >125m² | 1 per dwelling | tier lost |
| Office / business premises | 1 per 30m² ground/1st floor, 1 per 40m² above, min 2 | 1 per 40m² | understated where most offices are |
| Industry | 1 per 100m², min 2 per unit | 1 per 75m² | overstated |
| Shop (individual) | 4.4 per 100m² GFA | 1 per 25m² | |
| Bulky goods | 3 per 100m² ≤400m², 2 per 100m² above | flat 1 per 50m² | tier lost |
| Multi dwelling / flats | 1 / 1.5 / 2 per 1-, 2-, 3-bed + 1 per 5 visitor | 1 / 1.5 per 1-, 2+-bed + 1 per 4 | wrong tiers and ratio |
| Gym, medical centre | …plus the employees component | component omitted | understated |
| Take away, secondary dwelling | **not in Schedule 1** | confident rates | invented |

An 80m² café with 40 seats and 6 staff now returns **17 spaces**; the old data said 8. A business
acting on 8 would have had its DA come back.

The rate model changed to make this expressible. Each entry carries a structured `spec` supporting
added components, "whichever is greater" alternatives, tiers by floor area, and minimums — and
`spec` is **None** wherever the DCP assesses a use on merits, the rule needs an input the caller has
not given, or the use is not in the schedule. `estimate_spaces()` then shows the rule and declines
to produce a number. Declining is right more often than it looks here: a confident wrong space
count is what sends a DA back. The old estimator read the rate out of prose with a regex, so it
could only ever see one area-based component — the café rule was unreadable to it.

`scripts/audit_parking_rates.py` checks every stored requirement still appears in the PDF, and
`tests/test_parking_rates.py` runs the same check plus the specific corrections, so a regression
names the fault rather than showing a diff. All 25 sourced entries verify verbatim.

Schedule 1 is a three-column PDF table, so unlike the LEP's semicolon lists it cannot be diffed
structurally with confidence — hence verbatim storage plus a presence check rather than a parser
pretending to more precision than it has.

### 0.4 Watch the council site instead of sampling it

0.1 fixed a stale fee scale; nothing stops the next one. Planning documents decay continuously —
DCP amendments, a reissued chapter, the July fee reset — and this repo currently learns about that
only when somebody happens to look. It went two years without anybody happening to look.

`scripts/fetch_council_documents.py` and `SCRAPER.md` make the check cheap now: re-crawl the planning and
business sections, compare the published set against `documents/`, and report anything new, renamed
or changed in size. Run it on a schedule (quarterly is probably right; a `/loop` or a scheduled
cloud agent both work) and have it open an issue or a PR rather than a log line nobody reads.

Two cautions worth building in from the start. It must **not** auto-commit — every fetched file
still needs the checks in `SCRAPER.md` §8 and a human deciding whether it belongs. And the LEP 2000
trap means a "new" chapter may be a superseded one reissued at a new URL, so `/check-documents`
should gate anything the watcher proposes.

Note this is the *belt* to 0.1's *braces*: `TestScheduleCurrency` already fails when the fee scale
falls two years behind regardless of whether the watcher ever runs. Prefer that pattern — a check
that fails loudly in CI beats a job that has to be alive to be useful.

# Phase 1 — Make the business path work end to end — ✅ **DONE 2026-08-02**

The journey broke in three places. All three are fixed, and
`tests/test_business_path.py` walks the whole thing — address to lodgeable
answers — as one test.

### 1.1 `get_da_checklist` refuses the words businesses use — ✅ **DONE**

It was a chain of `if "commercial" in dev_type` substring tests, so
`"change_of_use" in "change of use"` was False and the most common business DA type was
refused. The checklists moved to `data/checklists.py` and the tool now uses the same
`vocabulary.resolve()` every other tool got in 3.1/3.2, with `CHECKLIST_SYNONYMS` covering how
businesses actually speak — *change of use, fitout, new tenancy, cafe, shop, office, hairdresser,
warehouse, signage, demolish*. `nuclear reactor` is still refused; the point was never to accept
everything.

The contents were thin too, so they now carry what businesses are caught by: BCA reclassification
and fire safety upgrade on a change of use, accessibility, waste, the parking assessment, and a
`commonly_missed` list naming the approvals that are **not** the DA — trade waste, Food Act
registration, footpath dining, and contamination on a move to a more sensitive use. Two new
checklists were added for signage and demolition, and `commercial` and `change_of_use` now point at
each other, since a new building and taking over a tenancy are different questions.

### 1.2 The SEE draft ignores the site it is written for — ✅ **DONE**

The draft mentioned flood **zero** times for a CBD café, because the flood and heritage blocks were
conditional on caller-asserted booleans that defaulted to nothing. `_site_constraints()` now
resolves them from the address via `lookup_constraints` when the caller has not asserted them, and
a Site Constraints block appears in section 2 saying how each was determined.

**Flood is now unconditional.** It always gets a section, and where it has not been established the
draft says so loudly rather than staying silent — because the state flood layer holds no Lismore
data and can never rule flooding out, and a SEE silent on flood in this LGA is one Council comes
back on. Constraints are tri-state (`True`/`False`/not established) because "we did not find it"
and "it is not there" are different sentences to put in a document going to Council.

The draft also used to assert *"No SEPPs preclude the granting of consent"* — a claim nothing had
checked, made on the applicant's behalf. It now names the SEPPs likely to be relevant and leaves
the assessment to be done.

### 1.3 Treat "change of use" as a first-class case — ✅ **DONE**

`check_permissibility(land_use="change of use")` returned `likely_permitted_with_consent` via the
table's catch-all — a confident answer to a question nobody asked. Process words (*change of use,
fitout, alterations and additions, renovation, demolition*) are now refused with an explanation of
why the land use table cannot answer them, what to ask instead, and the four things a change of use
carries that a new building does not: possible exempt/complying status under the Codes SEPP,
existing use rights, contamination on a move to a more sensitive use, and parking assessed against
the new use.

---

# Phase 2 — The things that actually cause friction with Council

Phase 1 makes the path work. This is where the reported problem — businesses having trouble with
Council — most likely actually lives.

### 2.1 Answer "what will this cost me", not "what is the DA fee" — ✅ **DONE 2026-08-02**

"Which for commercial can dwarf the DA fee" understated it. On an 80m² café fitout costing $50,000:

| | |
|---|---|
| DA lodgement fee | **$370** |
| Section 7.11 contribution, urban catchment | **$16,081** |

That is 43×, and it was invisible. `calculate_da_fees` now takes `development_type` and a floor
area and returns both, plus Council's 0.1% technology charge and notification fees, summed into
`budget_at_least` with `what_it_leaves_out` naming everything not in it.

**A defect fell out of reading the fee schedule properly.** Schedule 4 Item 2.7 sets a flat fee for
development *"not involving the erection of a building, the carrying out of a work, the subdivision
of land, or the demolition of a building or work"* — a pure change of use, the commonest business
DA there is. Priced off the cost brackets with a $0 cost of works it returned **$153**; the fee is
**$395**. `involves_building_work=False` selects it.

**The single most valuable thing here is section 2.7 of the contributions plan**, which nothing in
the original plan item anticipated. Contributions are charged on the *net increase in demand*, with
the contribution attributable to the existing lawful use discounted. So:

| Change of use, 80m², urban | contribution |
|---|---|
| shop → café | **nil** — both are retail premises |
| office → café | **$12,310** — 1.6 → 7 peak vehicle trips per 100m² |

Both answers are actionable and neither is guessable. The allowance is not automatic: it must be
evidenced with the DA, so the tool says to lodge proof of the previous use rather than argue it
after the consent is conditioned. Note the plan uses "credit" (section 2.8) for something else
entirely — negotiated works-in-kind — so the argument has to be made under the word "allowance" or
it goes to the wrong provision.

**What is deliberately not quantified.** Section 64 water and wastewater is real, is large for a
food premises, and **cannot be computed from anything in this repo**: the DSP rates are in 2016
dollars indexed annually, and it carries no table converting a non-residential use into equivalent
tenements — Council assesses that. The rates and service areas are returned so the charge can be
named and the applicant told to ask early, but no total is invented. Same for the long service
levy, which is a Long Service Corporation charge and is not in Council's schedule at all; it is
listed with its source rather than a made-up rate.

The catchment is also never guessed. Rates differ by catchment and for retail the **rural rate is
20% higher** than urban ($24,210 against $20,102 per 100m²), so a silent default to urban would
understate a village proposal. Without a stated catchment all three are returned and the
contribution is excluded from `budget_at_least` rather than being quietly picked.

**The audit is stronger than the other two transcriptions', because it could be.** Table E2 is
re-derivable from Table E1 — occupancy × per-head rates, plus PVTs × the traffic rate, plus the
4.5% administration loading — so `scripts/audit_contributions.py` rebuilds all 30 published cells
rather than only searching for them in the PDF. That catches a transposed digit, which a presence
check cannot. It also *found* something: **tourist and visitor accommodation in the rural catchments
is $212.68 below its own derivation**, exactly the Open Space and Recreation component that every
other rural row includes. Whether that is intentional is not recoverable from the document, so the
published figure is stored (it is what Council levies) and the gap is named in
`KNOWN_TABLE_DISCREPANCIES` rather than absorbed by widening the tolerance.

Two smaller things fixed in passing: the server instructions injected into **every** session still
read *"Fees are calculated from the 2024-25 statutory scale"* a year after 0.1 moved it to 2026-27,
with a test asserting the stale literal was present. The year is now interpolated from
`DA_FEE_SCHEDULE_YEAR` and the test asserts agreement rather than a copy. The README's worked
examples were also still quoting the pre-0.3 parking rate and a 2024-25 fee.

Still open, and needing a planner rather than a document: whether a **contribution in lieu of
parking** applies in Lismore (item 2.2), and the s7.11 treatment of a fitout that increases GFA
within an existing tenancy.

### 2.2 Make parking a decision, not a number

`get_parking_rates` computes the requirement and any shortfall **[verified]**. For a CBD business
the shortfall is usually the whole argument: an existing tenancy has no on-site parking and cannot
grow any. What a business needs next is what to *do* about it — the existing-use credit for parking
already attributable to the previous use, whether a contribution in lieu applies, and how to argue
a shortfall in the SEE **[verify with planner]**.

### 2.3 Signage

Almost every business needs it; it is DCP Chapter 9; there is no tool. Signage on a heritage item
or in a conservation area is a common refusal point in a CBD.

### 2.4 Name the approvals that are not the DA

Trade waste, food premises registration, footpath/outdoor dining, liquor licensing, the
Construction Certificate, the Occupation Certificate. These are separate from the DA and are where
businesses get caught. Even a plain "here is what else you will need and who issues it" is
disproportionately useful, and cheap to provide.

### 2.5 Set expectations on time, and on what stops the clock

40 business days is the headline, but a request for information pauses it, and an incomplete
lodgement never starts it. A business planning a fit-out around an assumed date needs to know which
of its own omissions will cost it weeks.

---

# Phase 3 — Prevent the rejection before it happens

Once the above is in place, the highest-value thing left is **completeness**: check a proposal
against the checklist, the constraints and the referrals, and tell the applicant what is missing
*before* lodgement. That is the difference between a DA that runs 40 days and one that runs four
months.

A pre-lodgement brief is the natural companion — Council offers a free duty planner (Tuesdays and
Thursdays) and pre-lodgement meetings, and a business that walks in with the right questions
already framed gets far more out of them.

---

## Housekeeping

Small, non-urgent, and worth doing when next in the area rather than as a project.

- **Derive the tool count instead of hardcoding it in three places.** It currently appears in
  `README.md`, `tests/test_registry.py` and a docstring in `tests/test_instructions.py`, so adding
  a tool means editing three unrelated files and CI fails on the two you forget. It caught out three
  separate changes on 2026-08-01 alone. The registry already knows how many tools there are —
  assert the README table matches `registered()` rather than restating the number, and drop it from
  the docstring.

## Deliberately not doing

- **Encoding SEPP pathways** without a planner. Getting it wrong means confidently telling a
  business a use is permitted when it is not — worse than the present gap, which errs toward
  "check with Council". The caveat on every refusal stays.
- **Predicting whether Council will approve something.** The tool should make an application
  complete and well-argued; it should not imply an outcome.
- **More transport, dispatch or SDK work** unless something is broken. That is where the previous
  plan kept leading, and it is not what limits this tool.

## Open questions

1. **Is anyone using the public server?** It has had structured logging since 5.1 and nobody has
   read it. If real businesses are connecting, their questions are the best possible input to this
   plan, and worth more than everything above. If they are not, then distribution — getting it in
   front of businesses, perhaps via Council or the chamber of commerce — matters more than any
   feature here.
2. **Which businesses, and what actually went wrong for them?** "Issues with DAs and the council"
   covers refusals, delays, RFIs, cost surprises and confusion, and they need different fixes. Two
   or three real cases would sharpen this plan more than any amount of code reading.
3. **Is there an appetite to work with Council directly?** Much of the friction above is Council's
   to fix, and a tool that Council recognises is a very different proposition to one it does not.
