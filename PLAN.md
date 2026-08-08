# Lismore DA Assistant — Plan

> **Written 2026-08-01. Supersedes `IMPROVEMENT_PLAN.md`**, which was a technical evaluation of the
> server as a piece of software. It is deleted, not archived — `git show 4ded0a8:IMPROVEMENT_PLAN.md`
> if you want it. That document did its job: 500 tests, CI, a module split, an address lookup, a
> search index. It is superseded because it kept generating *engineering* work, and the thing that
> now limits this tool is not engineering.
>
> Everything marked **[verified]** below was checked by running the tools on 2026-08-01, not by
> reading the code.
>
> **There is no planner to check with.** This project has no relationship with Lismore City
> Council and no line to a planning professional, so a note saying "verify with planner" is not a
> deferred task — it is a permanent one, and one that had started leaking into tool output as an
> unfinished sentence shown to applicants. Those markers were removed on 2026-08-02. The rule that
> replaces them: if a question cannot be settled from the documents in `documents/`, the tool says
> so plainly, says why, and points the applicant at Council's free Duty Planner — who they, unlike
> us, have every standing to ask. Declining out loud is a finished answer. A marker is not.

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

Nothing else on this plan matters if the numbers are wrong. Every item here is answerable from a
document in `documents/`, which is what makes it doable.

0.1 to 0.5 are done. The zone tables came back **clean**; the parking rates did not, and
0.3 is the one to read — most of the 22 entries were wrong, in both directions, on the numbers a
CBD assessment argues about. **0.5 is the one to read next**, because it found the same failure in
a file this phase had never looked at: the flood freeboard was wrong by 200mm and three of its
fields cited provisions that exist in no document here. One unaudited data file remains, `standards.py`
— item 0.6.

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

> **Follow-up, 2026-08-02.** The café rate was still being applied on the wrong reading, which this
> worked example hid. Schedule 1's wording does not say what "(whichever is greater)" governs, and
> the estimator took `max(seats + employees, GFA)` — under which the staff component vanishes
> entirely whenever the floor-area basis wins. It now takes `employees + max(seats, GFA)`: staff
> added, and the greater taken between the two measures of *customer capacity*, which are the two
> things it is meaningful to compare.
>
> The evidence is Tweed Shire Council's 2018 *Review of car parking requirements for small
> business*, which tabulates eight councils and cites this exact schedule — "Lismore City, Ref: DCP
> 2012 - Chapter 7 - Schedule 1" — splitting it into `Staff parking: 1/2 employees` and
> `Customer parking: 1/3 seats or 15/100m2 GFA whichever is greater`. Schedule 1's own
> drive-through entry is worded the same way, and unambiguously, because there the two customer
> measures sit adjacent.
>
> **The two readings agree on 80m²/40 seats/6 staff — both give 17** — which is why nothing caught
> it: that is the example used throughout this repo, in the README, and in
> `tests/test_business_path.py`. They diverge for a sparsely seated café in a large tenancy, where
> the old reading understated: 80m² with 20 seats and 6 staff was **12**, and is **15**.
> `TestTheCafeReading` now pins the divergent cases specifically, since the headline one cannot.
>
> This is an interpretation, not a transcription, so `note` on the entry discloses the ambiguity to
> the applicant rather than presenting the figure as settled. The verbatim `rate` string is
> untouched — the audit still checks it against the PDF.

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

### 0.4 Watch the council site instead of sampling it — ✅ **DONE 2026-08-02**

`scripts/verify_against_council.py`. The gap it closes is narrower than it sounds and worth naming
precisely: the three `audit_*.py` scripts check the transcribed data against the PDFs **in this
repository**, so a reissued chapter or an amended fee schedule would leave every audit green while
the server quoted superseded figures. Nothing checked the documents themselves.

Three passes: re-download every document with a recorded source URL and compare byte for byte;
re-verify every figure the server would quote against the *freshly downloaded* copy; crawl
Council's planning pages for PDFs the repo does not carry. It never writes to `documents/`.

**First run, 2026-08-02 — everything verifies.** All four source documents are byte-identical to
what Council publishes today, and all 80 figures still appear in them: 20 fee and charge figures,
41 Section 7.11 rates, 11 Section 64 charges, 25 parking requirements.

Three things that run turned up:

- **No current indexed Section 7.11 rate sheet exists.** The contributions page links the plan and
  nothing else, so "the plan's published rates, treat them as a floor, ask Council for the indexed
  figure" is the complete and correct position rather than a hedge.
- **Four current DCP chapters named in CLAUDE.md's own tables are not in `documents/`** — Part A
  chapters 6 and 16, Part B chapters 10 and 11. Not fetched; that is a separate decision.
- **A regular agent cannot read the council website at all.** `lismore.nsw.gov.au` returns 403 to
  plain HTTP, confirmed against three pages. Without a browser there is nothing to compare against,
  which is a large part of why this server is worth having.

The reporting needed as much care as the fetching. A first cut reported 48 of 59 crawled links as
"new", most of them chapters already held under Council's other naming convention — an audit nobody
would read twice. Matching on chapter identity (part, number, LEP edition) rather than filename,
and collapsing the LEP 2000 editions the repo declines by policy, brings it to **four** genuinely
absent documents. `KNOWN_NOT_CARRIED` records the ones already decided against, with reasons,
because "we looked and said no" is information and silence is not.

The matcher had a bug worth remembering: an underscore is a word character, so `part_b_chapter_1`
failed a `\b` lookahead, fell through to the Part A default, and matched Part B chapter 1 to the
Part A chapter 1 file. `tests/test_council_verification.py` pins it, along with the manifest naming
files that exist.

Still to do: run it on a schedule. Quarterly is probably right, and it should open an issue rather
than write a log line nobody reads.

<details><summary>The original plan for this item</summary>

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

</details>

### 0.5 Re-transcribe the flood controls — ✅ **DONE 2026-08-08**

**Phase 0 was declared done without ever reaching `data/flood.py` or `data/standards.py`.** Every
other data module got an audit — zones, parking, contributions, signage, approvals, timing,
readiness. These two are the oldest files in `data/`, they had no audit, and checking the first of
them against DCP Chapter 8 found it was not a transcription at all.

**The freeboard was wrong.** The file said the Flood Planning Level was "1% AEP + **500mm**
freeboard". §8.2 says the freeboard is **300mm**, and says it three times. A 200mm error is the
difference between a compliant slab and a non-compliant one, in the LGA that went 14m under in
2022, and `get_flood_requirements` returned it as the headline field.

Three more fields were unsourced rather than merely wrong. `"1% AEP"`, `"2090"`, `"13.4"` and
`"Exemption Precinct"` appear **zero times** in the chapter, zero times in LEP 2012, and nowhere
else in `documents/` — the chapter says "1 in 100 year ARI" throughout. A "CBD Development
Exemption Precinct" allowing shop-top housing above the PMF was being reported to applicants as a
Council provision. It is gone, along with its copy in `data/referrals.py`, which was attaching an
evacuation plan and a PMF refuge to a precinct that does not exist. `TestTheInventedProvisionsAreGone`
keeps all four out.

**Reading the chapter properly changed the shape of the tool, not just its numbers.**

- **The controls are per flood hazard area, and there are five** — Floodway (§8.4), High Flood Risk
  (§8.5), Flood Fringe (§8.6), Low Flood Risk (§8.7), plus CBD Flood Liable, which §8.3 gives the
  Flood Fringe's controls; rural land (§8.8) is separate again. They differ sharply: a commercial
  building in the High Flood Risk Area needs a **mezzanine refuge above the 1-in-500 year level**
  and one in the Flood Fringe does not, and Low Flood Risk has no controls at all. Answering
  "commercial" with one requirement was wrong four times out of five. The old data also gave the
  commercial answer as 25% of GFA alone, omitting the engineer's risk analysis and the mezzanine —
  both of which cost money and change a design.
- **§8.3 exempts a change of use from the commercial and industrial controls** in both the High
  Flood Risk and Flood Fringe areas. This is the most valuable sentence in the chapter for this
  repo's audience, and it inverts the answer: **a café taking over a CBD shop does not have to put
  25% of its floor area above the Flood Planning Level.** The old tool would have told it that it
  did. `is_change_of_use` selects it, and the exemption is stated *instead of* the requirements
  rather than beside them — with what it does **not** lift said plainly, since cl 5.21 and the
  building-work controls survive it.
- **The area is never inferred.** Map 1 is a bitmap on the chapter's last page. Same wall as the
  CBD parking boundary in item 2.2 and the contributions catchment in 2.1, same treatment:
  `flood_area` is an argument, and without it every area's controls come back with "none of these
  is your requirement yet". The zone is explicitly not a proxy — the areas are drawn on depth and
  velocity, and the CBD Flood Liable area is not the shape of the E2 zone.
- **The LEP is never omitted.** cl 5.21(2) is a *bar on granting consent*, not a standard to design
  to, so a proposal can meet every DCP figure and still fail it — and cl 5.21(3)(a) makes projected
  climate change mandatory to consider, which the DCP's levels (modelled 2001, mapped 2003 and
  2007) predate. cl 5.22 additionally reaches land between the flood planning area and the PMF for
  childcare, educational and tourist uses.

Two smaller finds worth their space: §8.6.4(2) exempts work **under $50,000** from the certificate
of structural adequacy and §8.5.4(2) does not, which is real money to a fitout; and §8.5.3 measures
its 25% against the 1-in-100 ARI level where §8.6.3 uses the Flood Planning Level. Both look like
drafting slips and both are carried as written rather than tidied.

`scripts/audit_flood.py` checks all 40 stored controls against the chapter and the LEP text. It
does two things a presence check alone cannot: it verifies the **derived constants agree with the
quotes they were read from**, so `FREEBOARD_MM` cannot drift from its own source sentence the way
the old figure had; and it **counts the numbered controls off the document** and reports any the
data does not carry, because three commercial requirements out of four reads as complete and is
not. Scoping that scan to §8.4 onward mattered — counting §8.1's objectives reported three
permanent false gaps, and an audit that always reports the same false gaps is one nobody reads
twice, which is item 0.1's lesson again.

CLAUDE.md and `QUICK_REFERENCE.md` both carried the 500mm figure and the invented precinct. Both
are corrected, and CLAUDE.md says what it used to say — it is loaded as context in every session
and would otherwise have the agent contradict its own tool, exactly as in item 2.5. The server
instructions gained a flood line and were held at the 4,200-character budget by compressing, which
is what the guard is for.

**Still open: `data/standards.py`, the other unaudited file.** It fails the same inspection — its
"0.9m side setback" is Chapter 1's *fence articulation recess*, its "4.5m front setback" is an
apartment separation figure, its "15% deep soil" is the chapter's *land steeper than 15%*, and its
80m² private open space carries a 5m minimum dimension where the table says 2.5m and applies only
to lots under 400m². Lower value than flood under the business reframing, since it is residential —
but `get_setback_requirements` states those figures with no hedge, and A1.4's **15m street setback
in RU1, R5 and E3** is a business-zone control sitting unread. That is item 0.6.

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

Two questions this could not settle, because no document in the repo answers them: whether a
**contribution in lieu of parking** applies in Lismore (item 2.2), and the s7.11 treatment of a
fitout that increases GFA within an existing tenancy. Both are named in the tool's output as
Duty Planner questions rather than guessed at.

> **Update, item 2.2 (2026-08-06):** the first of those is now half settled. DCP §7.7.3.3 does
> provide for a contribution in lieu of parking in the CBD — the provision was in the repo the
> whole time. Its *rate* remains unrecoverable, since the DCP points at the repealed Section 94
> and the current contributions plan has no car parking category, so it stays a Duty Planner
> question rather than a number.

### 2.2 Make parking a decision, not a number — ✅ **DONE 2026-08-06**

Reading the chapter first was the right instruction, and the suspicion behind it was correct.
Chapter 7 answers all three questions — and reading it turned up something none of them
anticipated.

**Schedule 1 is not the rate in the CBD.** §7.7.2 sets it as the minimum "for developments located
outside the Lismore CBD"; §7.7.3.1 replaces it inside the CBD with a flat **3.3 spaces/100m² GFA**
for all non-residential use. Nothing in the server knew the distinction existed, so every answer it
ever gave a CBD business used the wrong schedule — for exactly the businesses this repo is for. On
the standing 80m² café example:

| | spaces |
|---|---|
| Schedule 1, what the tool said | **14** |
| §7.7.3.1 fixed CBD rate | **3** |
| less the §7.7.3.4 deemed credit (80m² @ 2.5/100m²) | **1** |

"You are 14 spaces short, justify it" and "you owe one space, which you may be able to pay for" are
different proposals, and the first talks a viable business out of a tenancy. This is item 0.3
again: the numbers were nobody's guess, they were simply never read.

**All three of the things this item asked for are in the chapter**, none needed an outside answer:

- **Existing-use credit** — §7.7.3.4. A CBD site being redeveloped is deemed to have already
  provided parking at 2.5 spaces/100m² of existing GFA, *less* the spaces physically on the site.
  It is usually most of a change-of-use requirement and it is not automatic. If the site has
  evidence of a past cash-in-lieu payment for more, the greater figure applies, on the developer.
- **Contribution in lieu** — §7.7.3.3, "consolidated parking". This settles the question item 2.1
  left open: **yes, it exists**, in the CBD, and the component paid out is *also* reduced by 25%.
  The **rate is not recoverable**, though: the DCP cites the repealed Section 94 and a plan section
  (2.5.5) that does not exist in the current plan, and the Section 7.11 Plan 2024-2041 has no car
  parking contribution category at all. So it is named, sourced and explained — never estimated,
  the same treatment as Section 64.
- **Arguing a shortfall** — §7.5 lists the six criteria Council must consider, which is what a
  variation is actually argued against. Plus §7.7.3.2 shared parking (25% off, five conditions,
  applied *after* the credit), §7.7.3.1(iii)'s one-off 20%/40m² floor space allowance, and for a
  café the one that matters most: **unenclosed outdoor dining is not GFA and generates no
  requirement at all** (§7.7.3.1(ii)).

**The CBD boundary is never inferred.** Map 1 defines it and is a bitmap on the chapter's last page
with no extractable text. The E2 zone is close to that line but is not it. So `location` is an
argument, and without it the tool returns both figures and says plainly that neither is the answer
yet — the same discipline the contributions catchment follows, for the same reason.

`generate_see_draft` was carrying the same defect, which is the failure CLAUDE.md already names it
for. On an E2 site it now assesses **both** rates: it still refuses to report a shortfall as
adequate, but states the shortfall as a range and tells the applicant to settle Map 1 before
lodging. Deferring entirely would have given up the guarantee that matters more.

The audit was extended to presence-check all twelve §7.7.x provisions against the PDF, not just
Schedule 1 — and it immediately caught two of the new transcriptions where the wording had been
compressed.

### 2.3 Signage — ✅ **DONE 2026-08-06**

`get_signage_requirements` and `list_signage_types`, from DCP Chapter 9. Reading the chapter
reordered the tool before it was written.

**The answer is usually "you don't need an application".** §9.11 says it outright — "These
Environmental Planning Instruments provide for certain types of signage as Exempt or Complying
Development and the provisions of this DCP chapter are not applicable." The ordinary shopfront set
— wall, window, fascia, under-awning, top hamper — is Exempt Development, needing neither a DA nor
a CDC, provided it meets the SEPP's criteria. Projecting wall signs and pylon/directory boards are
Complying Development, so they take a CDC. So the tool leads with the **approval pathway**, then
the site prohibition, then the size standard. A size table first would answer a question most
businesses do not have and bury the one they do — the exemption is stated as conditional
throughout, because "no application needed" without "if it meets every criterion" is the harmful
simplification here.

**The A-frame is the trap, and it is worse than a size breach.** Portable footpath signs —
sandwich boards, A-frames — are *not permissible* unless they meet LEP 2012 Schedule 2. And §9.8
compounds it: the footpath is Council or RMS land, the landowner's agreement must be in the DA, and
"Council will not agree to the erection of signage in the road reserve for commercial development
other than signage attached to protrusions such as awnings". So it fails at owner's consent rather
than on the merits — earlier and more final — and the tool raises it unprompted. Nobody asks about
a "portable footpath sign", so the synonym table carries the words a business actually uses; the
café's other board, the chalkboard menu, is a *different* entry that must be affixed to private
property.

**Heritage, the refusal point this item named.** §9.2 prohibits advertising in a heritage area,
residential zone, conservation area, open space and waterways — but the exception is the half a
business needs: building and business identification signs are excepted. So a shop in a heritage
area or a home business in a residential zone can still put its name up; what it cannot have is
general advertising for someone who does not trade there. A prohibited result therefore says what
the business *can* still do rather than stopping at "no", and on a heritage site the §9.4
guidelines are reordered to lead with Character — the only guideline phrased as a prohibition
("no sign shall obstruct or block the view of any feature of historic architecture"). Heritage is
never inferred from the zone, and an unestablished heritage status is reported as unestablished
rather than as clear.

**A stale cross-reference, flagged not relied on.** The chapter cites SEPP 64 throughout; SEPP 64
was repealed and folded into SEPP (Industry and Employment) 2021 Chapter 3. No document in this
repo carries the current instrument, so that is returned as a pointer with an explicit "not
verified here" — a business searching "SEPP 64" today finds a repealed policy and may conclude the
control is gone. It has not.

`scripts/audit_signage.py` presence-checks all 24 sign types plus the general provisions, the
prohibited-zone list and the design guidelines, and reports any sign type §9.3 defines that the
data does not carry — which is how `business identification sign` and `building identification
sign`, the two the heritage exception turns on, were caught missing on the first pass.

**Housekeeping done in passing**, because it blocked this: the tool count was hardcoded in three
places and adding two tools failed two unrelated tests. `tests/test_registry.py` now asserts the
README's tool table equals `registered()` and that the stated total matches, instead of restating
a number.

### 2.4 Name the approvals that are not the DA — ✅ **DONE 2026-08-06**

`get_other_approvals` and `list_other_approvals`, covering fifteen approvals: trade waste, food
premises notification and registration, the food safety supervisor, food premises construction
standards, outdoor dining, liquor licensing, the CC, the Principal Certifier, the OC, the long
service levy, Section 68 water/sewer/stormwater, on-site sewage management, Section 138 road
reserve works, the annual fire safety statement and commercial waste.

The framing that makes it work is stated before the list: **development consent decides that the
use is allowed on the land, and nothing else.** It is not permission to build, connect a sink to
the sewer, serve food or alcohol, occupy the building, or put a table on the footpath. Two of these
— the CC and the OC — cannot even be applied for until the consent exists, so they sit *after* the
DA in the timeline rather than beside it, and the OC is the one that most often moves an opening
date. The result is grouped by **when** each approval happens rather than listed flat, because the
useful cut is "what must I do before I lodge" and "what can I not start until consent arrives".

**The selection rule is the inverse of the rest of the repo: over-list.** Everywhere else a
confident wrong answer is the danger and the tool declines. Here a wrongly included approval costs
a sentence of reading and a missing one costs weeks, so an unresolved trigger produces the approval
*plus* a question rather than an omission — every question names what was listed anyway. The one
exception is trade waste on an unsewered site, which is dropped: it is approval to discharge *to
the sewer*, so listing it there points at the wrong approval rather than merely an unnecessary one.

Two things the documents turned up that were not in the plan item:

- **Temporary footpath dining is fee-free and is not a Council application.** Under the NSW Outdoor
  Dining Policy 2019 you apply through Service NSW and "Council and state government agency fees
  will be waived". Council's schedule agrees — Tiers 1 and 2 read "Subject to NSW Outdoor Dining
  Policy" where Tiers 3 and 4, permanent structures, carry $85.25 and $113.65 per m² per year. The
  temporary/permanent line also reaches back into item 2.2: a permanent enclosure becomes gross
  floor area under DCP §7.7.3.1(ii) and generates a parking requirement that unenclosed dining does
  not.
- **Food premises registration stopped being free.** Every annual registration fee in Council's
  schedule was **$0.00** in 2025-26 and carries a real figure in 2026-27 — $607.50 for a small food
  business plus a $355 administrative assessment on a new application. A café budgeting from last
  year's schedule budgets nothing for this. The fee is waived where the application accompanies a
  DA, which is worth timing deliberately.

**Fees are quoted only from documents this repo carries**, cited by page, and everything set by a
state agency — the liquor licence, the long service levy — is named with no figure at all, the same
rule Section 64 follows. `scripts/audit_approvals.py` checks all 25 quoted figures still appear in
the source PDFs, which is the check that matters here because these go stale on a fixed annual
cycle.

The server instructions gained a step for this and blew their 4,000-character budget. The budget
was kept and the existing text compressed instead — the instructions ship in every session, so the
guard is doing its job.

### 2.5 Set expectations on time, and on what stops the clock — ✅ **DONE 2026-08-06**

`get_assessment_timeline`. **The only Phase 2 item whose source was not already in the repo** —
nothing under `documents/` said anything about assessment time, because the periods are set by
regulation rather than by Council. So the EP&A Regulation 2021 was fetched
(`scripts/fetch_epa_regulation.py`, Playwright, since legislation.nsw.gov.au 403s plain HTTP)
rather than written from memory, and it is now the first thing in `documents/legislation/`.

**Doing that immediately contradicted this repo's own knowledge base.** The item above, and
CLAUDE.md, both said *40 business days*. Section 91(4) says **"The assessment period is 40 days"** —
calendar days. The regulation uses "business days" in the two places it means them, so the
distinction is the drafter's and not an inference. Forty business days is about eight weeks; forty
calendar days is under six. CLAUDE.md is corrected and carries a note saying what it used to say,
since it is loaded as context in every session and would otherwise have the agent contradict its
own tool.

**The bigger correction is what the period is at all.** Section 91(1): the consent authority "is
taken to have refused" consent if it does not determine in time. That is a **deemed refusal — an
appeal right, not a delivery date.** Passing 40 days does not refuse the DA, does not invalidate
it, and does not oblige Council to stop assessing. Quoting the number and qualifying it afterwards
is how it became a delivery date in the first place, so the correction is the first field in the
response and the tool refuses to turn any period into a calendar date.

Three provisions do the real work of the item, and none are guessable:

- **s92(1): the clock starts at lodgement**, which is when the Portal completeness check passes and
  the fee is paid — not when the applicant presses submit. Days spent before that are simply lost,
  and they are the part most within the applicant's control.
- **s94(2)-(3): a request for information stops the clock, but only if made within 25 days of
  lodgement.** A request on day 30 does not stop it at all. This is the least-known provision in
  the area and it cuts both ways.
- **s39: a rejected DA is "taken never to have been made."** Not delayed — undone, starting again
  from zero, with the fee refunded in full (s254(1)) and a 14-day window for Council to do it.

Plus the trap in **s36(5)**: missing the deadline in an information request means you are *taken to
have notified* that you will not provide it, and the DA is determined on what is already there.
Silence is treated as a decision. And **s36(2)**, a genuine limit applicants do not know they have:
Council may not demand information at DA stage that belongs with the Construction Certificate.

The fetch script **refuses to write anything that does not contain the provisions being sought**,
which is what caught a wrong SL number returning a live 404 page on the first attempt — the same
failure that once put fifteen error pages into `documents/lep/`. `scripts/audit_timing.py` then
checks all 17 quotes against the fetched text; unlike the other audits it guards against *the law
changing*, not a transcription slipping.

**The instructions budget was raised, having been held twice.** Items 2.2 and 2.3 were absorbed by
compressing the surrounding text; 2.4 was too. This one would not fit without cutting something
load-bearing, so the 4,000-character guard moved to 4,200 with the reasoning recorded in the test.
The server had 21 tools when 4,000 was set and now has 28. Compress before raising it again.

---

# Phase 3 — Prevent the rejection before it happens — ✅ **DONE 2026-08-06**

`check_da_readiness` and `prepare_prelodgement_brief`. Both were written as this item described
them, and both were reshaped by reading the source rather than the plan.

### What reading the Regulation changed

The item said "completeness". The provision it turns out to be about is **s39 — rejection** — and
that had been in the repo since item 2.5 without anyone reading its subsections. Two things fall
out of them:

- **Every ground for rejection is administrative.** Illegible, unclear about the consent sought,
  missing a required document, an integrated-development approval not identified, a biodiversity
  report or species impact statement absent. Not one is about the merits. *That is why this phase
  is possible at all* — it is the only failure in the DA process a checklist can genuinely
  prevent, as against a refusal, which it cannot.
- **The window is 14 days, before assessment starts.** So the fortnight before lodgement is where
  this is cheap, and after lodgement the risk has already passed.

**The single most valuable finding is s25(b), which nothing in the plan item anticipated.** The
application must *list* the approvals the development needs under EP&A Act s4.46 — and s39(1)(d)
makes failing to list them a ground to reject. Applicants read that field as asking whether they
*have* the approvals, which is not what it asks, and leave it blank. The repo could already
produce the list: `get_other_approvals` has done so since item 2.4. Nothing had connected the two.
`check_da_readiness` now names the approvals to write into the field.

Three more the Regulation supplies and no Council document does: **s27(1)(a)** expires a BASIX
certificate at three months *for lodgement purposes*, so one obtained early and held while plans
were finalised is a document the applicant believes they have and does not; **s35B(2)** requires a
clause 4.6 request to accompany the application and states both limbs of the test, so a request
arguing only that the proposal is reasonable has answered half of it; and **s24(3)** confirms the
application is lodged on the day the fee is paid, which is what makes an incomplete lodgement cost
weeks rather than days.

### The design decision that took two attempts

The first cut emitted the s25 approvals list and the s39(1)(a) description-of-development
requirement as `rejection_risk` findings. They apply to every application, so **every proposal
ever checked came back "not ready"** — which is item 0.1's lesson exactly: a warning present on
every answer carries no information. They are `confirm_before_lodging` now, and `rejection_risk`
is reserved for something actually known to be wrong. The best verdict the tool can reach is
"nothing this tool can check is outstanding", which is deliberately a much smaller claim than
"ready": Council runs the completeness check, and two of its grounds — whether the description is
clear, whether the plans are legible at the scale printed — cannot be tested from here at all.

The document matcher needed the same care in the other direction. Reporting a document as missing
that the applicant has costs them a moment; reporting one as ready that they do not have costs them
the lodgement. So matching requires the head noun **and** the first word to agree — an earlier
version accepted "waste management plan" as "stormwater management plan", which share two words of
three and none of their content — words that matched nothing come back under `not_recognised`
rather than being dropped, and a match is reported as *"you listed this"*, never as verified.
Nothing here can open a file.

### The brief is the repository's refusals, collected

This is the half worth keeping. Every question in `DUTY_PLANNER_QUESTIONS` is a wall an earlier
item hit and correctly declined to guess past — the CBD boundary that is a bitmap (2.2), the
contributions catchment where rural retail is 20% dearer (2.1), the Section 64 charge whose plan
has no non-residential conversion table (2.1), the contribution-in-lieu rate that cites a repealed
Act (2.2), whether the change of use needs a DA at all (1.3). Those refusals were right and they
stay. What was missing is that each looked like a caveat on one answer, scattered across five
tools' outputs, and nobody assembled them into the one thing they are collectively good for:
**the agenda for the free fifteen minutes that can settle them.**

Fifteen minutes is a real constraint and it shapes the document. Questions are ordered by what
each costs to leave unresolved, not by topic — the first can remove the entire application, the
last changes a design decision. Five go in the session and the rest under "if there is time", so
the applicant chooses having been told the cost. And section 2 says what **not** to ask, built
from what was actually resolved rather than a fixed list: a session spent re-deriving the zone is
a session wasted, and a section claiming the zone is settled when no address was supplied would
waste it more surely than saying nothing.

If you add a tool that declines to answer something, add the question here too. Otherwise the
refusal is a dead end rather than a redirection.

### Done in passing

Four things moved rather than being copied, because the second copy is always the one that drifts:
`NOT_A_LAND_USE` from `tools/zoning.py` to `landuse.py` (a readiness check given "fitout" has the
same problem `check_permissibility` had), the referral characteristic map from inside the
`check_referrals` handler to `data/referrals.py`, `_site_constraints` from `tools/see.py` to
`readiness.py` (one implementation of the rule that the flood layer can confirm but never clear),
and the CBD location parser from `tools/parking.py` to `parking.py`.

`scripts/audit_readiness.py` checks all 13 quotes against the fetched regulation, reusing
`audit_timing.py`'s comparison, and reads the s39(1) paragraph letters off the source rather than
a hardcoded list — a list of five grounds out of six reads as complete and is not. The
instructions budget was held at 4,200 this time: the new step needed ~440 characters and they were
found by compressing, which is what the guard is for.

---

## Housekeeping

Small, non-urgent, and worth doing when next in the area rather than as a project.

- ~~**Derive the tool count instead of hardcoding it in three places.**~~ ✅ **DONE 2026-08-06**,
  in the course of item 2.3, which added two tools and was promptly failed by two unrelated tests —
  the fourth time this has caught a change. `tests/test_registry.py` now parses the README's tool
  tables and asserts they equal `registered()`, plus that the stated total agrees; the literal is
  gone from the `test_instructions.py` docstring. The README is the right thing to check against,
  because it is the part a human maintains.

## Deliberately not doing

- **Encoding SEPP pathways** from the SEPPs themselves. Getting it wrong means confidently telling
  a business a use is permitted when it is not — worse than the present gap, which errs toward
  "check with Council". The caveat on every refusal stays. This is not waiting on anyone: it is a
  judgement that the risk of a wrong "yes" outweighs the cost of a "we can't tell you", and it
  would only change if the SEPP text were in `documents/` and auditable the way the LEP tables are.
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
