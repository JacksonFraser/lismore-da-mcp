"""Standard Instrument land use definitions and the term hierarchy."""

# Land-use term definitions from the Standard Instrument (Local Environmental
# Plans) Order 2006 Dictionary, as carried into Lismore LEP 2012. These are
# paraphrased for readability — the Standard Instrument dictionary applies
# uniformly across NSW LEPs, but wording can be amended over time, so always
# verify against the current Lismore LEP 2012 Dictionary before relying on
# a definition for a formal submission.
LAND_USE_DEFINITIONS = {
    "retail_premises": {
        "term": "retail premises",
        "definition": "A building or place used for selling items by retail, or hiring/displaying items for retail sale or hire (goods or materials), whether for consumption on or off the site. Includes bulky goods premises, cellar door premises, food and drink premises, garden centres, hardware and building supplies, kiosks, markets, plant nurseries, roadside stalls, rural supplies, shops, timber yards, and vehicle sales/hire premises. Does NOT include highway service centres, service stations, industrial retail outlets, restricted premises, or liquid fuel depots.",
        "related_terms": ["shop", "food_and_drink_premises"],
    },
    "food_and_drink_premises": {
        "term": "food and drink premises",
        "definition": "Premises used for the preparation and retail sale of food or drink (or both) for immediate consumption on or off the premises. Includes restaurant or cafe, take away food and drink premises, pubs, and small bars. Does NOT include a registered club. This is a sub-category of 'retail premises', but is assessed separately because most LEPs and DCPs attach different parking, amenity and (sometimes) permissibility requirements to it than to a plain 'shop'.",
        "related_terms": ["restaurant_or_cafe", "take_away_food_and_drink_premises", "retail_premises"],
    },
    "shop": {
        "term": "shop",
        "definition": "Retail premises that sell merchandise such as groceries, personal care products, clothing, music, homewares, stationery, electrical goods or the like, or that hire out such merchandise. Does NOT include food and drink premises or restricted premises. A shop that also prepares and sells food/drink for consumption (rather than just retailing packaged goods) shifts toward — or into — 'food and drink premises' territory; the distinction usually turns on whether preparation for consumption is occurring, not just packaging or scale.",
        "related_terms": ["retail_premises", "food_and_drink_premises"],
    },
    "restaurant_or_cafe": {
        "term": "restaurant or cafe",
        "definition": "A food and drink premises that provides seating and dining facilities wholly or principally for the preparation and serving of food and drink to people for consumption on the premises, whether or not liquor, take-away meals or entertainment are also provided.",
        "related_terms": ["food_and_drink_premises", "take_away_food_and_drink_premises"],
    },
    "take_away_food_and_drink_premises": {
        "term": "take away food and drink premises",
        "definition": "Food and drink premises used for the preparation and retail sale of food or drink for immediate consumption away from the premises, where dining facilities are not provided on-site. Includes premises selling to people seated in a motor vehicle.",
        "related_terms": ["food_and_drink_premises", "restaurant_or_cafe"],
    },
    "business_premises": {
        "term": "business premises",
        "definition": "A building or place at or on which a service is provided directly to members of the public on a regular basis or on 2+ days per week — e.g. banks, post offices, hairdressers, funeral homes. Does NOT include office premises, retail premises, warehouse/distribution centres, or industrial retail outlets.",
        "related_terms": ["commercial_premises", "office_premises"],
    },
    "commercial_premises": {
        "term": "commercial premises",
        "definition": "A building or place used for one or more of: business premises, office premises, retail premises. A broad umbrella term — most specific uses (shop, cafe, office) will also separately satisfy a more precise definition, and consent authorities generally assess against the more specific term where one applies.",
        "related_terms": ["business_premises", "retail_premises", "office_premises"],
    },
    "home_business": {
        "term": "home business",
        "definition": "A business carried on in a dwelling, or in a building ancillary to a dwelling, by the permanent residents of the dwelling, that does not involve the manufacture, alteration, servicing or repair of items other than items used in the business, and does not interfere with neighbours' amenity (noise, traffic, signage etc.).",
        "related_terms": ["home_occupation"],
    },
    "home_occupation": {
        "term": "home occupation",
        "definition": "An occupation carried on in a dwelling by permanent residents that does not involve employing anyone outside the household, does not interfere with neighbourhood amenity, does not involve exhibiting goods for sale, and does not require alterations to the dwelling. Narrower than 'home business' — usually exempt or permitted without consent, whereas home business typically needs consent.",
        "related_terms": ["home_business"],
    },
    "neighbourhood_shop": {
        "term": "neighbourhood shop",
        "definition": "A shop that has a retail floor area of not more than 80m² (commonly, check current LEP for the exact figure) and is used for selling food, groceries or other small daily convenience items to meet the needs of people in the surrounding neighbourhood.",
        "related_terms": ["shop", "retail_premises"],
    },
    # Dwelling types
    "dwelling_house": {
        "term": "dwelling house",
        "definition": "A building containing only one dwelling. May include secondary structures (garage, shed) but only one self-contained dwelling unit on the lot.",
        "related_terms": ["dwelling", "residential_accommodation"],
    },
    "dual_occupancy": {
        "term": "dual occupancy",
        "definition": "Two dwellings on one lot of land (attached or detached). Includes a dwelling house with a secondary dwelling, or two attached dwellings. Does not include a secondary dwelling if the principal dwelling is not a dwelling house.",
        "related_terms": ["dwelling_house", "secondary_dwelling"],
    },
    "secondary_dwelling": {
        "term": "secondary dwelling",
        "definition": "A self-contained dwelling on the same lot as a principal dwelling, with a maximum floor area (typically 60m² — check current SEPP). Often called a 'granny flat'. Must be used in conjunction with the principal dwelling.",
        "related_terms": ["dual_occupancy", "dwelling_house"],
    },
    "multi_dwelling_housing": {
        "term": "multi dwelling housing",
        "definition": "Three or more dwellings on one lot where each dwelling has access at ground level (no common corridor). Includes townhouses, villas, terraces. Does not include residential flat buildings.",
        "related_terms": ["attached_dwellings", "residential_flat_building"],
    },
    "residential_flat_building": {
        "term": "residential flat building",
        "definition": "A building containing 3 or more dwellings where at least some dwellings are only accessible via common corridors, stairs or lifts. Essentially apartments/units.",
        "related_terms": ["multi_dwelling_housing", "shop_top_housing"],
    },
    "attached_dwellings": {
        "term": "attached dwellings",
        "definition": "A building containing 3 or more dwellings, where each dwelling is attached to another dwelling by a common wall, each dwelling has private open space at ground level, and each dwelling has separate access.",
        "related_terms": ["multi_dwelling_housing", "semi-detached_dwellings"],
    },
    "shop_top_housing": {
        "term": "shop top housing",
        "definition": "One or more dwellings located above ground floor retail premises or business premises. Common in commercial zones where residential is only permitted above commercial uses.",
        "related_terms": ["residential_flat_building", "commercial_premises"],
    },
    "boarding_house": {
        "term": "boarding house",
        "definition": "A building that provides lodgers with a principal place of residence for 3 months or more, may have shared facilities, and has rooms that accommodate one or more lodgers. Does not include backpackers' accommodation, group home, serviced apartments, seniors housing, or hotel/motel.",
        "related_terms": ["residential_accommodation", "group_home"],
    },
    # Industrial/commercial
    "light_industries": {
        "term": "light industries",
        "definition": "An industry not involving hazardous chemicals/processes, and that would not, through operation, cause interference with the amenity of the neighbourhood by noise, vibration, smell, fumes, smoke, vapour, steam, soot, ash, dust, waste water, waste products, grit, oil, or otherwise.",
        "related_terms": ["general_industries", "industrial_retail_outlet"],
    },
    "general_industries": {
        "term": "general industries",
        "definition": "An industry other than a heavy industry or light industry. Typically manufacturing, processing, or repair operations that may have some off-site impacts but are not hazardous.",
        "related_terms": ["light_industries", "heavy_industries"],
    },
    "warehouse_or_distribution_centre": {
        "term": "warehouse or distribution centre",
        "definition": "A building or place used mainly or exclusively for storing or handling items pending their sale, distribution, or export, whether or not goods are sold by retail from the building or place. Includes self-storage units.",
        "related_terms": ["storage_premises", "light_industries"],
    },
    "vehicle_repair_station": {
        "term": "vehicle repair station",
        "definition": "A building or place used for the purpose of carrying out repairs to, or the selling and fitting of accessories to, vehicles or agricultural machinery, but not including a vehicle body repair workshop or premises primarily involved in tyre sales.",
        "related_terms": ["vehicle_body_repair_workshop", "service_station"],
    },
    # Recreation/community
    "recreation_facility_indoor": {
        "term": "recreation facility (indoor)",
        "definition": "A building or place used predominantly for indoor recreation, whether or not operated for profit. Includes squash courts, indoor swimming pools, gymnasiums, bowling alleys, ice rinks. Does not include registered clubs or recreation facilities (major).",
        "related_terms": ["recreation_facility_outdoor", "recreation_facility_major"],
    },
    "community_facility": {
        "term": "community facility",
        "definition": "A building or place owned or controlled by a public authority or non-profit community organisation used for public purposes. Includes community centres, public halls, meeting rooms. Does not include educational establishments or places of public worship.",
        "related_terms": ["place_of_public_worship", "educational_establishment"],
    },
    "centre_based_child_care_facility": {
        "term": "centre-based child care facility",
        "definition": "A building or place used for the education and care of children that is regulated under the Children (Education and Care Services) National Law. Includes long day care, occasional care, pre-school. Does not include home-based child care, school, or out-of-school-hours care on school grounds.",
        "related_terms": ["home_based_child_care", "educational_establishment"],
    },
    # Tourist/accommodation
    "hotel_or_motel_accommodation": {
        "term": "hotel or motel accommodation",
        "definition": "A building or place that provides temporary or short-term accommodation on a commercial basis and includes dining/bar facilities and one or more communal spaces. May be licensed premises. Does not include a boarding house, backpackers' accommodation, bed and breakfast, or serviced apartments.",
        "related_terms": ["tourist_and_visitor_accommodation", "backpackers_accommodation"],
    },
    "bed_and_breakfast_accommodation": {
        "term": "bed and breakfast accommodation",
        "definition": "An existing dwelling in which temporary or short-term accommodation is provided on a commercial basis by the permanent residents of the dwelling. Typically limited number of guests (commonly 6). Includes breakfast for guests.",
        "related_terms": ["farm_stay_accommodation", "tourist_and_visitor_accommodation"],
    },
}

LAND_USE_HIERARCHY = {
    # Food and drink
    "restaurant or cafe": ["food and drink premises", "retail premises", "commercial premises"],
    "cafe": ["restaurant or cafe", "food and drink premises", "retail premises", "commercial premises"],
    "restaurant": ["restaurant or cafe", "food and drink premises", "retail premises", "commercial premises"],
    "take away food and drink premises": ["food and drink premises", "retail premises", "commercial premises"],
    "takeaway": ["take away food and drink premises", "food and drink premises", "retail premises", "commercial premises"],
    "pub": ["food and drink premises", "retail premises", "commercial premises"],
    "small bar": ["food and drink premises", "retail premises", "commercial premises"],
    "food and drink premises": ["retail premises", "commercial premises"],
    # Retail
    "shop": ["retail premises", "commercial premises"],
    "bookshop": ["shop", "retail premises", "commercial premises"],
    "neighbourhood shop": ["shop", "retail premises", "commercial premises"],
    "retail premises": ["commercial premises"],
    # Business and office
    "office premises": ["business premises", "commercial premises"],
    "office": ["office premises", "business premises", "commercial premises"],
    "business premises": ["commercial premises"],
    # Recreation
    "gym": ["recreation facility (indoor)", "recreation facilities (indoor)"],
    "gymnasium": ["recreation facility (indoor)", "recreation facilities (indoor)"],
    "fitness centre": ["recreation facility (indoor)", "recreation facilities (indoor)"],
}

CATCHALL_TERM = "any other development not specified"
