# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This file has two halves:

- **Part 1 — Working on the code** (below): how to build, run and modify the MCP server.
- **Part 2 — Lismore DA knowledge base** (from "Lismore Development Application Assistant"
  onward): domain content loaded as context when *using* the agent to answer planning questions.
  Do not delete it when editing this file.

**Who this is for: local businesses in the Lismore LGA going through a DA** — opening, changing
use, fitting out or expanding — where the friction is between the business and Council. Not
primarily householders, though the server was largely built as though it were: the SEE form tooling,
residential standards and setback tools all target R zones, while a business is usually doing a
**change of use** in E1–E4, MU1 or RU5. See **`PLAN.md`** for what that reframing implies and what
is being done about it; read it before picking up work, because the previous plan
(`IMPROVEMENT_PLAN.md`, deleted — `git show 4ded0a8:IMPROVEMENT_PLAN.md`) kept generating
engineering work that is no longer the constraint.

---

# PART 1 — WORKING ON THE CODE

## Commands

```bash
uv sync                                   # install deps into .venv (Python >=3.14)
uv sync --extra scraping                  # + httpx/playwright, only for scripts/fetch_*.py
# uv is not installed on every machine that runs this. The stdlib equivalent,
# and how the current .venv was built (Homebrew python@3.14, 2026-08-02):
python3.14 -m venv .venv && .venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m lismore_da_mcp.server # run the server over stdio (what .mcp.json launches)
MCP_TRANSPORT=http PYTHONPATH=src PORT=8080 \
  .venv/bin/python -m lismore_da_mcp.server   # run the public HTTP transport locally
curl localhost:8080/health                # → "ok"
```

## Repo tooling (`.claude/`, committed on purpose)

| | |
|---|---|
| `/check-documents` | Validates `documents/`: real PDFs, no error pages, right LEP edition, indexed, in a searched category. Also runs in CI. |
| `/smoke` | Drives the server with a real MCP client over **both** transports. The unit tests call handlers directly and CI only imports the HTTP app — neither opens a session, and two shipped bugs were visible only to a real client. |
| `planning-data-reviewer` agent | Checks transcribed data in `data/` against the source documents. The repo's core risk is that this data is hand-copied and nothing verifies it; the tests pin that it has not *changed*, not that it is *right*. |
| `scripts/audit_parking_rates.py` | Checks every parking requirement in `data/parking.py` still appears verbatim in DCP Chapter 7. Schedule 1 is a three-column PDF table that cannot be diffed structurally, so the rates are stored verbatim and presence-checked. All 22 entries were wrong before 2026-08-02. |
| `scripts/audit_zone_tables.py` | Diffs every zone land use table against `documents/lep/lep-2012-nsw-full.txt`. All 21 match as of 2026-08-02; `tests/test_zone_transcription.py` keeps it that way. Known defects in the *scraped source text* — three lost semicolons — are listed in `SOURCE_TEXT_DEFECTS` rather than silently tolerated. |
| `scripts/audit_timing.py` | Checks the assessment-period quotes in `data/timing.py` against `documents/legislation/epa-regulation-2021-assessment-periods.txt`, and that each stored figure matches its own quote. Unlike the others this guards against **the law changing**, not a transcription slipping — that text is a fetched snapshot of legislation.nsw.gov.au, so a mismatch means an amendment. |
| `scripts/audit_approvals.py` | Checks every dollar figure quoted in `data/approvals.py` still appears in Council's fees schedule, and that `SEQUENCE`/`BY_ACTIVITY` resolve. These are prose, not verbatim quotes, so the figures are what can be checked — and Council reissues the schedule every July, a refresh this repo has already missed twice. |
| `scripts/audit_readiness.py` | Checks the lodgement and rejection provisions in `data/readiness.py` against the fetched EP&A Regulation text, reusing `audit_timing.py`'s comparison. It also checks every paragraph of s39(1) is carried, reading the letters off the source rather than a hardcoded list — a list of five rejection grounds out of six reads as complete and is not. Like `audit_timing.py` it guards against **the law changing**. |
| `scripts/audit_signage.py` | Checks every DCP Chapter 9 definition, standard and general provision in `data/signage.py` still appears verbatim in the chapter, and reports any sign type §9.3 defines that the data does not carry. That last check found `business identification sign` and `building identification sign` missing — the two the §9.2 heritage exception turns on. |
| `scripts/audit_contributions.py` | Checks the Section 7.11 rates two ways: every figure still appears in the plan PDF, **and** all 30 cells of Table E2 rebuild from Table E1's components. The derivation catches a transposed digit that a presence check cannot, and it found one real discrepancy in the published table (`KNOWN_TABLE_DISCREPANCIES`). Prefer this shape wherever a source table has recoverable internal arithmetic. |
| `scripts/audit_standards.py` | Checks every DCP Chapter 1 quote in `data/standards.py` against the chapter, and reads the Acceptable Solution labels (A1.1, A26.3, …) off the document to report any the data does not carry. It also runs the check the others cannot: that the figures recorded in `NOT_SET_BY_THIS_CHAPTER` really are **absent**. A presence check only looks at what is stored, so it is structurally blind to invention — which is how this file came to assert a side setback, a site coverage maximum and a deep soil percentage that Chapter 1 does not contain. |
| `scripts/audit_flood.py` | Checks all 40 flood controls in `data/flood.py` against DCP Chapter 8 and the LEP text. Two checks beyond presence: the derived constants must agree with the quotes they were read from (the freeboard was wrong by 200mm and nothing noticed), and every numbered control in §8.4–§8.8 is counted off the document, so a requirement nobody transcribed is reported rather than invisible. |
| `scripts/audit_definitions.py` | Checks all 36 land use definitions in `data/definitions.py` against the LEP Dictionary, plus the clause 5.4 controls each carries. Beyond presence it checks each quote **opens with its own term** (verbatim LEP text lifted from the wrong entry passes a presence check), that `land_use_table_term` really is how `data/zones.py` spells the use, that `LAND_USE_HIERARCHY`'s first links agree with the LEP's own "X is a type of Y" notes — which caught `office premises` recorded as a type of business premises — and, like `audit_standards.py`, that the recorded inventions are still **absent**. |
| `scripts/audit_landuse_matching.py` | The only audit that checks a **tool** rather than a data file: it asks `check_permissibility` about all 991 land use rows in both the table's spelling and the LEP Dictionary's, and grades the answer against the table. Every other audit here would pass with the matching layer completely broken, which is how ROADMAP.md S1's defect survived 1,346 tests. The singular↔plural pairing is read off the Dictionary in the document, never computed — a candidate spelling the document does not confirm is discarded, so the audit can never grade the tool against a word that is not a land use. It also audits `LAND_USE_TABLE_SPELLINGS` itself, since S1's fix turned that pairing into stored data: every pair must be one the document yields, every pair the document yields must be stored, and every table spelling must appear verbatim in `data/zones.py` — a pair whose right-hand side is not a real table entry resolves onto nothing and reads exactly like one that works. |
| `scripts/verify_against_council.py` | The audits above check the data against the PDFs **in this repo**; this checks those PDFs are still what Council publishes. Re-downloads each, compares byte for byte, re-verifies every figure against the fresh copy, and crawls for documents we do not carry. Needs the `scraping` extra — the council site 403s plain HTTP. Never writes to `documents/`. |
| `protect-private-paths.py` hook | Hard-blocks `git add`/`commit` touching `documents/output/`, `my-application/` or `_quarantined/`. `.gitignore` covers the accident; the hook covers `-f`, a rewritten ignore file, and anyone who never read this file. |

`.claude/settings.local.json` stays out of git (per-machine permissions); everything else in
`.claude/` is shared, because a guardrail only one person has is not a guardrail.

There is no linter or formatter configured. Changes are verified by calling the
tools through an MCP client (the local `lismore-da` server from `.mcp.json`, or the deployed
`lismore-da-public`), or by importing `lismore_da_mcp.server` and calling handlers directly:

```bash
.venv/bin/python -c "
import asyncio, json
from lismore_da_mcp.server import call_tool
print(asyncio.run(call_tool('get_parking_rates', {'development_type': 'restaurant'}))[0].text)"
```

## Architecture

`src/lismore_da_mcp/server.py` is ~190 lines of wiring: it registers the SDK adapters, dispatches
tool calls, and re-exports much of the package so older `from lismore_da_mcp.server import X`
imports keep working. It is not where the code lives. Find things by module:

| Layer | Where | What |
|---|---|---|
| Facts | `data/` | Hand-transcribed source content: `zones`, `parking`, `contributions`, `fees`, `definitions`, `standards`, `referrals`, `flood`, `checklists`, `instruments`, `see_templates`, `signage`, `approvals`, `timing`, `readiness`, `contacts`. No logic. |
| Domain logic | `fees.py`, `contributions.py`, `parking.py`, `signage.py`, `approvals.py`, `timing.py`, `readiness.py`, `flood.py`, `standards.py`, `landuse.py`, `search.py`, `index.py`, `vocabulary.py`, `addresses.py` | Applies the facts. Handler-free and directly unit-testable. |
| Tools | `tools/` | One module per domain (`zoning`, `parking`, `signage`, `approvals`, `timing`, `readiness`, `fees`, `planning`, `documents`, `see`), each a thin handler carrying its own schema. |
| SEE form | `see/` | `fields`, `layout`, `fill`, `generate`, `parsers` for the Council PDF. |
| Plumbing | `registry.py`, `app.py`, `transport.py`, `observability.py`, `config.py` | Registration, the `Server` object, stdio/HTTP, logging, paths. |

A handler should stay thin: if it computes rather than formats, the computation belongs one layer
down, where it can be tested and reused. `generate_see_draft` is the cautionary example — it
hand-rolled a parking calculation instead of calling `parking.estimate_spaces`, and told an 80m²
café with no on-site parking that its parking was adequate against a real requirement of 14 spaces.

**Two transports, one server object.** `main()` branches on `MCP_TRANSPORT`: unset/`stdio` →
`stdio_server()` for local `.mcp.json` use; `http` → a Starlette app (`build_http_app()`) mounting
`StreamableHTTPSessionManager(stateless=True)` at `/mcp`, with `/health` and an in-process per-IP
rate limiter (`_RateLimitMiddleware`, 30 req/60s). `render.yaml` deploys the HTTP mode to
https://lismore-da-mcp.onrender.com as an **open, unauthenticated** endpoint.

**`PUBLIC_MODE` is a privacy switch, not just a transport flag.** It is `True` iff
`MCP_TRANSPORT=http`. In that mode `fill_see_pdf` must write to a per-request temp dir, return the
PDF inline (base64), and delete it — never into the shared `documents/output/` tree, because
generated SEEs contain a named applicant's address and would otherwise be readable by the next
caller. Any new tool that writes files must respect this branch.

**A tool is one decorated function that carries its own schema.** `registry.py` holds the `@tool`
decorator and the registry; `tools/` holds the handlers, one module per domain. Adding a tool means
writing the decorated function and updating the tool table in `README.md` — nothing else. (The old
shape, a `TOOLS` list plus a 1,000-line `if/elif` chain in `call_tool`, is gone.)

**`validate_arguments()` is the only gate on arguments.** It checks each call against that tool's
own schema — rejecting unknown arguments, missing/empty required ones, and wrong types — rather
than letting handlers `.get()` a default and answer confidently wrong. An empty `land_use` once
returned "permitted without consent", and a string where a number belonged reached `float()` and
surfaced as a raw `MCPError` reading "could not convert string to float". **The SDK does not
validate arguments; nothing checks them but this function**, so anything the schema can express
that it does not check is unenforced: `_JSON_TYPES` covers the type keyword only, and a test fails
if a schema declares a type it does not know.

**The SDK's shape is confined to one seam.** Handlers are registered by method name and take
`(context, params)`, returning typed results. `server.py` keeps `call_tool(name, arguments)` and
`list_tools()` as plain functions and wraps them in `_on_call_tool` / `_on_list_tools` adapters
registered via `add_request_handler`. Tests and `conftest` call the plain functions, so the next
SDK break lands in two adapters rather than across 800+ tests. Note the schema attribute is
`Tool.input_schema` (the wire format is unchanged — it is a pydantic alias), and handlers are
read back with `server.get_request_handler(method)`.

**Handlers are synchronous and run on a worker thread** — `call_tool` dispatches through
`asyncio.to_thread`. Every handler blocks (PDF extraction, SQLite, and HTTPS with an 8s timeout in
the address tools), so called inline each one held the single event loop thread for its whole
duration: the public deployment served one caller at a time and `/health` stalled behind whatever
tool was running. Five concurrent calls to a 0.3s handler took 1.51s before, 0.30s after.
`to_thread` beats making 23 handlers async because they are blocking by nature — `fitz` and
`sqlite3` have no async API. **This is safe only because nothing is shared:** `sqlite3.connect` and
`fitz.open` happen per call and never cross threads, the data dicts are read-only, and
`fill_see_pdf` stages its output beside the target and `os.replace`s it into place so two
concurrent fills to the same filename cannot interleave into a half-written PDF. If you add a
handler that caches a connection, an open `Document`, or any mutable module state, that assumption
breaks and the symptom will be corrupted output under load rather than an exception —
`tests/test_concurrency.py` guards it.

**Knowledge lives in module-level dicts, not in the PDFs.** `ZONES`, `PARKING_RATES`,
`LAND_USE_DEFINITIONS`, `RESIDENTIAL_STANDARDS`, `REFERRAL_REQUIREMENTS`, `FLOOD_PLANNING`,
`SEE_TEMPLATES`, `CONTACT_INFO` are hand-transcribed from the source documents. The zone land use
tables are transcribed verbatim from `documents/lep/lep-2012-nsw-full.txt` and are the
authoritative answer for permissibility — prefer them over the prose summaries in Part 2.

**Document access is two-tier.** Structured tools answer from the dicts; `search_dcp` /
`read_dcp_section` / `list_documents` fall back to the files under `documents/`. Scope is
centralised in `DOC_CATEGORIES` (dcp, lep, forms, fees, exempt-development, business, legislation) and
`SEARCHABLE_SUFFIXES` / `LISTABLE_SUFFIXES` — extend those rather than re-globbing in a handler.
`_score_lines()` scores lines by how many distinct query tokens they contain (stopwords dropped,
exact-phrase is only a ranking bonus) so partial concept matches still surface; `search_document()`
and `extract_document_section()` dispatch PDF vs `.txt` behind it. PDFs are addressed by page,
`.txt` extracts by line, and search results carry a `location` string that `read_dcp_section`
accepts either way.

**`addresses.py` is the only thing here that touches the network.** `lookup_zone_by_address`
geocodes an address via NSW Spatial Services and reads the zone off the NSW ePlanning Land Zoning
Map — the two free unauthenticated APIs behind the Planning Portal. Everything else answers
offline. Three rules hold it together: nothing in the module raises (every failure returns a
payload with `error` and a `fallback` telling the caller to read the zone off the Planning Portal
by hand, so an outage restores the server's previous behaviour rather than breaking a tool);
`LISMORE_ADDRESS_LOOKUP=off` disables it entirely; and **the geocoder's answer is verified, not
trusted**. It matches loosely and silently — `99999 Keen Street` comes back as `387 Keen Street`,
and a wrong suburb is ignored — both as `numRecs: 1`. `_verify_match()` re-checks number, road and
suburb against the response, because a zone for the wrong property flows straight into
`check_permissibility` and then into an SEE. Note it is a *point* query: a lot straddling a zone
boundary reports only the zone under its address point, which the result's caveat states. Tests
never hit the network — `tests/conftest.py` has an autouse fixture with canned responses; the live
checks in `tests/test_addresses.py::TestLive` are opt-in via `LISMORE_LIVE_TESTS=1` and should be
run after any change to the URLs or response fields.

`lookup_site_constraints` queries the sibling layers at the same point — Height of Buildings (14),
Minimum Lot Size (22), EPI Heritage (16), Bushfire Prone Land (Hazard 229) and Flood Planning
(Hazard 230) — concurrently, since handlers run inline in the async dispatcher and five serial
round trips would block it. One layer failing does not take the others with it. **The trap it
exists to avoid: an empty layer result means either "not affected" or "this dataset does not cover
this council", and those are opposite.** The state Flood Planning Map contains *zero features for
the entire Lismore LGA*, so a naive reading reports the CBD — inundated in 2022 — as not flood
affected. So an empty result triggers a per-layer coverage check (`LGA_NAME='LISMORE'`, cached per
process), and an uncovered layer answers `unknown` with an explicit "this is not evidence the site
is unaffected". Flood additionally always carries a Lismore-specific warning unless the site is
positively flagged. Bushfire Prone Land has no `LGA_NAME` column, so its coverage was verified by
hand instead (6,877 features across a Lismore bounding box, 2026-08-01). If you add a layer, add
its coverage semantics too — reporting a mapping gap as an absence of constraint is the failure
mode that matters here.

**SEE PDF filling discovers geometry instead of hardcoding coordinates.** The Lismore template has
no AcroForm fields, so `see_layout()` finds answer boxes (white-filled rects) and tick boxes
(Wingdings glyphs U+F0A8 / U+F071) at fill time and sorts them into reading order.
`SEE_FORM_FIELDS` addresses them as `{page, box|check: index}`. `SEE_LAYOUT_EXPECTED` asserts the
per-page box/checkbox counts so a reissued form fails loudly rather than silently writing text
into the wrong place. `_draw_single_line`/`_draw_wrapped` shrink text to `MIN_FONTSIZE` (6.5pt) and
report overflow; overflowed fields auto-tick the page-1 "supporting information attached" box.
`preview_see_form` renders what would be written; `fill_see_pdf` produces the file. The template
only covers **Minor Development** — `SEE_TEMPLATE_SCOPE` gates this, and out-of-scope proposals
must use `generate_see_draft` (free-form EP&A Schedule 1 headings) instead.

## Documents and privacy

`documents/` (~69MB of official PDFs) **is committed**; `.gitignore` deliberately excludes
`documents/output/*` (generated SEEs contain applicant PII), `my-application/` (the repo owner's
real details), and `_quarantined/`. `_quarantined/README.md` records a third party's real signed
SEE that was mistaken for a blank template — never restore files from there into `documents/`.
Treat any new document added under `documents/` as published: check it is genuinely blank/public
before committing, and record it in `documents/DOCUMENT_INDEX.md`.

The `scripts/fetch_*.py` scripts are one-off Playwright scrapers (legislation.nsw.gov.au,
austlii, planning.nsw.gov.au all return 403 to plain HTTP fetches). They are never imported by the
server and their deps stay in the `scraping` extra so Render doesn't ship browser binaries. **These
scripts save whatever the server returned, including 403/404 bodies and Cloudflare challenge
pages** — 15 such files were committed to `documents/lep/` under names promising real content and
had to be deleted (see `documents/DOCUMENT_INDEX.md`). Open anything a scraper produces before
committing it; the document tools now search `.txt`, so junk extracts surface as answers.

Fee figures are on the **2026-27** statutory schedule (`calculate_da_fee()`), transcribed from
`documents/fees/fees-and-charges-2026-27.pdf` p30. They need a July refresh every year — and that
refresh had been missed twice before 2026-08-01, so the tool quoted figures ~6.5% low while a
standing "confirm this figure" caveat sat on every answer. A caveat that is always present carries
no information; `schedule_status()` now adds a loud warning **only** when the scale is actually
behind, and `TestScheduleCurrency` fails once it is two years behind. `calculate_da_fees` is the source of truth for a number — the tables
in Part 2 and `QUICK_REFERENCE.md` are indicative only.

**The lodgement fee is not what a DA costs, and treating it as though it were was the single
largest gap in this repo.** For an 80m² café fitout the fee is $370 and the Section 7.11
contribution is $16,081. `data/contributions.py` carries the contribution rates and
`contributions.py` applies them; `calculate_da_fees` composes everything quantifiable into
`budget_at_least` and lists the rest under `what_it_leaves_out` and `not_estimated`. Three rules
hold it together, and each exists because the alternative puts a wrong number in a business's
budget: **the catchment is never assumed** (rural retail is charged 20% more than urban, so a
default to urban understates a village proposal, and without a stated catchment the contribution is
left out of the total rather than picked); **a change of use is charged on the increase in demand
over the existing lawful use**, per section 2.7 of the plan, which takes shop → café to nil and
office → café to $12,310 — call it the "allowance", never the "credit", which is a different
provision; and **Section 64 water and wastewater is named but never quantified**, because the DSP
is in 2016 dollars and has no non-residential ET conversion table, so only Council can produce that
figure. Anything added here that cannot be sourced should follow the last of those and go in
`UNQUANTIFIED_CHARGES` with its source, not be estimated.

**`readiness.py` composes; it does not know anything new.** `check_da_readiness` and
`prepare_prelodgement_brief` run the checklist, the constraints, the referrals, the parking rate
and the Regulation's own content requirements against *one* proposal — the thing no single tool
did. Three rules hold them together and each inverts a rule that applies elsewhere. It
**over-lists**, like `approvals.py`, because a wrongly-included requirement costs a sentence of
reading and a missing one costs the application. It **never reports a document as verified** —
nothing here can open a file, so `document_gap` echoes the applicant's own words back, matches
them conservatively (head noun *and* first word must agree, or "waste management plan" is accepted
as "stormwater management plan"), and reports words that matched nothing rather than dropping
them. And it **never says "ready"**: the best verdict is that nothing it can check is outstanding,
which is a much smaller claim.

The severity split matters and is easy to get wrong. Sections 25 and 39(1)(a) apply to *every*
application, so emitting them as deficiencies made the verdict read "not ready" for every proposal
ever checked — the same failure as the standing fee caveat in item 0.1, where a warning present on
every answer carried no information. They are `confirm_before_lodging`; `rejection_risk` is
reserved for something actually known to be wrong.

**`data/readiness.py`'s second half is the repository's refusals, collected.** Every entry in
`DUTY_PLANNER_QUESTIONS` is a wall an earlier item hit and correctly declined to guess past — the
CBD boundary that is a bitmap, the contributions catchment, the Section 64 charge with no
non-residential conversion table, the contribution-in-lieu rate that cites a repealed Act. Those
refusals stay. What was missing is that they were scattered across five tools' outputs, so nothing
assembled them into the one thing they are collectively good for: the agenda for the free
fifteen-minute Duty Planner session. Each carries what it costs to leave unresolved, because
fifteen minutes does not fit ten questions and the applicant has to choose. **If you add a tool
that declines to answer something, add the question here too** — otherwise the refusal is a dead
end rather than a redirection.

**`flood.py` selects; `data/flood.py` is the chapter.** DCP Chapter 8 sets its controls per flood
hazard area, and there are five of them — Floodway, High Flood Risk, Flood Fringe, Low Flood Risk
and CBD Flood Liable, which §8.3 gives the Flood Fringe's controls — plus rural land. They differ
enough that answering "commercial" with one requirement, which the old data did, was wrong four
times out of five: the High Flood Risk Area demands a mezzanine refuge above the 1-in-500 year
level, the Flood Fringe does not, and the Low Flood Risk Area has no controls at all. Three rules
hold this together. **The area is never inferred** — Map 1 is a bitmap, the zone is not a proxy,
and without `flood_area` the tool returns every area's controls rather than picking one, exactly as
`parking.py` does with the CBD boundary. **A change of use is checked against §8.3 first**, which
lifts the commercial and industrial controls entirely in the High Flood Risk and Flood Fringe
areas — the commonest business DA there is, so reporting a 25%-above-FPL requirement against a café
fitout is this repo's most likely flood-shaped mistake. And **the DCP never goes back alone**: LEP
cl 5.21(2) is a bar on granting consent rather than a standard to design to, and cl 5.21(3)(a)
requires climate change to be considered, which the DCP's 2001 modelling predates.

**`standards.py` answers from DCP Chapter 1, and its hardest job is saying what the chapter does
not contain.** Chapter 1 is Performance Criteria with Acceptable Solutions, so §1.3 makes every
figure a deemed-to-comply safe harbour rather than a limit — reporting "you must have 6m" talks an
applicant out of an argument the chapter expressly invites, so `HOW_TO_READ_A_FIGURE` rides along
with every answer. The front setback comes from the **zone** (6m in R1/R2/R3/RU5, 15m in RU1/R5/E3,
28m on an RMS road), which the old tool never asked for; it asked for storeys, which decide nothing
here. And **Chapter 1 sets no side setback, no rear setback and no site coverage maximum for an
ordinary lot** — `NOT_SET_BY_THIS_CHAPTER` answers each with what governs instead, because the old
file filled all three with figures that are not in the document.

Both files' figures were invented rather than transcribed: 500mm of freeboard against the
chapter's 300mm, a "CBD Development Exemption Precinct" and a "2090 climate change level" in no
document here, a side setback that is small lot housing's, a front setback that is a five-storey
building separation, a "15% deep soil" that is the chapter's *land steeper than 15%*. Each looked
researched because each collided with a real number somewhere in the source. **Do not add a figure
to either file that you have not read in the document, and prefer `NOT_SET_BY_THIS_CHAPTER` to a
plausible guess** — a presence-checking audit cannot catch an invention, which is why
`audit_standards.py` also asserts the absences.

**`data/definitions.py` quotes the LEP Dictionary, and the same failure had reached it.** Which
defined term a proposal falls under is the whole assessment — it decides permissibility off the
land use table, the Chapter 7 parking rate, and whether a change of use owes a contribution at all
(shop → café is nil, office → café is $12,310). Until 2026-08-08 the file held paraphrases written
from memory, and said so in its own docstring. `warehouse or distribution centre` read "whether or
not goods are sold by retail" where the LEP says **"but from which no retail sales are made"**;
`business premises` invented a "2+ days per week" test that appears nowhere in the LEP and dropped
the exclusion of a medical centre; `boarding house` omitted the affordable-housing and registered-
provider paragraphs that are the whole modern definition; `centre-based child care facility`
excluded out-of-school-hours care, which paragraph (a)(iii) includes.

Three rules hold it together. **Definitions are quoted, never summarised** — anything that is not
the LEP's words lives in `why_this_matters`, which the tool labels as guidance. **A number in a
definition is almost always in the wrong place**: the Dictionary defines terms and the figures live
in clause 5.4, so every invented figure was a real control filed under the wrong provision — a
neighbourhood shop is **200m²** (cl 5.4(7)), not the 80m² the file asserted, and `FIGURES_NOT_IN_
THE_DEFINITION` records the four with the clause that really sets each. And **the Dictionary term
is not always the land use table term** — the table says "Light industries" and "Attached
dwellings" where the Dictionary defines the singular, so `land_use_table_term` carries the plural
and the audit checks it against `data/zones.py`.

**`landuse.py` decides which stored fact applies, and until 2026-08-20 nothing checked it.** Every
audit above passes on data; all 21 zone tables match the LEP verbatim; and `check_permissibility`
still answered the *opposite* of what they say depending on how the use was spelled — 287 of the
991 land use rows, 120 of them a confident "permitted" against a table that prohibits the use.
`audit_landuse_matching.py` is the guard, and ROADMAP.md S1 records the fix. Four rules hold it
together now.

**The singular↔plural pairing is data, not a rule.** `LAND_USE_TABLE_SPELLINGS` carries the LEP's
own 105 pairs, read off the Dictionary in the document. No suffix rule reaches "Crematoria" →
crematorium, "Jetties" → jetty, "Rural workers' dwellings" → rural worker's dwelling (the
possessive moves rather than disappearing) or "Restaurants or cafes" → restaurant or cafe (both
sides of the "or" have to move together) — the old `re.sub(r"\b(\w{3,}?)s\b", r"\1", text)`
produced "facilitie" and "industrie" and met nothing. **Do not add a pair by inflecting a word**;
if the Dictionary does not define the singular there is no pair, and the audit will say so.

**Anything keyed in the LEP's spelling must be looked up in the LEP's spelling.**
`LAND_USE_HIERARCHY` was being consulted with a canonicalised term, so `business premises` became
`busines premise` and took the entire `premises` family with it — which is why E4 answered
"permitted" for uses it prohibits via `Commercial premises`.

**A term the LEP names is never approximated at.** `match_land_use`'s "approximate" strength is a
word-boundary containment search, and once the spelling table let `Home industries` canonicalise
properly, a proposal for `industry` in R2 began matching it. For a recognised use there is nothing
to approximate towards: it is in this table under its own name, or reaches it through the
hierarchy, or it is absent and the catch-all decides. Fuzzy matching is only for words this server
cannot place at all.

**The catch-all has two readings and only one of them is an answer.** Falling through to "any other
development not specified" means either *this use is genuinely unlisted here*, which is the LEP's
own answer and correct — `industry` in R2 is prohibited — or *this server could not identify the
proposal*, which is not a fact about the LEP at all. `KNOWN_LAND_USES` separates them; an
unrecognised term reports `not_found` / `unrecognised` with `permissible` left None, so it cannot
reach `readiness.py` as a "stop" or `see.py` as "Prohibited". One bug producing both 120 wrong
"yes" answers and 91 wrong "no" ones, purely by which catch-all a zone happened to carry, is what
that distinction exists to prevent. Note the row is worded two ways — RU2, RU3, SP2 and C1 say "Any
development not specified" without the "other", so test with `_is_catchall()` rather than against
`CATCHALL_TERM` as a substring.

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
6. **For fees**: Read `documents/fees/fees-and-charges-2025-26.pdf`
7. **For heritage requirements**: Read `documents/dcp/chapter-12-heritage-conservation.pdf`
8. **For subdivision requirements**: Read `documents/dcp/chapter-5a-urban-residential-subdivision.pdf`
9. **For buffer requirements**: Read `documents/dcp/chapter-11-buffer-areas.pdf`
10. **For vegetation/trees**: Read `documents/dcp/chapter-14-vegetation-protection.pdf`
11. **For Nimbin-specific**: Read `documents/dcp/part-b-chapter-6-nimbin-village.pdf`
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
inventions in `data/standards.py` (item 0.6). Prefer `get_residential_standards` and
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

## Lismore CBD Requirements (E2 Commercial Centre)
- Weather protection (awnings/verandahs) required
- Energy efficiency measures
- Disabled access compliance
- Respect for streetscape and heritage values
- Crime prevention through environmental design

## Health Precinct (Brewster Street E2 Zone)
- Specific urban design requirements
- Integration with Lismore Base Hospital precinct

## General Commercial Standards
- Assessment based on:
  - Adjacent building design
  - Context and form
  - Overall streetscape character
- Council assesses each application on individual merit

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

## Heritage Items
- Complete list in LEP 2012 Schedule 5
- Seven Heritage Conservation Areas in LGA

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

## Lismore Council Fees 2025-26
Current fees and charges available at:
https://www.lismore.nsw.gov.au/files/assets/public/v/5/1.-households/2.-rates-and-water/ed25-21941-fees_and_charges_2025_26.pdf

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
- Fees 2025-26: https://www.lismore.nsw.gov.au/files/assets/public/v/5/1.-households/2.-rates-and-water/ed25-21941-fees_and_charges_2025_26.pdf

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
