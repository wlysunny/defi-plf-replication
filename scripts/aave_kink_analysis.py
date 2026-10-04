"""
Pre-specified test of kink clustering on Aave V3 (Ethereum, Core market), the
project's existing dataset. Criterion: analysis_plans/aave_kink_criterion.md.

Inputs:
  data/aave_v3/aave_v3_daily_panel.csv        (Aave V3 subgraph; collect_aave_v3_subgraph.py)
  data/aave_v3/aave_v3_rate_params_daily.csv  (chain state; collect_aave_v3_rate_params.py)

Steps:
  1. Validation of the subgraph against the chain, per reserve and period:
     utilisation on the weekly validation days, and the variable borrow rate on all days.
  2. The clustering rule of the cDAI test (kink_clustering_analysis.py), unchanged,
     applied to each reserve in each of three periods.
  3. Secondary, reported only: share of days with the borrow rate within 0.25 pp
     of the rate at the kink, and the model's slope below and above the kink.

Run from the repository root:
    python scripts/aave_kink_analysis.py
"""

import json
import os

import numpy as np
import pandas as pd

import kink_clustering_analysis as k

SUBGRAPH_PATH = 'data/aave_v3/aave_v3_daily_panel.csv'
PARAMS_PATH = 'data/aave_v3/aave_v3_rate_params_daily.csv'
RESULTS_PATH = 'results/aave_kink_results.json'

RAY = 10 ** 27
SYMBOLS = ['USDC', 'USDT', 'DAI', 'WETH']
PERIODS = [
    ('2023-02 to 2023-12', '2023-02-01', '2024-01-01'),
    ('2024', '2024-01-01', '2025-01-01'),
    ('2025-01 to 2025-11', '2025-01-01', '2025-12-01'),
]
VALIDATION_MAX_MEDIAN_GAP_PP = 0.5
NEAR_RATE_PP = 0.25
WEEKLY_BOOT_BLOCK = 2            # weekly fallback data: blocks of two samples, i.e. about two weeks


def to_int(value):
    return k.big(value)


def load(subgraph_path=SUBGRAPH_PATH, params_path=PARAMS_PATH):
    sg = pd.read_csv(subgraph_path, dtype=str)
    pr = pd.read_csv(params_path, dtype=str)
    sg['asset'] = sg['reserve_id'].str[:42].str.lower()
    pr['asset'] = pr['asset'].str.lower()
    df = sg.merge(pr, on=['asset', 'sample_utc'], how='outer', suffixes=('', '_chain'), indicator='source_match')
    df['symbol'] = df['symbol'].fillna(df['symbol_chain'])
    rows = []
    for r in df.itertuples(index=False):
        kink_raw = to_int(r.irm_optimalUsageRatio)
        kink = kink_raw / RAY if kink_raw is not None else np.nan
        if not np.isnan(kink) and not 0.3 < kink <= 1.0:
            raise ValueError(f'Unexpected optimalUsageRatio units: {kink_raw} ({r.symbol}, {r.sample_utc})')
        util_sg = float(r.item_utilizationRate) * 100 if isinstance(r.item_utilizationRate, str) else np.nan
        reason = None
        if r.source_match != 'both':
            reason = 'missing in one source'
        elif np.isnan(kink):
            reason = 'no kink parameter'
        elif np.isnan(util_sg):
            reason = 'missing utilisation'
        # chain utilisation, validation days only
        v_debt, s_debt, bal = (to_int(r.val_variableDebt_totalSupply), to_int(r.val_stableDebt_totalSupply),
                               to_int(r.val_underlying_balanceOf_aToken))
        if s_debt is None and v_debt is not None:
            s_debt = 0     # stable borrowing was removed in Aave V3.2; the stable-debt address may hold no contract
        util_chain = np.nan
        if None not in (v_debt, s_debt, bal) and v_debt + s_debt + bal > 0:
            util_chain = (v_debt + s_debt) / (bal + v_debt + s_debt) * 100
        rate_sg, rate_chain = to_int(r.item_variableBorrowRate), to_int(r.pool_currentVariableBorrowRate)
        base, s1, s2 = (to_int(r.irm_baseVariableBorrowRate), to_int(r.irm_variableRateSlope1),
                        to_int(r.irm_variableRateSlope2))
        kink_rate = (base + s1) / RAY * 100 if None not in (base, s1) else np.nan
        rows.append({
            'symbol': r.symbol, 'utc': pd.Timestamp(r.sample_utc).tz_localize(None),
            'kink_pct': kink * 100, 'util_subgraph_pct': util_sg, 'util_chain_pct': util_chain,
            'rate_subgraph_pct': rate_sg / RAY * 100 if rate_sg is not None else np.nan,
            'rate_chain_pct': rate_chain / RAY * 100 if rate_chain is not None else np.nan,
            'rate_equal': (rate_sg == rate_chain) if None not in (rate_sg, rate_chain) else np.nan,
            'kink_rate_pct': kink_rate,
            'slope1_pp': s1 / RAY * 100 if s1 is not None else np.nan,
            'slope2_pp': s2 / RAY * 100 if s2 is not None else np.nan,
            'staleness_days': float(r.staleness_seconds) / 86400 if isinstance(r.staleness_seconds, str) else np.nan,
            'excluded': reason,
        })
    return pd.DataFrame(rows).sort_values(['symbol', 'utc']).reset_index(drop=True)


def panel_for(df, source):
    """Rows in the format expected by kink_clustering_analysis.assess."""
    col = 'util_subgraph_pct' if source == 'subgraph' else 'util_chain_pct'
    p = df.copy()
    if source == 'chain':
        p = p[p['util_chain_pct'].notna()]          # weekly validation days only
    p['distance_pp'] = p[col] - p['kink_pct']
    p['excluded'] = p['excluded'].where(p['excluded'].notna() | p[col].notna(), 'missing utilisation')
    return p[['utc', 'distance_pp', 'excluded']].reset_index(drop=True)


def validate(s):
    both = s.dropna(subset=['util_subgraph_pct', 'util_chain_pct'])
    gap = (both['util_subgraph_pct'] - both['util_chain_pct']).abs()
    eq = s['rate_equal'].dropna()
    return {'n_validation_days': int(len(both)),
            'median_abs_util_gap_pp': float(gap.median()) if len(gap) else None,
            'max_abs_util_gap_pp': float(gap.max()) if len(gap) else None,
            'share_rate_exactly_equal': float(eq.astype(bool).mean()) if len(eq) else None,
            'passes': bool(len(gap) and gap.median() <= VALIDATION_MAX_MEDIAN_GAP_PP)}


def secondary(s):
    ok = s[s['excluded'].isna()]
    near = (ok['rate_subgraph_pct'] - ok['kink_rate_pct']).abs() <= NEAR_RATE_PP
    return {'share_rate_within_0.25pp_of_kink_rate': float(near.mean()) if len(ok) else None,
            'median_slope_below_kink_pp_per_100pp': float(ok['slope1_pp'].median()) if len(ok) else None,
            'median_slope_above_kink_pp_per_100pp': float(ok['slope2_pp'].median()) if len(ok) else None,
            'median_staleness_days': float(ok['staleness_days'].median()) if len(ok) else None,
            'max_staleness_days': float(ok['staleness_days'].max()) if len(ok) else None}


def overall(results):
    """
    Holds: at least 8 of 12 reserve-periods hold AND at least 3 of the 4 reserves hold in
    at least 2 of their 3 periods (so that the verdict is not carried by one group of assets).
    Does not hold: 4 or fewer reserve-periods hold. Mixed evidence: anything else.
    """
    holding = [r['decision'] in (k.HOLDS, k.HOLDS_WEAK) for r in results]
    holds = sum(holding)
    per_reserve = {s: sum(h for h, r in zip(holding, results) if r['symbol'] == s) for s in SYMBOLS}
    reserves_ok = sum(n >= 2 for n in per_reserve.values())
    if holds >= 8 and reserves_ok >= 3:
        verdict = 'clustering at the kink holds on Aave V3'
    elif holds <= 4:
        verdict = 'clustering at the kink does not hold on Aave V3'
    else:
        verdict = 'mixed evidence'
    return {'periods_holding': holds, 'periods_total': len(results),
            'periods_holding_per_reserve': per_reserve,
            'reserves_holding_in_at_least_2_of_3': reserves_ok, 'verdict': verdict}


def run(subgraph_path=SUBGRAPH_PATH, params_path=PARAMS_PATH, results_path=RESULTS_PATH, verbose=True):
    say = print if verbose else (lambda *a, **kw: None)
    rng = np.random.default_rng(k.BOOT_SEED)
    df = load(subgraph_path, params_path)
    say(f"{len(df)} rows; excluded: {df['excluded'].value_counts().to_dict() or 'none'}")
    results = []
    for symbol in SYMBOLS:
        s_all = df[df['symbol'] == symbol]
        for label, start, end in PERIODS:
            s = s_all[(s_all['utc'] >= start) & (s_all['utc'] < end)]
            val = validate(s)
            source = 'subgraph' if val['passes'] else 'chain (weekly)'
            block = k.BOOT_BLOCK if val['passes'] else WEEKLY_BOOT_BLOCK
            r = k.assess(panel_for(s, 'subgraph' if val['passes'] else 'chain'), f'{symbol} {label}',
                         start, end, rng, block)
            r.update({'symbol': symbol, 'utilisation_source': source, 'validation': val,
                      'secondary': secondary(s)})
            results.append(r)
            if r['decision'] == k.INSUFFICIENT:
                say(f"  {r['period']:26s} n={r['n_samples']:4d}  [{source}]  {r['decision']}")
                continue
            lo, hi = r['modal_bin_range_pp']
            say(f"  {r['period']:26s} n={r['n_samples']:4d}  [{source}]  kink-bin share {r['kink_bin_share']:.2f}  "
                f"modal bin [{lo:+.1f}, {hi:+.1f}) pp  bootstrap {r['bootstrap_mode_proportion']:.2f}  "
                f"->  {r['decision']}")
    summary = overall(results)
    say(f"\nAave V3: {summary['periods_holding']}/{summary['periods_total']} reserve-periods; "
        f"{summary['reserves_holding_in_at_least_2_of_3']}/4 reserves hold in at least 2 of 3 periods "
        f"{summary['periods_holding_per_reserve']} -> {summary['verdict']}")
    out = {'criterion': 'analysis_plans/aave_kink_criterion.md', 'subgraph_panel': subgraph_path,
           'chain_params': params_path, 'bin_width_pp': k.BIN_WIDTH, 'results': results, 'summary': summary,
           'bootstrap': {'block_samples_daily': k.BOOT_BLOCK, 'block_samples_weekly': WEEKLY_BOOT_BLOCK,
                         'reps': k.BOOT_REPS, 'seed': k.BOOT_SEED}}
    if results_path:
        os.makedirs(os.path.dirname(results_path), exist_ok=True)
        with open(results_path, 'w') as f:
            json.dump(out, f, indent=2, default=str)
        say(f'Saved {results_path}')
    return out


if __name__ == '__main__':
    run()
