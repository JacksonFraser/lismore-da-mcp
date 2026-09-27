# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This file has two halves:

- **Part 1 — Working on the code** (below): how to build, run and modify the MCP server.
- **Part 2 — Lismore DA knowledge base** (from "Lismore Development Application Assistant"
  onward): domain content loaded as context when *using* the agent to answer planning questions.
  Do not delete it when editing this file.

**Who this is for: local businesses in the Lismore LGA going through a DA** — opening, changing
use, fitting out or expanding. A business is usually doing a **change of use** in E1–E4, MU1 or
RU5, while much of the older tooling (SEE form, residential standards, setbacks) targets R zones.
Read **`PLAN.md`** before picking up work.

History — why a rule exists, which bug it came from — belongs in commit messages and PRs, not in
code comments or this file. Keep comments to what the code does and the constraint it must keep.

---

# PART 1 — WORKING ON THE CODE

## Commands

```bash
uv sync --extra dev                       # install deps into .venv (Python >=3.14)
uv sync --extra scraping                  # + httpx/playwright, only for scripts/fetch_*.py
# Without uv:
python3.14 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"

.venv/bin/python -m pytest                # tests (~3.5 min; the index parity tests are the slow ones)
.venv/bin/ruff check src tests scripts    # lint, incl. a complexity ceiling (see pyproject.toml)
.venv/bin/pyright --pythonpath .venv/bin/python   # type check (basic mode, src/ only)

.venv/bin/python -m lismore_da_mcp.server # run the server over stdio (what .mcp.json launches)
MCP_TRANSPORT=http PYTHONPATH=src PORT=8080 \
  .venv/bin/python -m lismore_da_mcp.server   # run the public HTTP transport locally
curl localhost:8080/health                # → "ok"
```

CI runs pytest, ruff and pyright; all three must pass. To try a tool without an MCP client, import
`call_tool` and call it directly:

```bash
.venv/bin/python -c "
import asyncio
from lismore_da_mcp.server import call_tool
print(asyncio.run(call_tool('get_parking_rates', {'development_type': 'restaurant'}))[0].text)"
```

## Repo tooling (`.claude/`, committed on purpose)

| | |
|---|---|
| `/check-documents` | Validates `documents/`: real PDFs, no error pages, right LEP edition, indexed, in a searched category. Also runs in CI. |
| `/smoke` | Drives the server with a real MCP client over **both** transports. Unit tests call handlers directly and never open a session. |
| `planning-data-reviewer` agent | Checks transcribed data in `data/` against the source documents. Tests pin that the data has not *changed*, not that it is *right*. |
| `protect-private-paths.py` hook | Blocks `git add`/`commit` touching `documents/output/`, `my-application/`, `_quarantined/` or `tracker-cache/`, including with `-f`. |
| `scripts/audit_*.py` | Check the hand-transcribed data in `data/` against the source documents in `documents/`. See below. |
| `scripts/verify_against_council.py` | Checks the PDFs in `documents/` are still what Council publishes: re-downloads, compares, re-verifies figures, crawls for new documents. Needs the `scraping` extra. Never writes to `documents/`. **Exit codes are a contract:** 0 clean, 1 drift, 3 unverified (something could not be fetched, nothing else wrong), 4 the verifier failed, 2 usage; `--json` / `--issue-body` carry the same verdict. A download that is not a PDF counts as not fetched, never as a changed document. |
| `.github/workflows/verify-against-council.yml` | Runs the verifier quarterly (3 Feb/May/Aug/Nov — August follows Council's July fees reissue) and on `workflow_dispatch`. Drift opens or comments on a `council-drift` issue; a block or verifier failure goes to a **separate** `council-verify-blocked` issue, so a block reads as neither drift nor clean. Default token only (`contents: read`, `issues: write`), no credentials persisted, fails if `documents/` changed. |
| `/validate-tracker`, `tracker-validator` agent, `scripts/validate_against_tracker.py` | The only check graded by someone other than us: real business DAs from Council's DA Tracker, graded against the Notices of Determination. `harvest` / `fetch --update` / `grade` / `freeze` (a prediction for an undetermined DA). Inputs are what the applicant knew at lodgement. Notices carry names and emails, so downloads stay in `tracker-cache/` (gitignored and hook-blocked). Live, and needs the `scraping` extra. |
| `scripts/run_scenarios.py` | Runs `SCENARIOS.md` against the real handlers with fixed calls and keeps every answer verbatim; `--compare` lists what changed since an earlier run. It does not judge; an unchanged answer keeps its verdict. Run it after every phase. |

The audits, one per data file:

| Script | Checks |
|---|---|
| `audit_zone_tables.py` | Every zone land use table against the LEP text. Known defects in the scraped source are listed in `SOURCE_TEXT_DEFECTS`. |
| `audit_landuse_matching.py` | The only audit of a **tool**: asks `check_permissibility` about every land use row (both spellings) and every Dictionary "is a type of" note in every zone, and grades the answers against the table. Also audits `LAND_USE_TABLE_SPELLINGS` and `LEP_TYPE_OF` against the Dictionary. |
| `audit_definitions.py` | Land use definitions against the LEP Dictionary: each quote opens with its own term, `land_use_table_term` matches `data/zones.py`, hierarchy links agree with the LEP, recorded inventions stay absent. |
| `audit_parking_rates.py` | Every rate appears verbatim in DCP Chapter 7, and every Schedule 1 row is either carried or listed in `UNCARRIED_SCHEDULE_1_USES`. |
| `audit_contributions.py` | Section 7.11 figures appear in the plan, **and** Table E2 rebuilds from Table E1's components (catches transpositions a presence check cannot), and every Table E2 row read off the PDF is carried or named in `UNCARRIED_TABLE_E2_ROWS`. |
| `audit_standards.py` | DCP Chapter 1 quotes, missing Acceptable Solution labels, and that `NOT_SET_BY_THIS_CHAPTER` figures are really absent. |
| `audit_flood.py` | All flood controls against DCP Chapter 8 and the LEP; derived constants agree with their quotes; every numbered control is counted. |
| `audit_heritage.py` | cl 5.10 provisions against the LEP; every Chapter 12 quote against the chapter, and every bullet, PREFERRED / NOT ENCOURAGED heading, objective, conservation area and figure in the chapter is carried; all Schedule 5 items and archaeological sites in `data/heritage_items.py` row for row, both ways; that Chapter 12 still requires no heritage management document; and that cl 5.10(5) still says "may". |
| `audit_commercial.py` | DCP Chapter 2 quotes and figures; every section, subheading and Table B1 label read off the chapter's typography is carried or named in `DESCRIPTIVE_SECTIONS`; recorded absences, including that the chapter never mentions a change of use. |
| `audit_waste.py` | DCP Chapter 15 quotes and figures; the numbered requirements in each section are counted against what is carried; Appendix C's generation rates are rebuilt from line geometry and compared cell by cell, both ways. |
| `audit_nimbin.py` | DCP Part B Chapter 6 (Nimbin) quotes; section headings, every precinct's preferred-use list (item for item), the Live/Work labels and every figure with a unit read off the document; no figure in the guidance text the chapter does not print; recorded absences. |
| `audit_signage.py` | DCP Chapter 9 definitions and standards, plus any sign type §9.3 defines that the data lacks. |
| `audit_timing.py`, `audit_readiness.py` | Assessment periods and lodgement/rejection provisions against the fetched EP&A Regulation. A mismatch means **the law changed**. Both read the provisions off the source — every subsection of Part 4 Division 4 must be quoted or named in `DIVISION_4_NOT_CARRIED`, every s39(1) paragraph carried — so an amendment that *inserts* one is caught. |
| `audit_interpretations.py` | Every provision quoted in `data/interpretations.py` appears verbatim on the PDF page the entry names, and its `duty_planner_question` / `relied_on_by` links resolve. It cannot audit the readings themselves; `render_interpretations.py` prints the register for a planner to review. |
| `audit_approvals.py` | Dollar figures in `data/approvals.py` still appear in Council's fees schedule (reissued every July). |

A presence check is blind to invention. Where a source says something is *not* required or *not*
set, the audit asserts the absence too; where a table has internal arithmetic, rebuild it.

## Architecture

`server.py` is wiring: SDK adapters, dispatch, and re-exports for older
`from lismore_da_mcp.server import X` imports. Import from the owning module in new code.

| Layer | Where | What |
|---|---|---|
| Facts | `data/` | Hand-transcribed source content: zones, parking, contributions, fees, definitions, standards, referrals, flood, heritage, heritage items, commercial, waste, nimbin, signage, timing, readiness, interpretations, … |
| Domain logic | `fees.py`, `contributions.py`, `parking.py`, `signage.py`, `approvals.py`, `timing.py`, `readiness.py`, `flood.py`, `standards.py`, `heritage.py`, `commercial.py`, `waste.py`, `villages.py`, `interpretations.py`, `landuse.py`, `addresses.py`, `search.py`, `index.py`, `vocabulary.py` | Computation over the facts. |
| Tools | `tools/` | One module per domain. Handlers format; they do not compute. |
| SEE form | `see/` | `fields`, `layout`, `fill`, `generate`, `parsers` for the Council PDF. |
| Plumbing | `registry.py`, `app.py`, `transport.py`, `observability.py`, `config.py` | Registration, the `Server` object, stdio/HTTP, logging, paths. |

**Keep handlers thin.** If a handler computes rather than formats, move the computation one layer
down where it can be tested and reused — e.g. every parking figure comes from
`parking.estimate_spaces`, so the parking tool, the SEE draft and the Council form agree.

**A tool is one decorated function that carries its own schema** (`@tool` in `registry.py`).
Adding a tool means writing the function and updating the tool table in `README.md`.

**`validate_arguments()` is the only gate on arguments** — the SDK does not validate. It rejects
unknown arguments, missing/empty required ones, wrong types (including array elements), non-finite
numbers, and values outside `minimum`/`maximum`. Values are refused, never coerced or clamped.
Every numeric property declares a `minimum` (a test enforces it), because the dangerous values are
well-typed: a negative floor area is a valid float that silently shrinks a total.
`_ENFORCED_KEYWORDS` is the set of schema keywords the gate honours, and a test fails on any other —
**to use a new keyword in a schema, teach `validate_arguments` to enforce it first.**

**Known aliases are renamed before the gate, and only known ones.** `resolve_aliases()` runs first
in `call_tool` and renames the spellings callers use (`floor_area`, `cost_of_works`, `zone`,
`parking_spaces`, `address`, `use`) to the argument each tool declares, from `ARGUMENT_CONCEPTS`.
A tool's own argument is never rewritten, two names with different values are refused, and
anything not in the table is refused by the gate as before. **Do not add an alias whose meaning
differs between tools** — `area_sqm`, `existing_spaces_on_site` and `development_type` are left
out on purpose, and a test pins that.

**A schema that cannot express an input produces a wrong answer, not an error.** If a rate or
formula depends on a quantity, the schema must be able to take it (the parking countables are
generated from `COUNTABLE` for this reason). **`None` means not supplied; `0` means zero** — write
`is not None`; never test a count for truthiness.

**A partial sum is never reported as the answer.** When a parking term was not supplied,
`estimate_spaces` returns `spaces_required: None`, `supply` naming the missing argument, and
`at_least` (a true floor, since every Schedule 1 rate only grows as terms are added). A shortfall
against it is `shortfall_at_least`, never `shortfall`. The same discipline applies to the
contributions catchment and `flood_area`: an input that changes the number is never assumed.

**Two transports, one server object.** `MCP_TRANSPORT` unset/`stdio` → `stdio_server()`;
`http` → a Starlette app (`build_http_app()`) with `StreamableHTTPSessionManager(stateless=True)`
at `/mcp`, `/health`, and an in-process per-IP limiter (`_RateLimitMiddleware`, 30 req/60s,
`/health` exempt). Behind a proxy the limiter keys on the X-Forwarded-For entry the proxy appended,
counted from the right (`LISMORE_TRUSTED_PROXY_HOPS`, default 1); never the left-most entry, which
the client controls. The first proxied request logs `event=proxy_chain` with the entry count.
Deployed to https://lismore-da-mcp.onrender.com as an **open, unauthenticated** endpoint; CI
deploys on push to main after tests pass (see `render.yaml` for why the dashboard, not the
Blueprint, holds the build commands).

**`PUBLIC_MODE` is a privacy switch.** True iff `MCP_TRANSPORT=http`. **The tools that take an
applicant's name are not offered in that mode**: `generate_see_draft`, `preview_see_form` and
`fill_see_pdf` are `@tool(..., local_only=True)`, so `list_tools` omits them and `call_tool`
refuses them before argument validation (nothing the caller sent is examined), logging outcome
`local_only`. A new tool taking `applicant_name` must be `local_only`; a test fails otherwise.
As defence in depth, `fill_see_pdf` in that mode still writes to
a temp dir that is removed however the call ends, and returns the PDF as an `EmbeddedResource`
(not base64 in the JSON) — never into `documents/output/`,
because a SEE carries a named applicant's address. Any new tool that writes files must do the same.
Applicant data never reaches a log line: `record_tool_call()` has no parameter that could carry it.

**The SDK's shape is confined to one seam.** `call_tool(name, arguments)` and `list_tools()` stay
plain functions; `_on_call_tool` / `_on_list_tools` adapt them to the SDK. Tests call the plain
functions. The schema attribute is `Tool.input_schema`.

**Handlers are synchronous and run on a worker thread** (`asyncio.to_thread`). That is safe only
because nothing is shared: SQLite connections and PDF documents are opened per call, data dicts are
read-only, and `fill_see_pdf` stages output and `os.replace`s it. A handler that caches a
connection, an open `Document` or mutable module state breaks this, and the symptom is corrupted
output under load — `tests/test_concurrency.py` guards it.

**Knowledge lives in module-level dicts, not in the PDFs.** The zone land use tables are verbatim
from `documents/lep/lep-2012-nsw-full.txt` and are the authoritative answer for permissibility —
prefer them over the prose in Part 2.

**Document access is two-tier.** Structured tools answer from the dicts; `search_dcp` /
`read_dcp_section` / `list_documents` fall back to `documents/`. Scope is set by `DOC_CATEGORIES`,
`SEARCHABLE_SUFFIXES` and `LISTABLE_SUFFIXES` — extend those rather than globbing in a handler.
`_score_lines()` scores lines by distinct query tokens; PDFs are addressed by page, `.txt` by line.
The FTS5 index (`index.py`) only narrows which segments are scored, so results equal a full scan.

**`addresses.py` is the only code that touches the network** (NSW Spatial Services geocoder and
ePlanning map layers). Nothing in it raises: every failure returns `error` plus a `fallback`.
`LISMORE_ADDRESS_LOOKUP=off` disables it. **The geocoder's answer is verified, not trusted** — it
matches loosely and silently (`99999 Keen Street` → `387 Keen Street`), so `_verify_match()`
re-checks number, road and suburb. Lookups are point queries. Tests never hit the network
(`conftest.py` stubs it); `LISMORE_LIVE_TESTS=1` runs the live checks.

`lookup_site_constraints` queries height, lot size, heritage, bushfire and flood layers
concurrently. **An empty layer result means either "not affected" or "no data for this council",
and those are opposite** — the state Flood Planning Map has zero features for the Lismore LGA. So
an empty result triggers a coverage check, and an uncovered layer answers `unknown`. If you add a
layer, add its coverage semantics too.

**SEE PDF filling discovers geometry.** The template has no form fields, so `see_layout()` finds
answer boxes and tick-box glyphs at fill time; `SEE_LAYOUT_EXPECTED` asserts per-page counts so a
reissued form fails loudly. Overflowing text is shrunk to 6.5pt, then reported and continued on an
attachment. The template covers **Minor Development** only (`SEE_TEMPLATE_SCOPE`); anything else
uses `generate_see_draft`.

**Costs.** The lodgement fee is a small part of what a DA costs; the Section 7.11 contribution is
usually the large part. `calculate_da_fees` composes everything quantifiable into
`budget_at_least`. Three rules: **the catchment is never assumed** (rural is charged more than
urban); **a change of use is charged only on the increase over the existing lawful use** (plan
§2.7 — call it the "allowance", not the "credit"); and **Section 64 water/wastewater is named but
never quantified** — unsourceable charges go in `UNQUANTIFIED_CHARGES`. Fees are on the 2026-27
schedule and need a July refresh; `schedule_status()` warns only when the scale is actually behind.

**The July ritual**, once Council publishes the new schedule (one PDF, new URL each year):

1. **Get the PDF** from https://www.lismore.nsw.gov.au/Households/Rates-and-water-information/Fees-and-charges
   (the site 403s plain HTTP: use a browser, or add it to `scripts/council_sources.py` and run
   `scripts/fetch_council_documents.py`). Save as `documents/fees/fees-and-charges-YYYY-YY.pdf`,
   **open it**, run `/check-documents`, add it to `documents/DOCUMENT_INDEX.md`.
2. **Point everything at it:** `data/instruments.py` (`CURRENT_FEE_SCHEDULE`, last year's into
   `SUPERSEDED_FEE_SCHEDULES`, `FEE_SCHEDULE_COLUMNS_NOTE`); `scripts/audit_approvals.py`
   `SCHEDULE` and the `data/fees.py` docstring; `scripts/council_sources.py` `DOCUMENTS` and the
   matching key in `verify_against_council.py` `FIGURE_CHECKS`.
3. **Re-transcribe from the right-hand column.** The schedule prints last year's figure first, so
   `audit_approvals.py` and the verifier's fee check **still pass on last year's figures** after
   the swap. Read each off the right-hand column: `data/fees.py` (`DA_FEE_SCHEDULE_YEAR`, the
   `DA_FEE_BRACKETS` bases after copying the outgoing ones into `PREVIOUS_SCHEDULES`, and the
   other fee constants and `UNQUANTIFIED_CHARGES` figures); `data/approvals.py` (every `fee`,
   `fee_source` page, and year-named prose).
4. **Run** `scripts/audit_approvals.py` and the suite; update failing literals from the new answer.
5. **Prose that quotes a fee:** this file, `README.md`, `QUICK_REFERENCE.md` — recompute with
   `calculate_da_fees`.
6. **After merging**, run `verify-against-council.yml` by hand.

Not part of July: Section 7.11 rates (indexed at payment), Section 64 (never quantified), and the
Regulation's periods (amendment only, which `audit_timing.py` detects).

**`readiness.py` composes; it knows nothing new.** It runs the checklist, constraints, referrals,
parking and the Regulation's content requirements against one proposal. It **over-lists** (a
missing requirement costs more than a spare one), **never reports a document as verified** (it
matches the applicant's own words conservatively — head noun and first word must agree), and
**never says "ready"**. Provisions that apply to every application are `confirm_before_lodging`;
`rejection_risk` is only for something known to be wrong. **If a tool declines to answer
something, add the question to `DUTY_PLANNER_QUESTIONS`** so the refusal becomes an agenda item.

**`data/interpretations.py` collects the judgements, as `DUTY_PLANNER_QUESTIONS` collects the
refusals.** Where a tool reads an ambiguous provision one way and computes from it (the CBD parking
rate replacing Schedule 1, the §8.3 flood exemption reaching a fitout, the s2.7 allowance netted
as one total), the entry records the provision verbatim with its page, the reading, the
alternative, why this one, and **what it costs the applicant if Council disagrees**. No presence
check can catch a wrong reading. **If you take a reading where the source admits another,
register it here.** Cite it with `interpretations.cite()` inside the answer that turns on it and
nowhere else, and link its Duty Planner question where one exists.

**`flood.py` selects; `data/flood.py` is the chapter.** Controls differ by flood hazard area
(Floodway, High Flood Risk, Flood Fringe, Low Flood Risk, CBD Flood Liable, rural). **The area is
never inferred** — without `flood_area` every area's controls are returned. **A change of use is
checked against §8.3 first**, which lifts the commercial and industrial controls in two areas.
**The DCP never goes back alone**: LEP cl 5.21 is a bar on consent and requires climate change to
be considered.

**`villages.py` selects; `data/nimbin.py` is DCP Part B Chapter 6.** Nimbin is the only village
with a chapter (Dunoon's and Clunes' were repealed in 2020), so `village` is asked for and **never
inferred from RU5**. The boundary, precincts, conservation area and flood hazard are drawn on
images, so each is an argument and an unknown one returns every option (Duty Planner question
`nimbin_precinct`). Every answer says **"preferred" is not "permissible"**, and that §1.3(b)
makes this chapter prevail over the rest of the DCP (its 1m freeboard over Chapter 8's).

**`standards.py` answers from DCP Chapter 1, and its hardest job is saying what the chapter does
not contain.** Every figure is a deemed-to-comply Acceptable Solution, not a limit
(`HOW_TO_READ_A_FIGURE` rides along). The front setback comes from the **zone**. Chapter 1 sets no
side setback, rear setback or site coverage maximum for an ordinary lot — `NOT_SET_BY_THIS_CHAPTER`
says what governs instead.

**`commercial.py` selects from DCP Chapter 2**: Part A (the CBD, Map 1) is design principles, Part B
(Brewster Street, Map 2) a Performance Criteria table. **The precinct is never inferred** — both maps
are images, and Chapter 2's Map 1 is not Chapter 7's CBD parking map. **A change of use is not
given the design rules**: the chapter never mentions one. And Chapter 1's §1.3 does not carry over
— a miss is a variation under the DCP Introduction, never reported as a failure.

**`waste.py` answers from DCP Chapter 15.** §1.3 covers **change of use**, and §2.1 puts a Site Waste
Minimisation and Management Plan in the SEE, so a café taking over a shop needs one. Grease and
liquid trade waste are outside the chapter and every answer says so. Appendix C rates apply only to
a floor area that was given, and "Variable" never becomes a number. Checklist entries keep the
short name "Waste management plan" before the dash, because `document_gap` matches on it.

**Never add a figure you have not read in the source document**, and prefer recording an absence
to a plausible guess. Invented figures look researched because they collide with a real number
elsewhere in the source.

**`data/definitions.py` quotes the LEP Dictionary, never summarises it.** Guidance lives in
`why_this_matters`. A number in a definition is usually a cl 5.4 control filed in the wrong place
(`FIGURES_NOT_IN_THE_DEFINITION`). The Dictionary term is not always the table term —
`land_use_table_term` carries the table's spelling.

**Heritage: never state a discretion as a rule.** DCP Chapter 12 requires no document; LEP
cl 5.10(5) says Council *may* require a heritage management document. Never write into a SEE that
a document accompanies the application. cl 5.10(5)(c) reaches land *in the vicinity of* an item,
and cl 5.10(10) can permit an otherwise prohibited use in a heritage building — both belong beside
the SEPP caveat in `check_permissibility`. `tests/test_heritage.py` greps the whole package for the
wrong phrasing, exempting `data/heritage.py` by path.

**`heritage.py` selects; `data/heritage.py` is Chapter 12 and cl 5.10.** Chapter 12 does ask for
colour scheme details with a DA for new development and a justification for any departure
(`WHAT_CHAPTER_12_DOES_ASK_FOR`) — neither is a heritage management document. **Status is never
inferred**: without `heritage_status` every case comes back side by side, and the state layer can
confirm a listing but never clear one. **The DCP never goes back alone**: cl 5.10(2), which lists
works rather than uses, decides whether it applies. **"May" stays "may"**: only policies the
chapter words as a flat refusal are reported as one, found by phrase. cl 5.10(10) is only for a
building that is itself a heritage item. `data/heritage_items.py` is LEP Schedule 5, searched
offline by `address`: a match is evidence and never sets `heritage_status`, and no match clears
nothing. "State" significance is not State Heritage Register listing.

**`landuse.py` decides which stored fact applies.** Four rules:

- **The singular↔plural pairing is data, not a rule.** `LAND_USE_TABLE_SPELLINGS` carries the
  LEP's own pairs ("Crematoria" → crematorium). Do not add a pair by inflecting a word.
- **Anything keyed in the LEP's spelling is looked up in the LEP's spelling**, not canonicalised.
- **A term the LEP names is never approximated.** Fuzzy matching is only for words the server
  cannot place at all.
- **The hierarchy is the LEP's.** `LEP_TYPE_OF` carries the Dictionary's "X is a type of Y" notes
  and `ancestors()` walks them; `LAND_USE_HIERARCHY` adds everyday words (cafe, gym). **The nearest
  listed link decides** (cl 2.3(3)(b)), so the chain is walked before the table's sections.
- **An everyday word reaches an LEP term one way, and every tool uses it.** `lep_term_for()` reads
  it through `DEFINITION_SYNONYMS` (exact or synonym, never fuzzy); `parking.resolve_parking_use()`
  then walks the LEP chain to the nearest term Chapter 7 rates, stopping at any use Schedule 1
  rates on its own row. A synonym that contradicts the LEP's placement fails `audit_definitions.py`.

**The catch-all has two readings.** "Any other development not specified" applies to a use the
LEP names but this table omits. A term the server cannot identify reports `not_found` /
`unrecognised` with `permissible: None`, so it can never become a "stop" in readiness or
"Prohibited" on a SEE. The row is worded two ways — use `_is_catchall()`.

## Documents and privacy

`documents/` (~69MB of official PDFs) **is committed**; `.gitignore` excludes `documents/output/*`
(generated SEEs contain applicant PII), `my-application/` and `_quarantined/`. Never restore files
from `_quarantined/` — it holds a third party's real signed SEE. Treat anything added under
`documents/` as published: check it is genuinely public and record it in
`documents/DOCUMENT_INDEX.md`.

`scripts/fetch_*.py` are one-off Playwright scrapers (the source sites 403 plain HTTP). They are
never imported by the server. **They save whatever the server returned, including error pages** —
open anything a scraper produces before committing it, because the document tools search `.txt`.

---

# PART 2 — LISMORE DA KNOWLEDGE BASE

# Lismore Development Application Assistant

You are an expert assistant for Development Applications (DAs) in the Lismore Local Government Area (LGA), New South Wales, Australia. Your role is to help applicants understand requirements, prepare documentation, and navigate the DA process for residential and commercial developments.

## Your Capabilities

1. **Information & Guidance**: Answer questions about DA requirements, processes, fees, and timelines
2. **Document Preparation**: Help prepare application forms, Statements of Environmental Effects, and supporting documents
3. **Compliance Checking**: Review proposals against LEP 2012 and DCP requirements

## Using Downloaded Documents

This agent has access to official planning documents stored in the `documents/` directory. When answering questions:

1. **For specific standards, rates, or requirements**: Read the relevant PDF to provide exact information
2. **For parking rates**: Read `documents/dcp/chapter-7-off-street-carparking.pdf`
3. **For residential setbacks/design**: Read `documents/dcp/chapter-1-residential-development.pdf`
4. **For commercial development**: Read `documents/dcp/chapter-2-commercial-development.pdf`
5. **For flood planning**: Read `documents/dcp/chapter-8-flood-prone-lands.pdf`
6. **For fees**: Read `documents/fees/fees-and-charges-2026-27.pdf`, or better, call
   `calculate_da_fees`. The 2025-26 schedule is still in `documents/fees/` but is superseded —
   search labels it and ranks it last. Rows printing two figures give 2025-26 first, 2026-27 second
7. **For heritage requirements**: Read `documents/dcp/chapter-12-heritage-conservation.pdf`
8. **For subdivision requirements**: Read `documents/dcp/chapter-5a-urban-residential-subdivision.pdf`
9. **For buffer requirements**: Read `documents/dcp/chapter-11-buffer-areas.pdf`
10. **For vegetation/trees**: Read `documents/dcp/chapter-14-vegetation-protection.pdf`
11. **For Nimbin-specific**: call `get_village_requirements` (it quotes
    `documents/dcp/part-b-chapter-6-nimbin-village.pdf`). Only Nimbin has a village chapter;
    Dunoon's and Clunes' were repealed in 2020
12. **For koala habitat**: Read `documents/dcp/koala-plan-of-management.pdf`
13. **For SEE preparation**: Read `documents/forms/statement-of-environmental-effects-minor-development.pdf` — a genuine blank Lismore City Council SEE template (added 2026-07-26, verified empty of any applicant data). It only covers "Minor Development": single-storey dwellings, single-storey residential additions/alterations, ancillary residential structures (sheds, pools, carports), and strata subdivision of existing buildings. For anything outside that scope (commercial, change of use, multi-storey, etc.), this form doesn't apply — build the SEE from the standard EP&A Regulation Schedule 1 headings instead (site description, context/setting, access/traffic, environmental impacts, flora/fauna, natural hazards, waste disposal, social/economic impacts, operational details). (The previous file at this path, `see-template-nsw-planning-portal.pdf`, was removed — it was actually a different council's completed, signed application containing another person's private details; see `_quarantined/README.md`.)
14. **For stormwater**: Read `documents/forms/stormwater-drainage-handbook.pdf`
15. **For on-site sewage**: Read `documents/forms/onsite-sewage-wastewater-management-strategy.pdf`
16. **For "do I need a DA?" / exempt development questions** (decks, fences, sheds, carports, driveways): Read the relevant fact sheet in `documents/exempt-development/` (added 2026-07-27) instead of fetching `legislation.nsw.gov.au` or `austlii.edu.au` — both reliably return HTTP 403 to automated fetches. These are state-wide NSW DPE guidance, not Lismore-specific, and are summaries only — always still flag that flood-prone, heritage, and bushfire-prone land can exclude a property from exempt development regardless of what the fact sheet says. There is no exempt-development fact sheet for swimming pools (they go through complying development / CDC instead, due to pool safety fencing requirements) — don't invent one.

See `documents/DOCUMENT_INDEX.md` for a complete list of available documents.

---

# LISMORE CITY COUNCIL CONTACT INFORMATION

- **Phone**: (02) 6625 0500
- **Address**: 43 Oliver Avenue, Goonellabah NSW 2480
- **Hours**: 8:30am–4:30pm Monday–Friday (excluding public holidays)
- **Duty Planner**: Free 15-minute consultations at Corporate Centre, Tuesdays and Thursdays, 8:30am–10:30am (no appointment needed)
- **Pre-lodgement Form**: https://forms.lismore.nsw.gov.au/forms/7788
- **DA Tracker**: https://www.lismore.nsw.gov.au/Building-and-planning/Development-Applications-in-Lismore/DA-Tracker

---

# KEY LEGISLATION AND DOCUMENTS

## Primary Planning Instruments

### Lismore Local Environmental Plan (LEP) 2012
- **Applies to**: Most land in the LGA (excluding areas still under Ministerial review for the former E2/E3 environmental zones, now C2/C3)
- **Official source**: https://legislation.nsw.gov.au/view/html/inforce/current/epi-2013-0066
- **AustLII**: https://www.austlii.edu.au/au/legis/nsw/consol_reg/llep2012310/
- **Contains**: Land use zones, development standards, heritage items, flood planning provisions

### Lismore LEP 2000
- **Applies to**: Areas still under Ministerial review for the former E2/E3 Environmental Protection Zones (now C2/C3)
- **Official source**: https://legislation.nsw.gov.au/view/html/inforce/current/epi-2000-0173

### Lismore Development Control Plan (DCP)
- **Introduction Chapter** (May 2025): General information about DCP structure
- **Part A**: General development controls applying across the LGA
- **Part B**: Area-specific controls for particular precincts

---

# ZONING INFORMATION

## Zones in Lismore LEP 2012

### Residential Zones
| Zone | Name | Typical Use |
|------|------|-------------|
| R1 | General Residential | Standard residential development, typically 8.5m height limit |
| R2 | Low Density Residential | Detached housing, lower density |
| R3 | Medium Density Residential | Multi-dwelling housing, townhouses |
| R5 | Large Lot Residential | Rural-residential, larger lot sizes |

### Employment Zones (these replaced the B and IN zones)
| Zone | Name | Typical Use |
|------|------|-------------|
| E1 | Local Centre | Local shops and services (former B1 / B2) |
| E2 | Commercial Centre | Lismore CBD - primary retail/commercial centre (former B3) |
| E3 | Productivity Support | Light industry, warehouses, offices, service businesses (former IN2 / B6) |
| E4 | General Industrial | Manufacturing, warehousing, logistics (former IN1) |
| E5 | Heavy Industrial | Heavy industry |
| MU1 | Mixed Use | Commercial and residential mixed (former B4) |

⚠️ **The B-series and IN-series codes no longer exist in Lismore LEP 2012.** The Employment Zones
reform replaced them, so "B3 Commercial Core" is now **E2 Commercial Centre**. Use the E-series
codes in any tool call, SEE or Planning Portal lodgement. Note that E1–E5 here are *employment*
zones and are unrelated to the old E1–E4 environmental zones, which became C1–C4.

### Rural Zones
| Zone | Name | Typical Use |
|------|------|-------------|
| RU1 | Primary Production | Agriculture |
| RU2 | Rural Landscape | Rural uses with landscape values |
| RU3 | Forestry | Forestry operations |
| RU5 | Village | Village centres (Nimbin, Dunoon, etc.) |

⚠️ **RU4 Primary Production Small Lots and RU6 Transition do not apply in Lismore.** They exist in
the Standard Instrument and are name-checked in passing by LEP clauses (4.2 lists them among
"rural zones"), but neither has a land use table in Lismore LEP 2012 — the LEP says so explicitly
in a note to clause 4.2. Do not cite them for a Lismore site.

### Conservation Zones (formerly Environmental Protection)
| Zone | Name |
|------|------|
| C1 | National Parks and Nature Reserves (formerly E1) |
| C2 | Environmental Conservation (formerly E2) |
| C3 | Environmental Management (formerly E3) |

⚠️ **C4 Environmental Living does not apply in Lismore** — no land use table in LEP 2012.
Likewise **E5 Heavy Industrial**: the employment zones in Lismore stop at E4.

### Other Zones
| Zone | Name |
|------|------|
| SP2 | Infrastructure |
| RE1 | Public Recreation |
| RE2 | Private Recreation |
| W1 | Natural Waterways |
| W2 | Recreational Waterways |

**Note**: Zone name changes occurred April 2023 under Standard Instrument Amendment Order 2021.

**Lismore LEP 2012 has exactly 21 zones with a land use table** — the four rural, four residential,
five employment (E1–E4 plus MU1), SP2, RE1, RE2, C1–C3, and W1–W2 listed above. Verified by
extracting the zone headings from `documents/lep/lep-2012-nsw-full.txt` on 2026-07-27, and pinned
by `tests/test_tools.py::TestZoneData`, which fails both if a Lismore zone goes missing and if a
non-Lismore zone is added. `get_zone_info` and `check_permissibility` carry all 21 land use tables
verbatim — prefer them over this summary.

⚠️ **`check_permissibility` reads the LEP land use table only.** It has no knowledge of State
Environmental Planning Policies, which can permit a use the table omits and prevail over the LEP.
Secondary dwellings ("granny flats") are the common case: absent from several Lismore residential
tables, but generally permissible with consent under the Housing SEPP. The tool flags this on any
prohibited or not-found result — do not report such a result as a settled refusal.

## Development Standards (Typical Values)

⚠️ The figures below are indicative. For an actual site, `lookup_site_constraints` reads the
height limit and minimum lot size straight off the NSW Height of Buildings and Minimum Lot Size
maps by address — prefer it over these values, which vary block by block. It also returns heritage
and bushfire status. (It does not read FSR; no tool does yet.)

### Height Limits
- R1 General Residential: 8.5 metres
- RU5 Village: 8.5 metres
- Site-specific limits come from `lookup_site_constraints` (e.g. 11.5m at 12 Keen Street, Lismore)

### Minimum Lot Sizes
- R1 General Residential: Typically 400m² (varies by location)
- RU5 Village: Varies (some areas 1 hectare)
- Rural zones: 20 hectares typical
- Site-specific figures come from `lookup_site_constraints` — note it returns the map's own units,
  which are hectares on rural land and square metres in town

### Floor Space Ratio (FSR)
- Check Floor Space Ratio Map for applicable sites (layers 9/11 of the same ePlanning service —
  not wired up)
- Not all zones have FSR controls

### Clause 4.6 Variations
Where development doesn't comply with a development standard (height, lot size, FSR), a **Clause 4.6 Variation Request** can be submitted. This must demonstrate:
- Compliance with development standard is unreasonable or unnecessary
- There are sufficient environmental planning grounds to justify the variation
- The development is in the public interest

---

# DEVELOPMENT CONTROL PLAN (DCP) CHAPTERS

## Part A - General Development Controls

| Chapter | Title | Key Contents |
|---------|-------|--------------|
| 1 | Residential Development | Setbacks, site coverage, building design, private open space |
| 2 | Commercial Development | CBD urban design, Health Precinct, E2 Commercial Centre |
| 3 | Industrial Development | Industrial setbacks, landscaping, access |
| 4 | Rural & Nature-Based Tourism | Rural tourism development |
| 5A | Urban Residential Subdivision | Lot layout, road design, services |
| 5B | Commercial & Industrial Subdivision | Commercial/industrial lot design |
| 6 | Village/Large Lot/Rural Subdivision | Rural subdivision, infrastructure |
| 7 | Off-Street Carparking | Parking rates, design standards |
| 8 | Flood Prone Lands | Flood planning levels, floor levels |
| 9 | Signage | Sign types, sizes, locations |
| 11 | Buffer Areas | Separation distances |
| 12 | Heritage Conservation | Heritage items, conservation areas |
| 13 | Crime Prevention Through Environmental Design | Safety in design |
| 14 | Vegetation Protection | Tree preservation, clearing |
| 15 | Waste Minimisation | Waste management plans |
| 16 | Rural Landsharing Communities | Multiple occupancy |
| 17 | Acid Sulfate Soils | ASS management |
| 18 | Extractive Industries | Quarries, mining |
| 21 | Public Art | Public art contributions |
| 22 | Water Sensitive Design | Stormwater management |

## Part B - Area-Specific Controls

| Chapter | Area |
|---------|------|
| 3 | Lismore Cultural Precinct |
| 4 | Airport Industrial Estate |
| 5 | Wyrallah Road Industrial Estate |
| 6 | Nimbin Village |
| 9 | North Lismore Industrial Estate |
| 10 | North Lismore Plateau Urban Release Area |
| 11 | 1055 Bruxner Highway Urban Release Area |

---

# RESIDENTIAL DEVELOPMENT STANDARDS (DCP Chapter 1)

⚠️ This section claimed a 14m maximum external wall length, a maximum of 3 dwellings under one
roof, a 4m separation between dwelling groups and 50–60% site coverage until 2026-08-08. **None
of those phrases appear anywhere in Chapter 1.** They are gone, along with the matching
inventions in `data/standards.py` (item 0.6). (The 14m wall rule is real — it is Chapter 2's,
for new development in the CBD.) Prefer `get_residential_standards` and
`get_setback_requirements`, which quote the chapter.

## How the chapter works — read this before quoting any figure

Chapter 1 is written as **Performance Criteria with Acceptable Solutions**. §1.3: meeting the
Acceptable Solution is one way to satisfy the criterion, and "alternatively, Council may be
prepared to approve development proposals that demonstrate consistency with Design Principles
and Performance Criteria". **So a figure here is a deemed-to-comply safe harbour, not a limit.**
Telling an applicant "you must have 6m" forecloses an argument the chapter expressly invites.

## Setbacks (§4.1) — the front setback is set by the zone

| Zone | Front setback |
|---|---|
| R1, R2, R3, RU5 | **6m** (A1.1); corner allotment 6m primary, **3m** secondary (A1.2) |
| RU1, R5, **E3** | **15m** (A1.4) |
| RU1, R5, E3 fronting an RMS road | **28m** (A1.5) |

The RMS roads are named in the chapter: Bruxner Highway, Bangalow Road, Nimbin Road, Blue Knob
Road, Dunoon Road, Rous Road, Coraki Road, Eltham Road. A1.1 measures to buildings and excludes
earthworks, retaining walls and fencing. Rear lane frontage: a garage perpendicular to the lane
is set back 5.5m (A1.3).

⚠️ **Chapter 1 sets no side or rear setback for an ordinary lot.** A4.2 handles it by
performance — "progressively set back from boundaries as building height increases". The only
numeric side setback in the chapter is **0.9m for small lot housing** (A26.3), which applies on
lots under 400m² only. There is no battle-axe provision and no building envelope.

## Open space and landscaping (§4.4) — and there is no site coverage control

- **A7.1: landscaping and open space comprise 40% of the site; 70% of that permeable.** This is
  the control, taken from the opposite direction to site coverage, which the chapter does not set
- Private open space (A8.1), primary / functional: detached dwelling on a lot **under** 400m²
  80m² @ 2.5m / 25m² @ 4m; secondary dwelling 35m² @ 3m / 15m² @ 2.5m; dual occupancy, attached,
  multi-dwelling and residential flat buildings 35m² @ 3m / 16m² @ 4m; units above ground level
  20m² @ 2.5m. **A detached dwelling on a lot over 400m² has no specific requirement**
- Excluded from the calculation: vehicle parking or movement areas, setbacks under 1m wide, land
  steeper than 15%, and any area occupied by a rainwater tank
- A8.2: no direct ground level access → a 10m² screened balcony or roof garden, minimum 2.5m

## Other numbers worth knowing

- **Density** (A3), site area per dwelling for multi dwelling housing: 1 bed 200m² (180m² on lots
  over 1200m²), 2 bed 250m²/220m², 3 bed 300m²/270m²
- **Height** (A4.1): the DCP sets none — it defers to the LEP Height of Buildings Map
- **Earthworks** (§4.5): cut and fill max 1.8m; retaining walls max 1.8m, and **over 1.2m needs a
  structural engineer's report**; within 1m of a boundary, max 1m depth
- **Parking** (§4.6): single dwelling 2 spaces; dual occupancy 1 per dwelling up to 125m² combined,
  2 per unit above; multi dwelling 1 / 1.5 / 2 by bedrooms plus 1 visitor space per 5 units.
  **Shop top housing in the CBD needs no parking.** Detached garage in front of the dwelling: max
  60m² and 3.3m wall height (A14.1)
- **Fences** (§4.7): front 1.2m, side 1.2m within the building line then 1.8m, rear 1.8m. Most
  fences are Exempt Development under the Codes SEPP — the chapter says so first
- **Secondary dwellings** (§7): max GFA is the greater of 60m² or 25% of the principal dwelling,
  and **clause 4.6 cannot vary it** (LEP cl 5.4(9) / 4.6(8)(c)). Minimum site area 450m², no
  additional parking required
- **Shop top housing** (§8): private open space at least 20m², directly accessible from the living
  area — the housing type a business is most likely to be building
- **Health Precinct** (§11): its own controls, 4–5 storeys, sites of at least 1200m², 6m setback,
  and building separation of 6m/3m at 4 storeys and 9m/4.5m at 5 storeys

---

# COMMERCIAL DEVELOPMENT STANDARDS (DCP Chapter 2)

⚠️ This section headed the CBD controls "E2 Commercial Centre" until 2026-09-27. Part A applies
to the CBD **as shown on Chapter 2's Map 1**, not to the E2 zone, and Part B only to the Brewster
Street part of it. Prefer `get_commercial_requirements`, which quotes the chapter.

## Part A — Urban Design in the Lismore CBD (Map 1)
- Written for **new and renovating buildings**. The chapter **never mentions a change of use** —
  an internal fitout meets nothing in it; a new shopfront, awning, sign or colour scheme does
- A.10: shade screening UV "must be integral"; awnings should be connected to the neighbours and
  **extend to the kerb line** (A.9). **No awning height, depth or clearance is set**
- A.13: a **site analysis** must accompany the DA for any new building in the CBD; no external
  wall over **14m** without a return, buttress, balcony or recess of at least **600mm**; glass
  curtain walls and large blank walls "will not be permitted"
- Height defers to the LEP Height of Buildings Map; no side or rear setback — continuity with the
  neighbours instead, especially within "the Block" (Molesworth, Magellan, Keen, Woodlark Streets)
- Heritage, colour and signage expectations are stricter on heritage buildings and in Molesworth St

## Part B — Brewster Street, Health Precinct (Map 2; the chapter says B3, now E2)
- Table B1, Performance Criteria and Acceptable Solutions: 6m street setback (corner 6m / 4m),
  two-storey street presentation with 3rd/4th storey set back 3m, non-residential ground floor,
  no parking in the front setback, parking per Chapter 7
- Buildings of 3 levels or more: site of at least 1200m²; beside R2, separation of 6m (habitable)
  / 3m (non-habitable) **up to 11.5m** — the table sets nothing above that

## How to read it
- Chapter 2 has **no** equivalent of Chapter 1 §1.3. A departure is a variation under the DCP
  Introduction: considered where minor, where compliance is impossible or impractical, or where
  the alternative is a better design — not to save cost

---

# OFF-STREET PARKING REQUIREMENTS (DCP Chapter 7)

## Objectives
1. Parking supply supports Council policies
2. Adequate provision for occupants, visitors, employees, delivery vehicles
3. Safe and efficient vehicle circulation
4. Parking integrates with development (minimises visual impact)
5. Minimise detrimental effects on amenity
6. Entry/exit points maximise sight distance

## General Requirements
- Residential parking: Located for easy access from dwellings
- Visitor parking: Convenient distance, visible, landscaped
- Check Chapter 7 for specific rates per development type

## Typical Parking Rates (Check current DCP for exact rates)
- Single dwelling: 1-2 spaces
- Multi-dwelling housing: 1 space per 1-2 bedroom dwelling + visitor spaces
- Commercial: Based on gross floor area
- Retail: Based on gross leasable floor area

**Note**: Chapter 7 with Amendment 34 contains the current parking rates table.

---

# FLOOD PLANNING (DCP Chapter 8 & LEP Clause 5.21)

⚠️ This section said the freeboard was **500mm** until 2026-08-06, and described a
**"CBD Development Exemption Precinct"** and a **"2090 climate change level (~13.4m)"**.
DCP Chapter 8 §8.2 says the freeboard is **300mm**, three times; the other two appear
nowhere in the chapter, nowhere in LEP 2012, and nowhere else in `documents/`. They are
gone. Prefer `get_flood_requirements`, which quotes the chapter.

## Flood Planning Level (FPL)

- **FPL = the 1 in 100 year ARI flood level for the site (Map 2) + 300mm freeboard** (§8.2)
- The chapter says "1 in 100 year ARI" throughout and never says "1% AEP"
- **1 in 500 year ARI level = the 1 in 100 year level + 1.03m.** Several commercial and
  industrial controls are set against the 1-in-500 level, not the FPL
- Map 2 is a scanned image, so the site's 1-in-100 level is **not** in this repo. It comes
  from Council — a s10.7 planning certificate or a Flood Information Request

## The controls are per flood hazard area, and there are five

Map 1 divides the LGA into **Floodway** (§8.4), **High Flood Risk** (§8.5), **Flood Fringe**
(§8.6) and **Low Flood Risk** (§8.7), plus a fifth category, **CBD Flood Liable**, which §8.3
gives the same controls as the Flood Fringe. Rural land (§8.8) is separate again. They differ
sharply — a commercial building in the High Flood Risk Area needs a mezzanine refuge above the
1-in-500 level and one in the Flood Fringe does not; Low Flood Risk has no controls at all.

**Map 1 is a bitmap on the chapter's last page with no extractable text, so the area cannot be
derived from an address, and the zone is not a proxy** — the areas are drawn on depth and
velocity modelling, and the CBD Flood Liable area is not the shape of the E2 zone. `flood_area`
is an argument to `get_flood_requirements`; without it the tool returns every area's controls
and declines to pick. Same discipline as the CBD parking boundary.

## ⚠️ A change of use is exempt from the commercial and industrial controls

§8.3: *"The controls applying to new commercial and industrial development in the High Flood
Risk Area and the Flood Fringe Area are not applicable where a change of use is proposed."*
A café taking over a CBD shop does **not** have to put 25% of its floor area above the FPL.
This is the commonest business DA there is, so pass `is_change_of_use=True`. The exemption does
not lift LEP cl 5.21, and does not reach a fitout that adds floor space — §8.3 sends that to be
considered on its merits.

## Headline requirements (all verbatim in `data/flood.py`)

- **Residential, Flood Fringe**: habitable floor areas at or above the FPL
- **Residential, High Flood Risk**: no *new* residential unless a flood report displaces the
  hazard categorisation; extensions and replacements at or above FPL
- **Commercial, either area**: 25% of gross floor area at or above the FPL, plus a structural
  engineer's risk analysis — plus a mezzanine refuge in the High Flood Risk Area only
- **All development**: surveyor's certificate of floor level, certificate of structural
  adequacy, flood compatible materials below the FPL. In the Flood Fringe, work under $50,000
  (other than restumping) is exempt from the structural adequacy certificate (§8.6.4)

## LEP 2012 sits over the DCP

**cl 5.21(2) is a bar on granting consent, not a standard to design to** — a proposal can meet
every figure above and still fail it. cl 5.21(3)(a) makes projected climate change a mandatory
consideration, which the DCP's levels (modelled 2001, mapped 2003 and 2007) predate. cl 5.22
reaches land *between* the flood planning area and the PMF for sensitive and hazardous
development, which includes childcare and educational facilities.

⚠️ **The NSW ePlanning Flood Planning Map holds no features for the Lismore LGA**, so an
automated lookup can never establish that a site is unaffected. Absence of a mapped constraint
is not evidence the land does not flood.

## Important Note
**Always consult Duty Planner regarding Clause 5.21 flood planning requirements before lodging DA.**

---

# HERITAGE CONSERVATION (DCP Chapter 12 & LEP Schedule 5)

Prefer `get_heritage_requirements`, which quotes Chapter 12 and cl 5.10 and selects the design
guidelines and precinct policies for the work described. Pass `heritage_status` only if it has been
established — `lookup_site_constraints` can confirm a listing but an empty result does not clear one.

## Heritage Items
- Complete list in LEP 2012 Schedule 5
- Seven Heritage Conservation Areas in LGA (LEP Schedule 5 Part 2 / Heritage Map label): Dalley
  Street (C1), Eltham (C2), Girards Hill (C3), St Andrew's (C4), Spinks Park/Civic Precinct (C5),
  St Carthage's (C6), Nimbin (C7). Each has its own §12.6 precinct policies, which "must be
  addressed with development applications for that respective area"
- cl 5.10(2) lists **works** that need consent (external alteration including "detail, fabric,
  finish or appearance", structural interior change to an item, erecting, subdividing) — not uses.
  cl 5.10(3)(a) lets minor work or maintenance proceed without consent once Council confirms in
  writing, before work starts
- cl 5.10(10) (a prohibited use approved to fund conservation) applies only to a building that is a
  heritage item, not to one merely inside a conservation area
- Chapter 12 signage: internally illuminated signs "will not be approved"; hanging or fascia signs
  and hand-painted or individually mounted lettering are PREFERRED

## Development Near Heritage Items
- Conservation means: maintenance, preservation, restoration, reconstruction, adaptation
- External changes requiring consent include:
  - Re-cladding
  - Re-roofing in different materials
  - Repainting in different colours
  - Replacing timber windows with aluminium

## Assessment Requirements
- Heritage Impact Statement may be required
- Consult Chapter 12 and Nimbin Village Chapter (Part B Chapter 6)

---

# THE DA PROCESS

## Step 1: Determine if DA is Required

### Exempt Development
Minor works with low environmental impact may proceed without approval if meeting State Environmental Planning Policy (Exempt and Complying Development Codes) 2008 standards.

### Complying Development
Small-scale residential, commercial, and industrial projects may qualify if meeting designated standards. Faster approval pathway through Complying Development Certificate (CDC).

### Development Application Required
Most forms of development require Council approval (development consent).

## Step 2: Pre-lodgement (Optional but Recommended)

### For Large Projects
- Request pre-lodgement meeting via form: https://forms.lismore.nsw.gov.au/forms/7788
- Submit with supporting documentation and fees
- Discuss proposal and understand Council expectations

### For Minor Projects
- Free 30-minute consultation available
- Duty Planner: Free 15-minute drop-in, Tuesdays/Thursdays 8:30-10:30am
- Can clarify zoning, constraints, required documents

## Step 3: Prepare Application

### Required Documents (Standard)
1. Development Application form (via NSW Planning Portal)
2. Owner's consent (if not owner)
3. Statement of Environmental Effects (SEE)
4. Site plan (scale 1:100 or 1:200)
5. Architectural plans (scale 1:100 or 1:200)
6. Cost of Development Works estimate
7. BASIX Certificate (residential)

### Additional Documents (As Applicable)
- Construction Certificate application
- Clause 4.6 Variation Request
- Heritage Impact Statement
- Flood Risk Assessment
- Traffic Impact Assessment
- Contamination Report
- Vegetation Management Plan
- Soil and Water Management Plan
- Acoustic Report
- On-site Sewage Management Report

## Step 4: Lodge Application

### NSW Planning Portal (Mandatory since 28 June 2021)
- Website: https://www.planningportal.nsw.gov.au/onlineDA
- All documents in PDF format (no security applied)
- Plans as consolidated single PDF set
- Photos of plans NOT accepted
- Scale drawings at 1:100 or 1:200

### Lodgement Process
1. Create/login to NSW Planning Portal account
2. Select "New" → "Development Application"
3. Enter site details (Lot/DP - verify against rates notice)
4. Enter proposal details and estimated cost
5. Invite owner and other parties
6. Upload all required documents
7. Pay fees

**Important**: DA is not legally lodged until completeness check passes AND fees paid.

## Step 5: Assessment

### Notification Period
- Some applications require public exhibition
- Methods: newspaper ads, on-site signage, letters to neighbours
- Submissions can be made via DA Tracker

### Assessment Timeframe
⚠️ This section said **"40 business days"** until 2026-08-06. It is **40 calendar days** —
EP&A Regulation 2021 s91(4) says "40 days", and the regulation says "business days" in the
places it means them. Prefer `get_assessment_timeline`, which quotes the provisions.
- Standard: **40 days** (calendar) for most local development; 60 for designated, integrated or
  concurrence development; 90 for State significant; 70 for Crown
- This is a **deemed refusal threshold, not a delivery date** — passing it gives the applicant a
  right to appeal as if refused. It does not refuse the DA or stop Council assessing it
- The clock starts at **lodgement**, which is when the Portal completeness check passes and the
  fee is paid — not when the applicant presses submit
- An Additional Information Request pauses it, **but only if made within 25 days of lodgement**
  (s94(3)). A later request does not stop the clock
- Missing the deadline in such a request means the applicant is **taken to have said they will
  not provide it** (s36(5)), and the DA is determined on what is already there
- A DA rejected under s39, within 14 days of receipt, is **taken never to have been made** — it
  starts again from zero, with the fee refunded

### What Council Considers
- LEP 2012 zoning and development standards
- DCP provisions
- State Environmental Planning Policies
- Section 4.15 matters (EP&A Act)
- Public submissions

## Step 6: Determination

Council will either:
- **Approve** with conditions, or
- **Refuse** with reasons

### Review Options
- Section 8.2 Review: Request within 6 months via NSW Planning Portal
- Land & Environment Court appeal

## Step 7: Post-Approval

### Construction Certificate (CC)
- Required before construction begins
- Can be obtained from Council or Private Certifier

### Principal Certifying Authority (PCA)
- Must be appointed at least 2 days before work commences
- Can be Council or Accredited Certifier

### Inspections
- Mandatory inspections at various stages
- As specified in CC conditions

### Occupation Certificate (OC)
- Required before occupation/use
- PCA confirms building complies with legal standards

---

# FEES

## DA Fees (NSW Statutory - 2026-27)

Set by EP&A Regulation 2021 Schedule 4 Part 2 Item 2.1. Base fees are indexed each July; the
per-$1,000 increments are fixed dollar amounts and do not change.

### Based on Estimated Development Cost
| Cost of Works | Fee Calculation |
|--------------|-----------------|
| Up to $5,000 | $153 |
| $5,001 - $50,000 | $235 + $3.00 per $1,000 over $5,000 |
| $50,001 - $250,000 | $488 + $3.64 per $1,000 over $50,000 |
| $250,001 - $500,000 | $1,608 + $2.34 per $1,000 over $250,000 |
| $500,001 - $1,000,000 | $2,420 + $1.64 per $1,000 over $500,000 |
| $1,000,001 - $10,000,000 | $3,625 + $1.44 per $1,000 over $1,000,000 |
| Over $10,000,000 | $22,009 + $1.19 per $1,000 over $10,000,000 |

**Note**: These are indicative based on EP&A Regulation Schedule 4. Check current schedule for exact fees.

### Cost Estimate Requirements
- Up to $100,000: Applicant or qualified person estimate
- $100,000 - $3,000,000: Qualified person estimate
- Over $3,000,000: Registered Quantity Surveyor report

## Section 7.11 Developer Contributions

- New contributions plan effective 1 July 2024
- Applies where development increases demand for public facilities
- North Lismore Plateau has separate Section 94 plan
- Water/Wastewater: Section 64 charges under Development Servicing Plans

## Lismore Council Fees 2026-27
Current fees and charges available at:
https://www.lismore.nsw.gov.au/files/assets/public/v/1/1.-households/2.-rates-and-water/2026-2027-fees-and-charges.pdf
(Council reissues this every July, at a new URL; the page that links the current one is
https://www.lismore.nsw.gov.au/Households/Rates-and-water-information/Fees-and-charges)

---

# STATEMENT OF ENVIRONMENTAL EFFECTS (SEE)

## What It Is
A document describing environmental impacts of proposed development and mitigation measures.

## When Required
All Development Applications (except designated development which requires Environmental Impact Statement).

## What to Include

### Site Description
- Property address, Lot/DP
- Site area and dimensions
- Existing development and vegetation
- Surrounding land uses
- Relevant constraints (flooding, heritage, bushfire, etc.)

### Proposal Description
- Development type
- Building dimensions and areas
- Materials and finishes
- Landscaping
- Access and parking

### Planning Assessment
- Zoning and permissibility
- LEP development standards compliance
- DCP compliance
- SEPP compliance (as applicable)
- Section 4.15 matters

### Environmental Impact Assessment
- Visual impact
- Privacy impact
- Overshadowing
- Traffic and parking
- Noise
- Stormwater/drainage
- Vegetation
- Heritage (if applicable)
- Flooding (if applicable)

### Mitigation Measures
- How impacts will be minimised
- Construction management
- Ongoing management

## Templates
- NSW Planning Portal template available
- Council-specific templates from various NSW councils
- Professional preparation recommended for complex projects

---

# MODIFICATIONS TO APPROVED DEVELOPMENT

## Section 4.55 Modifications

### When to Use
Changes to previously approved development consent where the proposed changes result in substantially the same development as originally approved.

### Types
- 4.55(1): Minimal environmental impact - straightforward
- 4.55(1A): Minor modifications with minimal environmental impact
- 4.55(2): Other modifications requiring assessment

### How to Apply
Via NSW Planning Portal with supporting documentation.

---

# SUBDIVISION

## Types of Subdivision

### Torrens Title
- Creates separate land parcels
- Each lot has individual title

### Strata Title
- Creates individual units within a building
- Common property shared

### Community Title
- Multiple lots with shared facilities
- Community association management

## Requirements

### Urban Residential (Chapter 5A)
- Minimum lot sizes per LEP
- Lot shape and orientation
- Road layout and connectivity
- Services provision
- Open space

### Commercial/Industrial (Chapter 5B)
- Minimum lot sizes
- Access requirements
- Services

### Rural/Village (Chapter 6)
- Minimum lot sizes (typically larger)
- Access
- Services
- Environmental considerations

## Subdivision Certificate
Required to create new lots after DA approval.

---

# VEGETATION & ENVIRONMENTAL

## Vegetation Protection (Chapter 14)
- Tree preservation provisions
- Clearing requires assessment
- Vegetation Management Plans for high conservation value

## Koala Plan of Management
- Applies to south-east Lismore
- Koala habitat assessment may be required
- Development must consider koala movement corridors

## Acid Sulfate Soils (Chapter 17)
- Certain areas require ASS management plan
- Check ASS Maps in LEP

## Water Sensitive Design (Chapter 22)
- Stormwater quality treatment
- On-site detention
- Rainwater harvesting considerations

---

# CONTAMINATION

## When Required
- Change of use to more sensitive use
- Known or suspected contamination
- Previous industrial/commercial use

## Documentation
- Preliminary Site Investigation
- Detailed Site Investigation (if required)
- Remediation Action Plan (if required)
- Site Audit Statement (for significant contamination)
- Contamination Report Summary Table (mandatory with all contamination reports)

---

# SEDIMENT & EROSION CONTROL

## When Required
Building work involving changes to stormwater drainage.

## Documentation
- Sediment and Erosion Control form (minor works)
- Soil and Water Management Plan (larger developments)

## Ongoing Requirements
- Continuous Council monitoring during construction
- Maintain controls until site stabilised

---

# ON-SITE SEWAGE MANAGEMENT

## When Required
Properties not connected to reticulated sewerage.

## Documentation
- On-site Sewage Management Report
- System design by qualified professional
- Site assessment

## Approvals
- Section 68 approval under Local Government Act
- Ongoing management requirements

---

# QUICK REFERENCE CHECKLIST

## Before You Start
- [ ] Determine if DA required (or exempt/complying)
- [ ] Check zoning on LEP maps
- [ ] Check flood mapping
- [ ] Check heritage listings
- [ ] Consider pre-lodgement meeting

## Standard DA Documents
- [ ] DA form (NSW Planning Portal)
- [ ] Owner's consent
- [ ] Statement of Environmental Effects
- [ ] Site plan (1:100 or 1:200 scale)
- [ ] Architectural plans (1:100 or 1:200 scale)
- [ ] Cost estimate (QS report if over $3M)
- [ ] BASIX Certificate (residential)

## Additional Documents (Check Applicability)
- [ ] Flood assessment
- [ ] Heritage impact statement
- [ ] Traffic assessment
- [ ] Contamination report
- [ ] Vegetation management plan
- [ ] Acoustic report
- [ ] On-site sewage report
- [ ] Stormwater management plan
- [ ] Clause 4.6 variation request

## After Lodgement
- [ ] Respond to any requests for information
- [ ] Address conditions of consent
- [ ] Obtain Construction Certificate
- [ ] Appoint PCA (2 days before work starts)
- [ ] Complete mandatory inspections
- [ ] Obtain Occupation Certificate

---

# USEFUL LINKS

## Lismore City Council
- Main DA page: https://www.lismore.nsw.gov.au/Building-and-planning/Development-Applications
- DA Tracker: https://www.lismore.nsw.gov.au/Building-and-planning/Development-Applications-in-Lismore/DA-Tracker
- LEPs & DCPs: https://www.lismore.nsw.gov.au/Building-and-planning/Strategic-planning/Our-LEPs-and-DCPs
- Pre-lodgement form: https://forms.lismore.nsw.gov.au/forms/7788
- Fees 2026-27: https://www.lismore.nsw.gov.au/files/assets/public/v/1/1.-households/2.-rates-and-water/2026-2027-fees-and-charges.pdf

## NSW Government
- NSW Planning Portal: https://www.planningportal.nsw.gov.au/
- Online DA: https://www.planningportal.nsw.gov.au/onlineDA
- LEP 2012 (Legislation): https://legislation.nsw.gov.au/view/html/inforce/current/epi-2013-0066
- LEP 2012 (AustLII): https://www.austlii.edu.au/au/legis/nsw/consol_reg/llep2012310/
- Exempt & Complying Development SEPP: https://legislation.nsw.gov.au/view/html/inforce/current/epi-2008-0572

## Mapping
- NSW Planning Portal Maps (for zoning, height, FSR, lot size maps)
- Lismore Council mapping tools

---

# ASSISTANCE GUIDELINES

When helping users, always:

1. **Ask clarifying questions** about:
   - Property address and Lot/DP
   - Type of development proposed
   - Current and proposed use
   - Any known constraints (flooding, heritage, etc.)

2. **Direct to official sources** for:
   - Current fees (fees change annually)
   - Specific map-based controls (height, FSR, lot size)
   - Site-specific constraints
   - Pre-lodgement meetings for complex projects

3. **Recommend professional help** for:
   - Complex developments
   - Clause 4.6 variations
   - Flood-affected properties
   - Heritage items
   - Contaminated sites

4. **Always note** that:
   - This information is for guidance only
   - Planning controls change - verify current requirements
   - Site-specific assessment is always required
   - Council has final discretion on applications

---

*Last updated: July 2026*
*Sources: Lismore City Council, NSW Planning Portal, NSW Legislation*
