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

| Tool | Description |
|------|-------------|
| `get_parking_rates` | Get parking requirements for a development type |
| `get_zone_info` | Get zone objectives, permitted uses, height limits |
| `calculate_da_fees` | Calculate DA lodgement fee from development cost |
| `get_flood_requirements` | Get flood planning level and floor requirements |
| `get_contact_info` | Get Lismore Council contacts and duty planner info |
| `search_dcp` | Search DCP documents for specific provisions |
| `read_dcp_section` | Read pages from a DCP chapter PDF |
| `list_documents` | List all available planning documents |
| `get_da_checklist` | Get required documents for a DA by type |
| `list_parking_types` | List development types with parking rates |
| `list_zones` | List all zone codes in Lismore LEP 2012 |

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
