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
  prevent. **[corrected]**
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

### S3 — Never compute from an input the schema cannot express · **HIGH**
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

### S4 — Say "may" where the source says may · **HIGH**
`readiness.py:431` and `tools/see.py:109` assert *"A Heritage Impact Statement is required (DCP
Chapter 12)"*. Chapter 12 mentions a HIS twice, both in definitions, and requires nothing; LEP
cl 5.10(5) says the consent authority **may** require a **heritage management document**, of which
a HIS is one of three forms. `addresses.py:630` and `signage.py:237` already hedge correctly — the
fix is to make the two document-writing modules agree with the two that got it right.

While in there: `grep -rn "5\.10" src/` returns nothing. cl 5.10(5)(c) reaches land *in the
vicinity of* a heritage item, and cl 5.10(10) is the provision by which a café opens in a heritage
building in a zone that would otherwise prohibit it. Neither is cited anywhere.

### S5 — The smaller confirmed defects
Fifteen more, listed with evidence in `SCENARIOS.md` D5–D12. The ones that mislead rather than
merely annoy: `lookup_site_constraints` answers for a Byron Bay address with no out-of-area warning
(its sibling refuses correctly); the signage fallback offers eight suggestions that are **all
exempt-pathway**, including for an above-awning sign that needs consent; `shop top housing` is
absent from the parking data while `audit_parking_rates.py` reports it clean; the fee schema's own
description recommends the path that under-quotes by $242; and the *"CBD exemption precinct"* that
`CLAUDE.md` records as deleted on 2026-08-06 is still live at `data/readiness.py:239` and
`tools/see.py:82`.

---

# Phase A — Survive first contact

Cheap, days not weeks, and it is the distribution work that can be done from here. Everything in
this phase is aimed at the first three tool calls of a session that has never used this server.

### A1 — Accept the argument names callers actually use

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

### A3 — Make the composed tools the front door

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

### A4 — Put the identity statement where it is constant

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

---

# Phase B — Say which readings we chose

`PLAN.md` established that the *data* is verified line by line. Nothing yet covers the layer above
it: the readings taken where a source is ambiguous. Those are where a business gets hurt now,
because the data underneath them is right.

### B1 — An interpretation register

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

### C1 — Transcribe DCP Chapter 12 and give it a tool

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

### C2 — LEP Schedule 5 heritage items

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

### E1 — The third direction for the two audits that lack it

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

### E2 — Put `verify_against_council.py` on a schedule

The script exists and does the right thing; only the cron does not. GitHub Actions, quarterly,
opening an issue on drift. It needs the `scraping` extra and must never write to `documents/`.
Converts a chore that has already been missed twice into an alert nobody has to remember.

### E3 — The July ritual

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
3. **Should the two PII-taking tools be exposed on the public transport at all?** A4 proposes
   disabling them until there is a reason. If the answer is "keep them", the privacy design needs a
   real test rather than a design argument, and the endpoint needs terms.
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
- **Re-run `SCENARIOS.md` after each phase.** It caught fifteen defects that 1,346 tests and ten
  audits did not, because it is the only thing here that composes tools the way an applicant does.
- **Do not declare a phase finished without listing what was in it.** Phase 0 was declared done
  twice while files it had never opened still held invented figures. Before closing a phase, write
  down the items it covered and check each one — the failure mode is not laziness, it is that
  "all the data modules are audited" sounds true when nobody has enumerated the data modules.
