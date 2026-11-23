#!/usr/bin/env python3
"""
End-to-end reproducible 7-day settled funding rate audit for PerpSpread.
Zero external dependencies (Python 3 stdlib only).

Usage:
    python3 scripts/reconcile_btc_7d.py [SYMBOL]

Default SYMBOL is BTC. Fetches raw 7-day settled exchange funding prints from
https://perpspread.com/api/v1/history?symbol=BTC&days=7&source=settled&format=json
and independently recomputes per-venue cumulative 7D rates, 7D Realized Spread APR,
and $10,000 (1x = $5,000/leg) Standard VIP 0 taker PnL vs Live Snapshot projection.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

BASE_URL = "https://perpspread.com"
CAPITAL_USD = 10_000.0
LEG_NOTIONAL_USD = CAPITAL_USD / 2.0  # 1x delta-neutral = $5,000 long + $5,000 short

# Published Standard VIP 0 taker fee rates across all 7 covered venues
STANDARD_VIP0_TAKER = {
    "okx": 0.0005,
    "binance": 0.0005,
    "bybit": 0.00055,
    "bitget": 0.0006,
    "gate": 0.0005,
    "hyperliquid": 0.00045,
    "aster": 0.00035,
}


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "perpspread-mcp-audit/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fmt_signed_usd(val: float) -> str:
    sign = "+" if val >= 0 else "-"
    return f"{sign}${abs(val):.2f}"


def main() -> int:
    symbol = (sys.argv[1] if len(sys.argv) > 1 else "BTC").strip().upper()
    q_sym = urllib.parse.quote(symbol)

    settled_url = f"{BASE_URL}/api/v1/history?symbol={q_sym}&days=7&source=settled&format=json"
    spread_url = f"{BASE_URL}/api/v1/spreads?symbol={q_sym}"

    settled = fetch_json(settled_url)
    spread_payload = fetch_json(spread_url)

    if not settled.get("ok") or not spread_payload.get("ok") or not spread_payload.get("data"):
        print(f"Error: symbol {symbol} unavailable from PerpSpread API", file=sys.stderr)
        return 1

    opp = spread_payload["data"][0]
    long_ex = opp["longExchange"]
    short_ex = opp["shortExchange"]
    live_spread_apr = opp["spreadAprPct"] / 100.0
    entry_basis_ratio = (opp.get("entryBasisPct") or 0.0) / 100.0

    print(f"=== PerpSpread Reproducible 7D Settled Funding Audit ({symbol}) ===")
    print(f"Snapshot UTC : {spread_payload['updatedAt']}")
    print(f"Optimal Pair : Long {long_ex} ({opp['longIntervalHours']}h) / Short {short_ex} ({opp['shortIntervalHours']}h)")
    print(f"Web Audit URL: {BASE_URL}/audit/btc-7d" if symbol == "BTC" else f"Terminal URL : {BASE_URL}/funding/{symbol.lower()}")
    print()

    print(f"{'Venue':<13} {'Status':<8} {'7D Prints':>9} {'Sum 7D Rate':>13} {'Recomp APR':>12} {'API APR':>10} {'Delta':>9}")
    print("-" * 80)

    recomp_by_ex: dict[str, dict[str, float]] = {}
    for h in settled["histories"]:
        ex = h["exchange"]
        status = h["status"]
        pts = h.get("points", [])
        if status != "ok":
            print(f"{ex:<13} {status:<8} {'—':>9} {'—':>13} {'—':>12} {'—':>10} {'—':>9}")
            continue

        # Recompute directly from the raw settled print array
        cum_7d_rate = sum(p["ratePct"] / 100.0 for p in pts)
        recomp_apr_pct = cum_7d_rate * (365.0 / 7.0) * 100.0
        api_apr_pct = float(h["avg7dAprPct"])
        delta_pct = recomp_apr_pct - api_apr_pct

        recomp_by_ex[ex] = {
            "cum7d": cum_7d_rate,
            "aprPct": recomp_apr_pct,
            "prints": float(len(pts)),
        }

        print(
            f"{ex:<13} {status:<8} {len(pts):>9d} "
            f"{cum_7d_rate * 100:>+12.5f}% {recomp_apr_pct:>+11.3f}% "
            f"{api_apr_pct:>+9.3f}% {delta_pct:>+8.3f}%"
        )

        # Allow tiny tolerance (< 0.25% APR) from 5-decimal rounding & 1-second boundary drift
        assert abs(delta_pct) < 0.25, f"APR mismatch on {ex}: {recomp_apr_pct:.3f}% vs {api_apr_pct:.3f}%"

    print()

    if long_ex in recomp_by_ex and short_ex in recomp_by_ex:
        net_cum_7d = recomp_by_ex[short_ex]["cum7d"] - recomp_by_ex[long_ex]["cum7d"]
        recomp_realized_spread_apr_pct = net_cum_7d * (365.0 / 7.0) * 100.0
        api_realized_spread_apr_pct = settled.get("realized7dSpreadAprPct")

        long_taker = STANDARD_VIP0_TAKER[long_ex]
        short_taker = STANDARD_VIP0_TAKER[short_ex]
        round_trip_fees_usd = LEG_NOTIONAL_USD * 2.0 * (long_taker + short_taker)
        entry_basis_usd = LEG_NOTIONAL_USD * entry_basis_ratio

        realized_7d_gross_usd = LEG_NOTIONAL_USD * net_cum_7d
        realized_7d_net_usd = realized_7d_gross_usd + entry_basis_usd - round_trip_fees_usd

        live_7d_gross_usd = LEG_NOTIONAL_USD * live_spread_apr * (7.0 / 365.0)
        live_7d_net_usd = live_7d_gross_usd + entry_basis_usd - round_trip_fees_usd

        print("--- Active Pair Reconciliation ($10,000 at 1x = $5,000/leg · Standard VIP 0) ---")
        print(f"Recomputed 7D Realized Spread APR : {recomp_realized_spread_apr_pct:+.3f}%")
        if api_realized_spread_apr_pct is not None:
            print(f"API Reported 7D Realized APR      : {api_realized_spread_apr_pct:+.3f}%")
            assert abs(recomp_realized_spread_apr_pct - api_realized_spread_apr_pct) < 0.35
        print(f"Live Snapshot Spread APR          : {live_spread_apr * 100:+.3f}%")
        print(f"Round-Trip VIP 0 Taker Fees       : -${round_trip_fees_usd:.2f} ({long_ex} {long_taker*100:.3f}% + {short_ex} {short_taker*100:.3f}%)")
        print(f"Mark-Price Entry Basis            : {fmt_signed_usd(entry_basis_usd)}")
        print(f"7D Realized Baseline Net PnL      : {fmt_signed_usd(realized_7d_net_usd)} (Gross {fmt_signed_usd(realized_7d_gross_usd)})")
        print(f"Live Snapshot 7D Extrapolation    : {fmt_signed_usd(live_7d_net_usd)} (Gross {fmt_signed_usd(live_7d_gross_usd)})")
        print("\nOK: Raw settled funding prints reconciled cleanly against PerpSpread API.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
