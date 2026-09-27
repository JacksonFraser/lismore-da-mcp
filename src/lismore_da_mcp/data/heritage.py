"""LEP 2012 clause 5.10 and DCP Chapter 12, quoted verbatim.

ROADMAP.md S4. Nine places in this repository asserted that **"a Heritage Impact
Statement is required (DCP Chapter 12)"**. Both halves of that are wrong:

- **Chapter 12 requires no heritage document.** It mentions a heritage impact
  statement exactly twice, both times in its definitions section, and says of
  itself that it "will apply whenever development consent is required under
  clause 5.10 Lismore LEP 2012". Checked against
  `documents/dcp/chapter-12-heritage-conservation.pdf`, 2026-08-20. (This line
  used to say "requires no document at all". Reading the chapter end to end for
  ROADMAP.md C1 found two things it does ask for — colour scheme details with a
  DA for new development, and a justification for any departure from its
  policies — carried in `WHAT_CHAPTER_12_DOES_ASK_FOR`. Neither is a heritage
  management document.)
- **The provision is cl 5.10(5), and it says *may*.** The consent authority
  *may* require a **heritage management document** — of which a heritage impact
  statement is one of three forms, the others being a heritage conservation
  management plan and "any other document that provides guidelines for the
  ongoing management and conservation" of the item.

The difference is not pedantry. Telling an applicant a specific document is
mandatory sends them to buy a heritage consultant's report before anyone has
asked for one, and it forecloses the conversation in which Council says what it
actually wants — which for a shopfront repaint may be nothing. This is the same
failure as the residential standards in item 0.6: stating a discretion as a rule
talks an applicant out of an argument the source expressly leaves open.

Two subclauses nothing here cited before, and both change who is affected:

- **cl 5.10(5)(c) reaches the neighbours.** The heritage assessment power
  applies to land "within the vicinity of" a heritage item or conservation area,
  not only to the item itself. A site that `lookup_site_constraints` reports as
  not heritage-listed can still be caught.
- **cl 5.10(10) is how a café opens in a heritage building.** It lets the
  consent authority approve development "for any purpose" of a heritage building
  "even though development for that purpose would otherwise not be allowed by
  this Plan", on five conditions. It is a pathway past a prohibited land use
  table result, and it belongs with the SEPP caveat in `check_permissibility`
  rather than nowhere.

ROADMAP.md C1 added the chapter itself — its scope, §12.3's binding-with-a-
variation-route modality, the §12.4 principles, every §12.5 design guideline and
all seven §12.6 conservation area policies — below the LEP provisions, and the
consent trigger (cl 5.10(2)) and its exception (cl 5.10(3)) beside them, because
whether Chapter 12 applies at all turns on cl 5.10(2).

Every LEP quote appears verbatim in `documents/lep/lep-2012-nsw-full.txt` and
every Chapter 12 quote in the chapter; `scripts/audit_heritage.py` checks both,
counts the chapter's bullets and headings against what is carried, and checks
that the phrase this file exists to correct is still absent from Chapter 12.
"""

SOURCE = "Lismore LEP 2012 clause 5.10"

# What the LEP may require, and the fact that it is one of three things.
HERITAGE_MANAGEMENT_DOCUMENT = {
    "clause": "Lismore LEP 2012 Dictionary",
    "quote": (
        "heritage management document means—\n"
        "(a)  a heritage conservation management plan, or\n"
        "(b)  a heritage impact statement, or\n"
        "(c)  any other document that provides guidelines for the ongoing management and "
        "conservation of a heritage item, Aboriginal object, Aboriginal place of heritage "
        "significance or heritage conservation area."
    ),
    "why_this_matters": (
        "A heritage impact statement is one of three forms this can take, not the required "
        "form. Ask Council which it wants before commissioning one — for minor external work "
        "it is often satisfied by far less than a consultant's report."
    ),
}

# The power, and the word it turns on.
HERITAGE_ASSESSMENT = {
    "clause": "cl 5.10(5)",
    "quote": (
        "The consent authority may, before granting consent to any development—\n"
        "(a)  on land on which a heritage item is located, or\n"
        "(b)  on land that is within a heritage conservation area, or\n"
        "(c)  on land that is within the vicinity of land referred to in paragraph (a) or (b),\n"
        "require a heritage management document to be prepared that assesses the extent to "
        "which the carrying out of the proposed development would affect the heritage "
        "significance of the heritage item or heritage conservation area concerned."
    ),
    "in_plain_words": (
        "Council may ask for a heritage document. It is not automatic, and it is not "
        "necessarily a Heritage Impact Statement. Paragraph (c) also catches land in the "
        "vicinity of a heritage item — so a neighbouring site can be assessed for heritage "
        "impact even though it is not itself listed."
    ),
}

# The obligation that *is* unconditional, and it is Council's, not the applicant's.
CONSIDERATION_IS_MANDATORY = {
    "clause": "cl 5.10(4)",
    "quote": (
        "The consent authority must, before granting consent under this clause in respect of a "
        "heritage item or heritage conservation area, consider the effect of the proposed "
        "development on the heritage significance of the item or area concerned. This "
        "subclause applies regardless of whether a heritage management document is prepared "
        "under subclause (5) or a heritage conservation management plan is submitted under "
        "subclause (6)."
    ),
    "in_plain_words": (
        "The impact must be considered whether or not any document is required. So a proposal "
        "that says nothing about heritage impact leaves the consent authority to reach its own "
        "view — which is the practical reason to address it in the SEE even when no report has "
        "been asked for."
    ),
}

# The pathway past a prohibited land use table result.
CONSERVATION_INCENTIVES = {
    "clause": "cl 5.10(10)",
    "quote": (
        "The consent authority may grant consent to development for any purpose of a building "
        "that is a heritage item or of the land on which such a building is erected, or for any "
        "purpose on an Aboriginal place of heritage significance, even though development for "
        "that purpose would otherwise not be allowed by this Plan, if the consent authority is "
        "satisfied that—\n"
        "(a)  the conservation of the heritage item or Aboriginal place of heritage "
        "significance is facilitated by the granting of consent, and\n"
        "(b)  the proposed development is in accordance with a heritage management document "
        "that has been approved by the consent authority, and\n"
        "(c)  the consent to the proposed development would require that all necessary "
        "conservation work identified in the heritage management document is carried out, and\n"
        "(d)  the proposed development would not adversely affect the heritage significance of "
        "the heritage item, including its setting, or the heritage significance of the "
        "Aboriginal place of heritage significance, and\n"
        "(e)  the proposed development would not have any significant adverse effect on the "
        "amenity of the surrounding area."
    ),
    "in_plain_words": (
        "A use the zone's land use table prohibits can still be approved in a heritage "
        "*building*, if the use is what pays for conserving it. This is the provision behind "
        "a café or gallery in an old bank or church. The five conditions are cumulative and "
        "condition (b) means a heritage management document stops being optional — here it is "
        "the basis of the consent. Put it to the Duty Planner before abandoning a site."
    ),
}

# The correction itself, kept as data so the nine call sites cannot re-diverge.
WHAT_CHAPTER_12_DOES_NOT_SAY = {
    "the_claim": "A Heritage Impact Statement is required (DCP Chapter 12).",
    "why_it_is_wrong": (
        "DCP Chapter 12 requires no heritage document. It mentions a heritage impact statement "
        "only in its definitions, and states that it applies whenever consent is required under "
        "LEP cl 5.10. The power to require a document is cl 5.10(5), it is discretionary "
        "('may'), and what it names is a heritage management document — of which a heritage "
        "impact statement is one of three forms."
    ),
    "say_instead": (
        "Council may require a heritage management document (LEP cl 5.10(5)) — a Heritage "
        "Impact Statement is the usual form. Ask which is wanted before commissioning one."
    ),
}


# --- When cl 5.10 requires consent, and when it does not ---------------------
#
# ROADMAP.md C1. Chapter 12 "will apply whenever development consent is
# required under clause 5.10", so whether it applies at all turns on this
# subclause. Note what it lists: works — demolishing, altering, erecting,
# subdividing, disturbing. It does not list a change of use.

CONSENT_REQUIRED = {
    "clause": "cl 5.10(2)",
    "quote": (
        "Requirement for consent Development consent is required for any of the following—\n"
        "(a)  demolishing or moving any of the following or altering the exterior of any of the "
        "following (including, in the case of a building, making changes to its detail, fabric, "
        "finish or appearance)—\n"
        "(i)  a heritage item,\n"
        "(ii)  an Aboriginal object,\n"
        "(iii)  a building, work, relic or tree within a heritage conservation area,\n"
        "(b)  altering a heritage item that is a building by making structural changes to its "
        "interior or by making changes to anything inside the item that is specified in "
        "Schedule 5 in relation to the item,\n"
        "(c)  disturbing or excavating an archaeological site while knowing, or having "
        "reasonable cause to suspect, that the disturbance or excavation will or is likely to "
        "result in a relic being discovered, exposed, moved, damaged or destroyed,\n"
        "(d)  disturbing or excavating an Aboriginal place of heritage significance,\n"
        "(e)  erecting a building on land—\n"
        "(i)  on which a heritage item is located or that is within a heritage conservation "
        "area, or\n"
        "(ii)  on which an Aboriginal object is located or that is within an Aboriginal place "
        "of heritage significance,\n"
        "(f)  subdividing land—\n"
        "(i)  on which a heritage item is located or that is within a heritage conservation "
        "area, or\n"
        "(ii)  on which an Aboriginal object is located or that is within an Aboriginal place "
        "of heritage significance."
    ),
    "in_plain_words": (
        "Paragraph (a) is the one a business meets: altering the exterior includes changes to "
        "a building's 'detail, fabric, finish or appearance', which is how a repaint, new "
        "signage fixed to the facade or a new shopfront comes to need consent on a heritage "
        "item or in a conservation area. Paragraph (b) reaches inside a heritage item only for "
        "structural changes, or for anything Schedule 5 specifically lists inside it. The list "
        "is of works; a change of use is not on it."
    ),
}

CONSENT_NOT_REQUIRED = {
    "clause": "cl 5.10(3)",
    "quote": (
        "When consent not required However, development consent under this clause is not "
        "required if—\n"
        "(a)  the applicant has notified the consent authority of the proposed development and "
        "the consent authority has advised the applicant in writing before any work is carried "
        "out that it is satisfied that the proposed development—\n"
        "(i)  is of a minor nature or is for the maintenance of the heritage item, Aboriginal "
        "object, Aboriginal place of heritage significance or archaeological site or a building, "
        "work, relic, tree or place within the heritage conservation area, and\n"
        "(ii)  would not adversely affect the heritage significance of the heritage item, "
        "Aboriginal object, Aboriginal place, archaeological site or heritage conservation "
        "area, or"
    ),
    "exempt_development_quote": "(d)  the development is exempt development.",
    "in_plain_words": (
        "Minor work and maintenance can go ahead without consent under this clause — but only "
        "after you have told Council and Council has replied in writing, before the work "
        "starts, that it is satisfied on both counts. Deciding for yourself that the work is "
        "minor does not engage this subclause."
    ),
}

CONSERVATION_MANAGEMENT_PLAN = {
    "clause": "cl 5.10(6)",
    "quote": (
        "Heritage conservation management plans The consent authority may require, after "
        "considering the heritage significance of a heritage item and the extent of change "
        "proposed to it, the submission of a heritage conservation management plan before "
        "granting consent under this clause."
    ),
}


# --- DCP Chapter 12, quoted verbatim ----------------------------------------
#
# ROADMAP.md C1. Everything below appears in
# `documents/dcp/chapter-12-heritage-conservation.pdf` (21 pages, read end to
# end 2026-09-27) and `scripts/audit_heritage.py` checks each string against
# it. Slips in the source — "polices", "formers details", "1910 and1930s",
# "Views too and from", "semi rural urban from" — are kept, because a quote
# corrected is no longer a quote and the audit would rightly reject it.
#
# What the chapter is, read whole: an introduction tying it to cl 5.10;
# objectives; definitions; §12.3, which makes its policies binding on Schedule 5
# items *with a variation route*; §12.4 conservation principles written as
# recommendations; §12.5 design guidelines per building element, each split
# PREFERRED / NOT ENCOURAGED; and §12.6, one section per heritage conservation
# area, each with a statement of significance, defining characteristics and
# precinct policies. Its only figures are 1 metre (garage setback behind the
# dwelling front), 1.2 and 1.8 metres (fence heights), "less than 1 metre"
# (Dalley Street front fences) and the 1000m2 that describes existing Nimbin
# lots. The audit checks no other figure is in it.

CHAPTER_12 = "Lismore DCP Part A Chapter 12 — Heritage Conservation"

CHAPTER_12_SCOPE = {
    "section": "Chapter 12 introduction",
    "applies_to": (
        "This Chapter applies to land within Lismore City, and specifically to the buildings, "
        "items, archaeological sites and heritage conservation areas listed in Schedule 5 of "
        "the Lismore Local Environmental Plan 2012."
    ),
    "non_listed_properties": (
        "This Chapter may also be recommended by Council to owners of non-listed, but similar "
        "historic properties to guide sympathetic alterations outside of heritage conservation "
        "areas."
    ),
    "read_with": (
        "This Chapter should be read in conjunction with the Lismore Local Environmental Plan "
        "2012, Chapter 6 (Nimbin Village) of Part B of this DCP and any other Council policies "
        "or other chapters of this DCP which may be relevant to the proposal (e.g. requirements "
        "for development on flood prone lands, tree preservation, off-street car parking, urban "
        "design and weather protection and crime prevention through environmental design)."
    ),
    "trigger": (
        "This Chapter will apply whenever development consent is required under clause 5.10 "
        "Lismore LEP 2012."
    ),
    "external_changes_note": (
        "Note. Non structural changes which alter the exterior of a building such as cladding, "
        "re-roofing in different materials, repainting with a different colour, replacement of "
        "timber windows with aluminium, etc are alterations that require consent."
    ),
}

OBJECTIVES = [
    "To protect the significance and setting of heritage items, heritage conservation areas "
    "and archaeological sites in the Lismore City Council area;",
    "To integrate heritage conservation into planning and development controls;",
    "To allow sympathetic changes to occur;",
    "To provide detailed polices which encourage well designed extensions and infill "
    "development;",
    "To encourage and promote public awareness, appreciation and knowledge of the value of "
    "heritage items and conservation areas.",
]

# §12.3 — the modality of the whole chapter, in two sentences that pull in
# opposite directions. Report both or neither.
HOW_THE_CHAPTER_APPLIES = {
    "section": "12.3",
    "must_comply": (
        "Development applications applying to items listed in Schedule 5 LEP 2012 must comply "
        "with relevant policies set out in Clauses 12.4 (Heritage Principles), 12.5 (Design "
        "Guidelines) and 12.6 (Precinct Policies)."
    ),
    "variation": (
        "It is recognised that the policies in this plan may not be appropriate in every case, "
        "and sometimes a variation is required. If a proposal departs from the policies, "
        "justification must be provided. A variation may be approved if it meets the overall "
        "aims and objectives of this Chapter."
    ),
    "in_plain_words": (
        "The policies bind, but not absolutely: a proposal can depart from one if it says why "
        "and still meets the chapter's objectives. The PREFERRED / NOT ENCOURAGED labels are "
        "the chapter's own, and 'not encouraged' is weaker than 'prohibited' — only a handful "
        "of policies are worded as a flat refusal, and those are listed separately. Where you "
        "depart from a policy, put the justification in the Statement of Environmental "
        "Effects: §12.3 says it must be provided."
    ),
}

# §12.2. Carried because an applicant who *is* asked for one needs to know what
# it contains — three parts, none of which is a particular consultant's format.
HERITAGE_IMPACT_STATEMENT_DEFINITION = {
    "section": "12.2",
    "quote": (
        "heritage impact statement means a document consisting of: (a) a statement "
        "demonstrating the heritage significance of a heritage item or heritage conservation "
        "area, and (b) an assessment of the impact that proposed development will have on that "
        "significance, and (c) proposals for measures to minimise that impact."
    ),
}

# What Chapter 12 *does* ask to accompany an application. S4 established that it
# requires no heritage management document, and that stands — but "requires no
# document at all", as this file's docstring used to put it, was one clause too
# strong. Reading the chapter end to end found these two.
WHAT_CHAPTER_12_DOES_ASK_FOR = [
    {
        "section": "12.5 Colours",
        "quote": "Colour scheme details for new development will be required with the "
                 "development application.",
        "applies_to": "New development — the sentence closes the guideline on colours for new "
                      "development, not the one for old buildings.",
    },
    {
        "section": "12.3",
        "quote": "If a proposal departs from the policies, justification must be provided.",
        "applies_to": "Any proposal that departs from a Chapter 12 policy. This is content for "
                      "the SEE, not a separate report.",
    },
]

# §12.4 Heritage Principles. Written as recommendations, and the tool says so.
PRINCIPLES = {
    "section": "12.4",
    "why_conserve": [
        "Heritage items and places provide a link to the past and help people understand "
        "connections to their local history.",
        "Heritage buildings provide examples of craftsmanship and materials which are becoming "
        "increasingly rare.",
        "Heritage places provide identity and meaning to the town.",
        "Heritage is a drawcard for tourism which is an important part of the local economy.",
        "Heritage is an asset that should be looked after carefully.",
    ],
    "burra_charter_approach": (
        "“do as much as necessary to care for the place and make it useable, but otherwise "
        "change it as little as possible”"
    ),
    "burra_charter_intro": (
        "The Conservation Principles from the Burra Charter are summarised briefly below. "
        "Before preparing a development application, it is recommended that these principles "
        "are carefully considered."
    ),
    "burra_charter_principles": [
        "retain what is important about a place;",
        "provide for current and future maintenance;",
        "respect original fabric, past uses, associations and meanings;",
        "understand and retain evidence of changes which are part of the history;",
        "understand the place before making decisions;",
        "use traditional techniques and materials to conserve original materials;",
        "retain the use of a place if it is important, or ensure a compatible new use;",
        "involve minimal change to allow new uses, respect the original fabric, associations "
        "and uses;",
        "retain an appropriate visual setting for heritage places;",
        "keep a building, work or other component in its historical location, because the "
        "physical location of a heritage item or place is part of its heritage significance, "
        "relocation is a last resort to ensure survival of the building;",
        "keep contents, fixtures and objects which are part of a place’s heritage significance "
        "at that place;",
        "retain related buildings and objects as they are also important; and",
        "enable people who have special associations and meanings with a place in its care and "
        "future management to be involved.",
    ],
    "understanding_heritage_value": (
        "Lack of maintenance, badly designed alterations, incorrect materials, inappropriate "
        "subdivisions which detract from the setting of a building, and unsympathetic colour "
        "schemes all result in the loss of heritage value. It is therefore important to "
        "understand why a building or place is important before changes are considered."
    ),
    "original_fabric_intro": (
        "Care and skill are needed to make decisions about the care and management of a "
        "heritage building or place and it is recommended that these actions are followed:"
    ),
    "original_fabric": [
        "Understand the properties of traditional materials before making changes, for example "
        "use correct mortars with old bricks.",
        "Obtain advice from Council regarding access to a Heritage Advisor/Officer and "
        "information on traditional materials such as metal and timber.",
        "Seek advice from skilled tradesmen with heritage experience.",
        "Beware of irreversible changes such as painting of brickwork.",
        "Consider a range of solutions when planning upgrades for safety, access and fire "
        "protection.",
        "Regular maintenance is essential to look after an old building, and can prevent more "
        "costly repairs.",
    ],
}

# §12.5 Design Guidelines, one entry per element in the chapter's order. The
# `preferred` / `not_encouraged` split is the chapter's own labelling; `guidance`
# holds a plain list the chapter gives under neither label.
DESIGN_GUIDELINES = {
    "streetscape_context": {
        "heading": "General Streetscape Context",
        "intro": (
            "It is important that alterations, new additions or new buildings are ‘good "
            "neighbours’ and are consistent with the character of the locality. Understanding "
            "this context helps when designing a new building or alterations."
        ),
        "guidance_label": "Design elements which characterise the historic areas of Lismore:",
        "guidance": [
            "weatherboard buildings, mainly single storey with galvanised metal roofing;",
            "consistency of scale, height, and bulk within residential streets;",
            "steeper roof pitches, often with complex hip and gables ;",
            "long slender proportions to windows, especially those facing the street;",
            "projecting gables to the street;",
            "verandahs generally on front or side elevations;",
            "informal grass verges with consistent street tree planting;",
            "front fences of low to medium height;",
            "masonry and stone restricted mainly to large churches and key civic and commercial "
            "buildings.",
        ],
    },
    "sympathetic_change": {
        "heading": "Sympathetic Change",
        "intro": (
            "Heritage protection is not intended to freeze historic properties in time. The "
            "need to upgrade older homes to modern standards is accepted but these changes "
            "should take place in the most sympathetic way possible. Those elements which led "
            "to a property being protected must be maintained."
        ),
        "guidance_label": "Basic principles to be observed:",
        "guidance": [
            "Maintain the general scale, height and bulk and proportions of traditional "
            "buildings in the streetscape.",
            "Do not overwhelm the original building with an extension. Consider creating two "
            "separate buildings with a linkage. This helps retain the integrity of the "
            "original.",
            "Do not alter original front facades of buildings in conservation areas. Additions "
            "are best sited to the side or rear.",
            "Keep floor levels similar to adjoining buildings.",
            "Avoid making a replica copy of a heritage building for infill development, but "
            "follow proportions and scale.",
            "Keep it simple by not using a mixture of features from different eras or adding "
            "historic features to new buildings.",
        ],
    },
    "roof": {
        "heading": "Roof Pitch and Form",
        "preferred": [
            "Ensure that roof pitch, proportion and orientation to the street is compatible "
            "with traditional roofs in the surrounding streetscape.",
            "Use uncoloured galvanised steel where possible or reinstate a painted roof where "
            "evidence of this exists.",
            "Use correct gutters in the maintenance of older buildings. Quad, half round and "
            "ogee gutters are the most appropriate profiles, depending on original details.",
        ],
        "not_encouraged": [
            "Modern material such as ‘colorbond’ on heritage items. Avoid concrete tiles or "
            "contemporary colours such as blues, etc in metal roofing on non-heritage items as "
            "this is incompatible with the character of the streetscape in heritage "
            "conservation areas.",
            "Perforated box gutters as they are not correct in a historic context.",
        ],
    },
    "verandahs": {
        "heading": "Verandahs",
        "preferred": [
            "Include verandahs into the design of new development.",
            "Use a simple skillion style as it integrates well with new buildings.",
            "Conserve verandahs with original timber detailing.",
            "Open up enclosed verandahs where possible and re-instate missing details.",
        ],
        "not_encouraged": [
            "Bullnose style, lace ironwork, decorative fretwork or federation brackets to posts "
            "on modern buildings, as it lacks historic context. These features may be "
            "re-instated to a historic building, where it can be shown that they previously "
            "existed.",
        ],
    },
    "windows_and_doors": {
        "heading": "Windows and Doors",
        "preferred": [
            "Use strong vertical proportions to windows in new development and additions.",
            "Use timber windows for restoration of traditional buildings.",
            "Use timber windows without glazing bars for infill development where possible as "
            "it is consistent with the character of the streetscape. Aluminium windows with a "
            "suitable frame size and proportions will be considered for new work but have a "
            "different aesthetic character and limit the ability to vary colour schemes.",
        ],
        "not_encouraged": [
            "Aluminium windows on heritage items or significant buildings.",
        ],
    },
    "building_materials": {
        "heading": "Building Materials",
        "preferred": [
            "Use matching materials for restoration and additions to existing buildings.",
            "Use lightweight materials such as timber, compressed sheeting, or cement profiled "
            "weatherboards for infill development in a frontage dominated by timber buildings. "
            "The use of masonry is only acceptable in a mixed street frontage of timber and "
            "masonry buildings where less than half the buildings are of timber construction.",
            "Paint or render new masonry (where acceptable) for infill development in a plain "
            "colour and texture, in preference to face brick.",
        ],
        "not_encouraged": [
            "Textured paint type finishes.",
            "White, light, multi coloured, or double height bricks or imitation sandstone "
            "blocks.",
        ],
    },
    "colours": {
        "heading": "Colours",
        "preferred": [
            "Use a traditional colour scheme for an old building. Seek advice from Council, "
            "paint companies, and numerous books on this subject. Contrasting colour schemes "
            "which use dark walls with light trims can also be very effective, but be careful "
            "in colour selection and ensure that it will be sympathetic in the streetscape.",
            "Use variations to traditional colours for new development but still maintaining "
            "light colours for wall and roof and dark to trims, which will be harmonious in the "
            "streetscape. Colour scheme details for new development will be required with the "
            "development application.",
        ],
        "not_encouraged": [
            "Typical traditional colour schemes such as Cream, Indian Red and Brunswick Green "
            "for new development.",
            "Bold primary colours, black or white.",
        ],
    },
    "setbacks": {
        "heading": "Setbacks and Orientation",
        "intro": "Setbacks for new development should comply with Council’s requirements.",
        "guidance": [
            "Variations will only be considered where it can be demonstrated that the setback "
            "is consistent with adjoining development and that the new building will not be "
            "intrusive in the streetscape.",
            "Minimum setbacks may need to be increased to protect the setting of a heritage "
            "item, where new development is adjacent.",
        ],
    },
    "garages_and_carports": {
        "heading": "Garages and Carports",
        "preferred": [
            "Retain early garages, carports and sheds wherever possible as they contribute to "
            "the character of the heritage conservation area.",
            "Locate garages generally towards the rear of allotments and set back a minimum of "
            "1 metre from the front of the dwelling.",
            "Keep garages and carports separate from the house as a general rule.",
            "Match the roof pitch, form and materials of the main building as closely as "
            "possible.",
            "Respect vertical proportions. Avoid double width horizontal doors.",
            "Consider a simple car port under a continuation of the roof line, for small sites "
            "as this has less visual impact.",
        ],
        "not_encouraged": [
            "Prefabricated metal sheds with low pitched roofs. These are not compatible with "
            "traditional streetscapes and should be avoided.",
        ],
    },
    "fences": {
        "heading": "Fences",
        "preferred": [
            "Be consistent with traditional fences in the streetscape. They are generally a "
            "modest height, and not solid to allow a view of the garden and the front of the "
            "house.",
            "Choose a fence style and materials which is consistent with the age and style of "
            "the dwelling. Examples include picket fences, low post and rail fences and low "
            "walls with galvanised pipe common to the 1920s and 30s.",
            "Use a simple fence style for new development that will harmonise in the "
            "streetscape.",
        ],
        "not_encouraged": [
            "Metal panel fences, pool fencing, spear tops, aluminium lace panels and bagged "
            "masonry fences as they are inconsistent with the character of heritage items or "
            "heritage conservation areas.",
            "Fencing higher than 1.2 metres forward of the front building line. Elsewhere the "
            "maximum height is 1.8 metres.",
        ],
    },
    "outbuildings_and_pools": {
        "heading": "Outbuildings and Swimming Pools",
        "intro": (
            "Swimming pools and additional shed space should generally be located at the rear "
            "of properties."
        ),
        "preferred": [
            "Ensure that they are well positioned to respect the setting and spaces around the "
            "building, especially in relation to heritage items.",
            "Respect original garden layouts retaining mature trees, shrubs, plants and "
            "pathways.",
            "Locate swimming pool safety fencing at the rear of properties where it will be "
            "screened from public view and add landscaping to soften the impact on a historic "
            "house.",
        ],
    },
    "signage": {
        "heading": "Signage and Advertising",
        "intro": (
            "Signage on commercial or civic buildings can contribute to the character of the "
            "streetscape provided that it is visually sympathetic."
        ),
        "preferred": [
            "Use signs of an appropriate size and in appropriate locations, e.g. hanging signs "
            "or signs within a fascia.",
            "Use traditional hand painted signage, or individually mounted letters in "
            "preference to pre-cut vinyl lettering.",
            "Use colour schemes that are effective and readable through the use of contrast.",
        ],
        "not_encouraged": [
            "Signs in locations, which detract from a building such as above parapets, large "
            "projections or over-large fascias.",
            "Bold primary, fluorescent or neon colours. Council may require bold corporate "
            "colour schemes to be adapted to make them acceptable on heritage items or in "
            "conservation areas.",
            "Internally illuminated signs such as box signs or neon letters as they are "
            "inconsistent with heritage buildings and precincts and will not be approved. "
            "Consider externally illuminated signage with spotlights subject to development "
            "consent.",
        ],
    },
}

PRECINCT_POLICIES_INTRO = {
    "section": "12.6",
    "quote": (
        "The following section outlines specific policies which relate to the different "
        "heritage conservation areas. These policies must be addressed with development "
        "applications for that respective area."
    ),
}

# §12.6, one entry per heritage conservation area. The DCP heading and the LEP
# name differ for every area ("SPINKS PARK AND CIVIC PRECINCT/HERITAGE
# CONSERVATION AREA" / "Spinks Park/Civic Precinct Conservation Area"), and both
# are carried so the audit can find each in its own document.
# `lep_name`, `heritage_map_label` and `lep_significance` are LEP Schedule 5
# Part 2's; everything else is the chapter's.
CONSERVATION_AREAS = {
    "dalley_street": {
        "lep_name": "Dalley Street Conservation Area",
        "heritage_map_label": "C1",
        "lep_significance": "Local",
        "dcp_heading": "DALLEY STREET HERITAGE CONSERVATION AREA",
        "statement_of_significance": [
            "Good row of early twentieth century homes. Buildings not outstanding in themselves "
            "but combining well, particularly the row of inter-war houses at Nos 29-35. Set in "
            "generous grounds with well maintained front lawns and gardens. Gentle rise on the "
            "flood free knoll enhances streetscape. The large symmetrical ground hugging "
            "bungalows contrast with the raised basements of contemporary housing elsewhere in "
            "Lismore.",
        ],
        "characteristics": [
            "Detached single storey houses, mainly from the interwar period built at low "
            "density on large lots.",
            "Predominantly timber construction with galvanised metal roofs with strong "
            "horizontal proportions.",
            "Low front fences especially low brick walls or posts with galvanised pipe. Not "
            "picket fences.",
            "Landscaped spacious grounds with mature trees and shrubs.",
            "Verandahs and gabled porches are a strong design element common to many houses.",
            "High proportion of dwellings used as professional consulting rooms due to "
            "proximity to St Vincent’s Hospital.",
        ],
        "policies": [
            "Any development in this precinct must respect the scale, density, form and "
            "proportions of existing development, with special attention to the low set "
            "horizontal emphasis of existing dwellings.",
            "Generous setbacks and landscaping especially to the front of buildings should be "
            "maintained, to conserve the spaces between buildings which contribute to the "
            "character of this precinct.",
            "Any development in this precinct should remain single storey to maintain the "
            "visual character and unity of this streetscape.",
            "Car parking should not be approved in front set back areas as it would erode the "
            "visual amenity of the streetscape and detract from the setting of the dwellings.",
            "Front fences should be low (less than 1 metre) and in character with the "
            "established pattern of development. Solid fencing to front boundaries will not be "
            "permitted as it is out of character in the streetscape, but is acceptable to side "
            "and rear boundaries.",
        ],
        "note": (
            "The chapter notes a high proportion of dwellings here are used as professional "
            "consulting rooms — the business most likely to be proposing work in this area. The "
            "policy on car parking in front setbacks is the one that meets it."
        ),
    },
    "spinks_park_civic": {
        "lep_name": "Spinks Park/Civic Precinct Conservation Area",
        "heritage_map_label": "C5",
        "lep_significance": "Local",
        "dcp_heading": "SPINKS PARK AND CIVIC PRECINCT/HERITAGE CONSERVATION AREA",
        "statement_of_significance": [
            "Pre-First World War urban park located at the centre of town, on the eastern bank "
            "of Wilson’s River. The site of a number of notable period buildings, monuments and "
            "street furniture. Enhanced by tree planting from circa 1900. Site of recreational "
            "facilities (bowls, croquet and baths) from the 1920s. Consciously created in "
            "accordance with the prize winning design by noted architect FJ Board. Board also "
            "designed many of the park’s buildings including the rotunda and CWA rooms. One of "
            "the forward looking works of an active and progressive municipal Council, "
            "eventually named after Mayor Spinks. Considerable social, historical and aesthetic "
            "significance, despite alteration of the original design concept. Local "
            "Significance.",
            "Important concentration of buildings forming an attractive period townscape. "
            "Setting enhanced by park and proximity to the river and centre of town. Buildings "
            "of note on Molesworth and Magellan Streets include several public, civic and "
            "commercial buildings. The former post office building is a fine landmark on the "
            "corner of the two streets. The grouping marks the historic shift of the town "
            "centre from its original focus, north of Woodlark St.",
        ],
        "characteristics": [
            "A city centre park of considerable community value which has been in continuous "
            "use since the early 1900s.",
            "Substantial and notable public and commercial buildings in a prominent streetscape "
            "located opposite Spinks Park.",
            "Historic tree planting and relationship with the Wilsons River.",
            "Periodic flood events, recently addressed by construction of a levee wall.",
        ],
        "policies": [
            "Ensure continued public use and ongoing management of War Memorial Park and Spinks "
            "Park through an adopted Plan of Management.",
            "Ensure that heritage issues are fully addressed when making decisions about "
            "alterations, changes and development of any facilities, structures, uses or layout "
            "in the park.",
            "Buildings, monuments and structures must be carefully conserved in accordance with "
            "the Principles of this Plan and the Burra Charter. (Council’s budget needs to "
            "reflect these obligations).",
            "Ensure that measures are taken for the protection of historic buildings, "
            "structures or monuments during any festivals or events held in the park.",
            "Adopt a policy on graffiti removal and ensure that any graffiti on historic "
            "structures is removed immediately with appropriate methods.",
            "Ensure that original plantings that relate to the historical significance of the "
            "park as originally laid out by FJ Board are maintained as long as possible and "
            "take action to plant the same replacement species if or when required.",
            "Foster an understanding and appreciation of the historical and social significance "
            "of Spinks Park in the community so that it is valued as an important public space "
            "and precinct for future generations.",
        ],
        "note": (
            "Every precinct policy for this area is addressed to the park and to Council as its "
            "manager; none is written for the commercial buildings the statement of "
            "significance names on Molesworth and Magellan Streets. A business there is still "
            "inside the conservation area — LEP cl 5.10 and the §12.5 guidelines apply — but no "
            "precinct policy is aimed at it."
        ),
    },
    "st_carthages": {
        "lep_name": "St Carthage’s Conservation Area",
        "heritage_map_label": "C6",
        "lep_significance": "Local",
        "dcp_heading": "ST CARTHAGE’S HERITAGE CONSERVATION AREA",
        "statement_of_significance": [
            "Important grouping of Cathedral and school buildings set in generous and attractive "
            "grounds. Major townspace significance in a very visible inner urban location. "
            "Social and historical interest for the changes in use over the years, consistent "
            "with the changing circumstances of the Church and Catholic education. Local "
            "Significance.",
        ],
        "characteristics": [
            "Large scale buildings in a distinct group with views over low lying playing "
            "fields.",
            "Elevated site and visually prominent.",
            "Important spaces between key buildings contribute to the visual character of the "
            "precinct.",
            "Architectural and aesthetic qualities of the precinct are very important to the "
            "city centre identity.",
            "Large fig trees on eastern side of Dawson Street contribute to the aesthetic "
            "quality of the streetscape.",
        ],
        "policies": [
            "Development in this precinct must be carefully assessed not only in relation to "
            "any individual heritage item, but also to the relationship between key buildings, "
            "and the spaces they create, and on the character of the precinct as a whole.",
            "Owners of buildings in this precinct need to consider long term maintenance plans "
            "and uses of historic buildings. Preparation of heritage conservation management "
            "plans for this group of buildings is recommended.",
            "Any proposals for development of sports facilities on open space land surrounding "
            "this precinct such as club houses, amenities etc, must be carefully designed and "
            "sited, sympathetic in form, scale and colours and should not obstruct views of "
            "landmark buildings.",
            "Any advertising on sports fields surrounding the precinct should also be suitably "
            "discreet.",
        ],
        "note": (
            "A heritage conservation management plan is *recommended* here, in the chapter's "
            "word — not required. Whether one is required is LEP cl 5.10(6), which says the "
            "consent authority may require it."
        ),
    },
    "st_andrews": {
        "lep_name": "St Andrew’s Conservation Area",
        "heritage_map_label": "C4",
        "lep_significance": "Local",
        "dcp_heading": "ST ANDREWS HERITAGE CONSERVATION AREA",
        "statement_of_significance": [
            "The St Andrews/Court House precinct is a notable illustration of the response of "
            "urban form to social and environmental factors. Views too and from the river "
            "contribute to the precinct’s townscape value. All buildings, grand and modest, "
            "create period streetscapes of interest, though there have been some unwelcome "
            "intrusions. The varied period character adds to the interest. Historically this "
            "was the original commercial centre of Lismore.",
            "The elevated site gives the magnificent Church landmark prominence. The Court "
            "House and Police station mark the establishment of law and order as well as "
            "official early recognition of the importance of Lismore as a settlement.",
            "For residential buildings, the precinct offered a flood free location. Verandahs "
            "are a unifying design element. The large filigree style building on Coleman Street "
            "is an unusual building of special note. The row on Coleman Street also has the "
            "benefit of a green strip on Molesworth St, kept free of buildings by regular "
            "flooding. Local Significance.",
        ],
        "characteristics": [
            "An elevated site, which is visually prominent and historically important to the "
            "city.",
            "The Church, Court House and associated buildings provide this precinct with a "
            "strong, formal character and sense of place.",
            "The continuous land uses of law and order with associated legal offices are "
            "important and provide enduring character and identity to this precinct.",
            "The streetscapes display a mixture of architectural styles and scale of buildings.",
            "The row of elevated dwellings on Coleman Street in their leafy surroundings are "
            "unique in the city and contrast with the more formal character of the legal "
            "buildings.",
        ],
        "policies": [
            "Development in this precinct must relate sympathetically to surrounding neighbours "
            "and not overwhelm important individual heritage items.",
            "All development should be high quality, formal in character and use materials "
            "which harmonise with neighbouring sites.",
            "Owners of buildings in this precinct need to consider long term maintenance plans "
            "and management of key heritage items.",
            "Any advertising in this precinct should be restrained in colours, size and style "
            "consistent with the formal legal and religious character of the precinct.",
        ],
    },
    "girards_hill": {
        "lep_name": "Girards Hill Conservation Area",
        "heritage_map_label": "C3",
        "lep_significance": "Local",
        "dcp_heading": "GIRARDS HILL HERITAGE CONSERVATION AREA",
        "statement_of_significance": [
            "The Girards Hill precinct is notable as a diverse collection of houses unified by "
            "their consistent use of timber and iron. This consistent period feature "
            "distinguishes Lismore from other towns in the region which have lost much of this "
            "character, or which developed using quite different materials. The townscape value "
            "of the area also derives from the imposition of a modified street grid on a "
            "sloping hillside. This provides for dramatic siting of houses and enhances views "
            "into and out of the area. Narrow street pavements with grassed verges in many of "
            "the streets contribute to a strong perception of a semi rural urban from. This "
            "area features many fine buildings as well as good private gardens and trees. There "
            "are however, many unsympathetic intrusions. Regional Significance.",
        ],
        "characteristics": [
            "Residential in character, predominantly single storey featuring many significant "
            "individual buildings and groups of buildings from the 1880s to 1940s.",
            "Streetscapes have a strong identity created by the consistent use of weatherboards "
            "and corrugated metal roofing.",
            "A variety of roof forms consistent with the evolving architectural styles.",
            "Informal grassed verges combined with established shady street trees enhance the "
            "setting of the timber dwellings and provide amenity for residents.",
            "Widespread use of architectural detailing of timber joinery appropriate to the "
            "changing styles, e.g. bellcast weatherboards, brackets, valances, window hoods, and "
            "gable end trims.",
            "Timber picket fences and 1920-30s fences of timber beams and brick piers, and "
            "galvanised pipes define front boundaries.",
        ],
        "policies": [
            "Generally, all original timber homes should be maintained and conserved as they "
            "collectively make up the character of this precinct.",
            "The early workers cottages at the western end of Parkes Street are particularly "
            "important as they provide an important link to early life in the city. Any "
            "alterations must be carefully designed not to overwhelm the modest scale of these "
            "original buildings.",
            "Any proposals affecting significant or contributory buildings in this precinct "
            "which are not individually listed as heritage items in the Lismore LEP, (as they "
            "are included collectively in the Conservation Area), need to be considered in a "
            "similar manner to that of a heritage item.",
            "Any alterations or additions affecting buildings which are important as part of a "
            "group must maintain those elements which unite the buildings and retain the group "
            "value.",
            "Unsympathetic alterations should be reversed wherever possible in conjunction with "
            "development applications for other work.",
            "The unformed wide grass verges and street trees in Cathcart Street, James Street "
            "and others must be carefully retained. Intrusions should not be made into these "
            "verges to widen the road pavement, create sealed parking areas, or create wide "
            "driveway entrances.",
            "Well designed, high quality infill development which respects the scale, form, "
            "proportions and materials of the precinct will be favourably considered on sites "
            "which are not identified as significant or contributory.",
        ],
        "note": (
            "The chapter calls this area of Regional Significance; LEP Schedule 5 Part 2 lists "
            "it as Local. And the third policy treats contributory buildings 'in a similar "
            "manner to that of a heritage item' — a DCP assessment policy, which does not make "
            "such a building a heritage item for LEP cl 5.10(10)."
        ),
    },
    "nimbin": {
        "lep_name": "Nimbin Conservation Area",
        "heritage_map_label": "C7",
        "lep_significance": "Local",
        "dcp_heading": "NIMBIN VILLAGE HERITAGE CONSERVATION AREA",
        "statement_of_significance": [
            "The town and its setting have high local significance as a cultural landscape. "
            "There is a high degree of integrity, and abundant surviving evidence to demonstrate "
            "the process of village development. Unlike most other settlements in the study "
            "area, development is densely nucleated within the original survey boundaries. The "
            "main street is separately listed as a grouping. Local Significance.",
            "Outstanding streetscape located at the core of the Nimbin heritage conservation "
            "area. Unique in Australia. Colourful murals expressing New Age/Alternative themes "
            "symbolises the transformation of the local community following the 1973 Aquarius "
            "Festival. Aesthetically the colour gives new life to the Inter-war architecture, "
            "and signals the economic benefits brought about by the new rural population and "
            "increasing numbers of tourists. Illustrative of local theme of “Rural "
            "Renaissance.”",
            "Streetscape enhanced by topography and fork in the road, as well as new buildings "
            "continuing traditional forms. State Significance.",
        ],
        "characteristics": [
            "A unique main street with a ‘new age’ social and aesthetic character layered on a "
            "historic building stock.",
            "Traditional residential single storey, weatherboard and iron buildings, built "
            "mainly between 1910 and1930s.",
            "A defined edge to the village centre, surrounded by an outstanding landscape "
            "setting.",
            "Residential allotment sizes generally a minimum of 1000m2.",
        ],
        "also_applies": (
            "Chapter 6 (Nimbin Village) of Part B of this Development Control Plan applies to "
            "proposals in this Heritage Conservation Area."
        ),
        "policies": [
            "Restoration or reconstruction work in the heritage conservation area should be "
            "accurate to historical architectural details.",
            "Awnings may be replaced by verandahs on old buildings but must be appropriate to "
            "the age and style of the building. i.e. bullnose verandahs are not usually "
            "associated with 1920s and 1930s buildings. Use old photographs if available to "
            "provide details. Where cantilevered awnings are original, retain and repair where "
            "necessary.",
            "Use traditional elements in shop facades such as stall risers beneath windows. Do "
            "not introduce large modern plate glass windows to ground level. Retain recessed "
            "doorways, tiled entries, and original details.",
            "Colours on historic buildings need not be restricted to the heritage palette in "
            "this precinct owing to its unique visual character.",
            "Security shutters if required should be placed inside the shop to maintain the "
            "external character of the main street. External roller shutters are not "
            "considered compatible with the heritage significance of this precinct and should "
            "be avoided. Alternative measures such as security lighting, cameras, or alarms "
            "should be considered.",
            "Murals are a dynamic part of the streetscape and ongoing maintenance is required. "
            "New murals may be introduced within appropriate elements of a building in the main "
            "street precinct subject to development consent.",
            "The introduction of any new paving, planting and street furniture should be guided "
            "by a master plan developed in consultation with the local community.",
        ],
        "note": (
            "The chapter gives the main street State Significance; LEP Schedule 5 Part 2 lists "
            "the conservation area as Local. The 1000m2 is a description of existing lots among "
            "the area's characteristics, not a minimum lot size control — that comes from the "
            "LEP Minimum Lot Size Map. Nimbin is also the one area whose shopfront policies are "
            "specific: stall risers, no large plate glass, security shutters inside."
        ),
    },
    "eltham": {
        "lep_name": "Eltham Conservation Area",
        "heritage_map_label": "C2",
        "lep_significance": "Local",
        "dcp_heading": "ELTHAM HERITAGE CONSERVATION AREA",
        "statement_of_significance": [
            "Eltham Village is significant as a place of continuing activity by European "
            "occupation. Eltham, located in the centre of the now largely cleared Big Scrub, was "
            "a centre where timber getters harvested red cedar and hoop pine. The early timber "
            "getters camped in the grassland understorey of the subtropical rainforest and used "
            "the Wilsons River to float logs to nearby Boat Harbour where ships would convey "
            "logs to markets.",
        ],
        "characteristics": [
            "Open rural setting on rising land adjacent to Wilsons River.",
            "Roadside avenue of trees planted in honour of First World War service men.",
            "Surviving railway structures, including iron Pratt truss bridge over Wilsons River "
            "1891 – 94, railway tracks, gate keeper’s cottage, site of station as evidence of "
            "village.",
            "Large timber buildings constructed of local big scrub timbers including the "
            "Masonic Lodge, former Jubilee Hall, Eltham Village Gallery (general store) Hotel "
            "(modified).",
            "Weatherboard clad buildings with corrugated iron roofs.",
            "Low impact civil engineering grassed verges and table drains, gravel areas, basic "
            "sealed road widths.",
            "Informal landscaping.",
            "Modern housing of unobtrusive styles encompassing 20th century fashions.",
            "Surviving sections of calf sale yards.",
        ],
        "policies": [
            "Respect and retain quiet rural village setting and characteristics.",
            "Preserve surviving railway structures and archaeological sites.",
            "Retain roadside tree plantings.",
            "Owners of buildings in this precinct need to consider long term maintenance plans "
            "and management of key heritage items.",
            "Attempt to maintain low impact engineering works and structures.",
            "Development in this precinct must relate sympathetically to surrounding neighbours "
            "and not overwhelm important individual heritage items.",
        ],
        "note": (
            "The chapter's statement for Eltham runs to six paragraphs of settlement history; "
            "only the first, which states the significance, is carried here. The rest is in the "
            "chapter at §12.6."
        ),
    },
}

# Policies worded as a flat refusal rather than a preference. The selector finds
# them by these phrases in the stored quotes, and the audit checks each phrase
# still occurs in the chapter — so nothing can be reported as a refusal the
# chapter does not make.
REFUSAL_PHRASES = ("will not be approved", "will not be permitted", "should not be approved")
