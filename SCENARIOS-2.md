# Scenario Suite 2 — 200 scenarios

> **Written 2026-08-09. NOT YET RUN.** Suite 1 (`SCENARIOS.md`) has been executed once; this is
> built but deliberately unexecuted, to be worked through over time.
>
> **Suite 1 is not superseded.** It stays as the regression suite — the 100 scenarios that found
> the current defects should keep being run after every phase. This suite goes where suite 1 did
> not, and it is shaped by what suite 1 found rather than being more of the same.

## What run 1 established, and what follows for this suite

Run 1 returned **56 PASS · 28 PARTIAL · 15 FAIL**, and the shape of the failures mattered more than
the count: **not one was a bad fact.** Every audit passed, all 21 zone tables matched the LEP, every
dollar figure traced to its page. All 15 failures were in *selection, matching and application*.

Four things follow, and they are what this suite is built from:

1. **The defect classes were found by accident and should be swept deliberately.** D1 surfaced
   because one agent happened to try a plural. D2 because one tried a negative. A suite that relies
   on an agent's curiosity finds what that agent was curious about. Groups **LU**, **MO**, **NU**
   and **XT** sweep those four classes systematically.
2. **Failures cluster where tools compose.** Single-tool, single-chapter domains (flood, cost,
   timing, signage) returned 29 passes and no failures. Change of use, needing six tools to agree,
   failed 6 in 15. Group **JN** is therefore ten full journeys rather than single calls — the
   highest-yield shape in run 1.
3. **Whole surfaces went untested.** The SEE tools, the document search tools, and the entire
   privacy and transport layer got almost no coverage — and the SEE tools are the ones that take an
   applicant's name and address over an open, unauthenticated endpoint. Groups **SE**, **DO** and
   **OP**.
4. **Whole domains went under-sampled.** Rural, village and industrial got one scenario between
   them; subdivision, modifications and post-approval got none. Groups **RV**, **RD**, **SU**,
   **PA**.

## A note on what belongs here and what belongs in an audit

Some checks below are mechanical enough that a scenario is the wrong instrument. **LU-19…LU-26**
is a sample of a sweep that should ultimately be `audit_landuse_matching.py` — walking every term
in all 21 tables, singular and plural, asserting the *tool* agrees with the *table*. That guard is
Phase S1 in `ROADMAP.md`. The scenarios here exist to prove the class before the audit is written,
and to stay readable afterwards. Same for **NU**: the boundary sweep becomes a property test.

**Do not delete these once the audits exist.** A scenario says what a business asked; an audit says
what a function returned. Both are worth keeping.

## Judging

Unchanged from suite 1 — the six checks (internal consistency, source grounding, correct refusal,
silent wrongness, robustness, first contact), and the same verdicts: `PASS` · `PARTIAL` · `FAIL` ·
`BLOCKED`. Risk is what a wrong answer costs a business: `HIGH` (money, rejection, or a wrong
"yes"), `MED` (delay or rework), `LOW` (friction).

**One rule added after run 1.** Where a scenario's expected answer depends on a *reading* of an
ambiguous source, record the reading rather than the verdict — those belong in the interpretation
register (`ROADMAP.md` B1), not in a pass/fail column. A suite that scores interpretation as fact
manufactures false confidence.

---

# LU — Land use vocabulary and matching (30)

The D1 class, swept. Every business word a real applicant uses, and every place the singular/plural
and hierarchy machinery can drop one.

## LU-01…LU-18 — the words businesses actually use

Each: does `check_permissibility` resolve it, does `get_parking_rates` resolve it, and do the two
agree? **Passes if** both answer via a shown derivation, or both refuse. **Fails if** one answers
and the other refuses, or either resolves silently without showing how. **Risk: HIGH** for the
permissibility limb, **MED** for parking.

| ID | Business word | Expected defined term | Zone to test |
|---|---|---|---|
| LU-01 | barber / hairdresser | business premises | E1 |
| LU-02 | bakery | food and drink premises → shop? or artisan food and drink industry | E2 |
| LU-03 | craft brewery | artisan food and drink industry vs light industry | E3 |
| LU-04 | cellar door | artisan food and drink industry | RU1 |
| LU-05 | nail salon / beauty salon | business premises | E1 |
| LU-06 | physiotherapist | health consulting rooms / medical centre | E2 |
| LU-07 | dentist | health consulting rooms | E2 |
| LU-08 | veterinary clinic | veterinary hospital | E3 |
| LU-09 | yoga / pilates studio | recreation facility (indoor) | E2 |
| LU-10 | dance school | recreation facility (indoor) vs educational establishment | E1 |
| LU-11 | after-school care | centre-based child care facility, para (a)(iii) | R2 |
| LU-12 | art gallery | information and education facility | E2 |
| LU-13 | bike shop with repairs | shop vs vehicle repair station | E1 |
| LU-14 | panel beater | vehicle body repair workshop | E4 |
| LU-15 | tyre fitting | vehicle repair station | E3 |
| LU-16 | laundromat | business premises | E1 |
| LU-17 | pet grooming | business premises vs animal boarding or training establishment | E3 |
| LU-18 | self-storage units | self-storage units / warehouse or distribution centre | E4 |

## LU-19…LU-26 — the singular/plural sweep

The mechanism confirmed in run 1: `canonical_use()` strips a trailing `-s` and cannot pair `-ies`
with `-y`. **Every row must return the same permissibility for both forms.** **Risk: HIGH.**

| ID | Singular | Plural (table form) | Zone | LEP position |
|---|---|---|---|---|
| LU-19 | centre-based child care facility | Centre-based child care facilities | E4 | prohibited |
| LU-20 | light industry | Light industries | E4 | permitted with consent |
| LU-21 | industry | Industries | E1, E2 | prohibited |
| LU-22 | home business | Home businesses | R2, RU5 | permitted with consent |
| LU-23 | home industry | Home industries | R2 | permitted with consent |
| LU-24 | rural industry | Rural industries | RU1 | check table |
| LU-25 | artisan food and drink industry | Artisan food and drink industries | RU1, E1 | permitted with consent |
| LU-26 | attached dwelling | Attached dwellings | R3 | control — `-s` form, should already pass |

## LU-27…LU-30 — the machinery itself

**LU-27 — A catchall result is never a permissibility answer.** Any result with
`match_type: catchall` means the term was not recognised, which is a different fact from the use
being permitted. **Passes if** it says so, and carries the SEPP caveat. **Fails if** it reports
`likely_permitted_with_consent` unhedged, as run 1 found. **Risk: HIGH**

**LU-28 — The catchall never states a falsehood.** Run 1 caught *"'light industry' is not listed in
the Zone E4 land use table"* when it is item 3. **Passes if** the tool does not assert absence it
has not established. **Risk: HIGH**

**LU-29 — `land_use_table_term` is consulted.** `data/definitions.py` carries the table spelling for
every defined term. **Passes if** `landuse.py` resolves through it rather than string-comparing.
**Risk: HIGH**

**LU-30 — `similar_uses` never contradicts `permissibility`.** Run 1 found `R2` + `home business`
returning likely-prohibited while listing `"Home businesses"` in its own `similar_uses`. **Passes
if** no payload contains both. **Risk: HIGH**

---

# MO — Modality and source fidelity (15)

The D4 class, swept. For every requirement the tools assert, does the modality match the source?
**Passes if** "must/required" corresponds to a mandatory provision, and a discretionary provision is
reported as "may". **Fails if** a discretionary power is stated as a requirement, as with the
Heritage Impact Statement. **Risk: HIGH** wherever the requirement costs money to satisfy.

| ID | Asserted requirement | Check against |
|---|---|---|
| MO-01 | Heritage Impact Statement | LEP cl 5.10(5) — *may*, and a HIS is one of three forms *(known FAIL)* |
| MO-02 | BASIX certificate | when it actually applies; not to a commercial fitout |
| MO-03 | Access report | tools say "commonly required" — is that sourced? |
| MO-04 | Traffic impact assessment | what triggers it, and who says so |
| MO-05 | Acoustic report | run 1 found it emitted as unconditional boilerplate |
| MO-06 | Waste management plan | DCP Ch 15 — mandatory or guidance? |
| MO-07 | Contamination report | SEPP Resilience and Hazards trigger |
| MO-08 | Flood risk assessment | DCP Ch 8 vs LEP cl 5.21 |
| MO-09 | Certificate of structural adequacy | §8.6.4 — exempt under $50,000, except restumping |
| MO-10 | Surveyor's certificate of floor level | which areas, and is it ever lifted |
| MO-11 | Clause 4.6 variation request | required, or the applicant's option |
| MO-12 | Owner's consent | mandatory; check the landlord case is stated |
| MO-13 | QS report over $3m | EP&A Reg — check the threshold and who may certify |
| MO-14 | Fire safety schedule | when, and at DA or CC stage |
| MO-15 | s39(1)(d) rejection ground | run 1 found it cited on every application; it reads *"for an application for integrated development"* |

---

# XT — Cross-tool contradiction (20)

Run 1 found six contradictions incidentally. This group hunts them. Each scenario runs **one
situation through two or more tools** and checks the answers can both be true.

| ID | Tools | The contradiction to hunt | Risk |
|---|---|---|---|
| XT-01 | `check_permissibility` ↔ `get_parking_rates` | a use one resolves and the other refuses | MED |
| XT-02 | `check_permissibility` ↔ `get_definition` | the definition says a use is a type of X; permissibility disagrees | HIGH |
| XT-03 | `get_parking_rates` ↔ `check_da_readiness` | the CBD number with the Schedule 1 basis *(known FAIL)* | MED |
| XT-04 | `calculate_da_fees` ↔ `get_da_checklist` | change-of-use treated as building work by one | MED |
| XT-05 | `get_flood_requirements` ↔ `lookup_site_constraints` | flood status asserted vs unknown | HIGH |
| XT-06 | `get_signage_requirements` ↔ `get_other_approvals` | signage exempt in one, an approval in the other | MED |
| XT-07 | `check_da_readiness` ↔ `prepare_prelodgement_brief` | a question answered in one, still open in the other | MED |
| XT-08 | `generate_see_draft` ↔ `get_parking_rates` | the SEE's parking figure vs the tool's *(the historical bug)* | HIGH |
| XT-09 | `get_zone_info` ↔ `check_permissibility` | the table listing vs the permissibility verdict | HIGH |
| XT-10 | `get_other_approvals` preamble ↔ its own entries | CC "applied for" vs "issued" *(known FAIL)* | MED |
| XT-11 | `lookup_zone_by_address` ↔ `lookup_site_constraints` | one refuses out-of-LGA, the other answers *(known FAIL)* | HIGH |
| XT-12 | `calculate_da_fees` ↔ `get_contact_info` | fee year vs stated schedule currency | LOW |
| XT-13 | `get_flood_requirements` ↔ `check_referrals` | flood controls vs whether a flood referral fires | MED |
| XT-14 | `get_definition` ↔ `get_parking_rates` | hairdresser inside business premises, no rate applied *(known)* | MED |
| XT-15 | `check_referrals` ↔ `get_da_checklist` | a referral needing a document the checklist omits | MED |
| XT-16 | `get_signage_requirements` ↔ `check_permissibility` | signage as a land use vs as signage | LOW |
| XT-17 | `check_da_readiness` with vs without an address | run 1 found more input *hardens* a heritage "no" *(known FAIL)* | HIGH |
| XT-18 | `get_assessment_timeline` ↔ `check_da_readiness` | integrated development period vs the 40-day boilerplate | MED |
| XT-19 | `calculate_da_fees` ↔ `get_other_approvals` | a fee quoted in both, differing | HIGH |
| XT-20 | stdio transport ↔ HTTP transport | the same call, different answers | HIGH |

---

# NU — Numeric domain and boundary (20)

The D2 class, swept. `validate_arguments()` checks type and not domain, so every numeric argument
is in scope. **Passes if** the value is rejected with a clear message, or handled correctly.
**Fails if** it produces a wrong number, a negative output, an uncaught exception, or invalid JSON.

| ID | Input class | Applied to | Risk |
|---|---|---|---|
| NU-01 | `0` | every numeric argument in turn | MED |
| NU-02 | negative | `gross_floor_area_m2` *(known FAIL — deletes a $16,081 charge)* | HIGH |
| NU-03 | negative | `floor_area_sqm` *(known FAIL — returns −12 spaces)* | HIGH |
| NU-04 | negative | `development_cost`, `seats`, `num_employees`, `spaces_provided` | HIGH |
| NU-05 | `inf` | `development_cost` *(known FAIL — uncaught OverflowError)* | HIGH |
| NU-06 | `nan` | `development_cost` *(known FAIL — uncaught UnboundLocalError)* | HIGH |
| NU-07 | `-inf` | `development_cost` *(known FAIL — emits invalid JSON)* | HIGH |
| NU-08 | `1e308` | any area or cost | MED |
| NU-09 | fractional (`80.5`) | areas and counts — is a half-seat rejected? | LOW |
| NU-10 | numeric string (`"80"`) | any number argument | LOW |
| NU-11 | `$5,000` / `$5,001` | fee bracket boundary | MED |
| NU-12 | `$50,000` / `$50,001` | fee bracket boundary | MED |
| NU-13 | `$250,000` / `$250,001` | boundary — run 1 measured a $394 cliff on $1 | MED |
| NU-14 | `$500,000` / `$500,001` | fee bracket boundary | MED |
| NU-15 | `$1,000,000` / `$1,000,001` | fee bracket boundary | MED |
| NU-16 | `$10,000,000` / `$10,000,001` | top bracket boundary | LOW |
| NU-17 | area just under / over 100m² | contribution charged per 100m² — rounding direction | HIGH |
| NU-18 | `neighbourhood shop` at 199 / 200 / 201 m² | cl 5.4(7) threshold | HIGH |
| NU-19 | secondary dwelling at 59 / 60 / 61 m² | cl 5.4(9), and that cl 4.6 cannot vary it | MED |
| NU-20 | every numeric property declares a `minimum` | schema-level; a test, not a call | HIGH |

---

# SE — The SEE tools (20)

Barely touched in run 1, and these are the tools that take an applicant's name and address.

**SE-01…SE-05 — Template scope.** The Council form covers **Minor Development only**: single-storey
dwellings, single-storey residential additions, ancillary structures, and strata subdivision of an
existing building. **Passes if** each in-scope type fills, and every out-of-scope proposal
(commercial, change of use, multi-storey) is refused and redirected to `generate_see_draft`.
**Fails if** a business change of use reaches the residential form. **Risk: HIGH**

**SE-06…SE-09 — Geometry discovery.** The template has no AcroForm fields; boxes are found at fill
time. **Passes if** `SEE_LAYOUT_EXPECTED` per-page counts hold, tick boxes map to the right
questions, and a reissued form fails loudly rather than writing into the wrong place. **Risk: HIGH**

**SE-10…SE-12 — Overflow.** Long answers shrink to 6.5pt and then overflow. **Passes if** overflow
is reported *and* auto-ticks the page-1 "supporting information attached" box. **Risk: MED**

**SE-13…SE-16 — Draft quality for a business.** `generate_see_draft` for a commercial change of use.
**Passes if** it engages with the site's real constraints (flood, heritage, bushfire), its parking
figure comes from `parking.estimate_spaces` rather than being hand-rolled, and every placeholder is
clearly bracketed. **Fails if** it asserts anything the tools would refuse to assert — the phantom
"CBD exemption precinct" is the known instance. **Risk: HIGH**

**SE-17…SE-20 — Privacy under `PUBLIC_MODE`.** The branch that has never run in production.
**Passes if** the PDF is written to a per-request temp dir, returned inline as base64, and deleted;
nothing lands in `documents/output/`; no applicant name, address or filename appears in any log
line; and two concurrent fills of the same filename cannot interleave into a half-written PDF.
**Risk: HIGH** — this is the only place applicant PII enters the system.

---

# DO — Document search and retrieval (15)

Zero coverage in run 1, and the fallback for every chapter with no structured tool.

| ID | Scenario | Passes if | Risk |
|---|---|---|---|
| DO-01 | Search a phrase known to be in Ch 7 | it is found, with a usable `location` | MED |
| DO-02 | Feed that `location` to `read_dcp_section` | the round trip works for a PDF page | MED |
| DO-03 | Same for a `.txt` source | the round trip works by line | MED |
| DO-04 | Partial concept match ("weather protection awning") | scoring surfaces it without an exact phrase | MED |
| DO-05 | Query matching a known junk/404 extract | junk does not surface as an answer | HIGH |
| DO-06 | Search scoped by category | `DOC_CATEGORIES` respected | LOW |
| DO-07 | `list_documents` | every listed file exists and opens | MED |
| DO-08 | Search for DCP Ch 2 content (no structured tool) | commercial controls are reachable | HIGH |
| DO-09 | Search for Ch 15 waste content | reachable | MED |
| DO-10 | Search for Ch 12 heritage controls | reachable, and the answer is not the HIS assertion | HIGH |
| DO-11 | Search for Ch 3 industrial setbacks | reachable | MED |
| DO-12 | Query with only stopwords | refuses rather than returning noise | LOW |
| DO-13 | Query matching nothing | says so; no empty-result-as-answer | MED |
| DO-14 | A superseded LEP 2000 chapter | the edition is disclosed in the result | HIGH |
| DO-15 | Search index missing at boot | degrades to a stated fallback, never a traceback | MED |

---

# RV — Rural, village and industrial (20)

One scenario between them in run 1, and the controls differ sharply from the CBD cases.

| ID | Situation | Passes if | Risk |
|---|---|---|---|
| RV-01 | Shop in Nimbin (RU5) | RU5 table used; Part B Ch 6 Nimbin raised | MED |
| RV-02 | Café in a village outside Nimbin | RU5 without Nimbin-specific controls | MED |
| RV-03 | Farm gate sales, RU1 | the right defined term, not "shop" | HIGH |
| RV-04 | Roadside stall | its own definition and cl 5.4 limit | MED |
| RV-05 | Cellar door at a vineyard | artisan food and drink industry | HIGH |
| RV-06 | Farm stay accommodation | RU1 permissibility; note R2 prohibits it | MED |
| RV-07 | Agritourism | whether the term exists in this LEP at all | HIGH |
| RV-08 | Rural industry vs light industry | the distinction is surfaced, not resolved silently | HIGH |
| RV-09 | Contribution in a rural catchment | ~20% above urban, and the catchment is never assumed | HIGH |
| RV-10 | Unsewered site | s68 raised; run 1 found it over-suppressed | MED |
| RV-11 | Bushfire prone rural land | constraint reported; exempt pathways closed | HIGH |
| RV-12 | RU1 minimum lot size | returned in hectares, not m² | MED |
| RV-13 | Warehouse in E4 | table and parking agree | MED |
| RV-14 | Light industry in E3 | permitted; check both singular and plural | HIGH |
| RV-15 | Industrial setbacks | DCP Ch 3 reachable at all | MED |
| RV-16 | Wyrallah Rd / Airport estates | Part B chapters raised | LOW |
| RV-17 | Vehicle body repair in E3 vs E4 | the zones differ; the answer should | MED |
| RV-18 | Depot vs warehouse | definitions distinguished | MED |
| RV-19 | Rural front setback | 15m, or 28m on a named RMS road | MED |
| RV-20 | Rural change of use with no works | Item 2.7 flat fee, not Item 2.1 | MED |

---

# RD — Residential-adjacent business (15)

The overlap zone, where a business proposal meets residential controls.

| ID | Situation | Passes if | Risk |
|---|---|---|---|
| RD-01 | Shop top housing, CBD | **no parking required** *(known FAIL — the use is absent from the data)* | HIGH |
| RD-02 | Shop top housing, outside CBD | 1 or 2 per dwelling by GFA | MED |
| RD-03 | Shop top housing private open space | ≥20m², directly accessible | LOW |
| RD-04 | Home business vs home occupation | distinguished, with the consent difference | HIGH |
| RD-05 | Home industry | distinguished from home business | MED |
| RD-06 | Home occupation (sex services) | handled factually; it is a defined term | LOW |
| RD-07 | Working from home, no clients | whether consent is needed at all | MED |
| RD-08 | Boarding house | the affordable-housing and registered-provider limbs | HIGH |
| RD-09 | Secondary dwelling | Housing SEPP caveat where the table omits it | HIGH |
| RD-10 | Secondary dwelling max GFA | greater of 60m² or 25%, and cl 4.6 cannot vary it | MED |
| RD-11 | B&B accommodation | permissibility and parking | MED |
| RD-12 | Childcare in R2 | permitted with consent; check the plural | HIGH |
| RD-13 | Small lot housing side setback | 0.9m (A26.3), lots under 400m² only | MED |
| RD-14 | Side/rear setback on an ordinary lot | reported as **not set** by Chapter 1 | HIGH |
| RD-15 | Site coverage maximum | reported as not set; the control is 40% landscaping (A7.1) | HIGH |

---

# SU — Subdivision and modification (15)

No coverage in run 1.

| ID | Situation | Passes if | Risk |
|---|---|---|---|
| SU-01 | s4.55(1) — correcting a minor error | the three modification types are distinguished | MED |
| SU-02 | s4.55(1A) — minimal environmental impact | correct threshold | MED |
| SU-03 | s4.55(2) — substantially the same development | the test is stated | HIGH |
| SU-04 | Modifying consent to extend trading hours | which subsection, and what it needs | HIGH |
| SU-05 | Modification fee | how it is calculated | MED |
| SU-06 | Strata subdivision of an existing building | **in** the Minor Development SEE scope | MED |
| SU-07 | Torrens subdivision of an urban lot | DCP Ch 5A raised | MED |
| SU-08 | Commercial/industrial subdivision | DCP Ch 5B raised | MED |
| SU-09 | Rural/village subdivision | DCP Ch 6 raised | MED |
| SU-10 | Subdivision certificate | distinguished from consent | MED |
| SU-11 | Lot below the minimum lot size | cl 4.6 pathway explained, not promised | HIGH |
| SU-12 | Subdivision contribution | charged per lot, not per m² | HIGH |
| SU-13 | Boundary adjustment | whether it is subdivision at all | MED |
| SU-14 | Community title | distinguished from strata | LOW |
| SU-15 | Subdivision of flood-affected land | LEP cl 5.21 applies to subdivision too | HIGH |

---

# PA — Post-approval and operational (10)

Consent is not permission to build, occupy or trade. Run 1 touched this once.

| ID | Situation | Passes if | Risk |
|---|---|---|---|
| PA-01 | Construction Certificate | can be *applied for* before consent, issued only after *(known contradiction)* | MED |
| PA-02 | Appointing a PCA | at least 2 days before work starts | MED |
| PA-03 | Mandatory inspections | listed, and tied to CC conditions | LOW |
| PA-04 | Occupation Certificate | required before occupation or use | HIGH |
| PA-05 | Trading before the OC issues | stated as a real risk, not glossed | HIGH |
| PA-06 | Conditions of consent | how to read them; deferred commencement | MED |
| PA-07 | Food premises registration timing | after fitout, before trading | MED |
| PA-08 | Annual fire safety statement | ongoing obligation, not one-off | MED |
| PA-09 | Trade waste agreement timing | before connection, and the fitout implications | MED |
| PA-10 | s68 approvals | which ones survive a change of use | MED |

---

# JN — Full journeys (10)

The highest-yield shape in run 1. Each is a complete run of **8–12 calls** in the order an applicant
would make them, judged on whether the answers cohere — not on any single one.

**Passes if** every tool agrees with every other, no figure changes without explanation, every
refusal is redirected, and the composed output could be taken to Council. **Fails if** any two
answers cannot both be true.

- **JN-01** — Café in a CBD heritage shopfront, flood affected. The archetype: change of use,
  heritage, flood, CBD parking, contributions, signage, food registration.
- **JN-02** — Gym in an E3 warehouse. Change of use, industrial zone, parking by a different rate.
- **JN-03** — Childcare centre in a village. Permissibility (plural!), cl 5.22, referrals, parking
  by children, flood.
- **JN-04** — Brewery with a cellar door on RU1 land. Definitional ambiguity, rural catchment, s68,
  bushfire.
- **JN-05** — Retail to medical centre. Parking by practitioners, contributions on the increase,
  access compliance.
- **JN-06** — Restaurant expanding 100m² → 140m². Floor area increase, contributions *(known
  FAIL)*, flood §8.3 not reaching the addition, parking on the increase.
- **JN-07** — Office to co-working. Low-drama control case; should be clean end to end.
- **JN-08** — Hairdresser fitout in a local centre. Vocabulary *(known FAIL)*, trade waste
  *(known FAIL)*, signage.
- **JN-09** — Bottle shop with a liquor licence. Permissibility, licence as a non-Council approval,
  hours, amenity.
- **JN-10** — A proposal that should be refused early: a use genuinely prohibited, on land genuinely
  constrained. **Passes if** the tools say so plainly and early, rather than producing a complete
  application for something that cannot be approved.

---

# OP — Operations, privacy and transport (10)

The layer `PLAN.md` records as healthy but unverified under real use.

| ID | Scenario | Passes if | Risk |
|---|---|---|---|
| OP-01 | `PUBLIC_MODE` file handling | temp dir, base64 inline, deleted; never `documents/output/` | HIGH |
| OP-02 | Applicant data in logs | structurally impossible, not merely absent | HIGH |
| OP-03 | Five concurrent handler calls | no corruption; ~0.3s not ~1.5s | MED |
| OP-04 | Two concurrent fills, same filename | `os.replace` prevents a half-written PDF | HIGH |
| OP-05 | Rate limiter | 30 requests / 60s per IP, and it engages | MED |
| OP-06 | `/health` under load | does not stall behind a running tool | MED |
| OP-07 | Stateless HTTP session | a real MCP client completes a session over both transports | HIGH |
| OP-08 | Search index absent at boot | reports `absent` and degrades, never crashes | MED |
| OP-09 | `LISMORE_ADDRESS_LOOKUP=off` | address tools disabled cleanly with a stated fallback | MED |
| OP-10 | Network failure mid-lookup | returns an `error` + `fallback` payload; **nothing in `addresses.py` ever raises** | HIGH |

---

## Running this suite

Same method as run 1 — batch by group across parallel agents, one group per agent, results to a
scratchpad file per batch, then **re-verify every finding by hand against the source before
recording it.** Three agent claims did not survive that check in run 1; one was nearly dismissed on
a check of mine that was too crude. Both directions of error are real.

Two rules carried forward, and one added:

- **Agents test; they do not repair.** No file in the repository is modified during a run.
- **Record actual output, not a summary of it.** A scenario that passes on a reading of the code and
  fails when run is the whole point.
- **New: do not run this suite against a tree with uncommitted fixes in it.** Run 1's value came
  from testing what is deployed, not what is intended. Fix on a branch, then re-run both suites.

## Expected outcome

If Phase S lands first, **LU, XT and NU should largely pass** — they are the swept versions of what
it fixes, and a low failure rate there is the evidence Phase S worked. **SE, DO, OP, RV, SU and PA
are genuinely unknown**; nothing in this repository has tested them, and run 1's central lesson was
that the file nobody has looked at is not the file nobody needs to look at.

The groups to watch are **DO-08…DO-11 and RV**, because they probe the chapters with no structured
tooling. If search cannot reach DCP Chapters 2, 3, 12 and 15 usefully, then the content gap is worse
than `ROADMAP.md` Phase D assumes — the fallback does not work either.
