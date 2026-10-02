"""
Simulation check of the kink-clustering decision rules
(analysis_plans/kink_clustering_criterion.md).

Synthetic panels in the format of data/onchain/cdai_panel.csv are generated
with a known utilisation process, and the full analysis is run on each. The
real panel is never read.

Both the about-daily panel (new-data periods) and the about-hourly panel
(the paper's periods) are simulated.

Scenarios (expected decision in every period):
  A. Utilisation fluctuates tightly around the kink            -> Holds
  B. Utilisation wanders well below the kink                   -> Does not hold
  C. Utilisation sits mostly 3-7 points above the kink         -> Does not hold
  D. Utilisation centred on the kink but very persistent and
     widely spread                                             -> reported, no fixed expectation

The kink changes from 90% to 80% in mid-2022 in every scenario, to check that
distances are measured from the kink active at each sample.

Run from the repository root:
    python simulate_kink_clustering.py
"""

import os
import tempfile

import numpy as np
import pandas as pd

import kink_clustering_analysis as k

TOTAL = 10 ** 26           # pool size in wei units; only ratios matter
COLUMNS = ['block', 'timestamp', 'utc', 'cdai_borrowRatePerBlock', 'cdai_supplyRatePerBlock',
           'cdai_getCash', 'cdai_totalBorrows', 'cdai_totalReserves', 'cdai_reserveFactorMantissa',
           'cdai_interestRateModel', 'irm_baseRatePerBlock', 'irm_multiplierPerBlock',
           'irm_jumpMultiplierPerBlock', 'irm_kink']


def ar1(n, sd, phi, rng):
    x = np.zeros(n)
    eps = rng.normal(0, sd * np.sqrt(1 - phi ** 2), n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + eps[i]
    return x


def make_panel(path, scenario, seed, times):
    rng = np.random.default_rng(seed)
    n = len(times)
    kink = np.where(times < pd.Timestamp('2022-07-01'), 90.0, 80.0)
    if scenario == 'A':
        util = kink + ar1(n, 1.2, 0.7, rng)
    elif scenario == 'B':
        util = 55 + ar1(n, 10, 0.97, rng)
    elif scenario == 'C':
        util = kink + 5 + ar1(n, 1.2, 0.7, rng)
    else:
        util = kink + ar1(n, 6, 0.98, rng)
    util = np.clip(util, 1, 99.5)
    rows = []
    for i, (t, u, kk) in enumerate(zip(times, util, kink)):
        borrows = int(TOTAL * u / 100)
        reserves = 10 ** 22
        cash = TOTAL - borrows + reserves
        kink_value = str(int(kk / 100 * 10 ** 18))
        if i % 97 == 5:            # a few samples whose model has no kink getter
            kink_value = ''
        if i % 211 == 7:           # a few samples with no borrows
            borrows, cash = 0, TOTAL
        rows.append([8_983_575 + i * 6000, int(t.timestamp()), t.strftime('%Y-%m-%d %H:%M:%S'),
                     '1', '1', str(cash), str(borrows), str(reserves), '1', '0xabc', '1', '1', '1', kink_value])
    pd.DataFrame(rows, columns=COLUMNS).to_csv(path, index=False)


EXPECTED = {'A': k.HOLDS, 'B': k.NOT_HOLD, 'C': k.NOT_HOLD, 'D': None}


def main(seeds=(1, 2, 3)):
    records = []
    with tempfile.TemporaryDirectory() as tmp:
        path, dense = os.path.join(tmp, 'panel.csv'), os.path.join(tmp, 'dense.csv')
        daily_times = pd.date_range('2019-11-23', '2025-11-30', freq='D')
        hourly_times = pd.date_range('2020-02-21', '2020-04-21 23:00', freq='h')
        for scenario, expected in EXPECTED.items():
            for seed in seeds:
                make_panel(path, scenario, seed, daily_times)
                make_panel(dense, scenario, seed + 100, hourly_times)
                res = k.run(panel_path=path, dense_path=dense, results_dir=None, verbose=False)
                for r in res['paper_periods'] + res['new_periods']:
                    records.append({'scenario': scenario, 'seed': seed, 'period': r['period'],
                                    'decision': r['decision'], 'expected': expected,
                                    'correct': None if expected is None else r['decision'] == expected})
    table = pd.DataFrame(records)
    print(pd.crosstab([table['scenario']], table['decision']).to_string())
    checked = table.dropna(subset=['expected'])
    print(f"\n{int(checked['correct'].sum())}/{len(checked)} period decisions match the known answer "
          f"(scenarios A-C); scenario D is reported for information.")
    os.makedirs('results', exist_ok=True)
    table.to_csv('results/kink_clustering_simulation_check.csv', index=False)
    print('Saved results/kink_clustering_simulation_check.csv')


if __name__ == '__main__':
    main()
