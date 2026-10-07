"""
Reproduce the fund-concentration figures of Section 5.1.3 (Figure 6): the share
of locked funds held by the three largest accounts on Compound.

The paper reports, for 2020-06-04, 50.3 per cent for DAI, 60.0 for ETH and 47.3
for USDC. notebooks/compound/compound-wealth.ipynb plots the distributions but
does not print these shares. This script executes, unchanged, the notebook cells
that load the event logs and compute balances (compute_balances, which replays
Transfer events), and applies the rule of utils.plot_cumulative_hist (positive
balances only). Two versions, as fixed in Amendment 2 of
analysis_plans/reproduction_liquidity_wealth_criterion.md:

  all events      what the notebook computes from the committed logs today
  to 2020-06-04   events in blocks up to the end of 2020-06-04 UTC, the paper's
                  date; the verdict is applied to this version

Output: results/reproduction_concentration.csv

Run from the repository root:
    python scripts/reproduce_concentration.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
import compounds_research.utils  # noqa: E402,F401

import matplotlib  # noqa: E402
matplotlib.use('Agg')
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

NOTEBOOK = 'notebooks/compound/compound-wealth.ipynb'
BLOCK_TIMES = 'data/derived/eth_block_times_sampled.csv'
OUT = 'results/reproduction_concentration.csv'
CUTOFF = pd.Timestamp('2020-06-05 00:00:00')       # end of 2020-06-04 UTC (exclusive)
PAPER = {'cdai': 50.3, 'ceth': 60.0, 'cusdc': 47.3}  # per cent held by the three largest accounts
TOP_N = 3


def notebook_namespace():
    cells = [c for c in json.load(open(NOTEBOOK))['cells'] if c['cell_type'] == 'code']
    ns = {'__name__': 'compound_wealth'}
    run = []
    # Execute cells in order up to the one defining compute_balances, skipping any
    # cell that loads the events or computes balances (done below, once per version).
    for i, c in enumerate(cells):
        src = ''.join(c['source'])
        if 'load_events()' in src.replace('def load_events()', '') or 'compute_balances()' in src.replace('def compute_balances()', ''):
            continue
        exec(compile(src, f'{NOTEBOOK} [cell {i}]', 'exec'), ns)
        first = next((l for l in src.splitlines() if l.strip()), '')
        run.append(f'{i}: {first[:60]}')
        if 'def compute_balances' in src:
            break
    print('Executed notebook cells unchanged:')
    for r in run:
        print('   ', r)
    if 'compute_balances' not in ns:
        sys.exit('compute_balances was not found in the notebook')
    return ns


def shares(balances):
    pos = sorted((v for _, v in balances if v > 0), reverse=True)
    total = sum(pos)
    return 100 * sum(pos[:TOP_N]) / total, len(pos)


def verdict(ours, paper):
    if round(ours, 1) == round(paper, 1):
        return 'exact'
    if abs(ours - paper) <= 1.0:
        return 'numerical'
    return 'not reproduced'


def main():
    ns = notebook_namespace()
    events = ns['load_events']()
    print('#events', len(events))

    bt = pd.read_csv(BLOCK_TIMES).sort_values('block_number')
    blocks = np.array([int(e['blockNumber']) for e in events])
    ts = np.interp(blocks, bt['block_number'], bt['timestamp'])
    cutoff_ts = CUTOFF.timestamp()
    last_event = pd.to_datetime(ts.max(), unit='s')
    print(f'Latest event in the logs: {last_event:%Y-%m-%d %H:%M} UTC (interpolated; clamped to the range of the block-time table)')
    if ts.max() < cutoff_ts:
        print('  note: logs end before the cutoff')

    rows = []
    for label, subset in [('all events', events),
                          ('to 2020-06-04', [e for e, t in zip(events, ts) if t < cutoff_ts])]:
        ns['events'] = subset                       # compute_balances reads the global `events`
        balances = ns['compute_balances']()
        for market, paper in PAPER.items():
            share, n = shares(balances[market])
            v = verdict(share, paper) if label == 'to 2020-06-04' else '(not judged)'
            rows.append({'version': label, 'market': market, 'paper_pct': paper,
                         'ours_pct': round(share, 3), 'accounts_positive': n, 'verdict': v})
            print(f'  {label:14s} {market:6s} paper {paper:5.1f}  ours {share:6.2f}  '
                  f'accounts with positive balance {n:6d}  {v}')

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print('Saved', OUT)


if __name__ == '__main__':
    main()
