# PerpSpread MCP Server & Reproducible Funding Audit Toolkit

[![MCP Protocol](https://img.shields.io/badge/MCP-2025--03--26%20Streamable%20HTTP-2563eb)](https://modelcontextprotocol.io)
[![Hosted Endpoint](https://img.shields.io/badge/Endpoint-perpspread.com%2Fapi%2Fmcp-10b981)](https://perpspread.com/api/mcp)
[![Venues](https://img.shields.io/badge/Venues-7%20CEX%20%2B%20Perp%20DEX-6366f1)](https://perpspread.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

Official hosted **Model Context Protocol (MCP)** server manifest (`server.json`), client configurations, and zero-dependency funding reconciliation scripts for **[PerpSpread](https://perpspread.com)** — an independent 7-venue crypto perpetual futures funding-rate arbitrage, cash-and-carry, and Top-20 L2 orderbook slippage terminal.

Connect Claude, Cursor, Codex CLI, Windsurf, or any MCP-compatible AI agent directly to live cross-exchange funding spreads and orderbook depth with **zero local installation** and **no API key required** on the free tier (`15 req/min`).

---

## Live Terminal & Endpoints

- **Web Terminal**: [https://perpspread.com](https://perpspread.com)
- **Hosted MCP Endpoint (Streamable HTTP / JSON-RPC 2.0)**: `https://perpspread.com/api/mcp`
- **CEX vs Perp DEX Live Monitor**: [https://perpspread.com/funding/cex-vs-dex](https://perpspread.com/funding/cex-vs-dex)
- **BTC Live Spread & L2 Orderbook Depth**: [https://perpspread.com/funding/btc](https://perpspread.com/funding/btc)
- **Reproducible 7D BTC Settled Reconciliation Audit**: [https://perpspread.com/audit/btc-7d](https://perpspread.com/audit/btc-7d)
- **7-Venue Perpetual Fee & Breakeven Calculator**: [https://perpspread.com/fee-calculator](https://perpspread.com/fee-calculator)
- **Methodology & Fee Baseline**: [https://perpspread.com/methodology](https://perpspread.com/methodology)
- **Machine-Readable Site Guide (`llms.txt`)**: [https://perpspread.com/llms.txt](https://perpspread.com/llms.txt)

---

## Covered Venues (7)

| Type | Venues | Settlement Cadence | Standard VIP 0 Taker Fee |
| --- | --- | --- | --- |
| **CEX (5)** | OKX, Binance Futures, Bybit, Bitget, Gate.io | 4h / 8h (normalized to 365d APR) | `0.050%` / `0.050%` / `0.055%` / `0.060%` / `0.050%` |
| **Perp DEX (2)** | Hyperliquid, Aster | 1h / 8h (normalized to 365d APR) | `0.045%` / `0.035%` |

> **Neutrality Convention**: All default rankings, breakeven days, simulators, and MCP tools use **Standard VIP 0 taker fees** and **`1×` delta-neutral sizing** (`$10,000` total capital = `$5,000` Long + `$5,000` Short). Optional OKX 20% new-user fee rebate (`0.040%` taker) is strictly opt-in (`okx_rebate: true`).

---

## Tools

All 5 tools are **read-only**, **idempotent**, and return structured JSON payloads from live exchange feeds (`protocolVersion: 2025-03-26`).

- **`get_top_funding_spreads`** — Scan live cross-exchange perpetual funding rate arbitrage spreads across all 7 venues with liquidity filters, entry basis, and breakeven days.
- **`get_symbol_funding_breakdown`** — Inspect all 7 venues' live funding rates, settlement intervals (`1h`/`4h`/`8h`), mark prices, 24h volume, and 7D/30D realized funding APR for any coin.
- **`audit_orderbook_slippage`** — Fetch live Top-20 L2 orderbooks across the optimal Long and Short venues for a symbol to measure real bid/ask depth and execution slippage in basis points.
- **`calculate_rotation_breakeven`** — Model whether rotating from an active delta-neutral funding-arb pair (`A`) into a new target symbol (`B`) pays back 4-leg fees, slippage, and exit/entry price basis.
- **`get_cash_and_carry_spreads`** — Discover live single-venue Spot-Long / Perp-Short positive funding cash-and-carry spreads across CEX venues.

### Tool Parameters Reference

| Tool | Required Params | Optional Params |
| --- | --- | --- |
| `get_top_funding_spreads` | *(none)* | `min_volume_usd` (number, default `1000000`), `exchange` (`okx` \| `binance` \| `bybit` \| `bitget` \| `gate` \| `hyperliquid` \| `aster`), `limit` (`1–50`, default `10`) |
| `get_symbol_funding_breakdown` | `symbol` (e.g. `"BTC"`, `"ETH"`, `"SOL"`, `"HYPE"`) | *(none)* |
| `audit_orderbook_slippage` | `symbol` (e.g. `"BTC"`, `"SOL"`) | *(none)* |
| `calculate_rotation_breakeven` | `current_symbol`, `current_long`, `current_short`, `target_symbol` | `capital_usd` (default `20000`), `execution` (`"taker"` \| `"maker"`, default `"taker"`), `okx_rebate` (boolean, default `false`) |
| `get_cash_and_carry_spreads` | *(none)* | `min_volume_usd` (number, default `1000000`), `limit` (`1–30`, default `10`) |

### Example Prompts for Your AI Agent

- *"Find the top 5 cross-exchange funding spreads involving Hyperliquid with at least $5M daily volume, then audit L2 orderbook slippage on the #1 result."*
- *"Compare live funding APR vs 7-day realized settled APR for BTC and SOL across all 7 venues so I don't chase a one-hour funding spike."*
- *"I am holding a $20,000 delta-neutral position long OKX / short Binance on ETH. Calculate whether rotating into SOL pays back 4-leg taker fees and slippage."*
- *"Show me the best Spot-Long / Perp-Short cash-and-carry yields right now with at least $10M 24h perp volume."*

---

## Quick Start (Client Setup)

No local build, Docker container, or npm install is needed — point your MCP client to the hosted Streamable HTTP endpoint `https://perpspread.com/api/mcp`.

### Claude Code CLI

```bash
claude mcp add --transport http perpspread https://perpspread.com/api/mcp
```

### Claude Desktop

Add to `claude_desktop_config.json` (template in [`configs/claude_desktop_config.json`](./configs/claude_desktop_config.json)):

```json
{
  "mcpServers": {
    "perpspread": {
      "url": "https://perpspread.com/api/mcp"
    }
  }
}
```

### Cursor / Windsurf / Cline

Add to `.cursor/mcp.json` (or your editor's MCP settings; template in [`configs/cursor_mcp.json`](./configs/cursor_mcp.json)):

```json
{
  "mcpServers": {
    "perpspread": {
      "url": "https://perpspread.com/api/mcp"
    }
  }
}
```

### OpenAI Codex CLI

Add to `~/.codex/config.toml` (template in [`configs/codex_config.toml`](./configs/codex_config.toml)):

```toml
[mcp_servers.perpspread]
url = "https://perpspread.com/api/mcp"
# Optional: unlock 60 req/min + 30D history via https://perpspread.com/pricing
# http_headers = { "X-API-Key" = "ps_live_your_key_here" }
```

### Optional API Key (Higher Rate Limits)

| Tier | Rate Limit | History Window | Auth Header |
| --- | --- | --- | --- |
| **Free (No Auth)** | `15 req/min` | 7 days settled & 15m snapshots | *(none required)* |
| **Developer (`ps_live_`)** | `60 req/min` | 30 days settled & snapshots | `X-API-Key: ps_live_...` |

Get a free API key at [perpspread.com/pricing](https://perpspread.com/pricing).

---

## Verify the Live MCP Endpoint

Run the zero-dependency Python 3 smoke test (performs `GET` discovery, JSON-RPC `initialize`, `notifications/initialized`, `tools/list`, and live `tools/call`):

```bash
python3 scripts/mcp_smoke_test.py
```

Or test directly with `curl`:

```bash
# 1. Server discovery manifest
curl -s https://perpspread.com/api/mcp | jq .

# 2. List all 5 MCP tools via JSON-RPC 2.0
curl -s -X POST https://perpspread.com/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | jq .
```

---

## Reproducible 7-Day Settled Funding Audit (Python & Node.js)

Independently verify PerpSpread's [`/audit/btc-7d`](https://perpspread.com/audit/btc-7d) numbers against raw settled exchange prints. Both scripts use only standard library modules (zero external packages):

```bash
# Python 3 (defaults to BTC; pass any symbol such as ETH, SOL, HYPE)
python3 scripts/reconcile_btc_7d.py BTC

# Node.js 18+
node scripts/reconcile_btc_7d.mjs BTC
```

What the audit verifies end-to-end:
1. Fetches all 7 venues' settled funding timestamps over the last 7 days from `/api/v1/history?symbol=BTC&days=7&source=settled&format=json` (typically `168` hourly prints on Hyperliquid vs `21` 8-hour prints on CEXs/Aster).
2. Recomputes per-venue cumulative 7-day funding `cum7dRate = Σ(rawRate)` and annualized `avg7dApr = cum7dRate × (365 / 7)` directly from the raw print array.
3. Reconciles `realized7dSpreadApr = shortAvg7dApr − longAvg7dApr` against the API's reported figure and asserts numerical consistency.
4. Prints a side-by-side **`$10,000` (`1×` · `$5,000/leg`) Standard VIP 0** P&L breakdown comparing **Live Snapshot Projection** vs **7D Realized Settled Baseline** so transient funding spikes are never confused with sustained carry.

---

## Direct REST, CSV & DuneSQL LiveFetch

All public data endpoints are permitted in [`robots.txt`](https://perpspread.com/robots.txt) and work natively inside **DuneSQL `http_get()`** dashboards:

```bash
# Live 7-venue spreads (filter by minVol or single symbol)
curl -s "https://perpspread.com/api/v1/spreads?minVol=1000000&limit=25"

# Raw 7-day settled exchange funding prints (JSON)
curl -s "https://perpspread.com/api/v1/history?symbol=BTC&days=7&source=settled&format=json"

# Persisted 15-minute spread & Open Interest snapshots (JSON or CSV)
curl -s "https://perpspread.com/api/v1/history?symbol=BTC&days=7&format=json"
curl -s "https://perpspread.com/api/v1/history?symbol=BTC&days=7&format=csv"
```

```sql
-- DuneSQL LiveFetch example (paste directly into Dune)
SELECT http_get('https://perpspread.com/api/v1/spreads?minVol=1000000&limit=10') AS raw_json;
```

---

## Official MCP Registry Metadata

This repository includes a schema-compliant [`server.json`](./server.json) (`2025-12-11` schema) for publishing to the [Official MCP Registry](https://registry.modelcontextprotocol.io):

```bash
mcp-publisher login github
mcp-publisher publish
```

---

## License

MIT — see [`LICENSE`](./LICENSE).
