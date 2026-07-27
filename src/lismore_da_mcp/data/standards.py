"""Residential development standards from Lismore DCP Chapter 1."""

RESIDENTIAL_STANDARDS = {
    "setbacks": {
        "front": {
            "general": "Match established building line OR minimum 4.5m to articulated facade, 6m to garage",
            "corner_lots": "Secondary frontage: minimum 3m, or 1.5m for walls with no major openings",
            "battle_axe": "5m from access handle boundary",
        },
        "side": {
            "single_storey": "0.9m minimum (can be nil for attached dwellings)",
            "two_storey": "Minimum 0.9m ground floor, 1.5m upper floors OR comply with building envelope",
            "building_envelope": "Setback increases with height at 45° angle from boundary at 2.4m height",
        },
        "rear": {
            "general": "Minimum 3m for single storey, 6m for two storey",
            "corner_lots": "May be reduced where secondary street frontage provides address",
        },
    },
    "site_coverage": {
        "R1_R2_R3": "Maximum 50% (higher densities may allow more with design excellence)",
        "R5_large_lot": "Generally no maximum but buildings should cluster near road frontage",
        "notes": "Site coverage = total building footprint / site area × 100%",
    },
    "building_height": {
        "general": "8.5m or 2 storeys, whichever is less (check Height of Buildings Map for variations)",
        "exceptions": "Some precincts allow 9m or more — always verify against LEP Height Map",
    },
    "private_open_space": {
        "dwelling_house": "Minimum 80m² with minimum dimension 5m, directly accessible from living area",
        "attached_dwelling": "Minimum 35m² per dwelling with minimum dimension 4m",
        "apartment": "Minimum 10m² balcony per dwelling with minimum dimension 2.4m",
    },
    "landscaping": {
        "front_setback": "Minimum 50% soft landscaping (grass, garden beds, trees)",
        "deep_soil": "Minimum 15% of site as deep soil zone (no structures/paving above or below)",
    },
    "car_parking_design": {
        "garage_width": "Maximum 50% of building frontage width",
        "driveway_width": "Maximum 3m for single dwelling, 5.5m for dual crossover",
        "garage_setback": "Minimum 5.5m from front boundary (to allow car in front of garage door)",
    },
}
