# Lismore DA Assistant — Roadmap

> **Written 2026-08-09.** This does **not** supersede `PLAN.md`, which is the record of Phases 0–3
> and the reasoning behind them. `CLAUDE.md` cites that document's item numbers as the *why* for
> rules that are still load-bearing ("item 0.3", "item 2.1", "the same failure as item 0.1"), so
> deleting it would strand those references. `PLAN.md` is the past; this is the next.
>
> Everything marked **[verified 2026-08-09]** was checked by running the code, the tests or the
> audits on that date — not by reading prose about it. Three things this document was going to
> assert turned out to be false when checked, and they are recorded in *What is already fine* below
> rather than quietly dropped, because a roadmap that lists non-problems wastes the same time twice.

---

## Where this starts from

`PLAN.md`'s open question 1 answered itself: in seven days of logs the public server took 30 tool
calls and **every one was ours**. The conclusion drawn there — *distribution now matters more than
any feature here* — is correct, and this document accepts it rather than relitigating it.

But it needs one refinement, and the refinement changes the work:

**The user of this server is a Claude session, not a business.** A café owner in Lismore does not
connect an MCP server. What reaches them is either (a) a Claude conversation with this server
attached, (b) a person helping them who ran it, or (c) a piece of paper that came out of it. In
every one of those, a model — not a human — is choosing tool names and argument names.

That collapses two things `PLAN.md` treats as separate. **"Distribution" and "the caller gets the
arguments wrong" are the same problem.** The only usability evidence this repository has ever had
is three `invalid_arguments` results in an 18-second span, which item 1 of Phase A below fixes, and
which reproduced on the first natural-phrasing attempt on 2026-08-09 **[verified]**. Every hour
spent making the first three calls succeed is distribution work, and it is the only distribution
work that can be done from inside this repo.

The rest of distribution cannot. It is in the *Distribution* track near the end, it is mostly not
code, and it needs a decision that is not ours to make.

### What run 1 of the scenario suite changed — read this before the ordering below

**Added 2026-08-09.** The paragraphs above were written before anything had been tested end to end.
Building `SCENARIOS.md` and running its 100 scenarios (**56 PASS · 28 PARTIAL · 15 FAIL**) did not
overturn the reasoning about *distribution*, but it did overturn the ordering, because it found a
problem this document did not know existed.

The friction thesis above is half right. The vocabulary layer does refuse when it could answer —
and it **also answers when it should refuse**. A prohibited use is reported as permitted, unhedged;
a sign flip silently deletes a $16,081 charge. Those are correctness, not friction, and **Phase S
below now precedes Phase A**.

One consequence that follows directly, and matters for sequencing: **the argument-name friction is
currently acting as a brake.** Every refused call is a wrong answer not delivered. Fixing A1 before
Phase S would raise the rate of confidently wrong answers, so the convenience work waits on the
correctness work. Do not remove the brake first.

`SCENARIOS-2.md` holds a second suite of 200 scenarios, built from what run 1 learned and
deliberately not yet run. Suite 1 stays as the regression suite.

---

## What is already fine — do not spend time here

Checked on 2026-08-09 because this roadmap was about to propose fixing them:

- **The audits do run in CI.** `.github/workflows/tests.yml` runs only `pytest` and
  `check_documents.py`, which looks like the ten audit scripts are unwired. They are not: the test
  modules import the audit modules and re-run their comparisons (`from audit_flood import
  chapter_text`, `from audit_parking_rates import schedule_text`, and so on for all ten). The
  guardrail is connected. **[verified]**
- ~~**`audit_parking_rates.py` already checks completeness**~~ — **withdrawn 2026-08-09.** Its
  docstring says it "also reports Schedule 1 land uses with no entry here", and on that basis this
  entry credited it. Running the scenarios found `shop top housing` — Schedule 1 p14, *"CBD
  (defined in Map 1) – No carparking requirements"* — absent from `data/parking.py` while the audit
  reports "27 entries checked, 0 not matching". The completeness check does not cover this case.
  Reading a docstring is not verifying a claim, which is the same mistake this section exists to
  prevent. **[corrected]** — and on 2026-08-20 it turned out to be worse than "does not cover this
  case": **there was no completeness check at all**, only a docstring describing one. S5 wrote it.
- **Fee staleness degrades loudly, not silently.** `schedule_status()` returns an "OUT OF DATE / do
  not budget from it" block the moment the scale is one July behind; the test fails at two. The
  one-year tolerance is deliberate and documented. **[verified]**
- **`prepare_prelodgement_brief` already composes the whole walk** from `proposed_use` alone. It
  does not need building. It needs *finding* — see A3. **[verified]**
- **The SEE draft is honest about being a scaffold**: 17 bracketed placeholders and explicit notes
  to the applicant, and it now engages with the site (9 flood, 6 heritage, 5 bushfire mentions for
  a CBD address). **[verified]**

---

## The decision this roadmap cannot make

**What shape should reach a business?** The work below is worth doing on any answer, so it is not
blocking — but the answer changes what comes after Phase D, and only a human can give it.

1. **Stay an MCP server.** Cheapest. Accepts that the audience is people who already use Claude
   with connectors, which is not "a café owner in Lismore" but might be whoever advises them.
2. **Make the paper the product.** `prepare_prelodgement_brief` already returns plain text designed
   to be printed and carried to Council's free Duty Planner session. That artifact reaches someone
   who has never heard of MCP. A thin public page that runs the walk and hands back the brief would
   put it in reach of any business with a browser — at the cost of a build this repo has twice
   decided not to do, plus a privacy surface (see A4 and *Deliberately not doing*).
3. **Go through an institution.** Council itself, a chamber of commerce, a business advisor. Highest
   leverage per unit of code, zero code, and entirely dependent on a relationship that does not
   exist. `PLAN.md` open question 3 is the same question.

These are not exclusive, and 3 does not preclude 1. What would settle it is `PLAN.md` open
question 2 — *two or three real cases* — which remains the single highest-value unblocked action
available and is still not a coding task.

---

# Phase S — Make the selection layer as trustworthy as the data
> **Added 2026-08-09 after running `SCENARIOS.md`.** This phase did not exist when the roadmap was
> written, and it now precedes everything below it. 100 scenarios produced **15 failures, and not
> one of them was a bad fact.** Every audit passes, all 21 zone tables match the LEP, every dollar
> figure traces to its page. What fails is the layer that decides *which stored fact applies* — and
> nothing in this repository tests or audits that layer.
>
> The Phase 0 lesson generalises: *the file nobody has looked at is not the file nobody needs to
> look at.* The layer nobody has audited is `landuse.py`, `vocabulary.py` and the handlers.

### S1 — Fix singularisation, and never answer a use question by falling through · **DONE 2026-08-20**

> **Landed.** The audit below is clean: all 991 land use rows across all 21 zone tables, asked in
> both the table's spelling and the Dictionary's, now get the table's own answer. 287 → **0**.
>
> Three changes, matching the three parts named below:
>
> 1. **The pairing is data.** `LAND_USE_TABLE_SPELLINGS` in `data/definitions.py` carries the LEP's
>    own 105 singular↔plural pairs, read off the Dictionary rather than computed. `canonical_use()`
>    consults it before falling back to the suffix rule, which is now load-bearing for nothing the
>    tables name. `audit_landuse_matching.py` checks the stored pairing against the document, checks
>    every table spelling appears verbatim in `data/zones.py`, and checks it against the
>    `land_use_table_term` some definitions already carried.
> 2. **The hierarchy is keyed the way lookups arrive.** `LAND_USE_HIERARCHY` is written in the LEP's
>    spelling and was being looked up with a canonicalised term, so `business premises` became
>    `busines premise` and the whole `premises` family missed. `E4` + `business premises` now
>    correctly returns prohibited, via `Commercial premises`.
> 3. **The catch-all no longer answers for a term nobody recognised.** This needed a distinction the
>    tool could not previously draw. A use the LEP names that this table omits *is* genuinely
>    unlisted, and the catch-all is then the LEP's own answer — `industry` in R2 is prohibited and
>    saying so is right. A term nothing here can place is a failure to identify the proposal, and it
>    now reports `not_found` / `unrecognised` with `permissible` left None, so it no longer reaches
>    `readiness.py` as a "stop" or `see.py` as "Prohibited". `KNOWN_LAND_USES` is what separates
>    them. The SEPP caveat is now gated on *anything that is not a settled permission*, so it covers
>    the wrong-yes shape the old prohibited-only gate missed.
>
> **Two things found while fixing it that the audit could not see.** The audit only asks about terms
> the tables name, so neither would ever have failed it:
>
> - **Four zones' catch-all was invisible.** RU2, RU3, SP2 and C1 word the row *"Any development not
>   specified in item 2 or 3"* — without the *"other"* that `CATCHALL_TERM` tests for as a substring.
>   In those four an unlisted use came back `not_found` rather than prohibited. `_is_catchall()` now
>   matches both wordings.
> - **Better resolution made the fuzzy fallback dangerous.** Once `Home industries` canonicalised
>   properly, a proposal for `industry` in R2 started matching it by word-boundary containment —
>   *"appears to correspond to Home industries"*, which it does not. For a use the LEP names there is
>   nothing to approximate towards, so `approximate` is now skipped for any recognised term.
>
> **Not done here, deliberately:** `hairdresser` still returns `not_found` rather than resolving to
> `business premises`, though `vocabulary.py:264` already maps it and the LEP's own definition names
> hairdressers. Wiring `DEFINITION_SYNONYMS` into `check_permissibility` is Phase A convenience work,
> and the sequencing note above says not to remove the brake first. It is strictly better than the
> `permitted` it used to return.

`landuse.py:40` strips a trailing `-s` and cannot pair `-ies` with `-y`; 40 land use table terms end
in `-ies`. `match_land_use(..., "hierarchy")` compounds it by looking the canonicalised term up
against raw `LAND_USE_HIERARCHY` keys, making the whole `premises` family unreachable. Verified:

- `E1` + `industry` → `likely_permitted_with_consent`; E1 item 4 prohibits `Industries`
- `E4` + `business premises`, `E4` + `hairdresser` → permitted; E4 prohibits `Commercial premises`
- `E4` + `centre-based child care facility` → permitted; the **plural** returns `prohibited`
- `R2` + `home business` → `likely_prohibited`; R2 permits `Home businesses`, and the same payload's
  `similar_uses` lists that exact term

`data/definitions.py` already carries `land_use_table_term` for precisely this, and `landuse.py`
never consults it. Three parts to the fix, and the third matters most:

1. Resolve through `land_use_table_term` before any string comparison.
2. Replace naive singularisation with the LEP's own singular↔plural pairing, which is *data*, not a
   rule — the Dictionary defines the singular, the table uses the plural, and the mapping exists.
3. **A catchall result must never be reported as a permissibility answer.** Falling through to
   "any other development not specified" means the tool did not recognise the term, which is a
   different fact from the use being permitted. It should say so, and carry the SEPP caveat, which
   is currently gated to prohibited-shaped answers at `tools/zoning.py:251` and so never reaches a
   wrong "yes".

**Write the guard first, before touching `landuse.py`.** `scripts/audit_landuse_matching.py`: walk
every term in all 21 tables, in both singular and plural, and assert the tool's answer matches the
table. It is `audit_zone_tables.py` extended from *the data matches the source* to *the tool agrees
with the data*.

> **The guard exists and the blast radius is measured — `scripts/audit_landuse_matching.py`,
> 2026-08-09.** It asks every one of the 991 land use rows across all 21 tables in two spellings:
> the table's own, and the one the LEP Dictionary defines. The result splits cleanly:
>
> | | |
> |---|---:|
> | asked in the table's own spelling | **0 wrong** |
> | asked in the Dictionary's spelling | **287 wrong** — now 0, see above |
>
> — 120 `wrong_yes` (the table prohibits it, the tool said yes), 91 `wrong_no`, and 76 `unfound`,
> where the answer's shape happens to agree but the term was never actually found. **Every one of
> the 120 wrong "yes" answers ships without the SEPP caveat**, confirming the gating defect at
> `tools/zoning.py:251`, and **every one of the 287 resolves via `catchall` or `none`** — no failure
> is a mismatch onto some other term.
>
> Against the sweep this replaces: wrong_yes was close (115 → 120), wrong_no was understated
> (75 → 91), and the third class was not named at all. The pairing is read off the Dictionary in
> the document rather than computed, which is what makes it data — 105 of the 153 distinct table
> terms carry a second spelling, 47 are already spelled the Dictionary's way, and the single
> genuinely unpaired term is explained in `UNPAIRED_TABLE_TERMS`.
>
> **The zero in the first row is the useful half of the finding.** Once a term is found, everything
> downstream is right; the entire defect is resolution. That narrows the fix below to exactly what
> items 1 and 2 describe and rules out a wider rewrite.

Three reasons it comes first rather than last, and the first is the one that decides it:

1. ~~**The blast radius is not actually known.**~~ **Now known — see above.** The 115-wrong-yes /
   75-wrong-no figure was an agent's sweep never independently re-derived; the audit re-derives it
   at 120 / 91 / 76. The surgery in items 1 and 2 is justified, and nothing wider is.
2. **It is the oracle the fix is graded against.** Nothing else can say the fix is *complete*
   rather than working on the handful of examples already in hand.
3. **It is the repo's own pattern.** Every data module has an audit; the matching layer has none,
   which is precisely why this survived 1,346 tests and ten audits.

### S2 — Give `validate_arguments()` a domain check · **DONE 2026-08-20**

> **Landed.** All three measured defects are refused at the gate, and every numeric property in
> every schema now declares a `minimum` — 35 of them, none of which had a bound before.
>
> - **Non-finite numbers** are rejected before a handler sees them. `inf` and `nan` were reachable
>   because `json.loads` accepts both.
> - **`minimum` and `maximum` are enforced** from the schema. `gross_floor_area_m2: -80` and
>   `development_cost: -5000` are now errors rather than smaller numbers.
> - **A test asserts every numeric property declares a `minimum`**, in the same shape as the
>   existing `_JSON_TYPES` test.
>
> **One more found while doing it, and it generalises the item.** Writing the "every numeric
> property is bounded" test suggested its own generalisation — *does any schema declare a keyword
> the gate does not enforce?* — and that found `items`, declared on all five array arguments and
> enforced on none. `documents_prepared: ["site plan", 5, None]` surfaced to the caller as an
> uncaught `AttributeError`, the same shape as the raw `MCPError` this gate exists to prevent.
> Array element types are now checked, and `_ENFORCED_KEYWORDS` plus a test pin the rule in both
> directions: **to add a keyword to a schema, teach `validate_arguments` to honour it first.**
>
> That rule is the durable part of this item. A declared-but-unchecked constraint is worse than an
> absent one, because it documents itself to the caller as enforced.
>
> **Left alone deliberately:** `fees.py`'s bracket loop is still partial in principle — nothing
> assigns `fee` if no bracket matches. In practice the top bracket's upper bound is `inf`, so every
> finite cost matches, and `nan` (the only value that fell through) is now refused at the gate.
> Adding a second check inside the domain layer would contradict "validate_arguments is the only
> gate", which is the architecture this repo has chosen and documented.

### S2 — original entry · **CRITICAL**
`CLAUDE.md` already records that `_JSON_TYPES` covers the type keyword only. The cost is now
measured: `gross_floor_area_m2: -80` returns `contribution: None` and `budget_at_least: 420.0`
where `+80` returns `16081.24` / `16501.24` — a sign flip silently deletes the largest charge in
the answer, while `why_not` reads *"Supply gross_floor_area_m2 to get a figure"*. And
`development_cost: inf` raises an uncaught `OverflowError` (`fees.py:68`), `nan` an uncaught
`UnboundLocalError`; `json.loads` accepts both, so they are reachable over the wire.

Minimum, at the one gate: reject non-finite numbers, and enforce `minimum` from the schema so
negatives cannot reach a handler. Then a test that every numeric property declares a `minimum`,
in the same shape as the existing `_JSON_TYPES` test.

### S3 — Never compute from an input the schema cannot express · **DONE 2026-08-20**

> **Landed.** Both halves, plus a third case of the same defect found on the way.
>
> **Parking.** All twelve countables now have arguments, generated from `COUNTABLE` so a rate that
> starts counting something new cannot fail to be askable — ten of them had none. And a rate whose
> terms were not all supplied now returns **no number**, with `supply` naming the argument to send,
> instead of a partial sum with `not counted: practitioners` in a list three levels down. The
> medical centre goes from a confident **5** to a declined answer, and to the correct **17** once
> practitioners are given.
>
> **Contributions.** `existing_gross_floor_area_m2` (and `existing_dwellings` /
> `existing_beds_or_sites`) are now arguments. `estimate_contribution` had accepted `existing_counts`
> all along and nothing ever passed it, so the answer's own advice — *"supply the previous floor area
> if it differed"* — named an argument that did not exist. The restaurant expanding 100m² → 140m²
> now returns **$8,040.62** where it returned $0. The same-area assumption is kept, because it is
> right for the ordinary same-tenancy change of use and the shop → café nil is this repo's flagship
> answer; what changed is that it is correctable, and that when an *assumed* net is what set
> `budget_at_least` the answer says so where the number is rather than three levels down.
>
> **The third case: zero was not expressible either.** `estimate_spaces` filtered falsy counts, and
> every caller passed `arguments.get(...) or 0`, so `num_employees: 0` and "nobody said" were the
> same value. An owner-operated café with no staff could not say so, and a rate that should have
> declined instead computed against a silent zero. Now `None` means not supplied and `0` means zero.
> This is the same defect as the missing arguments — an input the caller cannot express — and it is
> what made the parking fix land correctly rather than half-correctly.
>
> **Where this bites, and why it is still right.** `check_da_readiness` gained `num_employees` and
> `seats`, because the café rate adds a staff component and without it there is now no figure at
> all. Three of the twenty-seven rates decline on floor area alone — restaurant, café and gym — and
> each is a use where the staff component is exactly what CLAUDE.md's cautionary tale turned on: an
> 80m² café told its parking was adequate against a real requirement of 14 spaces. A declined answer
> that names the missing argument is worth more than a number that is quietly 20% low.

### S3 — original entry · **HIGH**
`data/parking.py` recognises `practitioners, children, beds, rooms, dwellings,
accommodation_units, work_bays`; `get_parking_rates` exposes `seats` and `num_employees`. A medical
centre with 5 employees returns **5 spaces** against a rate of *"4 per practitioner, plus 1 per
employee"*, with `"not counted: practitioners"` three levels down in `calculation.basis`.

The safe behaviour already exists — `calculation` is omitted entirely when *no* countable is
supplied. Extend that to a *partial* one: expose the missing arguments, and where the dominant term
is absent, decline the number rather than burying the caveat. Same rule as the catchment.

`calculate_da_fees` has the identical defect and it is worth $8,000: a restaurant expanding
100m²→140m² returns `net_contribution: 0.0` because the previous use is *assumed* to occupy the
same floor area, with `existing_gross_floor_area_m2` rejected as an unknown argument. The module
that refuses to assume the catchment assumes this one, and puts $0 into the total rather than
leaving it out.

### S4 — Say "may" where the source says may · **DONE 2026-08-20**

> **Landed, and it was wider than the two modules named below.** The claim was verified against both
> sources first: DCP Chapter 12 mentions a heritage impact statement exactly twice, both in its
> definitions, requires no document, and says of itself only that it applies "whenever development
> consent is required under clause 5.10". cl 5.10(5) says the consent authority **may** require a
> **heritage management document** — a conservation management plan, a heritage impact statement, or
> any other guidance document.
>
> **Nine sites, not two.** `readiness.py` and `tools/see.py` were the assertions, but the same wrong
> citation had reached `see/generate.py` twice, `data/checklists.py` three times, and
> `data/readiness.py`. And the two modules this item held up as correct were only half right:
> `addresses.py` and `signage.py` hedged the modality ("likely", "may") and then pointed at a chapter
> that requires nothing. All nine now cite cl 5.10(5).
>
> **The worst one was in the SEE draft.** `see/generate.py` wrote *"A Heritage Impact Statement
> accompanies this application"* into text going to Council over the applicant's name — a statement
> of fact about a document cl 5.10(5) only says Council *may* ask for, and which the applicant may
> not have. It is now an `[APPLICANT TO COMPLETE]`.
>
> **Both new clauses are cited.** cl 5.10(5)(c) — land *in the vicinity of* an item — is carried in
> the readiness findings and the checklist condition, because a site that `lookup_site_constraints`
> reports as unlisted can still be caught. cl 5.10(10) is offered by `check_permissibility` beside
> the SEPP caveat, since both are reasons a prohibited result is not a settled refusal.
>
> **Guarded by an absence, and by a grep.** `data/heritage.py` quotes the clauses verbatim and
> `scripts/audit_heritage.py` checks them against the LEP — but the load-bearing check is that
> Chapter 12 still requires *nothing*, which a presence check cannot see. It also pins the modality:
> if cl 5.10(5) stops saying "may", every hedge here is wrong in the other direction.
> `tests/test_heritage.py` greps the whole package for the phrase rather than pinning nine call
> sites, because propagation was the failure mode.
>
> One thing deliberately untouched: `data/referrals.py` lists a Heritage Impact Statement for a
> **State Heritage Register** item. That is the Heritage Act s60 regime, not cl 5.10, and this repo
> holds no document for it — changing it would be guessing in the other direction.

### S4 — original entry · **HIGH**
`readiness.py:431` and `tools/see.py:109` assert *"A Heritage Impact Statement is required (DCP
Chapter 12)"*. Chapter 12 mentions a HIS twice, both in definitions, and requires nothing; LEP
cl 5.10(5) says the consent authority **may** require a **heritage management document**, of which
a HIS is one of three forms. `addresses.py:630` and `signage.py:237` already hedge correctly — the
fix is to make the two document-writing modules agree with the two that got it right.

While in there: `grep -rn "5\.10" src/` returns nothing. cl 5.10(5)(c) reaches land *in the
vicinity of* a heritage item, and cl 5.10(10) is the provision by which a café opens in a heritage
building in a zone that would otherwise prohibit it. Neither is cited anywhere.

### S5 — The smaller confirmed defects · **DONE 2026-08-20**

> **Landed — thirteen of the fifteen, with two deferred for stated reasons.** D7 was fixed under S3.
> D9 (natural argument names refused by 13 of 14 tools) is Phase A1, and the sequencing note above
> says the convenience work waits on the correctness work — which this item completes.
>
> The five that mislead rather than annoy:
>
> - **D5** — `lookup_site_constraints` now refuses an out-of-LGA address, and the gate is one shared
>   function so it cannot diverge from its sibling again. Byron Bay was getting a full report with
>   the Lismore flood caveat attached, which is the most load-bearing sentence either tool returns.
> - **D6** — five phrasings of "sign above the awning" now resolve, and **every suggestion carries
>   its pathway**. The bias was structural: string similarity has no idea that the below-awning sign
>   is exempt and the above-awning one needs consent, so an all-exempt list now says that is a
>   property of the spelling and not a finding about the caller's sign.
> - **D8** — `shop top housing` added, and it is on `excluded_uses` so the fixed CBD rate is not
>   applied to a use Schedule 1 charges nothing for. **The audit's completeness check did not
>   exist** — the docstring had claimed it since the file was written, which is how "27 entries
>   checked, 0 not matching" printed while this was absent. It exists now: the land use column is
>   isolated from the PDF by x-position, and the 51 uncarried entries are named rather than silent.
> - **D10** — the schema no longer recommends the $242 under-quote, and a nil-cost answer names
>   Item 2.7 where the caller can see it.
> - **D11** — the invented "CBD exemption precinct" is gone from both live sites. The notes
>   recording that it was invented stay, and a test now guards both directions: the phrase must not
>   be *asserted*, and the records of its removal must not disappear either.
>
> D12's ten are all fixed. Three were worth more than their MED rating: **s39(1)(d)** was cited
> against every application when it reads "for an application for integrated development"; the
> **document matcher** cleared both the waste and stormwater requirements from a bare "management
> plan", short-circuiting the very check written to keep them apart; and **cl 5.22** was transcribed,
> audited, and reached no output that named it — while the natural path,
> `development_type="childcare centre"`, errored out with three options and no redirect, for the
> exact use the clause exists for.
>
> **`tests/test_smaller_defects.py` keeps them together** rather than scattering them across nine
> files. They are held together by provenance, not subject: each was found by running
> `SCENARIOS.md` against the live server and verified by hand against the source. Split up, they
> would read as unrelated assertions with no record of why anyone thought to check.

### S5 — original entry
Fifteen more, listed with evidence in `SCENARIOS.md` D5–D12. The ones that mislead rather than
merely annoy: `lookup_site_constraints` answers for a Byron Bay address with no out-of-area warning
(its sibling refuses correctly); the signage fallback offers eight suggestions that are **all
exempt-pathway**, including for an above-awning sign that needs consent; `shop top housing` is
absent from the parking data while `audit_parking_rates.py` reports it clean; the fee schema's own
description recommends the path that under-quotes by $242; and the *"CBD exemption precinct"* that
`CLAUDE.md` records as deleted on 2026-08-06 is still live at `data/readiness.py:239` and
`tools/see.py:82`.

### S6 — The run-2 leftovers · **DONE 2026-09-27**

> **Landed — four carried over from run 1 and two from the LOW list; the rest are elsewhere.**
> Listed in `SCENARIOS.md` under *Results — run 2*, tested together in
> `tests/test_run2_leftovers.py`, and every test of a fix fails on the code before it.
>
> - **cl 5.22 reaches `check_da_readiness`.** A childcare centre, school or boarding house now gets
>   a `confirm_before_lodging` finding that the flood question reaches past the flood planning
>   area to the probable maximum flood — the one flood finding a Flood Planning Level cannot
>   settle. Matched on the applicant's words with `flood.py`'s own list; a shop gets nothing.
> - **Heritage no longer hardens to silence when an address is given.** The state layer's "not
>   within a mapped area" is a point reading; it now yields an `address_in_the_see` finding naming
>   cl 5.10(5)(c) and the conservation area question stays on the Duty Planner agenda, whose own
>   text already said the layer does not stand in for Schedule 5. Supplying an address had made
>   the answer *less* careful.
> - **`available_flood_areas` offers `cbd_flood_liable`**, and a test holds the menu equal to the
>   words the schema offers, each of which must resolve.
> - **RU4, RU6, R4, E5, C4, W3 and W4 are "not used in Lismore", not "not found".** The names are
>   the LEP's own, read from the clauses that mention them, and RU4/RU6 carry the cl 4.2 note
>   verbatim. A code the Plan never mentions (SP1, X9) is still "not found".
> - **`get_da_checklist`** takes the LEP's food terms, and answers `heritage` (or `flood`,
>   `bushfire`, `height`) with the conditional document that condition adds — read off
>   `CONDITIONAL_DOCUMENTS`' own wording — instead of refusing it as an unknown type.
>
> Not done here: zero `gross_floor_area_m2` is fixed in PR #70's change to the same lines; the
> hairdresser note is A2's; and **implausible inputs stay unflagged**, because any threshold
> would be a figure no document gives, and a flag on every large answer would be a standing
> caveat.

---

# Phase T — What Council actually did

> **Added 2026-09-27.** The first ground truth from outside this repository. Everything before it —
> the audits, 1,346 tests, both scenario runs — checks the tools against the documents *we* hold,
> graded by us. This checks them against what Lismore City Council actually decided.
>
> **Method.** 21 business DAs lodged on or after 1 July 2024 (the current contributions plan) were
> taken from Council's DA Tracker — cafés, a takeaway, barbers, tattoo studios, a hair salon, a
> beauty salon, a medical centre, a gym, two pub jobs, a vehicle repair workshop, storage, a
> childcare expansion, three signs, and one refused small bar. Each was run through the tools with
> only what the business would have known, and graded against Council's Notice of Determination:
> the conditions, the Section 7.11 and Section 64 tables, and the lodged → determined dates.
>
> **The headline.** No wrong "yes", and no invented figure — Phase S held. The stored rates are
> right: where the tool produced a contribution it matched Council within 0.3%, and the Section 64
> DSP rates reproduce Council's per-ET figures to the cent. What failed was **coverage** — the tool
> could not answer for the commonest trades, did not size the largest costs, and did not know
> Council's standard conditions — and one real bug that understates a charge.

**Results.**

| Checked | Result |
|---|---|
| Permissibility, 18 cases | 14 correct · **0 wrong** · 4 unrecognised: *hair salon, barbershop, tattoo studio, tattoo studio and barber* — all approved |
| Section 7.11, rate | Pub additions $2,814.22 vs Council **$2,805.67** (DA 2024/198); vehicle repair at the industry rate, to the cent (DA 2024/337) |
| Section 7.11, in use | Mostly no figure: a floor area is demanded where the answer is nil at any size, and uses without a Table E2 row get "ask Council" |
| Section 7.11, bug | `existing_gross_floor_area_m2: 0` is discarded → **$0** where Council charged $2,805.67 (T1) |
| Section 64 | Levied in 4 of 15 business consents — $9,763 (medical centre), $32,732 (gym) — never sized (T3) |
| Conditions | Food registration, trade waste, outdoor dining, fire safety, skin penetration: predicted. **Flood Evacuation Plan: 9 of 15, never predicted** (T4) |
| Timing | Median **62 days**; 25 of 33 business DAs over 40. The tool refuses to estimate (T5) |
| Signs | Two pylons told "a CDC, not a DA"; both went by DA (T6) |
| Address lookup | 5 of 21 real addresses fail — safely (T7) |

**Two suspected gaps, checked and found fine — do not spend time here:**
`takeaway` and `take away food and drink premises` both reach the retail rate (only the run-together
`takeaway food and drink premises` fails, which is a spelling nobody is owed); and the signage
fallback for an unknown sign already warns that an all-exempt suggestion list is an artefact of
spelling (S5, D6).

**Limits.** Twenty-one cases found street by street, not a census. Notices do not show requests for
information, so `check_da_readiness` is **not** validated by this — the one refused application (a
small bar whose SEE was a single generic page with an `[address]` placeholder left in) has no
published reasons; T9 and T10 record what its own documents show. Most floor areas were back-derived from Council's own charge. Three zones came
from a neighbouring address.

**Privacy.** Notices carry the applicant's name, postal address and email. None are committed.
Cite the DA number — public, and enough to re-fetch — never a name.

### T1 — A zero existing floor area is thrown away, and same-use additions net to $0 · **DONE 2026-09-27**

> **Landed.** DA 2024/198 now grades **PASS — $2,814.22 against Council's $2,805.67** (was FAIL,
> $0). Three changes, one per layer the bug crossed:
>
> - **The handler** keeps a supplied `0` (`is not None` in both comprehensions in `tools/fees.py`),
>   and `contributions._units` treats `0` as zero units rather than "not supplied".
> - **The allowance** no longer assumes an area for the *same* use. `_same_use()` compares the LEP
>   term each word stands for, through A2's `lep_term_for`, so plurals and mapped words match. Pub →
>   pub with no previous area now returns `net_contribution: None`, `supply:
>   existing_gross_floor_area_m2` and `at_most` (the gross). A *change* of use — shop → café,
>   office → café — keeps the same-area default, which is right for it.
> - **The budget** no longer falls back from a `None` net to the gross. `net or gross` would have
>   put the whole area into `budget_at_least` as new: the opposite error, just as unannounced.
>
> Two S3 tests pinned restaurant → restaurant netting to $0 under the same-area default, with a
> rationale ("a change of use in the same tenancy") that described a different case. They now test
> a real change of use, office → café, and `TestTheSameUseIsNotAssumedToHaveBuiltNothing` holds the
> new behaviour. **Known edge:** "restaurant" and "restaurant or cafe" are different LEP terms, so
> that pair is still read as a change of use and keeps the default.

**Original entry:**

**The evidence.** DA 2024/198 converted 14m² of a pub's laundry into bar area; Council charged
**$2,805.67** at the retail rate. The tool's gross figure is right ($2,814.22), but:

- `existing_use: "pub"` → **$0**, because the allowance assumes the previous use occupied the
  same floor area — which, for the same use, means nothing was built.
- `existing_use: "pub", existing_gross_floor_area_m2: 0` → **still $0.** `tools/fees.py:136-140`
  builds `existing_counts` with `if arguments.get(...)`, which drops a `0`, so the same-area
  assumption returns. `contributions._units` also treats `<= 0` as not supplied. This is the
  `None`-means-not-supplied / `0`-means-zero rule in `CLAUDE.md`, broken one argument over from
  where S3 fixed it.

**The fix.**
1. `is not None` in both comprehensions in `tools/fees.py` (the proposal's `counts` has the same
   pattern), and let `_units` return `0` units for a supplied zero on the *existing* side.
2. When `existing_use` resolves to the **same use** as the proposal and no existing area is given,
   do not assume one — return `net_contribution: None` with `supply: existing_gross_floor_area_m2`,
   the discipline `CLAUDE.md` sets for `flood_area` and the catchment. The same-area assumption is
   right for a *change* of use in a tenancy, and meaningless for additions to the same use.

**Test.** Pub 14m², existing 0 → $2,814.22. Pub → pub with no existing area → `None` plus `supply`.
Pub → pub at 10m² → $804.07 (unchanged). **Cost:** an hour.

### T2 — Contributions should resolve words the way every other tool now does · **HIGH**

**The evidence.** Since A2, `check_permissibility` reads `hairdresser` as business premises;
`calculate_da_fees` still says it is "not listed in Table E2 — ask Council", because
`contributions.py` resolves through `LAND_USE_HIERARCHY` and `HIERARCHY_TO_TYPE` only. That is the
same-word, opposite-answer split A2 was written to end, one tool further on. Separately, in all
five consents where the previous use is known and its Table E2 rate is no lower than the new
use's, Council charged **nil** — retail → café (2025/38, 2025/30), pub → café (2025/42), shop →
barber and shop → beauty salon (2026/15, 2024/291, business premises being the cheaper row). Without
a floor area the tool gives no figure, when the answer is nil at any size.

**The fix.**
1. Resolve the contribution type through `landuse.lep_term_for()` and `ancestors()` to the nearest
   `HIERARCHY_TO_TYPE` key, carrying `interpretation()`'s sentence.
2. No-increase shortcut: when the existing use's Table E2 rate is at least the proposal's and no
   area is given, answer *nil, if the new use occupies no more floor area than the old one did*.
3. Vocabulary, in `DEFINITION_SYNONYMS`: `hair salon`, `hairdressing salon`, `barbershop`,
   `barber shop` → business premises. The LEP names hairdressers; these are the words applicants
   use, and DA 2026/15 is Council describing a barbershop as "a business premises" verbatim.
   **`tattoo studio` stays refused** — A2 left it that way deliberately, and although Council
   approved two (2024/246, 2026/213), the one published notice does not name the category. Put it
   in B1 instead.
4. **Council's readings of uses with no Table E2 row go to B1, not to the data.** DA 2024/337
   charged a vehicle repair station at the industry rate, to the cent; DA 2024/153 charged a
   medical centre replacing a dwelling on net traffic only. One notice each is an observation, not
   a rule. Promote a reading when a second notice agrees.

**Cost:** half a day, most of it the test matrix.

### T3 — Size Section 64 per ET, and add the charge that is missing · **HIGH**

**The evidence.** Section 64 was levied in 4 of the 15 business consents, and in both where the
Section 7.11 table is also readable it was the larger of the two:

| DA | Use | ET (water / sewer) | Section 64 | Section 7.11 |
|---|---|---|---|---|
| 2024/153 | dwelling → medical centre | 0.20 / 0.89 | **$9,763.16** | $4,142.15 |
| 2025/157 | new gym, North Lismore | 1.21 / 1.21 | **$32,732.10** | (table is an image) |
| 2024/337 | vehicle repair additions | 0.13 / 0.13 | $2,659.35 | $1,868.60 |
| 2025/29 | hair salon | 0 / 0.11 | $906.95 → **$0** under "Policy 11.3.3" | — |

Three findings:

- **The DSP rates in `data/contributions.py` are right**, indexed by one factor:
  6,500 × 1.2685 = $8,245.04 and 1,400 × 1.2682 = $1,775.42 (Dec-24 quarter); 11,100 × 1.2875 =
  $14,291.22 (North Lismore, 2025). The "2016 dollars" objection is a CPI lookup, not a wall.
- **Every notice has a third line the repo does not carry: Rous County Council bulk water,
  $10,350/ET (2024-25) and $10,958/ET (2025-26)** — larger than Lismore's water and sewer charges
  combined in the medical centre's table. `SECTION_64_NOTES["also"]` names Rous in one sentence.
- **The ET is Council's assessment, and 0.11–1.21 was seen.** That part of the refusal stands.

And one claim to correct: `SECTION_64_NOTES["who_it_catches"]` says a café in a former shop "can be
assessed at several ETs". **None of the four café consents carried a Section 64 charge.** Four is
not enough to say never, but it is enough to stop asserting the opposite.

**The fix.** Fetch Rous County Council's developer charges document into `documents/fees/`
(checked blank and public, indexed); store the quarter's index factor with its source; return
**per-ET figures for all three lines** in the site's service area, with the observed ET range
labelled as observed. Still no total — the ET is Council's. Fetch Policy 11.3.3 too: a waiver that
takes a charge to $0 is worth knowing about before lodging. Extend `audit_contributions.py` to
re-derive the per-ET rates.

**Cost:** a day, most of it the Rous source. Do not store a Rous figure read off a notice.

### T4 — Tell a floodplain business to expect a Flood Evacuation Plan · **HIGH**

**The evidence.** Nine of fifteen consents required one: 2024/153, 2024/198, 2024/291, 2025/38,
2025/157, 2025/178, 2025/182, 2025/192, 2026/15 — cafés, a barber, a beauty salon, a storage yard.
**DCP Chapter 8 requires one only for motels.** This is Council's standard practice, which is
exactly what no document in `documents/` can show. The condition's content is consistent: the
Wilsons River gauge height (station 058176) at which evacuation starts, the evacuation procedure,
hazardous materials above the FPL, and routes out of Lismore — due within three months of consent,
or before the Occupation Certificate. The same notices also state **the site's Flood Planning
Level** (13.32–13.88m AHD seen), the figure this repo says it cannot get.

**The fix.** A small `OBSERVED_CONDITIONS` list — each entry with its content, when it falls due,
and the DA numbers it was seen in — surfaced by `get_other_approvals` and `check_da_readiness` for
a business on or near the floodplain, **labelled as practice, not rule**. Everything that decides a
number stays sourced to documents; this only tells the applicant what to have ready. Add *"The
consent will state your FPL; ask for it now"* to the flood question in `DUTY_PLANNER_QUESTIONS`.

**Cost:** half a day. Resist predicting approval from these (see *Deliberately not doing*) —
they are conditions on consents that were granted.

### T5 — Say what turnaround actually looks like · **MED**

**The evidence.** `get_assessment_timeline` gives the 40-day deemed-refusal period and then says
current turnaround is "not in any document". The tracker has it. For 33 business DAs lodged since
July 2024: **median 62 days, 75th percentile 101, 25 over 40.** In the sample, a $0 shop → barber
took 132 days (2026/15), shop → beauty salon 154 (2024/291), dwelling → medical centre 237
(2024/153).

**The fix.** A dated snapshot — n, median, 75th percentile, the window, the query that produced it
— refreshed by T8, and shown beside the statutory period. Keep the rule that no date is
calculated; a distribution is not a date. It measures lodged → determined, so it includes any
information-request pause, which is what a landlord actually waits through.

**Cost:** two hours once T8 exists.

### T6 — The signage headline should carry its own condition · **MED**

**The evidence.** Both pylons in the sample, 6m and 5m and illuminated (2024/272, 2024/313), went
by DA; the tool's headline for each was "Complying Development — a CDC, not a DA". The DCP says a
pylon is complying *"if erected in accordance with"* the Codes SEPP, whose criteria this repo does
not carry — and *Deliberately not doing* keeps it that way. `list_signage_types` already puts the
condition in its label; `get_signage_requirements` puts it in a sub-field.

**The fix.** The label becomes "Complying Development **if it meets the SEPP criteria, which this
server does not check** — otherwise a DA", and illuminated signs and unknown heritage status say a
DA is the common route. No SEPP encoding. **Cost:** an hour.

### T7 — Accept Lot/DP where the address will not resolve · **MED**

**The evidence.** 5 of 21 real addresses returned no match. Council records a different street
number from the state's address point — the small bar lodged as 135 Keen Street and was tracked as
133; a pub is 68 Bridge Street to one and 72 to the other. The refusal is correct (the nearest match
is a different property), but it stops the applicant at step one — and every notice and rates
notice carries the Lot/DP, which `CLAUDE.md` already tells us to ask for.

**The fix.** A `lot_dp` argument that finds the parcel in the NSW cadastre and reads the zone at
its centroid, with the straddle caveat. Verify live before relying on the service; the existing
rules (never raise, `LISMORE_ADDRESS_LOOKUP=off`, verify rather than trust) apply unchanged.

**Cost:** a day, most of it the live verification.

### T8 — Make this run repeatable: `scripts/validate_against_tracker.py` · **MED**

> **DONE 2026-09-27.** The script has four modes (`harvest`, `fetch`, `grade`, `freeze`), the
> 21 cases are in `tests/fixtures/tracker_cases.json` with Council's figures read off the notices,
> and `/validate-tracker` plus the `tracker-validator` agent run the loop. `grade` reproduces the
> run above: permissibility PASS 14 · GAP 4; Section 7.11 FAIL 1 (T1) · GAP 13; Section 64 GAP 4;
> Flood Evacuation Plan GAP 9. **2026/200/1** (self-storage, Goonellabah) is the first frozen
> prediction — recorded before Council decides, so it is the first case graded without hindsight.
> `tracker-cache/` is gitignored and in `protect-private-paths.py`. T5 can now build on it.

Everything above came from a one-off harness. Make it a script, so the figures this phase cites are
its output rather than a claim. What had to be learned:

- The tracker is Civica/Altitude at `lismore-nsw.altitudelg.com/e-services/` and needs Playwright,
  like the council site. `daEnquiry.do` accepts a GET, but **the date filters are ignored and
  results cap near 150**, so search by street name and filter dates locally.
- Documents are at `dialog/getElectronicDocumentContents.do?id=…`; notices are text-extractable
  with `fitz`. Some tables are images (DA 2025/157's Section 7.11) — report those, do not guess.
- Grade against: permissibility (approved ⇒ not prohibited), Section 7.11 per component (each
  component implies a worker count and PVTs, which is how the floor areas above were recovered
  and how the Table E2 row Council used can be identified), Section 64 per ET, conditions present
  or absent, days lodged → determined.
- **Cache outside the repo** — the notices carry personal details. Put the cache path in
  `.gitignore` *and* in `protect-private-paths.py`, the same two locks as `documents/output/`.

Run it quarterly beside `verify_against_council.py` (E2). **Cost:** a day.

### T9 — Give licensed and live-music venues their own requirements · **HIGH**

**The evidence.** The one refusal in the sample, DA 2026/24 (a change of use from restaurant to a
small bar with live music, CBD laneway, refused June 2026). Council's reasons are not published —
the tracker shows "Refusal Notice Issued" and no document — so what follows is read from the
application's own lodged documents and press coverage, not from Council:

- **The applicant's own acoustic report showed non-compliance.** Measured against the Liquor &
  Gaming NSW Standard Noise Condition — the criterion the report says Council's Environmental
  Health Officer told it to use — music at the nearest shop-top residence was ~22dB over
  background at 63Hz and 125Hz, **about 17dB over the limit**, after soundproofing works. It set an
  internal cap of 91dB(C) against tested levels of 101–109dB(C), and said further reduction "would
  require a significant investment to a building that was not designed to contain loud music".
  Upstairs tenants (a yoga studio and consulting rooms) measured 60–64dB(A).
- **The report's own mitigation was not lodged.** It recommended a Noise Management Plan and
  ventilation that does not undo the sound insulation; neither is among the six documents lodged.
- **Fire safety.** The only fire document lodged was a 2022 annual fire safety statement for the
  building. The owner's public fundraiser, launched three weeks before refusal, named fire safety
  upgrades as the cost of keeping the venue — consistent with a change of building classification
  for an assembly use, which a restaurant → live-music venue usually is.
- **The venue opened three months before the DA was lodged** and has kept listing gigs since the
  refusal. The DA was regularising a use already trading — a common and expensive position for a
  business, because every month of assessment is a month of exposure.

What the tool would have said: `check_da_readiness` flags missing operating details, a BCA
assessment, fire safety and a site plan — the right direction. But the checklist's only noise
line is *"Acoustic report (if the new use generates noise, especially near residential)"*, which
this applicant satisfied on paper. Nothing names a **plan of management**, a **noise management
plan**, the **standard the acoustic report will be judged against**, or the fact that an acoustic
report which finds exceedance is evidence for refusal rather than a box ticked.

**The fix.** A licensed-premises branch in `data/checklists.py` and `readiness.py`, triggered by
the LEP terms that carry it (small bar, pub, entertainment facility, function centre, nightclub)
and by `serves_alcohol` or live music:

1. **Plan of management** — hours, patron capacity, security, patron arrival and departure, the
   complaints line.
2. **Noise management plan** — music limits, who measures them and with what, reviewed yearly.
3. **Acoustic report assessed against the Liquor & Gaming Standard Noise Condition**, at the
   *hours, days and patron numbers applied for*, at the nearest residence and at any tenancy above
   or beside.
4. **BCA classification and fire safety for the proposed occupancy**, before the lease commitment
   rather than after lodgement.

Source rule: fetch the Standard Noise Condition's text from Liquor & Gaming NSW into
`documents/legislation/`. Do not transcribe it from the acoustic report, which is a second-hand
quotation in a private document. Items 1–2 are practice, not law — label them the way T4 labels
the Flood Evacuation Plan, with the DA they were inferred from, and revise the item if the refusal
reasons ever surface (from the applicant, or a GIPA request; the review and appeal windows close
around December 2026).

**Cost:** half a day, plus the source fetch. Add `2026/24` to the scenario suites as the licensed
venue case — neither suite has one that ends in refusal.

### T10 — Say out loud that the documents have to agree with each other · **MED**

**The evidence.** In the same application, the SEE proposed live music Thursday and Friday
5–11pm and Saturday and Sunday 12–11pm, for about 120 patrons; the acoustic report assessed
Friday and Saturday 6–10pm and Sunday 12–7pm. The SEE also said an acoustic report would be
prepared "if required by Council" while one was attached, and closed with an unfilled
`[address]` placeholder. A document that asks for more than its own evidence supports is one an
assessor can refuse on without going further.

**Why this is not a document check.** `readiness.py` never reports a document as verified —
nothing here can open a file, and that rule stays. What it can do is say, at the point of
lodgement, what a business most often gets wrong between documents.

**The fix.** A `confirm_before_lodging` item for any use with operating hours or patronage —
*"the hours, days and patron numbers must be the same in the SEE, the plan of management and every
report; a specialist report assesses only what it was asked to, so check its assumptions and its
conclusion before lodging"* — and a matching line in `not_checked_here`. `generate_see_draft`
should take hours and patron numbers once, as arguments, and write them the same way everywhere
they appear.

**Cost:** two hours.

**Order within the phase:** T1 first — it is the only item that makes an answer wrong rather than
missing. Then T2 and T3, which are where the money is; then T4 and T9, which are what the most
businesses will be asked for and the one refusal the sample contains. T10 rides along with T9.
T8 before T5, which depends on it.

---

# Phase U — Use Council's record, not just grade against it

> **Added 2026-09-27.** Phase T used the DA Tracker as an answer key. Reading 21 notices showed it
> is also a source, and a better one than the documents for three questions a business actually
> asks: *what has already been approved on this site*, *what will Council ask of me*, and *how long
> will I be paying rent before I can open*. Council's consents are heavily templated, so its past
> decisions predict its next ones better than any reading of the DCP. None of this predicts
> **approval** — 20 of 21 were approved, and *Deliberately not doing* still stands.
>
> **Shared rules for all three:**
> - **Snapshot, never live.** Build from a scheduled harvest (T8's machinery) into a dated data
>   file. The public server must not scrape Council's site per request: it is slow, fragile, and
>   an open endpoint scraping on demand is a way to get the tracker blocked for everyone.
> - **Public record only in the snapshot.** DA number, property, lot/DP, description, dates,
>   determination, Council's figures and condition *headings*. Never the applicant, the officer or
>   any contact detail — `parse_listing` already skips them, and `council_facts` is the model.
> - **Say how old it is.** Every answer carries the snapshot date, the way `schedule_status()`
>   does for fees — loudly only when it is actually stale.
> - Do T1–T4 first. This phase adds new answers; T fixes wrong and missing ones.

### U1 — `site_history`: what has already been approved here · **HIGH**

**The evidence.** The small bar refused in June 2026 (DA 2026/24) sat on the same lots — Lots 1
and 2, DP 11350 — as a café approved a year earlier (DA 2025/38), whose consent limited trading
to **9–5 weekdays and 9:30–2:30 Saturday "to ensure reasonable expectations of residential
amenity"**. That is the single most relevant fact about the site for a late-night venue, it was
public, and nothing in this server could have surfaced it. The same lookup answers two other
questions no tool can today:

- **The Section 7.11 allowance.** It depends on evidence of the lawful existing use as at
  1 January 2024 (`EXISTING_DEVELOPMENT_ALLOWANCE["what_you_must_do"]`), and a prior consent *is*
  that evidence. Shop → café is $0 and office → café is ~$12k — the allowance is the difference.
- **Inherited constraints.** Hours, patron limits and conditions on a prior consent tell a
  business what the neighbours have already been promised.

**The fix.** A `site_history` tool that takes an address or lot/DP and returns prior DAs on the
same lots: number, description, dates, determination, and — where a notice is on the tracker —
the condition headings, hours conditions and contributions. **Key it by lot/DP, not street
number**: Council's and the geocoder's street numbers disagree (T7), while the tracker's search
form takes `lotNumber` and `planNumber` directly and every notice lists them.

**Cost:** two days, most of it the snapshot and the lot/DP index. Depends on T8 (done) and pairs
with T7.

### U2 — `find_precedents`: what Council did with applications like mine · **HIGH**

**The evidence.** Across 15 business consents the conditions repeat almost word for word: a Flood
Evacuation Plan (9 of 15), fire safety certification, health premises registration and "no skin
penetration" for hair and beauty, AS 4674 food fitout and an 8kW cooking-appliance limit for
cafés, hours of operation on nearly all. Timing splits the same way: five of the six business DAs
over 100 days in the sample had an information request (the sixth, a childcare expansion, was
notified to neighbours twice), and most without one took 29–64 days.

**The fix.** A `find_precedents` tool: given a use (resolved through `lep_term_for`, so "barber"
finds business premises consents), a zone and optionally a street, return the most recent
comparable determinations with days taken, whether there was an information request, the charges
levied, and the condition headings. Add a short **conditions preview** — the headings that appear
in most of the matches, with what each will require — labelled as practice, not rule, like T4.

**Guard against over-reading.** Show the count behind every pattern ("7 of 9 café consents"), and
answer "not enough precedent" below three matches rather than generalising from one or two.

**Cost:** two days on top of U1's snapshot. Condition headings need a light parser over notice
text. Only headings go into the snapshot, never the notice itself.

### U3 — The lease-stage check, with the cost of waiting · **MED**

**The evidence.** A business's real decision point is signing the lease, not lodging the DA —
and `get_assessment_timeline` tells it the 40-day statutory period while the observed median for
business DAs is 62 days and the 75th percentile 101 (T5). At those figures a business pays about
**nine weeks of rent before it can open at the median, and fourteen at the 75th percentile** —
the number that should set the rent-free period it negotiates, and one no tool gives.

**The fix.** Not a new walk — `prepare_prelodgement_brief` already composes one. Add an optional
`weekly_rent` argument and a *before you sign* section at the top: whether the use is allowed; whether a DA is
needed at all; the charges including the Section 64 range (T3); flood and heritage; the site's
history (U1); and **rent exposure = weekly rent × the observed duration distribution** for that
kind of DA, shown as a median and a slow case, never a date. Keep T5's rule that no calendar date
is calculated.

**Cost:** a day once T5 and U1 exist.

**Order within the phase:** U1 first — it is cheapest, it underpins the contribution allowance,
and it would have flagged the one refusal in the sample. U2 reuses its snapshot. U3 needs T5.

---

# Phase A — Survive first contact

Cheap, days not weeks, and it is the distribution work that can be done from here. Everything in
this phase is aimed at the first three tool calls of a session that has never used this server.

### A1 — Accept the argument names callers actually use

> **DONE 2026-09-25.** `resolve_aliases()` in `registry.py`, run by `call_tool` before
> `validate_arguments`. Six concepts — floor area, cost of works, zone, parking spaces provided,
> address, the proposed use — each with an ordered list of the arguments it may land on, so a tool
> takes the one it declares. The five RB-01 calls now resolve. The collision guard is
> `test_an_alias_never_shadows_a_tools_own_argument`; names whose meaning differs between tools
> (`area_sqm`, `existing_spaces_on_site`, `development_type`) are excluded and pinned. The use
> concept reaches `development_type` only in the parking and fees tools, where it is the use.

**The evidence.** The logs' only usability signal is three `invalid_arguments` results in 18
seconds against `calculate_da_fees`. On 2026-08-09 the first natural-phrasing attempt at the
business path failed twice in a row for the same reason **[verified]**:

| concept | spellings currently in use |
|---|---|
| floor area | `floor_area_sqm` (6 tools), `gross_floor_area_m2` (fees), `area_sqm` (signage), `site_area_sqm` |
| cost | `development_cost` (fees), `estimated_cost` (the three SEE tools) |
| zone | `zone_code` (8 tools), `zone` (setbacks) |
| parking supplied | `spaces_provided`, `parking_spaces_provided`, `existing_spaces_on_site`, `existing_parking_spaces` |

The most complex tool in the business path is the odd one out on the two commonest arguments.

**The fix.** `validate_arguments()` in `registry.py:110` is the only gate on arguments, so this is
one change in one place: an alias map applied *before* the unknown-argument check, rewriting known
aliases to the canonical name.

**Why this does not weaken the gate.** That gate exists because a misspelt or omitted argument used
to produce a confident wrong answer — an empty `land_use` returned "permitted without consent". An
alias is a known-correct rename, not a guess at what the caller meant. Genuinely unknown arguments
still hard-refuse with the existing message. The distinction to hold: **rewrite what we know,
refuse what we do not, never default.**

**Guard it** the way `_JSON_TYPES` is guarded — a test that fails if any alias collides with a real
property name on any tool, so the map cannot silently shadow a legitimate argument.

**Done when** the four rows above each resolve from any spelling, an unknown argument still returns
the existing refusal, and the collision test exists.

**Cost:** ~30 lines and a test. Half a day.

### A2 — Share the resolution path across the other tools

> **DONE 2026-09-27.** `landuse.lep_term_for()` is the shared step, used by `classify_land_use`
> (so permissibility, readiness and the SEE draft) and by `parking.resolve_parking_use()` (all four
> parking callers), which walks the LEP chain to the nearest Chapter 7 rate and shows the path.
> Hairdresser, barber, dry cleaner and bank now reach business premises in both tools; tattoo
> studio still refuses. The walk stops at a use Schedule 1 rates on its own row, which is how it
> found `pub` -> hotel accommodation rate still live in `PARKING_SYNONYMS`. The audit is
> `check_synonyms_follow_the_lep`, which found two synonyms contradicting the LEP.
> **Reduced 2026-08-09.** S1 now owns the resolution machinery itself — `land_use_table_term`,
> singular↔plural, and the rule that a catchall is never an answer. What is left here is the
> *second* half of the problem: making the other tools use that machinery, so a word
> `check_permissibility` can resolve is not refused by `get_parking_rates`. **Do this after S1, on
> top of it** — building a second resolver here would be the drift this repo already warns about.

**The evidence.** `check_permissibility` answers for `barber`, `hairdresser`, `bakery`, `brewery`;
`get_parking_rates` refuses all four **[verified]**. Same word, adjacent questions, opposite
failure modes — which reads to a caller as an unreliable tool rather than a coverage boundary.

**It is not a knowledge gap.** The LEP Dictionary at `documents/lep/lep-2012-nsw-full.txt:4505`
names **hairdressers** explicitly inside `business premises`, and DCP Chapter 7 carries a
`business_premises` rate. The repository holds both halves and does not connect them **[verified]**.

**The fix.** When a term misses a per-tool synonym table, resolve it through `LAND_USE_HIERARCHY`
before refusing — and *show the derivation*, in the register this repo already writes in:

> Chapter 7 sets no rate for 'hairdresser'. The LEP Dictionary includes hairdressers in 'business
> premises', so that rate is applied.

That is a derivation from two transcribed, audited sources, not a guess, and it is auditable the
same way — extend `audit_definitions.py` to check that every hierarchy fallback lands on a term the
target table actually carries.

There are five separate synonym tables in `vocabulary.py`. They should share this fallback. Where
the hierarchy cannot reach, the existing refusal stays: **the fallback must never invent a
category**, only follow one the LEP states.

**Done when** `barber` returns the `business_premises` rate with its derivation shown, an
unreachable term still refuses, and the audit covers the fallback.

**Cost:** 1–2 days, most of it deciding which tools share the path.

### A3 — Make the composed tools the front door · **DONE 2026-09-27**

> **Landed.** The server `instructions` now open with a START HERE paragraph naming
> `prepare_prelodgement_brief` as the first call for anyone who has not narrowed the question —
> ahead of the numbered steps, because an agent reads those as the procedure and would otherwise
> walk them one narrow tool at a time. The tool's own description opens the same way, for clients
> that drop the instructions. **The budget held**: 4,193 characters before, 4,156 after, by
> compressing the opening, step 2, the fee and flood lines, and dropping step 7's now-redundant
> mention of the brief. The 4,200 guard was not touched.
>
> One narrow tool points back, and only on one answer: `check_permissibility` adds
> `the_rest_of_the_job` when the use is *permitted with consent* — the one verdict that opens a
> larger job rather than closing it. Not on "prohibited", not on an unrecognised term, and not on
> every tool: a pointer present on every answer is item 0.1's standing caveat again. Tests pin the
> placement, that "needs only proposed_use" agrees with the schema's `required`, and the pointer's
> presence and absence.

**The evidence.** `prepare_prelodgement_brief` needs only `proposed_use`, runs the whole walk, and
produces the one artifact that physically travels to Council **[verified]**. It is the best thing
in this repository and it sits undiscoverable behind 30 tools, most of which answer one question.

**The fix.** Name it in the server `instructions` as the default starting point for anyone who has
not already narrowed the question, and have the narrow tools point back to it when they answer a
fragment of a larger job. No new tool.

**Done when** a session that opens with "I want to open a café at 12 Keen Street" reaches the brief
without being told it exists.

**Cost:** hours. Watch the instructions budget — `PLAN.md` records it held at 4,200 characters by
compressing rather than growing, and that guard should hold here too.

### A4 — Put the identity statement where it is constant · **DONE 2026-09-27**

> **Half done 2026-09-25.** The statement is in the server `instructions` ("An independent tool,
> not Lismore City Council's" — fitted inside the 4,200-character budget by compressing, not by
> raising it) and in the brief, whose header no longer opens "For: Lismore City Council". Both are
> pinned by tests.
>
> **The PII decision, 2026-09-27: off on the public transport.** `generate_see_draft`,
> `fill_see_pdf` — and `preview_see_form`, which the entry below did not name — are registered
> `local_only`. The public server does not list them, and a call from a stale tool list is refused
> before its arguments are examined, with `not_available_on_the_public_server` and a pointer to
> running the server locally. Stdio is unchanged. `preview_see_form` went too because it takes the
> same required name and address and echoes the name back; it writes no file, but leaving it up
> would keep a PII intake open for a tool whose only purpose is to precede one that is gone.
> A test fails if any tool taking `applicant_name` is not `local_only`, so a fourth cannot slip in.
>
> The refusal logs as its own outcome, `local_only`, rather than `invalid_arguments`. That is the
> "reason to expose them" the entry below asks for, made countable: if it ever shows up in the
> logs, someone real wanted these tools publicly, and the answer to open question 3 changes.
> `fill_see_pdf`'s temp-dir-and-inline branch stays, as defence in depth.

**The evidence.** The only "guidance only, verify with Council" statement lives in `README.md:226`,
which nobody reaching this through the public endpoint or a connector ever sees **[verified]**.
Meanwhile every answer cites clause and page number and reads exactly like official advice. This
project **has no relationship with Lismore City Council**, and nothing in its output says so.

**Where it goes matters more than what it says.** A `disclaimer` key on every response would
recreate precisely the anti-pattern item 0.1 diagnosed: a caveat present on every answer carries no
information, and that is *why* two missed fee resets went unnoticed behind a standing "confirm this
figure" note. An identity statement is different in kind — it is constant by nature, so it belongs
somewhere constant, not stapled to each answer:

- the server `instructions` field, which every client session receives once, and
- the printed output of `prepare_prelodgement_brief`, the artifact most likely to be mistaken for
  something official because it is the one that ends up on a desk at Council.

**The related decision.** `fill_see_pdf` and `generate_see_draft` take an applicant's name and
address, run behind an open unauthenticated endpoint with no terms and no privacy policy, and have
**never been called by anyone real** — so the privacy design (structural log exclusion, per-request
temp dir, base64 inline, delete) is well-built and entirely unexercised **[verified]**. Consider
disabling those two on the public transport until there is a reason to expose them. Turning off an
untested surface that nobody uses costs nothing today and closes the only place applicant PII can
enter this system.

**Done when** the identity statement is in both places, and a decision is recorded either way on
the two PII tools.

**Cost:** an hour, plus the PII decision.

### A5 — Make the brief a one-page printout

**The evidence.** People bring paper to the Duty Planner's counter, and the brief is the only
output here that can reach a business owner without an AI client. It is plain text today, which is
the right content in the wrong form: printed from a chat window it is long, unformatted and easily
mistaken for something Council issued (see A4).

**The fix.** A `format: "pdf"` option on `prepare_prelodgement_brief` that returns one A4 page:
the site and use, the questions for the Duty Planner in priority order with what each costs if
unresolved, the charges known and unknown, and the identity statement at the foot. Return it
inline in public mode and never write it to disk, following `fill_see_pdf`'s `PUBLIC_MODE` rule.
**Take no name or address beyond the property** — a brief does not need an applicant, so this
stays off the PII surface A4 is trying to shrink.

This is the smallest version of shape option 2 in *The decision this roadmap cannot make*: the
paper becomes the product without building the public page, so it does not pre-empt that decision.

**Cost:** half a day. Reuse `fitz`, already a dependency.

---

# Phase B — Say which readings we chose

`PLAN.md` established that the *data* is verified line by line. Nothing yet covers the layer above
it: the readings taken where a source is ambiguous. Those are where a business gets hurt now,
because the data underneath them is right.

### B1 — An interpretation register · **DONE 2026-09-27**

> **Landed — 22 readings, 35 quoted provisions, every one verified on its page.**
> `data/interpretations.py` carries each with the provision verbatim (source, section, PDF page),
> the reading taken, the alternative, why this one, what it costs the applicant if Council
> disagrees, and which way the error falls. `scripts/audit_interpretations.py` checks every quote
> against its document *on the stated page*, and that every `duty_planner_question` and
> `relied_on_by` link resolves; `tests/test_interpretations.py` re-runs it and pins each stated
> cost against what the tool actually computes, so the register cannot drift into describing a
> different tool.
>
> **The entries.** *Parking (6):* the CBD fixed rate replacing Schedule 1 rather than flooring it;
> the café "(whichever is greater)"; the §7.7.3.4 credit reaching a change of use, not only a
> rebuild; rounding once after the credit; the credit not applied to uses kept on Schedule 1 in the
> CBD; unenclosed outdoor dining generating no requirement. *Contributions (6):* the same-floor-area
> default for the previous use; the s2.7 allowance netted as one total rather than per
> infrastructure category; pro rata per 100m²; food and drink premises charged as retail;
> warehouses charged as industry; the published rural tourist figure that does not rebuild from
> Table E1. *Flood (4):* §8.3 reaching a change of use with a fitout; the exemption reaching CBD
> Flood Liable land; the all-development controls surviving it; the controls applied despite §8.3's
> stale LEP 2000 reference. *And one each:* the fees schedule's p30 column attribution; cl 5.10(5)
> "may"; cl 2.3(3)(b) — the nearest listed ancestor decides; §9.2 "residential" mapped to R zones
> and not RU5; the 40-day period as calendar days; Chapter 1's figures as safe harbours.
>
> **Cited where they bite, and only there.** `get_parking_rates`, `calculate_da_fees` (through the
> contribution) and `get_flood_requirements` carry `readings_relied_on` — id, the reading in one
> line, the cost if Council disagrees — inside the answer whose figure turns on it. A shop placed
> outside the CBD cites nothing, and a test says so. Readings that are the stricter choice and cost
> nothing if wrong (the LEP 2000 reference, the all-development flood controls) are registered for
> B2 but not cited, and the fee column is not either: about 4% of a lodgement fee on every fee
> answer is the standing caveat item 0.1 diagnosed.
>
> **Two found by doing it.** `warehouse or distribution centre` resolved to the Industry row
> *exactly*, so nothing in the answer flagged a judgement the LEP's own definition of industry
> argues against — it is the weakest entry in the register and now says so where it is used. And
> the evidence paragraph below conflates two readings: the CBD café's 3-against-17 rests on
> §7.7.3.1 replacing Schedule 1, not on "(whichever is greater)", which only governs the Schedule 1
> side. Both are registered separately.
>
> **Found and not fixed here, because it is S3's defect rather than a reading:** where one side of a
> "greater of" is missing, `estimate_spaces` takes the other side as the answer. An 80m² café
> outside the CBD with 6 staff and no seat count reports `spaces_required: 15` — 40 seats makes it
> 17 — and the function centre and boarding house `or_` / `or_alt` rules do the same. It should be
> `at_least: 15` with `supply: ["seats"]`.
>
> **Not registered, deliberately:** the parking `at_least` floor, which is arithmetic on readings
> already registered rather than a reading of its own; and the catchment, Section 64 and CBD
> boundary, which are refusals and already in `DUTY_PLANNER_QUESTIONS`. `scripts/render_interpretations.py`
> prints the register as B2's review packet, with a line per entry for the planner's mark.

**The evidence.** An 80m² CBD café returns **3 parking spaces**; Schedule 1 would give ~17
**[verified]**. The difference rests on a reading of "(whichever is greater)" that the tool itself
attributes to Tweed Shire's 2018 cross-council review. The tool flagging it is exactly right. But
if Council reads it the other way, a business has planned a fitout around a number that is out by
14 spaces, and no audit in this repository can catch that, because every figure involved is
correctly transcribed.

There are at least a dozen such calls — the CBD parking reading, the change-of-use contribution
allowance under section 2.7, the §8.3 flood exemption, the fee schedule's column attribution — and
they are scattered as prose across individual tool outputs. Nothing assembles them.

**The fix.** `data/interpretations.py`, built on the same insight that produced
`DUTY_PLANNER_QUESTIONS`. That collected the repository's **refusals**; this collects its
**judgements**. Each entry carries: the provision, the reading taken, the alternative reading, why
this one, and **what it costs if Council disagrees** — that last field is what makes the register
usable rather than merely honest, exactly as the cost-of-leaving-it-unresolved field does for the
Duty Planner questions.

Tools that rely on a registered interpretation reference it, so an applicant sees the judgement
inside the answer that depends on it rather than in a footnote somewhere else.

**The rule to add to `CLAUDE.md`**, mirroring the one that already exists for refusals: *if you
take a reading where the source admits another, register it here.* Otherwise the judgement is
invisible and the next person to read the code assumes it was the only possibility.

**Done when** every reading currently defended in prose has an entry, and at least the parking,
contributions and flood tools cite theirs.

**Cost:** 2–3 days, most of it finding them.

### B2 — The planner review packet

B1's real payoff. Once the register exists it *is* the review document: hand one planner a dozen
readings with their alternatives, not 15,000 lines of source.

This is the highest-value action available to this project and **it is not a coding task** — it
needs one professional's hour. The transcription is verified; the reasoning on top of it has never
been checked by anyone with standing to check it.

**Done when** a planner has been through the register and each entry is marked confirmed, disputed
or unresolved. A disputed entry becomes either a correction or a `DUTY_PLANNER_QUESTIONS` item —
both are better than the present state, which is a confident number with a footnote.

---

# Phase C — Heritage, the unfinished half

**The evidence.** `PLAN.md` observes that businesses are disproportionately exposed to **flood and
heritage**, because the commercial centre is the flood-affected, heritage-listed part of the LGA.
Flood got the full treatment in item 0.5: 724 lines of transcribed data, 40 controls, its own
audit, five hazard areas, and a refusal to infer the area. Heritage got none of it.

Today heritage appears only as a referral trigger, a §9.2 signage exception, and a checklist line
**[verified]**. `lookup_site_constraints` can tell a business its site is a heritage item, and
every downstream tool can tell it a Heritage Impact Statement is needed — and then nothing here can
say what DCP Chapter 12 actually requires. The document is in `documents/dcp/`, unread by any tool.

That is the sharpest audience-aligned gap in the repository: the tool raises the alarm and cannot
answer the question it just raised.

### C1 — Transcribe DCP Chapter 12 and give it a tool · **DONE 2026-09-27**

> **Landed as `get_heritage_requirements`.** This entry predates S4, which had already established
> that Chapter 12 requires no heritage document — so the first job was to read the chapter end to end
> and find out what it *does* contain. The answer is more than the S4 notes implied: §12.3 makes its
> policies binding on Schedule 5 items with a variation route ("If a proposal departs from the
> policies, justification must be provided"); §12.4 is Burra Charter principles written as
> recommendations; §12.5 is twelve design guidelines split PREFERRED / NOT ENCOURAGED — signage,
> colours, roof, windows, materials, verandahs, fences, garages, setbacks, outbuildings; and §12.6
> gives each of the seven conservation areas a statement of significance, characteristics and
> precinct policies. All of it is in `data/heritage.py` verbatim: 223 quotes.
>
> **S4's docstring was one clause too strong.** "Chapter 12 requires no document at all" is not
> quite right: §12.5 says "Colour scheme details for new development will be required with the
> development application", and §12.3 requires a justification for any departure. Neither is a
> heritage management document, so S4's correction stands and its absence check still passes; the
> sentence is fixed and the two are carried as `WHAT_CHAPTER_12_DOES_ASK_FOR`.
>
> **The audit was written first and runs both directions.** Presence of every stored string; then
> completeness counted off the document — all 164 bullets, 9 PREFERRED and 8 NOT ENCOURAGED
> headings, 5 objectives, 7 conservation area headings, every figure with a unit (there are five),
> and every Schedule 5 Part 2 row against the stored area names, labels and significance. The page 9
> photograph's scanner noise includes four bullet glyphs; that count is pinned, so a real bullet
> cannot be skipped as noise.
>
> **The rules carried from flood.** Status is never inferred: without `heritage_status` the tool
> returns heritage item / conservation area / both / vicinity / none known side by side, and says the
> state layer confirms but cannot clear. The DCP never goes back alone: cl 5.10(2)–(5) come with every
> answer and (10) wherever an item is possible. "May" stays "may": guidelines are reported under the
> chapter's own labels, and only the three phrasings the chapter itself uses as a flat refusal are
> reported as one.
>
> **The business cases.** Works select the guidelines ("new sign", "repaint facade", "shopfront");
> a sign also gets the pointer to Chapter 9 §9.2. A change of use is told that cl 5.10(2) lists works,
> not uses — a reading, flagged for the Duty Planner — and is offered cl 5.10(10) only where the
> building could be a heritage item: a building that is merely inside a conservation area, even a
> Girards Hill "contributory" one, is not "a building that is a heritage item".
>
> **Not done here:** the DUTY_PLANNER_QUESTIONS entry for "does a change of use with no works
> trigger cl 5.10?" — the tool points at the existing `heritage_status` question instead, to keep
> `readiness.py` out of this change while other work is in flight there. Worth adding.

### C1 — original entry

Same shape as flood: `data/heritage.py` verbatim, `heritage.py` to select, `get_heritage_requirements`,
`scripts/audit_heritage.py` with **both** directions — presence of what is stored, and a count of
the controls in the chapter that are not.

Two rules to carry across from flood before writing a line:

- **Never infer the constraint.** A conservation area boundary is a map, like Flood Map 1 and the
  CBD parking boundary. If the site's status is not supplied and the ePlanning heritage layer does
  not positively flag it, return the controls for both cases rather than picking. The state layer
  can confirm heritage; it cannot clear it — the same trap `lookup_site_constraints` already
  handles for flood.
- **The DCP does not go back alone.** LEP Schedule 5 lists the items and clause 5.10 is the consent
  provision; the chapter is guidance under them.

**Cost:** a week, on the flood template. The template is the reason this is a week and not a month.

### C2 — LEP Schedule 5 heritage items · **DONE 2026-09-27**

> **Transcribed, because the layer answers a narrower question than it looks.** The check this entry
> asks for came first. The live layer could not be queried from the session that did this work (the
> proxy refused mapprod3), so the comparison is from the code and the canned responses:
> `lookup_site_constraints` asks whether the *point under the address* intersects a heritage polygon
> and returns `H_NAME`, `SIG`, `H_ID`. That answers "is this building listed" well — when the service
> is up and the address point sits on the listed lot. It cannot answer three things Schedule 5 can:
> whether a listing exists when no map service is reachable; what is listed **on the same street**,
> which is the evidence an applicant has for the cl 5.10(5)(c) vicinity rule C1 surfaces; and what the
> listing covers — grounds, street trees, or an interior (A5), which cl 5.10(2)(b) turns on. So this
> does not duplicate a working lookup; it answers the question beside it.
>
> **What landed.** `data/heritage_items.py` carries all 113 items (I1–I113) and 18 archaeological
> sites (A1–A18) row for row as the LEP prints them; Part 2's seven conservation areas were already in
> C1. `audit_heritage.py` re-reads both tables from the LEP text and diffs every row both ways, and
> reports any gap in the numbering read off the document. `get_heritage_requirements` takes an
> optional `address` and returns `schedule_5_cross_check`: a listing at that address, listings on the
> same street, and same-named streets in other suburbs.
>
> **Positive-only, both ways.** A match never sets `heritage_status` — a Schedule 5 address can be a
> range, a road reserve or several lots — and no match clears nothing: a conservation area is a map
> boundary, and an item round the corner is as near as one on the street. The matcher reads the LEP's
> own address forms (ranges, `1/115` unit prefixes, "Bridge and Woodlark Streets", I49's untyped
> "188 Keen") and rejects a street name followed by another word ("Leycester Creek", "Eltham Railway
> Bridge"); each is a test.
>
> **Left for later, deliberately.** Joining the layer's `H_ID` to the Schedule 5 row inside
> `lookup_site_constraints` would let it quote the property description — but `addresses.py`'s
> heritage handling is being changed in parallel, so it is not touched here. And "State" in the
> Significance column is not State Heritage Register listing; nothing here treats it as one.

### C2 — original entry

Lower priority and only worth it if C1 lands: the item list makes "is this specific building
listed" answerable offline, against a source already in `documents/`. Check first whether the
ePlanning layer already answers it well enough — do not transcribe a table to duplicate a working
lookup.

---

# Phase D — The rest of the audience-aligned content

Ordered by how often a business hits it. Each is the same shape as C1 and none is urgent.

- **D1 — DCP Chapter 2, Commercial Development.** The one chapter written for the audience this
  server is explicitly for, currently reachable only through generic keyword search **[verified]**,
  while Chapter 1 (Residential) has two dedicated tools, 1,112 lines of data and its own audit.
  Awnings and weather protection, CBD urban design, the Health Precinct.
- **D2 — DCP Chapter 15, Waste Minimisation.** Referenced seven times in checklists as prose with
  no structured answer **[verified]**. A waste management plan is a standard request-for-information
  trigger on food premises, which makes it a delay, which is rent.
- **D3 — The villages (RU5).** `PLAN.md` names RU5 as a business zone and Part B Chapter 6 (Nimbin)
  sits unread in `documents/`. Least common, genuinely underserved.

**Before starting any of these, re-read the lesson from Phase 0**: *the file nobody has looked at is
not the file nobody needs to look at.* Each of these is a fresh transcription, which is the activity
that produced every invented figure this project has had to remove. Write the audit first.

---

# Phase E — Do not rot

Small, dull, and the reason the fee schedule was two years stale before anyone noticed.

### E1 — The third direction for the two audits that lack it · **DONE 2026-09-27**

> **Landed.** Both audits now read the inventory off the document and fail on anything neither
> carried nor named with a reason.
>
> - **`audit_timing.py`** reads every subsection of Part 4 Division 4 (ss91–95) off the fetched
>   regulation — 17 of them — and requires each to be quoted in `data/timing.py` or named in
>   `DIVISION_4_NOT_CARRIED` with why it cannot reach an ordinary local DA. An inserted `s94(8)`, a
>   dropped explanation and an explanation for a subsection that no longer exists are each reported,
>   and tests show all three failing. It also checks each quote against the subsection its `clause`
>   names rather than the whole 600KB text, so a quote filed under the wrong subsection is caught.
>   One subsection turned out worth carrying rather than explaining: **s94(7)**, the 25-day limit on
>   a referral agency's own information request. The data had paraphrased it as "the same 25-day
>   style limit", but the agency's 25 days run from when it receives Council's referral, not from
>   lodgement. It is now quoted and reaches `get_assessment_timeline`.
> - **`audit_contributions.py`** reads Table E2's development type column off the PDF by
>   x-position (superscript note letters dropped, wrapped labels joined) and requires each of the 11
>   rows to be carried by `plan_name` or named in `UNCARRIED_TABLE_E2_ROWS`. All 10 rated rows are
>   carried; "Other Development" is named, since it is Note E rather than a rate.

Most audits already check both directions; two do not **[verified]**:

- **`audit_timing.py` is presence-only.** It checks all 17 stored quotes still appear in the
  regulation. It cannot see a provision an amendment *adds*. That matters more here than anywhere
  else in the repo, because this audit's whole purpose is to detect **the law changing** rather
  than a transcription slipping — and an amendment that inserts a period or a limit is exactly the
  case it is blind to. Read the assessment-period provisions off the source and report any not
  carried, the way `audit_readiness.py` already reads the s39(1) paragraph letters.
- **`audit_contributions.py`** has presence plus a strong derivation check across all 30 cells of
  Table E2, which is better than completeness for that table — but nothing checks that every
  development type in the plan is carried in the data. Smaller, worth an hour while in there.

### E2 — Put `verify_against_council.py` on a schedule · **DONE 2026-09-27**

> **Landed.** `.github/workflows/verify-against-council.yml`, quarterly on the 3rd of Feb, May,
> Aug and Nov — August so the run follows Council's July fees reissue — plus `workflow_dispatch`.
> Default `GITHUB_TOKEN` only, `contents: read` and `issues: write`, checkout without credentials,
> and a step that fails if `documents/` changed.
>
> **The part that needed design was "could not fetch".** Council's site 403s plain HTTP and may
> refuse GitHub's runners altogether, and before this change a refused download was lumped in with
> drift as a "problem", exit 1. A block would have opened a drift issue every quarter until
> someone learned to ignore it. The script now has an exit-code contract — 0 clean, 1 drift,
> 3 unverified, 4 verifier error, 2 usage — and writes the same verdict as JSON; drift outranks a
> partial block, and an uncaught exception no longer exits with the drift code. A download that is
> not a PDF (a challenge page saved under a PDF's name) is *not fetched*, not *changed*. After three
> consecutive failed downloads the rest are skipped, so a blocked runner answers in minutes rather
> than an hour. Drift and "could not run" open **different** issues (`council-drift`,
> `council-verify-blocked`); a later run that fetches successfully closes the latter.
>
> **Found while testing it:** `normalise()` in the verifier had lost its curly-apostrophe
> replacement — both calls were straight-to-straight no-ops — so the hotel and motel parking rates
> (*manager's/owner's*) would have reported as drift against an unchanged Chapter 7 on the very
> first run. A test now serves the committed PDFs as the "live" copies and requires a clean verdict,
> which runs every real figure check against every real document.
>
> **Not verified here:** the live run. This environment cannot download Playwright's Chromium, so
> the workflow has not executed against Council's site; trigger it once by hand after merging.

The script exists and does the right thing; only the cron does not. GitHub Actions, quarterly,
opening an issue on drift. It needs the `scraping` extra and must never write to `documents/`.
Converts a chore that has already been missed twice into an alert nobody has to remember.

### E3 — The July ritual · **DONE 2026-09-27**

> **Landed** as a section of `CLAUDE.md` Part 1, "The July ritual", beside the fee paragraph, with
> a pointer from `data/fees.py`'s docstring. It is six steps rather than two, because grepping for
> the schedule's filename and year found it named in eight places — `data/instruments.py`,
> `council_sources.py`, the verifier's `FIGURE_CHECKS`, `audit_approvals.py`, `data/fees.py`,
> `data/approvals.py`, tests and prose.
>
> **One trap the two-step version would have walked into:** the schedule prints last year's figure
> beside this year's on 999 rows, so after the PDF is swapped `audit_approvals.py` and the
> verifier's fee check both still pass with every figure a year stale — they are presence checks,
> and the stale figure is present, in the left column. The ritual says so at the step where it
> matters. Making the audit column-aware would close it properly and is not done here.

The statutory fee scale and Council's fees schedule both reset in July. `schedule_status()` already
shouts when the scale is behind **[verified]**, so this is not a silent failure — but shouting is
not refreshing. Write the two-step down in `CLAUDE.md` where the next July will find it: get the
new PDF, re-run `audit_approvals.py`.

---

# The distribution track

Runs in parallel with everything above and is mostly not code. Phase A **is** the codeable part.

- **Get two or three real cases.** `PLAN.md` open question 2, still the highest-value unblocked
  action in this project. Refusals, delays, RFIs and cost surprises need different fixes, and this
  roadmap is guessing which until someone knows.
- **Then re-read the logs.** The current reading found only ourselves. Any real user changes what
  Phase D should contain far more than any amount of reading the source documents will.
  **Filter server-side** — `PLAN.md` records that day-level queries silently truncate at 1,000
  lines and undercounted by 7×.
- **Decide the shape** (the three options above). Not urgent until Phase A lands, because Phase A
  is worth doing on all three.
- **Approach Council's small business planner — with something to give.** Several consents in
  Phase T's sample were signed by a *Development Planner – Small Business / Process Improvement*:
  a role that exists to reduce exactly the friction this repo is about. The tracker analysis is a
  useful gift to that role — a 62-day median for business DAs, and five of the six over 100 days
  carrying an information request — and a better opening than asking for time. This is the concrete form of
  shape option 3 and of *Open questions* 2. Lead with the data, not the tool.
- **Get the information request letters.** They are what drives delay (Phase T: five of the six
  business DAs over 100 days had one), and the tracker publishes none, so `check_da_readiness` is still graded
  against nothing. Two routes: a **GIPA request** to Council for de-identified information request
  letters on business DAs since July 2024, and asking recent applicants directly — the tracker
  shows who had one. Twenty letters would show which requests recur for which use, and would make
  the readiness check testable for the first time. Keep them out of the repo the way
  `tracker-cache/` is kept out, and record only the categories of what was asked.

### A telemetry idea worth designing carefully

The logs record tool, outcome and duration and **nothing else, by shape not by discipline** — that
is what keeps applicant data out of them, and it should not be loosened casually. But it also means
the repository cannot learn which questions it is failing to answer: A2 exists only because
someone tried `barber` by hand on 2026-08-09.

A narrow version is compatible with the guard: log the **unresolved term only** when a resolution
fails, and only for arguments whose schema is a land-use category (`development_type`, `sign_type`,
`land_use`) — never a free-prose field, and never `property_address`, `applicant_name` or anything
in the SEE tools. That turns the synonym gaps into data instead of anecdote.

**Do not implement this by relaxing `record_tool_call()`'s signature.** The whole point of the
current design is that the function *cannot* be handed applicant data. Add an explicitly
allowlisted second path with its own test asserting the allowlist, or leave it alone.

---

## Deliberately not doing

Carried forward from `PLAN.md` and still right:

- **Encoding SEPP pathways** from the SEPPs themselves. A wrong "yes" is worse than "we cannot tell
  you."
- **Predicting whether Council will approve something.**
- **More transport, dispatch or SDK work** unless something is broken.

New:

- **Reorganising the documentation.** `CLAUDE.md` (66KB) and `PLAN.md` (70KB) against ~15,000 lines
  of source is a real and growing cost. It is also the cost of the thing that made the data
  trustworthy — each rule carries the failure that produced it, which is why the invented figures
  were found and removed. It is not what is limiting this tool. Revisit if a second person ever
  works here.
- **Reading uploaded documents** — an SEE, an acoustic report — to check them. It would have
  caught the small bar's contradictions (T10), but it breaks `readiness.py`'s rule that nothing
  here reports a document as verified, and it pulls private files onto an open endpoint. T10's
  *confirm before lodging* item gets most of the benefit without either cost.
- **A `disclaimer` field on every tool response.** See A4: this recreates the standing-caveat
  failure of item 0.1 and would make the identity statement invisible within a week.
- **Building the public web front end** before the shape decision is made. It is option 2 of three,
  it carries a privacy surface this project has deliberately kept small, and choosing it by
  accident — because it was the fun part — is how the previous plan kept generating engineering
  that was not the constraint.

---

## Open questions

1. **Which of the three shapes?** See *The decision this roadmap cannot make*. Not blocking Phase A.
2. **Is there an appetite to approach Council directly?** `PLAN.md` open question 3, unchanged and
   still the highest-leverage relationship that does not exist.
3. ~~**Should the two PII-taking tools be exposed on the public transport at all?**~~ **Decided
   2026-09-27: no, until there is a reason** — and three tools, not two (A4). Revisit if the
   `local_only` outcome appears in the public logs; exposing them then needs a real test of the
   privacy design rather than a design argument, and terms for the endpoint.
4. **Does anyone want the parking reading resolved badly enough to ask?** B1 registers it; B2 would
   settle it. Council's Duty Planner would answer this in ten minutes of a free session, and it is
   worth ~14 parking spaces to an 80m² CBD café.

---

## How to work through this

The habit that already works here, kept: **one item per branch, one PR, and the commit message
says what changed for an applicant rather than what changed in the code.** The audits and all 1,346
tests run in CI on every one **[verified]**.

Two rules for whoever picks this up:

- **Phase S before anything else, then Phase A.** S is correctness: the tool currently tells a
  business a prohibited use is permitted, and deletes a $16,081 charge on a sign flip. A is days of
  work and the only distribution work available from inside the repo. Everything after both is
  worth less while the tool is confidently wrong and hard to call.
- **Phase T's T1 goes with the correctness work, ahead of Phase A** — it understates a charge the
  way S3's sign flip did. The rest of Phase T can run alongside Phase A: it is coverage, and it is
  the only part of this roadmap graded against Council's decisions rather than our own reading.
- **Phase U after T1–T4.** It adds answers the server has never given; T fixes answers it gives
  wrongly or not at all. U1 can start as soon as T1 is in, since it shares only T8's machinery.
- **Re-run `SCENARIOS.md` after each phase.** It caught fifteen defects that 1,346 tests and ten
  audits did not, because it is the only thing here that composes tools the way an applicant does.
- **Do not declare a phase finished without listing what was in it.** Phase 0 was declared done
  twice while files it had never opened still held invented figures. Before closing a phase, write
  down the items it covered and check each one — the failure mode is not laziness, it is that
  "all the data modules are audited" sounds true when nobody has enumerated the data modules.
