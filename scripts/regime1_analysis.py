"""
Regime 1 re-analysis, implementing the pre-specified criterion in
analysis_plans/regime1_criterion.md, including Amendment 1.

Steps, in the order the criterion specifies:
  1. Load cDAI observations and average them within each hour.
  2. Compute the modelled borrow rate for every hour from the observed
     utilisation, using the original rate functions and parameter table.
  3. Time-alignment check around the on-chain model switch.
  4. Mean absolute error (MAE, primary) and median absolute error (MdAE,
     secondary) with block-bootstrap confidence intervals for every regime;
     construct-validity check against the authors' labels, and against the
     auxiliary LLM labels if they have been saved.
  5. Compare original and corrected parameters for the two-day window and for
     the whole of regime 1.
  6. Apply the decision rules and save all results.

Run from the repository root:
    python scripts/regime1_analysis.py
"""

import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath('.'))
from simulator.engine import dai_rate_model  # noqa: E402
from simulator.engine.dai_rate_params import PARAM_REGIMES, PARAM_REGIME_NUMS  # noqa: E402

DATA_PATH = 'data/compound/cdai.pkl'
LLM_OUTPUT_PATH = 'analysis_plans/llm_labelling_raw_output.txt'
RESULTS_DIR = 'results'

ONCHAIN_SWITCH = pd.Timestamp('2019-12-20 00:26:19')   # block 9,133,122
WINDOW_START = pd.Timestamp(PARAM_REGIME_NUMS['1'])     # 2019-12-17 21:57:22
WINDOW_END = ONCHAIN_SWITCH

# Researcher's labels, as committed in the criterion.
RESEARCHER_LABELS = {0: 'Good fit', 1: 'Poor fit', 2: 'Poor fit', 3: 'Poor fit',
                     4: 'Good fit', 5: 'Not stated', 6: 'Not stated', 7: 'Not stated',
                     8: 'Poor fit', 9: 'Not stated', 10: 'Not stated'}

MIN_WINDOW_HOURS = 24
BOOT_BLOCK = 24
BOOT_REPS = 2000
BOOT_SEED = 20261002
SCALE = 10 ** 18
POOL = 10 ** 24          # arbitrary pool size; only utilisation matters

INCONCLUSIVE = 'Inconclusive'
EXPLAINS_WINDOW = 'The correction explains the fit within the window'
EXPLAINS_REGIME = 'The correction explains the fit of regime 1 as a whole'
NOT_MAIN_CAUSE = 'The mis-dated switch is not the main cause of the poor fit'


# ---------------------------------------------------------------- data

def load_hourly(path):
    df = pd.read_pickle(path)
    return df[['borrow_rates', 'utilization_ratio']].resample('h').mean().dropna()


def regime_starts():
    return sorted((int(k), pd.Timestamp(v)) for k, v in PARAM_REGIME_NUMS.items())


def assign_regimes(index, data_end):
    """Original regime number of each timestamp (NaN before regime 0)."""
    starts = regime_starts()
    out = pd.Series(np.nan, index=index)
    for i, (num, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else data_end + pd.Timedelta(seconds=1)
        out[(index >= start) & (index < end)] = num
    return out


# ---------------------------------------------------------------- model

def params_for(regime_num):
    return PARAM_REGIMES[PARAM_REGIME_NUMS[str(regime_num)]]


def model_borrow_apr(utilisation, params):
    """Annual borrow rate (decimal) from utilisation, using the original rate function."""
    borrows = int(round(utilisation * POOL))
    per_block = dai_rate_model.get_borrow_rate(cash=POOL - borrows, borrows=borrows, reserves=0,
                                               regime_params=params)
    return per_block * dai_rate_model.BLOCKS_PER_YEAR / SCALE


def modelled_rates(hourly, regimes, corrected):
    """Modelled annual borrow rates; `corrected` applies regime 0 parameters until the on-chain switch."""
    values = []
    for ts, u, r in zip(hourly.index, hourly['utilization_ratio'], regimes):
        if np.isnan(r):
            values.append(np.nan)
            continue
        regime = int(r)
        if corrected and regime == 1 and ts < ONCHAIN_SWITCH:
            regime = 0
        values.append(model_borrow_apr(u, params_for(regime)))
    return pd.Series(values, index=hourly.index)


# ---------------------------------------------------------------- statistics

def summarise(errors, rng):
    """MAE and MdAE with 95% moving-block bootstrap intervals (errors in time order)."""
    e = np.asarray(errors, dtype=float)
    n = len(e)
    out = {'n_hours': int(n), 'mae': float(np.mean(e)) if n else float('nan'),
           'mdae': float(np.median(e)) if n else float('nan')}
    if n < BOOT_BLOCK:
        out.update(mae_ci_low=float('nan'), mae_ci_high=float('nan'),
                   mdae_ci_low=float('nan'), mdae_ci_high=float('nan'))
        return out
    n_blocks = int(np.ceil(n / BOOT_BLOCK))
    means, medians = np.empty(BOOT_REPS), np.empty(BOOT_REPS)
    for i in range(BOOT_REPS):
        starts = rng.integers(0, n - BOOT_BLOCK + 1, size=n_blocks)
        sample = np.concatenate([e[s:s + BOOT_BLOCK] for s in starts])[:n]
        means[i], medians[i] = sample.mean(), np.median(sample)
    out.update(mae_ci_low=float(np.percentile(means, 2.5)), mae_ci_high=float(np.percentile(means, 97.5)),
               mdae_ci_low=float(np.percentile(medians, 2.5)), mdae_ci_high=float(np.percentile(medians, 97.5)))
    return out


# ---------------------------------------------------------------- checks

def time_alignment(hourly):
    """
    Shift the model switch by whole hours around the on-chain time and find the
    shift that minimises the MAE over the 24 hours either side. Ties go to the
    smallest shift. The result is reported, not applied automatically.
    """
    lo, hi = ONCHAIN_SWITCH - pd.Timedelta(hours=24), ONCHAIN_SWITCH + pd.Timedelta(hours=24)
    sub = hourly[(hourly.index >= lo) & (hourly.index < hi)]
    old_rate = np.array([model_borrow_apr(u, params_for(0)) for u in sub['utilization_ratio']])
    new_rate = np.array([model_borrow_apr(u, params_for(1)) for u in sub['utilization_ratio']])
    observed = sub['borrow_rates'].to_numpy()
    by_offset = {}
    for offset in range(-12, 13):
        switch = ONCHAIN_SWITCH + pd.Timedelta(hours=offset)
        modelled = np.where(sub.index < switch, old_rate, new_rate)
        by_offset[offset] = float(np.mean(np.abs(modelled - observed)) * 100)
    best = min(by_offset, key=lambda k: (round(by_offset[k], 6), abs(k)))
    return {'hours_in_window': int(len(sub)), 'best_offset_hours': int(best),
            'mae_at_offset_0': by_offset[0], 'mae_at_best_offset': by_offset[best],
            'median_gap_between_models_pp': float(np.median(np.abs(old_rate - new_rate)) * 100),
            'mae_by_offset': {str(k): v for k, v in by_offset.items()}}


def validity(mae_by_regime, labels):
    good = [r for r, c in labels.items() if c == 'Good fit']
    poor = [r for r, c in labels.items() if c == 'Poor fit']
    reversed_pairs = [(p, g) for p in poor for g in good if not mae_by_regime[p] > mae_by_regime[g]]
    return {'good': good, 'poor': poor, 'pairs': len(good) * len(poor), 'reversed_pairs': reversed_pairs,
            'passed': bool(good) and bool(poor) and not reversed_pairs}


def read_llm_labels(path):
    if not path or not os.path.exists(path):
        return None
    canonical = {'good fit': 'Good fit', 'poor fit': 'Poor fit', 'not stated': 'Not stated'}
    labels = {}
    with open(path, encoding='utf-8') as f:
        for line in f:
            m = re.match(r'^\s*(\d+)\s*\|\s*(Good fit|Poor fit|Not stated)\s*\|', line, re.IGNORECASE)
            if m:
                labels[int(m.group(1))] = canonical[m.group(2).lower()]
    if sorted(labels) != list(range(11)):
        raise ValueError(f'Expected labels for regimes 0-10 in {path}, found {sorted(labels)}')
    return labels


def decide(valid, comp, benchmark):
    wo, wc, rc = comp['window_original'], comp['window_corrected'], comp['regime1_corrected']
    if not valid['passed'] or wc['n_hours'] < MIN_WINDOW_HOURS:
        return INCONCLUSIVE
    window_explained = (wo['mae_ci_low'] > benchmark
                        and wc['mae_ci_low'] <= benchmark
                        and wc['mae_ci_high'] < wo['mae_ci_low'])
    if not window_explained:
        return NOT_MAIN_CAUSE
    return EXPLAINS_REGIME if rc['mae_ci_low'] <= benchmark else EXPLAINS_WINDOW


# ---------------------------------------------------------------- main

def run(data_path=DATA_PATH, results_dir=RESULTS_DIR, llm_path=LLM_OUTPUT_PATH, verbose=True):
    say = print if verbose else (lambda *a, **k: None)
    rng = np.random.default_rng(BOOT_SEED)
    hourly = load_hourly(data_path)
    regimes = assign_regimes(hourly.index, hourly.index.max())
    observed_pp = hourly['borrow_rates'] * 100
    original = modelled_rates(hourly, regimes, corrected=False) * 100
    corrected = modelled_rates(hourly, regimes, corrected=True) * 100
    err_orig = (original - observed_pp).abs()
    err_corr = (corrected - observed_pp).abs()

    say(f'Hourly observations: {len(hourly)} ({hourly.index.min()} to {hourly.index.max()})')
    r0 = regimes == 0
    say(f'Scale check, regime 0 medians: observed {observed_pp[r0].median():.3f} pp, '
        f'modelled {original[r0].median():.3f} pp')

    align = time_alignment(hourly)
    say('\n[Check 1] Time alignment around the on-chain switch')
    say(f"  best offset {align['best_offset_hours']} h; MAE at 0 h {align['mae_at_offset_0']:.3f} pp, "
        f"at best {align['mae_at_best_offset']:.3f} pp; median gap between the two models "
        f"{align['median_gap_between_models_pp']:.3f} pp")

    per_regime = {num: summarise(err_orig[regimes == num].dropna().to_numpy(), rng)
                  for num, _ in regime_starts()}
    mae_by_regime = {k: v['mae'] for k, v in per_regime.items()}
    say('\n[Check 2] Error by regime, original parameters (percentage points)')
    for num, s in per_regime.items():
        say(f"  regime {num:2d} [{RESEARCHER_LABELS[num]:10s}] n={s['n_hours']:4d}  "
            f"MAE {s['mae']:.3f} [{s['mae_ci_low']:.3f}, {s['mae_ci_high']:.3f}]   MdAE {s['mdae']:.3f}")
    valid = validity(mae_by_regime, RESEARCHER_LABELS)
    say(f"  researcher labels: {'PASSED' if valid['passed'] else 'FAILED'}; "
        f"reversed pairs (poor, good): {valid['reversed_pairs'] or 'none'}")

    llm = read_llm_labels(llm_path)
    llm_result = None
    if llm is None:
        say(f'  LLM labels: not found at {llm_path} (auxiliary check not yet run)')
    else:
        differ = [k for k in range(11) if llm[k] != RESEARCHER_LABELS[k]]
        llm_result = {'labels': llm, 'agreement': 11 - len(differ), 'differing_regimes': differ}
        say(f'  LLM labels: agree on {11 - len(differ)}/11; differing regimes: {differ or "none"}')
        if any(RESEARCHER_LABELS[k] in ('Good fit', 'Poor fit') or llm[k] in ('Good fit', 'Poor fit')
               for k in differ):
            v2 = validity(mae_by_regime, llm)
            llm_result['validity'] = v2
            say(f"  validity under LLM labels: {'PASSED' if v2['passed'] else 'FAILED'}; "
                f"reversed pairs: {v2['reversed_pairs'] or 'none'}")

    in_window = (hourly.index >= WINDOW_START) & (hourly.index < WINDOW_END)
    in_r1 = (regimes == 1).to_numpy()
    comp = {'window_original': summarise(err_orig[in_window].to_numpy(), rng),
            'window_corrected': summarise(err_corr[in_window].to_numpy(), rng),
            'regime1_original': summarise(err_orig[in_r1].to_numpy(), rng),
            'regime1_corrected': summarise(err_corr[in_r1].to_numpy(), rng)}
    benchmark = max(mae_by_regime[0], mae_by_regime[4])
    say(f'\n[Comparison] benchmark (max MAE of regimes 0 and 4) = {benchmark:.3f} pp')
    for k, s in comp.items():
        say(f"  {k:18s} n={s['n_hours']:4d}  MAE {s['mae']:.3f} [{s['mae_ci_low']:.3f}, "
            f"{s['mae_ci_high']:.3f}]   MdAE {s['mdae']:.3f}")

    decision = decide(valid, comp, benchmark)
    say(f'\nDECISION: {decision}')

    results = {'criterion': 'analysis_plans/regime1_criterion.md (with Amendment 1)',
               'data': data_path, 'time_alignment': align, 'validity_researcher_labels': valid,
               'llm_check': llm_result, 'per_regime': per_regime, 'benchmark_mae': benchmark,
               'comparison': comp, 'decision': decision,
               'bootstrap': {'block_hours': BOOT_BLOCK, 'reps': BOOT_REPS, 'seed': BOOT_SEED}}
    if results_dir:
        os.makedirs(results_dir, exist_ok=True)
        table = pd.DataFrame(per_regime).T
        table.insert(0, 'label', [RESEARCHER_LABELS[i] for i in table.index])
        table.to_csv(f'{results_dir}/regime1_error_by_regime.csv', index_label='regime')
        with open(f'{results_dir}/regime1_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        say(f'Saved {results_dir}/regime1_results.json and {results_dir}/regime1_error_by_regime.csv')
    return results


if __name__ == '__main__':
    run()
