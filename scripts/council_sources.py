"""Where each committed document came from, and where to look for new ones.

Shared by `fetch_council_documents.py` (which downloads what is missing) and
`verify_against_council.py` (which checks what we have is still what Council
publishes). It exists because those two scripts disagreeing about a URL would
make the verifier's "unchanged" result meaningless.

**This manifest is deliberately incomplete.** `documents/` holds ~61 files and
only the ones below have a URL recorded, because `DOCUMENT_INDEX.md` never
recorded provenance and guessing a URL from a filename is exactly how the LEP
2000 / LEP 2012 mix-up gets made (SCRAPER.md §6). The verifier reports unmapped
files rather than skipping them quietly, so the gap stays visible and can be
closed a document at a time — by confirming a URL against the crawl, not by
pattern-matching a name.
"""

BASE = "https://www.lismore.nsw.gov.au/files/assets/public"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# Council index pages to crawl for documents we do not have. Keep this to pages
# that list planning documents for applicants — crawling the whole site turns
# the report into noise nobody reads, which is the failure mode PLAN.md 0.4
# specifically warns about.
CRAWL_PAGES = [
    "https://www.lismore.nsw.gov.au/Building-and-planning/Strategic-planning/Our-LEPs-and-DCPs",
    "https://www.lismore.nsw.gov.au/Households/Rates-and-water-information/Fees-and-charges",
    "https://www.lismore.nsw.gov.au/Building-and-planning/Strategic-planning/Developer-contributions",
]

# (url, category directory, local filename)
#
# Selected for business applicants: the DCP chapters a commercial or industrial
# proposal is assessed against, the documents that decide what it costs, and the
# food/home-business fact sheets. Every DCP entry here is the LEP 2012 version —
# check the `new-` / `_lep_2012` markers before adding more (SCRAPER.md §6).
DOCUMENTS = [
    # --- current fees. ---
    (f"{BASE}/v/1/1.-households/2.-rates-and-water/2026-2027-fees-and-charges.pdf",
     "fees", "fees-and-charges-2026-27.pdf"),

    # --- what a business DA actually costs beyond the lodgement fee ---
    (f"{BASE}/v/3/4.-building-and-planning/3.-strategic-planning/"
     "section-7.11-contributions-plan-2024-2041.pdf",
     "fees", "section-7.11-contributions-plan-2024-2041.pdf"),
    (f"{BASE}/v/1/4.-building-and-planning/5.-building-and-construction/"
     "development_servicing_plans_for_water_supply_and_wastewater.pdf",
     "fees", "development-servicing-plans-water-wastewater.pdf"),

    # --- the numbers a CBD assessment argues about. URL confirmed against the
    #     LEPs and DCPs page 2026-08-02; note it carries Amendment 34, which is
    #     the edition data/parking.py is transcribed from. ---
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-part-a-chapter-7-off-street-carparking-with-amd-34.pdf",
     "dcp", "chapter-7-off-street-carparking.pdf"),

    # --- DCP chapters a commercial/industrial proposal is assessed against ---
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-chapter_5b_-_commercial_and_industrial_subdivision_lep_2012.pdf",
     "dcp", "chapter-5b-commercial-industrial-subdivision.pdf"),
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-part_a_chapter_13_crime_prevention_through_environmental_design_lep_2012.pdf",
     "dcp", "chapter-13-crime-prevention-environmental-design.pdf"),
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-part_a_chapter_15_waste_minimisation_lep_2012.pdf",
     "dcp", "chapter-15-waste-minimisation.pdf"),
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-part_a_chapter_21_public_art_lep_2012.pdf",
     "dcp", "chapter-21-public-art.pdf"),
    (f"{BASE}/v/5/4.-building-and-planning/3.-strategic-planning/chapter-4.pdf",
     "dcp", "chapter-4-rural-nature-based-tourism.pdf"),
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-part_a_chapter_17_acid_sulfate_soils_lep_2012.pdf",
     "dcp", "chapter-17-acid-sulfate-soils.pdf"),

    # --- the precincts businesses are actually located in ---
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-development_control_plan_part_b_chapter_3_-_lismore_cultural_precinct.pdf",
     "dcp", "part-b-chapter-3-lismore-cultural-precinct.pdf"),
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-part_b_chapter_4_airport_industrial_estate_lep_2012.pdf",
     "dcp", "part-b-chapter-4-airport-industrial-estate.pdf"),
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-part_b_chapter_5_wyrallah_rd_industrial_estate_lep_2012.pdf",
     "dcp", "part-b-chapter-5-wyrallah-road-industrial-estate.pdf"),
    (f"{BASE}/v/1/4.-building-and-planning/3.-strategic-planning/"
     "new-part_b_chapter_9_north_lismore_industrial_estate_lep_2012.pdf",
     "dcp", "part-b-chapter-9-north-lismore-industrial-estate.pdf"),

    # --- land use matrix: an independent cross-check on the transcribed
    #     zone tables in data/zones.py (PLAN.md 0.2) ---
    (f"{BASE}/v/1/5.-council/7.-about-council/land-use-matrix-august-2023_1.pdf",
     "lep", "land-use-matrix-august-2023.pdf"),

    # --- opening a food business, and working from home ---
    (f"{BASE}/v/1/3.-business/4.-food-and-home-based-businesses/"
     "requirements_for_set_up_of_food_premises_fact_sheet.pdf",
     "business", "requirements-for-set-up-of-food-premises.pdf"),
    (f"{BASE}/v/1/3.-business/4.-food-and-home-based-businesses/"
     "home_based_food_business_fact_sheet.pdf",
     "business", "home-based-food-business.pdf"),
    (f"{BASE}/v/1/3.-business/4.-food-and-home-based-businesses/"
     "guidelines_for_food_businesses_at_temporary_events.pdf",
     "business", "food-businesses-at-temporary-events.pdf"),
    (f"{BASE}/v/3/3.-business/4.-food-and-home-based-businesses/"
     "standard_3.2.2a_guideline_for_businesses.pdf",
     "business", "food-standard-3-2-2a-guideline.pdf"),
    (f"{BASE}/v/1/3.-business/4.-food-and-home-based-businesses/"
     "nsw-outdoor-dining-policy-2019.pdf",
     "business", "nsw-outdoor-dining-policy-2019.pdf"),
    (f"{BASE}/v/2/3.-business/4.-food-and-home-based-businesses/"
     "fact-sheet-home-occupation.pdf",
     "business", "home-occupation-work-from-home.pdf"),
]

# Documents Council publishes that this repo deliberately does not carry, so the
# crawler stops reporting them every run. A reason is required — "we looked at
# it and decided not to" is information; silence is not.
KNOWN_NOT_CARRIED = {
    "section_94_contributions_plan_north_lismore_plateau.pdf":
        "North Lismore Plateau has its own Section 94 plan, which applies to one "
        "urban release area and not to the business applicants this repo targets. "
        "Worth adding if anyone asks about that precinct.",
}
