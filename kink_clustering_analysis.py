"""
Test whether cDAI utilisation clusters at the kink of the interest-rate model,
implementing analysis_plans/kink_clustering_criterion.md.

Run from the repository root, after the on-chain panel has been collected:
    python kink_clustering_analysis.py
"""

import json
import os

import numpy as np
import pandas as pd

PANEL_PATH = 'data/onchain/cdai_panel.csv'                    # about daily; new-data periods
DENSE_PANEL_PATH = 'data/onchain/cdai_panel_dense_2020.csv'    # about hourly; paper's periods
RESULTS_DIR = 'results'

BIN_WIDTH = 5.0                 # percentage points; the decision uses this width
SENSITIVITY_WIDTHS = (2.0, 10.0)
BOOT_BLOCK = 14                 # daily panel: blocks of about two weeks
DENSE_BOOT_BLOCK = 24           # hourly panel: blocks of about one day
BOOT_REPS = 2000
BOOT_SEED = 20261002
ROBUST_PROPORTION = 0.8
MIN_SAMPLES = 30

PAPER_PERIODS = [
    ('paper: 2020-02-21 to 2020-03-13', '2020-02-21', '2020-03-14'),
    ('paper: 2020-03-14 to 2020-04-05', '2020-03-14', '2020-04-06'),
    ('paper: 2020-04-06 to 2020-04-21', '2020-04-06', '2020-04-22'),
]
NEW_PERIODS = [
    ('new: 2020-05 to 2020-12', '2020-05-01', '2021-01-01'),
    ('new: 2021', '2021-01-01', '2022-01-01'),
    ('new: 2022', '2022-01-01', '2023-01-01'),
    ('new: 2023', '2023-01-01', '2024-01-01'),
    ('new: 2024', '2024-01-01', '2025-01-01'),
    ('new: 2025-01 to 2025-11', '2025-01-01', '2025-12-01'),
]

HOLDS = 'Holds'
HOLDS_WEAK = 'Holds, but not robustly'
NOT_HOLD = 'Does not hold'
INSUFFICIENT = 'Insufficient data'


# ---------------------------------------------------------------- data

def big(value):
    """Exact integer from a decimal string; None if blank."""
    if value is None or (isinstance(value, float) and np.isnan(value)) or str(value).strip() == '':
        return None
    return int(str(value))


def load_panel(path):
    raw = pd.read_csv(path, dtype=str)
    rows = []
    for r in raw.itertuples(index=False):
        cash, borrows, reserves, kink = (big(r.cdai_getCash), big(r.cdai_totalBorrows),
                                         big(r.cdai_totalReserves), big(r.irm_kink))
        reason = None
        if None in (cash, borrows, reserves):
            reason = 'missing value'
        elif kink is None:
            reason = 'no kink getter'
        elif borrows == 0:
            reason = 'zero borrows'
        util = d = np.nan
        if reason is None:
            util = borrows / (cash + borrows - reserves) * 100
            d = util - kink / 1e18 * 100
        rows.append({'utc': pd.Timestamp(r.utc), 'block': int(r.block), 'utilisation_pct': util,
                     'distance_pp': d, 'excluded': reason})
    return pd.DataFrame(rows).sort_values('block').reset_index(drop=True)


# ---------------------------------------------------------------- statistics

def bin_index(d, width):
    """Bin number with bin 0 = [-width/2, width/2), the kink bin."""
    return np.floor((np.asarray(d) + width / 2) / width).astype(int)


def kink_is_mode(d, width):
    bins, counts = np.unique(bin_index(d, width), return_counts=True)
    shares = dict(zip(bins, counts / counts.sum()))
    kink_share = shares.get(0, 0.0)
    others = [s for b, s in shares.items() if b != 0]
    return (kink_share > max(others)) if others else kink_share > 0, shares


def bootstrap_mode_proportion(d, width, rng, block):
    d = np.asarray(d)
    n = len(d)
    if n < block:
        return float('nan')
    n_blocks = int(np.ceil(n / block))
    hits = 0
    for _ in range(BOOT_REPS):
        starts = rng.integers(0, n - block + 1, size=n_blocks)
        sample = np.concatenate([d[s:s + block] for s in starts])[:n]
        hits += kink_is_mode(sample, width)[0]
    return hits / BOOT_REPS


def assess(panel, label, start, end, rng, block):
    in_period = (panel['utc'] >= start) & (panel['utc'] < end)
    period = panel[in_period]
    excluded = period['excluded'].value_counts().to_dict()
    d = period.loc[period['excluded'].isna(), 'distance_pp'].to_numpy()
    out = {'period': label, 'start': start, 'end_exclusive': end, 'n_samples': int(len(d)),
           'excluded': excluded}
    if len(d) < MIN_SAMPLES:
        out['decision'] = INSUFFICIENT
        return out
    is_mode, shares = kink_is_mode(d, BIN_WIDTH)
    proportion = bootstrap_mode_proportion(d, BIN_WIDTH, rng, block)
    if is_mode:
        out['decision'] = HOLDS if proportion >= ROBUST_PROPORTION else HOLDS_WEAK
    else:
        out['decision'] = NOT_HOLD
    modal_bin = max(shares, key=shares.get)
    out.update({
        'kink_bin_share': float(shares.get(0, 0.0)),
        'modal_bin_range_pp': [modal_bin * BIN_WIDTH - BIN_WIDTH / 2, modal_bin * BIN_WIDTH + BIN_WIDTH / 2],
        'modal_bin_share': float(shares[modal_bin]),
        'share_above_kink_bin': float(np.mean(d >= BIN_WIDTH / 2)),
        'bootstrap_mode_proportion': proportion,
        'sensitivity_kink_is_mode': {f'{w:g}pp': bool(kink_is_mode(d, w)[0]) for w in SENSITIVITY_WIDTHS},
        'median_distance_pp': float(np.median(d)),
    })
    return out


def overall(paper, new):
    paper_holds = sum(r['decision'] in (HOLDS, HOLDS_WEAK) for r in paper)
    new_holds = sum(r['decision'] in (HOLDS, HOLDS_WEAK) for r in new)
    consistency = 'reproduces the paper' if paper_holds >= 2 else 'does not reproduce the paper'
    if new_holds >= 4:
        generalisation = 'holds beyond the original sample'
    elif new_holds <= 2:
        generalisation = 'does not hold beyond the original sample'
    else:
        generalisation = 'mixed evidence'
    return {'paper_periods_holding': paper_holds, 'consistency_check': consistency,
            'new_periods_holding': new_holds, 'generalisation': generalisation}


# ---------------------------------------------------------------- main

def run(panel_path=PANEL_PATH, dense_path=DENSE_PANEL_PATH, results_dir=RESULTS_DIR, verbose=True):
    say = print if verbose else (lambda *a, **k: None)
    rng = np.random.default_rng(BOOT_SEED)
    panel = load_panel(panel_path)
    dense = load_panel(dense_path)
    for name, p in (('daily panel', panel), ('hourly panel', dense)):
        say(f"{name}: {len(p)} samples ({p['utc'].min()} to {p['utc'].max()}); "
            f"excluded: {p['excluded'].value_counts().to_dict() or 'none'}")
    paper = [assess(dense, *p, rng, DENSE_BOOT_BLOCK) for p in PAPER_PERIODS]
    new = [assess(panel, *p, rng, BOOT_BLOCK) for p in NEW_PERIODS]
    for r in paper + new:
        if r['decision'] == INSUFFICIENT:
            say(f"  {r['period']:32s} n={r['n_samples']:4d}  {r['decision']}")
            continue
        lo, hi = r['modal_bin_range_pp']
        say(f"  {r['period']:32s} n={r['n_samples']:4d}  kink-bin share {r['kink_bin_share']:.2f}  "
            f"modal bin [{lo:+.1f}, {hi:+.1f}) pp  above-kink share {r['share_above_kink_bin']:.2f}  "
            f"bootstrap {r['bootstrap_mode_proportion']:.2f}  ->  {r['decision']}")
    summary = overall(paper, new)
    say(f"\nConsistency check: {summary['paper_periods_holding']}/3 paper periods -> {summary['consistency_check']}")
    say(f"Generalisation: {summary['new_periods_holding']}/6 new periods -> {summary['generalisation']}")
    results = {'criterion': 'analysis_plans/kink_clustering_criterion.md', 'panel': panel_path,
               'dense_panel': dense_path,
               'bin_width_pp': BIN_WIDTH, 'paper_periods': paper, 'new_periods': new, 'summary': summary,
               'bootstrap': {'block_samples_daily': BOOT_BLOCK, 'block_samples_hourly': DENSE_BOOT_BLOCK,
                             'reps': BOOT_REPS, 'seed': BOOT_SEED}}
    if results_dir:
        os.makedirs(results_dir, exist_ok=True)
        with open(f'{results_dir}/kink_clustering_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        say(f'Saved {results_dir}/kink_clustering_results.json')
    return results


if __name__ == '__main__':
    run()
