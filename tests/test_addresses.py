"""Address → zone lookup.

The risk here is not failing to answer — it is answering about the wrong
property. The NSW address service matches loosely and does not say so: a
nonexistent house number comes back as a neighbouring house, and a wrong suburb
is silently ignored. Both arrive as `numRecs: 1` and look authoritative, and a
zone taken from either flows into check_permissibility and then into a document
that goes to Council.

So most of what follows tests refusal, and the upstream responses are canned
from real ones observed on 2026-08-01 (see the docstrings on each). One live
test is kept, opt-in via LISMORE_LIVE_TESTS=1, because canned fixtures cannot
notice the day the upstream API changes shape.
"""

import os

import pytest

from lismore_da_mcp import addresses
from lismore_da_mcp.addresses import (
    LookupUnavailable,
    lookup_constraints,
    lookup_zone,
    parse_address,
)


# Captured at import, before the autouse no-network fixture replaces it, so the
# opt-in live tests at the bottom have something real to restore.
REAL_GET_JSON = addresses._get_json


def geocoder_response(*records) -> dict:
    return {"addressResult": {"numRecs": len(records), "addresses": list(records)}}


def address_record(
    number="12", road="Keen", road_type="Street", suburb="Lismore",
    postcode=2480, council="Lismore", x=153.2818, y=-28.8046,
) -> dict:
    return {
        "houseNumberString": number,
        "roadName": road,
        "roadType": road_type,
        "suburbName": suburb,
        "postCode": postcode,
        "council": council,
        "addressString": f"{number}  {road} {road_type}  {suburb} {postcode}",
        "addressPoint": {"centreX": x, "centreY": y},
    }


def zone_response(*zones) -> dict:
    return {
        "features": [
            {"attributes": {
                "EPI_NAME": "Lismore Local Environmental Plan 2012",
                "LGA_NAME": lga,
                "SYM_CODE": code,
                "LAY_CLASS": name,
                "EPI_TYPE": "LEP",
            }}
            for code, name, lga in zones
        ]
    }


@pytest.fixture
def upstream(monkeypatch):
    """Drive both APIs from a test, replacing the conftest default."""

    state = {"geocode": geocoder_response(address_record()),
             "zone": zone_response(("E2", "Commercial Centre", "LISMORE"))}

    def canned(url: str, params: dict) -> dict:
        value = state["zone"] if url == addresses.ZONING_LAYER_URL else state["geocode"]
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(addresses, "_get_json", canned)
    return state


class TestParsing:
    @pytest.mark.parametrize("text,expected", [
        ("12 Keen Street, Lismore",
         {"house_number": "12", "road_name": "Keen", "road_type": "Street", "suburb": "Lismore"}),
        # No comma at all — the commonest way people type an address.
        ("12 Keen Street Lismore",
         {"house_number": "12", "road_name": "Keen", "road_type": "Street", "suburb": "Lismore"}),
        ("43 Oliver Ave Goonellabah 2480",
         {"house_number": "43", "road_name": "Oliver", "road_type": "Ave",
          "suburb": "Goonellabah", "postcode": "2480"}),
        ("12 Keen St, Lismore NSW 2480",
         {"house_number": "12", "road_name": "Keen", "suburb": "Lismore", "postcode": "2480"}),
        ("1A Keen Street Lismore", {"house_number": "1A", "road_name": "Keen"}),
    ])
    def test_parses(self, text, expected):
        parsed = parse_address(text)
        for key, value in expected.items():
            assert parsed[key] == value, f"{text}: {key}"

    def test_tenancy_prefix_is_not_read_as_the_street_number(self):
        """'Shop 3, 88 Keen Street' is number 88, not number 3."""
        assert parse_address("Shop 3, 88 Keen Street, Lismore")["house_number"] == "88"

    def test_street_name_excludes_the_road_type(self):
        """The geocoder wants roadName and roadType apart; together they miss."""
        parsed = parse_address("12 Keen Street, Lismore")
        assert parsed["road_name"] == "Keen"
        assert parsed["road_type"] == "Street"


class TestIncompleteAddresses:
    """Refused before any request is made, so the caller is told which part is missing."""

    def test_no_street_number(self, upstream):
        result = lookup_zone("Keen Street, Lismore")
        assert "street number" in result["missing"]
        assert "zone_code" not in result

    def test_no_suburb_or_postcode(self, upstream):
        assert "suburb or postcode" in lookup_zone("12 Keen Street")["missing"]

    def test_not_an_address(self, upstream):
        result = lookup_zone("my house")
        assert result["missing"] == ["street number", "suburb or postcode"]

    def test_fallback_is_always_offered(self, upstream):
        assert "Planning Portal" in lookup_zone("my house")["fallback"]


class TestLooseMatchesAreRefused:
    def test_wrong_house_number_is_not_silently_substituted(self, upstream):
        """Observed live: 99999 Keen Street returns '387 Keen Street East Lismore'."""
        upstream["geocode"] = geocoder_response(
            address_record(number="387", suburb="East Lismore")
        )
        result = lookup_zone("99999 Keen Street, Lismore")
        assert "zone_code" not in result
        assert result["differs_by"] == "street number"
        assert "387" in result["closest_match_rejected"]

    def test_wrong_suburb_is_not_silently_ignored(self, upstream):
        """Observed live: '12 Keen Street, Goonellabah' returns the Lismore property."""
        result = lookup_zone("12 Keen Street, Goonellabah")
        assert "zone_code" not in result
        assert result["differs_by"] == "suburb"

    def test_wrong_street_name_is_refused(self, upstream):
        result = lookup_zone("12 Woodlark Street, Lismore")
        assert "zone_code" not in result
        assert result["differs_by"] == "street name"

    def test_a_genuine_match_still_passes(self, upstream):
        assert lookup_zone("12 Keen Street, Lismore")["zone_code"] == "E2"

    def test_case_and_spacing_do_not_count_as_a_mismatch(self, upstream):
        assert lookup_zone("12  keen STREET,  lismore")["zone_code"] == "E2"


class TestAmbiguity:
    def test_multiple_properties_are_listed_rather_than_picked(self, upstream):
        # Keen Street and Keen Road both satisfy a query for road name "Keen".
        upstream["geocode"] = geocoder_response(
            address_record(road_type="Street", x=153.1, y=-28.8),
            address_record(road_type="Road", x=153.2, y=-28.9),
        )
        result = lookup_zone("12 Keen Street, Lismore")
        assert "zone_code" not in result
        assert "matched 2 different properties" in result["error"]
        assert len(result["matches"]) == 2

    def test_same_address_text_at_different_points_asks_for_the_unit(self, upstream):
        """Eight records printing '410 Keen Street' are units, not eight streets.

        Listing them would repeat one line, so the count and the list must not
        be allowed to contradict each other.
        """
        upstream["geocode"] = geocoder_response(
            address_record(x=153.1, y=-28.8),
            address_record(x=153.2, y=-28.9),
        )
        result = lookup_zone("12 Keen Street, Lismore")
        assert len(result["matches"]) == 1
        assert "unit or shop number" in result["note"]
        assert "2 separate properties share the address text" in result["note"]

    def test_duplicate_records_for_one_point_are_one_property(self, upstream):
        """Multi-tenancy sites return the same point several times; that is not ambiguity."""
        upstream["geocode"] = geocoder_response(address_record(), address_record())
        assert lookup_zone("12 Keen Street, Lismore")["zone_code"] == "E2"

    def test_no_match_at_all(self, upstream):
        upstream["geocode"] = geocoder_response()
        result = lookup_zone("12 Fakeroad Street, Lismore")
        assert "No NSW address matched" in result["error"]


class TestZoneResult:
    def test_reports_the_matched_address_back(self, upstream):
        result = lookup_zone("12 Keen Street, Lismore")
        assert "Keen Street" in result["matched_address"]
        assert "confirm_this_is_the_right_property" in result

    def test_names_the_instrument(self, upstream):
        zone = lookup_zone("12 Keen Street, Lismore")["zones"][0]
        assert zone["instrument"] == "Lismore Local Environmental Plan 2012"

    def test_points_at_the_next_tool(self, upstream):
        assert "check_permissibility" in lookup_zone("12 Keen Street, Lismore")["next_step"]

    def test_caveat_admits_it_is_a_point_not_a_lot(self, upstream):
        """A lot crossing a zone boundary reports only the zone under its address point."""
        assert "not a reading of the whole" in lookup_zone("12 Keen Street, Lismore")["caveat"]

    def test_outside_lismore_is_refused_not_answered(self, upstream):
        upstream["geocode"] = geocoder_response(address_record(council="Sydney"))
        upstream["zone"] = zone_response(("B3", "Commercial Core", "SYDNEY"))
        result = lookup_zone("12 Keen Street, Lismore")
        assert "not in the Lismore LGA" in result["error"]
        assert "zone_code" not in result

    def test_unzoned_land_is_not_reported_as_no_controls(self, upstream):
        upstream["zone"] = {"features": []}
        result = lookup_zone("12 Keen Street, Lismore")
        assert "No zoning is mapped" in result["error"]

    def test_split_zoning_withholds_a_single_zone_code(self, upstream):
        upstream["zone"] = zone_response(
            ("R2", "Low Density Residential", "LISMORE"),
            ("C2", "Environmental Conservation", "LISMORE"),
        )
        result = lookup_zone("12 Keen Street, Lismore")
        assert result["split_zoning"] is True
        assert "zone_code" not in result
        assert {z["zone_code"] for z in result["zones"]} == {"R2", "C2"}

    def test_repeated_polygons_of_one_zone_are_not_split_zoning(self, upstream):
        upstream["zone"] = zone_response(
            ("R2", "Low Density Residential", "LISMORE"),
            ("R2", "Low Density Residential", "LISMORE"),
        )
        assert lookup_zone("12 Keen Street, Lismore")["zone_code"] == "R2"


class TestDegradation:
    """A network failure must return the server to its pre-lookup behaviour, not break it."""

    def test_geocoder_unreachable(self, upstream):
        upstream["geocode"] = LookupUnavailable("URLError")
        result = lookup_zone("12 Keen Street, Lismore")
        assert "could not be reached" in result["error"]
        assert "Planning Portal" in result["fallback"]

    def test_zoning_layer_unreachable_still_reports_the_address(self, upstream):
        upstream["zone"] = LookupUnavailable("timed out")
        result = lookup_zone("12 Keen Street, Lismore")
        assert "could not be reached" in result["error"]
        assert "Keen Street" in result["matched_address"]

    def test_arcgis_error_payload_is_a_failure_not_an_empty_result(self, upstream):
        """The layer answers HTTP 200 with an error body; empty features means unzoned."""
        upstream["zone"] = {"error": {"code": 404, "message": "Service not found"}}
        result = lookup_zone("12 Keen Street, Lismore")
        assert "could not be reached" in result["error"]

    def test_switch_off_disables_outbound_lookups(self, monkeypatch, upstream):
        monkeypatch.setenv("LISMORE_ADDRESS_LOOKUP", "off")
        result = lookup_zone("12 Keen Street, Lismore")
        assert "switched off" in result["error"]

    def test_switch_defaults_to_on(self, upstream):
        assert addresses.lookup_enabled()

    def test_nothing_raises(self, upstream):
        """Every path returns a payload; a tool handler has no exception to catch."""
        upstream["geocode"] = LookupUnavailable("boom")
        for text in ["", "my house", "12 Keen Street, Lismore", "!!!"]:
            assert isinstance(lookup_zone(text), dict)


class TestToolLayer:
    def test_zone_the_server_has_no_table_for_is_flagged(self, call, upstream):
        upstream["zone"] = zone_response(("RU4", "Primary Production Small Lots", "LISMORE"))
        result = call("lookup_zone_by_address", {"address": "12 Keen Street, Lismore"})
        assert result["zones_not_held_by_this_server"] == ["RU4"]

    def test_known_zone_is_not_flagged(self, call, upstream):
        result = call("lookup_zone_by_address", {"address": "12 Keen Street, Lismore"})
        assert "zones_not_held_by_this_server" not in result

    def test_empty_address_is_rejected_by_validation(self, call):
        assert "Missing" in call("lookup_zone_by_address", {"address": "  "})["error"]


class TestSiteConstraints:
    """Height, lot size, heritage, bushfire and flood at an address.

    The failure that matters is reading an empty layer result as "not
    affected" — see TestFloodIsNeverRuledOut below.
    """

    @pytest.fixture
    def layers(self, monkeypatch):
        """Drive each constraint layer independently."""
        state = {label: [] for label in addresses.CONSTRAINT_LAYERS}
        state["_covered"] = dict.fromkeys(addresses.CONSTRAINT_LAYERS, True)

        by_id = {
            (svc, lid): label
            for label, (svc, lid, _, _) in addresses.CONSTRAINT_LAYERS.items()
        }

        def canned(url: str, params: dict) -> dict:
            if url == addresses.GEOCODER_URL:
                return geocoder_response(address_record())
            for (svc, lid), label in by_id.items():
                if url == addresses._layer_url(svc, lid):
                    if params.get("returnCountOnly"):
                        return {"count": 1 if state["_covered"][label] else 0}
                    return {"features": [{"attributes": a} for a in state[label]]}
            return {"features": []}

        monkeypatch.setattr(addresses, "_get_json", canned)
        return state

    def test_height_limit(self, layers):
        layers["height_limit"] = [{
            "MAX_B_H": 11.5, "UNITS": "m", "LEGIS_REF_CLAUSE": "Clause 4.3",
            "EPI_NAME": "Lismore Local Environmental Plan 2012",
        }]
        height = lookup_constraints("12 Keen Street, Lismore")["constraints"]["height_limit"]
        assert height["maximum_building_height_m"] == 11.5
        assert height["clause"] == "Clause 4.3"

    def test_minimum_lot_size(self, layers):
        layers["minimum_lot_size"] = [{"LOT_SIZE": 40.0, "UNITS": "ha", "LEGIS_REF_CLAUSE": "Clause 4.1"}]
        lot = lookup_constraints("12 Keen Street, Lismore")["constraints"]["minimum_lot_size"]
        assert (lot["minimum_lot_size"], lot["units"]) == (40.0, "ha")

    def test_heritage_lists_every_overlapping_item(self, layers):
        """An item inside a conservation area returns both, and both matter."""
        layers["heritage"] = [
            {"H_NAME": "Commonwealth Bank", "SIG": "Local", "H_ID": "I64", "LAY_CLASS": "Item - General"},
            {"H_NAME": "Spinks Park/ Civic Precinct", "SIG": "Local", "H_ID": "C5",
             "LAY_CLASS": "Conservation Area - General"},
        ]
        heritage = lookup_constraints("12 Keen Street, Lismore")["constraints"]["heritage"]
        assert heritage["answer"] == "affected"
        assert [i["item_number"] for i in heritage["items"]] == ["I64", "C5"]
        assert "Heritage Impact Statement" in heritage["note"]

    def test_bushfire_reports_the_category_and_its_consequences(self, layers):
        layers["bushfire"] = [{"Category": 2, "d_Category": "Vegetation Category 2"}]
        fire = lookup_constraints("12 Keen Street, Lismore")["constraints"]["bushfire"]
        assert fire["categories"] == ["Vegetation Category 2"]
        assert "cannot use exempt development" in fire["note"]

    def test_nothing_at_the_point_in_a_covered_layer(self, layers):
        heritage = lookup_constraints("12 Keen Street, Lismore")["constraints"]["heritage"]
        assert heritage["answer"] == "not_within_a_mapped_area"
        assert heritage["mapped_for_lismore"] is True

    def test_one_failing_layer_does_not_take_the_others_with_it(self, layers, monkeypatch):
        layers["height_limit"] = [{"MAX_B_H": 8.5, "UNITS": "m"}]
        real = addresses.features_at

        def flaky(service, layer_id, fields, lon, lat):
            if layer_id == addresses.CONSTRAINT_LAYERS["heritage"][1]:
                raise addresses.LookupUnavailable("timed out")
            return real(service, layer_id, fields, lon, lat)

        monkeypatch.setattr(addresses, "features_at", flaky)
        constraints = lookup_constraints("12 Keen Street, Lismore")["constraints"]
        assert constraints["heritage"]["answer"] == "unknown"
        assert "could not be reached" in constraints["heritage"]["error"]
        assert constraints["height_limit"]["maximum_building_height_m"] == 8.5

    def test_coverage_is_only_asked_once(self, layers, monkeypatch):
        calls = []
        real = addresses._get_json

        def counting(url, params):
            if params.get("returnCountOnly"):
                calls.append(url)
            return real(url, params)

        monkeypatch.setattr(addresses, "_get_json", counting)
        lookup_constraints("12 Keen Street, Lismore")
        lookup_constraints("12 Keen Street, Lismore")
        assert len(calls) == len(set(calls)), "coverage re-queried for the same layer"

    def test_a_bad_address_is_refused_before_any_layer_is_queried(self, layers):
        assert "missing" in lookup_constraints("my house")


class TestFloodIsNeverRuledOut:
    """The single most dangerous thing this tool could say.

    The state Flood Planning Map holds **zero features for the entire Lismore
    LGA** (verified 2026-08-01), so an empty result there is not the same as an
    empty result from a layer that covers the council. Lismore's CBD was
    inundated in 2022; reporting it as not flood affected would be worse than
    saying nothing at all.
    """

    @pytest.fixture
    def uncovered_flood(self, monkeypatch):
        service, layer_id, _, _ = addresses.CONSTRAINT_LAYERS["flood"]
        flood_url = addresses._layer_url(service, layer_id)

        def canned(url: str, params: dict) -> dict:
            if url == addresses.GEOCODER_URL:
                return geocoder_response(address_record())
            if params.get("returnCountOnly"):
                return {"count": 0 if url == flood_url else 1}
            return {"features": []}

        monkeypatch.setattr(addresses, "_get_json", canned)

    def test_no_lismore_data_reports_unknown_not_unaffected(self, uncovered_flood):
        flood = lookup_constraints("12 Keen Street, Lismore")["constraints"]["flood"]
        assert flood["answer"] == "unknown"
        assert flood["mapped_for_lismore"] is False
        assert "not evidence the site is unaffected" in flood["note"]

    def test_carries_the_lismore_specific_warning(self, uncovered_flood):
        flood = lookup_constraints("12 Keen Street, Lismore")["constraints"]["flood"]
        assert "Do not read this as 'not flood affected'" in flood["important"]
        assert "Duty Planner" in flood["important"]

    def test_warning_is_present_even_when_the_layer_covers_lismore(self):
        """Coverage arriving later must not silently remove the warning.

        Uses the conftest default, where every layer covers Lismore and the
        point is clear.
        """
        flood = lookup_constraints("12 Keen Street, Lismore")["constraints"]["flood"]
        assert flood["answer"] == "not_within_a_mapped_area"
        assert "important" in flood

    def test_warning_is_dropped_only_when_the_site_is_actually_flagged(self, monkeypatch):
        service, layer_id, _, _ = addresses.CONSTRAINT_LAYERS["flood"]
        flood_url = addresses._layer_url(service, layer_id)

        def canned(url: str, params: dict) -> dict:
            if url == addresses.GEOCODER_URL:
                return geocoder_response(address_record())
            if params.get("returnCountOnly"):
                return {"count": 1}
            if url == flood_url:
                return {"features": [{"attributes": {"LAY_CLASS": "Flood Planning Area"}}]}
            return {"features": []}

        monkeypatch.setattr(addresses, "_get_json", canned)
        flood = lookup_constraints("12 Keen Street, Lismore")["constraints"]["flood"]
        assert flood["answer"] == "affected"
        assert "important" not in flood


@pytest.mark.skipif(
    os.environ.get("LISMORE_LIVE_TESTS") != "1",
    reason="hits live NSW government APIs; set LISMORE_LIVE_TESTS=1 to run",
)
class TestLive:
    """The canned fixtures above cannot notice the upstream changing shape.

    These three were verified by hand on 2026-08-01. Run them after any change
    to the URLs, the parameter names or the fields read off the response.
    """

    @pytest.mark.parametrize("address,zone", [
        ("12 Keen Street, Lismore", "E2"),
        ("43 Oliver Avenue, Goonellabah", "RE1"),
        ("1 Cullen Street, Nimbin", "RU1"),
    ])
    def test_live_lookup(self, monkeypatch, address, zone):
        monkeypatch.setattr(addresses, "_get_json", REAL_GET_JSON)
        assert lookup_zone(address).get("zone_code") == zone
