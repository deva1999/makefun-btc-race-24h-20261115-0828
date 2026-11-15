# Breakout BTC Bot — make.fun btc-race-24h-20261115-0828

[![make.fun · btc-race-24h-20261115-0828](https://make.fun/badge/btc-race-24h-20261115-0828.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![rank](https://make.fun/badge/btc-race-24h-20261115-0828/deva1999/makefun-btc-race-24h-20261115-0828/rank.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)
[![reward](https://make.fun/badge/btc-race-24h-20261115-0828/deva1999/makefun-btc-race-24h-20261115-0828/reward.svg)](https://make.fun/bounty/btc-race-24h-20261115-0828?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261115-0828)

Entry for [btc-race-24h-20261115-0828](https://make.fun/bounty/btc-race-24h-20261115-0828): race a
cbBTC trading bot live for 24 hours on 1-minute on-chain bars, starting with $1,000 of paper USDC.
Long-only, no leverage, no real money.

## Strategy: one-hour breakout, then let it run

A full-size round trip costs about 40 bps here (4 bps fee + 2 bps slippage + ~15 bps price
impact each way on this pool), and 1-minute noise is ~12 bps with most bars flat — so fast
signals (EMA crosses, short momentum, dip-buying) whipsaw and pay the round trip many times
for nothing. On the published dev window every such variant loses money. This bot trades
rarely, only on a confirmed breakout:

- **Enter** (all cash) when the close breaks above the highest close of the previous 60 bars
  by more than 40 bps.
- **Exit** (whole position) when the close breaks below the lowest close of the previous
  60 bars, or falls 45 bps below the entry close (hard stop), or trails 100 bps below the
  highest close since entry. No take-profit: a strong hour can run several percent.
- **Nothing else.** No trading before 61 closes of history. Pure integer arithmetic on
  close prices; deterministic, no clock, no network, no randomness.

## Local dev-window grade

Run from the kit directory (the kit is not part of this repo):

```
node cli/makefun.mjs grade-local --kit <kit-dir> --bot . --driver process
```

Dev window (1,440 bars, frozen): the breakout filter fires twice, both round trips
profitable — net PnL **+$8.22** on $1,000, max drawdown 1.21%, 4 trades, $1.60 fees
(measured with the harness's exact fill arithmetic in a local replay, since the
kit's `grade-local` needs Docker, which this machine does not have; the server's
dev grade is the authoritative check). The whole dev profit comes from the
second round trip; the first half of the window contributes $0 (no trades).
See `main.py` for the full reasoning and the parameter-sensitivity note.

## Layout

- `main.py` — the bot (Python 3.13 standard library only, `agent-fun/bars-replay/v1`).
- `vendor/makefun_bars.py` — byte-identical copy of the kit's Python shim.
- `LICENSE` — MIT.

## Run

The grader runs `python3 -P -s /bot/main.py`; the bot speaks NDJSON on stdin/stdout via
the vendored shim. Nothing to install.
