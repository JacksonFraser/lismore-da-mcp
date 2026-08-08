"""Land use definitions, transcribed verbatim from the Lismore LEP 2012 Dictionary.

Which defined term a proposal falls under is the whole assessment. It decides
permissibility off the zone land use table, the DCP Chapter 7 parking rate, and
on a change of use whether a section 7.11 contribution is payable at all — shop
to cafe is nil and office to cafe is $12,310, because the first pair are both
retail premises and the second pair are not.

Until 2026-08-08 this file did not carry the definitions. It carried
paraphrases, written from memory, and its own docstring said so. They were
wrong in the way `data/standards.py` was wrong (item 0.6 of PLAN.md): plausible,
internally consistent, and colliding with a real figure somewhere else in the
LEP, which is what made them read as researched.

    warehouse or distribution centre    said "whether or not goods are sold by
                                        retail" — the LEP says "but from which
                                        no retail sales are made". Inverted
    neighbourhood shop                  said 80m2 retail floor area. The
                                        definition sets no area at all; clause
                                        5.4(7) sets 200m2
    business premises                   said "on 2+ days per week". That phrase
                                        appears nowhere in the LEP
    home business                       described home industry's conditions,
                                        and omitted the 2-employee allowance
                                        that makes the term usable
    boarding house                      omitted paragraphs (d) and (e) —
                                        affordable housing, managed by a
                                        registered community housing provider —
                                        which are the whole modern definition
    centre-based child care facility    excluded out-of-school-hours care, which
                                        paragraph (a)(iii) includes
    bed and breakfast accommodation     said "commonly 6" bedrooms; clause
                                        5.4(1) says no more than 5
    secondary dwelling                  said "typically 60m2"; clause 5.4(9)
                                        says the greater of 60m2 or 25% of the
                                        principal dwelling
    attached dwellings                  described private open space and
                                        separate access; the LEP's test is
                                        separate lots and nothing above
    residential flat building           described access by common corridors,
                                        which the definition does not mention
    hotel or motel accommodation        required dining and communal space; the
                                        LEP makes meals optional
    vehicle repair station              excluded tyre sales; the LEP excludes
                                        vehicle sales or hire premises
    light/general industries,           are `light industry`, `general industry`
    attached dwellings                  and `attached dwelling` in the
                                        Dictionary — the plural is the land use
                                        table's spelling, carried separately

Three rules hold this file together.

**The definition is quoted, never summarised.** `definition` is the LEP text
verbatim, paragraph numbering included, and `scripts/audit_definitions.py`
checks every one of them still appears in `documents/lep/lep-2012-nsw-full.txt`.
Anything that is not the LEP's words goes in `why_this_matters`, which is
labelled as guidance in the tool output and is not part of the definition.

**A number in a definition is almost always in the wrong place.** The
Dictionary defines terms; the numeric controls live in clause 5.4, and every
invented figure above was a real control filed under the wrong provision.
`additional_controls` carries clause 5.4 verbatim where it applies, so the
figure has a citation an applicant can quote. `FIGURES_NOT_IN_THE_DEFINITION`
records the four the old file invented, because a presence-checking audit only
looks at what is stored and is structurally blind to invention — item 0.6's
lesson.

**The Dictionary term and the land use table term are not always the same
word.** The table says "Light industries", "Attached dwellings" and "Recreation
facilities (indoor)"; the Dictionary defines the singular. `check_permissibility`
matches the table, so `land_use_table_term` carries the plural wherever it
differs and the audit checks it against `data/zones.py`.
"""

LAND_USE_DEFINITIONS = {
    "retail_premises": {
        "term": 'retail premises',
        "definition": (
            'retail premises means a building or place used for the purpose of selling items by retail, or hiring or displaying items for the purpose of selling them or hiring them out, whether the items are goods or materials (or whether also sold by wholesale), and includes any of the following—\n'
            '(a), (b)    (Repealed)\n'
            '(c)  food and drink premises,\n'
            '(d)  garden centres,\n'
            '(e)  hardware and building supplies,\n'
            '(f)  kiosks,\n'
            '(g)  landscaping material supplies,\n'
            '(h)  markets,\n'
            '(i)  plant nurseries,\n'
            '(j)  roadside stalls,\n'
            '(k)  rural supplies,\n'
            '(l)  shops,\n'
            '(la)  specialised retail premises,\n'
            '(m)  timber yards,\n'
            '(n)  vehicle sales or hire premises,\n'
            'but does not include farm gate premises, highway service centres, service stations, industrial retail outlets or restricted premises.'
        ),
        "lep_note": (
            'Retail premises are a type of commercial premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['shop', 'food_and_drink_premises', 'commercial_premises', 'specialised_retail_premises'],
    },
    "food_and_drink_premises": {
        "term": 'food and drink premises',
        "definition": (
            'food and drink premises means premises that are used for the preparation and retail sale of food or drink (or both) for immediate consumption on or off the premises, and includes any of the following—\n'
            '(a)  a restaurant or cafe,\n'
            '(b)  take away food and drink premises,\n'
            '(c)  a pub,\n'
            '(d)  a small bar.'
        ),
        "lep_note": (
            'Food and drink premises are a type of retail premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['restaurant_or_cafe', 'take_away_food_and_drink_premises', 'pub', 'retail_premises'],
        "why_this_matters": (
            "Most Lismore zone land use tables list 'Food and drink premises' rather than "
            "'Restaurant or cafe'. Permissibility is usually decided at this level; the "
            'parking rate and the section 7.11 contribution are decided at the more specific '
            'one.'
        ),
    },
    "shop": {
        "term": 'shop',
        "definition": (
            'shop means premises that sell merchandise such as groceries, personal care products, clothing, music, homewares, stationery, electrical goods or the like or that hire any such merchandise, and includes a neighbourhood shop and neighbourhood supermarket, but does not include food and drink premises or restricted premises.'
        ),
        "lep_note": (
            'Shops are a type of retail premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['retail_premises', 'neighbourhood_shop', 'food_and_drink_premises'],
        "why_this_matters": (
            'Shop and food and drink premises are mutually exclusive — the definition of shop '
            'excludes food and drink premises outright. Which one a proposal is decides the '
            'DCP Chapter 7 parking rate and, on a change of use, whether a section 7.11 '
            'contribution is payable at all: shop to cafe is nil, because both are retail '
            'premises.'
        ),
    },
    "restaurant_or_cafe": {
        "term": 'restaurant or cafe',
        "definition": (
            'restaurant or cafe means a building or place the principal purpose of which is the preparation and serving, on a retail basis, of food and drink to people for consumption on the premises, whether or not liquor, take away meals and drinks or entertainment are also provided, but does not include the preparation and serving of food and drink to people that occurs as part of—\n'
            '(a)  an artisan food and drink industry, or\n'
            '(b)  farm gate premises.'
        ),
        "lep_note": (
            'Restaurants or cafes are a type of food and drink premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['food_and_drink_premises', 'take_away_food_and_drink_premises', 'artisan_food_and_drink_industry'],
        "why_this_matters": (
            'The test is the principal purpose — preparation and serving for consumption on '
            'the premises. The definition says nothing about seating, so a venue is not taken '
            'out of this term by having few seats. DCP Chapter 7 does price the requirement '
            'per seat, but that is the parking rate, not the definition.'
        ),
    },
    "take_away_food_and_drink_premises": {
        "term": 'take away food and drink premises',
        "definition": (
            'take away food and drink premises means premises that are predominantly used for the preparation and retail sale of food or drink (or both) for immediate consumption away from the premises.'
        ),
        "lep_note": (
            'Take away food and drink premises are a type of food and drink premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['food_and_drink_premises', 'restaurant_or_cafe'],
    },
    "pub": {
        "term": 'pub',
        "definition": (
            'pub means licensed premises under the Liquor Act 2007 the principal purpose of which is the retail sale of liquor for consumption on the premises, whether or not the premises include hotel or motel accommodation and whether or not food is sold or entertainment is provided on the premises.'
        ),
        "lep_note": (
            'Pubs are a type of food and drink premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['food_and_drink_premises', 'hotel_or_motel_accommodation'],
        "why_this_matters": (
            'A pub is a food and drink premises, not tourist and visitor accommodation, even '
            'where it has rooms upstairs — hotel or motel accommodation is a separate term '
            'with a separate permissibility. Check the land use table for both if the '
            'proposal does both.'
        ),
    },
    "business_premises": {
        "term": 'business premises',
        "definition": (
            'business premises means a building or place at or on which—\n'
            '(a)  an occupation, profession or trade (other than an industry) is carried on for the provision of services directly to members of the public on a regular basis, or\n'
            '(b)  a service is provided directly to members of the public on a regular basis,\n'
            'and includes funeral homes, goods repair and reuse premises and, without limitation, premises such as banks, post offices, hairdressers, dry cleaners, travel agencies, betting agencies and the like, but does not include an entertainment facility, home business, home occupation, home occupation (sex services), medical centre, restricted premises, sex services premises or veterinary hospital.'
        ),
        "lep_note": (
            'Business premises are a type of commercial premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['commercial_premises', 'office_premises', 'retail_premises'],
        "why_this_matters": (
            'The dividing line from office premises is whether the public is dealt with at '
            'the premises on a direct and regular basis. A hairdresser, travel agent or dry '
            'cleaner is business premises; an accountant seeing clients only by appointment '
            'is office premises.'
        ),
    },
    "office_premises": {
        "term": 'office premises',
        "definition": (
            'office premises means a building or place used for the purpose of administrative, clerical, technical, professional or similar activities that do not include dealing with members of the public at the building or place on a direct and regular basis, except where such dealing is a minor activity (by appointment) that is ancillary to the main purpose for which the building or place is used.'
        ),
        "lep_note": (
            'Office premises are a type of commercial premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['commercial_premises', 'business_premises'],
    },
    "commercial_premises": {
        "term": 'commercial premises',
        "definition": (
            'commercial premises means any of the following—\n'
            '(a)  business premises,\n'
            '(b)  office premises,\n'
            '(c)  retail premises.'
        ),
        "related_terms": ['business_premises', 'office_premises', 'retail_premises'],
        "why_this_matters": (
            "An umbrella term covering all three. Where a zone permits 'Commercial premises' "
            'it permits each of them; where it lists only some, the specific term governs.'
        ),
    },
    "neighbourhood_shop": {
        "term": 'neighbourhood shop',
        "definition": (
            'neighbourhood shop means premises used for the purposes of selling general merchandise such as foodstuffs, personal care products, newspapers and the like to provide for the day-to-day needs of people who live or work in the local area, but does not include neighbourhood supermarkets or restricted premises.'
        ),
        "lep_note": (
            'See clause 5.4 for controls relating to the retail floor area of neighbourhood shops. Neighbourhood shops are a type of shop—see the definition of that term in this Dictionary.'
        ),
        "additional_controls": {
            "source": 'Lismore LEP 2012 clause 5.4(7)',
            "control": (
                '(7) Neighbourhood shops If development for the purposes of a neighbourhood shop is permitted under this Plan, the retail floor area must not exceed 200 square metres.'
            ),
        },
        "related_terms": ['shop', 'retail_premises'],
        "why_this_matters": (
            'A neighbourhood shop is permissible in some zones where a general shop is not, '
            'which is why the retail floor area cap in clause 5.4 matters — exceeding it '
            'makes the proposal a shop.'
        ),
    },
    "specialised_retail_premises": {
        "term": 'specialised retail premises',
        "definition": (
            'specialised retail premises means a building or place the principal purpose of which is the sale, hire or display of goods that are of a size, weight or quantity, that requires—\n'
            '(a)  a large area for handling, display or storage, or\n'
            '(b)  direct vehicular access to the site of the building or place by members of the public for the purpose of loading or unloading such goods into or from their vehicles after purchase or hire,\n'
            'but does not include a building or place used for the sale of foodstuffs or clothing unless their sale is ancillary to the sale, hire or display of other goods referred to in this definition.'
        ),
        "lep_note": (
            'Examples of goods that may be sold at specialised retail premises include automotive parts and accessories, household appliances and fittings, furniture, homewares, office equipment, outdoor and recreation equipment, pet supplies and party supplies. Specialised retail premises are a type of retail premises—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['retail_premises'],
        "why_this_matters": (
            "This is the current term for what the DCP and older instruments call 'bulky "
            "goods premises'. DCP Chapter 7 Schedule 1 still uses the old name for its "
            'parking rate.'
        ),
    },
    "medical_centre": {
        "term": 'medical centre',
        "definition": (
            'medical centre means premises that are used for the purpose of providing health services (including preventative care, diagnosis, medical or surgical treatment, counselling or alternative therapies) to out-patients only, where such services are principally provided by health care professionals. It may include the ancillary provision of other health services.'
        ),
        "lep_note": (
            'Medical centres are a type of health services facility—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['business_premises'],
        "why_this_matters": (
            'Expressly excluded from business premises, so a zone permitting business '
            'premises does not thereby permit a medical centre. It carries its own parking '
            'rate.'
        ),
    },
    "home_business": {
        "term": 'home business',
        "definition": (
            'home business means a business, whether or not involving the sale of items online, carried on in a dwelling, or in a building ancillary to a dwelling, by 1 or more permanent residents of the dwelling and not involving the following—\n'
            '(a)  the employment of more than 2 persons other than the residents,\n'
            '(b)  interference with the amenity of the neighbourhood because of the emission of noise, vibration, smell, fumes, smoke, vapour, steam, soot, ash, dust, waste water, waste products, grit or oil, traffic generation or otherwise,\n'
            '(c)  the exposure to view, from adjacent premises or from a public place, of unsightly matter,\n'
            '(d)  the exhibition of signage, other than a business identification sign,\n'
            '(e)  the retail sale of, or the exposure or offer for retail sale of, items, whether goods or materials, not produced at the dwelling or building, other than by online retailing,\n'
            'but does not include bed and breakfast accommodation, home occupation (sex services) or sex services premises.'
        ),
        "lep_note": 'See clause 5.4 for controls relating to the floor area used for a home business.',
        "additional_controls": {
            "source": 'Lismore LEP 2012 clause 5.4(2)',
            "control": (
                '(2) Home businesses If development for the purposes of a home business is permitted under this Plan, the carrying on of the business must not involve the use of more than 50 square metres of floor area.'
            ),
        },
        "related_terms": ['home_occupation', 'home_industry'],
        "why_this_matters": (
            'The workable option for a business run from home: up to 2 employees other than '
            'the residents, and a business identification sign is allowed. Clause 5.4 caps '
            'the floor area used.'
        ),
    },
    "home_occupation": {
        "term": 'home occupation',
        "definition": (
            'home occupation means an occupation that is carried on in a dwelling, or in a building ancillary to a dwelling, by one or more permanent residents of the dwelling and that does not involve—\n'
            '(a)  the employment of persons other than those residents, or\n'
            '(b)  interference with the amenity of the neighbourhood by reason of the emission of noise, vibration, smell, fumes, smoke, vapour, steam, soot, ash, dust, waste water, waste products, grit or oil, traffic generation or otherwise, or\n'
            '(c)  the display of goods, whether in a window or otherwise, or\n'
            '(d)  the exhibition of any signage (other than a business identification sign), or\n'
            '(e)  the sale of items (whether goods or materials), or the exposure or offer for sale of items, by retail,\n'
            'but does not include bed and breakfast accommodation, home occupation (sex services) or sex services premises.'
        ),
        "related_terms": ['home_business', 'home_industry'],
        "why_this_matters": (
            'Narrower than home business — no employees other than the residents at all, and '
            'no display of goods. It is permitted without consent in most residential zones, '
            'which home business generally is not, so the narrower term is often the one '
            'worth fitting into.'
        ),
    },
    "home_industry": {
        "term": 'home industry',
        "definition": (
            'home industry means an industrial activity, whether or not involving the sale of items online, carried on in a dwelling, or in a building ancillary to a dwelling, by 1 or more permanent residents of the dwelling and not involving the following—\n'
            '(a)  the employment of more than 2 persons other than the residents,\n'
            '(b)  interference with the amenity of the neighbourhood because of the emission of noise, vibration, smell, fumes, smoke, vapour, steam, soot, ash, dust, waste water, waste products, grit or oil, traffic generation or otherwise,\n'
            '(c)  the exposure to view, from adjacent premises or from a public place, of unsightly matter,\n'
            '(d)  the exhibition of signage, other than a business identification sign,\n'
            '(e)  the retail sale of, or the exposure or offer for retail sale of, items, whether goods or materials, not produced at the dwelling or building, other than by online retailing,\n'
            'but does not include bed and breakfast accommodation or sex services premises.'
        ),
        "lep_note": (
            'See clause 5.4 for controls relating to the floor area used for a home industry. Home industries are a type of light industry—see the definition of that term in this Dictionary.'
        ),
        "additional_controls": {
            "source": 'Lismore LEP 2012 clause 5.4(3)',
            "control": (
                '(3) Home industries If development for the purposes of a home industry is permitted under this Plan, the carrying on of the home industry must not involve the use of more than 60 square metres of floor area.'
            ),
        },
        "related_terms": ['home_business', 'light_industries'],
        "why_this_matters": (
            'An industrial activity rather than a business, and a type of light industry — so '
            'it is permissible in different zones from home business despite near-identical '
            'conditions.'
        ),
    },
    "residential_accommodation": {
        "term": 'residential accommodation',
        "definition": (
            'residential accommodation means a building or place used predominantly as a place of residence, and includes any of the following—\n'
            '(a)  attached dwellings,\n'
            '(b)  boarding houses,\n'
            '(baa)  co-living housing,\n'
            '(c)  dual occupancies,\n'
            '(d)  dwelling houses,\n'
            '(e)  group homes,\n'
            '(f)  hostels,\n'
            '(faa)    (Repealed)\n'
            '(g)  multi dwelling housing,\n'
            '(h)  residential flat buildings,\n'
            '(i)  rural workers’ dwellings,\n'
            '(j)  secondary dwellings,\n'
            '(k)  semi-detached dwellings,\n'
            '(l)  seniors housing,\n'
            '(m)  shop top housing,\n'
            'but does not include tourist and visitor accommodation or caravan parks.'
        ),
        "related_terms": ['dwelling_house', 'shop_top_housing', 'boarding_house'],
    },
    "dwelling_house": {
        "term": 'dwelling house',
        "definition": 'dwelling house means a building containing only one dwelling.',
        "lep_note": (
            'Dwelling houses are a type of residential accommodation—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['residential_accommodation', 'dual_occupancy', 'secondary_dwelling'],
    },
    "dual_occupancy": {
        "term": 'dual occupancy',
        "definition": 'dual occupancy means a dual occupancy (attached) or a dual occupancy (detached).',
        "lep_note": (
            'Dual occupancies are a type of residential accommodation—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['dwelling_house', 'secondary_dwelling', 'residential_accommodation'],
        "why_this_matters": (
            'A dual occupancy is two dwellings of equal standing. A dwelling house with a '
            'secondary dwelling is not a dual occupancy — it is a separate term with a floor '
            'area cap and, under DCP Chapter 1, no additional parking requirement. The two '
            'are commonly confused and are not interchangeable.'
        ),
    },
    "secondary_dwelling": {
        "term": 'secondary dwelling',
        "definition": (
            'secondary dwelling means a self-contained dwelling that—\n'
            '(a)  is established in conjunction with another dwelling (the principal dwelling), and\n'
            '(b)  is on the same lot of land as the principal dwelling, and\n'
            '(c)  is located within, or is attached to, or is separate from, the principal dwelling.'
        ),
        "lep_note": (
            'See clauses 5.4 and 5.5 for controls relating to the total floor area of secondary dwellings. Secondary dwellings are a type of residential accommodation—see the definition of that term in this Dictionary.'
        ),
        "additional_controls": {
            "source": 'Lismore LEP 2012 clause 5.4(9)',
            "control": (
                '(9) Secondary dwellings on land other than land in a rural zone If development for the purposes of a secondary dwelling is permitted under this Plan on land other than land in a rural zone, the total floor area of the dwelling, excluding any area used for parking, must not exceed whichever of the following is the greater—\n'
                '(a)  60 square metres,\n'
                '(b)  25% of the total floor area of the principal dwelling.'
            ),
        },
        "related_terms": ['dwelling_house', 'dual_occupancy', 'residential_accommodation'],
        "why_this_matters": (
            'The granny flat. Absent from several Lismore residential land use tables but '
            'generally permissible under the Housing SEPP, which prevails over the LEP — '
            'never report a table miss as a refusal. Clause 5.4(9) caps the floor area, and '
            'clause 4.6 cannot vary that cap.'
        ),
    },
    "multi_dwelling_housing": {
        "term": 'multi dwelling housing',
        "definition": (
            'multi dwelling housing means 3 or more dwellings (whether attached or detached) on one lot of land, each with access at ground level, but does not include a residential flat building.'
        ),
        "lep_note": (
            'Multi dwelling housing is a type of residential accommodation—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['attached_dwellings', 'residential_flat_building'],
    },
    "residential_flat_building": {
        "term": 'residential flat building',
        "definition": (
            'residential flat building means a building containing 3 or more dwellings, but does not include an attached dwelling, co-living housing or multi dwelling housing.'
        ),
        "lep_note": (
            'Residential flat buildings are a type of residential accommodation—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['multi_dwelling_housing', 'attached_dwellings', 'shop_top_housing'],
        "why_this_matters": (
            'The LEP distinguishes it from multi dwelling housing and attached dwellings by '
            'exclusion rather than by how the dwellings are reached. Ground level access to '
            'each dwelling is what makes something multi dwelling housing; separate lots are '
            'what make it attached dwellings.'
        ),
    },
    "attached_dwellings": {
        "term": 'attached dwelling',
        "land_use_table_term": 'Attached dwellings',
        "definition": (
            'attached dwelling means a building containing 3 or more dwellings, where—\n'
            '(a)  each dwelling is attached to another dwelling by a common wall, and\n'
            '(b)  each of the dwellings is on its own lot of land, and\n'
            '(c)  none of the dwellings is located above any part of another dwelling.'
        ),
        "lep_note": (
            'Attached dwellings are a type of residential accommodation—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['multi_dwelling_housing', 'residential_flat_building'],
    },
    "shop_top_housing": {
        "term": 'shop top housing',
        "definition": (
            'shop top housing means one or more dwellings located above the ground floor of a building, where at least the ground floor is used for commercial premises or health services facilities.'
        ),
        "lep_note": (
            'Shop top housing is a type of residential accommodation—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['residential_flat_building', 'commercial_premises'],
        "why_this_matters": (
            'The housing type a business in a centre zone is most likely to be building. DCP '
            'Chapter 7 requires no parking for shop top housing in the Lismore CBD.'
        ),
    },
    "boarding_house": {
        "term": 'boarding house',
        "definition": (
            'boarding house means a building or place—\n'
            '(a)  that provides residents with a principal place of residence for at least 3 months, and\n'
            '(b)  that contains shared facilities, such as a communal living room, bathroom, kitchen or laundry, and\n'
            '(c)  that contains rooms, some or all of which may have private kitchen and bathroom facilities, and\n'
            '(d)  used to provide affordable housing, and\n'
            '(e)  if not carried out by or on behalf of the Land and Housing Corporation—managed by a registered community housing provider,\n'
            'but does not include backpackers’ accommodation, co-living housing, a group home, hotel or motel accommodation, seniors housing or a serviced apartment.'
        ),
        "related_terms": ['residential_accommodation'],
        "why_this_matters": (
            'Paragraphs (d) and (e) are the whole of the modern definition: it must provide '
            'affordable housing and, in most cases, be managed by a registered community '
            'housing provider. A private lodging house that meets (a) to (c) alone is not a '
            'boarding house under this Plan.'
        ),
    },
    "industry": {
        "term": 'industry',
        "definition": (
            'industry means any of the following—\n'
            '(a)  general industry,\n'
            '(b)  heavy industry,\n'
            '(c)  light industry,\n'
            'but does not include—\n'
            '(d)  rural industry, or\n'
            '(e)  extractive industry, or\n'
            '(f)  mining.'
        ),
        "related_terms": ['light_industries', 'general_industries'],
    },
    "light_industries": {
        "term": 'light industry',
        "land_use_table_term": 'Light industries',
        "definition": (
            'light industry means a building or place used to carry out an industrial activity that does not interfere with the amenity of the neighbourhood by reason of noise, vibration, smell, fumes, smoke, vapour, steam, soot, ash, dust, waste water, waste products, grit or oil, or otherwise, and includes any of the following—\n'
            '(a)  high technology industry,\n'
            '(b)  home industry,\n'
            '(c)  artisan food and drink industry,\n'
            '(d)  creative industry.'
        ),
        "lep_note": (
            'Light industries are a type of industry—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['industry', 'general_industries', 'artisan_food_and_drink_industry', 'home_industry'],
    },
    "general_industries": {
        "term": 'general industry',
        "land_use_table_term": 'General industries',
        "definition": (
            'general industry means a building or place (other than a heavy industry or light industry) that is used to carry out an industrial activity.'
        ),
        "lep_note": (
            'General industries are a type of industry—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['industry', 'light_industries'],
    },
    "artisan_food_and_drink_industry": {
        "term": 'artisan food and drink industry',
        "definition": (
            'artisan food and drink industry means a building or place the principal purpose of which is the making or manufacture of boutique, artisan or craft food or drink products only. It must also include at least one of the following—\n'
            '(a)  a retail area for the sale of the products,\n'
            '(b)  the preparation and serving, on a retail basis, of food and drink to people for consumption on the premises, whether or not liquor, take away meals and drinks or entertainment are also provided,\n'
            '(c)  facilities for holding tastings, tours or workshops.'
        ),
        "lep_note": (
            'See clause 5.4 for controls in certain zones relating to the retail floor area of an artisan food and drink industry. Artisan food and drink industries are a type of light industry—see the definition of that term in this Dictionary.'
        ),
        "additional_controls": {
            "source": 'Lismore LEP 2012 clause 5.4(10)',
            "control": (
                '(10) Artisan food and drink industry exclusion If development for the purposes of an artisan food and drink industry is permitted under this Plan in Zone E3 Productivity Support, Zone E4 General Industrial, Zone E5 Heavy Industrial, Zone W4 Working Waterfront or a rural zone, the floor area used for retail sales (not including any cafe or restaurant area) must not exceed—\n'
                '(a)  30% of the gross floor area of the industry, or\n'
                '(b)  400 square metres,\n'
                'whichever is the lesser.'
            ),
        },
        "related_terms": ['light_industries', 'restaurant_or_cafe', 'food_and_drink_premises'],
        "why_this_matters": (
            'A brewery, distillery, roastery or bakery with a tasting room or cafe attached. '
            'It is a type of light industry, not a food and drink premises, so it is '
            'permissible in industrial zones where a cafe is not — and a cafe operating '
            'inside one is expressly carved out of the restaurant or cafe definition. Clause '
            '5.4(10) caps the retail floor area in E3, E4, E5 and rural zones.'
        ),
    },
    "warehouse_or_distribution_centre": {
        "term": 'warehouse or distribution centre',
        "definition": (
            'warehouse or distribution centre means a building or place used mainly or exclusively for storing or handling items (whether goods or materials) pending their sale, but from which no retail sales are made, but does not include local distribution premises.'
        ),
        "related_terms": ['light_industries', 'general_industries'],
        "why_this_matters": (
            'No retail sales may be made from it. A warehouse proposing to sell to the public '
            'is a different use — usually an industrial retail outlet or specialised retail '
            "premises — and self-storage is 'self-storage units', a separate term."
        ),
    },
    "vehicle_repair_station": {
        "term": 'vehicle repair station',
        "definition": (
            'vehicle repair station means a building or place used for the purpose of carrying out repairs to, or the selling and fitting of accessories to, vehicles or agricultural machinery, but does not include a vehicle body repair workshop or vehicle sales or hire premises.'
        ),
        "related_terms": ['light_industries'],
    },
    "recreation_facility_indoor": {
        "term": 'recreation facility (indoor)',
        "land_use_table_term": 'Recreation facilities (indoor)',
        "definition": (
            'recreation facility (indoor) means a building or place used predominantly for indoor recreation, whether or not operated for the purposes of gain, including a squash court, indoor swimming pool, gymnasium, table tennis centre, health studio, bowling alley, ice rink or any other building or place of a like character used for indoor recreation, but does not include an entertainment facility, a recreation facility (major) or a registered club.'
        ),
        "related_terms": ['community_facility'],
        "why_this_matters": (
            'Covers a gym, health studio or indoor pool. A registered club and an '
            'entertainment facility are excluded and are separate terms.'
        ),
    },
    "community_facility": {
        "term": 'community facility',
        "definition": (
            'community facility means a building or place—\n'
            '(a)  owned or controlled by a public authority or non-profit community organisation, and\n'
            '(b)  used for the physical, social, cultural or intellectual development or welfare of the community,\n'
            'but does not include an educational establishment, hospital, retail premises, place of public worship or residential accommodation.'
        ),
        "related_terms": ['recreation_facility_indoor'],
        "why_this_matters": (
            'Requires public authority or non-profit ownership or control. A privately run '
            'hall or meeting space is not a community facility.'
        ),
    },
    "centre_based_child_care_facility": {
        "term": 'centre-based child care facility',
        "definition": (
            'centre-based child care facility means—\n'
            '(a)  a building or place used for the education and care of children that provides any one or more of the following—\n'
            '(i)  long day care,\n'
            '(ii)  occasional child care,\n'
            '(iii)  out-of-school-hours care (including vacation care),\n'
            '(iv)  preschool care, or\n'
            '(b)  an approved family day care venue (within the meaning of the Children (Education and Care Services) National Law (NSW)),\n'
            'Note.\n'
            'An approved family day care venue is a place, other than a residence, where an approved family day care service (within the meaning of the Children (Education and Care Services) National Law (NSW)) is provided.\n'
            'but does not include—\n'
            '(c)  a building or place used for home-based child care or school-based child care, or\n'
            '(d)  an office of a family day care service (within the meanings of the Children (Education and Care Services) National Law (NSW)), or\n'
            '(e)  a babysitting, playgroup or child-minding service that is organised informally by the parents of the children concerned, or\n'
            '(f)  a child-minding service that is provided in connection with a recreational or commercial facility (such as a gymnasium) to care for children while the children’s parents are using the facility, or\n'
            '(g)  a service that is concerned primarily with providing lessons or coaching in, or providing for participation in, a cultural, recreational, religious or sporting activity, or providing private tutoring, or\n'
            '(h)  a child-minding service that is provided by or in a health services facility, but only if the service is established, registered or licensed as part of the institution operating in the facility.'
        ),
        "lep_note": (
            'Centre-based child care facilities are a type of early education and care facility—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['community_facility'],
        "why_this_matters": (
            'Out-of-school-hours care is inside this term, at paragraph (a)(iii). What is '
            'excluded is school-based child care, home-based child care, and creche-style '
            "minding provided at a gym for customers' children while they use it — paragraph "
            '(f), which a gym proposing a creche should read.'
        ),
    },
    "tourist_and_visitor_accommodation": {
        "term": 'tourist and visitor accommodation',
        "definition": (
            'tourist and visitor accommodation means a building or place that provides temporary or short-term accommodation on a commercial basis, and includes any of the following—\n'
            '(a)  backpackers’ accommodation,\n'
            '(b)  bed and breakfast accommodation,\n'
            '(c)  farm stay accommodation,\n'
            '(d)  hotel or motel accommodation,\n'
            '(e)  serviced apartments,\n'
            'but does not include—\n'
            '(f)  camping grounds, or\n'
            '(g)  caravan parks, or\n'
            '(h)  eco-tourist facilities.'
        ),
        "related_terms": ['hotel_or_motel_accommodation', 'bed_and_breakfast_accommodation'],
    },
    "hotel_or_motel_accommodation": {
        "term": 'hotel or motel accommodation',
        "definition": (
            'hotel or motel accommodation means a building or place (whether or not licensed premises under the Liquor Act 2007) that provides temporary or short-term accommodation on a commercial basis and that—\n'
            '(a)  comprises rooms or self-contained suites, and\n'
            '(b)  may provide meals to guests or the general public and facilities for the parking of guests’ vehicles,\n'
            'but does not include backpackers’ accommodation, a boarding house, bed and breakfast accommodation or farm stay accommodation.'
        ),
        "lep_note": (
            'Hotel or motel accommodation is a type of tourist and visitor accommodation—see the definition of that term in this Dictionary.'
        ),
        "related_terms": ['tourist_and_visitor_accommodation', 'pub', 'bed_and_breakfast_accommodation'],
    },
    "bed_and_breakfast_accommodation": {
        "term": 'bed and breakfast accommodation',
        "definition": (
            'bed and breakfast accommodation means an existing dwelling in which temporary or short-term accommodation is provided on a commercial basis by the permanent residents of the dwelling and where—\n'
            '(a)  meals are provided for guests only, and\n'
            '(b)  cooking facilities for the preparation of meals are not provided within guests’ rooms, and\n'
            '(c)  dormitory-style accommodation is not provided.'
        ),
        "lep_note": (
            'See clause 5.4 for controls relating to the number of bedrooms for bed and breakfast accommodation. Bed and breakfast accommodation is a type of tourist and visitor accommodation—see the definition of that term in this Dictionary.'
        ),
        "additional_controls": {
            "source": 'Lismore LEP 2012 clause 5.4(1)',
            "control": (
                '(1) Bed and breakfast accommodation If development for the purposes of bed and breakfast accommodation is permitted under this Plan, the accommodation that is provided to guests must consist of no more than 5 bedrooms.\n'
                'Note.\n'
                'Any such development that provides for a certain number of guests or rooms may involve a change in the class of building under the Building Code of Australia.'
            ),
        },
        "related_terms": ['tourist_and_visitor_accommodation', 'hotel_or_motel_accommodation'],
        "why_this_matters": (
            'It must be the permanent residents providing it, in an existing dwelling. A '
            'whole house let out while the owners are elsewhere is not bed and breakfast '
            'accommodation — that is short-term rental accommodation, governed by a State '
            'policy this repository does not carry. Ask the Duty Planner before assuming a '
            'short-term letting fits this term.'
        ),
    },
}


# The figures the pre-2026-08-08 paraphrases asserted, and where the real
# control lives. Every one of them was a number that exists in the LEP, filed
# against the wrong provision — which is exactly why they survived review.
#
# This mirrors NOT_SET_BY_THIS_CHAPTER in data/standards.py, and exists for the
# same reason: audit_definitions.py presence-checks what is stored, so it can
# only ever catch a quote that has drifted. It cannot catch a sentence somebody
# made up. Asserting the absences is the check that can.
#
# `must_not_contain` is what makes the check work, and the first version of it
# did not. It searched the definition for the *old wording* — "80m²" — so
# reinventing the identical control as "80 square metres" passed silently. A
# reinvention is written in fresh words by definition. So each record names the
# **kind** of figure the definition does not set, as a pattern, and the audit
# asserts no figure of that kind appears at all. Numbers the definitions do
# legitimately contain ("3 or more dwellings", "more than 2 persons", "at least
# 3 months") are untouched, because the patterns are scoped to a unit.
FIGURES_NOT_IN_THE_DEFINITION = {
    "neighbourhood_shop": {
        "was_claimed": "retail floor area of not more than 80m²",
        "absent_from": "the definition of neighbourhood shop, which sets no floor area",
        "must_not_contain": [(r"\d+\s*(?:m²|m2|square metres|sqm)", "a floor area")],
        "real_control": "200 square metres of retail floor area",
        "source": "Lismore LEP 2012 clause 5.4(7)",
    },
    "secondary_dwelling": {
        "was_claimed": "maximum floor area (typically 60m² — check current SEPP)",
        "absent_from": "the definition of secondary dwelling, which sets no floor area",
        "must_not_contain": [(r"\d+\s*(?:m²|m2|square metres|sqm)", "a floor area")],
        "real_control": (
            "the greater of 60 square metres or 25% of the total floor area of the principal "
            "dwelling, excluding any area used for parking"
        ),
        "source": "Lismore LEP 2012 clause 5.4(9)",
    },
    "bed_and_breakfast_accommodation": {
        "was_claimed": "typically limited number of guests (commonly 6)",
        "absent_from": "the definition, which limits neither guests nor bedrooms",
        "must_not_contain": [(r"\d+\s*(?:bedrooms?|guests?)", "a bedroom or guest limit")],
        "real_control": "no more than 5 bedrooms provided to guests",
        "source": "Lismore LEP 2012 clause 5.4(1)",
    },
    "home_business": {
        "was_claimed": (
            "does not involve the manufacture, alteration, servicing or repair of items other "
            "than items used in the business"
        ),
        "absent_from": (
            "the definition of home business — this is a paraphrase of home industry, a "
            "different term with a different permissibility. Note the definition does set an "
            "employee limit of 2, so only the floor area is asserted absent here."
        ),
        "must_not_contain": [(r"\d+\s*(?:m²|m2|square metres|sqm)", "a floor area")],
        "real_control": "50 square metres of floor area used for the business",
        "source": "Lismore LEP 2012 clause 5.4(2)",
    },
}

# Walking a use up to the broader terms that may carry it, for a land use table
# that lists the parent but not the child.
#
# The chains are the LEP's own — each Dictionary entry ends in a note reading
# "X are a type of Y", and audit_definitions.py reads those notes off the
# document and checks the first link of every chain against them. That check
# found one error here: office premises was recorded as a type of business
# premises. It is not. Both are types of commercial premises, and they are
# mutually exclusive — the test is whether the public is dealt with at the
# premises directly and regularly.
#
# Entries whose key is not itself a defined term (cafe, takeaway, gym, factory)
# are everyday words, and their first link is the term to use in a DA.
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
    "specialised retail premises": ["retail premises", "commercial premises"],
    "retail premises": ["commercial premises"],
    # Business and office. These two are siblings, not parent and child.
    "office premises": ["commercial premises"],
    "office": ["office premises", "commercial premises"],
    "business premises": ["commercial premises"],
    # Industry
    "light industry": ["industry"],
    "general industry": ["industry"],
    "home industry": ["light industry", "industry"],
    "artisan food and drink industry": ["light industry", "industry"],
    "brewery": ["artisan food and drink industry", "light industry", "industry"],
    "distillery": ["artisan food and drink industry", "light industry", "industry"],
    # Recreation
    "gym": ["recreation facility (indoor)", "recreation facilities (indoor)"],
    "gymnasium": ["recreation facility (indoor)", "recreation facilities (indoor)"],
    "fitness centre": ["recreation facility (indoor)", "recreation facilities (indoor)"],
}

CATCHALL_TERM = "any other development not specified"


# Groupings for list_definitions. This lived in the handler as a literal, which
# meant adding nine terms to this file left them out of the listing without
# failing anything — the same shape as the hardcoded tool count in the
# Housekeeping item of PLAN.md. audit_definitions.py checks it is exhaustive
# and disjoint, so a new definition has to be filed somewhere.
DEFINITION_CATEGORIES = {
    "retail_and_food": [
        "retail_premises", "shop", "neighbourhood_shop", "specialised_retail_premises",
        "food_and_drink_premises", "restaurant_or_cafe",
        "take_away_food_and_drink_premises", "pub",
    ],
    "commercial_and_services": [
        "commercial_premises", "business_premises", "office_premises", "medical_centre",
    ],
    "home_based": ["home_business", "home_occupation", "home_industry"],
    "residential": [
        "residential_accommodation", "dwelling_house", "dual_occupancy", "secondary_dwelling",
        "multi_dwelling_housing", "residential_flat_building", "attached_dwellings",
        "shop_top_housing", "boarding_house",
    ],
    "industrial": [
        "industry", "light_industries", "general_industries",
        "artisan_food_and_drink_industry", "warehouse_or_distribution_centre",
        "vehicle_repair_station",
    ],
    "community_and_recreation": [
        "recreation_facility_indoor", "community_facility", "centre_based_child_care_facility",
    ],
    "accommodation": [
        "tourist_and_visitor_accommodation", "hotel_or_motel_accommodation",
        "bed_and_breakfast_accommodation",
    ],
}
