"""
Simulation check of the regime 1 decision rules (supports Amendment 1 in
analysis_plans/regime1_criterion.md).

Before running regime1_analysis.py on the real data, the decision rules are
tested on simulated data in which the cause of poor fit is known. Each
scenario builds a synthetic cdai.pkl from the original parameter table, runs
the full analysis on it, and compares the decision with the expected one.
The real data are never read.

Scenarios:
  A. The mis-dated switch is the only problem in regime 1.
     Expected: the correction explains the fit of regime 1 as a whole.
  B. Regime 1 fits poorly throughout, independently of the switch.
     Expected: the mis-dated switch is not the main cause.
  C. Regimes labelled "good fit" fit worse than those labelled "poor fit".
     Expected: inconclusive (construct validity fails).

Run from the repository root:
    python simulate_regime1.py
"""

import os
import tempfile

import numpy as np
import pandas as pd

import regime1_analysis as a

GOOD_NOISE = 0.001      # 0.1 percentage points
POOR_NOISE = 0.01       # 1 percentage point
N_OBS = 30_000


def make_data(path, noisy_regimes, seed):
    rng = np.random.default_rng(seed)
    start, end = pd.Timestamp('2019-11-09'), pd.Timestamp('2020-05-08 23:00')
    ts = pd.to_datetime(np.sort(rng.uniform(start.value, end.value, N_OBS).astype('int64')))
    util = np.clip(0.5 + np.cumsum(rng.normal(0, 0.004, N_OBS)), 0.05, 0.98)
    df = pd.DataFrame({'utilization_ratio': util}, index=pd.DatetimeIndex(ts, name='date'))
    regimes = a.assign_regimes(df.index, df.index.max())
    true = []
    for t, u, r in zip(df.index, util, regimes):
        if np.isnan(r):
            true.append(0.05)
            continue
        r = int(r)
        if r == 1 and t < a.ONCHAIN_SWITCH:   # the on-chain truth: old model until the switch
            r = 0
        true.append(a.model_borrow_apr(u, a.params_for(r)))
    noise = np.where(np.isin(regimes, noisy_regimes), POOR_NOISE, GOOD_NOISE)
    df['borrow_rates'] = np.array(true) + rng.normal(0, 1, N_OBS) * noise
    df.to_pickle(path)


SCENARIOS = [
    ('A', 'mis-dated switch is the only problem in regime 1', [2, 3, 8], a.EXPLAINS_REGIME),
    ('B', 'regime 1 fits poorly throughout', [1, 2, 3, 8], a.NOT_MAIN_CAUSE),
    ('C', 'labelled good regimes fit worst', [0, 4], a.INCONCLUSIVE),
]


def main(seeds=(1, 2, 3)):
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'cdai_sim.pkl')
        for name, description, noisy, expected in SCENARIOS:
            for seed in seeds:
                make_data(path, noisy, seed)
                result = a.run(data_path=path, results_dir=None, llm_path=None, verbose=False)
                rows.append({'scenario': name, 'description': description, 'seed': seed,
                             'expected': expected, 'decision': result['decision'],
                             'correct': result['decision'] == expected})
    table = pd.DataFrame(rows)
    print(table[['scenario', 'seed', 'decision', 'correct']].to_string(index=False))
    os.makedirs('results', exist_ok=True)
    table.to_csv('results/regime1_simulation_check.csv', index=False)
    print(f"\n{table['correct'].sum()}/{len(table)} simulated decisions match the known answer.")
    print('Saved results/regime1_simulation_check.csv')


if __name__ == '__main__':
    main()
