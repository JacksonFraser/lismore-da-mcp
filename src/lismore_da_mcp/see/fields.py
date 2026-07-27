"""Field map, questions and scope rules for the official Lismore SEE form.

Indices refer to the rectangles discovered by see.layout, in reading order.
"""

# page = 0-based page index; box/check = index into that page's discovered rects
SEE_FORM_FIELDS = {
    # Page 1 - Application Details
    "supporting_info_attached": {"page": 0, "check": 0},
    "applicant_name": {"page": 0, "box": 0},
    "address_number": {"page": 0, "box": 1},
    "street_name": {"page": 0, "box": 2},
    "building_name": {"page": 0, "box": 3},
    "suburb": {"page": 0, "box": 4},
    "lot": {"page": 0, "box": 5},
    "dp": {"page": 0, "box": 6},
    "section": {"page": 0, "box": 7},

    # Page 2 - Descriptions
    "description_of_development": {"page": 1, "box": 0},
    "description_of_site": {"page": 1, "box": 1},
    "present_previous_use": {"page": 1, "box": 2},

    # Page 3 - Natural hazards, constraints, surrounding land use
    "bushfire_prone": {"page": 2, "check": 0},
    "flooding": {"page": 2, "check": 1},
    "hazards_comments": {"page": 2, "box": 0},
    "constraints": {"page": 2, "box": 1},
    "surrounding_land_use": {"page": 2, "box": 2},

    # Page 3 - Planning Controls
    "permissible_yes": {"page": 2, "check": 2},
    "permissible_no": {"page": 2, "check": 3},
    "zone_objectives_yes": {"page": 2, "check": 4},
    "zone_objectives_no": {"page": 2, "check": 5},
    "dcp_accordance_yes": {"page": 2, "check": 6},
    "dcp_accordance_no": {"page": 2, "check": 7},

    # Page 4 - Planning comments
    "planning_comments": {"page": 3, "box": 0},

    # Page 4 - Context and Setting
    "visually_prominent_yes": {"page": 3, "check": 0},
    "visually_prominent_no": {"page": 3, "check": 1},
    "inconsistent_streetscape_yes": {"page": 3, "check": 2},
    "inconsistent_streetscape_no": {"page": 3, "check": 3},
    "out_of_character_yes": {"page": 3, "check": 4},
    "out_of_character_no": {"page": 3, "check": 5},
    "inconsistent_land_use_yes": {"page": 3, "check": 6},
    "inconsistent_land_use_no": {"page": 3, "check": 7},
    "setback_variation_yes": {"page": 3, "check": 8},
    "setback_variation_no": {"page": 3, "check": 9},
    "context_comment": {"page": 3, "box": 1},

    # Page 4 - Privacy, Views and Overshadowing
    "privacy_issues_yes": {"page": 3, "check": 10},
    "privacy_issues_no": {"page": 3, "check": 11},
    "overshadowing_yes": {"page": 3, "check": 12},
    "overshadowing_no": {"page": 3, "check": 13},
    "acoustic_issues_yes": {"page": 3, "check": 14},
    "acoustic_issues_no": {"page": 3, "check": 15},
    "views_impact_yes": {"page": 3, "check": 16},
    "views_impact_no": {"page": 3, "check": 17},
    "privacy_comments": {"page": 3, "box": 2},

    # Page 5 - Access, Traffic and Utilities
    "legal_access_yes": {"page": 4, "check": 0},
    "legal_access_no": {"page": 4, "check": 1},
    "increase_traffic_yes": {"page": 4, "check": 2},
    "increase_traffic_no": {"page": 4, "check": 3},
    "traffic_amount": {"page": 4, "box": 0},
    "additional_access_yes": {"page": 4, "check": 4},
    "additional_access_no": {"page": 4, "check": 5},
    "parking_addressed_yes": {"page": 4, "check": 6},
    "parking_addressed_no": {"page": 4, "check": 7},
    "utilities_available_yes": {"page": 4, "check": 8},
    "utilities_available_no": {"page": 4, "check": 9},
    "access_comments": {"page": 4, "box": 1},

    # Page 5 - Environmental Impacts
    "air_pollution_yes": {"page": 4, "check": 10},
    "air_pollution_no": {"page": 4, "check": 11},
    "water_pollution_yes": {"page": 4, "check": 12},
    "water_pollution_no": {"page": 4, "check": 13},
    "noise_impacts_yes": {"page": 4, "check": 14},
    "noise_impacts_no": {"page": 4, "check": 15},
    "excavation_yes": {"page": 4, "check": 16},
    "excavation_no": {"page": 4, "check": 17},
    "erosion_yes": {"page": 4, "check": 18},
    "erosion_no": {"page": 4, "check": 19},
    "contamination_yes": {"page": 4, "check": 20},
    "contamination_no": {"page": 4, "check": 21},
    "sustainable_yes": {"page": 4, "check": 22},
    "sustainable_no": {"page": 4, "check": 23},
    "heritage_impact_yes": {"page": 4, "check": 24},
    "heritage_impact_no": {"page": 4, "check": 25},
    "aboriginal_yes": {"page": 4, "check": 26},
    "aboriginal_no": {"page": 4, "check": 27},
    "environmental_comments": {"page": 4, "box": 2},

    # Page 6 - Flora and Fauna
    "remove_vegetation_yes": {"page": 5, "check": 0},
    "remove_vegetation_no": {"page": 5, "check": 1},
    "threatened_species_yes": {"page": 5, "check": 2},
    "threatened_species_no": {"page": 5, "check": 3},
    "flora_comments": {"page": 5, "box": 0},

    # Page 6 - Waste and Stormwater Disposal
    "effluent_yes": {"page": 5, "check": 4},
    "effluent_no": {"page": 5, "check": 5},
    "trade_waste_yes": {"page": 5, "check": 6},
    "trade_waste_no": {"page": 5, "check": 7},
    "hazardous_waste_yes": {"page": 5, "check": 8},
    "hazardous_waste_no": {"page": 5, "check": 9},
    "stormwater_council": {"page": 5, "check": 10},
    "stormwater_other": {"page": 5, "check": 11},
    "stormwater_details": {"page": 5, "box": 1},
    "rainwater_tanks_yes": {"page": 5, "check": 12},
    "rainwater_tanks_no": {"page": 5, "check": 13},
    "overland_risks_yes": {"page": 5, "check": 14},
    "overland_risks_no": {"page": 5, "check": 15},
    "waste_comments": {"page": 5, "box": 2},

    # Page 6 - Social and Economic Impacts
    "economic_social_yes": {"page": 5, "check": 16},
    "economic_social_no": {"page": 5, "check": 17},
    "crime_prevention_yes": {"page": 5, "check": 18},
    "crime_prevention_no": {"page": 5, "check": 19},

    # Page 7 - Social comments, other matters, declaration
    # Boxes 2 and 3 are the signature boxes - left blank for wet signing.
    "social_comments": {"page": 6, "box": 0},
    "other_matters": {"page": 6, "box": 1},
    "declaration_name_1": {"page": 6, "box": 4},
    "declaration_name_2": {"page": 6, "box": 5},
    "declaration_date_1": {"page": 6, "box": 6},
    "declaration_date_2": {"page": 6, "box": 7},
}

SEE_QUESTIONS = {
    "permissible": "Is your proposal permissible in the zone?",
    "zone_objectives": "Is your proposal consistent with the zone objectives?",
    "dcp_accordance": "Is your proposal in accordance with the relevant development control plan?",
    "visually_prominent": "Will the development be visually prominent in the surrounding area?",
    "inconsistent_streetscape": "Will the development be inconsistent with the existing streetscape?",
    "out_of_character": "Will the development be out of character with the surrounding area?",
    "inconsistent_land_use": "Will the development be inconsistent with surrounding land uses?",
    "setback_variation": "Is the development a variation to the Building Line Setbacks?",
    "privacy_issues": "Will the development result in any privacy issues between adjoining properties?",
    "overshadowing": "Will the development overshadow adjoining properties and affect solar access?",
    "acoustic_issues": "Will the development result in any acoustic issues between adjoining properties?",
    "views_impact": "Will the development impact on views from adjoining or nearby properties and public places?",
    "legal_access": "Is legal and practical access available to the development?",
    "increase_traffic": "Will the development increase local traffic movements/volumes?",
    "additional_access": "Are additional access points to a road network required?",
    "parking_addressed": "Has vehicle manoeuvring and onsite parking been addressed in the design?",
    "utilities_available": "Are power, water, electricity, sewer and telecommunication services readily available?",
    "air_pollution": "Is the development likely to result in any form of air pollution (smoke, dust, odour)?",
    "water_pollution": "Does the development have the potential to result in any form of water pollution?",
    "noise_impacts": "Will the development have any noise impacts above background noise levels?",
    "excavation": "Does the development involve any significant excavation or filling?",
    "erosion": "Could the development cause erosion or sediment run-off?",
    "contamination": "Is there any likelihood of the development resulting in soil contamination?",
    "sustainable": "Is the development environmentally sustainable (including BASIX certificate where required)?",
    "heritage_impact": "Is the development in a heritage area or likely to impact a heritage item?",
    "aboriginal": "Is the development likely to disturb any aboriginal artefacts or relics?",
    "remove_vegetation": "Will the development remove any native vegetation from the site?",
    "threatened_species": "Is the development likely to impact threatened species or native habitat?",
    "effluent": "Will effluent be disposed of to the sewer?",
    "trade_waste": "Will liquid trade waste be discharged to Council's sewer?",
    "hazardous_waste": "Will the development result in any hazardous waste or other waste disposal issue?",
    "rainwater_tanks": "Does the development propose to have rainwater tanks?",
    "overland_risks": "Have all potential overland stormwater risks been considered in the design?",
    "economic_social": "Will the proposal have any economic or social consequences in the area?",
    "crime_prevention": "Has the development addressed any safety, security or crime prevention issues?",
}

# Free-text boxes the applicant can supply, keyed by the field they fill
SEE_COMMENT_FIELDS = {
    "hazards_comments": "Natural hazards comments",
    "constraints": "Other site constraints",
    "surrounding_land_use": "Surrounding land uses",
    "planning_comments": "Planning controls comments",
    "context_comment": "Context and setting comment",
    "privacy_comments": "Privacy, views and overshadowing comments",
    "access_comments": "Access, traffic and utilities comments",
    "environmental_comments": "Environmental impacts comments",
    "flora_comments": "Flora and fauna comments",
    "waste_comments": "Waste and stormwater comments",
    "social_comments": "Social and economic comments",
    "other_matters": "Other relevant matters",
    "stormwater_details": "Stormwater disposal details (if not to the Council system)",
    "traffic_amount": "How much will traffic increase by",
}

# What this template may be used for, per its own first page
SEE_TEMPLATE_SCOPE = {
    "dwelling_single_storey": "Single residential dwelling — single storey, in a residential zone, outside a heritage conservation area",
    "residential_addition_single_storey": "Residential additions and alterations — single storey only",
    "ancillary_residential_structure": "Other ancillary residential buildings and structures (swimming pools, sheds, carports)",
    "strata_subdivision": "Strata subdivision of an existing building",
}

RESIDENTIAL_ZONES = {"R1", "R2", "R3", "R5"}

# EP&A Regulation Schedule 1 headings, for proposals this template can't carry
PURPOSE_WRITTEN_SEE_HEADINGS = [
    "Description of the site (address, lot/DP, area, existing development)",
    "Description of the proposed development",
    "Context and setting",
    "Access, transport and traffic",
    "Utilities and servicing",
    "Environmental impacts and mitigation",
    "Flora and fauna",
    "Natural hazards (flooding, bushfire)",
    "Waste and stormwater disposal",
    "Social and economic impacts",
    "Operational details (hours, staff, processes, deliveries)",
    "Assessment against the LEP, DCP and s4.15 matters",
]
