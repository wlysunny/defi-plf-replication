"""
EXPLORATORY (post hoc) check of the Aave V3 kink test. Not part of the
pre-specified analysis in analysis_plans/aave_kink_criterion.md; written after
its results were seen. It does not change the pre-specified decision.

Question: in four reserve-periods the subgraph failed validation and the
decision was made on weekly chain utilisation computed from token balances,
which only approximates the protocol's internal definition from Aave V3.1.
Which utilisation measure is right, and do the decisions depend on it?

A third, independent measure: the protocol's own utilisation implied by the
variable borrow rate stored in the Pool at the sampled block, inverted through
the interest-rate model in force:
    below the kink:  u = kink * (r - base) / slope1
    above the kink:  u = kink + (1 - kink) * (r - base - slope1) / slope2
(stable-rate terms are ignored; stable borrowing was negligible and later removed).

For each reserve-period it reports:
  - median |difference| between subgraph and chain borrow rates (bp), and the share exactly equal;
  - median |difference| in utilisation: subgraph vs implied (daily), balance-based vs implied (weekly);
  - the pre-specified rule applied to each utilisation measure (reported, no decision).

Run from the repository root:
    python scripts/exploratory_aave_validation.py
"""

import json
import os

import numpy as np
import pandas as pd

import aave_kink_analysis as a
import kink_clustering_analysis as k

OUT_PATH = 'results/exploratory/aave_validation.json'


def implied_utilisation(df):
    rate = df['rate_chain_pct']
    base = df['kink_rate_pct'] - df['slope1_pp']
    kink = df['kink_pct'] / 100
    below = kink * (rate - base) / df['slope1_pp']
    above = kink + (1 - kink) * (rate - df['kink_rate_pct']) / df['slope2_pp']
    return np.where(rate <= df['kink_rate_pct'], below, above) * 100


def decide(s, col, rng, block):
    p = s.copy()
    p['distance_pp'] = p[col] - p['kink_pct']
    p['excluded'] = p['excluded'].where(p['excluded'].notna() | p[col].notna(), 'missing')
    p = p[p[col].notna() | p['excluded'].notna()]
    r = k.assess(p[['utc', 'distance_pp', 'excluded']].reset_index(drop=True), '', '1900', '2100', rng, block)
    return {'decision': r['decision'], 'n': r['n_samples'],
            'kink_bin_share': r.get('kink_bin_share'), 'modal_bin_range_pp': r.get('modal_bin_range_pp')}


def main():
    rng = np.random.default_rng(k.BOOT_SEED)
    df = a.load()
    df['util_implied_pct'] = implied_utilisation(df)
    rows = []
    for symbol in a.SYMBOLS:
        for label, start, end in a.PERIODS:
            s = df[(df['symbol'] == symbol) & (df['utc'] >= start) & (df['utc'] < end)]
            ok = s[s['excluded'].isna()]
            rate_gap_bp = (ok['rate_subgraph_pct'] - ok['rate_chain_pct']).abs() * 100
            sg_vs_imp = (ok['util_subgraph_pct'] - ok['util_implied_pct']).abs()
            wk = ok.dropna(subset=['util_chain_pct'])
            bal_vs_imp = (wk['util_chain_pct'] - wk['util_implied_pct']).abs()
            row = {
                'period': f'{symbol} {label}',
                'median_abs_rate_gap_bp': float(rate_gap_bp.median()),
                'p90_abs_rate_gap_bp': float(rate_gap_bp.quantile(0.9)),
                'share_rate_exactly_equal': float(ok['rate_equal'].astype(float).mean()),
                'median_abs_util_subgraph_vs_implied_pp': float(sg_vs_imp.median()),
                'median_abs_util_balance_vs_implied_pp': float(bal_vs_imp.median()),
                'median_kink_pct': float(ok['kink_pct'].median()),
                'median_util_implied_pct': float(ok['util_implied_pct'].median()),
                'rule_on_subgraph_daily': decide(s, 'util_subgraph_pct', rng, k.BOOT_BLOCK),
                'rule_on_implied_daily': decide(s, 'util_implied_pct', rng, k.BOOT_BLOCK),
            }
            rows.append(row)
            print(f"{row['period']:26s} rate gap {row['median_abs_rate_gap_bp']:6.2f} bp (p90 {row['p90_abs_rate_gap_bp']:6.2f})  "
                  f"util |sg-imp| {row['median_abs_util_subgraph_vs_implied_pp']:5.2f}  "
                  f"|bal-imp| {row['median_abs_util_balance_vs_implied_pp']:5.2f} pp  "
                  f"kink {row['median_kink_pct']:.0f}% util(imp) {row['median_util_implied_pct']:.1f}%  "
                  f"rule: subgraph {row['rule_on_subgraph_daily']['decision']}, implied {row['rule_on_implied_daily']['decision']}")
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump({'status': 'exploratory, post hoc', 'periods': rows}, f, indent=2, default=str)
    print(f'\nSaved {OUT_PATH}')


if __name__ == '__main__':
    main()
