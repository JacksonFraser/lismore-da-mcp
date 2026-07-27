# MCP Server Tool Evaluation

## Test Scenario: Opening a Café in Lismore

**User Profile**: First-time applicant with no planning knowledge
**Goal**: Understand requirements to open a café in Lismore CBD

---

## The Journey

### Step 1: What is a "café" in planning terms?

**Tool Used**: `get_definition`
**Query**: `{"term": "cafe"}`

**Result**:
```json
{
  "error": "No definition found for 'cafe'",
  "similar_terms": ["restaurant or cafe"],
  "available_terms": [27 terms listed]
}
```

**Evaluation**:
- **Helpful**: Yes - it didn't just fail, it suggested the correct term "restaurant or cafe"
- **Issue**: User has to try again with corrected term
- **Improvement**: Could auto-match partial terms or common synonyms

---

### Step 2: Get the correct definition

**Tool Used**: `get_definition`
**Query**: `{"term": "restaurant or cafe"}`

**Result**: Full definition explaining it's a "food and drink premises" that provides seating for on-premises consumption.

**Evaluation**:
- **Helpful**: Yes - clear definition with related terms
- **Good**: Shows hierarchy (restaurant or cafe → food and drink premises)

---

### Step 3: What zones exist?

**Tool Used**: `list_zones`

**Result**: 17 active zones categorized by type (residential, employment, etc.)

**Evaluation**:
- **Helpful**: Yes - clear overview
- **Good**: Shows legacy codes (B1, B2, B3) redirect to new codes
- **Missing**: No guidance on "which zone would suit a café"

---

### Step 4: Can I open a café in E2 (CBD)?

**Tool Used**: `check_permissibility`
**Query**: `{"land_use": "restaurant or cafe", "zone_code": "E2"}`

**Result**:
```json
{
  "permissibility": "likely_permitted_with_consent",
  "detail": "'restaurant or cafe' is not explicitly listed but Zone E2 permits
             'any other development not specified'",
  "advice": "Confirm with Council Duty Planner"
}
```

**Evaluation**:
- **Issue Found**: This is technically correct but misleading
- **Problem**: "Restaurant or cafe" IS permitted in E2, just via the parent term "Commercial premises"
- **Root Cause**: The permissibility checker doesn't understand hierarchical land use definitions:
  - `restaurant or cafe` ⊂ `food and drink premises` ⊂ `commercial premises`
- **Impact**: User might think café is uncertain when it's clearly permitted
- **Fix Needed**: Implement hierarchical matching - if "commercial premises" is permitted and user asks about "café", recognize café falls under that umbrella

---

### Step 5: Check parent term "commercial premises"

**Tool Used**: `check_permissibility`
**Query**: `{"land_use": "commercial premises", "zone_code": "E2"}`

**Result**:
```json
{
  "permissibility": "permitted_with_consent",
  "detail": "'Commercial premises' is permitted with development consent in Zone E2",
  "next_steps": "A Development Application is required for this use."
}
```

**Evaluation**:
- **Works correctly** for the parent term
- **User Experience**: Poor - user shouldn't need to know the technical hierarchy

---

### Step 6: Parking requirements

**Tool Used**: `get_parking_rates`
**Query**: `{"development_type": "cafe"}`

**Result**:
```json
{
  "parking_spaces": "1 per 10m²",
  "rate_description": "1 space per 10m² dining area"
}
```

**Evaluation**:
- **Excellent**: Direct answer with clear rate
- **Helpful**: Also shows restaurant has slightly different requirements (+ staff parking)
- **Missing**: No info about CBD parking reductions or contribution-in-lieu options

---

### Step 7: DA fees

**Tool Used**: `calculate_da_fees`
**Query**: `{"development_cost": 50000}`

**Result**:
```json
{
  "estimated_fee": 355.00,
  "cost_estimate_requirement": "Applicant estimate",
  "note": "Additional fees may apply..."
}
```

**Evaluation**:
- **Excellent**: Clear answer with context
- **Good**: Notes additional fees exist (advertising, s7.11, etc.)
- **Helpful**: Shows cost estimate requirements

---

### Step 8: Document checklist

**Tool Used**: `get_da_checklist`
**Query**: `{"development_type": "change_of_use"}`

**Result**:
- 6 base documents
- 3 type-specific documents
- 6 conditional documents with triggers

**Evaluation**:
- **Excellent**: Comprehensive and well-structured
- **Good**: Conditional documents explain when they're needed
- **Helpful**: Shows Planning Portal URL for lodgement

---

### Step 9: SEE template

**Tool Used**: `get_see_template`
**Query**: `{"section": "site_description"}`

**Result**: 6 specific prompts for what to include in the site description section.

**Evaluation**:
- **Excellent**: Actionable guidance
- **Helpful**: User knows exactly what to write
- **Good**: All 6 SEE sections available

---

### Step 10: Flood requirements

**Tool Used**: `get_flood_requirements`
**Query**: `{"development_type": "cbd"}`

**Result**:
- FPL: 1% AEP + 500mm freeboard
- CBD exemption conditions
- Advice to consult Duty Planner

**Evaluation**:
- **Good**: Highlights CBD exemption for shop-top housing
- **Helpful**: Warns about consulting Duty Planner
- **Missing**: Doesn't say whether the specific property is flood-affected

---

### Step 11: Referral requirements

**Tool Used**: `check_referrals`
**Query**: `{"development_characteristics": ["heritage", "significant_traffic"]}`

**Result**:
- Heritage Council referral triggered → needs HIS
- Transport NSW triggered → needs TIA

**Evaluation**:
- **Excellent**: Shows exactly what triggers each referral
- **Helpful**: Lists required documents for each authority
- **Good**: Clear warning that Council confirms final requirements

---

### Step 12: Contact information

**Tool Used**: `get_contact_info`

**Result**:
- Phone, address, hours
- Duty Planner: Tuesdays/Thursdays 8:30-10:30am
- Pre-lodgement form URL
- DA Tracker URL

**Evaluation**:
- **Excellent**: Complete and actionable
- **Helpful**: Free duty planner consultation - no appointment needed

---

### Step 13: DCP search

**Tool Used**: `search_dcp`
**Query**: `{"query": "food premises commercial"}`

**Result**: Found 5 results across multiple DCP chapters with context.

**Evaluation**:
- **Good**: Fuzzy matching works (found "commercial premises" and "food")
- **Helpful**: Shows page numbers and context snippets
- **Issue**: Results are generic - hard to find specific café requirements

---

## Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| **Definitions lookup** | 8/10 | Works well, suggests corrections, but needs synonym matching |
| **Zone information** | 9/10 | Comprehensive data, legacy code support |
| **Permissibility checking** | 9/10 | **FIXED** - now understands hierarchical land uses (cafe→commercial premises) |
| **Parking rates** | 9/10 | Excellent, direct answers |
| **Fee calculation** | 10/10 | Accurate, includes context |
| **Document checklist** | 9/10 | Well-structured, conditional logic |
| **SEE templates** | 9/10 | Actionable prompts |
| **Flood requirements** | 7/10 | Good info but not site-specific |
| **Referral checking** | 8/10 | Clear triggers and documents |
| **Contact info** | 10/10 | Complete with duty planner details |
| **DCP search** | 7/10 | Works but results can be noisy |

**Overall: 8.7/10** (up from 8.3 after permissibility fix)

---

## Critical Issues Found

### 1. ~~Permissibility Checker Doesn't Understand Hierarchies~~ FIXED

**Problem**: When checking "restaurant or cafe" in E2, it said "likely permitted" via catch-all instead of recognizing it's explicitly permitted under "Commercial premises".

**Status**: **FIXED** - Implemented hierarchical term matching.

**Result After Fix**:
```json
{
  "land_use": "cafe",
  "zone_code": "E2",
  "permissibility": "permitted_with_consent",
  "detail": "'cafe' falls under 'Commercial premises' which is permitted with development consent in Zone E2",
  "classification": "'cafe' is a type of 'commercial premises'"
}
```

The tool now correctly recognizes that:
- `cafe` → `restaurant or cafe` → `food and drink premises` → `commercial premises`
- If any parent term is permitted, the child term is also permitted

### 2. No Property-Specific Constraint Lookup (MEDIUM PRIORITY)

**Problem**: Can't determine from an address:
- What zone the property is in
- Whether it's flood-affected
- Whether it's a heritage item

**Impact**: User must manually check Planning Portal or call Council.

**Fix**: Would require NSW Planning Portal API integration or manual precinct data.

### 3. Parking Tool Doesn't Know About CBD Reductions (LOW PRIORITY)

**Problem**: Returns standard rate but CBD often has:
- Reduced requirements
- Contribution-in-lieu options
- Shared parking arrangements

**Fix**: Add location context parameter and CBD-specific variations.

---

## What Worked Well

1. **Definition lookup with suggestions** - guided user to correct term
2. **Fee calculator** - accurate and contextual
3. **Document checklist** - comprehensive with conditional logic
4. **SEE templates** - actionable writing prompts
5. **Referral checker** - clear triggers and document requirements
6. **Contact info** - complete with duty planner availability
7. **Zone information** - full permissibility tables with legacy support

---

## Recommendations

### Immediate (Before Release)
1. **Fix hierarchical permissibility** - critical for user confidence
2. **Add common term synonyms** to definition lookup (cafe→restaurant or cafe, shop→retail premises)

### Short-term
3. **Add parking variations** for CBD/heritage/shared parking scenarios
4. **Improve DCP search** with category filtering (residential vs commercial)

### Medium-term
5. **Site constraint checker** using precinct-based data (if API unavailable)
6. **Heritage item lookup** - parse Schedule 5 into searchable index

### Long-term
7. **Integration with NSW Planning Portal** for live zone/constraint data
8. **DA cost estimator** with rough per-m² rates for common fit-outs

---

## End-to-End Workflow Assessment

| Workflow Stage | Tool Support | Gap |
|----------------|--------------|-----|
| "What can I build here?" | Partial | Can't lookup property constraints |
| "Is my use permitted?" | Good | **FIXED** - hierarchical matching now works |
| "What documents do I need?" | Excellent | Comprehensive checklist |
| "How do I write the SEE?" | Good | Templates for all sections |
| "What parking do I need?" | Good | No CBD variations |
| "What will it cost?" | Good | Fees accurate, no fit-out cost guidance |
| "Any special approvals?" | Good | Referral triggers clear |
| "Who do I contact?" | Excellent | Duty planner details included |

**Verdict**: The tools support the middle of the workflow well (documents, SEE, fees, referrals) but struggle at the beginning (property lookup, permissibility) where users need the most help.

---

*Generated: July 2026*
*Test conducted using MCP server v1.0 with 18 tools*
