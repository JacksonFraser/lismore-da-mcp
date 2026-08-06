"""Signage standards match DCP Chapter 9, and the tool answers the real question.

PLAN.md item 2.3. Almost every business needs a sign and there was no tool for
it. The thing reading the chapter turned up is that most shopfront signage is
**Exempt Development** — no DA, no CDC — so the tool leads with the approval
pathway rather than with a size table, and the tests below pin that ordering as
much as the numbers.

Chapter 9's controls are prose under per-sign headings rather than a table, so
as with the parking rates every standard is stored verbatim and
`TestStandardsAreInTheDCP` is the real guarantee.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_signage import chapter_text, normalise  # noqa: E402

from lismore_da_mcp.data.signage import (  # noqa: E402
    APPLICATION_REQUIREMENTS, DESIGN_GUIDELINES, EXISTING_USE_RIGHTS,
    ROAD_RESERVE, SEPP_PROHIBITED_ZONES, SIGNAGE)


@pytest.fixture(scope="module")
def chapter():
    return normalise(chapter_text())


class TestStandardsAreInTheDCP:
    @pytest.mark.parametrize("key", sorted(SIGNAGE))
    def test_definition_appears_verbatim(self, key, chapter):
        assert normalise(SIGNAGE[key]["definition"]) in chapter, (
            f"{key}'s definition is no longer in Chapter 9 verbatim. Read the chapter before "
            "editing — do not adjust the stored text to make this pass."
        )

    @pytest.mark.parametrize("key", sorted(k for k, v in SIGNAGE.items() if v.get("standard")))
    def test_standard_appears_verbatim(self, key, chapter):
        assert normalise(SIGNAGE[key]["standard"]) in chapter

    @pytest.mark.parametrize("label", [
        "9.2 intro", "9.2 exceptions", "9.5 applications", "9.5 plans",
        "9.6 existing use", "9.7 duration", "9.8 road reserve",
    ])
    def test_provision_appears_verbatim(self, label, chapter):
        quotes = {
            "9.2 intro": SEPP_PROHIBITED_ZONES["verbatim_intro"],
            "9.2 exceptions": SEPP_PROHIBITED_ZONES["exceptions_verbatim"],
            "9.5 applications": APPLICATION_REQUIREMENTS["verbatim"],
            "9.5 plans": APPLICATION_REQUIREMENTS["plans_verbatim"],
            "9.6 existing use": EXISTING_USE_RIGHTS["verbatim"],
            "9.7 duration": APPLICATION_REQUIREMENTS["duration_verbatim"],
            "9.8 road reserve": ROAD_RESERVE["verbatim"],
        }
        assert normalise(quotes[label]) in chapter

    @pytest.mark.parametrize("name", sorted(DESIGN_GUIDELINES["guidelines"]))
    def test_design_guideline_appears_verbatim(self, name, chapter):
        assert normalise(DESIGN_GUIDELINES["guidelines"][name]) in chapter

    def test_every_sign_type_in_9_3_is_carried(self, chapter):
        """A sign the chapter defines but the tool does not know is a hole a
        business falls into. Matched on the term §9.3 itself defines, not on our
        display name — the chapter spells it 'fascia' in §9.3 and 'Facia' in the
        §9.11 heading, and comparing display names reported both as missing."""
        import re
        defined = {d.strip() for d in re.findall(r"([a-z/ ]+?) means a sign", chapter)}
        carried = {normalise(e["definition"]).split(" means ")[0] for e in SIGNAGE.values()}
        assert defined, "the §9.3 definition scan matched nothing — the regex has rotted"
        assert defined - carried == set()


class TestTheAnswerIsUsuallyNoApplication:
    """The finding that reorders the whole tool.

    §9.11: "These Environmental Planning Instruments provide for certain types
    of signage as Exempt or Complying Development and the provisions of this DCP
    chapter are not applicable." A business asking about a shopfront sign mostly
    does not need an application, and leading with a size limit answers a
    question it does not have.
    """

    def test_the_ordinary_shopfront_set_is_exempt(self, call):
        for sign in ("wall_sign", "window_sign", "fascia_sign", "top_hamper_sign",
                     "awning_sign_below"):
            result = call("get_signage_requirements", {"sign_type": sign})
            assert result["do_you_need_an_application"]["pathway"] == "exempt", sign

    def test_complying_signs_are_named_as_a_cdc_not_a_da(self, call):
        for sign in ("projecting_wall_sign", "pylon_sign"):
            result = call("get_signage_requirements", {"sign_type": sign})
            assert result["do_you_need_an_application"]["pathway"] == "complying", sign
            assert "CDC" in result["do_you_need_an_application"]["label"]

    def test_exempt_is_conditional_not_absolute(self, call):
        """The exemption holds only while the sign meets every SEPP criterion.
        Reporting "no application needed" without that condition would be the
        harmful simplification here."""
        result = call("get_signage_requirements", {"sign_type": "wall_sign"})
        meaning = result["do_you_need_an_application"]["meaning"]
        assert "provided the sign meets every criterion" in meaning
        assert "it needs development consent" in meaning

    def test_the_pathway_comes_before_the_size(self, call):
        """Ordering is the deliverable, not a nicety — a dict preserves insertion
        order and that is what the client renders."""
        result = call("get_signage_requirements", {"sign_type": "pylon", "height_m": 9})
        keys = list(result)
        assert keys.index("do_you_need_an_application") < keys.index("size")


class TestTheAFrameTrap:
    """The commonest signage mistake a Lismore café makes, and the reason the
    synonyms matter more here than anywhere else: nobody asks about a "portable
    footpath sign"."""

    @pytest.mark.parametrize("phrase", [
        "A-frame", "a frame", "sandwich board", "footpath sign", "pavement sign",
    ])
    def test_a_business_s_own_words_resolve(self, phrase, call):
        result = call("get_signage_requirements", {"sign_type": phrase})
        assert result["sign_type"] == "portable_footpath_sign"

    def test_it_is_reported_as_not_permissible(self, call):
        result = call("get_signage_requirements", {"sign_type": "sandwich board"})
        assert result["do_you_need_an_application"]["pathway"] == "restricted"
        assert "Schedule 2" in result["standard"]

    def test_the_road_reserve_problem_is_raised_unprompted(self, call):
        """It fails at owner's consent, not on the merits — which is earlier and
        more final, and is not something an applicant would think to ask."""
        result = call("get_signage_requirements", {"sign_type": "A-frame"})
        assert result["road_reserve"]["applies"] is True
        assert "will not agree" in result["road_reserve"]["provision"]
        assert "before it is ever assessed" in result["road_reserve"]["consequence"]

    def test_an_awning_sign_is_not_caught_by_the_road_reserve_rule(self, call):
        """§9.8 expressly allows signage attached to protrusions such as awnings,
        so the same warning on an under-awning sign would be noise."""
        result = call("get_signage_requirements", {"sign_type": "under awning sign"})
        assert result["road_reserve"]["applies"] is False

    def test_a_menu_board_is_distinguished_from_a_footpath_sign(self, call):
        """Both are 'the board out the front' to an operator, but the chapter
        treats them differently — a chalkboard must be affixed to private
        property."""
        result = call("get_signage_requirements", {"sign_type": "menu board"})
        assert result["sign_type"] == "chalkboard_sign"
        assert "affixed to private property" in result["size"]["standard"]


class TestTheHeritageRefusalPoint:
    """PLAN.md names this as a common refusal point in a CBD. §9.2 prohibits
    advertising in a heritage area — but the exception is the useful half."""

    def test_heritage_is_prohibited_ground_for_general_advertising(self, call):
        result = call("get_signage_requirements", {
            "sign_type": "billboard", "zone_code": "E2", "is_heritage": True})
        assert result["where_it_can_go"]["prohibited"] is True
        assert any("heritage" in g for g in result["where_it_can_go"]["grounds"])

    def test_a_business_identification_sign_survives_the_prohibition(self, call):
        """The answer a business needs: you can still put your name up."""
        result = call("get_signage_requirements", {
            "sign_type": "business sign", "zone_code": "R1", "is_heritage": True})
        assert result["where_it_can_go"]["prohibited"] is False
        assert "expressly excepted" in result["where_it_can_go"]["saved_by_exception"]

    def test_a_prohibited_sign_is_told_what_it_can_have_instead(self, call):
        result = call("get_signage_requirements", {
            "sign_type": "billboard", "zone_code": "R1"})
        assert "business identification sign" in \
            result["where_it_can_go"]["what_you_can_still_do"]

    def test_prohibited_and_saved_are_never_both_asserted(self, call):
        """`prohibited: true` next to an exception that defeats it invites the
        reader to stop at the first field."""
        result = call("get_signage_requirements", {
            "sign_type": "wall_sign", "zone_code": "R1", "is_heritage": True})
        where = result["where_it_can_go"]
        assert where["prohibited"] is False
        assert "grounds" not in where
        assert where["would_be_prohibited_but_for_the_exception"]

    def test_character_leads_the_guidelines_on_a_heritage_site(self, call):
        result = call("get_signage_requirements", {
            "sign_type": "wall_sign", "is_heritage": True})
        assert list(result["design_guidelines"]["guidelines"])[0] == "Character"
        assert "Heritage Impact Statement" in result["design_guidelines"]["lead_with"]

    def test_unstated_heritage_is_not_treated_as_absent(self, call):
        """The failure mode that matters: a site whose heritage status was never
        checked must not read as cleared."""
        result = call("get_signage_requirements", {"sign_type": "wall_sign", "zone_code": "E2"})
        assert "heritage_not_established" in result["where_it_can_go"]
        assert "has not been ruled out" in \
            result["where_it_can_go"]["heritage_not_established"]

    def test_a_mixed_use_zone_is_not_a_residential_prohibition(self, call):
        """§9.2 excludes mixed residential/business zones by its own words, and
        MU1 is Lismore's."""
        result = call("get_signage_requirements", {
            "sign_type": "billboard", "zone_code": "MU1"})
        assert result["where_it_can_go"]["prohibited"] is False


class TestSizeIsCheckedNotAsserted:
    def test_an_oversize_sign_is_measured_against_the_standard(self, call):
        result = call("get_signage_requirements", {
            "sign_type": "under awning sign", "area_sqm": 3.2})
        assert result["size"]["complies"] is False
        assert "over by 1.2m²" in result["size"]["assessment"][0]

    def test_a_compliant_sign_says_so(self, call):
        result = call("get_signage_requirements", {
            "sign_type": "under awning sign", "area_sqm": 1.5})
        assert result["size"]["complies"] is True

    def test_pylon_height_is_checked(self, call):
        result = call("get_signage_requirements", {"sign_type": "pylon", "height_m": 9})
        assert result["size"]["complies"] is False
        assert "7.5m" in result["size"]["assessment"][0]

    def test_an_unmeasured_sign_is_not_reported_as_compliant(self, call):
        result = call("get_signage_requirements", {"sign_type": "pylon"})
        assert result["size"]["complies"] is None
        assert "not assessed" in result["size"]["assessment"][0]

    def test_no_standard_is_not_reported_as_no_limit(self, call):
        """Chapter 9 sets no size for a window sign. That is not licence to cover
        the glass, and the tool must not imply it is."""
        result = call("get_signage_requirements", {"sign_type": "window sign", "area_sqm": 99})
        assert "size" not in result
        assert "assessed on merit" in result["no_numeric_standard"]
        assert "has not been assessed against anything" in result["no_numeric_standard"]


class TestTheStaleSeppReference:
    """Chapter 9 cites SEPP 64 throughout, which was repealed and folded into
    SEPP (Industry and Employment) 2021. No document here carries the current
    instrument, so it is flagged as a pointer rather than cited as fact."""

    def test_the_warning_is_attached_to_every_answer(self, call):
        result = call("get_signage_requirements", {"sign_type": "wall_sign"})
        assert "SEPP 64" in result["check_the_sepp_reference"]["issue"]

    def test_it_does_not_claim_to_have_verified_the_current_instrument(self, call):
        result = call("get_signage_requirements", {"sign_type": "wall_sign"})
        warning = result["check_the_sepp_reference"]
        assert "No document in this repository" in warning["not_verified_here"]
        assert "Confirm the current provision" in warning["not_verified_here"]


class TestToolSurface:
    def test_an_unknown_sign_type_explains_rather_than_guessing(self, call):
        result = call("get_signage_requirements", {"sign_type": "hologram projection"})
        assert "error" in result
        assert "available_sign_types" in result

    def test_the_listing_groups_by_what_approval_is_needed(self, call):
        result = call("list_signage_types", {})
        groups = result["by_approval_pathway"]
        exempt = [s["sign_type"] for s in
                  groups["exempt — no application needed if it meets the SEPP criteria"]]
        assert "wall_sign" in exempt
        assert "Most shopfront signage" in result["start_here"]

    def test_signage_can_ride_on_an_existing_da(self, call):
        """§9.5: a sign need not be its own DA. A business already lodging for a
        fitout should not pay twice."""
        result = call("get_signage_requirements", {"sign_type": "billboard"})
        assert "need not be a separate application" in result["if_you_lodge"]["not_a_separate_da"]

    def test_taking_over_a_tenancy_with_an_existing_sign_is_addressed(self, call):
        result = call("get_signage_requirements", {"sign_type": "wall_sign"})
        assert "1985" in result["existing_signage_on_the_premises"]["verbatim"]
