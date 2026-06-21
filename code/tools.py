from __future__ import annotations
import json
import random

from .db import get_connection

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "roll_dice",
            "description": (
                "Roll one or more dice. Use for any dice roll in the Cyberpunk RED system "
                "(d6, d10, etc.). Always call this instead of inventing results."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer", "description": "Number of dice to roll"},
                    "sides": {"type": "integer", "description": "Sides per die (e.g. 10 for d10, 6 for d6)"},
                },
                "required": ["count", "sides"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_gigs",
            "description": (
                "Fetch the current live gig postings from the fixer board database. "
                "Call this whenever the user asks what jobs are available, what's on the board, "
                "or what gigs are up right now. Pass a district to filter by location "
                "(e.g. PACIFICA, WATSON, WESTBROOK, HEYWOOD, CITY CENTER, SANTO DOMINGO, BADLANDS). "
                "Do not answer from general knowledge — "
                "use this tool to get the actual current listings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "district": {
                        "type": "string",
                        "description": "Optional district filter. Omit to return gigs from all districts.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": (
                "Fetch the current live news articles from the Night City feed database. "
                "Call this whenever the user asks what's happening in Night City, what's in the news, "
                "or what the latest screamsheets say. Pass a district to filter by location. "
                "Do not answer from general knowledge — "
                "use this tool to get the actual current headlines."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "district": {
                        "type": "string",
                        "description": "Optional district filter. Omit to return news from all districts.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_market",
            "description": (
                "Fetch the current live black market listings from the Night Markets database. "
                "Call this whenever the user asks what's for sale, what's available on the markets, "
                "or what listings are up right now. Pass a district to filter by location. "
                "Do not answer from general knowledge — "
                "use this tool to get the actual current inventory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "district": {
                        "type": "string",
                        "description": "Optional district filter. Omit to return listings from all districts.",
                    },
                },
                "required": [],
            },
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    if name == "roll_dice":
        count = max(1, int(args.get("count", 1)))
        sides = max(2, int(args.get("sides", 10)))
        rolls = [random.randint(1, sides) for _ in range(count)]
        return json.dumps({"dice": f"{count}d{sides}", "rolls": rolls, "total": sum(rolls)})

    if name == "get_gigs":
        district = args.get("district", "").strip().upper()
        with get_connection() as conn:
            if district:
                rows = conn.execute(
                    "SELECT title, category, fixer, payout, risk, district, description "
                    "FROM gigs WHERE UPPER(district) = ? ORDER BY created_at DESC LIMIT 10",
                    (district,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT title, category, fixer, payout, risk, district, description "
                    "FROM gigs ORDER BY created_at DESC LIMIT 10"
                ).fetchall()
        return json.dumps([dict(r) for r in rows])

    if name == "get_news":
        district = args.get("district", "").strip().upper()
        with get_connection() as conn:
            if district:
                rows = conn.execute(
                    "SELECT title, byline, body, district, category "
                    "FROM news WHERE UPPER(district) = ? ORDER BY created_at DESC LIMIT 10",
                    (district,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT title, byline, body, district, category "
                    "FROM news ORDER BY created_at DESC LIMIT 10"
                ).fetchall()
        return json.dumps([dict(r) for r in rows])

    if name == "get_market":
        district = args.get("district", "").strip().upper()
        with get_connection() as conn:
            if district:
                rows = conn.execute(
                    "SELECT name, category, description, price, seller, district, rarity, condition "
                    "FROM market_items WHERE UPPER(district) = ? ORDER BY created_at DESC LIMIT 10",
                    (district,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT name, category, description, price, seller, district, rarity, condition "
                    "FROM market_items ORDER BY created_at DESC LIMIT 10"
                ).fetchall()
        return json.dumps([dict(r) for r in rows])

    return json.dumps({"error": f"Unknown tool: {name}"})
