"""Flood planning levels and floor level requirements (DCP Chapter 8, LEP cl 5.21)."""

FLOOD_PLANNING = {
    "flood_planning_level": "1% AEP (1-in-100 year) flood level + 500mm freeboard",
    "proposed_fpl": "1% AEP 2090 climate change level + 500mm freeboard (~13.4m in high-risk areas)",
    "residential_requirement": "All habitable floor areas must be at or above the Flood Planning Level",
    "commercial_requirement": "Minimum 25% of gross floor area must be above the Flood Planning Level",
    "cbd_exemption": {
        "applies_to": "Lismore CBD Development Exemption Precinct",
        "allows": "Shop-top housing and tourist accommodation",
        "conditions": [
            "Habitable floor levels above FPL",
            "Structural soundness proven",
            "Site-specific evacuation plan prepared",
            "Refuge available above Probable Maximum Flood (PMF)"
        ]
    },
    "advice": "Always consult Duty Planner regarding Clause 5.21 flood planning requirements before lodging DA"
}
