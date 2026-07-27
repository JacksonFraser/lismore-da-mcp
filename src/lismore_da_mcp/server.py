"""
Lismore Development Application MCP Server

Provides tools for assisting with Development Applications in the Lismore LGA.
"""

import base64
import json
import math
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource

# Initialize server
server = Server("lismore-da-mcp")

# Path to documents directory
DOCS_DIR = Path(__file__).parent.parent.parent / "documents"

# When served over the public Streamable HTTP transport (MCP_TRANSPORT=http), tools that
# generate files must not persist them to shared local disk — one caller's output (which can
# contain another person's name/address) must never be readable by another caller. In this mode
# fill_see_pdf writes to a per-request temp dir, returns the file inline, and deletes it
# immediately instead of writing into the shared documents/output/ tree.
PUBLIC_MODE = os.environ.get("MCP_TRANSPORT", "stdio").lower() == "http"

# ============================================================================
# DATA: Parking Rates, Zone Info, Fee Schedules
# ============================================================================

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

# ============================================================================
# RESIDENTIAL DEVELOPMENT STANDARDS (from DCP Chapter 1)
# ============================================================================

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

# ============================================================================
# REFERRAL REQUIREMENTS (Integrated Development & Concurrence)
# ============================================================================

REFERRAL_REQUIREMENTS = {
    "rural_fire_service": {
        "trigger": "Development on bushfire prone land (check Bush Fire Prone Land Map)",
        "types": ["Subdivision", "Special fire protection purpose development (schools, childcare, hospitals, aged care)", "Residential in bushfire prone area"],
        "approval": "Bushfire Safety Authority (s100B of Rural Fires Act)",
        "documents": ["Bushfire Assessment Report", "Asset Protection Zones shown on plans"],
    },
    "heritage_council": {
        "trigger": "Development affecting State Heritage Register item",
        "types": ["Works on State-listed heritage items", "Works within curtilage of State heritage"],
        "approval": "Heritage Council NSW concurrence",
        "documents": ["Heritage Impact Statement", "Conservation Management Plan (if required)"],
    },
    "epa": {
        "trigger": "Scheduled activities under Protection of the Environment Operations Act",
        "types": ["Large industrial facilities", "Waste facilities", "Concrete batching > 150 tonnes/day", "Extractive industries"],
        "approval": "Environment Protection Licence from EPA",
        "documents": ["Environmental Impact Statement (for designated development)"],
    },
    "transport_nsw": {
        "trigger": "Development with access to classified road OR significant traffic generation",
        "types": ["New access to state/regional road", "Development generating > 50 peak hour vehicle trips"],
        "approval": "Concurrence from Transport for NSW",
        "documents": ["Traffic Impact Assessment", "Road Safety Audit"],
    },
    "natural_resources_access_regulator": {
        "trigger": "Works on waterfront land (within 40m of mapped waterways)",
        "types": ["Building within 40m of river/creek", "Vegetation clearing near waterways", "Dredging/reclamation"],
        "approval": "Controlled activity approval under Water Management Act",
        "documents": ["Vegetation Management Plan", "Erosion and Sediment Control Plan"],
    },
    "biodiversity_conservation": {
        "trigger": "Clearing native vegetation above threshold OR impact on threatened species",
        "types": ["Clearing > 0.25ha on sensitive land", "Impact on threatened species/EEC"],
        "approval": "Biodiversity Development Assessment Report (BDAR) may be required",
        "documents": ["BDAR or Biodiversity Certification", "Species Impact Statement"],
    },
    "council_flood_assessment": {
        "trigger": "Development on flood prone land — the defining constraint across much of this LGA",
        "types": ["Any development below the Flood Planning Level", "Habitable floor space on flood prone land", "Development in the CBD flood exemption precinct"],
        "approval": "Council assessment against LEP 2012 clause 5.21 and DCP Chapter 8 (internal, not an external referral)",
        "documents": ["Flood Risk Assessment", "Survey showing floor levels relative to the Flood Planning Level", "Site-specific evacuation plan and refuge above the Probable Maximum Flood (CBD precinct)"],
    },
    "mine_subsidence": {
        "trigger": "Development within Mine Subsidence District",
        "types": ["N/A — no Mine Subsidence Districts in Lismore LGA"],
        "approval": "Not applicable",
    },
    "water_nsw": {
        "trigger": "Development in Sydney drinking water catchment",
        "types": ["N/A — Lismore not in Sydney catchment"],
        "approval": "Not applicable",
    },
}

# ============================================================================
# SEE SECTION TEMPLATES
# ============================================================================

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

# Fee calculation based on NSW EP&A Regulation Schedule 4
# EP&A Regulation 2021 Schedule 4, as published for 2024-25 in
# documents/fees/nsw-planning-fees-2024-25.pdf (p2). Each bracket is
# (upper bound of estimated cost, base fee, increment per $1,000 above the
# bracket floor). Bases are stepped, not continuous — that is how the schedule
# is written, so the fee jumps at each boundary.
DA_FEE_SCHEDULE_YEAR = "2024-25"
DA_FEE_BRACKETS = [
    (5_000,      144.00, 0.00,       0),
    (50_000,     220.00, 3.00,       5_000),
    (250_000,    459.00, 3.64,      50_000),
    (500_000,  1_509.00, 2.34,     250_000),
    (1_000_000, 2_272.00, 1.64,    500_000),
    (10_000_000, 3_404.00, 1.44, 1_000_000),
    (math.inf, 20_667.00, 1.19,  10_000_000),
]


def calculate_da_fee(development_cost: float) -> dict:
    """Calculate DA fee based on estimated development cost."""
    for upper, base, per_thousand, floor in DA_FEE_BRACKETS:
        if development_cost <= upper:
            # Schedule 4 charges the increment "for each $1,000, or part $1,000,
            # by which estimated cost exceeds" the bracket floor — so a partial
            # thousand is charged as a whole one. Interpolating linearly here
            # under-charged every cost that wasn't a round number of thousands.
            excess = max(0.0, development_cost - floor)
            fee = base + per_thousand * math.ceil(excess / 1000)
            break

    cost_estimate_requirement = "Applicant estimate"
    if development_cost > 100000:
        cost_estimate_requirement = "Qualified person estimate"
    if development_cost > 3000000:
        cost_estimate_requirement = "Registered Quantity Surveyor report"

    return {
        "estimated_fee": round(fee, 2),
        "development_cost": development_cost,
        "cost_estimate_requirement": cost_estimate_requirement,
        "fee_schedule_year": DA_FEE_SCHEDULE_YEAR,
        "note": "This is the statutory DA lodgement fee only. Additional fees may apply for advertising, referrals, long service levy, and Section 7.11 contributions.",
        "currency_warning": (
            f"Calculated from the {DA_FEE_SCHEDULE_YEAR} EP&A Regulation Schedule 4 scale. "
            "Statutory fees are re-set each July — confirm against Council's current fees and "
            "charges before relying on this figure."
        ),
    }


CONTACT_INFO = {
    "council": "Lismore City Council",
    "phone": "(02) 6625 0500",
    "address": "43 Oliver Avenue, Goonellabah NSW 2480",
    "hours": "8:30am–4:30pm Monday–Friday (excluding public holidays)",
    "duty_planner": {
        "service": "Free 15-minute consultations",
        "location": "Corporate Centre, Goonellabah",
        "days": "Tuesdays and Thursdays",
        "time": "8:30am–10:30am",
        "appointment": "No appointment needed"
    },
    "pre_lodgement_form": "https://forms.lismore.nsw.gov.au/forms/7788",
    "da_tracker": "https://www.lismore.nsw.gov.au/Building-and-planning/Development-Applications-in-Lismore/DA-Tracker",
    "planning_portal": "https://www.planningportal.nsw.gov.au/onlineDA"
}


# ============================================================================
# PDF Search Functions
# ============================================================================

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "into", "is", "it", "of", "on", "or", "that", "the", "to", "was",
    "what", "when", "where", "will", "with",
}


def _query_tokens(query: str) -> list[str]:
    """Break a query into significant lowercase tokens (drops stopwords/short words)."""
    words = "".join(c if c.isalnum() else " " for c in query.lower()).split()
    tokens = [w for w in words if len(w) >= 3 and w not in STOPWORDS]
    return tokens or words  # fall back to raw words if everything got filtered out


# Every category the document tools search and list. `exempt-development` holds the
# state-wide NSW DPE fact sheets used for "do I need a DA?" questions; leaving it out
# meant those PDFs shipped with the repo but were unreachable through any tool.
DOC_CATEGORIES = ["dcp", "lep", "forms", "fees", "exempt-development"]

# .txt is included because parts of the LEP only exist here as text extracts
# (legislation.nsw.gov.au and austlii both 403 automated fetches, so they were
# scraped once via Playwright). Note that anything under documents/ is assumed to be
# real content: files that were actually scraper failures — 404 pages, Cloudflare
# challenges — were removed rather than filtered at search time, because a search hit
# quoting a bot-verification page is worse than no hit. Check any new .txt before
# adding it.
SEARCHABLE_SUFFIXES = {".pdf", ".txt"}
LISTABLE_SUFFIXES = {".pdf", ".txt", ".xls", ".xlsx"}


def _score_lines(lines: list[str], tokens: list[str], query: str) -> list[tuple[int, int, list[str], str]]:
    """Score each line by how many distinct query tokens it contains.

    Returns (index, score, matched_terms, context) for every line that matched at
    least one token. Requiring the full phrase verbatim would return nothing for a
    query like "food and drink premises change of use"; scoring by token count still
    ranks a full-phrase line highest while surfacing lines covering only part of the
    concept.
    """
    hits = []
    for i, line in enumerate(lines):
        line_lower = line.lower()
        matched = [t for t in tokens if t in line_lower]
        if not matched:
            continue

        score = len(matched)
        if query.lower() in line_lower:
            score += len(tokens)  # exact-phrase bonus, still just a ranking boost

        start = max(0, i - 2)
        end = min(len(lines), i + 3)
        context = '\n'.join(lines[start:end])
        hits.append((i, score, matched, context.strip()[:500]))
    return hits


def search_pdf(pdf_path: Path, query: str, max_results: int = 5) -> list[dict]:
    """Search a PDF for text matching the query, scored per line."""
    tokens = _query_tokens(query)
    if not tokens:
        return []

    scored = []
    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            lines = doc[page_num].get_text().split('\n')
            for _, score, matched, context in _score_lines(lines, tokens, query):
                scored.append({
                    "score": score,
                    "matched_terms": matched,
                    "page": page_num + 1,
                    "location": f"page {page_num + 1}",
                    "context": context,
                    "file": pdf_path.name
                })

        doc.close()
    except Exception as e:
        return [{"error": str(e)}]

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:max_results]


def search_text_file(text_path: Path, query: str, max_results: int = 5) -> list[dict]:
    """Search a plain-text document, reporting line numbers where a PDF reports pages.

    read_dcp_section takes the same line numbers as its start/end range for .txt files,
    so a hit here can be opened directly.
    """
    tokens = _query_tokens(query)
    if not tokens:
        return []

    try:
        lines = text_path.read_text(encoding="utf-8", errors="replace").split('\n')
    except Exception as e:
        return [{"error": str(e)}]

    scored = [
        {
            "score": score,
            "matched_terms": matched,
            "line": i + 1,
            "location": f"line {i + 1}",
            "context": context,
            "file": text_path.name
        }
        for i, score, matched, context in _score_lines(lines, tokens, query)
    ]

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:max_results]


def search_document(path: Path, query: str, max_results: int = 5) -> list[dict]:
    """Search one document, dispatching on file type."""
    if path.suffix.lower() == ".txt":
        return search_text_file(path, query, max_results)
    return search_pdf(path, query, max_results)


def searchable_documents(chapter: str = "") -> list[Path]:
    """Every searchable document across all categories, optionally filtered by filename."""
    paths = []
    for subdir in DOC_CATEGORIES:
        subdir_path = DOCS_DIR / subdir
        if not subdir_path.exists():
            continue
        for path in sorted(subdir_path.iterdir()):
            if path.suffix.lower() not in SEARCHABLE_SUFFIXES:
                continue
            if chapter and chapter.lower() not in path.name.lower():
                continue
            paths.append(path)
    return paths


def find_document(name: str) -> Path | None:
    """Locate a document by filename or filename fragment, across all categories."""
    candidates = [
        path for path in searchable_documents()
        if name.lower() in path.name.lower()
    ]
    if not candidates:
        return None
    # Prefer an exact filename match over a fragment match ('chapter-1' would
    # otherwise resolve by directory order rather than by what was asked for).
    for path in candidates:
        if path.name.lower() == name.lower():
            return path
    return candidates[0]


def extract_pdf_section(pdf_path: Path, start_page: int = 1, end_page: int = None) -> str:
    """Extract text from specific pages of a PDF."""
    try:
        doc = fitz.open(pdf_path)
        if end_page is None:
            end_page = len(doc)

        text = ""
        for page_num in range(start_page - 1, min(end_page, len(doc))):
            page = doc[page_num]
            text += f"\n--- Page {page_num + 1} ---\n"
            text += page.get_text()

        doc.close()
        return text[:10000]  # Limit output size
    except Exception as e:
        return f"Error reading PDF: {e}"


def extract_text_section(text_path: Path, start_line: int = 1, end_line: int = None) -> str:
    """Extract a line range from a plain-text document.

    Text extracts have no pages, so read_dcp_section's start/end are read as line
    numbers here — matching the line numbers search_text_file reports.
    """
    try:
        lines = text_path.read_text(encoding="utf-8", errors="replace").split('\n')
        if end_line is None:
            end_line = min(len(lines), max(start_line, 1) + 199)  # default window

        selected = lines[max(start_line, 1) - 1:min(end_line, len(lines))]
        header = f"--- {text_path.name}, lines {start_line}-{min(end_line, len(lines))} of {len(lines)} ---\n"
        return (header + '\n'.join(selected))[:10000]
    except Exception as e:
        return f"Error reading text file: {e}"


def extract_document_section(path: Path, start: int = 1, end: int = None) -> str:
    """Read a section of one document — pages for PDFs, lines for text extracts."""
    if path.suffix.lower() == ".txt":
        return extract_text_section(path, start, end)
    return extract_pdf_section(path, start, end)


def list_available_documents() -> list[dict]:
    """List all available documents in the documents directory."""
    documents = []

    if DOCS_DIR.exists():
        for subdir in DOC_CATEGORIES:
            subdir_path = DOCS_DIR / subdir
            if subdir_path.exists():
                for file in sorted(subdir_path.iterdir()):
                    if file.suffix.lower() in LISTABLE_SUFFIXES:
                        documents.append({
                            "category": subdir,
                            "filename": file.name,
                            "path": str(file.relative_to(DOCS_DIR)),
                            "addressed_by": "line number" if file.suffix.lower() == ".txt" else "page number",
                        })

    return documents


# ============================================================================
# SEE PDF Form Configuration
# ============================================================================

# Path to the blank SEE PDF template
SEE_TEMPLATE_PATH = DOCS_DIR / "forms" / "statement-of-environmental-effects-minor-development.pdf"

# The blank template carries no AcroForm fields, so answers have to be drawn
# onto the page. Rather than hardcode coordinates — which were consistently a
# few dozen points out, so text landed on top of the printed labels and outside
# the boxes — the geometry is read out of the template at fill time:
#
#   * every answer box is a white-filled rectangle drawn over the grey form
#   * every tick box is a Wingdings empty-square glyph
#
# Fields below reference those by page plus index in reading order (top to
# bottom, then left to right). If Council reissues the form with a different
# layout the indices still resolve to real boxes, and SEE_LAYOUT_EXPECTED makes
# a change in box/checkbox counts fail loudly instead of silently misplacing text.

# Wingdings empty squares: U+F0A8 on the Yes/No rows, U+F071 on page 1
CHECKBOX_GLYPHS = {"\uf0a8", "\uf071"}

# (boxes, checkboxes) expected per page — guards against template changes
SEE_LAYOUT_EXPECTED = {
    0: (8, 1),
    1: (3, 0),
    2: (3, 8),
    3: (3, 18),
    4: (3, 28),
    5: (3, 20),
    6: (8, 0),
    7: (0, 0),
}


def _answer_boxes(page) -> list:
    """White-filled input boxes on a page, in reading order."""
    boxes, seen = [], set()
    for drawing in page.get_drawings():
        rect = drawing["rect"]
        if drawing.get("fill") != (1.0, 1.0, 1.0):
            continue
        if rect.width < 30 or rect.height < 10:
            continue
        key = (round(rect.x0, 1), round(rect.y0, 1), round(rect.x1, 1), round(rect.y1, 1))
        if key in seen:
            continue
        seen.add(key)
        boxes.append(rect)
    boxes.sort(key=lambda r: (round(r.y0), r.x0))
    return boxes


def _checkbox_rects(page) -> list:
    """Tick box glyph rectangles on a page, in reading order."""
    rects = []
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                for char in span.get("chars", []):
                    if char["c"] in CHECKBOX_GLYPHS:
                        rects.append(fitz.Rect(char["bbox"]))
    rects.sort(key=lambda r: (round(r.y0), r.x0))
    return rects


def see_layout(doc) -> dict:
    """Map each page to its answer boxes and tick boxes, discovered from the PDF."""
    return {
        page_num: {
            "boxes": _answer_boxes(doc[page_num]),
            "checks": _checkbox_rects(doc[page_num]),
        }
        for page_num in range(len(doc))
    }


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


# ---------------------------------------------------------------------------
# Land use classification
# ---------------------------------------------------------------------------
# Child terms and the broader parent categories they fall under. If a parent is
# permitted in a zone, so is everything beneath it.

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


def canonical_use(term: str) -> str:
    """Normalise a land use term for comparison, including naive singularisation.

    Applied to both sides of every comparison, so "Restaurants or cafes" and
    "restaurant or cafe" meet in the middle.
    """
    text = term.lower().replace("-", " ").replace("_", " ")
    text = " ".join(text.split())
    return re.sub(r"\b(\w{3,}?)s\b", r"\1", text)


def match_land_use(term: str, uses: list[str], strength: str) -> str | None:
    """Find `term` in a zone's use list at one matching strength.

    "exact" compares whole terms, "hierarchy" looks for the broader categories the
    term sits under, "approximate" falls back to a word-boundary containment search.
    Keeping these separate is what stops 'shop' latching onto 'Shop top housing'
    before the hierarchy has had a chance to resolve it to 'Commercial premises'.
    """
    target = canonical_use(term)
    if not target:
        return None

    if strength == "exact":
        return next((use for use in uses if canonical_use(use) == target), None)

    if strength == "hierarchy":
        for parent in LAND_USE_HIERARCHY.get(target, []):
            parent_canonical = canonical_use(parent)
            for use in uses:
                if canonical_use(use) == parent_canonical:
                    return use
        return None

    return next(
        (use for use in uses if re.search(rf"\b{re.escape(target)}\b", canonical_use(use))),
        None,
    )


def classify_land_use(proposed_use: str, zone_info: dict, zone_code: str = "") -> dict | None:
    """Classify a use against a zone's land use table.

    Returns None when there is nothing to go on. `permissible` is left None when the
    answer is genuinely unclear, so the form's tick stays blank rather than recording
    a guess. An express listing beats a broader group term, which is why matching
    strength is the outer loop: 'Restaurants or cafes' is expressly permitted in R1
    even though its parent 'Commercial premises' is prohibited there.
    """
    if not proposed_use or not zone_info:
        return None

    zone_label = f"Zone {zone_code}".strip() if zone_code else "the zone"
    categories = (
        ("permitted_without_consent", zone_info.get("permitted_without_consent", []), True, "permitted without consent in"),
        ("permitted_with_consent", zone_info.get("permitted_with_consent", []), True, "permitted with consent in"),
        ("prohibited", zone_info.get("prohibited", []), False, "prohibited in"),
    )

    for strength in ("exact", "hierarchy", "approximate"):
        for category, uses, permissible, phrase in categories:
            matched = match_land_use(proposed_use, uses, strength)
            if not matched or CATCHALL_TERM in canonical_use(matched):
                continue
            if strength == "hierarchy":
                statement = (
                    f"'{proposed_use}' falls under '{matched}', which is {phrase} {zone_label} "
                    "under the LEP 2012 land use table."
                )
            elif strength == "exact":
                statement = f"'{matched}' is {phrase} {zone_label} under the LEP 2012 land use table."
            else:
                statement = (
                    f"'{proposed_use}' appears to correspond to '{matched}', which is {phrase} {zone_label}. "
                    "Confirm the exact land use term with Council."
                )
            return {
                "permissible": permissible if strength != "approximate" else None,
                "matched_use": matched,
                "match_type": strength,
                "category": category,
                "statement": statement,
                "basis": f"LEP 2012 land use table for {zone_label} — matched '{matched}' ({strength})",
            }

    with_consent = zone_info.get("permitted_with_consent", [])
    prohibited = zone_info.get("prohibited", [])

    if any(CATCHALL_TERM in canonical_use(u) for u in with_consent):
        return {
            "permissible": None,
            "matched_use": None,
            "match_type": "catchall",
            "category": "catchall",
            "statement": (
                f"'{proposed_use}' is not listed in the {zone_label} land use table, which permits "
                "'any other development not specified in item 2 or 4' with consent. Confirm with the Duty Planner."
            ),
            "basis": f"not listed in the {zone_label} land use table; catch-all applies",
        }
    if any(CATCHALL_TERM in canonical_use(u) for u in prohibited):
        return {
            "permissible": False,
            "matched_use": None,
            "match_type": "catchall",
            "category": "catchall",
            "statement": (
                f"'{proposed_use}' is not listed in the {zone_label} land use table, which prohibits "
                "'any other development not specified'. This use is likely prohibited."
            ),
            "basis": f"not listed in the {zone_label} land use table; prohibited catch-all applies",
        }

    return {
        "permissible": None,
        "matched_use": None,
        "match_type": "none",
        "category": None,
        "statement": f"'{proposed_use}' could not be located in the {zone_label} land use table. Confirm with Council.",
        "basis": f"no match in the {zone_label} land use table",
    }


# ---------------------------------------------------------------------------
# The form's Yes/No questions
# ---------------------------------------------------------------------------
# Every one of these is a declaration the applicant signs as true on page 7, so
# none of them is answered unless the answer was supplied or is entailed by
# something that was. Keys match the SEE_FORM_FIELDS prefixes ("<key>_yes"/"_no").

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


def parse_street_address(
    property_address: str,
    unit: str = "",
    street_number: str = "",
    street: str = "",
    suburb: str = "",
) -> dict:
    """Split an address into the form's boxes, preferring explicitly supplied parts.

    The free-text fallback handles tenancy prefixes ("Shop 3, 88 Keen Street"),
    which the previous first-token-before-the-comma approach shifted one box left.
    """
    parts = {
        "unit": unit.strip(),
        "street_number": street_number.strip(),
        "street": street.strip(),
        "suburb": suburb.strip(),
    }
    if parts["street_number"] and parts["street"]:
        return parts

    text = property_address.strip()
    if not text:
        return parts

    segments = [s.strip() for s in text.split(",") if s.strip()]

    # Suburb: the last segment that isn't just NSW and/or a postcode
    if not parts["suburb"]:
        for segment in reversed(segments[1:] or segments):
            candidate = re.sub(r"\b\d{4}\b", "", segment)
            candidate = re.sub(r"\bNSW\b", "", candidate, flags=re.I)
            candidate = " ".join(candidate.split())
            if candidate:
                parts["suburb"] = candidate
                break

    # Street: work through the leading segments, peeling off any tenancy prefix
    street_text = segments[0] if segments else ""
    prefix = re.match(r"^(shop|unit|suite|tenancy|villa|apartment|apt)\s*([\w/-]+)?\s*$", street_text, re.I)
    if prefix and len(segments) > 1:
        # "Shop 3, 88 Keen Street, ..." — the tenancy is its own segment
        if not parts["unit"]:
            parts["unit"] = " ".join(w for w in prefix.groups() if w).strip()
        street_text = segments[1]
    else:
        inline = re.match(r"^(shop|unit|suite|tenancy|villa|apartment|apt)\s+([\w/-]+)[,\s]+(.*)$", street_text, re.I)
        if inline:
            if not parts["unit"]:
                parts["unit"] = f"{inline.group(1)} {inline.group(2)}".strip()
            street_text = inline.group(3)

    number = re.match(r"^(\d+[A-Za-z]?(?:\s*[-–/]\s*\d+[A-Za-z]?)?)\s+(.*)$", street_text.strip())
    if number:
        parts["street_number"] = parts["street_number"] or number.group(1).replace(" ", "")
        parts["street"] = parts["street"] or number.group(2).strip()
    else:
        parts["street"] = parts["street"] or street_text.strip()

    return parts


def parse_land_identifier(
    lot_dp: str = "",
    lot: str = "",
    plan_type: str = "",
    plan_number: str = "",
    section: str = "",
) -> dict:
    """Resolve the Lot / DP / Section boxes, preferring explicitly supplied parts.

    Recognises "Lot 12 DP 758651", "12/758651", "SP 12345" and comma-separated
    variants. Returns whatever it could resolve — the caller refuses to write a
    blank land identifier rather than printing empty boxes.
    """
    resolved = {
        "lot": lot.strip(),
        "plan_type": (plan_type or "").strip().upper(),
        "plan_number": str(plan_number or "").strip(),
        "section": section.strip(),
    }
    text = " ".join((lot_dp or "").split())
    if not text:
        return resolved

    # Each part is picked up by its own keyword, so "Lot 5 Section 3 DP 1234"
    # doesn't hand the section number to the lot box.
    if not resolved["section"]:
        m = re.search(r"\bsec(?:tion)?\s*[:.]?\s*([\w-]+)", text, re.I)
        if m:
            resolved["section"] = m.group(1).strip(" ,.").upper()

    if not resolved["lot"]:
        m = re.search(r"\blot\s*[:.]?\s*([\w-]+)", text, re.I)
        if m:
            resolved["lot"] = m.group(1).strip(" ,.").upper()

    if not resolved["plan_number"]:
        m = re.search(r"\b(DP|SP|CP)\s*[:.]?\s*(\d+)", text, re.I)
        if m:
            resolved["plan_type"] = m.group(1).upper()
            resolved["plan_number"] = m.group(2)
            # "12 DP 758651" — a bare lot number ahead of the plan, no keyword
            if not resolved["lot"]:
                before = re.search(r"([\w-]+)\s*,?\s*$", text[:m.start()])
                if before and "sec" not in before.group(1).lower():
                    resolved["lot"] = before.group(1).strip(" ,.").upper()
        else:
            # 12/758651 — lot over plan, deposited plan assumed
            m = re.match(r"^(?:lot\s*)?([\w-]+)\s*/\s*(\d+)$", text, re.I)
            if m:
                resolved["lot"] = resolved["lot"] or m.group(1).upper()
                resolved["plan_type"] = "DP"
                resolved["plan_number"] = m.group(2)

    return resolved


def estimate_parking_requirement(rate_text: str, floor_area_sqm: float, num_employees: int) -> dict | None:
    """Turn a DCP Chapter 7 rate string into an indicative number of spaces.

    Returns None when the rate can't be read numerically, rather than guessing.
    """
    total = 0.0
    basis = []

    area_rate = re.search(r"1\s*(?:space)?\s*per\s*(\d+(?:\.\d+)?)\s*m", rate_text, re.I)
    if area_rate and floor_area_sqm:
        per = float(area_rate.group(1))
        total += floor_area_sqm / per
        basis.append(f"{floor_area_sqm:g}m² at 1 space per {per:g}m²")

    staff_rate = re.search(r"1\s*(?:space)?\s*per\s*(\d+)\s*(?:staff|employee)", rate_text, re.I)
    if staff_rate and num_employees:
        per = float(staff_rate.group(1))
        total += num_employees / per
        basis.append(f"{num_employees} staff at 1 space per {per:g}")

    if not basis:
        return None

    return {
        "spaces_required": math.ceil(total),
        "basis": basis,
        "rate": rate_text,
        "caveat": "Indicative only. The DCP rate may apply to a narrower area (e.g. dining area rather than gross floor area) — confirm the area basis with Council.",
    }


def generate_see_form_data(
    applicant_name: str,
    property_address: str,
    lot_dp: str,
    zone_code: str,
    proposed_use: str,
    development_type: str,
    floor_area_sqm: float,
    minor_development_type: str = "",
    building_description: str = "",
    hours_of_operation: str = "",
    num_employees: int = 0,
    num_customers: int = 0,
    estimated_cost: float = 0,
    is_flood_affected: bool | None = None,
    is_bushfire_prone: bool | None = None,
    is_heritage: bool | None = None,
    in_heritage_conservation_area: bool | None = None,
    existing_use: str = "",
    site_description: str = "",
    surrounding_context: str = "",
    unit: str = "",
    street_number: str = "",
    street: str = "",
    suburb: str = "",
    building_name: str = "",
    lot: str = "",
    plan_type: str = "",
    plan_number: str = "",
    section: str = "",
    internal_works_only: bool = False,
    parking_spaces_provided: int | None = None,
    stormwater_to_council_system: bool | None = None,
    answers: dict | None = None,
    comments: dict | None = None,
) -> dict:
    """Build the SEE form data, plus a report of what still needs answering.

    Returns {"fields", "unanswered_questions", "derived_answers", "blocking_issues",
    "parking", "required_documents"}. Nothing is ticked unless the answer was given
    in `answers` or is entailed by another supplied fact (listed in derived_answers).
    """
    answers = {k: v for k, v in (answers or {}).items() if v is not None}
    comments = {k: v.strip() for k, v in (comments or {}).items() if isinstance(v, str) and v.strip()}

    blocking: list[str] = []
    derived: dict[str, str] = {}
    required_documents: list[str] = []

    unknown_answers = sorted(set(answers) - set(SEE_QUESTIONS))
    if unknown_answers:
        blocking.append(
            "Unrecognised answer key(s): " + ", ".join(unknown_answers)
            + ". Valid keys: " + ", ".join(sorted(SEE_QUESTIONS))
        )
    unknown_comments = sorted(set(comments) - set(SEE_COMMENT_FIELDS))
    if unknown_comments:
        blocking.append(
            "Unrecognised comment key(s): " + ", ".join(unknown_comments)
            + ". Valid keys: " + ", ".join(sorted(SEE_COMMENT_FIELDS))
        )

    # --- scope: this template covers minor residential development only --------
    if minor_development_type not in SEE_TEMPLATE_SCOPE:
        blocking.append(
            "This form is for 'Minor Development Only'. Set minor_development_type to one of: "
            + ", ".join(SEE_TEMPLATE_SCOPE)
            + ". Anything else needs a purpose-written SEE (see the generate_see_draft tool)."
        )

    zone_code = (zone_code or "").upper().strip()
    zone_info = ZONES.get(zone_code, {})
    if not zone_info:
        blocking.append(
            f"Zone '{zone_code}' is not in the LEP 2012 zone list. Valid zones: "
            + ", ".join(sorted(z for z in ZONES if "redirect_to" not in ZONES[z]))
        )
    elif "redirect_to" in zone_info:
        replacement = zone_info["redirect_to"]
        blocking.append(
            f"Zone {zone_code} was replaced by {replacement} under the employment zones reform. Use {replacement}."
        )
        zone_info = ZONES.get(replacement, {})
        zone_code = replacement

    zone_name = zone_info.get("name", "")

    if minor_development_type == "dwelling_single_storey":
        if zone_code and zone_code not in RESIDENTIAL_ZONES:
            blocking.append(
                f"The template restricts single dwellings to residential zones; {zone_code} is not one "
                f"({', '.join(sorted(RESIDENTIAL_ZONES))})."
            )
        if in_heritage_conservation_area:
            blocking.append(
                "The template excludes single dwellings in heritage conservation areas — a purpose-written SEE is required."
            )

    # --- permissibility, from the LEP land use table ---------------------------
    proposed_use = (proposed_use or "").strip()
    permissibility = classify_land_use(proposed_use, zone_info, zone_code) if zone_info else None
    if permissibility and permissibility["permissible"] is not None:
        answers.setdefault("permissible", permissibility["permissible"])
        derived["permissible"] = permissibility["basis"]

    # --- answers entailed by supplied facts -----------------------------------
    if is_heritage is not None or in_heritage_conservation_area is not None:
        heritage_affected = bool(is_heritage or in_heritage_conservation_area)
        answers.setdefault("heritage_impact", heritage_affected)
        derived["heritage_impact"] = (
            "site declared a heritage item or within a heritage conservation area"
            if heritage_affected else "site declared as neither a heritage item nor in a conservation area"
        )
        if heritage_affected:
            required_documents.append(
                "Heritage Impact Statement (DCP Chapter 12) — the impact on heritage significance must be assessed, not assumed"
            )

    if internal_works_only:
        for key, basis in (
            ("excavation", "internal works only — no ground disturbance proposed"),
            ("remove_vegetation", "internal works only — no vegetation removal proposed"),
            ("threatened_species", "internal works only — no habitat disturbance proposed"),
        ):
            if key not in answers:
                answers[key] = False
                derived[key] = basis

    if is_flood_affected:
        required_documents.append(
            "Flood Risk Assessment and floor levels relative to the Flood Planning Level (LEP cl 5.21, DCP Chapter 8)"
        )
    if is_bushfire_prone:
        required_documents.append(
            "Bushfire assessment addressing Planning for Bushfire Protection (BAL rating)"
        )

    # --- parking, from the DCP rate rather than an assertion -------------------
    parking = None
    rate_key = (proposed_use or "").lower().replace(" ", "_")
    rate_entry = PARKING_RATES.get(rate_key)
    if rate_entry:
        parking = estimate_parking_requirement(rate_entry["spaces"], floor_area_sqm, num_employees)
        if parking:
            parking["spaces_provided"] = parking_spaces_provided
            if parking_spaces_provided is None:
                parking["shortfall"] = None
            else:
                parking["shortfall"] = max(0, parking["spaces_required"] - parking_spaces_provided)

    # --- text boxes: supplied text, or facts, never filler --------------------
    def article(word: str) -> str:
        return "an" if word[:1].lower() in "aeiou" else "a"

    dev_type_desc = {
        "new_building": "Construction of a new building",
        "alteration": "Alterations and additions to an existing building",
        "change_of_use": "Change of use of an existing premises",
        "fitout": "Internal fit-out of an existing premises",
    }.get(development_type, development_type)

    proposal_lines = []
    if building_description:
        proposal_lines.append(building_description)
    elif proposed_use:
        proposal_lines.append(f"{dev_type_desc} to {article(proposed_use)} {proposed_use}.")
    else:
        proposal_lines.append(f"{dev_type_desc}.")
    proposal_lines.append("")
    if floor_area_sqm:
        proposal_lines.append(f"Floor area: {floor_area_sqm:g}m²")
    if hours_of_operation:
        proposal_lines.append(f"Hours of operation: {hours_of_operation}")
    if num_employees:
        proposal_lines.append(f"Number of employees: {num_employees}")
    if num_customers:
        proposal_lines.append(f"Maximum customers: {num_customers}")
    if estimated_cost:
        proposal_lines.append(f"Estimated cost of works: ${estimated_cost:,.0f}")
    proposal_desc = "\n".join(proposal_lines).strip()

    site_lines = [site_description] if site_description else []
    if zone_name:
        site_lines.append(f"The site is zoned {zone_code} {zone_name} under Lismore LEP 2012.")
    if existing_use:
        site_lines.append(f"Existing use: {existing_use}")
    site_desc = "\n\n".join(site_lines).strip()

    hazard_lines = []
    if is_flood_affected:
        hazard_lines.append(
            "The site is flood prone. Floor levels, structural soundness and evacuation are to be assessed "
            "against LEP 2012 clause 5.21 and DCP Chapter 8."
        )
    if is_bushfire_prone:
        hazard_lines.append(
            "The site is bushfire prone. Planning for Bushfire Protection applies and a BAL assessment is required."
        )
    if is_flood_affected is False and is_bushfire_prone is False and not hazard_lines:
        hazard_lines.append("The site is not identified as flood prone or bushfire prone.")
    hazards_comments = comments.get("hazards_comments") or "\n".join(hazard_lines)

    constraint_lines = []
    if is_heritage:
        constraint_lines.append(
            "The site is a heritage item under LEP 2012 Schedule 5. A Heritage Impact Statement accompanies "
            "this application; the impact on heritage significance is assessed there."
        )
    if in_heritage_conservation_area:
        constraint_lines.append("The site is within a heritage conservation area.")
    constraints = comments.get("constraints") or "\n".join(constraint_lines)

    planning_lines = [f"Zone: {zone_code} {zone_name}".strip()]
    if permissibility:
        planning_lines.append(permissibility["statement"])
    if comments.get("planning_comments"):
        planning_lines.append(comments["planning_comments"])
    planning_comments = "\n".join(line for line in planning_lines if line)

    access_lines = [comments["access_comments"]] if comments.get("access_comments") else []
    if parking:
        summary = (
            f"Off-street parking: DCP Chapter 7 indicates approximately {parking['spaces_required']} "
            f"space(s) for this use ({'; '.join(parking['basis'])})."
        )
        if parking_spaces_provided is not None:
            summary += f" {parking_spaces_provided} space(s) are provided on site."
            if parking["shortfall"]:
                summary += (
                    f" This is a shortfall of {parking['shortfall']} space(s), which is addressed in the "
                    "parking assessment accompanying this application."
                )
        access_lines.append(summary)
    access_comments = "\n".join(access_lines)

    waste_lines = [comments["waste_comments"]] if comments.get("waste_comments") else []
    if stormwater_to_council_system:
        waste_lines.append("Stormwater is disposed of to the Council drainage system.")
    elif stormwater_to_council_system is False and comments.get("stormwater_details"):
        waste_lines.append(f"Stormwater disposal: {comments['stormwater_details']}")
    waste_comments = "\n".join(waste_lines)

    social_lines = [comments["social_comments"]] if comments.get("social_comments") else []
    if num_employees:
        social_lines.append(f"The proposal will provide employment for {num_employees} people.")
    social_comments = "\n".join(social_lines)

    # --- assemble the fields --------------------------------------------------
    address = parse_street_address(property_address, unit, street_number, street, suburb)
    land = parse_land_identifier(lot_dp, lot, plan_type, plan_number, section)

    if not land["plan_number"]:
        blocking.append(
            "The land could not be identified. Supply plan_type ('DP', 'SP' or 'CP') and plan_number, "
            "or a lot_dp string such as 'Lot 12 DP 758651'. The form is not written with a blank land identifier."
        )
    if not address["street_number"] or not address["street"]:
        blocking.append(
            "The street address could not be split reliably. Supply street_number and street "
            "(plus unit for a shop or unit tenancy)."
        )

    plan_box = land["plan_number"]
    if plan_box and land["plan_type"] and land["plan_type"] != "DP":
        plan_box = f"{land['plan_type']} {plan_box}"

    fields: dict = {
        "applicant_name": applicant_name,
        "address_number": " ".join(p for p in (address["unit"], address["street_number"]) if p).strip(),
        "street_name": address["street"],
        "building_name": building_name,
        "suburb": address["suburb"],
        "lot": land["lot"],
        "dp": plan_box,
        "section": land["section"],

        "description_of_development": proposal_desc,
        "description_of_site": site_desc,
        "present_previous_use": existing_use,

        "bushfire_prone": is_bushfire_prone,
        "flooding": is_flood_affected,
        "hazards_comments": hazards_comments,
        "constraints": constraints,
        "surrounding_land_use": comments.get("surrounding_land_use") or surrounding_context,

        "planning_comments": planning_comments,
        "context_comment": comments.get("context_comment", ""),
        "privacy_comments": comments.get("privacy_comments", ""),
        "access_comments": access_comments,
        "traffic_amount": comments.get("traffic_amount", ""),
        "environmental_comments": comments.get("environmental_comments", ""),
        "flora_comments": comments.get("flora_comments", ""),
        "waste_comments": waste_comments,
        "stormwater_details": comments.get("stormwater_details", ""),
        "social_comments": social_comments,
        "other_matters": comments.get("other_matters", ""),

        "stormwater_council": stormwater_to_council_system,
        "stormwater_other": (not stormwater_to_council_system) if stormwater_to_council_system is not None else None,

        "declaration_name_1": applicant_name,
        "declaration_name_2": "",
        "declaration_date_1": "",  # signed and dated by hand
        "declaration_date_2": "",
    }

    # One tick per answered question; unanswered questions stay blank on the form.
    unanswered = []
    for key, question in SEE_QUESTIONS.items():
        value = answers.get(key)
        if value is None:
            fields[f"{key}_yes"] = None
            fields[f"{key}_no"] = None
            unanswered.append({"key": key, "question": question})
        else:
            fields[f"{key}_yes"] = bool(value)
            fields[f"{key}_no"] = not bool(value)

    if is_flood_affected is None:
        unanswered.append({"key": "flooding", "question": "Is the site subject to flooding or stormwater inundation?"})
    if is_bushfire_prone is None:
        unanswered.append({"key": "bushfire_prone", "question": "Is the site bushfire prone?"})
    if stormwater_to_council_system is None:
        unanswered.append({"key": "stormwater", "question": "How will stormwater from roof and hard standing be disposed of?"})
    if answers.get("increase_traffic") and not fields["traffic_amount"]:
        unanswered.append({"key": "traffic_amount", "question": SEE_COMMENT_FIELDS["traffic_amount"]})
    if parking and parking.get("shortfall") is None:
        unanswered.append({
            "key": "parking_spaces_provided",
            "question": f"How many off-street parking spaces are provided? DCP Chapter 7 indicates approximately {parking['spaces_required']}.",
        })
    if not fields["present_previous_use"]:
        unanswered.append({"key": "existing_use", "question": "What is the present use and previous use of the site?"})

    # Comment boxes that are questions in their own right, not optional extras
    for field, question in (
        ("constraints", "What other constraints exist on the site (vegetation, easements, sloping land, drainage lines, contamination)?"),
        ("surrounding_land_use", "What types of land use and development exist on surrounding land?"),
    ):
        if not fields[field]:
            unanswered.append({"key": field, "question": question})

    return {
        "fields": fields,
        "unanswered_questions": unanswered,
        "derived_answers": derived,
        "blocking_issues": blocking,
        "parking": parking,
        "required_documents": required_documents,
    }


FILL_FONT = "helv"
FILL_FONT_OBJ = fitz.Font(FILL_FONT)
BOX_PADDING = 3          # points of clearance inside each answer box
MAX_FONTSIZE = 10.0
MIN_FONTSIZE = 6.5       # below this the form stops being legible when printed


def _draw_tick(page, rect) -> None:
    """Draw a cross inside the tick box, sized to the box."""
    inset = rect.width * 0.22
    box = fitz.Rect(rect.x0 + inset, rect.y0 + inset, rect.x1 - inset, rect.y1 - inset)
    width = max(0.8, rect.width * 0.09)
    page.draw_line(box.tl, box.br, color=(0, 0, 0), width=width)
    page.draw_line(box.bl, box.tr, color=(0, 0, 0), width=width)


def _write(page, area, text: str, fontsize: float) -> list:
    """Write text into area, returning the lines that didn't fit.

    TextWriter is used rather than Page.insert_textbox because it writes the
    part that fits and hands back the remainder, instead of discarding the whole
    field when the text is too long.
    """
    writer = fitz.TextWriter(page.rect)
    leftover = writer.fill_textbox(
        area,
        text,
        font=FILL_FONT_OBJ,
        fontsize=fontsize,
        align=fitz.TEXT_ALIGN_LEFT,
        warn=None,  # None = stay silent on overflow; True warns, False raises
    )
    writer.write_text(page, color=(0, 0, 0))
    return leftover or []


def _draw_single_line(page, rect, text: str) -> bool:
    """Draw one line of text, vertically centred in the box, shrinking to fit its width.

    Returns False when the value is too long even at the minimum size; it is
    then ellipsised rather than printed across the form's labels.
    """
    width = rect.width - 2 * BOX_PADDING
    fontsize = min(MAX_FONTSIZE, rect.height * 0.62)

    while (fitz.get_text_length(text, fontname=FILL_FONT, fontsize=fontsize) > width
           and fontsize > MIN_FONTSIZE):
        fontsize -= 0.25

    fits = fitz.get_text_length(text, fontname=FILL_FONT, fontsize=fontsize) <= width
    if not fits:
        while text and fitz.get_text_length(text + "…", fontname=FILL_FONT, fontsize=fontsize) > width:
            text = text[:-1]
        text = text.rstrip() + "…"

    line_height = fontsize * 1.2
    top = rect.y0 + max(0, (rect.height - line_height) / 2)
    _write(page, fitz.Rect(rect.x0 + BOX_PADDING, top, rect.x1 - BOX_PADDING, rect.y1), text, fontsize)
    return fits


def _draw_wrapped(page, rect, text: str) -> bool:
    """Draw wrapped text inside the box, shrinking to fit.

    Returns False if the text still doesn't fit at the minimum size — as much as
    fits is written, and the caller reports the field so the rest can go on an
    attachment page.
    """
    area = rect + (BOX_PADDING, BOX_PADDING, -BOX_PADDING, -BOX_PADDING)
    fontsize = MAX_FONTSIZE

    while fontsize > MIN_FONTSIZE:
        # Measure on a throwaway copy so a failed attempt leaves no ink behind.
        probe = fitz.open()
        probe_page = probe.new_page(width=page.rect.width, height=page.rect.height)
        if not _write(probe_page, area, text, fontsize):
            probe.close()
            _write(page, area, text, fontsize)
            return True
        probe.close()
        fontsize -= 0.5

    return not _write(page, area, text, MIN_FONTSIZE)


def fill_see_pdf(form_data: dict, output_path: Path) -> dict:
    """Fill the SEE PDF template and save to output_path.

    Returns {"success": bool, ...} with any layout warnings — fields whose text
    was too long for the printed box (those need a continuation attachment) and
    any field whose box couldn't be located in the template.
    """
    try:
        doc = fitz.open(SEE_TEMPLATE_PATH)
        layout = see_layout(doc)

        overflowed: list[str] = []
        unresolved: list[str] = []
        template_changed: list[str] = []

        for page_num, (want_boxes, want_checks) in SEE_LAYOUT_EXPECTED.items():
            found = layout.get(page_num)
            if found is None:
                template_changed.append(f"page {page_num + 1} missing")
                continue
            got = (len(found["boxes"]), len(found["checks"]))
            if got != (want_boxes, want_checks):
                template_changed.append(
                    f"page {page_num + 1}: expected {want_boxes} boxes/{want_checks} tick boxes, found {got[0]}/{got[1]}"
                )

        for field_name, field_config in SEE_FORM_FIELDS.items():
            value = form_data.get(field_name)
            if value is None:
                continue

            page_num = field_config["page"]
            if page_num >= len(doc):
                unresolved.append(field_name)
                continue
            page = doc[page_num]

            if "check" in field_config:
                if not value:
                    continue  # unticked boxes are left as the form prints them
                checks = layout[page_num]["checks"]
                index = field_config["check"]
                if index >= len(checks):
                    unresolved.append(field_name)
                    continue
                _draw_tick(page, checks[index])
                continue

            text = str(value).strip()
            if not text:
                continue

            boxes = layout[page_num]["boxes"]
            index = field_config["box"]
            if index >= len(boxes):
                unresolved.append(field_name)
                continue
            box = boxes[index]

            # Boxes only one line tall get centred single-line treatment;
            # the tall comment boxes get wrapped paragraphs.
            if box.height < 24:
                fits = _draw_single_line(page, box, " ".join(text.split()))
            else:
                fits = _draw_wrapped(page, box, text)

            if not fits:
                overflowed.append(field_name)

        # Anything that spilled has to continue on an attachment, so tick page 1's
        # "I have provided supporting information ... attached to this SEE" box —
        # unless the caller has taken a position on it either way.
        if overflowed and form_data.get("supporting_info_attached") is None:
            checks = layout[0]["checks"]
            if checks:
                _draw_tick(doc[0], checks[0])

        doc.save(str(output_path))
        doc.close()

        return {
            "success": True,
            "overflowed_fields": overflowed,
            "unresolved_fields": unresolved,
            "template_layout_changed": template_changed,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# MCP Tool Definitions
# ============================================================================

TOOLS: list[Tool] = [
        Tool(
            name="get_parking_rates",
            description="Get off-street parking requirements for a development type in Lismore. Supply floor_area_sqm, num_employees and spaces_provided to also get the indicative number of spaces required and any shortfall to be addressed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_type": {
                        "type": "string",
                        "description": "Type of development (e.g., 'dwelling_house', 'restaurant', 'shop', 'office', 'warehouse')"
                    },
                    "floor_area_sqm": {
                        "type": "number",
                        "description": "Optional. Floor area the rate applies to, in square metres."
                    },
                    "num_employees": {
                        "type": "integer",
                        "description": "Optional. Number of employees, for rates with a staff component."
                    },
                    "spaces_provided": {
                        "type": "integer",
                        "description": "Optional. Spaces provided on site, to calculate the shortfall."
                    }
                },
                "required": ["development_type"]
            }
        ),
        Tool(
            name="get_zone_info",
            description="Get information about a zoning classification in Lismore LEP 2012, including objectives, permitted uses, and development standards.",
            inputSchema={
                "type": "object",
                "properties": {
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code (e.g., 'R1', 'R2', 'R3', 'B2', 'B3', 'IN1', 'RU5')"
                    }
                },
                "required": ["zone_code"]
            }
        ),
        Tool(
            name="calculate_da_fees",
            description="Calculate the Development Application lodgement fee based on estimated development cost.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_cost": {
                        "type": "number",
                        "description": "Estimated cost of development works in dollars"
                    }
                },
                "required": ["development_cost"]
            }
        ),
        Tool(
            name="get_flood_requirements",
            description="Get flood planning requirements for development in Lismore, including floor level requirements and exemptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_type": {
                        "type": "string",
                        "description": "Type of development: 'residential', 'commercial', or 'cbd'"
                    }
                },
                "required": ["development_type"]
            }
        ),
        Tool(
            name="get_contact_info",
            description="Get Lismore City Council contact information, including duty planner availability and key URLs.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="search_dcp",
            description="Search Lismore's planning documents (DCP chapters, LEP documents and text extracts, forms, fee schedules, and the NSW exempt-development fact sheets) for specific provisions, requirements, or keywords. Matches on significant terms in the query, not just the exact phrase, so multi-word conceptual queries still surface partial matches. Each hit reports the file plus a location — a page number for PDFs, a line number for text extracts — that read_dcp_section accepts directly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term or phrase to find in DCP documents"
                    },
                    "chapter": {
                        "type": "string",
                        "description": "Optional: specific chapter to search (e.g., 'chapter-1', 'chapter-7', 'nimbin')"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="read_dcp_section",
            description="Read a section from any planning document — a DCP chapter, an LEP text extract, a form, a fee schedule, or an exempt-development fact sheet. Use list_documents for filenames.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chapter": {
                        "type": "string",
                        "description": "Document filename or a fragment of it (e.g., 'chapter-7-off-street-carparking.pdf', 'lep-2012-nsw-full.txt', 'fences')"
                    },
                    "start_page": {
                        "type": "integer",
                        "description": "Starting page number, or starting line number for .txt documents (default: 1)"
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "Ending page number, or ending line number for .txt documents (optional; .txt defaults to a 200-line window)"
                    }
                },
                "required": ["chapter"]
            }
        ),
        Tool(
            name="list_documents",
            description="List all available planning documents (DCP chapters, LEP documents and text extracts, forms, fee schedules, exempt-development fact sheets), with how each is addressed by read_dcp_section.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_da_checklist",
            description="Get a checklist of required documents for a Development Application based on development type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_type": {
                        "type": "string",
                        "description": "Type of development (e.g., 'dwelling', 'commercial', 'subdivision', 'change_of_use')"
                    }
                },
                "required": ["development_type"]
            }
        ),
        Tool(
            name="list_parking_types",
            description="List all development types that have parking rate information available.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="list_zones",
            description="List all zone codes available in Lismore LEP 2012.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_definition",
            description="Get the Standard Instrument LEP definition of a land-use term (e.g. 'retail premises' vs 'food and drink premises' vs 'shop'), including related terms. Use this to work out which defined use a proposal actually falls under before checking zone permissibility.",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "Land-use term to look up (e.g. 'retail premises', 'food and drink premises', 'shop', 'home business')"
                    }
                },
                "required": ["term"]
            }
        ),
        Tool(
            name="check_permissibility",
            description="Check if a specific land use is permitted in a specific zone. Returns whether the use is permitted without consent, permitted with consent, prohibited, or not found. Essential first step for any DA - confirms the proposal is actually permissible.",
            inputSchema={
                "type": "object",
                "properties": {
                    "land_use": {
                        "type": "string",
                        "description": "The proposed land use (e.g., 'restaurant or cafe', 'dwelling house', 'warehouse', 'shop top housing')"
                    },
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code (e.g., 'R1', 'E2', 'MU1')"
                    }
                },
                "required": ["land_use", "zone_code"]
            }
        ),
        Tool(
            name="get_setback_requirements",
            description="Get setback requirements for residential development. Returns front, side, and rear setback requirements based on dwelling type and lot configuration.",
            inputSchema={
                "type": "object",
                "properties": {
                    "setback_type": {
                        "type": "string",
                        "description": "Type of setback: 'front', 'side', 'rear', or 'all'"
                    },
                    "development_type": {
                        "type": "string",
                        "description": "Optional: 'single_storey', 'two_storey', 'corner_lot', 'battle_axe'"
                    }
                },
                "required": ["setback_type"]
            }
        ),
        Tool(
            name="check_referrals",
            description="Check what external agency referrals (integrated development approvals) may be required for a development. Returns triggers and required documents for each potential referral authority.",
            inputSchema={
                "type": "object",
                "properties": {
                    "development_characteristics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of development characteristics, e.g., ['bushfire_prone', 'near_waterway', 'heritage_item', 'significant_traffic', 'vegetation_clearing', 'industrial']"
                    }
                },
                "required": ["development_characteristics"]
            }
        ),
        Tool(
            name="get_see_template",
            description="Get Statement of Environmental Effects (SEE) section template with prompts for what to include. Returns structured guidance for writing each section of an SEE.",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "SEE section: 'site_description', 'proposal_description', 'planning_framework', 'environmental_impacts', 'mitigation_measures', 'section_4_15_matters', or 'all'"
                    }
                },
                "required": ["section"]
            }
        ),
        Tool(
            name="get_residential_standards",
            description="Get residential development standards from DCP Chapter 1, including site coverage, private open space, landscaping, and car parking design requirements.",
            inputSchema={
                "type": "object",
                "properties": {
                    "standard_type": {
                        "type": "string",
                        "description": "Type of standard: 'site_coverage', 'private_open_space', 'landscaping', 'car_parking_design', 'building_height', or 'all'. Defaults to 'all'."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="list_definitions",
            description="List all available land-use definitions in the system. Use this to see what terms have definitions available before calling get_definition.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="generate_see_draft",
            description="Generate a draft Statement of Environmental Effects (SEE) document based on proposal details. Automatically pulls in zone information, parking requirements, flood planning, and other relevant data to create a structured SEE ready for review and refinement.",
            inputSchema={
                "type": "object",
                "properties": {
                    "property_address": {
                        "type": "string",
                        "description": "Street address of the property"
                    },
                    "lot_dp": {
                        "type": "string",
                        "description": "Lot and DP number (e.g., 'Lot 1 DP 123456')"
                    },
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code (e.g., 'E2', 'R1', 'MU1')"
                    },
                    "site_area_sqm": {
                        "type": "number",
                        "description": "Site area in square metres"
                    },
                    "existing_use": {
                        "type": "string",
                        "description": "Current/existing use of the property"
                    },
                    "proposed_use": {
                        "type": "string",
                        "description": "Proposed land use (e.g., 'restaurant or cafe', 'shop', 'dwelling house')"
                    },
                    "development_type": {
                        "type": "string",
                        "description": "Type of development: 'new_building', 'alteration', 'change_of_use', 'fitout'"
                    },
                    "floor_area_sqm": {
                        "type": "number",
                        "description": "Gross floor area of the proposal in square metres"
                    },
                    "building_description": {
                        "type": "string",
                        "description": "Description of proposed works (e.g., 'Internal fitout for cafe with kitchen, counter, and 8-seat dining area')"
                    },
                    "hours_of_operation": {
                        "type": "string",
                        "description": "Proposed hours of operation (e.g., '7am-4pm Monday to Saturday')"
                    },
                    "num_employees": {
                        "type": "integer",
                        "description": "Number of employees"
                    },
                    "num_customers": {
                        "type": "integer",
                        "description": "Maximum number of customers/patrons at any time"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "Estimated cost of development works in dollars"
                    },
                    "is_flood_affected": {
                        "type": "boolean",
                        "description": "Is the property within the flood planning area?"
                    },
                    "is_heritage": {
                        "type": "boolean",
                        "description": "Is the property a heritage item or in a heritage conservation area?"
                    },
                    "existing_parking_spaces": {
                        "type": "integer",
                        "description": "Number of existing on-site parking spaces (0 if none)"
                    },
                    "applicant_name": {
                        "type": "string",
                        "description": "Name of the applicant"
                    }
                },
                "required": ["property_address", "zone_code", "proposed_use", "development_type", "floor_area_sqm"]
            }
        ),
        Tool(
            name="preview_see_form",
            description="Preview exactly what will be written into the official Lismore SEE PDF, including every tick. Shows the questions still unanswered and any issue that blocks the form being generated. Review this before calling fill_see_pdf.",
            inputSchema={
                "type": "object",
                "properties": {
                    "applicant_name": {
                        "type": "string",
                        "description": "Full name of the applicant"
                    },
                    "minor_development_type": {
                        "type": "string",
                        "enum": ["dwelling_single_storey", "residential_addition_single_storey", "ancillary_residential_structure", "strata_subdivision"],
                        "description": "REQUIRED. Which of the four development types this Council template covers. Anything outside this list (commercial work, change of use, multi-storey) cannot use this form - build a purpose-written SEE with generate_see_draft instead."
                    },
                    "property_address": {
                        "type": "string",
                        "description": "Full street address, e.g. '45 Keen Street, Lismore NSW 2480'. Prefer the separate unit/street_number/street/suburb fields where the address has a shop or unit number."
                    },
                    "unit": {
                        "type": "string",
                        "description": "Tenancy identifier if any, e.g. 'Shop 3', 'Unit 2'"
                    },
                    "street_number": {
                        "type": "string",
                        "description": "Street number only, e.g. '88' or '5-7'"
                    },
                    "street": {
                        "type": "string",
                        "description": "Street name only, e.g. 'Keen Street'"
                    },
                    "suburb": {
                        "type": "string",
                        "description": "Suburb only, without NSW or postcode"
                    },
                    "building_name": {
                        "type": "string",
                        "description": "Building name, if known"
                    },
                    "lot_dp": {
                        "type": "string",
                        "description": "Land identifier as text, e.g. 'Lot 12 DP 758651' or 'SP 12345'. Prefer lot/plan_type/plan_number. The form is not generated without a plan number."
                    },
                    "lot": {
                        "type": "string",
                        "description": "Lot number on its own"
                    },
                    "plan_type": {
                        "type": "string",
                        "enum": ["DP", "SP", "CP"],
                        "description": "Deposited, Strata or Community plan"
                    },
                    "plan_number": {
                        "type": "string",
                        "description": "Plan number on its own, e.g. '758651'"
                    },
                    "section": {
                        "type": "string",
                        "description": "Section number, if the land has one"
                    },
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code under Lismore LEP 2012, e.g. 'R1', 'E2'. Employment zones replaced the B-series codes in 2023."
                    },
                    "proposed_use": {
                        "type": "string",
                        "description": "Proposed land use, e.g. 'dwelling house', 'shed'"
                    },
                    "development_type": {
                        "type": "string",
                        "description": "Type: 'new_building', 'alteration', 'change_of_use', 'fitout'"
                    },
                    "floor_area_sqm": {
                        "type": "number",
                        "description": "Floor area in square metres"
                    },
                    "building_description": {
                        "type": "string",
                        "description": "Description of the proposed works, in the applicant's own words. Used verbatim as the description of development."
                    },
                    "site_description": {
                        "type": "string",
                        "description": "Physical description of the site: shape, slope, vegetation, waterways"
                    },
                    "surrounding_context": {
                        "type": "string",
                        "description": "Land uses and development on surrounding land"
                    },
                    "existing_use": {
                        "type": "string",
                        "description": "Present and previous use of the site"
                    },
                    "hours_of_operation": {
                        "type": "string",
                        "description": "Proposed operating hours, where the use has any"
                    },
                    "num_employees": {
                        "type": "integer",
                        "description": "Number of employees"
                    },
                    "num_customers": {
                        "type": "integer",
                        "description": "Maximum customers at any time"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "Estimated cost of works in dollars"
                    },
                    "is_flood_affected": {
                        "type": "boolean",
                        "description": "Is the site flood prone? Omit if unknown - the tick is then left blank rather than guessed."
                    },
                    "is_bushfire_prone": {
                        "type": "boolean",
                        "description": "Is the site bushfire prone? Omit if unknown."
                    },
                    "is_heritage": {
                        "type": "boolean",
                        "description": "Is the site a heritage item under LEP 2012 Schedule 5? Omit if unknown."
                    },
                    "in_heritage_conservation_area": {
                        "type": "boolean",
                        "description": "Is the site within a heritage conservation area? Omit if unknown."
                    },
                    "internal_works_only": {
                        "type": "boolean",
                        "description": "True if the works are wholly internal. Lets the excavation and vegetation questions be answered from that fact."
                    },
                    "parking_spaces_provided": {
                        "type": "integer",
                        "description": "Off-street parking spaces provided on site. Compared against the DCP Chapter 7 rate so any shortfall is stated."
                    },
                    "stormwater_to_council_system": {
                        "type": "boolean",
                        "description": "True if stormwater goes to the Council drainage system; false if disposed of another way (describe it in comments.stormwater_details)."
                    },
                    "answers": {
                        "type": "object",
                        "description": "The applicant's answers to the form's Yes/No questions, as {question_key: true|false}. Any question left out stays blank on the form and is returned in unanswered_questions - these are declarations signed as true, so they are never filled in on the applicant's behalf. Keys: zone_objectives, dcp_accordance, visually_prominent, inconsistent_streetscape, out_of_character, inconsistent_land_use, setback_variation, privacy_issues, overshadowing, acoustic_issues, views_impact, legal_access, increase_traffic, additional_access, parking_addressed, utilities_available, air_pollution, water_pollution, noise_impacts, excavation, erosion, contamination, sustainable, heritage_impact, aboriginal, remove_vegetation, threatened_species, effluent, trade_waste, hazardous_waste, rainwater_tanks, overland_risks, economic_social, crime_prevention, permissible."
                    },
                    "comments": {
                        "type": "object",
                        "description": "Free text for the form's comment boxes, as {field: text}. Keys: hazards_comments, constraints, surrounding_land_use, planning_comments, context_comment, privacy_comments, access_comments, environmental_comments, flora_comments, waste_comments, social_comments, other_matters, stormwater_details, traffic_amount."
                    }
                },
                "required": ["applicant_name", "property_address", "lot_dp", "zone_code", "proposed_use", "development_type", "floor_area_sqm", "minor_development_type"]
            }
        ),
        Tool(
            name="fill_see_pdf",
            description="Fill the official Lismore SEE PDF form and save it. Refuses proposals outside the template's 'Minor Development Only' scope, and refuses to write a blank land identifier. Questions the applicant has not answered are left blank and reported rather than guessed. Run preview_see_form first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "applicant_name": {
                        "type": "string",
                        "description": "Full name of the applicant"
                    },
                    "minor_development_type": {
                        "type": "string",
                        "enum": ["dwelling_single_storey", "residential_addition_single_storey", "ancillary_residential_structure", "strata_subdivision"],
                        "description": "REQUIRED. Which of the four development types this Council template covers. Anything outside this list (commercial work, change of use, multi-storey) cannot use this form - build a purpose-written SEE with generate_see_draft instead."
                    },
                    "property_address": {
                        "type": "string",
                        "description": "Full street address, e.g. '45 Keen Street, Lismore NSW 2480'. Prefer the separate unit/street_number/street/suburb fields where the address has a shop or unit number."
                    },
                    "unit": {
                        "type": "string",
                        "description": "Tenancy identifier if any, e.g. 'Shop 3', 'Unit 2'"
                    },
                    "street_number": {
                        "type": "string",
                        "description": "Street number only, e.g. '88' or '5-7'"
                    },
                    "street": {
                        "type": "string",
                        "description": "Street name only, e.g. 'Keen Street'"
                    },
                    "suburb": {
                        "type": "string",
                        "description": "Suburb only, without NSW or postcode"
                    },
                    "building_name": {
                        "type": "string",
                        "description": "Building name, if known"
                    },
                    "lot_dp": {
                        "type": "string",
                        "description": "Land identifier as text, e.g. 'Lot 12 DP 758651' or 'SP 12345'. Prefer lot/plan_type/plan_number. The form is not generated without a plan number."
                    },
                    "lot": {
                        "type": "string",
                        "description": "Lot number on its own"
                    },
                    "plan_type": {
                        "type": "string",
                        "enum": ["DP", "SP", "CP"],
                        "description": "Deposited, Strata or Community plan"
                    },
                    "plan_number": {
                        "type": "string",
                        "description": "Plan number on its own, e.g. '758651'"
                    },
                    "section": {
                        "type": "string",
                        "description": "Section number, if the land has one"
                    },
                    "zone_code": {
                        "type": "string",
                        "description": "Zone code under Lismore LEP 2012, e.g. 'R1', 'E2'. Employment zones replaced the B-series codes in 2023."
                    },
                    "proposed_use": {
                        "type": "string",
                        "description": "Proposed land use, e.g. 'dwelling house', 'shed'"
                    },
                    "development_type": {
                        "type": "string",
                        "description": "Type: 'new_building', 'alteration', 'change_of_use', 'fitout'"
                    },
                    "floor_area_sqm": {
                        "type": "number",
                        "description": "Floor area in square metres"
                    },
                    "building_description": {
                        "type": "string",
                        "description": "Description of the proposed works, in the applicant's own words. Used verbatim as the description of development."
                    },
                    "site_description": {
                        "type": "string",
                        "description": "Physical description of the site: shape, slope, vegetation, waterways"
                    },
                    "surrounding_context": {
                        "type": "string",
                        "description": "Land uses and development on surrounding land"
                    },
                    "existing_use": {
                        "type": "string",
                        "description": "Present and previous use of the site"
                    },
                    "hours_of_operation": {
                        "type": "string",
                        "description": "Proposed operating hours, where the use has any"
                    },
                    "num_employees": {
                        "type": "integer",
                        "description": "Number of employees"
                    },
                    "num_customers": {
                        "type": "integer",
                        "description": "Maximum customers at any time"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "Estimated cost of works in dollars"
                    },
                    "is_flood_affected": {
                        "type": "boolean",
                        "description": "Is the site flood prone? Omit if unknown - the tick is then left blank rather than guessed."
                    },
                    "is_bushfire_prone": {
                        "type": "boolean",
                        "description": "Is the site bushfire prone? Omit if unknown."
                    },
                    "is_heritage": {
                        "type": "boolean",
                        "description": "Is the site a heritage item under LEP 2012 Schedule 5? Omit if unknown."
                    },
                    "in_heritage_conservation_area": {
                        "type": "boolean",
                        "description": "Is the site within a heritage conservation area? Omit if unknown."
                    },
                    "internal_works_only": {
                        "type": "boolean",
                        "description": "True if the works are wholly internal. Lets the excavation and vegetation questions be answered from that fact."
                    },
                    "parking_spaces_provided": {
                        "type": "integer",
                        "description": "Off-street parking spaces provided on site. Compared against the DCP Chapter 7 rate so any shortfall is stated."
                    },
                    "stormwater_to_council_system": {
                        "type": "boolean",
                        "description": "True if stormwater goes to the Council drainage system; false if disposed of another way (describe it in comments.stormwater_details)."
                    },
                    "answers": {
                        "type": "object",
                        "description": "The applicant's answers to the form's Yes/No questions, as {question_key: true|false}. Any question left out stays blank on the form and is returned in unanswered_questions - these are declarations signed as true, so they are never filled in on the applicant's behalf. Keys: zone_objectives, dcp_accordance, visually_prominent, inconsistent_streetscape, out_of_character, inconsistent_land_use, setback_variation, privacy_issues, overshadowing, acoustic_issues, views_impact, legal_access, increase_traffic, additional_access, parking_addressed, utilities_available, air_pollution, water_pollution, noise_impacts, excavation, erosion, contamination, sustainable, heritage_impact, aboriginal, remove_vegetation, threatened_species, effluent, trade_waste, hazardous_waste, rainwater_tanks, overland_risks, economic_social, crime_prevention, permissible."
                    },
                    "comments": {
                        "type": "object",
                        "description": "Free text for the form's comment boxes, as {field: text}. Keys: hazards_comments, constraints, surrounding_land_use, planning_comments, context_comment, privacy_comments, access_comments, environmental_comments, flora_comments, waste_comments, social_comments, other_matters, stormwater_details, traffic_amount."
                    },
                    "output_filename": {
                        "type": "string",
                        "description": "Output filename only — any path component is stripped. When running locally over stdio, saved to documents/output/; when served publicly over HTTP, returned inline as base64 and never written to disk. Default: 'SEE_filled.pdf'"
                    }
                },
                "required": ["applicant_name", "property_address", "lot_dp", "zone_code", "proposed_use", "development_type", "floor_area_sqm", "minor_development_type"]
            }
        ),
]

TOOL_SCHEMAS = {tool.name: tool.inputSchema for tool in TOOLS}


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return TOOLS


def validate_arguments(name: str, arguments: dict) -> dict | None:
    """Check arguments against the tool's own schema. Returns an error payload, or None if valid.

    Handlers read arguments with .get() and sensible-looking defaults, which means a
    misspelt or omitted argument used to produce a confident wrong answer rather than
    an error — an empty land_use reported 'permitted without consent'. Refuse instead.
    """
    schema = TOOL_SCHEMAS.get(name)
    if schema is None:
        return {"error": f"Unknown tool: {name}", "available_tools": sorted(TOOL_SCHEMAS)}

    properties = schema.get("properties", {})
    unknown = sorted(k for k in arguments if k not in properties)
    if unknown:
        return {
            "error": "Unrecognised argument(s): " + ", ".join(unknown),
            "accepted_arguments": sorted(properties),
            "note": "Unrecognised arguments are not guessed at. Re-send the call using the names above.",
        }

    missing = [
        key for key in schema.get("required", [])
        if arguments.get(key) is None
        or (isinstance(arguments[key], str) and not arguments[key].strip())
    ]
    if missing:
        return {
            "error": "Missing or empty required argument(s): " + ", ".join(missing),
            "required_arguments": schema.get("required", []),
        }

    return None


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    argument_error = validate_arguments(name, arguments)
    if argument_error:
        return [TextContent(type="text", text=json.dumps(argument_error, indent=2))]

    if name == "get_parking_rates":
        dev_type = arguments.get("development_type", "").lower().replace(" ", "_")
        if dev_type in PARKING_RATES:
            result = PARKING_RATES[dev_type]
            response = {
                "development_type": dev_type,
                "parking_spaces": result["spaces"],
                "rate_description": result["rate"],
                "source": "Lismore DCP Chapter 7 - Off-Street Carparking",
                "note": "Rates may vary by location. Check specific DCP provisions for exact requirements."
            }

            # Turn the rate into a number where the inputs allow it, so a shortfall
            # gets stated rather than left as an exercise for the reader.
            estimate = estimate_parking_requirement(
                result["spaces"],
                arguments.get("floor_area_sqm", 0) or 0,
                arguments.get("num_employees", 0) or 0,
            )
            if estimate:
                provided = arguments.get("spaces_provided")
                estimate["spaces_provided"] = provided
                if provided is not None:
                    shortfall = max(0, estimate["spaces_required"] - provided)
                    estimate["shortfall"] = shortfall
                    estimate["advice"] = (
                        f"A shortfall of {shortfall} space(s) must be justified in the SEE — "
                        "on-street or public parking nearby is an argument for a variation, not evidence of compliance."
                        if shortfall else "The rate is met by the spaces provided."
                    )
                response["calculation"] = estimate

            return [TextContent(type="text", text=json.dumps(response, indent=2))]
        else:
            # Try partial match
            matches = [k for k in PARKING_RATES.keys() if dev_type in k or k in dev_type]
            if matches:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Exact match not found for '{dev_type}'",
                        "similar_types": matches,
                        "suggestion": "Try one of the similar types listed above"
                    }, indent=2)
                )]
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Development type '{dev_type}' not found",
                    "available_types": list(PARKING_RATES.keys())
                }, indent=2)
            )]

    elif name == "get_zone_info":
        zone_code = arguments.get("zone_code", "").upper()
        if zone_code in ZONES:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "zone_code": zone_code,
                    **ZONES[zone_code],
                    "source": "Lismore LEP 2012"
                }, indent=2)
            )]
        else:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Zone '{zone_code}' not found",
                    "available_zones": list(ZONES.keys())
                }, indent=2)
            )]

    elif name == "calculate_da_fees":
        cost = arguments.get("development_cost", 0)
        result = calculate_da_fee(float(cost))
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    elif name == "get_flood_requirements":
        dev_type = arguments.get("development_type", "").lower()

        response = {
            "flood_planning_level": FLOOD_PLANNING["flood_planning_level"],
            "proposed_fpl": FLOOD_PLANNING["proposed_fpl"],
            "advice": FLOOD_PLANNING["advice"]
        }

        if "residential" in dev_type:
            response["requirement"] = FLOOD_PLANNING["residential_requirement"]
        elif "commercial" in dev_type or "industrial" in dev_type:
            response["requirement"] = FLOOD_PLANNING["commercial_requirement"]
        elif "cbd" in dev_type:
            response["cbd_exemption"] = FLOOD_PLANNING["cbd_exemption"]
        else:
            response["residential_requirement"] = FLOOD_PLANNING["residential_requirement"]
            response["commercial_requirement"] = FLOOD_PLANNING["commercial_requirement"]
            response["cbd_exemption"] = FLOOD_PLANNING["cbd_exemption"]

        return [TextContent(
            type="text",
            text=json.dumps(response, indent=2)
        )]

    elif name == "get_contact_info":
        return [TextContent(
            type="text",
            text=json.dumps(CONTACT_INFO, indent=2)
        )]

    elif name == "search_dcp":
        query = arguments.get("query", "")
        chapter = arguments.get("chapter", "")

        if not DOCS_DIR.exists():
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Documents directory not found"})
            )]

        # Search across all planning document categories, not just dcp/ — a query about
        # e.g. flood clauses, exempt development or heritage schedules may only be
        # answerable from lep/, exempt-development/ or forms/.
        all_results = []
        for path in searchable_documents(chapter):
            all_results.extend(search_document(path, query))

        if not all_results:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "query": query,
                    "results": [],
                    "message": "No matches found. Try different search terms."
                }, indent=2)
            )]

        # Re-rank globally across every document searched, then drop the
        # internal score before returning it.
        all_results.sort(key=lambda r: r.get("score", 0), reverse=True)
        top_results = all_results[:10]
        for r in top_results:
            r.pop("score", None)

        return [TextContent(
            type="text",
            text=json.dumps({
                "query": query,
                "results": top_results
            }, indent=2)
        )]

    elif name == "read_dcp_section":
        chapter = arguments.get("chapter", "")
        start_page = arguments.get("start_page", 1)
        end_page = arguments.get("end_page")

        # Resolve across every category, not just dcp/ — search_dcp can return a hit in
        # lep/ or exempt-development/, and there was previously no way to open it.
        doc_path = find_document(chapter)

        if not doc_path:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Document '{chapter}' not found",
                    "available": [str(p.relative_to(DOCS_DIR)) for p in searchable_documents()]
                }, indent=2)
            )]

        text = extract_document_section(doc_path, start_page, end_page)
        return [TextContent(
            type="text",
            text=text
        )]

    elif name == "list_documents":
        docs = list_available_documents()
        return [TextContent(
            type="text",
            text=json.dumps({"documents": docs}, indent=2)
        )]

    elif name == "get_da_checklist":
        dev_type = arguments.get("development_type", "").lower()
        # Keywords the branches below actually test for, surfaced so a rejected
        # call can name them instead of leaving the caller to guess.
        DA_CHECKLIST_TYPES = {
            "dwelling", "residential", "commercial", "subdivision", "change_of_use",
        }

        base_documents = [
            "Development Application form (via NSW Planning Portal)",
            "Owner's consent (if not the owner)",
            "Statement of Environmental Effects (SEE)",
            "Site plan (1:100 or 1:200 scale)",
            "Architectural plans (1:100 or 1:200 scale)",
            "Cost of Development Works estimate"
        ]

        additional = []

        if "dwelling" in dev_type or "residential" in dev_type:
            additional = [
                "BASIX Certificate",
                "Shadow diagrams (if 2+ storeys)",
                "Privacy assessment",
                "Landscape plan"
            ]
        elif "commercial" in dev_type:
            additional = [
                "Traffic impact assessment (if significant traffic generation)",
                "Acoustic report (if noise-generating use)",
                "Waste management plan",
                "BCA compliance report",
                "Fire safety schedule"
            ]
        elif "subdivision" in dev_type:
            additional = [
                "Survey plan",
                "Subdivision layout plan",
                "Services layout plan",
                "Stormwater management plan",
                "Road layout and pavement design"
            ]
        elif "change_of_use" in dev_type:
            additional = [
                "BCA compliance assessment",
                "Fire safety upgrade report (if required)",
                "Parking assessment"
            ]

        # Nothing matched, so there is no type-specific advice to give. Returning the
        # generic list anyway made 'nuclear reactor' and 'spaceship' look like
        # recognised development types with a considered answer behind them.
        if not additional:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"No checklist available for development type '{dev_type}'.",
                    "recognised_types": sorted(DA_CHECKLIST_TYPES),
                    "note": (
                        "Only the types above have type-specific document requirements. "
                        "Every DA needs the standard documents listed under "
                        "'documents_required_for_every_da' regardless of type."
                    ),
                    "documents_required_for_every_da": base_documents,
                }, indent=2)
            )]

        conditional = [
            {"condition": "If flood-affected land", "document": "Flood Risk Assessment"},
            {"condition": "If heritage item or near heritage", "document": "Heritage Impact Statement"},
            {"condition": "If vegetation removal required", "document": "Vegetation Management Plan"},
            {"condition": "If contamination suspected", "document": "Contamination Assessment"},
            {"condition": "If on-site sewage", "document": "On-site Sewage Management Report"},
            {"condition": "If Clause 4.6 variation needed", "document": "Clause 4.6 Variation Request"}
        ]

        return [TextContent(
            type="text",
            text=json.dumps({
                "development_type": dev_type,
                "required_documents": base_documents,
                "additional_for_type": additional,
                "conditional_documents": conditional,
                "lodgement": "All applications must be lodged via NSW Planning Portal: https://www.planningportal.nsw.gov.au/onlineDA"
            }, indent=2)
        )]

    elif name == "list_parking_types":
        return [TextContent(
            type="text",
            text=json.dumps({
                "available_development_types": list(PARKING_RATES.keys()),
                "categories": {
                    "residential": ["dwelling_house", "dual_occupancy", "multi_dwelling_housing", "residential_flat_building", "secondary_dwelling", "boarding_house"],
                    "commercial": ["shop", "retail", "office", "business_premises", "restaurant", "cafe", "take_away", "medical_centre", "hotel", "motel"],
                    "industrial": ["industry", "warehouse", "bulky_goods"],
                    "other": ["childcare_centre", "place_of_worship", "gym"]
                }
            }, indent=2)
        )]

    elif name == "list_zones":
        # Filter out legacy zones that just redirect
        active_zones = {code: info["name"] for code, info in ZONES.items() if "redirect_to" not in info}
        return [TextContent(
            type="text",
            text=json.dumps({
                "zones": active_zones,
                "categories": {
                    "residential": ["R1", "R2", "R3", "R5"],
                    "employment": ["E1", "E2", "E3", "E4"],
                    "mixed_use": ["MU1"],
                    "rural": ["RU5"],
                    "special_purpose": ["SP2"],
                    "recreation": ["RE1", "RE2"],
                    "conservation": ["C1", "C2", "C3"],
                    "waterways": ["W1"],
                    "legacy_codes": ["B1", "B2", "B3", "B4", "IN1", "IN2"]
                },
                "note": "Zone codes changed in April 2022 under Standard Instrument amendments. Legacy B/IN codes redirect to new E/MU zones."
            }, indent=2)
        )]

    elif name == "get_definition":
        raw_term = arguments.get("term", "")
        key = raw_term.strip().lower().replace(" ", "_").replace("-", "_")

        if key in LAND_USE_DEFINITIONS:
            entry = LAND_USE_DEFINITIONS[key]
            return [TextContent(
                type="text",
                text=json.dumps({
                    **entry,
                    "source": "Standard Instrument (Local Environmental Plans) Order 2006 — Dictionary, as carried into Lismore LEP 2012",
                    "caveat": "Paraphrased for readability. Definitions can be amended — verify against the current Lismore LEP 2012 Dictionary before relying on this for a formal submission."
                }, indent=2)
            )]

        # Try substring match against term keys/labels for near-misses
        matches = [
            v["term"] for k, v in LAND_USE_DEFINITIONS.items()
            if key in k or any(w in k for w in key.split("_") if len(w) >= 3)
        ]
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": f"No definition found for '{raw_term}'",
                "similar_terms": matches,
                "available_terms": [v["term"] for v in LAND_USE_DEFINITIONS.values()]
            }, indent=2)
        )]

    elif name == "check_permissibility":
        land_use = arguments["land_use"].strip()
        zone_code = arguments["zone_code"].upper().strip()

        redirect_note = None
        if zone_code in ZONES and "redirect_to" in ZONES[zone_code]:
            new_zone = ZONES[zone_code]["redirect_to"]
            redirect_note = f"Zone {zone_code} has been replaced by {new_zone}. Checked against {new_zone}."
            zone_code = new_zone

        if zone_code not in ZONES:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Zone \'{zone_code}\' not found",
                    "available_zones": [k for k in ZONES if "redirect_to" not in ZONES[k]]
                }, indent=2)
            )]

        zone = ZONES[zone_code]
        classification = classify_land_use(land_use, zone, zone_code)

        # Map the classification onto the verdicts this tool has always returned.
        verdicts = {
            ("exact", True): "permitted",
            ("hierarchy", True): "permitted_with_consent",
            ("exact", False): "prohibited",
            ("hierarchy", False): "prohibited",
        }
        permissibility = "unknown"
        if classification["match_type"] == "catchall":
            permissibility = "likely_permitted_with_consent" if classification["permissible"] is None else "likely_prohibited"
        elif classification["match_type"] == "approximate":
            permissibility = "likely_prohibited" if classification["category"] == "prohibited" else "uncertain"
        elif classification["matched_use"]:
            in_without = any(
                canonical_use(u) == canonical_use(classification["matched_use"])
                for u in zone.get("permitted_without_consent", [])
            )
            if classification["permissible"] is False:
                permissibility = "prohibited"
            else:
                permissibility = "permitted_without_consent" if in_without else "permitted_with_consent"
        elif classification["match_type"] == "none":
            permissibility = "not_found"

        result = {
            "land_use": land_use,
            "zone_code": zone_code,
            "zone_name": zone["name"],
            "permissibility": permissibility,
            "detail": classification["statement"],
            "matched_use": classification["matched_use"],
            "match_type": classification["match_type"],
        }
        if redirect_note:
            result["redirect_note"] = redirect_note
        if permissibility == "permitted_with_consent":
            result["next_steps"] = "A Development Application is required for this use."
        elif permissibility == "prohibited":
            result["advice"] = "This use cannot be approved in this zone. Consider an alternative zone or use."
        elif permissibility in ("uncertain", "not_found", "likely_permitted_with_consent", "likely_prohibited"):
            result["advice"] = "Confirm the exact land use term with the Council Duty Planner before relying on this."
            all_uses = zone.get("permitted_without_consent", []) + zone.get("permitted_with_consent", [])
            words = [w for w in canonical_use(land_use).split() if len(w) > 3]
            similar = [u for u in all_uses if any(w in canonical_use(u) for w in words)]
            if similar:
                result["similar_uses"] = similar[:5]

        # This tool reads the LEP land use table and nothing else. A State
        # Environmental Planning Policy can permit a use the table omits, and
        # prevails over the LEP where they conflict — most commonly for secondary
        # dwellings ("granny flats"), which are absent from several Lismore
        # residential tables but are generally permissible with consent under the
        # Housing SEPP. Without this note, a catch-all miss reads as a settled "no".
        if permissibility in ("likely_prohibited", "prohibited", "not_found"):
            result["scope_of_this_answer"] = (
                "Based on the Lismore LEP 2012 land use table only. State Environmental "
                "Planning Policies (Housing, Exempt and Complying Development Codes, "
                "Transport and Infrastructure, Primary Production) can independently permit "
                "a use that the LEP table does not list, and prevail over the LEP where they "
                "conflict. A use shown here as prohibited may still have a SEPP pathway — "
                "secondary dwellings are the common example. Check with the Duty Planner "
                "before treating this as a refusal."
            )

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_setback_requirements":
        setback_type = arguments.get("setback_type", "all").lower()
        dev_type = arguments.get("development_type", "").lower()

        setbacks = RESIDENTIAL_STANDARDS["setbacks"]

        if setback_type == "all":
            result = {
                "setbacks": setbacks,
                "source": "Lismore DCP Chapter 1 - Residential Development",
                "note": "These are general guidelines. Site-specific assessment required. Check DCP Chapter 1 for full provisions."
            }
        elif setback_type in setbacks:
            result = {
                "setback_type": setback_type,
                "requirements": setbacks[setback_type],
                "source": "Lismore DCP Chapter 1 - Residential Development"
            }
            if dev_type and dev_type in setbacks[setback_type]:
                result["specific_requirement"] = setbacks[setback_type][dev_type]
        else:
            result = {
                "error": f"Setback type '{setback_type}' not found",
                "available_types": ["front", "side", "rear", "all"]
            }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "check_referrals":
        characteristics = arguments.get("development_characteristics", [])

        # Map characteristics to referral authorities
        char_to_referral = {
            "bushfire": "rural_fire_service",
            "bushfire_prone": "rural_fire_service",
            "fire": "rural_fire_service",
            "heritage": "heritage_council",
            "state_heritage": "heritage_council",
            "industrial": "epa",
            "waste": "epa",
            "extractive": "epa",
            "traffic": "transport_nsw",
            "classified_road": "transport_nsw",
            "waterway": "natural_resources_access_regulator",
            "near_waterway": "natural_resources_access_regulator",
            "riparian": "natural_resources_access_regulator",
            "vegetation": "biodiversity_conservation",
            "vegetation_clearing": "biodiversity_conservation",
            "threatened_species": "biodiversity_conservation",
            "flood": "council_flood_assessment",
            "flooding": "council_flood_assessment",
            "flood_prone": "council_flood_assessment",
            "inundation": "council_flood_assessment",
        }

        triggered_referrals = {}
        unrecognised = []
        for char in characteristics:
            char_lower = char.lower().replace(" ", "_")
            matched = False
            for key, referral in char_to_referral.items():
                if key in char_lower:
                    matched = True
                    if referral not in triggered_referrals:
                        triggered_referrals[referral] = REFERRAL_REQUIREMENTS.get(referral, {})
            if not matched:
                unrecognised.append(char)

        response = {
            "triggered_referrals": triggered_referrals,
            "characteristics_checked": characteristics,
            "warning": "This is indicative only. Council will confirm all referral requirements at lodgement."
        }
        if not triggered_referrals:
            response["message"] = "No referrals triggered by the characteristics provided"
        # An unrecognised characteristic used to be dropped in silence, which read as
        # "no referral required" for a site that may well need one.
        if unrecognised:
            response["unrecognised_characteristics"] = unrecognised
            response["available_triggers"] = sorted(char_to_referral)
            response["note"] = (
                "The characteristics above were not recognised and have NOT been assessed. "
                "Re-send them using the available triggers, or treat them as unchecked."
            )

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    elif name == "get_see_template":
        section = arguments.get("section", "all").lower()

        if section == "all":
            result = {
                "see_template": SEE_TEMPLATES,
                "usage": "Use these headings and prompts to structure your Statement of Environmental Effects",
                "source": "Based on EP&A Regulation Schedule 1 and Lismore Council requirements"
            }
        elif section in SEE_TEMPLATES:
            result = {
                "section": section,
                "template": SEE_TEMPLATES[section],
                "source": "Based on EP&A Regulation Schedule 1 and Lismore Council requirements"
            }
        else:
            result = {
                "error": f"Section '{section}' not found",
                "available_sections": list(SEE_TEMPLATES.keys())
            }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "get_residential_standards":
        standard_type = arguments.get("standard_type", "all").lower()

        if standard_type == "all":
            result = {
                "residential_standards": RESIDENTIAL_STANDARDS,
                "source": "Lismore DCP Chapter 1 - Residential Development",
                "note": "These are summary guidelines. Always check the full DCP chapter for detailed provisions."
            }
        elif standard_type in RESIDENTIAL_STANDARDS:
            result = {
                "standard_type": standard_type,
                "requirements": RESIDENTIAL_STANDARDS[standard_type],
                "source": "Lismore DCP Chapter 1 - Residential Development"
            }
        elif standard_type == "setbacks":
            result = {
                "standard_type": "setbacks",
                "requirements": RESIDENTIAL_STANDARDS["setbacks"],
                "source": "Lismore DCP Chapter 1 - Residential Development"
            }
        else:
            result = {
                "error": f"Standard type '{standard_type}' not found",
                "available_types": list(RESIDENTIAL_STANDARDS.keys())
            }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    elif name == "list_definitions":
        definitions_list = [
            {"key": k, "term": v["term"]}
            for k, v in LAND_USE_DEFINITIONS.items()
        ]
        categories = {
            "retail_commercial": ["retail_premises", "food_and_drink_premises", "shop", "restaurant_or_cafe", "take_away_food_and_drink_premises", "business_premises", "commercial_premises", "neighbourhood_shop"],
            "home_based": ["home_business", "home_occupation"],
            "residential": ["dwelling_house", "dual_occupancy", "secondary_dwelling", "multi_dwelling_housing", "residential_flat_building", "attached_dwellings", "shop_top_housing", "boarding_house"],
            "industrial": ["light_industries", "general_industries", "warehouse_or_distribution_centre", "vehicle_repair_station"],
            "community_recreation": ["recreation_facility_indoor", "community_facility", "centre_based_child_care_facility"],
            "accommodation": ["hotel_or_motel_accommodation", "bed_and_breakfast_accommodation"],
        }
        return [TextContent(
            type="text",
            text=json.dumps({
                "available_definitions": definitions_list,
                "categories": categories,
                "total_count": len(definitions_list),
                "usage": "Use get_definition with any term key to get the full definition"
            }, indent=2)
        )]

    elif name == "generate_see_draft":
        # Extract all inputs
        property_address = arguments.get("property_address", "[ADDRESS NOT PROVIDED]")
        lot_dp = arguments.get("lot_dp", "[LOT/DP NOT PROVIDED]")
        zone_code = arguments.get("zone_code", "").upper()
        site_area = arguments.get("site_area_sqm", "[NOT PROVIDED]")
        existing_use = arguments.get("existing_use", "Vacant/Unknown")
        proposed_use = arguments.get("proposed_use", "")
        development_type = arguments.get("development_type", "")
        floor_area = arguments.get("floor_area_sqm", 0)
        building_description = arguments.get("building_description", "[NOT PROVIDED]")
        hours = arguments.get("hours_of_operation", "[NOT PROVIDED]")
        num_employees = arguments.get("num_employees")
        num_customers = arguments.get("num_customers")
        employees_line = num_employees if num_employees is not None else "[NOT PROVIDED]"
        customers_line = num_customers if num_customers is not None else "[NOT PROVIDED]"
        estimated_cost = arguments.get("estimated_cost", 0)
        is_flood = arguments.get("is_flood_affected", False)
        is_heritage = arguments.get("is_heritage", False)
        existing_parking = arguments.get("existing_parking_spaces", 0)
        applicant_name = arguments.get("applicant_name", "[APPLICANT NAME]")

        # Get zone information
        zone_info = ZONES.get(zone_code, {})
        zone_name = zone_info.get("name", "Unknown Zone")
        zone_objectives = zone_info.get("objectives", [])

        # Permissibility from the shared classifier, so this draft and
        # check_permissibility can't disagree about the same land use
        proposed_use_lower = proposed_use.lower().strip()
        classification = classify_land_use(proposed_use, zone_info, zone_code)
        if not classification:
            permissibility, permissibility_detail = "Unknown", ""
        elif classification["permissible"] is True:
            permissibility = "Permitted with consent"
            permissibility_detail = classification["statement"]
        elif classification["permissible"] is False:
            permissibility = "Prohibited"
            permissibility_detail = classification["statement"]
        else:
            permissibility = "To be confirmed"
            permissibility_detail = classification["statement"]

        # Get parking requirements
        parking_key = proposed_use_lower.replace(" ", "_").replace("or_", "")
        if "cafe" in parking_key or "restaurant" in parking_key:
            parking_key = "cafe"
        parking_info = PARKING_RATES.get(parking_key, PARKING_RATES.get("restaurant", {}))
        parking_rate = parking_info.get("rate", "Refer to DCP Chapter 7")

        # Calculate required parking
        if floor_area and "10m" in str(parking_info.get("spaces", "")):
            required_parking = max(1, int(floor_area / 10))
        else:
            required_parking = "[CALCULATE BASED ON DCP]"

        traffic_scale = (
            "minimal" if isinstance(num_customers, (int, float)) and num_customers <= 20
            else "moderate" if isinstance(num_customers, (int, float))
            else "[TO BE ASSESSED]"
        )

        # Get flood info
        flood_info = FLOOD_PLANNING if is_flood else None

        # Calculate DA fee
        fee_info = calculate_da_fee(estimated_cost) if estimated_cost else {"estimated_fee": None}
        # Either may legitimately be unknown at draft stage, so format defensively
        # instead of applying a currency format to a placeholder string.
        cost_line = f"${estimated_cost:,.2f}" if estimated_cost else "[TO BE PROVIDED]"
        fee = fee_info.get("estimated_fee")
        fee_line = f"${fee:,.2f}" if isinstance(fee, (int, float)) else "[CALCULATE ONCE COST OF WORKS IS KNOWN]"

        # Development type description
        dev_type_desc = {
            "new_building": "Construction of a new building",
            "alteration": "Alterations and additions to existing building",
            "change_of_use": "Change of use of existing premises",
            "fitout": "Internal fitout of existing premises"
        }.get(development_type, development_type)

        # Build the SEE document
        see_document = f"""
================================================================================
                    STATEMENT OF ENVIRONMENTAL EFFECTS
================================================================================

Prepared for: {applicant_name}
Property: {property_address}
Date: [INSERT DATE]

================================================================================
1. INTRODUCTION
================================================================================

This Statement of Environmental Effects (SEE) has been prepared in support of a
Development Application for {dev_type_desc.lower()} at {property_address}.

The proposal seeks consent for {proposed_use} within an existing {existing_use.lower()}
premises.

================================================================================
2. SITE DESCRIPTION
================================================================================

2.1 Property Details
--------------------
Address:            {property_address}
Legal Description:  {lot_dp}
Site Area:          {site_area} m²
Zone:               {zone_code} - {zone_name}

2.2 Existing Development
------------------------
The site currently contains {existing_use.lower() if existing_use != "Vacant/Unknown" else "a vacant premises"}.

2.3 Surrounding Context
-----------------------
The site is located within the {zone_name} zone. The surrounding area is
characterised by {"commercial and retail uses typical of the Lismore CBD" if zone_code == "E2" else "uses consistent with the " + zone_name + " zone"}.

[APPLICANT TO ADD: Description of adjoining properties and streetscape]

================================================================================
3. PROPOSED DEVELOPMENT
================================================================================

3.1 Development Overview
------------------------
Development Type:   {dev_type_desc}
Proposed Use:       {proposed_use.title()}
Floor Area:         {floor_area} m²

3.2 Description of Works
------------------------
{building_description}

3.3 Operational Details
-----------------------
Hours of Operation: {hours}
Number of Employees: {employees_line}
Maximum Customers:  {customers_line}

3.4 Estimated Cost
------------------
Cost of Works:      {cost_line}
DA Lodgement Fee:   {fee_line}

================================================================================
4. PLANNING FRAMEWORK ASSESSMENT
================================================================================

4.1 Lismore Local Environmental Plan 2012
------------------------------------------

4.1.1 Zoning
The site is zoned {zone_code} - {zone_name} under Lismore LEP 2012.

Zone Objectives:
{chr(10).join(f"• {obj}" for obj in zone_objectives[:3]) if zone_objectives else "[REFER TO LEP]"}

4.1.2 Permissibility
{permissibility_detail if permissibility_detail else f"The proposed {proposed_use} is {permissibility.lower()} in Zone {zone_code}."}

Development consent is required for this proposal.

4.1.3 Development Standards
Height:             {"Not applicable - no external works" if development_type in ["change_of_use", "fitout"] else "[CHECK HEIGHT MAP]"}
Floor Space Ratio:  {"Not applicable - no increase in GFA" if development_type in ["change_of_use", "fitout"] else "[CHECK FSR MAP]"}

{"4.1.4 Clause 5.21 - Flood Planning" if is_flood else ""}
{"The site is within the flood planning area. The proposal:" if is_flood else ""}
{"• Does not increase the intensity of use significantly" if is_flood else ""}
{"• Maintains existing floor levels" if is_flood else ""}
{"• Does not impede flood flows" if is_flood else ""}
{"[APPLICANT: Confirm floor level relative to Flood Planning Level]" if is_flood else ""}

{"4.1.5 Heritage" if is_heritage else ""}
{"The property is identified as a heritage item / within a heritage conservation area." if is_heritage else ""}
{"The proposal involves internal works only with no impact on heritage significance." if is_heritage else ""}
{"[APPLICANT: Prepare Heritage Impact Statement if external works proposed]" if is_heritage else ""}

4.2 Lismore Development Control Plan
-------------------------------------

4.2.1 Chapter 2 - Commercial Development
The proposal is consistent with the objectives of commercial development in the
Lismore CBD, providing active street frontage and contributing to the vitality
of the commercial centre.

4.2.2 Chapter 7 - Off-Street Car Parking
Parking Requirement: {parking_rate}
Required Spaces:     {required_parking}
Existing Spaces:     {existing_parking}
{"Parking Compliance: The existing parking provision is adequate for the proposed use." if existing_parking >= (required_parking if isinstance(required_parking, int) else 0) else "Parking Shortfall: [APPLICANT TO ADDRESS - consider CBD location, shared parking, contribution in lieu]"}

4.3 State Environmental Planning Policies
-----------------------------------------
The proposal has been assessed against relevant SEPPs. No SEPPs preclude the
granting of consent.

================================================================================
5. ENVIRONMENTAL IMPACT ASSESSMENT
================================================================================

5.1 Visual Impact
-----------------
{"The proposal involves internal works only with no change to the external appearance of the building. There is no adverse visual impact." if development_type in ["change_of_use", "fitout"] else "[ASSESS VISUAL IMPACT OF PROPOSED WORKS]"}

5.2 Traffic and Parking
-----------------------
The proposed {proposed_use.lower()} will generate {traffic_scale} traffic movements
consistent with the commercial nature of the area.

The site is located within the Lismore CBD with access to {"on-street parking, " if zone_code == "E2" else ""}public
transport, and pedestrian connections.

5.3 Noise and Amenity
---------------------
The proposed hours of operation ({hours}) are consistent with
the commercial character of the area. {"No amplified music or entertainment is proposed." if "cafe" in proposed_use.lower() or "restaurant" in proposed_use.lower() else ""}

Noise impacts will be limited to {"normal cafe/restaurant operations including customer conversation and kitchen equipment" if "cafe" in proposed_use.lower() or "restaurant" in proposed_use.lower() else "normal business operations"}.

5.4 Waste Management
--------------------
{"Food waste and general waste will be stored in appropriate bins within the premises and collected by a licensed waste contractor." if "cafe" in proposed_use.lower() or "restaurant" in proposed_use.lower() or "food" in proposed_use.lower() else "Waste will be managed in accordance with Council requirements."}

5.5 Stormwater and Drainage
---------------------------
{"No changes to existing stormwater or drainage arrangements." if development_type in ["change_of_use", "fitout"] else "[APPLICANT TO ADDRESS STORMWATER MANAGEMENT]"}

================================================================================
6. SECTION 4.15 MATTERS FOR CONSIDERATION
================================================================================

(a)(i) Environmental Planning Instruments
The proposal is consistent with Lismore LEP 2012. The use is permissible
with consent in the {zone_code} zone.

(a)(ii) Draft Environmental Planning Instruments
No draft EPIs affect this application.

(a)(iii) Development Control Plans
The proposal is consistent with the relevant provisions of Lismore DCP.

(a)(iiia) Planning Agreements
Not applicable.

(a)(iv) Regulations
The proposal complies with the EP&A Regulation 2021.

(b) Likely Impacts
The proposal will have positive economic impacts through job creation and
service provision. Environmental impacts are minimal given the {"internal nature of the works" if development_type in ["change_of_use", "fitout"] else "scale and nature of the proposal"}.

(c) Suitability of the Site
The site is suitable for the proposed development, being located within a
{"commercial centre with supporting infrastructure" if zone_code == "E2" else "zone that permits the proposed use"}.

(d) Submissions
To be addressed following public exhibition (if required).

(e) Public Interest
The proposal is in the public interest as it:
• Provides employment opportunities
• Contributes to the {"vitality of the CBD" if zone_code == "E2" else "local economy"}
• Is consistent with the objectives of the zone
• Has minimal environmental impact

================================================================================
7. CONCLUSION
================================================================================

This Statement of Environmental Effects demonstrates that the proposed
{proposed_use.lower()} at {property_address} is appropriate and warrants
the granting of development consent.

The proposal:
• Is permissible in the {zone_code} - {zone_name} zone
• Complies with the relevant provisions of Lismore LEP 2012
• Is consistent with Lismore Development Control Plan
• Will have minimal environmental impact
• Is in the public interest

It is requested that Council approve this Development Application.

================================================================================
                              END OF DOCUMENT
================================================================================

NOTES FOR APPLICANT:
--------------------
1. Replace all [BRACKETED TEXT] with actual information
2. Attach required plans and supporting documents
3. Verify all information before lodgement
4. Consult Duty Planner if uncertain about any requirements
   - Available: Tuesdays and Thursdays, 8:30am-10:30am
   - Location: Corporate Centre, Goonellabah
   - Phone: (02) 6625 0500

Generated by: Lismore DA MCP Server
"""

        return [TextContent(
            type="text",
            text=see_document
        )]

    elif name in ("preview_see_form", "fill_see_pdf"):
        shared_keys = (
            "applicant_name", "property_address", "lot_dp", "zone_code", "proposed_use",
            "development_type", "floor_area_sqm", "minor_development_type",
            "building_description", "site_description", "surrounding_context", "existing_use",
            "hours_of_operation", "num_employees", "num_customers", "estimated_cost",
            "is_flood_affected", "is_bushfire_prone", "is_heritage", "in_heritage_conservation_area",
            "internal_works_only", "parking_spaces_provided", "stormwater_to_council_system",
            "unit", "street_number", "street", "suburb", "building_name",
            "lot", "plan_type", "plan_number", "section", "answers", "comments",
        )
        kwargs = {key: arguments[key] for key in shared_keys if key in arguments}
        result = generate_see_form_data(**kwargs)

        form_data = result["fields"]
        unanswered = result["unanswered_questions"]
        blocking = result["blocking_issues"]

        # The form cannot be written while a scope or identification issue stands.
        if blocking:
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "blocking_issues": blocking,
                "purpose_written_see_headings": (
                    PURPOSE_WRITTEN_SEE_HEADINGS
                    if any("Minor Development Only" in issue for issue in blocking) else None
                ),
                "template_scope": SEE_TEMPLATE_SCOPE,
                "next_step": "Resolve the issues above, or use generate_see_draft to build a purpose-written SEE.",
            }, indent=2))]

        summary = {
            "applicant": form_data["applicant_name"],
            "premises": " ".join(p for p in (
                form_data["address_number"], form_data["street_name"], form_data["suburb"]) if p),
            "land": " ".join(p for p in (
                f"Lot {form_data['lot']}" if form_data["lot"] else "",
                # the form's box is labelled DP, so a deposited plan carries no prefix there
                f"DP {form_data['dp']}" if form_data["dp"].isdigit() else form_data["dp"]) if p),
            "development_type": arguments.get("minor_development_type"),
            "questions_answered": len(SEE_QUESTIONS) - len([q for q in unanswered if q["key"] in SEE_QUESTIONS]),
            "questions_total": len(SEE_QUESTIONS),
        }

        if name == "preview_see_form":
            # Every field that will be written, so review sees exactly what the PDF gets.
            ticks = {
                key: ("Yes" if form_data.get(f"{key}_yes") else "No" if form_data.get(f"{key}_no") else "— unanswered")
                for key in SEE_QUESTIONS
            }
            for key, label in (("flooding", "flooding"), ("bushfire_prone", "bushfire prone"),
                               ("stormwater_council", "stormwater to Council system")):
                value = form_data.get(key)
                ticks[label] = "Yes" if value else "No" if value is False else "— unanswered"

            return [TextContent(type="text", text=json.dumps({
                "summary": summary,
                "text_fields": {
                    key: value for key, value in form_data.items()
                    if not key.endswith(("_yes", "_no")) and isinstance(value, str) and value
                },
                "empty_text_fields": [
                    key for key, value in form_data.items()
                    if not key.endswith(("_yes", "_no")) and isinstance(value, str) and not value
                ],
                "tick_boxes": ticks,
                "derived_answers": result["derived_answers"],
                "unanswered_questions": unanswered,
                "parking": result["parking"],
                "required_documents": result["required_documents"],
                "next_step": (
                    "Collect answers to the unanswered questions and re-send them in `answers`/`comments`, "
                    "then call fill_see_pdf. Unanswered questions are left blank on the form."
                ),
            }, indent=2))]

        # --- fill_see_pdf ------------------------------------------------------
        # Sanitize unconditionally: .name strips any directory components (including
        # absolute paths and ../ traversal), so this can only ever resolve to a bare
        # filename inside the directory we choose below.
        output_filename = Path(arguments.get("output_filename") or "SEE_filled.pdf").name
        if not output_filename or output_filename in (".", ".."):
            output_filename = "SEE_filled.pdf"
        if not output_filename.endswith(".pdf"):
            output_filename += ".pdf"

        tmp_dir: Path | None = None
        if PUBLIC_MODE:
            tmp_dir = Path(tempfile.mkdtemp(prefix="see_"))
            output_path = tmp_dir / output_filename
        else:
            output_dir = DOCS_DIR / "output"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / output_filename

        fill_result = fill_see_pdf(form_data, output_path)
        if not fill_result["success"]:
            if tmp_dir is not None:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            return [TextContent(type="text", text=json.dumps({
                "success": False,
                "error": fill_result.get("error", "Failed to fill PDF."),
                "template_path": str(SEE_TEMPLATE_PATH),
            }, indent=2))]

        notes = [
            "Answer every blank question by hand before lodging — blanks are questions, not answers of 'No'",
            "Sign and date the declaration on page 7",
            "Lodge via NSW Planning Portal",
        ]
        if fill_result["overflowed_fields"]:
            notes.insert(0, (
                "Text longer than the printed box, trimmed to fit: "
                + ", ".join(fill_result["overflowed_fields"])
                + ". Continue it on an attachment; page 1's supporting-information box has been ticked."
            ))
        if fill_result["unresolved_fields"]:
            notes.insert(0, (
                "No box could be located in the template for: "
                + ", ".join(fill_result["unresolved_fields"])
                + " — complete these by hand."
            ))
        if fill_result["template_layout_changed"]:
            notes.insert(0, (
                "WARNING: the template's layout no longer matches what this tool expects ("
                + "; ".join(fill_result["template_layout_changed"])
                + "). Check every field position before lodging."
            ))

        response = {
            "success": True,
            "summary": summary,
            "unanswered_questions": unanswered,
            "derived_answers": result["derived_answers"],
            "required_documents": result["required_documents"],
            "parking": result["parking"],
            "notes": notes,
        }

        if tmp_dir is not None:
            pdf_bytes = output_path.read_bytes()
            shutil.rmtree(tmp_dir, ignore_errors=True)
            response["pdf_base64"] = base64.b64encode(pdf_bytes).decode("ascii")
            response["output_filename"] = output_filename
            notes.insert(0, "PDF returned inline as base64 (pdf_base64) — decode and save it yourself; nothing is kept on the server.")
        else:
            response["output_path"] = str(output_path)

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============================================================================
# Server Entry Point
# ============================================================================

async def run():
    """Run the MCP server over stdio (local, single-user — used by .mcp.json)."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


class _RateLimitMiddleware:
    """Best-effort in-memory per-IP fixed-window rate limiter.

    This is meant as a cheap abuse guard for an open, unauthenticated public deployment —
    not a substitute for a real edge limiter (e.g. Cloudflare) if traffic grows.
    """

    def __init__(self, app, max_requests: int = 30, window_seconds: float = 60.0):
        self.app = app
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict = {}

    async def __call__(self, scope, receive, send):
        import time
        from collections import deque

        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        ip = client[0] if client else "unknown"
        now = time.monotonic()
        hits = self._hits.setdefault(ip, deque())
        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            from starlette.responses import PlainTextResponse
            response = PlainTextResponse("Rate limit exceeded, try again shortly.", status_code=429)
            await response(scope, receive, send)
            return

        hits.append(now)
        await self.app(scope, receive, send)


def build_http_app():
    """Build the Starlette ASGI app that serves the MCP server over Streamable HTTP."""
    from contextlib import asynccontextmanager

    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Mount, Route
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

    # stateless=True: no tool here needs cross-request session state, and it keeps the
    # deployment simple (no session affinity needed if this is ever scaled beyond one instance).
    session_manager = StreamableHTTPSessionManager(app=server, stateless=True)

    async def handle_mcp(scope, receive, send):
        await session_manager.handle_request(scope, receive, send)

    async def health(_request):
        return PlainTextResponse("ok")

    @asynccontextmanager
    async def lifespan(_app):
        async with session_manager.run():
            yield

    app = Starlette(
        routes=[
            Route("/health", health),
            Mount("/mcp", app=handle_mcp),
        ],
        lifespan=lifespan,
    )
    return _RateLimitMiddleware(app)


def run_http():
    """Run the MCP server over Streamable HTTP (public deployment)."""
    import uvicorn

    app = build_http_app()
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)


def main():
    """Main entry point. MCP_TRANSPORT=http serves over Streamable HTTP; anything else (or
    unset) keeps the original stdio behavior used by local .mcp.json setups."""
    if PUBLIC_MODE:
        run_http()
    else:
        import asyncio
        asyncio.run(run())


if __name__ == "__main__":
    main()
