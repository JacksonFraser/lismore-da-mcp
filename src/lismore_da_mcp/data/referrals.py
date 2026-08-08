"""External agency referral triggers (integrated development and concurrence)."""

# The words a caller might use for a site characteristic, mapped to the referral
# authority it points at. Matched as substrings, so "bushfire_prone_land" and
# "bushfire" both reach the Rural Fire Service.
#
# This lived inside the check_referrals handler until the readiness check needed
# the same mapping. Two copies would have drifted, and the direction they drift
# in is a characteristic that stops being recognised — which reads to an
# applicant as "no referral required" rather than as an error.
CHARACTERISTIC_TRIGGERS = {
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
        # "the CBD flood exemption precinct" was here until 2026-08-06, with an
        # evacuation-plan-and-PMF-refuge document set attached to it. No such
        # precinct appears in DCP Chapter 8, in LEP 2012, or anywhere else in
        # documents/ — see the header of data/flood.py. What Map 1 actually has
        # is a **CBD Flood Liable** category, which §8.3 gives the Flood Fringe
        # Area's controls and no exemption of any kind.
        "types": ["Any development below the Flood Planning Level", "Habitable floor space on flood prone land", "Development in the CBD Flood Liable area, which takes the Flood Fringe controls (DCP §8.3)"],
        "approval": "Council assessment against LEP 2012 clause 5.21 and DCP Chapter 8 (internal, not an external referral)",
        "documents": ["Flood Risk Assessment", "Survey showing floor levels relative to the Flood Planning Level", "Certificate of structural adequacy from a qualified structural/civil engineer (DCP §8.5.4/§8.6.4)", "Risk analysis report from a structural engineer, for commercial and industrial development"],
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
