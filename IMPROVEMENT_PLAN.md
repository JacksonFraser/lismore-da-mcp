# Lismore DA MCP Server — Evaluation & Improvement Plan

Evaluation date: 2026-07-27. Against commit `dd84164` (`main`).

Two evaluations — **user perspective** (what an applicant or an LLM acting for one
experiences) and **technical perspective** (what maintaining and running this costs) — followed
by a proposed module breakdown and a chunked work plan.

Everything below was verified by running the tools, not by reading alone. Where a finding is a
legal/planning claim rather than a code observation it is marked **[verify with planner]**.

---

## Executive summary

The server is more thoughtfully built than its single-file shape suggests. Argument validation
refuses rather than guesses, retired zone codes return proper redirects, the public HTTP mode has
a real privacy switch, and the SEE PDF filler discovers form geometry instead of hardcoding
coordinates. Those are good decisions and none of the work below should undo them.

The problems cluster in three places:

1. **Data coverage gaps that produce confidently wrong answers.** Ten real LEP zones are missing
   entirely, including every rural zone in a predominantly rural LGA.
2. **Exact-token matching everywhere**, so ordinary words (`coffee shop`, `childcare`,
   `site description`) are rejected by tools that hold the answer.
3. **A 3,918-line module with no tests and no logging**, where 25% of the file is one `if/elif`
   chain — which makes every fix above riskier than it needs to be.

Recommended order: **safety net → correctness → structure → UX → performance**. Tests come first
specifically so the structural split can be verified rather than hoped at.

---

# Part 1 — User perspective

## U1. Ten real zones are missing, including all rural zones — **critical**

```
get_zone_info("RU1") → "Zone 'RU1' not found"
```

Missing from the `ZONES` dict: `RU1`, `RU2`, `RU3`, `RU4`, `RU6`, `R4`, `E5`, `C4`, `SP1`, `W2`.

RU1 Primary Production and RU2 Rural Landscape cover the large majority of the Lismore LGA's land
area. A farmer asking about a rural shed, a rural tourism operator, anyone outside the urban
footprint — all get "not found" from the tool that is supposed to be authoritative.

This also contradicts `CLAUDE.md`, which currently tells the agent: *"The `get_zone_info` and
`check_permissibility` tools carry the land use tables verbatim — prefer them over this summary."*
For those ten zones the summary is right and the tool is empty. Whichever gets fixed, they must
stop disagreeing.

The land use tables are already present in `documents/lep/lep-2012-nsw-full.txt` (the R2 table is
at line 675), so this is transcription, not research.

## U2. LEP-only reasoning misses SEPP overrides — **critical**

```
check_permissibility(zone_code="R2", land_use="secondary dwelling")
→ "likely_prohibited"
  "not listed in the Zone R2 land use table, which prohibits 'any other development not specified'"
```

Read strictly as a statement about the LEP land use table, that is correct — I verified against
the LEP text and "Secondary dwellings" genuinely is absent from R2 item 3.

But "can I build a granny flat?" is probably the single most common question a residential
council gets, and the practical answer is usually yes, via State Environmental Planning Policy
(Housing) 2021, which permits secondary dwellings with consent on land where dwelling houses are
permitted. **[verify with planner]** A SEPP overrides the LEP where they conflict, and this tool
has no knowledge of SEPPs at all.

The response never mentions that a SEPP pathway might exist. It reads as a settled "no". The
`advice` field says to confirm with the Duty Planner, which helps, but the headline
`permissibility: likely_prohibited` is what a caller will act on.

Minimum fix: when a use falls through to the catch-all prohibition, say explicitly that the answer
reflects the LEP land use table only and that SEPPs (Housing, Codes, Transport, Primary
Production) may independently permit it. Better fix: encode the handful of high-traffic SEPP
pathways — secondary dwellings, exempt/complying development, group homes.

## U3. Exact-token matching rejects ordinary words

Real results:

| Tool | Input | Result |
|---|---|---|
| `get_parking_rates` | `cafe` | ✅ 1 space per 10m² dining |
| `get_parking_rates` | `coffee shop` | ❌ Exact match not found |
| `get_parking_rates` | `takeaway` | ❌ not found |
| `get_parking_rates` | `child care centre` | ❌ not found |
| `get_parking_rates` | `hairdresser` | ❌ not found |
| `get_parking_rates` | `brewery` | ❌ not found |
| `get_definition` | `granny flat` | ❌ No definition found |
| `get_definition` | `deck` / `shed` | ❌ No definition found |
| `get_see_template` | `site description` | ❌ not found (key is `site_description`) |
| `preview_see_form` | `single storey dwelling` | ❌ (enum is `dwelling_single_storey`) |

`TOOL_EVALUATION.md` already caught this for `get_definition` + "cafe" and recommended synonym
matching. It was never generalised. The same defect now appears in at least five tools.

Note `get_see_template("site description")` failing is close to absurd — the section is literally
named that, and only the underscore differs.

## U4. `get_da_checklist` never refuses

```
get_da_checklist("spaceship")        → returns a checklist
get_da_checklist("nuclear reactor")  → returns a checklist
get_da_checklist("asdfgh")           → returns a checklist
```

It echoes the input as `development_type` and returns generic documents. This is the exact failure
mode `validate_arguments()` was written to prevent — a confident answer to a question the server
cannot actually answer — reintroduced one layer down. An unrecognised type should say so and list
what it does know.

## U5. Argument names are inconsistent across tools

Seven different names for "the thing you are asking about":

```
get_zone_info(zone_code)              get_parking_rates(development_type)
get_definition(term)                  get_see_template(section)
get_setback_requirements(setback_type) check_permissibility(land_use, zone_code)
check_referrals(development_characteristics)
```

Concrete evidence of the cost: while writing this evaluation, with the source open in front of me,
I guessed wrong on four of them in a single batch (`zone` vs `zone_code`, `development_type` vs
`development_characteristics`). An LLM caller without the source will do worse, and the strict
validator turns each near-miss into a hard failure rather than a recovery.

The validator is right to be strict. The names should be consistent enough that strictness rarely
bites.

## U6. The SEE tools take 34–35 parameters

`fill_see_pdf` has 35 properties, `preview_see_form` 34, `generate_see_draft` 17. That is a lot of
surface for a caller to populate correctly, and the fields are heavily correlated (`property_address`
alongside `unit`, `street_number`, `street`, `suburb`; `lot_dp` alongside `lot`, `plan_type`,
`plan_number`).

The parsing helpers (`parse_street_address`, `parse_land_identifier`) already exist to derive the
components. Consider accepting the composite fields and deriving the rest, with the granular
fields as optional overrides.

## U7. Setback advice ignores the things setbacks depend on

`get_setback_requirements(setback_type, development_type)` — no zone, no lot size, no street
frontage, no adjoining development. `CLAUDE.md` states setbacks depend on zone, lot size and
adjoining development, and DCP Chapter 1 varies them by wall height and length. The tool returns a
single answer per setback type regardless.

Either take those inputs, or state plainly in the response that the figure is a general default
and site-specific controls override it.

## U8. Superseded LEP 2000 documents are searched alongside current ones

Four chapters in `documents/dcp/` are LEP 2000 versions:

```
chapter-1-residential-lep2000.pdf         chapter-12-heritage-lep2000.pdf
chapter-14-tree-preservation-lep2000.pdf  part-b-chapter-6-nimbin-village-lep2000.pdf
```

`search_dcp` returns hits from these with no indication they are superseded. Per `CLAUDE.md`, LEP
2000 applies only to areas still under Ministerial review for the former E2/E3 zones — so for
almost every site a LEP 2000 hit is the wrong answer, presented identically to the right one.

## U9. Response shapes differ between success and failure

`preview_see_form` returns `{success: false, blocking_issues: [...]}` when it rejects, but on
success returns `{summary, text_fields, tick_boxes, ...}` with **no `success` key at all**. A
caller checking `response["success"]` sees `None` on the happy path.

## U10. Answers carry no currency information

`calculate_da_fees` returns a figure with no effective date, though the schedule hardcoded in
`calculate_da_fee()` is 2024-25 and statutory fees reset each July. Same for zone and DCP answers.
For a domain whose whole risk profile is "controls change", every response should date itself.

## U11. Search is slow enough to notice

`search_dcp` took **7.35s** locally on fast hardware, opening and re-extracting **41 documents**
per query. Render's free tier has a fraction of that CPU, so hosted queries will be substantially
worse, on top of cold-start delay.

## What works well — do not regress these

- **Legacy zone redirects.** `get_zone_info("B3")` returns a proper "now E2, use that" payload
  rather than a bare failure. Genuinely good.
- **`validate_arguments()`** refuses unknown/empty arguments instead of `.get()`-ing a default.
  The docstring records the real bug that motivated it.
- **`PUBLIC_MODE`** keeps generated SEEs (which contain a named applicant's address) out of shared
  disk on the public deployment.
- **SEE scope gate** blocks out-of-scope development and names the valid types plus the
  purpose-written fallback.
- **`SEE_LAYOUT_EXPECTED`** makes a reissued Council form fail loudly instead of writing an
  applicant's text into the wrong box.
- **Error messages frequently suggest alternatives** (`similar_terms`, `similar_uses`).

---

# Part 2 — Technical perspective

## T1. One module, two hotspots

3,918 lines in `src/lismore_da_mcp/server.py`:

| Concern | Lines | Share |
|---|---|---|
| SEE PDF form config + fill | 974–2111 | **29%** |
| `call_tool` dispatch | 2796–3811 | **25%** |
| Tool schemas | 2112–2795 | 17% |
| Data (parking, zones, definitions) | 35–493 | 11% |
| Document search/read | 749–973 | 5% |
| SEE templates, flood, fees, contact | 599–748 | 3% |
| Everything else | — | 10% |

## T2. `call_tool` is a 1,016-line `if/elif` chain

21 branches in one function. Adding a tool means editing three distant places (schema list,
dispatch chain, README). Nothing enforces that they stay in sync, and no branch can be tested
without going through the whole dispatcher.

## T3. No tests, no CI — **highest structural risk**

Zero test files. No CI (`gh pr checks` reported no checks on the branch merged today). The
riskiest code has no coverage at all: `see_layout()`'s geometry discovery, `calculate_da_fee()`
bracket boundaries, `classify_land_use()`, the address/lot parsers, `find_document()` resolution.

`SEE_LAYOUT_EXPECTED` exists precisely because a reissued form would otherwise misplace an
applicant's text — and nothing currently runs that check.

## T4. No logging anywhere

Zero references to `logging` or `logger`. On a public, unauthenticated service this means no
record of what was asked, what failed, or whether the rate limiter is engaging. Debugging a user
report is currently guesswork.

## T5. No search index

`searchable_documents()` returns 41 paths and every query re-opens and re-extracts all of them via
PyMuPDF. SQLite FTS5 is available through the stdlib `sqlite3` — an index built once at deploy
would take this from seconds to milliseconds with no new dependency.

## T6. Rate limiter grows without bound

`_RateLimitMiddleware._hits` (line ~3837) is keyed by IP and never evicts keys — only the deque
per key is trimmed. Every distinct IP that ever connects retains an entry for the process
lifetime. Slow leak on a long-running instance; also a small memory-amplification vector on an
open endpoint.

## T7. Dead code

- `calculate_da_fee()` line 700: `fee_unit = 111.32` assigned, never used — the brackets are
  hardcoded dollars. It reads as though the schedule is parameterised when it is not.
- Line 20: `Resource` imported from `mcp.types`, never used.

## T8. Broad exception handling with string returns

Five `except Exception` blocks return error strings or `[{"error": str(e)}]`. Combined with T4, a
PyMuPDF failure on one document is indistinguishable from that document having no matches.

## T9. Silent truncation

`extract_pdf_section` and `extract_text_section` both cut at 10,000 characters with no signal to
the caller. A user reading a long DCP section has no way to know content was dropped or how to get
the rest.

## T10. Data and logic are interleaved

459 lines of zone tables, plus parking rates, definitions, referrals and SEE templates, all as
Python literals inside the same module as the server logic. Transcribing a new zone means editing
the server. Moving these to data files (JSON/YAML) would let them be validated against the LEP
text independently, and would make U1 a data task rather than a code task.

## T11. Public endpoint exposure

Deliberately unauthenticated and documented as such. Worth noting that the in-process limiter is
per-instance and best-effort (the code says so), and there is no request logging to detect abuse
(T4). Fine at current traffic; revisit if usage grows.

---

# Part 3 — Proposed module breakdown

Target shape. Sizes are estimates from the current line counts.

```
src/lismore_da_mcp/
  __init__.py
  server.py              # wiring + entrypoint only, ~120 lines
  registry.py            # @tool decorator: schema + handler in one place

  transport/
    stdio.py             # stdio_server run loop
    http.py              # Starlette app, health, session manager
    ratelimit.py         # _RateLimitMiddleware (+ eviction)

  data/                  # pure data, no logic — candidates for JSON
    zones.py             # ZONES (+ the 10 missing)
    parking.py           # PARKING_RATES
    definitions.py       # LAND_USE_DEFINITIONS, LAND_USE_HIERARCHY
    standards.py         # RESIDENTIAL_STANDARDS
    referrals.py         # REFERRAL_REQUIREMENTS
    fees.py              # fee brackets + effective date
    contacts.py          # CONTACT_INFO
    flood.py             # FLOOD_PLANNING

  tools/                 # one module per domain: schema + handler together
    zoning.py            # get_zone_info, list_zones, check_permissibility,
                         # get_definition, list_definitions
    parking.py           # get_parking_rates, list_parking_types
    fees.py              # calculate_da_fees
    planning.py          # flood, setbacks, residential standards, referrals,
                         # checklist, contact
    documents.py         # search_dcp, read_dcp_section, list_documents
    see.py               # get_see_template, generate_see_draft,
                         # preview_see_form, fill_see_pdf

  see/                   # the 1,138-line block, split by responsibility
    layout.py            # _answer_boxes, _checkbox_rects, see_layout,
                         # SEE_LAYOUT_EXPECTED
    fields.py            # SEE_FORM_FIELDS, SEE_QUESTIONS, scope config
    render.py            # _draw_tick, _write, _draw_single_line, _draw_wrapped
    generate.py          # generate_see_form_data, parsers, classify_land_use
    fill.py              # fill_see_pdf

  search/
    index.py             # build/refresh the FTS index
    query.py             # search_document, _score_lines, searchable_documents,
                         # find_document, extract_document_section
```

**The registry is what removes the `if/elif` chain.** Roughly:

```python
@tool(name="get_zone_info", description=..., schema={...})
def get_zone_info(zone_code: str) -> dict:
    ...
```

The decorator appends to `TOOLS` and registers the handler in a dispatch dict, so schema and
implementation live together and cannot drift. `call_tool` becomes a lookup plus the existing
`validate_arguments()` call — a dozen lines.

**Sequencing note:** do this *after* Phase 0 tests exist. A pure-mechanical move of 3,900 lines
with no test suite is how subtle regressions get shipped.

---

# Part 4 — Work plan, in chunks

Each chunk is independently shippable. Effort is rough developer-hours.

## Phase 0 — Safety net ✅ **COMPLETE** (commit `b06950f`)

| # | Task | Status | Notes |
|---|---|---|---|
| 0.1 | Add `pytest` + `tests/`, wire it up | ✅ | `[dev]` extra + `[tool.pytest.ini_options]` |
| 0.2 | Tests for pure functions | ✅ | `test_fees.py`, `test_parsers.py`, `test_documents.py` |
| 0.3 | Test `see_layout()` + assert `SEE_LAYOUT_EXPECTED` | ✅ | `test_see_layout.py`; template matches expectations |
| 0.4 | Every tool called with valid args | ✅ | `test_tools.py`, incl. a test that fails if a tool is added without a smoke case |
| 0.5 | GitHub Actions workflow | ✅ | `.github/workflows/tests.yml`, Python 3.10 + 3.13, plus an HTTP-app import check |

**Result:** 159 passing, 22 xfailed, ~7s. The xfails are `strict=True`, so each flips to a
failure the moment its defect is fixed — they are executable targets for Phases 1 and 3, not
suppressed noise. Each references its plan item.

**Found while writing the tests — new, not in the original evaluation:**

`calculate_da_fee()` computes the per-$1,000 increment by linear interpolation, but Schedule 4
charges *"for each $1,000, **or part $1,000**, by which estimated cost exceeds"* the bracket
floor. A $5,500 development is quoted **$221.50** when Council will charge **$223.00**. The
bracket base fees themselves ($220 / $459 / $1,509 / $2,272) match the official schedule exactly —
only the rounding is wrong. Verified against `documents/fees/nsw-planning-fees-2024-25.pdf`, p2.
Pinned as a strict xfail in `test_fees.py::TestPartThousandRounding`. Added below as **1.8**.

## Phase 1 — Correctness (highest user impact) — **mostly complete**

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Transcribe the missing zones from `lep-2012-nsw-full.txt` | ✅ | **4 zones, not 10** — see correction below |
| 1.2 | Reconcile `CLAUDE.md` with reality | ✅ | Removed RU4/RU6/C4/E5; recorded the 21-zone set |
| 1.3 | Add SEPP caveat to prohibited/not-found results | ✅ | `scope_of_this_answer`, on refusals only |
| 1.4 | Encode high-traffic SEPP pathways | ⏸️ **deferred** | Needs planner review — see below |
| 1.5 | Tag documents with instrument; label LEP 2000 as superseded | ✅ | `data/instruments.py` |
| 1.6 | `get_da_checklist` refuses unknown types | ✅ | Still returns the universal documents |
| 1.7 | Add effective dates to responses | ◐ partial | Done for fees; zone/DCP responses still undated |
| 1.8 | Round the fee increment up per part-$1,000 | ✅ | Schedule now data-driven, not a chain of `elif` |

**Suite: 216 passing, 6 xfailed** (was 159/22). The 10 zone xfails became 42 real assertions.

### Correction to U1 — the evaluation over-claimed

U1 said ten zones were missing. **Four were.** The other six — RU4, RU6, R4, E5, C4, SP1 — exist in
the Standard Instrument and get name-checked in passing by LEP clauses, but have no land use table
in Lismore LEP 2012 and do not apply in this LGA. The LEP says so itself in a note to clause 4.2:
*"When this Plan was made it did not include Zone RU4 Primary Production Small Lots or Zone RU6
Transition."*

The error came from comparing `ZONES` against a generic Standard Instrument zone list rather than
against Lismore's actual LEP. **Lismore LEP 2012 has exactly 21 zones**, derived by extracting the
headings above each "Objectives of zone" block. `ZONES` was missing `RU1`, `RU2`, `RU3`, `W2`.

The impact claim in U1 stands regardless: those four included **every rural zone except RU5
Village**, in an LGA where RU1 and RU2 cover most of the land area.

`CLAUDE.md` carried the same over-claim (it listed RU6, C4 and E5 as Lismore zones) and has been
corrected. `tests/test_tools.py::TestZoneData` now fails in *both* directions — if a Lismore zone
goes missing, and if a non-Lismore zone is added back.

### Data-quality note

`documents/lep/lep-2012-nsw-full.txt` has at least one join defect: RU3's permitted-with-consent
list reads `"Aquaculture Boat launching ramps"` with the separating semicolon missing, evidently
lost when the page was scraped. Both are standard defined terms, so it was split on transcription.
**Assume other extracts may carry similar defects** — transcribe by reading, not by trusting the
delimiter.

### 1.5 — instrument labelling

Every search hit, document listing and section read now names its instrument, and the four LEP 2000
chapters carry a warning pointing at the current control.

The wording is deliberately not "superseded" full stop: **LEP 2000 is not repealed**. It still
applies to areas under Ministerial review for the former E2/E3 zones, so a LEP 2000 hit is usually
the wrong control and occasionally exactly the right one. Flagged rather than hidden.

Classification was verified rather than assumed — each PDF was scanned for its own *"applying to
land to which LEP 20xx applies"* header. Every document that self-identifies says LEP 2012; none
says LEP 2000, so the LEP 2000 set rests on the download naming convention, corroborated by each
having a LEP 2012 counterpart of the same chapter number.

One detail worth keeping: **chapter 14 changed title between instruments** — "Tree Preservation
Order" under LEP 2000, "Vegetation Protection" under LEP 2012. So the counterpart cannot be found
by name, which is why the warning points at the chapter *number*.

### Why 1.4 is deferred

Encoding SEPP pathways means taking on an ongoing obligation to track amendments to at least four
policies, and getting it wrong produces confident advice that a use is permitted when it isn't —
strictly worse than the current gap, which at least errs toward "check with Council". 1.3 closes
the dangerous half (a refusal that reads as settled) at a fraction of the cost. Recommend leaving
1.4 until a planner can review the encoding, per open question 1.

**Exit criteria:** no tool returns a confident answer outside its data coverage; every rural zone
resolves; the four `test_tools.py::TestKnownGaps` and `test_fees.py` xfails flip to passing.

## Phase 2 — Structural split — **2.1, 2.2, 2.4 complete**

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Extract `data/` modules | ✅ | 9 modules; a transcription is now reviewable without reading the server |
| 2.2 | Extract search and `see/` packages | ✅ | Plus `landuse.py`, which check_permissibility and the SEE generator share |
| 2.3 | Build a registry, migrate tools domain by domain | ✅ | `registry.py` + `tools/`; `server.py` 1,990 → 143 lines |
| 2.4 | Extract `transport`; reduce `server.py` to wiring | ✅ | Plus `app.py` holding the Server instance |
| 2.5 | Convert `data/*.py` to JSON + loader | ☐ | Optional |

**server.py: 4,185 → 1,990 lines.** Suite 216 → **223 passing**, 6 xfailed.

```
server.py      1990   TOOLS + call_tool + validate_arguments + main
data/zones.py   491   see/generate.py  376   see/fields.py 220
search.py       209   see/fill.py      188   data/definitions.py 176
see/parsers.py  154   landuse.py       131   transport.py   98
config.py        33   app.py            10   + 6 smaller data modules
```

**A real break the unit tests could not see.** Moving the transports out left
`transport.py` referencing a `server` object it no longer imported — `build_http_app()` raised
`NameError`. Every test still passed, because nothing exercised the HTTP path; only the CI import
step caught it. Fixed by moving the `Server` instance into `app.py` so transports and tool
registration both reach it without importing each other, and `tests/test_transport.py` now covers
the path directly. **Take this as evidence for keeping that CI step**, and as a reminder that
"tests pass" was not sufficient here.

`server.py` re-exports names it does not itself use, so `from lismore_da_mcp.server import X`
keeps working. This is deliberate and commented at the import block — do not strip those without
checking `tests/` first.

### 2.3 — the registry

`server.py` is now **143 lines**: `list_tools`, `call_tool`, `main`, and a re-export block. The
1,055-line `if/elif` chain and the 635-line `TOOLS` list are gone. A tool is one decorated function
carrying its own schema, in `tools/` grouped by domain (zoning, parking, fees, planning, documents,
see).

**Verified by diffing the tool surface against pre-refactor `main`**, not just by the suite
passing. All 21 tools present; 20 byte-identical in description and schema. The single difference
is `get_residential_standards`, whose schema previously carried `"required": []` and now omits the
key — JSON Schema treats an empty `required` and an absent one identically.

Two things the move surfaced:

- `preview_see_form` and `fill_see_pdf` shared one dispatch branch and told themselves apart by
  inspecting `name`, which a registered handler no longer receives. Split into two thin
  registrations over one `_see_form` implementation, deliberately still shared: a preview that
  diverged from what actually gets written would be worse than no preview.
- The decorator now rejects a duplicate tool name, and a `required` argument that isn't declared in
  `properties`, at import time rather than on the call that needed it.

**Exit criteria met:** no module over ~400 lines except `tools/see.py` (643, the SEE tools) and
`data/zones.py` (491, pure data); adding a tool touches one file.

## Phase 3 — Usability — **3.1 and 3.2 complete**

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Shared term-resolution helper | ✅ | `vocabulary.py` |
| 3.2 | Apply to parking, definitions, SEE sections, `minor_development_type` | ✅ | Plus the SEE generator's own parking lookup |
| 3.3 | Normalise argument names across tools (`*_code`, `*_type`) | 2h | U5. Breaking change — version the tools |
| 3.4 | Collapse SEE parameters | ◐ | Premise was wrong — see below |
| 3.5 | Consistent response envelope | ✅ | `preview_see_form` returned two shapes |
| 3.6 | Setbacks: take the inputs the controls actually depend on | ✅ | See below |

Resolution runs exact → squashed → synonym → fuzzy, most confident first. Most of U3's failures
turned out to be punctuation, not vocabulary: `take_away` and `childcare_centre` were already in
the table and `takeaway` / `child care centre` simply could not reach them.

**The design constraint was refusing to guess**, since a confident wrong answer about planning law
is worse than an error — the same reasoning behind `validate_arguments()`. Thresholds were set
from measured ratios against the real vocabularies rather than picked: genuine typos score
0.88–0.95 (`resturant`/`restaurant` 0.95), unrelated words 0.18–0.50 (`hairdresser`/`warehouse`
0.50). So `hairdresser` and `brewery` still refuse — they have no Chapter 7 rate, and quoting
warehouse rates at a hairdresser would be a wrong answer wearing a helpful face. A fuzzy match must
also beat its runner-up by a margin, so an ambiguous term yields suggestions rather than a coin
toss.

Any non-exact match is reported back in `interpreted_as`, so a caller can see that `coffee shop`
was answered as `cafe`. For `get_definition` this matters most: which Standard Instrument term
applies is what decides permissibility, so the swap is stated rather than silently applied.

`TestSynonymTablesAreValid` caught two aliases that were already dead on arrival (`take-away`,
`strata subdivision` — both normalise to their own targets) and guards against a synonym pointing
at a key that later gets renamed.

## Phase 4 — Performance — **4.1 and 4.2 complete**

| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | SQLite FTS5 index built at deploy time | ✅ | `index.py`; built by `render.yaml` buildCommand |
| 4.2 | Fall back to live scan if the index is missing | ✅ | `lookup()` returns `None`; degrades to slow, never to broken |
| 4.3 | Signal truncation in `extract_*_section` | ✅ | With a verified resume hint |

**Measured.** Hosted search before: **16–26s** warm (three runs: 24.9, 26.0, 16.5). Locally 7.4s
of the 7.8s was PyMuPDF extraction across 902 pages / 2.1M characters — the scoring was noise.
After: **0.02s** per query locally, ~400×. Index is 904 segments, built in ~8s.

**Parity took two fixes, both worth knowing about:**

1. *Result diversity.* A full scan caps each document at 5 hits before ranking globally. The first
   index version had no cap, so for "acid sulfate soils" the LEP text took 9 of 10 slots instead
   of 5. Reproduced deliberately.
2. *Tie ordering.* Single-token queries score every hit 1, so which hits survive is decided purely
   by visit order — and FTS5 does not return rows in the scan's document/page order. Candidates
   are now sorted into scan order before scoring.

**One deliberate behavioural difference.** A full scan matches *substrings*: `house` hits the token
`warehouse`. FTS5 matches tokens, and prefix terms (`house*`) recover `houses`/`housing` but not a
term embedded mid-token. Verified this affects nothing realistic — all 25 test queries return
byte-identical results — and only shows up for fragments like `"ouse"` or `"arking"`, where the
scan returns 10 hits and the index 0. Dropping those is an improvement, since `house` matching
`warehouse` is a false positive. Pinned in `tests/test_index.py::TestKnownDifference`.

Parity is enforced by `TestParityWithFullScan`, which runs the full scan it replaces for three
representative queries. That makes the suite ~31s instead of ~9s; the equivalence claim is worth
the 22 seconds.

## Phase 5 — Operations

| # | Task | Effort | Notes |
|---|---|---|---|
| 5.1 | Structured logging: tool name, duration, outcome — never applicant data | ✅ | `observability.py` |
| 5.2 | Evict idle IPs from the rate limiter | ✅ | Amortised sweep every 5 min |
| 5.3 | Remove dead code | ✅ | Both already gone; removed 5 imports the refactors left |
| 5.4 | Narrow broad `except Exception` | ✅ | Found a real bug — see below |
| 5.5 | Fix Render auto-deploy (GitHub App linkage) | — | Deferred; three pushes to `main` have not triggered a deploy |
| 5.6 | Trim nav chrome from the four `.txt` extracts | ✅ | Provenance kept as a `Source:` line |

### 3.4 — U6's premise was wrong

U6 proposed "accepting the composite fields and deriving the rest, with the granular fields as
optional overrides." **That was already the implementation.** A call with only the eight required
arguments works and derives everything:

```
property_address: "Shop 3, 88 Keen Street, Lismore NSW 2480"
lot_dp:           "Lot 12 Section 3 DP 758651"
  → address_number 'Shop 3 88'   street_name 'Keen Street'   suburb 'Lismore'
  → lot '12'   dp '758651'   section '3'
```

The evaluation counted 35 parameters and inferred a problem the code had already solved.

The real defect was the opposite: **the schema steered callers away from the composites.**
`property_address` said *"Prefer the separate unit/street_number/street/suburb fields"* and `lot_dp`
said *"Prefer lot/plan_type/plan_number"*. The parsers worked; the documentation told callers not
to rely on them. That is why the surface read as 35 parameters for an 8-parameter call.

Fixed by inverting that guidance, marking all eight derived components "Optional override. Derived
from … when omitted", and stating in both tool descriptions that eight arguments is a complete
call. Non-breaking. Regression tests now pin the derivation, which nothing guarded before.

**Still open, and a genuine decision rather than a defect:** grouping the 26 optional arguments into
nested objects (`address_parts`, `land_parts`, `site_constraints`, `operation_details`) would take
the surface from 34 top-level to about 18. It is a breaking change on a public unauthenticated
server, and unlike `development_type` it cannot be cleanly aliased — keeping both forms would push
the count to ~40 while the schema is being read.

### 3.6 — setbacks

U7 said setbacks depend on zone, lot size and adjoining development, and proposed either taking
those inputs or stating the limitation. Reading the chapter showed the premise was partly wrong:
**DCP Chapter 1 applies by development type, not by zone** — it covers "building, altering or using
land for the construction of residential development, including ancillary structures such as sheds,
pools and garages", wherever that occurs. Zone-gating would have been incorrect.

What the controls do depend on is **lot configuration** (front) and **storeys** (side, rear). The
tool took neither. Its single `development_type` argument conflated the two, so a two-storey corner
lot could not be expressed at all.

Now split into `storeys` and `lot_configuration`, with `development_type` kept as an alias — it is
a published argument and renaming it would break callers we cannot see. When the inputs determine a
figure the tool gives that figure and says why; when they do not it says which input is missing
rather than returning the "general" case as though it were the answer. Every variant stays
available under `all_cases`.

The response also states the chapter's scope, so a caller asking about a shopfront is pointed at
Chapters 2 and 3 instead of being handed residential numbers.

### 4.3, 3.5 and the address parser — clearing the last pinned defects

The suite now has **zero xfails**: every behaviour pinned as known-broken is fixed.

**4.3** — section reads cut at 10,000 characters silently, so a provision continuing past the cut
simply looked absent. Truncation is now stated and carries a resume point (`start_line=461`,
`start_page=5`). The hint is verified rather than asserted: a test resumes from it and checks the
cut line reappears, so the overlap is a partial line rather than a gap.

**3.5** — `preview_see_form` returned `success: False` when it refused and omitted the key entirely
when it worked, so a caller checking `response["success"]` saw `None` on the happy path and could
reasonably read it as failure. Same tool, same key, both paths now.

**Address parser** — `parse_street_address("Keen Street")` put "Keen Street" in the suburb box too.
With no comma there is nothing identifying a suburb, and the value was being written onto a form
that goes to Council. Blank is honest; an explicit `suburb` argument still wins.

### 5.4 — a real bug behind the style issue

`search_pdf` caught `Exception` and returned `[{"error": ...}]`. `search_all` merged that into the
result list, where it sorted as a scoreless entry and could be returned to the caller as a search
hit **with no file, location or context** whenever a query had fewer than ten real matches.
Confirmed by running a search against a deliberately corrupt PDF.

An unreadable document now contributes no hits and the failure goes to the log. `read_dcp_section`
still reports the error to the caller, because there the caller named that document and the failure
*is* the answer.

Catches are narrowed to `(OSError, RuntimeError, ValueError)` — PyMuPDF's `FileDataError`,
`EmptyFileError` and `FileNotFoundError` all subclass `RuntimeError`. A `TypeError` in the scorer is
a bug in this code and now surfaces as one instead of being reported as an unreadable document;
there is a test asserting that.

### 5.1 — logging

One line per tool call, plus rate-limit, startup and search-index events:

```
INFO  tool=get_zone_info     outcome=ok                duration_ms=0.1
INFO  tool=search_dcp        outcome=ok                duration_ms=40.6
WARN  tool=get_zone_info     outcome=invalid_arguments duration_ms=0.0
```

**Applicant data is excluded by shape, not by discipline.** `fill_see_pdf`, `preview_see_form` and
`generate_see_draft` all take a name, street address and lot/DP, on a public unauthenticated
service whose logs go to a third-party platform. So `record_tool_call()` has no parameter capable
of carrying an argument value — there is no call site where someone could pass one by accident, and
a test asserts that signature stays that way. Another test drives a real SEE call with a
distinctive fake name and address and asserts neither appears in captured output.

Invalid arguments log at WARNING, not ERROR: a caller mistake is not a server fault, and conflating
them makes the error rate useless for alerting.

The client IP is deliberately not logged on rate-limit events. It is personal information, Render's
proxy already records request detail, and what matters for tuning is that the limiter engaged at
all.

The search-index state is logged at startup because a missing index is otherwise invisible from
outside — search still answers, just ~1000× slower. That exact failure reached production once and
was caught only by timing the endpoint.

---

## Suggested order

**Phase 0 → 1 → 2 → 3 → 4 → 5**, with two deviations worth considering:

- **5.3** (dead code) is 15 minutes and can ride along with anything.
- **1.1** (missing zones) is the single highest-impact item in the document and does not depend on
  the test suite. If only one thing gets done, do that.

Phase 2 genuinely should wait for Phase 0. Everything else can be reordered to taste.

## Server instructions (added 2026-07-28, not from the original evaluation)

The evaluation treated this as 21 tools and missed that a remote agent gets **only** those 21 tool
descriptions. `initialize` returned `instructions: None`, and no prompts or resources were exposed.

Everything an agent needs that a schema cannot convey — the order of work, when to send someone to
the Duty Planner, that a LEP table miss is not a refusal — lived solely in this repository's
`CLAUDE.md`, which nobody connecting to the hosted server ever sees.

`instructions.py` now ships that briefing in the `initialize` response, where MCP clients surface it
to the model. 2,570 characters, budgeted rather than open-ended since it is injected every session.

Note this came from a correction: the first proposal was a `start_here` orchestration tool, which
was wrong. An MCP server is driven by an agent, and the agent already orchestrates — the fix is to
brief it, not to build a worse orchestrator inside the server.

`tests/test_instructions.py` guards both halves: that each caveat survives a tidy-up, and that the
factual claims still match the data (the zone count is read from `ZONES`, the retired-code
redirects are checked against it, and every tool named must still be registered).

## Open questions

1. Should `check_permissibility` attempt SEPP reasoning at all, or explicitly scope itself to the
   LEP and say so loudly? Encoding SEPPs is a large, ongoing maintenance commitment.
2. Is the public hosted server intended to stay unauthenticated as usage grows?
3. Are the LEP 2000 documents still needed, or can they move to an archive directory?
