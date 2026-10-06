"""
EXPLORATORY (post hoc). Is the original rate series an APY rather than an APR?

Why: in the paper's first kink period (regime 6) the original series sits about
0.33 percentage points above the on-chain borrow rate, almost exactly the
difference between a compounded annual yield (APY) and the simple annual rate
(APR = rate per block x 2,102,400) used by the authors' model and by our
on-chain panel. If the Compound API reported APY, then (a) part of the
"unreliable series" label in results/regime_annotation.csv is a unit difference,
not an error in the data, and (b) the authors' notebook (3_cdai_regimes.ipynb,
cell 4) subtracts an APR kink rate from an APY observed rate, which would push
observed rates artificially above the kink.

Three readings of the API's borrow_rates are compared with the on-chain APR,
each converted back to an APR on the chain's basis (2,102,400 blocks per year):
  raw    the API value is an APR (no conversion);
  apy_N  APY with per-block compounding over 2,102,400 blocks:
         APR = N * ((1 + API)^(1/N) - 1);
  apy_d  APY as in Compound's v2 documentation, daily compounding with 6,570
         blocks per day: rate per block = ((1 + API)^(1/365) - 1) / 6570.
The readings were fixed before the comparison was run.

For each of the authors' regimes: median absolute gap to the on-chain APR under
each reading, for borrow and supply rates. For regime 6 (21 Feb - 13 Mar 2020):
the authors' quantity (API rate - APR kink rate) and the same with the API rate
converted.

Run from the repository root:
    python scripts/exploratory_apy_check.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath('.'))
from simulator.engine.dai_rate_params import PARAM_REGIME_NUMS  # noqa: E402

PANELS = ['data/onchain/cdai_panel.csv', 'data/onchain/cdai_panel_dense_2020.csv']
API_PATH = 'data/compound/cdai.pkl'
OUT_PATH = 'results/exploratory/apy_check.json'
N = 2_102_400
BLOCKS_PER_DAY_DOCS = 6570


def to_apr(api, reading):
    api = np.asarray(api, dtype=float)
    if reading == 'raw':
        return api
    if reading == 'apy_N':
        return N * ((1 + api) ** (1 / N) - 1)
    if reading == 'apy_d':
        return ((1 + api) ** (1 / 365) - 1) / BLOCKS_PER_DAY_DOCS * N
    raise ValueError(reading)


def load():
    df = pd.concat([pd.read_csv(p, dtype=str) for p in PANELS]).fillna('').drop_duplicates('block')
    df['utc'] = pd.to_datetime(df['utc'])
    num = lambda c: pd.to_numeric(df[c].replace('', np.nan))
    df['chain_borrow_apr'] = num('cdai_borrowRatePerBlock') * N / 1e18
    df['chain_supply_apr'] = num('cdai_supplyRatePerBlock') * N / 1e18
    kink = num('irm_kink') / 1e18
    df['kink_rate_apr'] = (num('irm_baseRatePerBlock') + kink * num('irm_multiplierPerBlock')) * N / 1e18
    api = pd.read_pickle(API_PATH)[['borrow_rates', 'supply_rates']].resample('h').mean()
    df['hour'] = df['utc'].dt.floor('h')
    df = df.join(api, on='hour').dropna(subset=['borrow_rates', 'chain_borrow_apr'])
    return df.sort_values('utc')


def main():
    df = load()
    starts = sorted((int(k), pd.Timestamp(v)) for k, v in PARAM_REGIME_NUMS.items())
    readings = ['raw', 'apy_N', 'apy_d']
    rows = []
    print('Median |gap| to on-chain APR, percentage points (borrow / supply)\n')
    print(f"{'regime':>6} {'n':>5}  " + '  '.join(f'{r:>15}' for r in readings))
    for i, (num, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else df['utc'].max() + pd.Timedelta(seconds=1)
        s = df[(df['utc'] >= start) & (df['utc'] < end)]
        row = {'regime': num, 'n': int(len(s))}
        cells = []
        for r in readings:
            gb = float(np.median(np.abs(to_apr(s['borrow_rates'], r) - s['chain_borrow_apr']))) * 100
            gs = float(np.median(np.abs(to_apr(s['supply_rates'], r) - s['chain_supply_apr']))) * 100
            row[f'borrow_gap_pp_{r}'], row[f'supply_gap_pp_{r}'] = gb, gs
            cells.append(f'{gb:6.3f} / {gs:6.3f}')
        rows.append(row)
        print(f'{num:>6} {len(s):>5}  ' + '  '.join(f'{c:>15}' for c in cells))

    r6s, r6e = pd.Timestamp('2020-02-21'), pd.Timestamp('2020-03-14')
    s = df[(df['utc'] >= r6s) & (df['utc'] < r6e)]
    best = {}
    print("\nPaper's first period (21 Feb - 13 Mar 2020): rate minus APR kink rate, pp")
    for r in readings:
        d = (to_apr(s['borrow_rates'], r) - s['kink_rate_apr']) * 100
        best[r] = {'median': float(np.median(d)), 'share_within_0.25pp': float(np.mean(np.abs(d) <= 0.25)),
                   'share_above_0.25pp': float(np.mean(d > 0.25))}
        print(f"  {r:6s} median {best[r]['median']:+.3f}  within 0.25 pp {best[r]['share_within_0.25pp']:.2f}  "
              f"above {best[r]['share_above_0.25pp']:.2f}")
    chain = (s['chain_borrow_apr'] - s['kink_rate_apr']) * 100
    print(f"  chain  median {np.median(chain):+.3f}  within 0.25 pp {np.mean(np.abs(chain) <= 0.25):.2f}  "
          f"above {np.mean(chain > 0.25):.2f}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump({'status': 'exploratory, post hoc', 'readings': readings, 'regimes': rows,
                   'paper_period_1_rate_minus_kink': best,
                   'paper_period_1_chain_minus_kink_median_pp': float(np.median(chain))}, f, indent=2)
    print(f'\nSaved {OUT_PATH}')


if __name__ == '__main__':
    main()
