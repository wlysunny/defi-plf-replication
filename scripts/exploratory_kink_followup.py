"""
EXPLORATORY (post hoc) follow-up to the kink-clustering test. Not part of the
pre-specified analysis in analysis_plans/kink_clustering_criterion.md; written
after its results were seen.

The pre-specified test found that on-chain utilisation does not cluster at the
kink in any of the paper's three periods, whereas the paper reports that
"realized interest rates" cluster at the kink. This script examines why, in
three parts:

  1. Utilisation in the original data (Compound API, data/compound/cdai.pkl)
     compared with on-chain utilisation, hour by hour.
  2. The share of hours in which the borrow rate lies within 0.25 percentage
     points of the kink rate, for on-chain rates and for the original data.
  3. The slope of the interest-rate model below and above the kink, from the
     model parameters read on-chain in each period.

Run from the repository root:
    python scripts/exploratory_kink_followup.py
"""

import json
import os

import numpy as np
import pandas as pd

import kink_clustering_analysis as k

BLOCKS_PER_YEAR = 2102400
NEAR_PP = 0.25
OUT_PATH = 'results/exploratory/kink_followup.json'


def load_dense():
    raw = pd.read_csv(k.DENSE_PANEL_PATH, dtype=str)
    hour = pd.DatetimeIndex(pd.to_datetime(raw['utc']).dt.floor('h'))
    # .to_numpy() so that values are placed by position; passing Series with a different
    # index to the constructor would realign them to the new index and silently produce NaN.
    num = lambda col: raw[col].replace('', np.nan).astype(float).to_numpy()
    df = pd.DataFrame({
        'onchain_util_pct': num('cdai_totalBorrows') / (num('cdai_getCash') + num('cdai_totalBorrows')
                                                         - num('cdai_totalReserves')) * 100,
        'onchain_rate_pct': num('cdai_borrowRatePerBlock') * BLOCKS_PER_YEAR / 1e18 * 100,
        'kink': num('irm_kink') / 1e18,
        'base': num('irm_baseRatePerBlock'),
        'mult': num('irm_multiplierPerBlock'),
        'jump_mult': num('irm_jumpMultiplierPerBlock'),
    }, index=hour)
    df = df[~df.index.duplicated()]
    # Rate at exactly the kink, from the parameters active at each hour (per-block rates, annualised, in %).
    df['kink_rate_pct'] = (df['base'] + df['kink'] * df['mult']) * BLOCKS_PER_YEAR / 1e18 * 100
    df['slope_below_pp_per_100pp'] = df['mult'] * BLOCKS_PER_YEAR / 1e18 * 100
    df['slope_above_pp_per_100pp'] = df['jump_mult'] * BLOCKS_PER_YEAR / 1e18 * 100
    return df


def load_api():
    api = pd.read_pickle('data/compound/cdai.pkl')[['utilization_ratio', 'borrow_rates']]
    api = api.resample('h').mean() * 100
    return api.rename(columns={'utilization_ratio': 'api_util_pct', 'borrow_rates': 'api_rate_pct'})


def main():
    both = pd.concat([load_dense(), load_api()], axis=1, sort=True).dropna(
        subset=['onchain_util_pct', 'api_util_pct', 'onchain_rate_pct', 'api_rate_pct', 'kink_rate_pct'])
    rows = []
    print('Paper periods (kink utilisation 90%):\n')
    for label, start, end in k.PAPER_PERIODS:
        s = both[(both.index >= start) & (both.index < end)]
        near = lambda col: float(np.mean(np.abs(s[col] - s['kink_rate_pct']) <= NEAR_PP))
        row = {
            'period': label, 'hours': int(len(s)),
            'median_util_onchain_pct': float(s['onchain_util_pct'].median()),
            'median_util_api_pct': float(s['api_util_pct'].median()),
            'median_abs_util_gap_pp': float((s['api_util_pct'] - s['onchain_util_pct']).abs().median()),
            'median_kink_rate_pct': float(s['kink_rate_pct'].median()),
            'share_rate_near_kink_onchain': near('onchain_rate_pct'),
            'share_rate_near_kink_api': near('api_rate_pct'),
            'slope_below_kink_pp_per_100pp': float(s['slope_below_pp_per_100pp'].median()),
            'slope_above_kink_pp_per_100pp': float(s['slope_above_pp_per_100pp'].median()),
        }
        rows.append(row)
        print(f"{label}  ({row['hours']} hours)")
        print(f"  1. median utilisation: on-chain {row['median_util_onchain_pct']:.1f}%, original data "
              f"{row['median_util_api_pct']:.1f}%; median hourly gap {row['median_abs_util_gap_pp']:.2f} pp")
        print(f"  2. kink rate {row['median_kink_rate_pct']:.2f}%; share of hours within {NEAR_PP} pp of it: "
              f"on-chain {row['share_rate_near_kink_onchain']:.2f}, original data {row['share_rate_near_kink_api']:.2f}")
        print(f"  3. model slope per 100 pp of utilisation: below kink {row['slope_below_kink_pp_per_100pp']:.3f} pp, "
              f"above kink {row['slope_above_kink_pp_per_100pp']:.1f} pp\n")
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump({'status': 'exploratory, post hoc', 'near_kink_threshold_pp': NEAR_PP,
                   'blocks_per_year': BLOCKS_PER_YEAR, 'periods': rows}, f, indent=2)
    print(f'Saved {OUT_PATH}')


if __name__ == '__main__':
    main()
