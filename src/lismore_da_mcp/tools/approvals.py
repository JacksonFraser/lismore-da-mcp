"""The approvals that are not the DA."""

import json

from mcp.types import TextContent

from lismore_da_mcp.approvals import by_timing
from lismore_da_mcp.approvals import describe
from lismore_da_mcp.approvals import relevant
from lismore_da_mcp.data.approvals import APPROVALS
from lismore_da_mcp.data.approvals import WHAT_THE_DA_DOES_NOT_COVER
from lismore_da_mcp.data.contacts import CONTACT_INFO
from lismore_da_mcp.registry import tool


@tool(
    name='get_other_approvals',
    description="The approvals a business needs that are NOT the development application — trade waste, food premises registration, footpath dining, liquor licensing, the Construction Certificate and the Occupation Certificate. Development consent decides the use is allowed; it is not permission to build, connect to the sewer, serve food or alcohol, or open the doors. This is where businesses get caught, so call it early rather than after the DA.",
    properties={
        'proposed_use': {'type': 'string', 'description': "What the business will be, in plain words — 'cafe', 'restaurant', 'hairdresser', 'brewery', 'retail shop'. Used to work out which approvals apply."},
        'building_work': {'type': 'boolean', 'description': 'Optional. Whether the proposal involves any building work, including an internal fitout. Assumed true unless set to false, because a Construction Certificate cannot be skipped by omission.'},
        'serves_alcohol': {'type': 'boolean', 'description': 'Optional. Whether alcohol will be sold or supplied. A liquor licence comes from Liquor & Gaming NSW, not Council, and generally cannot be applied for until consent exists.'},
        'outdoor_dining': {'type': 'boolean', 'description': 'Optional. Whether tables or chairs will go on the footpath.'},
        'connected_to_sewer': {'type': 'boolean', 'description': 'Optional. Whether the premises is connected to reticulated sewer. If false, on-site sewage management applies and can be the constraint that decides whether the site supports the business.'},
        'works_in_road_reserve': {'type': 'boolean', 'description': 'Optional. Whether any work will happen in the road reserve — a vehicle crossing, footpath works, a hoarding or a skip during construction.'},
    },
    required=['proposed_use'],
)
def get_other_approvals(arguments: dict):
    keys, unresolved = relevant(
        arguments.get("proposed_use", ""),
        building_work=arguments.get("building_work"),
        serves_alcohol=arguments.get("serves_alcohol"),
        outdoor_dining=arguments.get("outdoor_dining"),
        connected_to_sewer=arguments.get("connected_to_sewer"),
        works_in_road_reserve=arguments.get("works_in_road_reserve"),
    )

    response = {
        "proposed_use": arguments.get("proposed_use"),
        # Stated before the list, because the list only makes sense once the
        # reader has stopped assuming the consent covers all of it.
        "what_the_da_does_not_cover": WHAT_THE_DA_DOES_NOT_COVER,
        "when_each_one_happens": by_timing(keys),
        "approvals": [describe(key) for key in keys],
    }

    if unresolved:
        # Listed anyway, never dropped. An approval omitted because a question
        # was not asked is exactly the failure this tool exists to prevent.
        response["questions_that_change_this_list"] = {
            "note": "Each of these is included in the list above rather than left out, so "
                    "nothing is missed by not answering. Answering narrows the list.",
            "questions": unresolved,
        }

    response["not_included_here"] = (
        "Signage — see get_signage_requirements, since most shopfront signage needs no "
        "application at all. Section 64 water and wastewater headworks charges, which only "
        "Council can quantify. Anything specific to your trade: a hairdresser, a mechanic, a "
        "childcare centre and a tattooist each carry their own registrations under separate "
        "legislation, and this list covers what is common to a commercial fitout rather than "
        "every industry."
    )
    response["fees_are_councils_current_schedule"] = (
        "Council's fees and charges are reissued every July. Figures here are from the current "
        "schedule in this repository and are checked against it by "
        "scripts/audit_approvals.py, but confirm anything you are budgeting against. State "
        "agency charges — a liquor licence, the long service levy — are named without a figure "
        "because no document here sets them."
    )
    response["who_to_ask"] = {
        "council": CONTACT_INFO.get("phone"),
        "duty_planner": CONTACT_INFO.get("duty_planner"),
        "advice": "Council's Environmental Health Officers are the people to ask about trade "
                  "waste, food premises and the fitout standards — not the duty planner, who "
                  "handles the planning side. DCP Chapter 7 §7.3 expressly encourages talking "
                  "to them before lodging, and for a food business that conversation is worth "
                  "more than any of the planning ones.",
    }
    return [TextContent(type="text", text=json.dumps(response, indent=2))]


@tool(
    name='list_other_approvals',
    description='List every non-DA approval this server knows about, with who issues each one.',
    properties={},
)
def list_other_approvals(arguments: dict):
    return [TextContent(type="text", text=json.dumps({
        "what_the_da_does_not_cover": WHAT_THE_DA_DOES_NOT_COVER,
        "approvals": [
            {"approval": entry["name"], "issued_by": entry["issued_by"],
             "triggered_by": entry["triggered_by"]}
            for entry in APPROVALS.values()
        ],
        "for_a_specific_business": "Call get_other_approvals with the proposed use to get only "
                                   "the ones that apply, in the order they are needed.",
    }, indent=2))]
