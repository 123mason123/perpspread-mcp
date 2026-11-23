#!/usr/bin/env python3
"""
Smoke test for PerpSpread's hosted Streamable HTTP MCP server (https://perpspread.com/api/mcp).
Zero external dependencies (Python 3 stdlib only).

Usage:
    python3 scripts/mcp_smoke_test.py
"""

from __future__ import annotations

import json
import os
import urllib.request

MCP_URL = "https://perpspread.com/api/mcp"


def rpc_call(method: str, params: dict, req_id: int) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "perpspread-mcp-smoke/1.0",
    }
    api_key = os.environ.get("PERPSPREAD_API_KEY")
    if api_key:
        headers["X-API-Key"] = api_key

    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method,
        "params": params,
    }).encode("utf-8")

    req = urllib.request.Request(MCP_URL, data=payload, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "error" in data:
        raise RuntimeError(f"MCP error for {method}: {data['error']}")
    return data["result"]


def main() -> int:
    # 1. List available MCP tools
    listed = rpc_call("tools/list", {}, 1)
    tool_names = [t["name"] for t in listed.get("tools", [])]
    print(f"1. Connected to {MCP_URL}")
    print(f"   Available tools ({len(tool_names)}): {', '.join(tool_names)}")
    assert len(tool_names) == 5, f"Expected 5 MCP tools, got {tool_names}"

    # 2. Fetch top 3 funding spreads (>= $5M 24h volume)
    top_res = rpc_call(
        "tools/call",
        {
            "name": "get_top_funding_spreads",
            "arguments": {"min_volume_usd": 5_000_000, "limit": 3},
        },
        2,
    )
    top_data = json.loads(top_res["content"][0]["text"])
    print(f"\n2. Top 3 live spreads (>= $5M 24h vol · updated {top_data.get('updatedAt')}):")
    for item in top_data.get("opportunities", []):
        print(
            f"   - {item['symbol']:<6} Long {item['longExchange']:<11} / Short {item['shortExchange']:<11} "
            f"Spread {item['spreadAprPct']:+.2f}% APR  Breakeven {item['breakevenDays']}d"
        )

    # 3. Run live Top-20 L2 orderbook slippage audit for BTC ($5,000 per leg)
    ob_res = rpc_call(
        "tools/call",
        {
            "name": "audit_orderbook_slippage",
            "arguments": {"symbol": "BTC", "notional_usd": 5000},
        },
        3,
    )
    ob_data = json.loads(ob_res["content"][0]["text"])
    print("\n3. Live BTC Top-20 L2 orderbook audit ($5,000/leg):")
    print("  ", json.dumps(ob_data, indent=2)[:600])
    print("\nOK: All PerpSpread MCP JSON-RPC calls succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
