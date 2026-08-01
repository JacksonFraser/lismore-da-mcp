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
uv sync                                   # install deps into .venv (Python >=3.10)
uv sync --extra scraping                  # + httpx/playwright, only for the fetch_*.py scripts
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

Effectively the whole server is one file: `src/lismore_da_mcp/server.py` (~3,800 lines). It is
organised as labelled banner sections; find things by section rather than by module.

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

**`validate_arguments()` is the only gate on arguments, and that is newer than it looks.** It
checks each call against that tool's own schema — rejecting unknown arguments, missing/empty
required ones, and (since the mcp 2.0 port) wrong types — rather than letting handlers `.get()` a
default and answer confidently wrong. An empty `land_use` once returned "permitted without
consent". **mcp 1.x had the SDK run the schema through jsonschema server-side before dispatch;
2.0 removed that entirely** — only `mcp.client.session` still carries jsonschema — so a string
where a number belonged reached `float()` and surfaced as a raw `MCPError` reading "could not
convert string to float". Type checking lives in `validate_arguments` now. Anything the schema
can express that this function does not check is unenforced on the server: `_JSON_TYPES` covers
the type keyword only, and a test fails if a schema declares a type it does not know.

**The SDK's shape is confined to one seam.** mcp 2.0 replaced the `@server.call_tool()` /
`@server.list_tools()` decorators with handlers registered by method name taking
`(context, params)` and returning typed results. `server.py` keeps `call_tool(name, arguments)`
and `list_tools()` as plain functions and wraps them in `_on_call_tool` / `_on_list_tools`
adapters registered via `add_request_handler`. Tests and `conftest` call the plain functions, so
the next SDK break lands in two adapters rather than across 490 tests. Note `Tool.inputSchema` is
`Tool.input_schema` in 2.x (the wire format is unchanged — it is a pydantic alias), and
`server.request_handlers` is now `server.get_request_handler(method)`.

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
centralised in `DOC_CATEGORIES` (dcp, lep, forms, fees, exempt-development) and
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

The `fetch_*.py` scripts at repo root are one-off Playwright scrapers (legislation.nsw.gov.au,
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

## Building Design
- Maximum external wall length: 14 metres (unless broken by architectural features)
- Medium density: Maximum 3 dwellings under single roof
- Dwelling groups: Minimum 4 metre separation between groups of 3

## Setbacks
Setbacks depend on zone, lot size, and adjoining development. General principles:
- Front setback: Generally consistent with established building line
- Side setbacks: Depend on building height and wall length
- Rear setbacks: Provide adequate private open space

## Private Open Space
- Required for all dwellings
- Minimum dimensions apply
- Must be functional and accessible from living areas

## Site Coverage
- Maximum site coverage varies by zone
- Generally 50-60% for residential zones
- Check specific DCP provisions

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

## Flood Planning Level (FPL)

### Current Standard
- 1% AEP (1-in-100 year) flood level + 500mm freeboard

### Proposed Changes (Under Review)
- 1% AEP 2090 climate change level + 500mm freeboard
- Approximately 13.4m for high-risk areas

## Habitable Floor Level Requirements

### Residential Development
- All habitable floor areas must be at or above FPL
- Extensions/additions: Habitable floors at or above FPL
- Exceptions only where Council considers requirement impractical/unreasonable

### Commercial/Industrial Development
- Percentage of development must be above FPL
- Some developments: Minimum 25% of gross floor area above FPL

## CBD Development Exemption Precinct
Allows residential development (shop-top housing, tourist accommodation) if:
- Habitable floor levels above FPL
- Structural soundness proven
- Site-specific evacuation plan prepared
- Refuge available above Probable Maximum Flood (PMF)

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
- Standard: 40 business days for most local development
- Clock pauses if Additional Information Request issued
- Complex developments may take longer

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
