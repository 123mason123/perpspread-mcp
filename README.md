# PerpSpread MCP & Reproducible Funding Audit Examples

Official Model Context Protocol (MCP) client configurations and zero-dependency audit scripts for **[PerpSpread](https://perpspread.com)** — an independent 7-venue perpetual futures funding-rate, cash-and-carry, and Top-20 L2 orderbook slippage terminal.

- **Live Terminal**: https://perpspread.com
- **BTC Live Spread & Depth**: https://perpspread.com/funding/btc
- **Live Reproducible BTC 7D Reconciliation Audit**: https://perpspread.com/audit/btc-7d
- **Methodology & Fee Baseline**: https://perpspread.com/methodology
- **Hosted MCP Endpoint (Streamable HTTP / JSON-RPC 2.0)**: `https://perpspread.com/api/mcp`
- **Machine-Readable Site Guide**: https://perpspread.com/llms.txt

---

## Covered Venues (7)

| Type | Exchanges | Settlement Cadence | Standard VIP 0 Taker Fee |
| --- | --- | --- | --- |
| **CEX (5)** | OKX, Binance Futures, Bybit, Bitget, Gate.io | 4h / 8h (normalized to 365d APR) | `0.050%` / `0.050%` / `0.055%` / `0.060%` / `0.050%` |
| **Perp DEX (2)** | Hyperliquid, Aster | 1h / 8h (normalized to 365d APR) | `0.045%` / `0.035%` |

> **Neutrality Convention**: All default rankings, breakeven days, simulators, and MCP tools use **Standard VIP 0 taker fees** and **`1×` delta-neutral sizing** (`$10,000` total capital = `$5,000` Long + `$5,000` Short). Optional OKX 20% new-user fee rebate (`0.040%` taker) is strictly opt-in (`okx_rebate: true`).

---

## 1. Connect to the Hosted MCP Server

No local server installation or API key is required on the free tier (`15 req/min`). Higher limits (`60 req/min` + 30-day history) are available via a free `ps_live_` key at [perpspread.com/pricing](https://perpspread.com/pricing).

### Available MCP Tools (`https://perpspread.com/api/mcp`)

1. `get_top_funding_spreads` — Scan live cross-exchange funding spreads across all 7 venues with minimum 24h volume and exchange filters.
2. `get_symbol_funding_breakdown` — Full 7-venue live rates, settlement intervals, mark prices, 24h volume, open interest, and 7D/30D realized funding APR for any coin.
3. `audit_orderbook_slippage` — Walk live Top-20 L2 orderbooks on the optimal Long & Short legs to measure real entry/exit slippage in basis points.
4. `calculate_rotation_breakeven` — Evaluate whether rotating an existing delta-neutral pair into a new target pays back 4-leg fees, L2 slippage, and exit/entry basis.
5. `get_cash_and_carry_spreads` — Scan single-venue Spot-Long / Perp-Short positive funding cash-and-carry spreads.

### Ready-to-Use Client Configs

- **Claude Desktop**: [`configs/claude_desktop_config.json`](./configs/claude_desktop_config.json)
- **Cursor**: [`configs/cursor_mcp.json`](./configs/cursor_mcp.json)
- **Codex CLI**: [`configs/codex_config.toml`](./configs/codex_config.toml)

```json
{
  "mcpServers": {
    "perpspread": {
      "url": "https://perpspread.com/api/mcp"
    }
  }
}
```

Test the live MCP endpoint immediately (Python 3 stdlib, zero external packages):

```bash
python3 scripts/mcp_smoke_test.py
```

---

## 2. Reproducible 7-Day Settled Funding Audit (Python & Node.js)

Verify PerpSpread's [`/audit/btc-7d`](https://perpspread.com/audit/btc-7d) numbers independently against raw settled exchange prints. Both scripts use only standard library modules (zero dependencies):

```bash
# Python 3 (defaults to BTC; pass any symbol such as ETH, SOL, HYPE)
python3 scripts/reconcile_btc_7d.py BTC

# Node.js 18+
node scripts/reconcile_btc_7d.mjs BTC
```

What the script verifies end-to-end:
1. Fetches all 7 venues' settled funding timestamps over the last 7 days from `/api/v1/history?symbol=BTC&days=7&source=settled&format=json` (typically `168` hourly prints on Hyperliquid vs `21` 8-hour prints on CEXs/Aster).
2. Recomputes per-venue cumulative 7-day funding `cum7dRate = Σ(rawRate)` and annualized `avg7dApr = cum7dRate × (365 / 7)` directly from the raw print array.
3. Reconciles `realized7dSpreadApr = shortAvg7dApr − longAvg7dApr` against the API's reported figure and asserts numerical consistency.
4. Prints a side-by-side **`$10,000` (`1×` · `$5,000/leg`) Standard VIP 0** P&L breakdown comparing **Live Snapshot Projection** vs **7D Realized Settled Baseline** so transient funding spikes are never confused with sustained 7-day carry.

---

## 3. Direct REST & CSV Endpoints (No Auth Required)

All public data endpoints are permitted in [`robots.txt`](https://perpspread.com/robots.txt):

```bash
# Live 7-venue spreads (all coins or single symbol)
curl -s "https://perpspread.com/api/v1/spreads?symbol=BTC"

# Raw 7-day settled exchange funding prints (JSON)
curl -s "https://perpspread.com/api/v1/history?symbol=BTC&days=7&source=settled&format=json"

# Persisted 15-minute spread & Open Interest snapshots (JSON or CSV)
curl -s "https://perpspread.com/api/v1/history?symbol=BTC&days=7&format=json"
curl -s "https://perpspread.com/api/v1/history?symbol=BTC&days=7&format=csv"
```

---

## License

MIT — see [`LICENSE`](./LICENSE).
