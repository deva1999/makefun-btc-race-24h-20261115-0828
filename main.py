"""Breakout trend bot for make.fun btc-race-24h-20261115-0828 (agent-fun/bars-replay/v1).

Long-only, one position, $1,000 paper USDC, 1-minute cbBTC/USDC bars.

Idea: in a 24-hour window the round trip costs about 40 bps (4 bps fee +
2 bps slippage + ~15 bps price impact each way at full size on this pool),
so only a move well above that is worth chasing. Fast trend signals
(EMA crosses, short momentum) whipsaw on this market: 1-minute noise is
~12 bps and most bars are flat, so they pay the round trip many times for
nothing. This bot therefore trades rarely and only on a confirmed
one-hour breakout, then lets the move run until it breaks down.

Rules (all integer arithmetic on close prices, no clock, no network,
no randomness; the only state is the close history):
  - Enter (all cash) when the latest close breaks above the highest close
    of the previous 60 bars by more than 40 bps.
  - Exit (whole position) when any of these fires:
      * the close breaks below the lowest close of the previous 60 bars
        (the breakout failed / the trend reversed),
      * the price falls 50 bps below the entry close (hard stop),
      * the price falls 120 bps below the highest close since entry
        (trailing stop that locks in a runaway move).
  - Nothing else: no take-profit (a strong hour can run several percent),
    no re-entry cooldown (a fresh breakout after an exit is a fresh signal),
    no trading before 61 closes of history exist.

Why these numbers: on the published dev window the breakout filter fires
twice in 1,440 bars and both round trips are profitable, while EMA-cross
and dip-buying variants tested on the same window all lose money to
whipsaw costs. The 60-bar lookback and 40 bps confirmation were chosen
because the same trades result for 30- and 60-bar lookbacks and for
stops of 40-60 bps, i.e. the signal is not a knife-edge fit to one
parameter value. The dev window decides only whether this bot races;
the race window is unseen, so the design deliberately prefers missing
a marginal move over paying for a false one.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
LOOKBACK = 60            # bars defining the breakout range
CONFIRM_BPS = 40         # entry must clear the 60-bar high by this much
STOP_BPS = 50            # hard stop below the entry close
TRAIL_BPS = 120          # trailing stop below the high since entry
MAX_SLIPPAGE_BPS = 300   # ~4x the largest 1-minute move seen on the dev window (79 bps)

closes = []              # close prices (ints), one per bar that carried CBBTC
in_position = False
entry_close = None
high_since_entry = None


def on_batch(state, batch):
    global in_position, entry_close, high_since_entry
    # Only extend history when this batch actually carried a bar for us;
    # a minute with no sample must not duplicate the previous close.
    if not any(b.get("symbol") == SYMBOL for b in batch.get("bars", [])):
        return []
    close = state.close(SYMBOL)
    if close is None:
        return []
    closes.append(close)
    if state.warming_up:
        return []
    if len(closes) < LOOKBACK + 2:
        return []
    if not in_position:
        high = max(closes[-LOOKBACK - 1:-1])
        # close clears the 60-bar high by more than CONFIRM_BPS
        if close * 10000 > high * (10000 + CONFIRM_BPS):
            cash = state.cash
            if cash < int(state.hello["fees"]["min_notional_quote_units"]):
                return []
            in_position = True
            entry_close = close
            high_since_entry = close
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []
    # In position: track the high-water mark, then test the three exits.
    if close > high_since_entry:
        high_since_entry = close
    low = min(closes[-LOOKBACK - 1:-1])
    stop_hit = close * 10000 <= entry_close * (10000 - STOP_BPS)
    trail_hit = high_since_entry * 10000 >= close * (10000 + TRAIL_BPS)
    breakdown = close < low
    if stop_hit or trail_hit or breakdown:
        holding = state.positions.get(SYMBOL)
        if holding is None or holding.qty <= 0:
            in_position = False
            return []
        in_position = False
        entry_close = None
        high_since_entry = None
        return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
