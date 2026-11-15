# btc-cent-forecast-01, wallet w2: multi-horizon momentum forecaster.
#
# For each case, read the 1-minute BTC closes (72 h up to the checkpoint) and
# forecast the price 240 minutes after the checkpoint as:
#
#   forecast = last_close + 240 * weighted_avg_per_minute_change
#
# where the per-minute change is averaged over four trailing windows
# (15, 60, 240, 720 minutes) and combined with weights 0.4 / 0.3 / 0.2 / 0.1.
# The implied 4-hour move is clamped to +/-2% of last_close, and the result is
# kept on the price grid's 5 decimals inside (0, 10,000,000).
#
# Fallback: with fewer than 100 prices the windows are meaningless, so the
# forecast is simply the last close (persistence).
#
# Python 3.13, standard library only, no network, deterministic.

import json
import math
import os
from pathlib import Path

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

MIN_PRICE = 0.00001
MAX_PRICE = 9_999_999.99999

# (window in minutes, weight) — weights sum to 1.
WINDOWS = ((15, 0.4), (60, 0.3), (240, 0.2), (720, 0.1))
HORIZON_MINUTES = 240
MAX_SHIFT_FRACTION = 0.02  # clamp the implied move to +/-2% of last close


def price5(x: float) -> float:
    """Clamp x inside the scorer's (0, 10,000,000) and round to 5 decimals."""
    return round(min(MAX_PRICE, max(MIN_PRICE, x)) * 1e5) / 1e5


def forecast(prices: list) -> float:
    """Multi-horizon momentum forecast from a list of 1-minute closes."""
    # Drop any non-finite entries; a window endpoint that is not a number
    # would otherwise poison the whole average.
    clean = [float(p) for p in prices if isinstance(p, (int, float)) and math.isfinite(p)]
    if not clean:
        raise ValueError("no finite prices")
    last = clean[-1]
    if last <= 0:
        raise ValueError("last price is not positive")
    if len(clean) < 100:
        return price5(last)

    n = len(clean)
    weighted = 0.0
    for window, weight in WINDOWS:
        w = min(window, n - 1)
        # Average per-minute change over the last w minutes.
        change = (clean[-1] - clean[-1 - w]) / w
        weighted += weight * change

    shift = HORIZON_MINUTES * weighted
    max_shift = MAX_SHIFT_FRACTION * last
    if shift > max_shift:
        shift = max_shift
    elif shift < -max_shift:
        shift = -max_shift
    return price5(last + shift)


def main() -> None:
    input_dir = Path(INPUT_DIR)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    inputs = sorted(p for p in input_dir.iterdir() if p.name.endswith(".in"))
    for path in inputs:
        case_id = path.name[: -len(".in")]
        case = json.loads(path.read_text(encoding="utf-8"))
        markets = case.get("markets")
        if not isinstance(markets, list) or len(markets) != 1:
            raise ValueError(f"{path.name} does not hold exactly one market")
        prices = markets[0].get("prices")
        if not isinstance(prices, list) or not prices:
            raise ValueError(f"{path.name} has no prices")
        out = {"forecasts": [{"case": case_id, "price": forecast(prices)}]}
        (output_dir / f"{case_id}.out").write_text(json.dumps(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
