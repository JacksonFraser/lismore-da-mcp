"""Address → zone lookup against two NSW government APIs.

Five tools require `zone_code` and, until now, nothing derived it. The intended
audience is people applying for the first time, who know their address and not
their zone — so the server could not answer the first question anyone asks.

Two free, unauthenticated services do it:

- **NSW Spatial Services** (`maps.six.nsw.gov.au`) turns an address into a point.
- **NSW ePlanning** (`mapprod3.environment.nsw.gov.au`, the Land Zoning Map layer
  behind the Planning Portal) returns the zone at that point, with `EPI_NAME`
  naming the instrument that zoned it.

Three deliberate choices:

**Nothing here raises.** Every failure returns a payload with an `error` key and
a `fallback` telling the caller to read the zone off the Planning Portal by hand
— which is exactly what they did before this module existed. A network outage
degrades the server to its previous behaviour rather than breaking a tool.

**The geocoder's answer is verified, not trusted.** It matches loosely, and its
loose matches are silent. Probed on 2026-08-01:

    houseNumber=99999 roadName=Keen suburb=Lismore  → "387 Keen Street East Lismore"
    houseNumber=12 roadName=Keen suburb=Goonellabah → "12 Keen Street Lismore"

Both return `numRecs: 1` and look authoritative. Passing either through would
produce a confident zone for a property the applicant never asked about, which
then flows into check_permissibility and into an SEE. So `_verify_match()`
re-checks the house number, road name and (where supplied) suburb against what
came back, and a mismatch is refused rather than reported.

**The lookup is a switch.** `LISMORE_ADDRESS_LOOKUP=off` disables it, because the
hosted instance is the only part of this server that makes outbound calls and an
operator may want it not to.

Privacy: a street address is personal information and it leaves this process. It
goes only to the NSW government planning APIs that exist to answer this question,
over HTTPS, and is never written to a log — see observability.py, whose
`record_tool_call` has no parameter that could carry one.
"""

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

GEOCODER_URL = "https://maps.six.nsw.gov.au/services/public/Address_Location"

# The ePlanning folder, not the sibling `Planning` folder — the latter 404s.
ZONING_LAYER_URL = (
    "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/ePlanning/"
    "Planning_Portal_Principal_Planning/MapServer/19/query"
)

# Short. A caller is waiting, and the public transport rate-limits per IP, so a
# hung upstream must not hold a worker for long.
TIMEOUT_SECONDS = 8.0

LGA_NAME = "LISMORE"

# Road types the geocoder accepts, longest first so "Street" is not matched as
# "St". Only used to split a road name from its type; the geocoder resolves
# abbreviations itself, and tolerates the type being omitted entirely.
ROAD_TYPES = [
    "Street", "Road", "Avenue", "Drive", "Court", "Place", "Lane", "Terrace",
    "Parade", "Crescent", "Close", "Way", "Highway", "Circuit", "Boulevard",
    "Esplanade", "Grove", "Rise", "Track", "Trail", "Parkway", "Loop", "Mews",
    "St", "Rd", "Ave", "Av", "Dr", "Ct", "Pl", "Ln", "Tce", "Pde", "Cres",
    "Cl", "Hwy", "Cct", "Blvd", "Esp", "Gr", "Pwy",
]

FALLBACK = (
    "Look the zone up by address on the NSW Planning Portal Spatial Viewer "
    "(https://www.planningportal.nsw.gov.au/spatialviewer/) and pass it as "
    "zone_code, or ask the Council Duty Planner."
)


def lookup_enabled() -> bool:
    """False when the operator has switched outbound address lookups off."""
    return os.environ.get("LISMORE_ADDRESS_LOOKUP", "on").strip().lower() not in (
        "off", "0", "false", "no", "disabled",
    )


# --- address parsing ------------------------------------------------------


def parse_address(text: str) -> dict:
    """Split a free-text address into the geocoder's parameters.

    The geocoder requires a house number and requires a suburb or postcode —
    without a number it returns every address on the street (177 for Keen
    Street), and without a locality it refuses outright. So both are checked
    here, where the caller can be told which part is missing, rather than being
    discovered as an unhelpful upstream error.
    """
    cleaned = " ".join((text or "").split())
    parsed = {
        "house_number": "",
        "road_name": "",
        "road_type": "",
        "suburb": "",
        "postcode": "",
    }
    if not cleaned:
        return parsed

    # Strip a tenancy prefix — "Shop 3, 88 Keen Street" is one property to the
    # geocoder, and the shop number would otherwise be read as the street number.
    cleaned = re.sub(
        r"^(shop|unit|suite|tenancy|villa|apartment|apt)\s*[\w/-]*\s*[,/]\s*",
        "",
        cleaned,
        flags=re.I,
    )

    segments = [s.strip() for s in cleaned.split(",") if s.strip()]
    if not segments:
        return parsed

    postcode = re.search(r"\b(\d{4})\b", " ".join(segments[1:]) if len(segments) > 1 else "")
    if postcode:
        parsed["postcode"] = postcode.group(1)

    if len(segments) > 1:
        for segment in reversed(segments[1:]):
            candidate = re.sub(r"\b\d{4}\b", "", segment)
            candidate = re.sub(r"\bNSW\b", "", candidate, flags=re.I)
            candidate = " ".join(candidate.split())
            if candidate:
                parsed["suburb"] = candidate
                break

    street_part = segments[0]

    # A single-segment address has to yield its own suburb: everything after the
    # road type is the locality. "12 Keen Street Lismore" is what people type.
    if len(segments) == 1:
        match = re.search(
            r"\b(" + "|".join(ROAD_TYPES) + r")\b\.?\s+(.+)$", street_part, re.I
        )
        if match:
            trailing = re.sub(r"\b\d{4}\b", "", match.group(2))
            trailing = re.sub(r"\bNSW\b", "", trailing, flags=re.I)
            trailing = " ".join(trailing.split())
            if trailing:
                parsed["suburb"] = trailing
            postcode = re.search(r"\b(\d{4})\b", match.group(2))
            if postcode:
                parsed["postcode"] = postcode.group(1)
            street_part = street_part[: match.end(1)]

    number = re.match(r"^(\d+[A-Za-z]?)\s+(.*)$", street_part.strip())
    if number:
        parsed["house_number"] = number.group(1)
        road = number.group(2).strip()
    else:
        road = street_part.strip()

    road_type = re.search(r"\s(" + "|".join(ROAD_TYPES) + r")\b\.?$", road, re.I)
    if road_type:
        parsed["road_type"] = road_type.group(1).title()
        parsed["road_name"] = road[: road_type.start()].strip()
    else:
        parsed["road_name"] = road

    return parsed


def _missing_parts(parsed: dict) -> list[str]:
    missing = []
    if not parsed["house_number"]:
        missing.append("street number")
    if not parsed["road_name"]:
        missing.append("street name")
    if not parsed["suburb"] and not parsed["postcode"]:
        missing.append("suburb or postcode")
    return missing


# --- HTTP -----------------------------------------------------------------


class LookupUnavailable(Exception):
    """An upstream API could not be reached or did not return usable JSON."""


def _get_json(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v not in ("", None)})
    request = urllib.request.Request(
        f"{url}?{query}",
        headers={"User-Agent": "lismore-da-mcp", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LookupUnavailable(f"{type(exc).__name__}") from exc
    except json.JSONDecodeError as exc:
        raise LookupUnavailable("invalid JSON from upstream") from exc


def geocode(parsed: dict) -> list[dict]:
    """Return candidate addresses for the parsed parts. May be empty."""
    payload = _get_json(
        GEOCODER_URL,
        {
            "houseNumber": parsed["house_number"],
            "roadName": parsed["road_name"],
            "roadType": parsed["road_type"],
            "suburb": parsed["suburb"],
            "postCode": parsed["postcode"],
            "projection": "EPSG:4326",
        },
    )
    result = payload.get("addressResult") or {}
    return result.get("addresses") or []


def zones_at(longitude: float, latitude: float) -> list[dict]:
    """Return every zoning feature covering the point.

    Normally one. The result is a list because the layer can return several
    where polygons meet or overlap — but note this is a *point* query, so a lot
    that straddles a zone boundary reports only the zone under its address
    point. Detecting that properly would need the lot's cadastral boundary, not
    a point. lookup_zone() says so in its caveat rather than implying otherwise.
    """
    payload = _get_json(
        ZONING_LAYER_URL,
        {
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "EPI_NAME,LGA_NAME,SYM_CODE,LAY_CLASS,EPI_TYPE,CURRENCY_DATE",
            "returnGeometry": "false",
            "f": "json",
        },
    )
    if "error" in payload:
        raise LookupUnavailable(str(payload["error"].get("message", "layer error")))
    return [f.get("attributes", {}) for f in payload.get("features") or []]


# --- verification ---------------------------------------------------------


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _verify_match(parsed: dict, candidate: dict) -> str | None:
    """Return a reason the candidate is not what was asked for, or None.

    The geocoder answers loose queries with a confident single record — a
    nonexistent house number resolves to a different house, and a wrong suburb is
    ignored. Neither is distinguishable from a good match in the response, so
    each supplied part is checked against what came back.
    """
    asked_number = _normalise(parsed["house_number"])
    got_number = _normalise(str(candidate.get("houseNumberString", "")))
    if asked_number and got_number and asked_number != got_number:
        return "street number"

    asked_road = _normalise(parsed["road_name"])
    got_road = _normalise(str(candidate.get("roadName", "")))
    if asked_road and got_road and asked_road != got_road:
        return "street name"

    asked_suburb = _normalise(parsed["suburb"])
    got_suburb = _normalise(str(candidate.get("suburbName", "")))
    if asked_suburb and got_suburb and asked_suburb != got_suburb:
        return "suburb"

    asked_postcode = _normalise(parsed["postcode"])
    got_postcode = _normalise(str(candidate.get("postCode", "")))
    if asked_postcode and got_postcode and asked_postcode != got_postcode:
        return "postcode"

    return None


def _format_address(candidate: dict) -> str:
    return " ".join(str(candidate.get("addressString", "")).split())


# --- resolving an address to a point --------------------------------------


def resolve_address(address: str) -> dict:
    """Turn an address into one verified property, or into a refusal.

    Returns either `{"error": ...}` or `{"match": ..., "longitude": ..., "latitude": ...}`.
    Shared by every address-based tool so they refuse identically — the
    verification below is the whole reason those tools can be trusted, and a
    second copy of it would be a second chance to get it wrong.
    """
    if not lookup_enabled():
        return {
            "error": "Address lookup is switched off on this server.",
            "fallback": FALLBACK,
        }

    parsed = parse_address(address)
    missing = _missing_parts(parsed)
    if missing:
        return {
            "error": "Could not read a full street address from " + repr(address),
            "missing": missing,
            "understood": {k: v for k, v in parsed.items() if v},
            "note": (
                "A street number and a suburb or postcode are both required — "
                "without them the address service cannot identify one property."
            ),
            "fallback": FALLBACK,
        }

    try:
        candidates = geocode(parsed)
    except LookupUnavailable as exc:
        return _unavailable("address service", exc)

    if not candidates:
        return {
            "error": f"No NSW address matched {address!r}.",
            "understood": {k: v for k, v in parsed.items() if v},
            "note": "Check the spelling of the street and suburb.",
            "fallback": FALLBACK,
        }

    verified = [c for c in candidates if _verify_match(parsed, c) is None]

    if not verified:
        mismatch = _verify_match(parsed, candidates[0])
        return {
            "error": f"No exact match for {address!r}.",
            "closest_match_rejected": _format_address(candidates[0]),
            "differs_by": mismatch,
            "note": (
                "The NSW address service answers loosely — it returns a nearby "
                "property rather than nothing. That result was not used, because "
                "zoning the wrong property would be worse than not answering. "
                "Check the address and try again."
            ),
            "fallback": FALLBACK,
        }

    # Distinct properties, not the duplicate records the service returns for
    # multi-tenancy sites (eight rows for one strata block share a point).
    distinct = {}
    for candidate in verified:
        point = candidate.get("addressPoint") or {}
        key = (round(point.get("centreX", 0), 6), round(point.get("centreY", 0), 6))
        distinct.setdefault(key, candidate)

    if len(distinct) > 1:
        labels = sorted({_format_address(c) for c in distinct.values()})
        result = {
            "error": f"{address!r} matched {len(distinct)} different properties.",
            "matches": labels[:10],
            "note": "Re-send with the suburb, or with the unit or shop number.",
            "fallback": FALLBACK,
        }
        if len(labels) < len(distinct):
            # Several separately-located records printing the same address text —
            # units in one building. Listing them would show the same line twice,
            # so say what is actually needed to tell them apart.
            result["note"] = (
                f"{len(distinct)} separate properties share the address text "
                f"{labels[0]!r} — typically units or tenancies in one building. "
                "Re-send with the unit or shop number."
            )
        return result

    match = next(iter(distinct.values()))
    point = match.get("addressPoint") or {}
    longitude, latitude = point.get("centreX"), point.get("centreY")
    if longitude is None or latitude is None:
        return {
            "error": f"The address service returned no coordinates for {address!r}.",
            "matched_address": _format_address(match),
            "fallback": FALLBACK,
        }

    return {"match": match, "longitude": longitude, "latitude": latitude}


# --- the zone lookup ------------------------------------------------------


def lookup_zone(address: str) -> dict:
    """Resolve an address to its LEP zone. Always returns a payload, never raises."""
    resolved = resolve_address(address)
    if "error" in resolved:
        return resolved

    match, longitude, latitude = resolved["match"], resolved["longitude"], resolved["latitude"]
    matched_address = _format_address(match)
    council = str(match.get("council") or "")

    try:
        features = zones_at(longitude, latitude)
    except LookupUnavailable as exc:
        return _unavailable("zoning map service", exc, matched_address=matched_address)

    lismore_features = [f for f in features if _normalise(f.get("LGA_NAME")) == _normalise(LGA_NAME)]

    if not features:
        return {
            "error": "No zoning is mapped at that location.",
            "matched_address": matched_address,
            "council": council,
            "note": (
                "Unzoned land on the state map is usually a mapping gap rather "
                "than an absence of controls."
            ),
            "fallback": FALLBACK,
        }

    if not lismore_features:
        other = sorted({str(f.get("LGA_NAME") or "?") for f in features})
        return {
            "error": f"{matched_address} is not in the Lismore LGA.",
            "matched_address": matched_address,
            "lga": other[0] if len(other) == 1 else other,
            "note": (
                "This server only holds Lismore LEP 2012 and the Lismore DCP. "
                "The zone above is real, but nothing else here applies to it — "
                "contact that council instead."
            ),
        }

    zones = []
    for feature in lismore_features:
        code = str(feature.get("SYM_CODE") or "").strip().upper()
        zones.append({
            "zone_code": code,
            "zone_name": str(feature.get("LAY_CLASS") or "").strip(),
            "instrument": str(feature.get("EPI_NAME") or "").strip(),
        })

    # Deduplicate — one lot can be returned once per overlapping map polygon.
    unique = {}
    for zone in zones:
        unique.setdefault(zone["zone_code"], zone)
    zones = list(unique.values())

    result = {
        "query": address,
        "matched_address": matched_address,
        "confirm_this_is_the_right_property": (
            "The address service matches loosely. If the address above is not "
            "the site, do not use this zone."
        ),
        "lga": "Lismore",
        "zones": zones,
        "source": (
            "NSW ePlanning Land Zoning Map (Planning Portal), via NSW Spatial "
            "Services address geocoder"
        ),
        "caveat": (
            "This is the zone at the address point, not a reading of the whole "
            "lot: a lot crossing a zone boundary can be in two zones and only "
            "the one under the address point is reported. The state map is also "
            "a guide — Council's own maps prevail, and site constraints (flood, "
            "heritage, bushfire) sit on separate layers this does not read."
        ),
    }

    if len(zones) == 1:
        result["zone_code"] = zones[0]["zone_code"]
        result["next_step"] = (
            f"Pass zone_code {zones[0]['zone_code']!r} to check_permissibility "
            "to confirm the proposed use is allowed."
        )
    else:
        result["split_zoning"] = True
        result["next_step"] = (
            "This lot is in more than one zone. Each zone's land use table "
            "applies to the part of the lot within it, so which zone governs "
            "depends on where the work is proposed. Check permissibility for "
            "each, and confirm the boundary with the Duty Planner before "
            "lodging — LEP clause 4.2E deals with subdividing split-zoned lots."
        )

    return result


# --- site constraints -----------------------------------------------------
#
# The same point query against the sibling layers, which turn `is_flood_affected`
# and `is_heritage` from things the caller asserts into things that are checked.
#
# The trap here is reading an empty result as "not affected". A layer returns no
# features both when the site is genuinely outside a mapped area and when the
# dataset does not cover this council at all, and those mean opposite things.
# **The state Flood Planning Map contains zero features for the whole Lismore
# LGA** (verified 2026-08-01), so a naive reading would report the Lismore CBD —
# inundated in 2022 — as not flood affected. So an empty result triggers a
# coverage check, and a layer with no Lismore data at all reports that it cannot
# answer rather than reporting an absence of constraint.

PRINCIPAL_PLANNING = "Planning_Portal_Principal_Planning"
HAZARD = "Planning_Portal_Hazard"

LAYER_BASE = "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/ePlanning/"

# label → (service, layer id, fields, whether the layer carries LGA_NAME)
CONSTRAINT_LAYERS = {
    "height_limit": (PRINCIPAL_PLANNING, 14, "EPI_NAME,LGA_NAME,MAX_B_H,UNITS,LEGIS_REF_CLAUSE", True),
    "minimum_lot_size": (PRINCIPAL_PLANNING, 22, "EPI_NAME,LGA_NAME,LOT_SIZE,UNITS,LEGIS_REF_CLAUSE", True),
    "heritage": (PRINCIPAL_PLANNING, 16, "EPI_NAME,LGA_NAME,LAY_CLASS,H_NAME,SIG,H_ID", True),
    "flood": (HAZARD, 230, "EPI_NAME,LGA_NAME,LAY_CLASS,COMMENT", True),
    # Bushfire Prone Land is a single state-wide RFS dataset with no LGA_NAME
    # column, so its coverage cannot be checked by council. It is verified to
    # cover this LGA (6,877 features across a Lismore bounding box, 2026-08-01).
    "bushfire": (HAZARD, 229, "Category,d_Category,Guideline,LastUpdate", False),
}

# Coverage does not change between requests; checking it once per process keeps
# the empty-result path from doubling every lookup.
_coverage_cache: dict[str, bool] = {}


def _layer_url(service: str, layer_id: int) -> str:
    return f"{LAYER_BASE}{service}/MapServer/{layer_id}/query"


def features_at(service: str, layer_id: int, fields: str, longitude: float, latitude: float) -> list[dict]:
    payload = _get_json(
        _layer_url(service, layer_id),
        {
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": fields,
            "returnGeometry": "false",
            "f": "json",
        },
    )
    if "error" in payload:
        raise LookupUnavailable(str(payload["error"].get("message", "layer error")))
    return [f.get("attributes", {}) for f in payload.get("features") or []]


def layer_covers_lismore(label: str) -> bool:
    """Does this layer hold any data for the Lismore LGA?

    Answers the question an empty point result cannot: whether "no features
    here" means "not affected" or "this dataset does not cover this council".
    """
    if label in _coverage_cache:
        return _coverage_cache[label]

    service, layer_id, _, has_lga = CONSTRAINT_LAYERS[label]
    if not has_lga:
        # No LGA column to filter on; coverage was verified by hand instead.
        _coverage_cache[label] = True
        return True

    payload = _get_json(
        _layer_url(service, layer_id),
        {"where": f"LGA_NAME='{LGA_NAME}'", "returnCountOnly": "true", "f": "json"},
    )
    if "error" in payload:
        raise LookupUnavailable(str(payload["error"].get("message", "coverage query failed")))
    covered = bool(payload.get("count", 0))
    _coverage_cache[label] = covered
    return covered


def _describe(label: str, features: list[dict]) -> dict:
    """Turn raw layer attributes into an answer, or into an honest absence."""
    if not features:
        try:
            if not layer_covers_lismore(label):
                return {
                    "answer": "unknown",
                    "mapped_for_lismore": False,
                    "note": (
                        "The NSW state dataset for this holds no data at all for "
                        "the Lismore LGA, so this lookup cannot tell you either "
                        "way. This is not evidence the site is unaffected."
                    ),
                }
        except LookupUnavailable as exc:
            return {"answer": "unknown", "error": f"coverage check failed ({exc})"}
        return {"answer": "not_within_a_mapped_area", "mapped_for_lismore": True}

    if label == "height_limit":
        first = features[0]
        return {
            "answer": "mapped",
            "maximum_building_height_m": first.get("MAX_B_H"),
            "units": first.get("UNITS"),
            "clause": first.get("LEGIS_REF_CLAUSE"),
            "instrument": first.get("EPI_NAME"),
        }

    if label == "minimum_lot_size":
        first = features[0]
        return {
            "answer": "mapped",
            "minimum_lot_size": first.get("LOT_SIZE"),
            "units": first.get("UNITS"),
            "clause": first.get("LEGIS_REF_CLAUSE"),
            "instrument": first.get("EPI_NAME"),
        }

    if label == "heritage":
        return {
            "answer": "affected",
            "items": [
                {
                    "name": f.get("H_NAME"),
                    "significance": f.get("SIG"),
                    "item_number": f.get("H_ID"),
                    "class": f.get("LAY_CLASS"),
                }
                for f in features
            ],
            "note": (
                "Council may require a heritage management document under LEP "
                "cl 5.10(5) — usually a Heritage Impact Statement, but not necessarily. "
                "Ask which is wanted before commissioning one. DCP Chapter 12 sets the "
                "design guidance; it does not itself require a document."
            ),
        }

    if label == "bushfire":
        return {
            "answer": "affected",
            "categories": sorted({str(f.get("d_Category") or f.get("Category")) for f in features}),
            "note": (
                "Bushfire prone land. A bushfire assessment is required, the site "
                "cannot use exempt development, and development may be integrated "
                "development requiring RFS referral."
            ),
        }

    return {
        "answer": "affected",
        "detail": [f.get("LAY_CLASS") or f.get("COMMENT") for f in features],
    }


def out_of_area(match: dict) -> dict | None:
    """A refusal if the geocoder placed this address in another council.

    `lookup_zone` gates on `LGA_NAME` from the zoning features and refuses
    correctly; `lookup_constraints` asked nothing at all and answered for
    `1 Jonson Street, Byron Bay` with Lismore-specific reasoning attached —
    including the flood caveat, which names this LGA and is the single most
    load-bearing sentence either tool returns. One of the two knew and the other
    did not ask. SCENARIOS.md D5.

    Gating here rather than on the layers' own `LGA_NAME` because the geocoder
    answers before any layer is queried, and because Bushfire Prone Land carries
    no `LGA_NAME` column at all — an out-of-area site whose layers all came back
    empty would otherwise pass the check by returning nothing.
    """
    council = str(match.get("council") or "").strip()
    if not council or _normalise(council) == _normalise(LGA_NAME):
        return None
    return {
        "error": f"{_format_address(match)} is in the {council} local government area, "
                 "not Lismore.",
        "matched_address": _format_address(match),
        "lga": council,
        "note": (
            "This server holds Lismore LEP 2012 and the Lismore DCP only. The state "
            "mapping layers would answer for this address, but every reading this tool "
            "puts around them is Lismore-specific — the flood caveat in particular — so "
            "the answer would be right in its numbers and wrong in its advice. Contact "
            f"{council} Council instead."
        ),
    }


def lookup_constraints(address: str) -> dict:
    """Site constraints at an address: height, lot size, heritage, bushfire, flood.

    Layers are queried concurrently — five sequential round trips would block
    the event loop for as long as the slowest chain, and handlers run inline in
    the async dispatcher. One layer failing does not take the others with it.
    """
    resolved = resolve_address(address)
    if "error" in resolved:
        return resolved

    match, longitude, latitude = resolved["match"], resolved["longitude"], resolved["latitude"]

    elsewhere = out_of_area(match)
    if elsewhere:
        return elsewhere
    constraints: dict[str, dict] = {}

    def query(label: str) -> tuple[str, dict]:
        service, layer_id, fields, _ = CONSTRAINT_LAYERS[label]
        try:
            return label, _describe(label, features_at(service, layer_id, fields, longitude, latitude))
        except LookupUnavailable as exc:
            return label, {
                "answer": "unknown",
                "error": f"This layer could not be reached ({exc}).",
            }

    with ThreadPoolExecutor(max_workers=len(CONSTRAINT_LAYERS)) as pool:
        for label, described in pool.map(query, CONSTRAINT_LAYERS):
            constraints[label] = described

    # Lismore's flooding is the reason this caveat is not generic. The state
    # layer has no Lismore data, so the server's own flood tooling and the free
    # Duty Planner are the real answer — say so where it cannot be missed.
    if constraints.get("flood", {}).get("answer") != "affected":
        constraints.setdefault("flood", {})["important"] = (
            "Do not read this as 'not flood affected'. Much of the Lismore LGA "
            "is flood affected and the flood provisions are under review. Use "
            "get_flood_requirements, and consult the free Duty Planner before "
            "lodging."
        )

    return {
        "query": address,
        "matched_address": _format_address(match),
        "confirm_this_is_the_right_property": (
            "The address service matches loosely. If the address above is not "
            "the site, none of the constraints below apply to it."
        ),
        "constraints": constraints,
        "source": "NSW ePlanning Principal Planning and Hazard map layers (Planning Portal)",
        "caveat": (
            "Point-in-time reading of the state map at the address point, not a "
            "reading of the whole lot, and not a substitute for Council's own "
            "maps or a Section 10.7 Planning Certificate — which is the document "
            "that formally states what applies to a property."
        ),
    }


def _unavailable(service: str, exc: Exception, **extra) -> dict:
    return {
        "error": f"The NSW {service} could not be reached ({exc}).",
        **extra,
        "note": (
            "This is a live lookup against an external service and it is the "
            "only part of this server that needs the network. Everything else "
            "still works."
        ),
        "fallback": FALLBACK,
    }
