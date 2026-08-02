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
| What will it cost me? | DA lodgement fee only, ~~2024-25 scale~~ → now 2026-27 (item 0.1) | ⚠️ still lodgement fee only |

The shape of that is worth stating plainly: **the retrieval half works well and the business half
is where it stops.** Zone, permissibility, parking and referrals are solid. The three things a
business actually needs to *act* — what to submit, what it costs, and a document that engages with
its site — are the three that fail.

---

# Phase 0 — Make the data trustworthy

Nothing else on this plan matters if the numbers are wrong. Each item is concrete and checkable,
and none needs a planner.

0.1 and 0.2 are done. 0.2 is the one to read: the zone tables came back **clean**, and the same
audit applied to parking found that **`data/parking.py` does not match the DCP** — which is now
0.3, and is the largest known correctness problem in the repo.

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

### 0.3 Correct the parking rates — **found by 0.2, not yet fixed**

The other half of 0.2 was DCP Chapter 7. **Those rates do not match the DCP.** The council document
is fine; `data/parking.py` is wrong. The values look written from general knowledge rather than
transcribed from Lismore's schedule.

Quoted verbatim from Chapter 7 Schedule 1, pp. 11–15:

| Use | DCP (correct) | `data/parking.py` (wrong) | Effect |
|---|---|---|---|
| Restaurant or cafe | "1 per 3 seats, plus 1 per 2 employees **or** 15 per 100m² GFA (whichever is greater)" | "1 per 10m² dining area" | 15/100m² = 1 per 6.67m². Understates ~33%, and omits the seats basis |
| Office premises | "1 per 30m² GFA for ground or 1st floor level and 1 per 40m² at subsequent upper levels. Minimum 2 spaces" | "1 per 40m² GFA" | Understates for ground/1st floor, where most small offices are; drops the minimum |
| Warehouse or distribution centre | "1 per 300m²" | "1 per 100m² GFA" | **Overstates 3×** — could kill a viable proposal |
| Industry (heavy, general, light) | "1 per 100m² GFA or part thereof. Minimum 2 spaces per unit or separate leased area" | "1 per 75m² GFA" | Overstates ~33% |
| Shop (individual) | "4.4 per 100m² GFA" | "1 per 25m² GFA" | 4.4/100 = 1 per 22.7m². Understates ~9% |
| Bulky goods premises | "≤400m² GFA – 3 per 100m²; >400m² – 2 per 100m²" | "1 per 50m² GFA" | Tiered in the DCP, flat here; wrong below 400m² |
| Gymnasium/fitness centre | "1 per 25m² GFA, plus 1 per 2 employees" | "1 per 25m² GFA" | Understates |
| Medical centre | "4 per practitioner, plus 1 per employee" | "4 per practitioner" | Understates |

`take_away` and `retail` have no entry under those names in the DCP schedule and are **unverified**
rather than presumed wrong.

The errors run both ways, and both directions cost a business. Understating means being told fewer
spaces are needed than Council will require — the DA comes back, weeks lost on a leased tenancy.
Overstating means abandoning a proposal that was actually viable. Parking is the flashpoint this
plan already identified as the recurring CBD argument.

**This is a schema change, not a value edit**, which is why it is its own item. Each entry is a
single rate string, so there is nowhere to put "whichever is greater", a rate that tiers by floor
area, or a per-unit minimum. `estimate_parking_requirement()` also parses that string with a regex,
so it can only ever read one basis. Doing this properly means:

- a rate model that carries alternative bases with a `max()` between them, size tiers, minimums,
  and a per-employee component
- an audit script for Chapter 7 in the shape of `audit_zone_tables.py`, so this cannot drift back
- checking the remaining ~20 entries in `PARKING_RATES`, not only the eight above
- keeping the existing honesty about area basis — the current caveat that the DCP rate may apply
  to a narrower area than GFA is right and should survive

---

### 0.4 Watch the council site instead of sampling it

0.1 fixed a stale fee scale; nothing stops the next one. Planning documents decay continuously —
DCP amendments, a reissued chapter, the July fee reset — and this repo currently learns about that
only when somebody happens to look. It went two years without anybody happening to look.

`fetch_council_documents.py` and `SCRAPER.md` make the check cheap now: re-crawl the planning and
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

# Phase 1 — Make the business path work end to end

The journey above breaks in three places. These are the three.

### 1.1 `get_da_checklist` refuses the words businesses use **[verified]**

```
change_of_use  → OK          change of use → REFUSED
commercial     → OK          cafe, restaurant, shop, office, fitout → REFUSED
```

The underlying data is fine — `change_of_use` and `commercial` checklists both exist. The tool
simply never got the vocabulary resolution that parking, definitions and the SEE sections received.
It is the one tool that work missed, and it lands on the single most common business DA type.

Wire it to `vocabulary.resolve()` with business synonyms, so a caller typing what a business would
say gets the checklist rather than a refusal.

Then check the checklist **contents** are right for a commercial change of use — a fit-out needs
things a dwelling does not (fire safety schedule, accessibility upgrade, trade waste, mechanical
ventilation for food) **[verify with planner]**.

### 1.2 The SEE draft ignores the site it is written for **[verified]**

For a café at 12 Keen Street — Lismore CBD, flood-affected, heritage conservation area — the draft
mentions flood **zero** times and heritage **zero** times. The residential draft mentions flood
once. The generator is effectively blind to where the site is.

Meanwhile `check_referrals` already knows: it returns flood as *"the defining constraint across
much of this LGA"*, with the exact documents required. **These two tools do not talk to each
other.**

A SEE that does not address flood on a CBD site is one Council will come back on, which is exactly
the delay this tool exists to prevent. Feed the constraints into the draft: take the address, run
the constraint lookup, and have the generator write the flood, heritage and bushfire sections with
the site's actual position — or, where it cannot, say plainly in the draft that the section needs
completing and why.

### 1.3 Treat "change of use" as a first-class case

Today `check_permissibility(land_use="change of use")` answers `likely_permitted_with_consent`
**[verified]**, which is a category error — a change of use is not a land use. The question a
business is asking is *"can this use go in this tenancy"*, which needs the **new** use checked, and
carries considerations a new building does not:

- whether consent is needed at all — some changes of use between similar commercial uses are
  exempt or complying under the Codes SEPP **[verify with planner]**
- existing use rights where the current use is no longer permissible **[verify with planner]**
- what the **previous** use means for contamination, when moving to a more sensitive use

---

# Phase 2 — The things that actually cause friction with Council

Phase 1 makes the path work. This is where the reported problem — businesses having trouble with
Council — most likely actually lives.

### 2.1 Answer "what will this cost me", not "what is the DA fee"

The lodgement fee is a fraction of it. A business also faces, variously: advertising/notification
fees, the long service levy above a threshold, Section 7.11 developer contributions (which for
commercial can dwarf the DA fee), Section 64 water and sewer headworks — significant for a food
premises — plus the Construction Certificate, inspections and an Occupation Certificate
**[verify with planner]** on every figure and threshold.

A business that budgets the DA fee and then meets a s7.11 contribution notice is exactly a business
having "issues with Council". Give them the whole number, with the parts named, or a clear
statement of which parts cannot be estimated without Council.

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
