# Lismore Development Application Assistant

An MCP server and knowledge base for assisting with Development Applications (DAs) in the Lismore Local Government Area, NSW, Australia.

## Features

- **Structured Tools**: Parking rates, zone info, fee calculator, flood requirements
- **Document Search**: Search DCP chapters for specific provisions
- **DA Checklists**: Get required documents based on development type
- **Offline PDFs**: 67MB of official planning documents stored locally

## Public Server

A hosted, public instance is running at **https://lismore-da-mcp.onrender.com** — no install
required. Add it as a remote MCP connector in any MCP-compatible client (Claude, etc.) using its
Streamable HTTP endpoint:

```
https://lismore-da-mcp.onrender.com/mcp
```

This is an open, unauthenticated endpoint (no API key) — it only serves public NSW planning
guidance, not private data. It's hosted on Render's free tier, so the first request after a period
of inactivity may take 30-60 seconds to wake up.

In Claude Code, add it with:

```bash
claude mcp add --transport http lismore-da-public https://lismore-da-mcp.onrender.com/mcp
```

To run your own copy instead (locally or self-hosted), see Quick Start below.

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/jacksonfraser/lismore-da-agent
uv sync
```

### 2. Configure Claude Code

The `.mcp.json` file is already configured. Claude Code will automatically detect and load the MCP server.

### 3. Run Claude Code

```bash
cd /Users/jacksonfraser/lismore-da-agent
claude
```

## Available MCP Tools

28 tools in total.

**Lookups**

| Tool | Description |
|------|-------------|
| `lookup_zone_by_address` | Find the LEP zone applying to a street address (live NSW Government mapping lookup) |
| `lookup_site_constraints` | Height limit, minimum lot size, heritage, bushfire and flood mapping for an address |
| `get_zone_info` | Zone objectives, permitted uses, and development standards for an LEP 2012 zone |
| `list_zones` | List all zone codes available in Lismore LEP 2012 |
| `check_permissibility` | Check whether a specific land use is permitted (with/without consent) in a specific zone |
| `get_definition` | Standard Instrument LEP definition of a land-use term, plus related terms |
| `list_definitions` | List all land-use terms with a definition available |
| `get_parking_rates` | Off-street parking requirements for a development type, with shortfall calculation and the DCP mechanisms for addressing a shortfall. Pass `location` — the Lismore CBD is charged a different rate from the rest of the LGA |
| `list_parking_types` | List development types with parking rate data available |
| `get_signage_requirements` | Whether a sign needs an application at all, whether it is prohibited on the site, and the DCP Chapter 9 standard. Most shopfront signage is Exempt Development |
| `list_signage_types` | List sign types grouped by the approval each needs (exempt / CDC / DA) |
| `get_setback_requirements` | Front/side/rear setback requirements for residential development |
| `get_residential_standards` | DCP Chapter 1 standards: site coverage, private open space, landscaping, car parking design |
| `get_flood_requirements` | Flood planning level and floor level requirements, with exemptions |
| `check_referrals` | External agency referrals (integrated development) a proposal may trigger |
| `calculate_da_fees` | What a DA costs: lodgement fee, Council's notification and technology charges, and the Section 7.11 developer contribution — which on a commercial DA is usually far larger than the fee |
| `get_da_checklist` | Required documents for a DA, by development type |
| `get_assessment_timeline` | How long a DA takes and what stops the clock — the 40-day period is a deemed-refusal threshold, not a delivery date |
| `get_other_approvals` | The approvals that are **not** the DA — trade waste, food premises registration, footpath dining, liquor licensing, the CC and the OC — with who issues each and when it is needed |
| `list_other_approvals` | List every non-DA approval, with the issuing authority |
| `get_contact_info` | Council contacts and duty planner availability |

**Documents**

| Tool | Description |
|------|-------------|
| `search_dcp` | Full-text search across DCP chapters, LEP documents, forms, and fee schedules |
| `read_dcp_section` | Read a page range from a specific DCP chapter PDF |
| `list_documents` | List all available planning documents |

**Statement of Environmental Effects (SEE)**

| Tool | Description |
|------|-------------|
| `get_see_template` | Section-by-section guidance for writing an SEE |
| `generate_see_draft` | Generate a full draft SEE from proposal details (any development type) |
| `preview_see_form` | Preview exactly what will be written to the official Lismore SEE PDF before generating it |
| `fill_see_pdf` | Fill and return the official Lismore SEE PDF (Minor Development scope only — see `preview_see_form` first) |

## Example Usage

```
User: What are the parking requirements for a restaurant?

Claude: [Uses get_parking_rates tool]
First: is the site inside the Lismore CBD? The two rates are not close.
- Outside the CBD, Schedule 1 applies: 1 per 2 employees, plus the greater of
  1 per 3 seats or 15 per 100m² GFA (DCP Chapter 7 Schedule 1, p14). An 80m²
  cafe with 40 seats and 6 staff needs 17 spaces; with 20 seats, 15.
  (Schedule 1's wording is ambiguous about what "whichever is greater" governs —
  the tool says so, and says which reading it applies.)
- Inside the CBD, a fixed rate of 3.3 spaces/100m² GFA replaces it (clause
  7.7.3.1). The same 80m² cafe needs 3 — and if it is taking over an existing
  80m² building, a deemed parking credit (clause 7.7.3.4) takes that to 1.
The CBD boundary is Map 1 of the chapter, which is a map image, so the tool
never guesses it: without `location` it returns both figures and says neither
is the answer yet.

User: I'm 4 spaces short in the CBD and the tenancy has nowhere to put them.

Claude: [Uses get_parking_rates tool]
A shortfall is a decision, not just a number to justify. Chapter 7 offers:
- A monetary contribution in lieu of building the spaces (clause 7.7.3.3),
  which also reduces the requirement for that component by 25%. The rate is
  not published in any current Council document — ask the Duty Planner.
- A deemed credit for parking the existing building is taken to have already
  provided (clause 7.7.3.4) — often most of the requirement.
- 25% off any component you open to the public as shared parking (7.7.3.2).
- For a cafe, keeping outdoor dining unenclosed: it is not gross floor area,
  so it generates no requirement at all (clause 7.7.3.1(ii)).
- Arguing it on the six merit criteria Council must consider (clause 7.5).

User: I'm opening an 80m² cafe in a vacant Lismore shop. What will the DA cost?

Claude: [Uses calculate_da_fees tool]
- DA lodgement fee: $370 (on a $50,000 fitout)
- Information & technology service charge: $50 (0.1% of cost)
- Section 7.11 contribution: $16,081 at the retail rate — but the tenancy was
  last used as a shop, which is also retail premises, so on section 2.7 the
  contribution is charged on the increase in demand and comes to nil. Lodge
  evidence of the previous use with the DA; the allowance is not automatic.
- Not included: Section 64 water and wastewater (ask Council early — a kitchen
  adds equivalent tenements), notification fees, long service levy.

User: What can I build in an R1 zone?

Claude: [Uses get_zone_info tool]
R1 General Residential zone allows:
- Dwelling houses, dual occupancies, multi-dwelling housing
- Residential flat buildings, boarding houses
- Neighbourhood shops, community facilities
- Maximum height: 8.5m (check Height Map)
```

## Project Structure

```
lismore-da-agent/
├── CLAUDE.md              # Knowledge base (loaded as context)
├── README.md              # This file
├── pyproject.toml         # Python project config
├── .mcp.json              # MCP server config for Claude Code
├── src/
│   └── lismore_da_mcp/
│       ├── server.py      # Wiring: SDK adapters, dispatch, re-exports
│       ├── app.py         # The MCP Server object
│       ├── transport.py   # stdio and Streamable HTTP
│       ├── registry.py    # The @tool decorator and argument validation
│       ├── observability.py
│       ├── config.py      # Paths, PUBLIC_MODE, document categories
│       ├── data/          # Hand-transcribed source content, no logic
│       ├── tools/         # Handlers, one module per domain
│       ├── see/           # Council SEE form: layout, fill, generate
│       └── *.py           # Domain logic: fees, contributions, parking,
│                          #   landuse, search, index, vocabulary, addresses
├── scripts/               # Audits, document checks, one-off scrapers
├── tests/
└── documents/
    ├── DOCUMENT_INDEX.md  # Index of all documents
    ├── dcp/               # DCP chapters (19 PDFs)
    ├── lep/               # LEP documents
    ├── fees/              # Fee schedules
    └── forms/             # Templates and guidelines
```

## Document Categories

### DCP Chapters (Part A)
- Chapter 1: Residential Development
- Chapter 2: Commercial Development
- Chapter 5A: Urban Residential Subdivision
- Chapter 7: Off-Street Carparking
- Chapter 8: Flood Prone Lands
- Chapter 11: Buffer Areas
- Chapter 12: Heritage Conservation
- Chapter 14: Vegetation Protection
- Chapter 22: Water Sensitive Design

### Area-Specific (Part B)
- Nimbin Village
- Lismore Urban Area

### Forms & Guidelines
- Statement of Environmental Effects template
- Vegetation Management Plan guidelines
- Erosion & Sediment Control guidelines
- On-site Sewage Management Strategy

## Keeping Information Current

1. **DCP Updates**: Check Lismore Council website for amendments
2. **LEP Changes**: Verify on legislation.nsw.gov.au
3. **Fee Schedules**: Update annually (July)
4. **Flood Provisions**: Currently under review - check with Duty Planner

## Disclaimer

This tool provides guidance only. Always verify current requirements with Lismore City Council. Planning controls change - complex projects should engage a planning consultant.

## Resources

- Lismore City Council: https://www.lismore.nsw.gov.au
- NSW Planning Portal: https://www.planningportal.nsw.gov.au
- Lismore LEP 2012: https://legislation.nsw.gov.au/view/html/inforce/current/epi-2013-0066
- Council Phone: (02) 6625 0500
