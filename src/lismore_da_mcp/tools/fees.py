"""DA lodgement fees."""

import json

from mcp.types import TextContent

from lismore_da_mcp.fees import calculate_da_fee
from lismore_da_mcp.registry import tool


@tool(
    name='calculate_da_fees',
    description='Calculate the Development Application lodgement fee based on estimated development cost.',
    properties={
        'development_cost': {'type': 'number', 'description': 'Estimated cost of development works in dollars'},
    },
    required=['development_cost'],
)
def calculate_da_fees(arguments: dict):
    cost = arguments.get("development_cost", 0)
    result = calculate_da_fee(float(cost))
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]
