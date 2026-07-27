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

21 tools in total.

**Lookups**

| Tool | Description |
|------|-------------|
| `get_zone_info` | Zone objectives, permitted uses, and development standards for an LEP 2012 zone |
| `list_zones` | List all zone codes available in Lismore LEP 2012 |
| `check_permissibility` | Check whether a specific land use is permitted (with/without consent) in a specific zone |
| `get_definition` | Standard Instrument LEP definition of a land-use term, plus related terms |
| `list_definitions` | List all land-use terms with a definition available |
| `get_parking_rates` | Off-street parking requirements for a development type, with shortfall calculation |
| `list_parking_types` | List development types with parking rate data available |
| `get_setback_requirements` | Front/side/rear setback requirements for residential development |
| `get_residential_standards` | DCP Chapter 1 standards: site coverage, private open space, landscaping, car parking design |
| `get_flood_requirements` | Flood planning level and floor level requirements, with exemptions |
| `check_referrals` | External agency referrals (integrated development) a proposal may trigger |
| `calculate_da_fees` | DA lodgement fee from estimated development cost |
| `get_da_checklist` | Required documents for a DA, by development type |
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
For a restaurant in Lismore:
- Parking spaces: 1 per 10m² dining area + 1 per 2 employees
- Source: Lismore DCP Chapter 7

User: How much will my DA cost for a $500,000 project?

Claude: [Uses calculate_da_fees tool]
Estimated DA fee: $2,094.50
Cost estimate required: Qualified person estimate
Note: Additional fees may apply for advertising, referrals, etc.

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
│       ├── __init__.py
│       └── server.py      # MCP server implementation
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
