"""LEP 2012 clause 5.10, quoted verbatim, and what DCP Chapter 12 does not say.

ROADMAP.md S4. Nine places in this repository asserted that **"a Heritage Impact
Statement is required (DCP Chapter 12)"**. Both halves of that are wrong:

- **Chapter 12 requires no document at all.** It mentions a heritage impact
  statement exactly twice, both times in its definitions section, and says of
  itself only that it "will apply whenever development consent is required under
  clause 5.10 Lismore LEP 2012". Checked against
  `documents/dcp/chapter-12-heritage-conservation.pdf`, 2026-08-20.
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

Every quote below appears verbatim in `documents/lep/lep-2012-nsw-full.txt`;
`scripts/audit_heritage.py` checks that, and checks that the phrase this file
exists to correct is still absent from DCP Chapter 12.
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
