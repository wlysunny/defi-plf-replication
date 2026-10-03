"""
Check the decision rules of aave_kink_analysis.py on synthetic data with known
answers, before the real Aave V3 data are examined.

Synthetic files have the exact column layout of the two collection scripts.
Utilisation is generated around the kink in force (which changes mid-sample, as
on Aave), and the interest-rate parameters are written in ray units.

Scenarios (all four reserves, three periods each):
  A  utilisation tightly around the kink                -> every period Holds
  B  utilisation about 20 points below the kink         -> every period Does not hold
  C  utilisation about 5 points above the kink          -> every period Does not hold
  V  as A, but the subgraph's utilisation is 3 points off the chain's
                                                          -> validation fails, weekly chain data used, Holds
  M  USDC and USDT around the kink in every period; DAI only in 2023; WETH only in 2024;
     otherwise 20 points below. 8 of 12 hold but only 2 reserves hold in 2 of 3 periods
                                                          -> overall Mixed evidence (tests the per-reserve condition)

The overall verdict is checked as well as each period decision.

Run from the repository root:
    python simulate_aave_kink.py
"""

import os
import tempfile

import numpy as np
import pandas as pd

import aave_kink_analysis as a
import kink_clustering_analysis as k
from collect_aave_v3_rate_params import COLUMNS as PARAM_COLUMNS, VALIDATION_EVERY
from collect_aave_v3_subgraph import COLUMNS as SUBGRAPH_COLUMNS
from simulate_kink_clustering import ar1

RAY = 10 ** 27
TOTAL = 10 ** 24
ASSETS = {'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', 'USDT': '0xdac17f958d2ee523a2206206994597c13d831ec7',
          'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f', 'WETH': '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'}
EXPECTED = {'A': k.HOLDS, 'B': k.NOT_HOLD, 'C': k.NOT_HOLD, 'V': k.HOLDS, 'M': None}
EXPECTED_VERDICT = {'A': 'clustering at the kink holds on Aave V3',
                    'B': 'clustering at the kink does not hold on Aave V3',
                    'C': 'clustering at the kink does not hold on Aave V3',
                    'V': 'clustering at the kink holds on Aave V3', 'M': 'mixed evidence'}
M_HOLDING_YEARS = {'USDC': (2023, 2024, 2025), 'USDT': (2023, 2024, 2025), 'DAI': (2023,), 'WETH': (2024,)}


def m_expected(symbol, period_label):
    year = int(period_label.split()[1][:4])
    return k.HOLDS if year in M_HOLDING_YEARS[symbol] else k.NOT_HOLD


def make_files(directory, scenario, seed):
    rng = np.random.default_rng(seed)
    times = pd.date_range('2023-02-01', '2025-11-30', freq='D')
    n = len(times)
    sg_rows, pr_rows = [], []
    for symbol, asset in ASSETS.items():
        kink = np.where(times < pd.Timestamp('2024-06-01'), 90.0, 92.0)
        if symbol == 'WETH':
            kink = np.where(times < pd.Timestamp('2024-06-01'), 80.0, 90.0)
        if scenario in ('A', 'V'):
            util = kink + ar1(n, 1.2, 0.7, rng)
        elif scenario == 'M':
            near = np.isin(times.year, M_HOLDING_YEARS[symbol])
            util = np.where(near, kink + ar1(n, 1.2, 0.7, rng), kink - 20 + ar1(n, 4, 0.9, rng))
        elif scenario == 'B':
            util = kink - 20 + ar1(n, 4, 0.9, rng)
        else:
            util = kink + 5 + ar1(n, 1.2, 0.7, rng)
        util = np.clip(util, 1, 99.5)
        offset = 3.0 if scenario == 'V' else 0.0
        base, s1, s2 = 0, int(0.06 * RAY), int(0.6 * RAY)
        for i, (t, u, kk) in enumerate(zip(times, util, kink)):
            utc = t.strftime('%Y-%m-%dT%H:%M:%SZ')
            ku = kk / 100
            uu = u / 100
            rate = base + (s1 * uu / ku if uu <= ku else s1 + s2 * (uu - ku) / (1 - ku))
            rate = int(rate)
            sg = dict.fromkeys(SUBGRAPH_COLUMNS, '1')
            sg.update({'symbol': symbol, 'reserve_id': asset + '0x2f39d218133afab8f2b819b1066c7e434ad94e9e',
                       'sample_utc': utc, 'sample_timestamp': int(t.timestamp()), 'staleness_seconds': 600,
                       'item_utilizationRate': f'{(u + offset) / 100:.6f}', 'item_variableBorrowRate': str(rate)})
            sg_rows.append(sg)
            pr = dict.fromkeys(PARAM_COLUMNS, '')
            pr.update({'symbol': symbol, 'asset': asset, 'sample_utc': utc, 'block': 16_500_000 + i * 7200,
                       'block_timestamp': int(t.timestamp()) - 5, 'strategy': '0xabc', 'strategy_version': 2,
                       'pool_currentVariableBorrowRate': str(rate),
                       'irm_optimalUsageRatio': str(int(ku * RAY)), 'irm_baseVariableBorrowRate': str(base),
                       'irm_variableRateSlope1': str(s1), 'irm_variableRateSlope2': str(s2)})
            if i % VALIDATION_EVERY == 0:
                debt = int(TOTAL * uu)
                pr.update({'val_aToken_totalSupply': str(TOTAL), 'val_variableDebt_totalSupply': str(debt),
                           'val_stableDebt_totalSupply': '0', 'val_underlying_balanceOf_aToken': str(TOTAL - debt)})
            pr_rows.append(pr)
    sg_path, pr_path = os.path.join(directory, 'sg.csv'), os.path.join(directory, 'pr.csv')
    pd.DataFrame(sg_rows, columns=SUBGRAPH_COLUMNS).to_csv(sg_path, index=False)
    pd.DataFrame(pr_rows, columns=PARAM_COLUMNS).to_csv(pr_path, index=False)
    return sg_path, pr_path


def main(seeds=(1, 2, 3)):
    total = correct = verdicts_ok = runs = 0
    for scenario, expected_all in EXPECTED.items():
        for seed in seeds:
            with tempfile.TemporaryDirectory() as d:
                sg, pr = make_files(d, scenario, seed)
                out = a.run(sg, pr, results_path=None, verbose=False)
            runs += 1
            v_ok = out['summary']['verdict'] == EXPECTED_VERDICT[scenario]
            verdicts_ok += v_ok
            if not v_ok:
                print(f"  VERDICT MISMATCH {scenario} seed {seed}: {out['summary']}")
            for r in out['results']:
                total += 1
                expected = m_expected(r['symbol'], r['period']) if scenario == 'M' else expected_all
                ok = r['decision'] == expected
                if scenario == 'V':
                    ok = ok and r['utilisation_source'] == 'chain (weekly)'
                else:
                    ok = ok and r['utilisation_source'] == 'subgraph'
                correct += ok
                if not ok:
                    print(f"  MISMATCH {scenario} seed {seed} {r['period']}: {r['decision']} "
                          f"[{r['utilisation_source']}], expected {expected}")
        print(f'Scenario {scenario}: done')
    print(f'\n{correct}/{total} period decisions match the known answer.')
    print(f'{verdicts_ok}/{runs} overall verdicts match the known answer.')


if __name__ == '__main__':
    main()
