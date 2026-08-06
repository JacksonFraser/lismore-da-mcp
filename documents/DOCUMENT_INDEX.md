# Lismore DA Document Index

This directory contains official planning documents downloaded from Lismore City Council and NSW Government sources.

## DCP Documents (Development Control Plan)

### Part A - General Development Controls

| File | Description |
|------|-------------|
| `dcp-introduction-may-2025.pdf` | DCP Introduction Chapter - Overview and structure |
| `chapter-1-residential-development.pdf` | Chapter 1 - Residential Development (LEP 2012) |
| `chapter-1-residential-v4.pdf` | Chapter 1 - Residential Development (v4 update) |
| `chapter-1-residential-lep2000.pdf` | Chapter 1 - Residential Development (LEP 2000) |
| `chapter-2-commercial-development.pdf` | Chapter 2 - Commercial Development CBD & Health Precinct |
| `chapter-3-industrial-development.pdf` | Chapter 3 - Industrial Development |
| `chapter-4-rural-nature-based-tourism.pdf` | Chapter 4 - Rural and Nature-Based Tourism Development (LEP 2012) |
| `chapter-5b-commercial-industrial-subdivision.pdf` | Chapter 5B - Commercial and Industrial Subdivision (LEP 2012) |
| `chapter-5a-urban-residential-subdivision.pdf` | Chapter 5A - Urban Residential Subdivision (with Amd 34) |
| `chapter-7-off-street-carparking.pdf` | Chapter 7 - Off-Street Carparking requirements |
| `chapter-8-flood-prone-lands.pdf` | Chapter 8 - Flood Prone Lands |
| `chapter-9-signage.pdf` | Chapter 9 - Signage |
| `chapter-11-buffer-areas.pdf` | Chapter 11 - Buffer Areas |
| `chapter-12-heritage-conservation.pdf` | Chapter 12 - Heritage Conservation (LEP 2012) |
| `chapter-12-heritage-lep2000.pdf` | Chapter 12 - Heritage Conservation (LEP 2000) |
| `chapter-14-vegetation-protection.pdf` | Chapter 14 - Vegetation Protection |
| `chapter-13-crime-prevention-environmental-design.pdf` | Chapter 13 - Crime Prevention Through Environmental Design (LEP 2012) |
| `chapter-14-tree-preservation-lep2000.pdf` | Chapter 14 - Tree Preservation Order (LEP 2000) |
| `chapter-15-waste-minimisation.pdf` | Chapter 15 - Waste Minimisation (LEP 2012) |
| `chapter-17-acid-sulfate-soils.pdf` | Chapter 17 - Acid Sulfate Soils (LEP 2012) |
| `chapter-18-extractive-industries.pdf` | Chapter 18 - Extractive Industries |
| `chapter-21-public-art.pdf` | Chapter 21 - Public Art (LEP 2012) |
| `chapter-22-water-sensitive-design.pdf` | Chapter 22 - Water Sensitive Design |

### Part B - Area-Specific Controls

| File | Description |
|------|-------------|
| `part-b-chapter-1-lismore-urban-area-lep2000.pdf` | Chapter 1 - Lismore Urban Area (**LEP 2000** — the council publishes no LEP 2012 edition of this chapter. Renamed 2026-08-01: it was filed without the marker and therefore reported as current.) |
| `part-b-chapter-3-lismore-cultural-precinct.pdf` | Chapter 3 - Lismore Cultural Precinct (LEP 2012) |
| `part-b-chapter-4-airport-industrial-estate.pdf` | Chapter 4 - Airport Industrial Estate (LEP 2012) |
| `part-b-chapter-5-wyrallah-road-industrial-estate.pdf` | Chapter 5 - Wyrallah Road Industrial Estate (LEP 2012) |
| `part-b-chapter-9-north-lismore-industrial-estate.pdf` | Chapter 9 - North Lismore Industrial Estate (LEP 2012) |
| `part-b-chapter-6-nimbin-village.pdf` | Chapter 6 - Nimbin Village (LEP 2012) |
| `part-b-chapter-6-nimbin-village-lep2000.pdf` | Chapter 6 - Nimbin Village (LEP 2000) |

### Environmental & Management Plans

| File | Description |
|------|-------------|
| `koala-plan-of-management.pdf` | Comprehensive Koala Plan of Management for South-East Lismore |

## LEP Documents

| File | Description |
|------|-------------|
| `lep-2012-nsw-full.txt` | **Added 2026-07-26.** Full text of Lismore LEP 2012 extracted from NSW Legislation site. Contains all zone land use tables, development standards, local provisions, heritage schedules, and clauses. ~300KB. **Trimmed 2026-07-28** — the site navigation header and footer were removed so they stop appearing in search results; a `Source:` line at the top preserves provenance. Source: `legislation.nsw.gov.au/view/whole/html/inforce/current/epi-2013-0066` |
| `clause-5.21-flood-planning.txt` | Clause 5.21 Flood Planning text from Lismore LEP 2012 (AustLII extract, chrome trimmed) |
| `part-4-development-standards.txt` | Part 4 principal development standards — clauses 4.1/4.1AA minimum subdivision lot size (AustLII extract, chrome trimmed) |
| `zone-r1-land-use-table.txt` | Clause 2.3 and the R1 zone land use table (AustLII extract, chrome trimmed) |
| `LEP_2012_Land_Use_Matrix.xls` | Land use permissibility matrix for all zones |
| `existing-land-use-rights-fact-sheet.pdf` | Existing Use Rights fact sheet |

**Removed 2026-07-27** — 15 files in this directory were scraper output, not content: the
`zone-*.txt` per-zone files (AustLII "404 File not found" pages, despite filenames promising zone
land use tables), `lep-dictionary.txt`, `schedule-5-heritage.txt` and
`standard-instrument-dictionary.txt` (404 / Cloudflare bot-verification pages),
`lep-2012-full.txt` (a Cloudflare "Just a moment..." challenge page), and
`lep-2012-austlii.txt` / `.html` (table of contents only, no substantive text). They were deleted
rather than filtered out at search time — the document tools now search `.txt` files, and a search
hit quoting a bot-verification page is worse than no hit. Recoverable from git history if needed.
**Verify any new `.txt` extract actually contains the content its filename claims before
committing it.** The zone land use tables live in `lep-2012-nsw-full.txt` and, transcribed, in the
`ZONES` dict behind the `get_zone_info` / `check_permissibility` tools.

| File | Description |
|------|-------------|
| `land-use-matrix-august-2023.pdf` | **Added 2026-08-01.** Council's Land Use Matrix (August 2023) — permitted/prohibited uses across every zone on four pages. Useful as an **independent cross-check** on the hand-transcribed `ZONES` tables (`PLAN.md` item 0.2), since it is a different rendering of the same land use tables. |

## Fees & Charges

> ⚠️ `calculate_da_fees` computes from the **2024-25** statutory scale (`data/fees.py`). The
> 2026-27 schedule below is newer than the code — see `PLAN.md` item 0.1.

| File | Description |
|------|-------------|
| `fees-and-charges-2026-27.pdf` | **Added 2026-08-01.** Lismore City Council Fees and Charges 2026-27 — the current year, and newer than the scale `calculate_da_fees` uses |
| `fees-and-charges-2025-26.pdf` | Lismore City Council Fees and Charges 2025-26 |
| `section-7.11-contributions-plan-2024-2041.pdf` | **Added 2026-08-01.** Lismore City Section 7.11 Infrastructure Contributions Plan 2024-2041 (33MB). For a commercial development these contributions can exceed the DA lodgement fee |
| `development-servicing-plans-water-wastewater.pdf` | **Added 2026-08-01.** Development Servicing Plans for Water Supply and Wastewater — the Section 64 headworks charges, significant for food premises |
| `nsw-planning-fees-2024-25.pdf` | NSW Planning Development Fees Schedule 2024-25 |

## Forms & Guidelines

| File | Description |
|------|-------------|
| `statement-of-environmental-effects-minor-development.pdf` | **Added 2026-07-26.** Genuine blank Lismore City Council SEE template, verified empty of any applicant data. Source: `lismore.nsw.gov.au/files/assets/public/v/1/5.-council/7.-about-council/statement-of-environmental-effects-minor-development.pdf`. Scope-limited — "Minor Development Only": single-storey dwellings, single-storey residential additions/alterations, ancillary residential structures (sheds, pools, carports), and strata subdivision of existing buildings. All other development types need a purpose-written SEE, not this form. Supersedes the removed `see-template-nsw-planning-portal.pdf` (see `_quarantined/README.md`) — that file was a different council's real, signed application, not a template. |
| `vegetation-management-plan-guidelines-2024.pdf` | Guidelines for Vegetation Management Plans (2024) |
| `guidelines-erosion-sedimentation-control.pdf` | Erosion and Sedimentation Control Guidelines |
| `c211-erosion-sedimentation-spec.pdf` | C211 Erosion and Sedimentation Control Specification |
| `stormwater-drainage-handbook.pdf` | Handbook of Stormwater Drainage Design |
| `onsite-sewage-wastewater-management-strategy.pdf` | On-site Sewage and Wastewater Management Strategy |
| `guide-for-resited-dwellings.pdf` | Guide for Re-sited Dwellings (Flood Recovery) |

## Exempt Development Fact Sheets (State-wide, NSW DPE)

Added 2026-07-27. Official NSW Department of Planning and Environment "rules for exempt
development" fact sheets — state-wide SEPP guidance (Exempt and Complying Development Codes
2008), not Lismore-specific. Use these to answer "do I need a DA?" questions for common minor
works. `legislation.nsw.gov.au` and `austlii.edu.au` (the primary legislative sources) reliably
return HTTP 403 to automated fetches, so these DPE-published fact sheet PDFs are cached locally
instead. Note: they're guidance summaries, not the legal text — site-specific exclusions (flood
control land, heritage items/conservation areas, bushfire-prone land, foreshore land) still
apply and can only be confirmed against the actual LEP maps/SEPP clauses for the specific
property. Source: `planning.nsw.gov.au/sites/default/files/2023-02/...`

| File | Description |
|------|-------------|
| `exempt-development/balconies-decks-patios-pergolas-terraces-verandahs.pdf` | Decks, patios, verandahs etc. attached to a dwelling — height/area/setback rules |
| `exempt-development/fences.pdf` | Fences — exempt and complying development rules |
| `exempt-development/carports-and-garages.pdf` | Carports and garages — exempt and complying development rules |
| `exempt-development/cabanas-cubby-houses-sheds-gazebos-greenhouses.pdf` | Garden sheds, cabanas, cubby houses, ferneries, gazebos, greenhouses |
| `exempt-development/driveways-hardstands-pathways-paving.pdf` | Driveways, hardstands, pathways and paving |
| `exempt-development/understanding-exempt-development.pdf` | General overview of what exempt development is and how it works |

No dedicated DPE exempt-development fact sheet exists for swimming pools — small pools are
generally handled as **complying development** (via a CDC), not exempt development, largely due
to mandatory pool safety fencing/barrier requirements. Don't fabricate a pool exemption; direct
those queries to the Housing Code / CDC pathway instead.

## Business & Food Premises

Added 2026-08-01 for business applicants (see `PLAN.md`). Retrieved from lismore.nsw.gov.au
`/Business/Food-businesses-in-Lismore` — see `SCRAPER.md` for the method.

| File | Description |
|------|-------------|
| `requirements-for-set-up-of-food-premises.pdf` | Council requirements for establishing, constructing and setting up a food premises |
| `home-based-food-business.pdf` | Home-based food business fact sheet |
| `food-businesses-at-temporary-events.pdf` | NSW Food Authority — food businesses at temporary events |
| `food-standard-3-2-2a-guideline.pdf` | Food Standards Code Standard 3.2.2A guideline for businesses |
| `nsw-outdoor-dining-policy-2019.pdf` | NSW Outdoor Dining Policy 2019 — footpath/outdoor dining approvals |
| `home-occupation-work-from-home.pdf` | Work-from-home / home occupation fact sheet |

## Legislation

Added 2026-08-06 for `PLAN.md` item 2.5. Nothing in this repository said anything about how long
a DA takes or what stops the clock — the periods are set by regulation, not by Council — so the
regulation was fetched rather than transcribed from memory. `scripts/fetch_epa_regulation.py`
retrieves it (legislation.nsw.gov.au returns 403 to plain HTTP and sits behind a Cloudflare
challenge, so it uses Playwright and the `scraping` extra) and **refuses to write anything that
does not contain the provisions being sought** — which is what caught a wrong SL number returning
a live 404 page on the first attempt.

| File | Description |
|------|-------------|
| `epa-regulation-2021-assessment-periods.txt` | Environmental Planning and Assessment Regulation 2021, full text (606KB), retrieved 2026-08-06 from legislation.nsw.gov.au (SL 2021 No 759). Source for `data/timing.py`: the assessment periods (ss 91-95), the stop-the-clock provisions (s94) and its 25-day limit, requests for additional information (s36) and rejection of applications (s39). Checked by `scripts/audit_timing.py` |

**This is a fetched snapshot of legislation, not a Council document.** It goes stale when the
regulation is amended, and the audit is what surfaces that: a quote that stops matching means the
law changed, not that the transcription slipped. Re-run the fetch script to refresh it.

## Using These Documents

When answering questions about Lismore DAs, Claude should:

1. **Reference specific documents** when providing detailed answers
2. **Read the relevant PDF** using the Read tool for exact standards, rates, and requirements
3. **Quote specific sections** where applicable
4. **Note document dates** as requirements may have been updated

## Document Sources

- Lismore City Council: https://www.lismore.nsw.gov.au
- NSW Planning Portal: https://www.planningportal.nsw.gov.au
- NSW Legislation: https://legislation.nsw.gov.au

## Last Updated

July 2026
