"""What a DA costs — lodgement fee, contributions and the rest."""

import json

from mcp.types import TextContent

from lismore_da_mcp.data.contributions import CATCHMENTS
from lismore_da_mcp.fees import calculate_da_fee, estimate_total_cost
from lismore_da_mcp.registry import tool


@tool(
    name='calculate_da_fees',
    description=(
        'What a Development Application will cost. Returns the statutory lodgement fee, '
        "Council's notification and technology charges, and — given development_type and a "
        'floor area — the Section 7.11 developer contribution, which on a commercial DA is '
        'usually far larger than the lodgement fee. For a change of use, pass existing_use '
        'as well: contributions are charged only on the increase in demand over the '
        'previous use, which is often the whole bill.'
    ),
    properties={
        'development_cost': {
            'type': 'number',
            'minimum': 0,
            'description': 'Estimated cost of development works in dollars. Use 0 for a change of use with no works.',
        },
        'development_type': {
            'type': 'string',
            'description': (
                "Optional but strongly recommended. The proposed use, e.g. 'cafe', 'shop', "
                "'office', 'warehouse', 'dwelling house'. Unlocks the Section 7.11 contribution."
            ),
        },
        'gross_floor_area_m2': {
            'type': 'number',
            'minimum': 0,
            'description': 'Optional. Gross floor area, for uses charged per 100m2 (all commercial and industrial).',
        },
        'dwellings': {
            'type': 'integer',
            'minimum': 0,
            'description': 'Optional. Number of dwellings, for residential development.',
        },
        'beds_or_sites': {
            'type': 'integer',
            'minimum': 0,
            'description': 'Optional. Beds or sites, for tourist and visitor accommodation.',
        },
        'catchment': {
            'type': 'string',
            'description': (
                "Optional. Contribution catchment: 'urban', 'rural_north' or 'rural_south'. "
                'Not guessed — without it every catchment is shown, because rural rates are '
                'higher than urban for retail.'
            ),
        },
        'existing_use': {
            'type': 'string',
            'description': (
                "Optional. For a change of use, the use already lawfully on the site — e.g. "
                "'shop' becoming a cafe. Applies the section 2.7 allowance."
            ),
        },
        # Without these the previous use was *assumed* to occupy the same floor
        # area as the proposal, so a restaurant expanding 100m² -> 140m² netted
        # to zero against a real increase of about $8,000. The assumption is
        # right for the ordinary same-tenancy change of use and is kept, but it
        # was previously uncorrectable: the answer said "supply the previous
        # floor area if it differed" and there was no argument to supply it in.
        # ROADMAP.md S3.
        'existing_gross_floor_area_m2': {
            'type': 'number',
            'minimum': 0,
            'description': (
                'Optional, for a change of use. Gross floor area of the previous lawful use, '
                'if it differed from the proposal. The contribution is charged on the increase '
                'in demand, so an expansion is charged only on the extra area. Defaults to the '
                "proposal's own floor area, which is the ordinary same-tenancy case."
            ),
        },
        'existing_dwellings': {
            'type': 'integer',
            'minimum': 0,
            'description': 'Optional, for a change of use. Dwellings in the previous lawful use, if it differed.',
        },
        'existing_beds_or_sites': {
            'type': 'integer',
            'minimum': 0,
            'description': 'Optional, for a change of use. Beds or sites in the previous lawful use, if it differed.',
        },
        'involves_building_work': {
            'type': 'boolean',
            'description': (
                'Optional, defaults true. Set false for a change of use with no building '
                'work, subdivision or demolition — a different, flat statutory fee applies.'
            ),
        },
        'is_dwelling': {
            'type': 'boolean',
            'description': "Optional. A dwelling costing $100,000 or less has Council's own fixed fee.",
        },
    },
    required=['development_cost'],
)
def calculate_da_fees(arguments: dict):
    catchment = arguments.get("catchment")
    if catchment and catchment not in CATCHMENTS:
        return [TextContent(type="text", text=json.dumps({
            "error": f"Unknown catchment '{catchment}'.",
            "catchments": list(CATCHMENTS),
            "note": (
                "Which catchment a site falls in comes from Figures 2 and 3 of the Section "
                "7.11 plan. Omit this argument to see all three."
            ),
        }, indent=2))]

    cost = float(arguments.get("development_cost", 0))
    counts = {
        key: arguments[key]
        for key in ("gross_floor_area_m2", "dwellings", "beds_or_sites")
        if arguments.get(key)
    }
    # The previous use's own measures, where they differ from the proposal's.
    # `estimate_contribution` has taken `existing_counts` all along and nothing
    # ever passed it, so the same-floor-area assumption could not be corrected.
    existing_counts = {
        key: arguments[f"existing_{key}"]
        for key in ("gross_floor_area_m2", "dwellings", "beds_or_sites")
        if arguments.get(f"existing_{key}")
    } or None

    result = estimate_total_cost(
        cost,
        development_type=arguments.get("development_type"),
        counts=counts,
        catchment=catchment,
        existing_use=arguments.get("existing_use"),
        existing_counts=existing_counts,
        involves_building_work=arguments.get("involves_building_work", True),
        is_dwelling=arguments.get("is_dwelling", False),
    )
    # This tool answered "what is the lodgement fee" until 2026-08-02 and now
    # answers "what will this cost", so the payload it returns is a different
    # shape. The server behind it is a deployed public endpoint, so the two keys
    # a caller is most likely to index on stay exactly where they were, and the
    # whole of the previous payload stays available under one key.
    detail = calculate_da_fee(
        cost,
        arguments.get("involves_building_work", True),
        arguments.get("is_dwelling", False),
    )
    result["estimated_fee"] = detail["estimated_fee"]
    result["fee_schedule_year"] = detail["fee_schedule_year"]
    result["da_lodgement_fee_detail"] = detail
    if "⚠️ FEE SCHEDULE OUT OF DATE" in detail:
        result["⚠️ FEE SCHEDULE OUT OF DATE"] = detail["⚠️ FEE SCHEDULE OUT OF DATE"]
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
