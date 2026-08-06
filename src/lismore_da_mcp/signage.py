"""Apply DCP Chapter 9 to a proposed sign.

The question a business actually has is "can I put this sign up, and do I need
an application for it" — not "what is the maximum area of an awning sign". So
the order here is pathway first, prohibition second, size third. Leading with
the size table answers a question most businesses do not have.

Nothing in this module decides whether a site is in a heritage area or an
environmentally sensitive area. §9.2's list is not a list of zones — "heritage
area" and "environmentally sensitive area" cut across zoning entirely — so the
zone is one input and the heritage flag is another, and where neither settles it
the answer says so rather than clearing the sign.
"""

from lismore_da_mcp.data.signage import DESIGN_GUIDELINES
from lismore_da_mcp.data.signage import PATHWAYS
from lismore_da_mcp.data.signage import ROAD_RESERVE
from lismore_da_mcp.data.signage import SEPP_PROHIBITED_ZONES
from lismore_da_mcp.data.signage import SIGNAGE

# §9.2 describes the prohibited areas in land-use words, not zone codes. This
# maps them onto Lismore LEP 2012 zones so the question can be asked of an
# actual site — but it is **this repo's reading, not the SEPP's text**, and two
# of the eight descriptions cannot be mapped this way at all:
#
#   * "heritage area" is a heritage listing, not a zone. Any zone can contain
#     one, which is why heritage is a separate input.
#   * "environmentally sensitive area" takes its meaning from LEP 2012 clause
#     3.3 and is likewise not a zone.
#
# So a False from this mapping means "not prohibited *on zoning grounds*",
# never "permitted".
ZONE_PROHIBITIONS = {
    "R1": "residential", "R2": "residential", "R3": "residential", "R5": "residential",
    "RE1": "open space", "RE2": "open space",
    "W1": "waterway", "W2": "waterway",
    "C1": "national park or nature reserve",
    "C2": "natural or other conservation area",
    "C3": "natural or other conservation area",
}

# §9.2's own carve-out. MU1 is Lismore's mixed residential/business zone, which
# the prohibition expressly does not reach.
MIXED_USE_EXCLUDED = ("MU1",)

# The sign types §9.2 excepts from the prohibition.
EXCEPTED_SIGN_TYPES = ("business_identification_sign", "building_identification_sign")


def pathway(entry: dict) -> dict:
    """What approval this sign needs, in the applicant's terms."""
    key = entry.get("pathway", "consent")
    described = dict(PATHWAYS.get(key, PATHWAYS["consent"]))
    described["pathway"] = key
    return described


def zone_restriction(sign_type: str, zone_code: str | None,
                     is_heritage: bool | None) -> dict:
    """Whether §9.2 prohibits this sign here, and what survives if it does.

    Returns a payload rather than a bool, because "prohibited" is almost never
    the end of the conversation: a business identification sign is excepted, so
    the useful answer is which sign the business can still have.
    """
    zone = (zone_code or "").strip().upper() or None
    excepted = sign_type in EXCEPTED_SIGN_TYPES
    entry = SIGNAGE.get(sign_type, {})
    also_exempt = entry.get("pathway") == "exempt"

    grounds = []
    if is_heritage:
        grounds.append("the site is a heritage item or in a heritage conservation area")
    if zone and zone in ZONE_PROHIBITIONS and zone not in MIXED_USE_EXCLUDED:
        grounds.append(f"the {zone} zone is a {ZONE_PROHIBITIONS[zone]} area")

    result = {
        "provision": SEPP_PROHIBITED_ZONES["exceptions_verbatim"],
        "source": SEPP_PROHIBITED_ZONES["source"],
        "what_it_means_for_a_business":
            SEPP_PROHIBITED_ZONES["what_it_means_for_a_business"],
    }

    if not grounds:
        result["prohibited"] = False
        if is_heritage is None:
            result["heritage_not_established"] = (
                "Heritage status was not supplied and is not a function of the zone, so it has "
                "not been ruled out. A heritage item or conservation area is a prohibited area "
                "under §9.2 — check it with lookup_site_constraints or Council before ordering "
                "a sign. Signage is a common refusal point on heritage buildings in the CBD."
            )
        if zone is None:
            result["zone_not_supplied"] = (
                "No zone was given, so the §9.2 zone prohibitions were not tested."
            )
        return result

    if excepted or also_exempt:
        # Reporting `prohibited: true` alongside an exception that defeats it
        # invites the reader to stop at the first field. The prohibition is
        # recorded as the thing that *would* have applied, not as the outcome.
        result["prohibited"] = False
        result["would_be_prohibited_but_for_the_exception"] = grounds
        result["saved_by_exception"] = (
            f"§9.2 prohibits advertisements here ({'; '.join(grounds)}), but this sign is "
            + ("a business or building identification sign, which is expressly excepted."
               if excepted else
               "Exempt Development under the SEPP, which §9.2 also excepts. That exception "
               "holds only while the sign meets every criterion in the SEPP — if it does not, "
               "the prohibition applies to it.")
        )
    else:
        result["prohibited"] = True
        result["grounds"] = grounds
        result["what_you_can_still_do"] = (
            "General advertising is prohibited here, but identification is not. A sign giving "
            "the name of the business and the nature of what it does — with the address and a "
            "logo — is a business identification sign and is excepted. Ask for that instead of "
            "appealing the prohibition."
        )
    return result


def size_check(entry: dict, area_sqm: float | None, height_m: float | None) -> dict | None:
    """Measure the proposal against the chapter's numeric control, if it has one.

    Returns None where the chapter sets no number for this sign type — which is
    most of them. An unstated limit is not an unlimited one, so the caller says
    so rather than reporting a pass.
    """
    max_area = entry.get("max_area_sqm")
    max_height = entry.get("max_height_m")
    if max_area is None and max_height is None:
        return None

    checks = []
    complies = True
    if max_area is not None:
        if area_sqm is None:
            checks.append(f"The limit is {max_area:g}m². No area was supplied, so compliance "
                          "was not assessed.")
            complies = None
        else:
            ok = area_sqm <= max_area
            complies = complies and ok
            checks.append(
                f"{area_sqm:g}m² against a limit of {max_area:g}m² — "
                + ("within the standard." if ok
                   else f"over by {area_sqm - max_area:g}m². This needs consent and a "
                        "justification, or a smaller sign.")
            )
    if max_height is not None:
        if height_m is None:
            checks.append(f"The limit is {max_height:g}m in height. No height was supplied, so "
                          "compliance was not assessed.")
            complies = None
        else:
            ok = height_m <= max_height
            complies = complies and ok
            checks.append(
                f"{height_m:g}m against a limit of {max_height:g}m — "
                + ("within the standard." if ok
                   else f"over by {height_m - max_height:g}m.")
            )

    return {
        "complies": complies,
        "assessment": checks,
        "standard": entry["standard"],
        "source": entry["source"],
    }


def is_on_road_reserve(sign_type: str) -> dict | None:
    """§9.8, for the sign types that end up over or on public land.

    This is worth surfacing unprompted because it is not an assessment issue —
    it fails at owner's consent, which is earlier and more final.
    """
    over_footpath = {
        "portable_footpath_sign": "stands on the footpath, which is Council or RMS land",
        "chalkboard_sign": "is often stood on the footpath, though the chapter requires it to "
                           "be affixed to private property",
        "bunting": "is commonly strung over the footpath",
    }
    attached_to_building = {
        "awning_sign_below": "is attached to an awning, which §9.8 expressly allows",
        "projecting_wall_sign": "projects over the footpath from the building",
        "fascia_sign": "is on the awning fascia, which §9.8 expressly allows",
    }
    if sign_type in over_footpath:
        return {
            "applies": True,
            "why": f"This sign {over_footpath[sign_type]}.",
            "provision": ROAD_RESERVE["verbatim"],
            "source": ROAD_RESERVE["source"],
            "consequence": "Council owns the road reserve and will not agree to commercial "
                           "signage in it except where the sign is attached to a protrusion "
                           "such as an awning. Without the landowner's agreement the DA cannot "
                           "be made, so this fails before it is ever assessed on its merits.",
        }
    if sign_type in attached_to_building:
        return {
            "applies": False,
            "why": f"This sign {attached_to_building[sign_type]}, so §9.8's road reserve "
                   "restriction is not an obstacle.",
            "source": ROAD_RESERVE["source"],
        }
    return None


def relevant_guidelines(sign_type: str, is_heritage: bool | None) -> dict:
    """The §9.4 criteria a proposal is actually argued against.

    Character leads whenever heritage is in play — it is the guideline a
    refusal on a historic building is written under, and it is the only one
    that says a sign *shall* do something rather than *should*.
    """
    guidelines = DESIGN_GUIDELINES["guidelines"]
    order = list(guidelines)
    if is_heritage:
        order.remove("Character")
        order.insert(0, "Character")

    result = {
        "source": DESIGN_GUIDELINES["source"],
        "intro": DESIGN_GUIDELINES["intro"],
        "guidelines": {name: guidelines[name] for name in order},
    }
    if is_heritage:
        result["lead_with"] = (
            "Character. On a heritage item or in a conservation area this is the criterion the "
            "assessment turns on, and it is the only guideline in §9.4 phrased as a "
            "prohibition: no sign shall obstruct or block the view of any feature of historic "
            "architecture. Address the fixing method too — whether the sign can be removed "
            "without damaging the fabric is usually asked, and a Heritage Impact Statement may "
            "be required under DCP Chapter 12."
        )
    return result
