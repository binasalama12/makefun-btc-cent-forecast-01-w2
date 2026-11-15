# btc-cent-forecast-01 — wallet w2: multi-horizon momentum forecaster

Forecasts Bitcoin's price 240 minutes after each checkpoint from the 4,320
one-minute closes (72 h) in the case.

## Approach

For the trailing windows of 15, 60, 240, and 720 minutes, compute the average
per-minute price change over that window (`(last − price w minutes ago) / w`).
Combine the four rates with weights 0.4 / 0.3 / 0.2 / 0.1 (short windows weigh
more: recent momentum matters most, long windows smooth out noise), then
extrapolate 240 minutes ahead:

```
forecast = last_close + 240 × weighted_avg_per_minute_change
```

The implied 4-hour move is clamped to ±2% of `last_close`, so a short burst
cannot throw the forecast far off, and the result is rounded to the price
grid's 5 decimals inside (0, 10,000,000).

Fallback: with fewer than 100 prices the windows are meaningless, so the
forecast is the last close (persistence).

## Properties

- Python 3.13, standard library only, no network, no randomness:
  two runs produce byte-identical output.
- Reads every `*.in` in `$MAKEFUN_INPUT_DIR` (else `/input`), writes one
  `<id>.out` per case to `$MAKEFUN_OUTPUT_DIR` (else `/output`).
- Fast: a few milliseconds per case, far under the 8-second cap.

## Run locally

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```
