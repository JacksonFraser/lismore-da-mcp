"""Off-street parking rates from Lismore DCP Chapter 7."""

PARKING_RATES = {
    # Residential
    "dwelling_house": {"spaces": "1-2", "rate": "1 space per dwelling, 2 if > 125m² GFA"},
    "dual_occupancy": {"spaces": "1 per dwelling", "rate": "1 space per dwelling"},
    "multi_dwelling_housing": {"spaces": "1-1.5 per dwelling + visitor", "rate": "1 space per 1-bed, 1.5 per 2+ bed, plus 1 visitor per 4 dwellings"},
    "residential_flat_building": {"spaces": "1-2 per dwelling + visitor", "rate": "1 space per 1-bed, 2 per 2+ bed, plus 1 visitor per 4 dwellings"},
    "secondary_dwelling": {"spaces": "1", "rate": "1 additional space"},
    "boarding_house": {"spaces": "1 per 3 rooms", "rate": "1 space per 3 boarding rooms + 1 for manager"},

    # Commercial
    "shop": {"spaces": "1 per 25m²", "rate": "1 space per 25m² GFA"},
    "retail": {"spaces": "1 per 25m²", "rate": "1 space per 25m² GFA"},
    "office": {"spaces": "1 per 40m²", "rate": "1 space per 40m² GFA"},
    "business_premises": {"spaces": "1 per 40m²", "rate": "1 space per 40m² GFA"},
    "restaurant": {"spaces": "1 per 10m² + 1 per 2 staff", "rate": "1 space per 10m² dining area plus 1 per 2 employees"},
    "cafe": {"spaces": "1 per 10m²", "rate": "1 space per 10m² dining area"},
    "take_away": {"spaces": "1 per 10m²", "rate": "1 space per 10m² GFA, minimum 4 spaces"},
    "medical_centre": {"spaces": "4 per practitioner", "rate": "4 spaces per practitioner"},
    "hotel": {"spaces": "1 per 2 rooms + function", "rate": "1 per 2 guest rooms plus parking for function rooms"},
    "motel": {"spaces": "1 per unit", "rate": "1 space per unit plus 1 for manager"},

    # Industrial
    "industry": {"spaces": "1 per 75m²", "rate": "1 space per 75m² GFA"},
    "warehouse": {"spaces": "1 per 100m²", "rate": "1 space per 100m² GFA"},
    "bulky_goods": {"spaces": "1 per 50m²", "rate": "1 space per 50m² GFA"},

    # Other
    "childcare_centre": {"spaces": "1 per 4 children", "rate": "1 space per 4 children plus staff parking"},
    "place_of_worship": {"spaces": "1 per 10 seats", "rate": "1 space per 10 seats or 1 per 10m² floor area"},
    "gym": {"spaces": "1 per 25m²", "rate": "1 space per 25m² GFA"},
}
