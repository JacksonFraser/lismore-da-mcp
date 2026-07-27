"""Zone land use tables from Lismore LEP 2012.

Transcribed from documents/lep/lep-2012-nsw-full.txt. Lismore has exactly 21
zones with a land use table; see tests/test_tools.py::TestZoneData, which fails
both if one goes missing and if a non-Lismore zone is added."""

ZONES = {
    # Residential Zones
    "R1": {
        "name": "General Residential",
        "objectives": [
            "To provide for the housing needs of the community.",
            "To provide for a variety of housing types and densities.",
            "To enable other land uses that provide facilities or services to meet the day to day needs of residents.",
            "To ensure that new development is compatible with the character, and preserves the amenity, of each residential area."
        ],
        "height": "8.5m (check Height Map)",
        "min_lot_size": "400m² typical (check Lot Size Map)",
        "permitted_without_consent": ["Environmental protection works", "Home occupations"],
        "permitted_with_consent": ["Attached dwellings", "Boarding houses", "Building identification signs", "Business identification signs", "Centre-based child care facilities", "Community facilities", "Dwelling houses", "Group homes", "Home industries", "Hostels", "Kiosks", "Multi dwelling housing", "Neighbourhood shops", "Oyster aquaculture", "Places of public worship", "Pond-based aquaculture", "Residential flat buildings", "Respite day care centres", "Restaurants or cafes", "Semi-detached dwellings", "Seniors housing", "Shop top housing", "Roads", "Tank-based aquaculture", "Any other development not specified in item 2 or 4"],
        "prohibited": ["Agriculture", "Air transport facilities", "Airstrips", "Amusement centres", "Animal boarding or training establishments", "Biosolids treatment facilities", "Boat building and repair facilities", "Car parks", "Cemeteries", "Charter boating and tourism facilities", "Commercial premises", "Correctional centres", "Crematoria", "Depots", "Eco-tourist facilities", "Entertainment facilities", "Farm buildings", "Farm stay accommodation", "Forestry", "Freight transport facilities", "Function centres", "Heavy industrial storage establishments", "Helipads", "Highway service centres", "Home occupations (sex services)", "Industrial retail outlets", "Industrial training facilities", "Industries", "Jetties", "Local distribution premises", "Marinas", "Mooring pens", "Moorings", "Mortuaries", "Passenger transport facilities", "Public administration buildings", "Recreation facilities (major)", "Registered clubs", "Research stations", "Restricted premises", "Rural industries", "Rural workers' dwellings", "Service stations", "Sewage treatment plants", "Sex services premises", "Signage", "Storage premises", "Transport depots", "Truck depots", "Vehicle body repair workshops", "Vehicle repair stations", "Veterinary hospitals", "Warehouse or distribution centres", "Waste or resource management facilities", "Water recycling facilities", "Water storage facilities", "Water treatment facilities", "Wholesale supplies"],
    },
    "R2": {
        "name": "Low Density Residential",
        "objectives": [
            "To provide for the housing needs of the community within a low density residential environment.",
            "To enable other land uses that provide facilities or services to meet the day to day needs of residents.",
            "To limit the density of residential development to ensure that development is compatible with the flood hazard associated with the land.",
            "To ensure that tourist and visitor accommodation is of a scale and intensity that is appropriate and compatible with the character of the area."
        ],
        "height": "8.5m typical",
        "min_lot_size": "600m² typical",
        "permitted_without_consent": ["Environmental protection works", "Home occupations"],
        "permitted_with_consent": ["Boat launching ramps", "Boat sheds", "Building identification signs", "Business identification signs", "Centre-based child care facilities", "Community facilities", "Dwelling houses", "Electricity generating works", "Emergency services facilities", "Environmental facilities", "Flood mitigation works", "Group homes", "Health consulting rooms", "Home-based child care", "Home businesses", "Home industries", "Information and education facilities", "Kiosks", "Neighbourhood shops", "Oyster aquaculture", "Places of public worship", "Pond-based aquaculture", "Recreation areas", "Recreation facilities (indoor)", "Recreation facilities (outdoor)", "Respite day care centres", "Restaurants or cafes", "Roads", "Tank-based aquaculture", "Tourist and visitor accommodation", "Water recreation structures"],
        "prohibited": ["Farm stay accommodation", "Local distribution premises", "Any other development not specified in item 2 or 3"],
    },
    "R3": {
        "name": "Medium Density Residential",
        "objectives": [
            "To provide for the housing needs of the community within a medium density residential environment.",
            "To provide a variety of housing types within a medium density residential environment.",
            "To enable other land uses that provide facilities or services to meet the day to day needs of residents."
        ],
        "height": "8.5m typical",
        "min_lot_size": "Varies",
        "permitted_without_consent": ["Environmental protection works", "Home occupations"],
        "permitted_with_consent": ["Attached dwellings", "Boarding houses", "Building identification signs", "Business identification signs", "Centre-based child care facilities", "Community facilities", "Dwelling houses", "Group homes", "Home industries", "Hostels", "Kiosks", "Multi dwelling housing", "Neighbourhood shops", "Oyster aquaculture", "Places of public worship", "Residential flat buildings", "Respite day care centres", "Restaurants or cafes", "Roads", "Semi-detached dwellings", "Seniors housing", "Shop top housing", "Tank-based aquaculture", "Any other development not specified in item 2 or 4"],
        "prohibited": ["Agriculture", "Air transport facilities", "Airstrips", "Amusement centres", "Animal boarding or training establishments", "Biosolids treatment facilities", "Boat building and repair facilities", "Boat sheds", "Car parks", "Cemeteries", "Charter and tourism boating facilities", "Commercial premises", "Correctional centres", "Crematoria", "Depots", "Eco-tourist facilities", "Entertainment facilities", "Farm buildings", "Farm stay accommodation", "Forestry", "Freight transport facilities", "Function centres", "Heavy industrial storage establishments", "Helipads", "Highway service centres", "Home occupations (sex services)", "Industrial retail outlets", "Industrial training facilities", "Industries", "Jetties", "Local distribution premises", "Marinas", "Mooring pens", "Moorings", "Mortuaries", "Passenger transport facilities", "Public administration buildings", "Recreation facilities (major)", "Registered clubs", "Research stations", "Restricted premises", "Rural industries", "Rural workers' dwellings", "Service stations", "Sewage treatment plants", "Sex services premises", "Signage", "Storage premises", "Transport depots", "Truck depots", "Vehicle body repair workshops", "Vehicle repair stations", "Veterinary hospitals", "Warehouse or distribution centres", "Waste or resource management facilities", "Water recycling facilities", "Water storage facilities", "Water treatment facilities", "Wholesale supplies"],
    },
    "R5": {
        "name": "Large Lot Residential",
        "objectives": [
            "To provide residential housing in a rural setting while preserving, and minimising impacts on, environmentally sensitive locations and scenic quality.",
            "To ensure that large residential lots do not hinder the proper and orderly development of urban areas in the future.",
            "To ensure that development in the area does not unreasonably increase the demand for public services or public facilities.",
            "To minimise conflict between land uses within this zone and land uses within adjoining zones.",
            "To provide rural residential development of a quality and scale that is compatible with the character of the rural area."
        ],
        "height": "8.5m typical",
        "min_lot_size": "4000m² to 2ha (varies)",
        "permitted_without_consent": ["Environmental protection works", "Extensive agriculture", "Home occupations", "Horticulture"],
        "permitted_with_consent": ["Bed and breakfast accommodation", "Boat launching ramps", "Boat sheds", "Building identification signs", "Business identification signs", "Centre-based child care facilities", "Community facilities", "Dual occupancies", "Dwelling houses", "Electricity generating works", "Emergency services facilities", "Environmental facilities", "Farm buildings", "Flood mitigation works", "Home-based child care", "Home businesses", "Home industries", "Information and education facilities", "Jetties", "Kiosks", "Neighbourhood shops", "Oyster aquaculture", "Places of public worship", "Plant nurseries", "Pond-based aquaculture", "Recreation areas", "Recreation facilities (outdoor)", "Respite day care centres", "Restaurants or cafes", "Roads", "Roadside stalls", "Sewerage systems", "Tank-based aquaculture", "Water recreation structures"],
        "prohibited": ["Dairies (pasture-based)", "Local distribution premises", "Any other development not specified in item 2 or 3"],
    },

    # Employment Zones (new Standard Instrument naming from 2022)
    "E1": {
        "name": "Local Centre",
        "notes": "Formerly B1 Neighbourhood Centre / B2 Local Centre",
        "objectives": [
            "To provide a range of retail, business and community uses that serve the needs of people who live in, work in or visit the area.",
            "To encourage investment in local commercial development that generates employment opportunities and economic growth.",
            "To enable residential development that contributes to a vibrant and active local centre and is consistent with the Council's strategic planning for residential development in the area.",
            "To encourage business, retail, community and other non-residential land uses on the ground floor of buildings.",
            "To ensure that development is of an appropriate scale and is compatible with the character of the surrounding neighbourhood.",
            "To provide for development that does not detract from the role of Zone E2 Commercial Centre as the primary centre of business, retail, community and cultural activity."
        ],
        "height": "Check Height Map",
        "permitted_without_consent": ["Environmental protection works", "Home occupations", "Home occupations (sex services)"],
        "permitted_with_consent": ["Amusement centres", "Artisan food and drink industries", "Boarding houses", "Centre-based child care facilities", "Commercial premises", "Community facilities", "Creative industries", "Entertainment facilities", "Function centres", "Home industries", "Hotel or motel accommodation", "Information and education facilities", "Local distribution premises", "Medical centres", "Oyster aquaculture", "Places of public worship", "Public administration buildings", "Recreation facilities (indoor)", "Respite day care centres", "Service stations", "Shop top housing", "Tank-based aquaculture", "Veterinary hospitals", "Any other development not specified in item 2 or 4"],
        "prohibited": ["Agriculture", "Air transport facilities", "Airstrips", "Animal boarding or training establishments", "Biosolids treatment facilities", "Boat building and repair facilities", "Boat sheds", "Camping grounds", "Caravan parks", "Cemeteries", "Charter and tourism boating facilities", "Correctional centres", "Crematoria", "Depots", "Eco-tourist facilities", "Exhibition homes", "Exhibition villages", "Farm buildings", "Forestry", "Freight transport facilities", "Heavy industrial storage establishments", "Helipads", "Highway service centres", "Industrial retail outlets", "Industrial training facilities", "Industries", "Marinas", "Mooring pens", "Moorings", "Mortuaries", "Port facilities", "Recreation facilities (major)", "Research stations", "Residential accommodation", "Resource recovery facilities", "Rural industries", "Sewage treatment plants", "Sex services premises", "Storage premises", "Transport depots", "Truck depots", "Vehicle body repair workshops", "Warehouse or distribution centres", "Waste disposal facilities", "Water recycling facilities", "Water storage facilities", "Water treatment facilities", "Wholesale supplies"],
    },
    "E2": {
        "name": "Commercial Centre",
        "notes": "Formerly B3 Commercial Core. Lismore CBD - primary retail/commercial centre",
        "objectives": [
            "To strengthen the role of the commercial centre as the centre of business, retail, community and cultural activity.",
            "To encourage investment in commercial development that generates employment opportunities and economic growth.",
            "To encourage development that has a high level of accessibility and amenity, particularly for pedestrians.",
            "To enable residential development only if it is consistent with the Council's strategic planning for residential development in the area.",
            "To ensure that new development provides diverse and active street frontages to attract pedestrian traffic and to contribute to vibrant, diverse and functional streets and public spaces."
        ],
        "height": "Check Height Map",
        "permitted_without_consent": ["Environmental protection works", "Home occupations", "Home occupations (sex services)"],
        "permitted_with_consent": ["Amusement centres", "Artisan food and drink industries", "Backpackers' accommodation", "Centre-based child care facilities", "Commercial premises", "Community facilities", "Creative industries", "Entertainment facilities", "Function centres", "Home industries", "Hotel or motel accommodation", "Information and education facilities", "Local distribution premises", "Medical centres", "Mortuaries", "Oyster aquaculture", "Passenger transport facilities", "Places of public worship", "Recreation areas", "Recreation facilities (indoor)", "Recreation facilities (outdoor)", "Registered clubs", "Respite day care centres", "Restricted premises", "Shop top housing", "Tank-based aquaculture", "Vehicle repair stations", "Veterinary hospitals", "Any other development not specified in item 2 or 4"],
        "prohibited": ["Agriculture", "Air transport facilities", "Airstrips", "Animal boarding or training establishments", "Biosolids treatment facilities", "Boat building and repair facilities", "Boat sheds", "Camping grounds", "Caravan parks", "Cemeteries", "Correctional centres", "Crematoria", "Depots", "Eco-tourist facilities", "Exhibition homes", "Exhibition villages", "Farm buildings", "Farm stay accommodation", "Forestry", "Freight transport facilities", "Heavy industrial storage establishments", "Helipads", "Highway service centres", "Industrial retail outlets", "Industrial training facilities", "Industries", "Mooring pens", "Moorings", "Port facilities", "Recreation facilities (major)", "Residential accommodation", "Resource recovery facilities", "Rural industries", "Sewage treatment plants", "Sex services premises", "Storage premises", "Transport depots", "Truck depots", "Vehicle body repair workshops", "Warehouse or distribution centres", "Waste disposal facilities", "Water recycling facilities", "Water storage facilities", "Water treatment facilities"],
    },
    "E3": {
        "name": "Productivity Support",
        "notes": "Formerly B5/B6 Business Development/Enterprise Corridor",
        "objectives": [
            "To provide a range of facilities and services, light industries, warehouses and offices.",
            "To provide for land uses that are compatible with, but do not compete with, land uses in surrounding local and commercial centres.",
            "To maintain the economic viability of local and commercial centres by limiting certain retail and commercial activity.",
            "To provide for land uses that meet the needs of the community, businesses and industries but that are not suited to locations in other employment zones.",
            "To provide opportunities for new and emerging light industries.",
            "To enable other land uses that provide facilities and services to meet the day to day needs of workers, to sell goods of a large size, weight or quantity or to sell goods manufactured on-site.",
            "To provide for residential uses, but only as part of mixed use development."
        ],
        "height": "Check Height Map",
        "permitted_without_consent": ["Environmental protection works", "Home occupations", "Home occupations (sex services)"],
        "permitted_with_consent": ["Animal boarding or training establishments", "Boat building and repair facilities", "Business premises", "Centre-based child care facilities", "Community facilities", "Depots", "Function centres", "Garden centres", "Hardware and building supplies", "Home industries", "Hotel or motel accommodation", "Industrial retail outlets", "Industrial training facilities", "Information and education facilities", "Kiosks", "Landscaping material supplies", "Light industries", "Local distribution premises", "Markets", "Mortuaries", "Neighbourhood shops", "Office premises", "Oyster aquaculture", "Passenger transport facilities", "Places of public worship", "Plant nurseries", "Recreation areas", "Recreation facilities (indoor)", "Recreation facilities (major)", "Recreation facilities (outdoor)", "Research stations", "Respite day care centres", "Rural supplies", "Service stations", "Shop top housing", "Specialised retail premises", "Storage premises", "Take away food and drink premises", "Tank-based aquaculture", "Timber yards", "Vehicle body repair workshops", "Vehicle repair stations", "Vehicle sales or hire premises", "Veterinary hospitals", "Warehouse or distribution centres", "Wholesale supplies", "Any other development not specified in item 2 or 4"],
        "prohibited": ["Agriculture", "Air transport facilities", "Airstrips", "Amusement centres", "Biosolids treatment facilities", "Boat sheds", "Camping grounds", "Caravan parks", "Cemeteries", "Charter and tourism boating facilities", "Correctional centres", "Eco-tourist facilities", "Entertainment facilities", "Exhibition homes", "Exhibition villages", "Farm buildings", "Forestry", "Freight transport facilities", "Heavy industrial storage establishments", "Helipads", "Highway service centres", "Industries", "Marinas", "Mooring pens", "Moorings", "Port facilities", "Registered clubs", "Residential accommodation", "Resource recovery facilities", "Restricted premises", "Retail premises", "Rural industries", "Sewage treatment plants", "Sex services premises", "Tourist and visitor accommodation", "Transport depots", "Truck depots", "Waste disposal facilities", "Water recycling facilities", "Water storage facilities", "Water treatment facilities"],
    },
    "E4": {
        "name": "General Industrial",
        "notes": "Formerly IN1 General Industrial",
        "objectives": [
            "To provide a range of industrial, warehouse, logistics and related land uses.",
            "To ensure the efficient and viable use of land for industrial uses.",
            "To minimise any adverse effect of industry on other land uses.",
            "To encourage employment opportunities.",
            "To enable limited non-industrial land uses that provide facilities and services to meet the needs of businesses and workers.",
            "To ensure that development does not adversely affect the flooding characteristics of the area or increase the hazard of flooding on adjoining land."
        ],
        "height": "Check Height Map",
        "permitted_without_consent": ["Environmental protection works", "Home occupations", "Home occupations (sex services)"],
        "permitted_with_consent": ["Depots", "Freight transport facilities", "Garden centres", "General industries", "Goods repair and reuse premises", "Hardware and building supplies", "Industrial retail outlets", "Industrial training facilities", "Kiosks", "Landscaping material supplies", "Light industries", "Liquid fuel depots", "Local distribution premises", "Neighbourhood shops", "Oyster aquaculture", "Plant nurseries", "Rural supplies", "Specialised retail premises", "Take away food and drink premises", "Tank-based aquaculture", "Timber yards", "Vehicle sales or hire premises", "Warehouse or distribution centres", "Any other development not specified in item 2 or 4"],
        "prohibited": ["Agriculture", "Airports", "Airstrips", "Amusement centres", "Animal boarding or training establishments", "Boat launching ramps", "Camping grounds", "Caravan parks", "Cemeteries", "Centre-based child care facilities", "Charter and tourism boating facilities", "Commercial premises", "Community facilities", "Correctional centres", "Eco-tourist facilities", "Educational establishments", "Entertainment facilities", "Exhibition homes", "Exhibition villages", "Farm buildings", "Forestry", "Function centres", "Health services facilities", "Highway service centres", "Information and education facilities", "Jetties", "Marinas", "Mooring pens", "Moorings", "Passenger transport facilities", "Port facilities", "Public administration buildings", "Recreation areas", "Recreation facilities (major)", "Recreation facilities (outdoor)", "Registered clubs", "Residential accommodation", "Respite day care centres", "Restricted premises", "Tourist and visitor accommodation", "Water recreation structures"],
    },

    # Mixed Use Zone
    "MU1": {
        "name": "Mixed Use",
        "notes": "Formerly B4 Mixed Use",
        "objectives": [
            "To encourage a diversity of business, retail, office and light industrial land uses that generate employment opportunities.",
            "To ensure that new development provides diverse and active street frontages to attract pedestrian traffic and to contribute to vibrant, diverse and functional streets and public spaces.",
            "To minimise conflict between land uses within this zone and land uses within adjoining zones.",
            "To encourage business, retail, community and other non-residential land uses on the ground floor of buildings.",
            "To encourage a range of housing within a vibrant mixed use environment that is accessible to community facilities, commercial services and transport."
        ],
        "height": "Check Height Map",
        "permitted_without_consent": ["Environmental protection works", "Home occupations", "Home occupations (sex services)"],
        "permitted_with_consent": ["Amusement centres", "Boarding houses", "Car parks", "Centre-based child care facilities", "Commercial premises", "Community facilities", "Entertainment facilities", "Function centres", "Information and education facilities", "Light industries", "Local distribution premises", "Medical centres", "Oyster aquaculture", "Passenger transport facilities", "Places of public worship", "Recreation areas", "Recreation facilities (indoor)", "Registered clubs", "Respite day care centres", "Restricted premises", "Shop top housing", "Tank-based aquaculture", "Tourist and visitor accommodation", "Vehicle repair stations", "Any other development not specified in item 2 or 4"],
        "prohibited": ["Agriculture", "Air transport facilities", "Airstrips", "Animal boarding or training establishments", "Biosolids treatment facilities", "Boat building and repair facilities", "Boat sheds", "Camping grounds", "Caravan parks", "Cemeteries", "Charter and tourism boating facilities", "Crematoria", "Depots", "Eco-tourist facilities", "Exhibition villages", "Farm buildings", "Forestry", "Freight transport facilities", "Heavy industrial storage establishments", "Helipads", "Highway service centres", "Industrial retail outlets", "Industrial training facilities", "Industries", "Marinas", "Mooring pens", "Moorings", "Mortuaries", "Port facilities", "Recreation facilities (major)", "Resource recovery facilities", "Rural industries", "Rural workers' dwellings", "Service stations", "Sewage treatment plants", "Sex services premises", "Storage premises", "Transport depots", "Truck depots", "Vehicle body repair workshops", "Warehouse or distribution centres", "Waste disposal facilities", "Water recycling facilities", "Water storage facilities", "Water treatment facilities", "Wholesale supplies"],
    },

    # Rural Zone
    "RU1": {
        "name": "Primary Production",
        "objectives": [
            "To encourage sustainable primary industry production by maintaining and enhancing the natural resource base.",
            "To encourage diversity in primary industry enterprises and systems appropriate for the area.",
            "To minimise the fragmentation and alienation of resource lands.",
            "To minimise conflict between land uses within this zone and land uses within adjoining zones.",
            "To preserve rural resources by ensuring that the viability of rural land is not extinguished by inappropriate development or incompatible uses.",
            "To enable a range of other uses to occur on rural land providing such uses do not conflict with existing or potential agriculture and do not detract from the scenic amenity and character of the rural environment.",
        ],
        "permitted_without_consent": [
            "Environmental protection works",
            "Extensive agriculture",
            "Forestry",
            "Home occupations",
            "Home occupations (sex services)",
            "Intensive plant agriculture",
        ],
        "permitted_with_consent": [
            "Agritourism",
            "Airstrips",
            "Animal boarding or training establishments",
            "Aquaculture",
            "Artisan food and drink industries",
            "Boat launching ramps",
            "Boat sheds",
            "Building identification signs",
            "Business identification signs",
            "Camping grounds",
            "Caravan parks",
            "Cellar door premises",
            "Cemeteries",
            "Community facilities",
            "Creative industries",
            "Dual occupancies",
            "Dwelling houses",
            "Eco-tourist facilities",
            "Environmental facilities",
            "Extractive industries",
            "Farm buildings",
            "Flood mitigation works",
            "Garden centres",
            "Helipads",
            "Home-based child care",
            "Home businesses",
            "Home industries",
            "Information and education facilities",
            "Intensive livestock agriculture",
            "Jetties",
            "Kiosks",
            "Landscaping material supplies",
            "Mooring pens",
            "Open cut mining",
            "Plant nurseries",
            "Recreation areas",
            "Recreation facilities (outdoor)",
            "Restaurants or cafes",
            "Roads",
            "Roadside stalls",
            "Rural industries",
            "Rural supplies",
            "Tourist and visitor accommodation",
            "Turf farming",
            "Water recreation structures",
        ],
        "prohibited": [
            "Backpackers’ accommodation",
            "Hotel or motel accommodation",
            "Local distribution premises",
            "Serviced apartments",
            "Any other development not specified in item 2 or 3",
        ],
    },
    "RU2": {
        "name": "Rural Landscape",
        "objectives": [
            "To encourage sustainable primary industry production by maintaining and enhancing the natural resource base.",
            "To maintain the rural landscape character of the land.",
            "To provide for a range of compatible land uses, including extensive agriculture.",
            "To enable a range of other uses that are compatible with the flood hazard associated with the land.",
            "To provide for a limited range of development that does not have an adverse effect on the ecological values of the land.",
        ],
        "permitted_without_consent": [
            "Environmental protection works",
            "Extensive agriculture",
            "Forestry",
            "Home occupations",
            "Home occupations (sex services)",
            "Intensive plant agriculture",
        ],
        "permitted_with_consent": [
            "Agritourism",
            "Airstrips",
            "Animal boarding or training establishments",
            "Aquaculture",
            "Bed and breakfast accommodation",
            "Boat launching ramps",
            "Boat sheds",
            "Building identification signs",
            "Business identification signs",
            "Camping grounds",
            "Cellar door premises",
            "Cemeteries",
            "Community facilities",
            "Dwelling houses",
            "Eco-tourist facilities",
            "Environmental facilities",
            "Farm buildings",
            "Farm stay accommodation",
            "Flood mitigation works",
            "Garden centres",
            "Helipads",
            "Home-based child care",
            "Home businesses",
            "Information and education facilities",
            "Intensive livestock agriculture",
            "Jetties",
            "Kiosks",
            "Landscaping material supplies",
            "Light industries",
            "Mooring pens",
            "Plant nurseries",
            "Recreation areas",
            "Recreation facilities (outdoor)",
            "Restaurants or cafes",
            "Roads",
            "Roadside stalls",
            "Rural industries",
            "Turf farming",
            "Vehicle repair stations",
            "Water recreation structures",
        ],
        "prohibited": [
            "Any development not specified in item 2 or 3",
        ],
    },
    "RU3": {
        "name": "Forestry",
        "objectives": [
            "To enable development for forestry purposes.",
            "To enable other development that is compatible with forestry land uses.",
        ],
        "permitted_without_consent": [
            "Environmental facilities",
            "Environmental protection works",
            "Extensive agriculture",
            "Uses authorised under the Forestry Act 2012 or under Part 5B (Private native forestry) of the Local Land Services Act 2013",
        ],
        "permitted_with_consent": [
            "Aquaculture",
            "Boat launching ramps",
            "Farm buildings",
            "Flood mitigation works",
            "Jetties",
            "Recreation areas",
            "Roads",
            "Water recreation structures",
        ],
        "prohibited": [
            "Any development not specified in item 2 or 3",
        ],
    },
    "RU5": {
        "name": "Village",
        "notes": "Applies to Nimbin, Dunoon, Clunes and other villages",
        "objectives": [
            "To provide for a range of land uses, services and facilities that are associated with a rural village."
        ],
        "height": "8.5m typical",
        "permitted_without_consent": ["Environmental protection works", "Extensive agriculture", "Home occupations"],
        "permitted_with_consent": ["Boat launching ramps", "Boat sheds", "Camping grounds", "Car parks", "Caravan parks", "Centre-based child care facilities", "Commercial premises", "Community facilities", "Dwelling houses", "Electricity generating works", "Entertainment facilities", "Environmental facilities", "Exhibition homes", "Farm buildings", "Flood mitigation works", "Home-based child care", "Home businesses", "Horticulture", "Information and education facilities", "Jetties", "Light industries", "Neighbourhood shops", "Oyster aquaculture", "Passenger transport facilities", "Places of public worship", "Recreation areas", "Recreation facilities (indoor)", "Recreation facilities (outdoor)", "Registered clubs", "Residential accommodation", "Respite day care centres", "Roads", "Schools", "Service stations", "Sewerage systems", "Signage", "Tank-based aquaculture", "Tourist and visitor accommodation", "Vehicle body repair workshops", "Vehicle repair stations", "Veterinary hospitals", "Waste or resource management facilities", "Water recreation structures", "Water supply systems", "Wholesale supplies"],
        "prohibited": ["Dairies (pasture-based)", "Farm stay accommodation", "Local distribution premises", "Rural workers' dwellings", "Serviced apartments", "Specialised retail premises", "Timber yards", "Any other development not specified in item 2 or 3"],
    },

    # Special Purpose and Recreation Zones
    "SP2": {
        "name": "Infrastructure",
        "objectives": [
            "To provide for infrastructure and related uses.",
            "To prevent development that is not compatible with or that may detract from the provision of infrastructure."
        ],
        "permitted_without_consent": ["Environmental protection works"],
        "permitted_with_consent": ["Aquaculture", "Car parks", "Environmental facilities", "Flood mitigation works", "Helipads", "Passenger transport facilities", "Roads", "Signage", "The purpose shown on the Land Zoning Map, including any development that is ordinarily incidental or ancillary to development for that purpose"],
        "prohibited": ["Any development not specified in item 2 or 3"],
    },
    "RE1": {
        "name": "Public Recreation",
        "objectives": [
            "To enable land to be used for public open space or recreational purposes.",
            "To provide a range of recreational settings and activities and compatible land uses.",
            "To protect and enhance the natural environment for recreational purposes.",
            "To ensure the community has adequate access to open space to meet the needs of all residents and improve amenity and quality of life."
        ],
        "permitted_without_consent": ["Environmental facilities", "Environmental protection works"],
        "permitted_with_consent": ["Aquaculture", "Boat launching ramps", "Boat sheds", "Camping grounds", "Car parks", "Caravan parks", "Centre-based child care facilities", "Charter and tourism boating facilities", "Community facilities", "Entertainment facilities", "Extensive agriculture", "Flood mitigation works", "Function centres", "Information and education facilities", "Jetties", "Kiosks", "Markets", "Passenger transport facilities", "Recreation areas", "Recreation facilities (indoor)", "Recreation facilities (major)", "Recreation facilities (outdoor)", "Respite day care centres", "Restaurants or cafes", "Roads", "Signage", "Water recreation structures"],
        "prohibited": ["Dairies (pasture-based)", "Any other development not specified in item 2 or 3"],
    },
    "RE2": {
        "name": "Private Recreation",
        "objectives": [
            "To enable land to be used for private open space or recreational purposes.",
            "To provide a range of recreational settings and activities and compatible land uses.",
            "To protect and enhance the natural environment for recreational purposes.",
            "To provide a range of recreational, educational and tourist activities on land in private ownership."
        ],
        "permitted_without_consent": ["Environmental protection works"],
        "permitted_with_consent": ["Aquaculture", "Boat launching ramps", "Boat sheds", "Camping grounds", "Car parks", "Caravan parks", "Centre-based child care facilities", "Charter and tourism boating facilities", "Community facilities", "Educational establishments", "Environmental facilities", "Extensive agriculture", "Flood mitigation works", "Food and drink premises", "Helipads", "Information and education facilities", "Jetties", "Kiosks", "Markets", "Passenger transport facilities", "Places of public worship", "Recreation areas", "Recreation facilities (indoor)", "Recreation facilities (major)", "Recreation facilities (outdoor)", "Registered clubs", "Respite day care centres", "Roads", "Signage", "Water recreation structures"],
        "prohibited": ["Dairies (pasture-based)", "Any other development not specified in item 2 or 3"],
    },

    # Conservation Zones
    "C1": {
        "name": "National Parks and Nature Reserves",
        "notes": "Formerly E1 National Parks and Nature Reserves",
        "objectives": [
            "To enable the management and appropriate use of land that is reserved under the National Parks and Wildlife Act 1974 or that is acquired under Part 11 of that Act.",
            "To enable uses authorised under the National Parks and Wildlife Act 1974.",
            "To identify land that is to be reserved under the National Parks and Wildlife Act 1974 and to protect the environmental significance of that land."
        ],
        "permitted_without_consent": ["Uses authorised under the National Parks and Wildlife Act 1974"],
        "permitted_with_consent": [],
        "prohibited": ["Any development not specified in item 2 or 3"],
    },
    "C2": {
        "name": "Environmental Conservation",
        "notes": "Formerly E2 Environmental Conservation",
        "objectives": [
            "To protect, manage and restore areas of high ecological, scientific, cultural or aesthetic values.",
            "To prevent development that could destroy, damage or otherwise have an adverse effect on those values.",
            "To retain areas of unique natural vegetation, particularly rainforest remnants and ecologically endangered communities."
        ],
        "permitted_without_consent": ["Environmental protection works"],
        "permitted_with_consent": ["Boat launching ramps", "Building identification signs", "Business identification signs", "Environmental facilities", "Extensive agriculture", "Flood mitigation works", "Jetties", "Oyster aquaculture", "Research stations", "Roads", "Water recreation structures"],
        "prohibited": ["Business premises", "Hotel or motel accommodation", "Industries", "Local distribution premises", "Multi dwelling housing", "Pond-based aquaculture", "Recreation facilities (major)", "Residential flat buildings", "Restricted premises", "Retail premises", "Seniors housing", "Service stations", "Tank-based aquaculture", "Warehouse or distribution centres", "Any other development not specified in item 2 or 3"],
    },
    "C3": {
        "name": "Environmental Management",
        "notes": "Formerly E3 Environmental Management",
        "objectives": [
            "To protect, manage and restore areas with special ecological, scientific, cultural or aesthetic values.",
            "To provide for a limited range of development that does not have an adverse effect on those values.",
            "To encourage the retention of wildlife habitats and associated vegetation and wildlife corridors."
        ],
        "permitted_without_consent": ["Environmental protection works", "Extensive agriculture", "Home occupations"],
        "permitted_with_consent": ["Bed and breakfast accommodation", "Boat launching ramps", "Building identification signs", "Business identification signs", "Camping grounds", "Caravan parks", "Cellar door premises", "Community facilities", "Dairies (pasture-based)", "Dwelling houses", "Eco-tourist facilities", "Emergency services facilities", "Environmental facilities", "Farm buildings", "Farm stay accommodation", "Flood mitigation works", "Home-based child care", "Home businesses", "Home industries", "Information and education facilities", "Jetties", "Kiosks", "Neighbourhood shops", "Oyster aquaculture", "Pond-based aquaculture", "Recreation areas", "Research stations", "Roads", "Roadside stalls", "Tank-based aquaculture", "Water recreation structures"],
        "prohibited": ["Industries", "Local distribution premises", "Multi dwelling housing", "Residential flat buildings", "Retail premises", "Seniors housing", "Service stations", "Warehouse or distribution centres", "Any other development not specified in item 2 or 3"],
    },

    # Waterway Zones
    "W1": {
        "name": "Natural Waterways",
        "objectives": [
            "To protect the ecological and scenic values of natural waterways.",
            "To prevent development that would have an adverse effect on the natural values of waterways in this zone.",
            "To provide for sustainable fishing industries and recreational fishing."
        ],
        "permitted_without_consent": ["Environmental protection works"],
        "permitted_with_consent": ["Aquaculture", "Boat launching ramps", "Boat sheds", "Building identification signs", "Business identification signs", "Emergency services facilities", "Environmental facilities", "Flood mitigation works", "Information and education facilities", "Jetties", "Mooring pens", "Moorings", "Recreation areas", "Research stations", "Roads", "Water recreation structures", "Water supply systems"],
        "prohibited": ["Business premises", "Hotel or motel accommodation", "Industries", "Local distribution premises", "Multi dwelling housing", "Recreation facilities (major)", "Residential flat buildings", "Restricted premises", "Retail premises", "Seniors housing", "Service stations", "Warehouse or distribution centres", "Any other development not specified in item 2 or 3"],
    },
    "W2": {
        "name": "Recreational Waterways",
        "objectives": [
            "To protect the ecological, scenic and recreation values of recreational waterways.",
            "To allow for water-based recreation and related uses.",
            "To provide for sustainable fishing industries and recreational fishing.",
            "To provide for activities that are compatible with, and complement, the scenic and ecological qualities of the waterway.",
        ],
        "permitted_without_consent": [
            "Environmental protection works",
            "Moorings",
        ],
        "permitted_with_consent": [
            "Aquaculture",
            "Boat building and repair facilities",
            "Boat launching ramps",
            "Boat sheds",
            "Building identification signs",
            "Business identification signs",
            "Car parks",
            "Charter and tourism boating facilities",
            "Community facilities",
            "Emergency services facilities",
            "Environmental facilities",
            "Flood mitigation works",
            "Information and education facilities",
            "Jetties",
            "Kiosks",
            "Marinas",
            "Markets",
            "Mooring pens",
            "Recreation areas",
            "Recreation facilities (outdoor)",
            "Registered clubs",
            "Restaurants or cafes",
            "Roads",
            "Water recreation structures",
            "Water supply systems",
        ],
        "prohibited": [
            "Industries",
            "Local distribution premises",
            "Multi dwelling housing",
            "Residential flat buildings",
            "Seniors housing",
            "Warehouse or distribution centres",
            "Any other development not specified in item 2 or 3",
        ],
    },

    # Legacy zone codes (for backwards compatibility with older references)
    "B1": {
        "name": "Neighbourhood Centre (LEGACY - now E1 Local Centre)",
        "notes": "This zone code has been replaced by E1 Local Centre under the Standard Instrument LEP amendments. Use E1 for current references.",
        "redirect_to": "E1",
    },
    "B2": {
        "name": "Local Centre (LEGACY - now E1 Local Centre)",
        "notes": "This zone code has been replaced by E1 Local Centre under the Standard Instrument LEP amendments. Use E1 for current references.",
        "redirect_to": "E1",
    },
    "B3": {
        "name": "Commercial Core (LEGACY - now E2 Commercial Centre)",
        "notes": "This zone code has been replaced by E2 Commercial Centre under the Standard Instrument LEP amendments. Use E2 for current references.",
        "redirect_to": "E2",
    },
    "B4": {
        "name": "Mixed Use (LEGACY - now MU1 Mixed Use)",
        "notes": "This zone code has been replaced by MU1 Mixed Use under the Standard Instrument LEP amendments. Use MU1 for current references.",
        "redirect_to": "MU1",
    },
    "IN1": {
        "name": "General Industrial (LEGACY - now E4 General Industrial)",
        "notes": "This zone code has been replaced by E4 General Industrial under the Standard Instrument LEP amendments. Use E4 for current references.",
        "redirect_to": "E4",
    },
    "IN2": {
        "name": "Light Industrial (LEGACY - see E3 Productivity Support or E4 General Industrial)",
        "notes": "This zone code has been replaced under the Standard Instrument LEP amendments. Check E3 Productivity Support or E4 General Industrial depending on location.",
        "redirect_to": "E3",
    },
}
