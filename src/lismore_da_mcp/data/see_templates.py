"""Section-by-section guidance for writing a Statement of Environmental Effects."""

SEE_TEMPLATES = {
    "site_description": {
        "heading": "Site Description",
        "prompts": [
            "Property address and legal description (Lot/DP)",
            "Site area (m²) and dimensions",
            "Current improvements (buildings, structures, vegetation)",
            "Topography and natural features",
            "Surrounding land uses and character",
            "Access arrangements (existing driveways, road frontage)",
        ],
    },
    "proposal_description": {
        "heading": "Proposed Development",
        "prompts": [
            "Type of development (new building, alteration, change of use, subdivision)",
            "Proposed use(s) and operational details",
            "Building dimensions (height, setbacks, site coverage, GFA)",
            "Materials and finishes",
            "Parking and access arrangements",
            "Landscaping and open space",
            "Hours of operation (if applicable)",
            "Number of employees/residents/customers (if applicable)",
        ],
    },
    "planning_framework": {
        "heading": "Planning Framework Assessment",
        "prompts": [
            "Zoning and permissibility under LEP",
            "Compliance with LEP development standards (height, FSR, lot size)",
            "Clause 4.6 variation request (if non-compliant)",
            "Applicable State Environmental Planning Policies (SEPPs)",
            "DCP compliance (setbacks, parking, design, landscaping)",
        ],
    },
    "environmental_impacts": {
        "heading": "Environmental Impact Assessment",
        "prompts": [
            "Visual impact and streetscape compatibility",
            "Privacy impacts on neighbours (windows, balconies, overlooking)",
            "Overshadowing impacts (shadow diagrams for 2+ storey)",
            "Traffic and parking impacts",
            "Noise and acoustic impacts",
            "Stormwater and drainage",
            "Vegetation impacts and tree removal",
            "Heritage impacts (if heritage item or conservation area)",
            "Flooding impacts (if flood-prone land)",
            "Contamination (if previous industrial/commercial use)",
        ],
    },
    "mitigation_measures": {
        "heading": "Mitigation Measures",
        "prompts": [
            "Design measures to minimise impacts",
            "Construction management (hours, noise, sediment control)",
            "Operational management (waste, deliveries, hours)",
            "Conditions of consent that would address impacts",
        ],
    },
    "section_4_15_matters": {
        "heading": "Section 4.15 Matters for Consideration",
        "prompts": [
            "(a)(i) Environmental planning instruments (LEP, SEPPs)",
            "(a)(ii) Draft environmental planning instruments",
            "(a)(iii) Development control plans",
            "(a)(iiia) Planning agreements",
            "(a)(iv) Regulations",
            "(b) Likely impacts (built environment, natural environment, social, economic)",
            "(c) Suitability of the site",
            "(d) Submissions (note: will be addressed after exhibition)",
            "(e) Public interest",
        ],
    },
}
