#!/usr/bin/env node
/**
 * End-to-end reproducible 7-day settled funding rate audit for PerpSpread.
 * Zero external dependencies (Node.js 18+ built-in fetch).
 *
 * Usage:
 *   node scripts/reconcile_btc_7d.mjs [SYMBOL]
 */

const BASE_URL = "https://perpspread.com";
const CAPITAL_USD = 10_000;
const LEG_NOTIONAL_USD = CAPITAL_USD / 2;

const STANDARD_VIP0_TAKER = {
  okx: 0.0005,
  binance: 0.0005,
  bybit: 0.00055,
  bitget: 0.0006,
  gate: 0.0005,
  hyperliquid: 0.00045,
  aster: 0.00035,
};

async function fetchJson(url) {
  const res = await fetch(url, {
    headers: {
      Accept: "application/json",
      "User-Agent": "perpspread-mcp-audit/1.0",
    },
  });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} for ${url}`);
  }
  return res.json();
}

function fmtSigned(val, digits = 3, suffix = "%") {
  return `${val >= 0 ? "+" : ""}${val.toFixed(digits)}${suffix}`;
}

async function main() {
  const symbol = (process.argv[2] || "BTC").trim().toUpperCase();
  const q = encodeURIComponent(symbol);

  const [settled, spreadPayload] = await Promise.all([
    fetchJson(`${BASE_URL}/api/v1/history?symbol=${q}&days=7&source=settled&format=json`),
    fetchJson(`${BASE_URL}/api/v1/spreads?symbol=${q}`),
  ]);

  if (!settled.ok || !spreadPayload.ok || !spreadPayload.data?.length) {
    console.error(`Error: symbol ${symbol} unavailable from PerpSpread API`);
    process.exit(1);
  }

  const opp = spreadPayload.data[0];
  const longEx = opp.longExchange;
  const shortEx = opp.shortExchange;
  const liveSpreadApr = opp.spreadAprPct / 100;
  const entryBasisRatio = (opp.entryBasisPct ?? 0) / 100;

  console.log(`=== PerpSpread Reproducible 7D Settled Funding Audit (${symbol}) ===`);
  console.log(`Snapshot UTC : ${spreadPayload.updatedAt}`);
  console.log(`Optimal Pair : Long ${longEx} (${opp.longIntervalHours}h) / Short ${shortEx} (${opp.shortIntervalHours}h)\n`);

  const byEx = new Map();
  for (const h of settled.histories) {
    if (h.status !== "ok") continue;
    const cum7d = h.points.reduce((acc, p) => acc + p.ratePct / 100, 0);
    const recompAprPct = cum7d * (365 / 7) * 100;
    const delta = recompAprPct - h.avg7dAprPct;
    byEx.set(h.exchange, { cum7d, recompAprPct, prints: h.points.length });
    console.log(
      `${h.exchange.padEnd(12)} prints=${String(h.points.length).padStart(3)}  ` +
        `cum7d=${fmtSigned(cum7d * 100, 5)}  recompAPR=${fmtSigned(recompAprPct, 3)}  ` +
        `apiAPR=${fmtSigned(h.avg7dAprPct, 3)}  delta=${fmtSigned(delta, 3)}`,
    );
    if (Math.abs(delta) >= 0.25) {
      throw new Error(`APR mismatch on ${h.exchange}: ${recompAprPct} vs ${h.avg7dAprPct}`);
    }
  }

  const longStats = byEx.get(longEx);
  const shortStats = byEx.get(shortEx);
  if (longStats && shortStats) {
    const netCum7d = shortStats.cum7d - longStats.cum7d;
    const realizedSpreadAprPct = netCum7d * (365 / 7) * 100;
    const roundTripFeesUsd =
      LEG_NOTIONAL_USD * 2 * (STANDARD_VIP0_TAKER[longEx] + STANDARD_VIP0_TAKER[shortEx]);
    const entryBasisUsd = LEG_NOTIONAL_USD * entryBasisRatio;
    const realized7dGrossUsd = LEG_NOTIONAL_USD * netCum7d;
    const realized7dNetUsd = realized7dGrossUsd + entryBasisUsd - roundTripFeesUsd;
    const live7dGrossUsd = LEG_NOTIONAL_USD * liveSpreadApr * (7 / 365);
    const live7dNetUsd = live7dGrossUsd + entryBasisUsd - roundTripFeesUsd;

    console.log(`\n--- Active Pair ($10,000 at 1x = $5,000/leg · Standard VIP 0) ---`);
    console.log(`Recomputed 7D Realized Spread APR : ${fmtSigned(realizedSpreadAprPct, 3)}`);
    console.log(`API Reported 7D Realized APR      : ${fmtSigned(settled.realized7dSpreadAprPct, 3)}`);
    console.log(`Live Snapshot Spread APR          : ${fmtSigned(liveSpreadApr * 100, 3)}`);
    console.log(`Round-Trip VIP 0 Taker Fees       : -$${roundTripFeesUsd.toFixed(2)}`);
    console.log(`7D Realized Baseline Net PnL      : ${fmtSigned(realized7dNetUsd, 2, " USD")} (Gross ${fmtSigned(realized7dGrossUsd, 2, " USD")})`);
    console.log(`Live Snapshot 7D Extrapolation    : ${fmtSigned(live7dNetUsd, 2, " USD")} (Gross ${fmtSigned(live7dGrossUsd, 2, " USD")})`);
    console.log(`\nOK: Raw settled funding prints reconciled cleanly against PerpSpread API.`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
