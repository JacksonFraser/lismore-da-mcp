# Lismore DA Quick Reference Card

## Council Contact
- **Phone**: (02) 6625 0500
- **Address**: 43 Oliver Avenue, Goonellabah NSW 2480
- **Duty Planner**: Tue/Thu 8:30-10:30am (free, no appointment)

## Key Links
| Resource | URL |
|----------|-----|
| NSW Planning Portal | planningportal.nsw.gov.au |
| DA Tracker | lismore.nsw.gov.au/DA-Tracker |
| Pre-lodgement Form | forms.lismore.nsw.gov.au/forms/7788 |

## Standard DA Documents
1. DA Form (via Planning Portal)
2. Owner's Consent
3. Statement of Environmental Effects
4. Site Plan (1:100/1:200)
5. Architectural Plans (1:100/1:200)
6. Cost Estimate
7. BASIX Certificate (residential)

## Common Zones
| Zone | Name | Height |
|------|------|--------|
| R1 | General Residential | 8.5m |
| R3 | Medium Density Residential | 8.5m |
| E2 | Commercial Centre (CBD) | Check map |
| E4 | General Industrial | Check map |

⚠️ The B-series and IN-series codes were retired by the Employment Zones reform (April 2023).
"B3 Commercial Core" is now **E2 Commercial Centre**; "IN1 General Industrial" is now
**E4 General Industrial**. Use the E-series codes in tool calls, SEEs, and Planning Portal
lodgements. The `get_zone_info` / `check_permissibility` tools carry the current land use tables.

## Flood Planning
- **FPL**: 1% AEP + 500mm freeboard
- **Residential**: Habitable floors at/above FPL
- **CBD Exemption**: Shop-top housing if above FPL + refuge above PMF

## Parking (Check DCP Chapter 7)
- Single dwelling: 1-2 spaces
- Multi-dwelling: Per bedroom + visitor
- Commercial: Per m² GFA

## Assessment Timeline
- Standard: 40 business days
- Clock pauses for additional info requests

## DA Fees (2026-27 schedule, indicative)
| Cost of Works | Approx. Fee |
|--------------|-------------|
| Up to $5k | $153 |
| $5k-$50k | $238-$370 |
| $50k-$250k | $492-$1,216 |
| $250k-$500k | $1,610-$2,193 |
| $500k-$1M | $2,422-$3,240 |

Use `calculate_da_fees` for an actual figure — it applies the same EP&A Regulation Schedule 4
brackets exactly. Statutory fees are re-set each July, so verify against Council's current
fees and charges before quoting a number to an applicant.

## Approval Pathway
```
DA Lodged → Assessment (40 days) → Determination
    ↓
Approved → CC → PCA Appointment → Construction → OC
```

## When to Get Help
- Flood-affected land: Consult Duty Planner first
- Heritage items: Heritage Impact Statement needed
- Clause 4.6 variation: Consider planning consultant
- Over $1M: Consider pre-lodgement meeting

## DCP Chapters (Most Used)
- Ch 1: Residential Development
- Ch 2: Commercial Development
- Ch 7: Off-Street Parking
- Ch 8: Flood Prone Lands
- Ch 12: Heritage Conservation
