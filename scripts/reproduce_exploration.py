"""
Reproduce Table 2 and Figures 1 to 5 of the paper with the authors' own code.

The code for these results is in notebooks/exploration.ipynb, but the notebook
does not run from top to bottom as stored: some calls are missing or were made
with other arguments, and two functions rely on a global `aave` that no cell
defines. This script therefore does not edit the notebook. It

  1. executes, unchanged, the notebook's set-up cells and every cell that
     defines a function;
  2. defines `aave = analyze_aave.load_data()`, the only addition. This exact
     line was in the notebook until commit cfcbabf (2020-05-29) and was removed
     in f4f9d28 (2020-08-31, "Updated UIP analysis"), while the functions that
     use `aave` were kept;
  3. redirects plt.savefig, whose paths point to the authors' LaTeX project, to
     figures/reproduction/ (file names kept);
  4. calls the authors' functions with the arguments that correspond to the
     paper: Table 2 (get_median_usd_funds_locked for the 15 cells of the
     table), Figure 1 (plot_market_summaries), Figures 2 to 4
     (plot_liquidity_market for eth, dai, usdc) and Figure 5
     (plot_illiquidity for dai).

Table 2 is compared with the paper according to
analysis_plans/reproduction_liquidity_wealth_criterion.md (Amendment 1):
exact if equal at two decimals, numerical if within 5 per cent.

Output: figures/reproduction/*.png|pdf and results/reproduction_table2.csv.
The dYdX shading loops are slow (several minutes per figure).

Run from the repository root:
    python scripts/reproduce_exploration.py
"""

import matplotlib
matplotlib.rcParams['savefig.bbox'] = 'tight'  # keep axis labels inside the saved figure
import json
import os
import sys

sys.path.insert(0, os.path.abspath('.'))
import compounds_research.utils  # noqa: E402,F401  (import first: avoids the circular import)

import matplotlib  # noqa: E402
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

NOTEBOOK = 'notebooks/exploration.ipynb'
FIG_DIR = 'figures/reproduction'
TABLE_OUT = 'results/reproduction_table2.csv'

# Paper, Table 2: median total supply in millions of USD, inception to 7 May 2020.
PAPER_TABLE2 = {
    ('compound', 'eth'): 76.58, ('compound', 'usdc'): 31.54, ('compound', 'dai'): 24.82,
    ('compound', 'sai'): 36.94, ('compound', 'bat'): 0.95,
    ('aave', 'eth'): 4.80, ('aave', 'usdc'): 4.12, ('aave', 'dai'): 0.95, ('aave', 'usdt'): 3.92,
    ('aave', 'bat'): 0.08, ('aave', 'lend'): 3.60, ('aave', 'link'): 12.21,
    ('dydx', 'eth'): 19.41, ('dydx', 'usdc'): 6.58, ('dydx', 'dai'): 4.64,
}


def load_notebook_namespace():
    cells = [c for c in json.load(open(NOTEBOOK))['cells'] if c['cell_type'] == 'code']
    ns = {'__name__': 'exploration'}
    run = []
    for i, c in enumerate(cells):
        src = ''.join(c['source'])
        if i < 3 or 'def ' in src:
            exec(compile(src, f'{NOTEBOOK} [cell {i}]', 'exec'), ns)
            run.append(i)
    print(f'Executed notebook cells {run} unchanged')
    return ns


def redirect_savefig():
    os.makedirs(FIG_DIR, exist_ok=True)
    original = plt.savefig

    def savefig(path, *args, **kwargs):
        target = os.path.join(FIG_DIR, os.path.basename(str(path)))
        original(target, *args, **kwargs)
        print('  saved', target)
    plt.savefig = savefig


def verdict(ours, paper):
    if round(ours, 2) == round(paper, 2):
        return 'exact'
    if abs(ours - paper) <= 0.05 * paper:
        return 'numerical'
    return 'not reproduced'


def main():
    ns = load_notebook_namespace()
    ns['aave'] = ns['analyze_aave'].load_data()  # restores the line removed in f4f9d28; see docstring
    redirect_savefig()

    print('\nTable 2')
    rows = []
    for (platform, market), paper in PAPER_TABLE2.items():
        try:
            ours = float(ns['get_median_usd_funds_locked'](platform, market)) / 1e6
            v = verdict(ours, paper)
        except Exception as e:  # report and continue: one failing cell should not hide the others
            ours, v = float('nan'), f'error: {type(e).__name__}: {e}'
        rows.append({'platform': platform, 'market': market, 'paper_musd': paper,
                     'ours_musd': round(ours, 4), 'verdict': v})
        print(f'  {platform:9s} {market:5s} paper {paper:7.2f}  ours {ours:9.3f}  {v}')
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(TABLE_OUT), exist_ok=True)
    df.to_csv(TABLE_OUT, index=False)
    print('  ', df['verdict'].value_counts().to_dict())
    print('  saved', TABLE_OUT)

    calls = [('Figure 1', 'plot_market_summaries', ()),
             ('Figure 2', 'plot_liquidity_market', ('eth',)),
             ('Figure 3', 'plot_liquidity_market', ('dai',)),
             ('Figure 4', 'plot_liquidity_market', ('usdc',)),
             ('Figure 5', 'plot_illiquidity', ('dai',))]
    for label, fn, args in calls:
        print(f'\n{label}: {fn}{args}')
        try:
            ns[fn](*args)
        except Exception as e:
            print(f'  error: {type(e).__name__}: {e}')
        plt.close('all')


if __name__ == '__main__':
    main()
