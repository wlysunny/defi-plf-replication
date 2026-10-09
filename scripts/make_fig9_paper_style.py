"""
Figure 9 redrawn in the authors' own format, for the update presentation.

The authors draw Figure 9 in notebooks/compound/3_cdai_regimes.ipynb (cell 4) with

    df_cdai['(Actual Rate) - (Kink Rate)'] = df_cdai['borrow_rates'] - df_cdai['kink_rate']
    sns.histplot(df_cdai['(Actual Rate) - (Kink Rate)'])

This script makes the same call (seaborn histplot, default bins and colour, rate as a
fraction, same x-axis label) for three versions of the paper's first period
(21 Feb - 13 Mar 2020):

  (a) the original API rate, as the authors compared it with the kink rate
  (b) the same API rate converted from a compounded yield to a simple annual rate
  (c) the on-chain borrow rate

Differences from the paper's figure, stated on the slide:
  - hourly samples (n = 501), as in the rest of the update; the paper's figure uses daily data
  - three panels share one x-axis so they can be compared; a dashed line marks 0 (at the kink)

Output: figures/update/fig9_paper_style.png
Run from the repository root:
    python scripts/make_fig9_paper_style.py
"""

import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import seaborn as sns  # noqa: E402

import exploratory_apy_check as apy  # noqa: E402

sys.path.insert(0, os.getcwd())          # repository root, for the authors' packages
import pandas as pd  # noqa: E402
from compounds_research import settings  # noqa: E402
from compounds_research.compound.utils import make_original_df  # noqa: E402
from simulator.engine import dai_rate_model  # noqa: E402
from simulator.engine.dai_rate_params import PARAM_REGIMES  # noqa: E402

OUT = 'figures/update/fig9_paper_style.png'
OUT_DAILY = 'figures/update/fig9_paper_style_daily.png'
XLABEL = '(Actual Rate) - (Kink Rate)'   # the authors' column name, used as their x-axis label


def distplot_bins(v):
    """Bin count used by seaborn's old distplot (the function the paper's figure was drawn
    with): Freedman-Diaconis rule, capped at 50 bins."""
    v = np.asarray(v)
    iqr = np.subtract(*np.percentile(v, [75, 25]))
    h = 2 * iqr / len(v) ** (1 / 3)
    bins = int(np.sqrt(len(v))) if h == 0 else int(np.ceil((v.max() - v.min()) / h))
    return min(bins, 50)


def naive_day(idx):
    idx = pd.DatetimeIndex(idx)
    if idx.tz is not None:
        idx = idx.tz_convert('UTC').tz_localize(None)
    return idx.normalize()


def authors_daily(regime='6'):
    """Daily series exactly as the authors build Figure 9, plus the two comparisons.

    (a) make_original_df('cdai', 'D'), rows with regime == 6, borrow_rates - kink_rate
        (the authors' code, unchanged)
    (b) the same pipeline, but the raw API rate is converted to a simple rate before the
        daily mean (the conversion is applied where the authors' rate enters)
    (c) on-chain borrow rate, daily mean of the hourly panel, on the same days
    """
    df = make_original_df(token='cdai', resampling_frequency='D')
    df = df[df['regime'] == float(regime)].copy()
    df['kink_rate'] = (df['kink'] * df['multiplier_per_block'] / 1e18 + df['base_rate_per_block']) \
        / 1e18 * dai_rate_model.BLOCKS_PER_YEAR
    a = df['borrow_rates'] - df['kink_rate']

    # (b): repeat make_original_df's resampling on the converted raw rate
    raw = pd.read_pickle(os.path.join(settings.DATA_PATH, 'compound', 'cdai.pkl'))
    conv = pd.Series(np.asarray(apy.to_apr(raw['borrow_rates'], 'apy_N')), index=raw.index)
    conv = conv.resample('D').mean()
    conv.index = naive_day(conv.index)
    days = naive_day(df.index)
    b = pd.Series(conv.reindex(days).values, index=df.index) - df['kink_rate']

    # (c): on-chain, daily mean on the same days
    h = apy.load()
    chain = pd.Series(h['chain_borrow_apr'].values, index=pd.DatetimeIndex(h['utc']))
    chain = chain.groupby(naive_day(chain.index)).mean()
    c = pd.Series(chain.reindex(days).values, index=df.index) - df['kink_rate']

    print(f'\nAuthors\' pipeline: {len(df)} days with regime {regime}, '
          f'{days.min().date()} to {days.max().date()}; on-chain days available: {c.notna().sum()}')
    print('Panel (a), sorted (compare with the paper\'s bars):')
    print(np.round(np.sort(a.dropna().values), 4))
    return [("(a) Paper's comparison: API rate", a),
            ('(b) API rate converted to simple', b),
            ('(c) On-chain rate', c)]


def series():
    df = apy.load()
    s = df[(df['utc'] >= '2020-02-21') & (df['utc'] < '2020-03-14')].copy()
    s = s.reset_index(drop=True)           # the loaded frame has duplicate index labels
    kink = s['kink_rate_apr']
    return s, [
        ("(a) Paper's comparison: API rate", s['borrow_rates'] - kink),
        ('(b) API rate converted to simple', apy.to_apr(s['borrow_rates'], 'apy_N') - kink),
        ('(c) On-chain rate', s['chain_borrow_apr'] - kink),
    ]


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    s, panels = series()

    # Report what is plotted, so the slide's numbers can be checked against it
    print(f'n = {len(s)} hourly samples, {s["utc"].min()} to {s["utc"].max()}')
    for label, v in panels:
        v = v.dropna()
        daily = v.groupby(s.loc[v.index, 'utc'].dt.floor('D')).mean()
        print(f'{label:40s} median {np.median(v) * 100:+.3f} pp | min {v.min() * 100:+.2f} '
              f'max {v.max() * 100:+.2f} pp | daily-mean median {np.median(daily) * 100:+.3f} pp')

    plt.rcdefaults()                       # plain matplotlib look, as in the authors' notebook
    plt.rcParams.update({'font.size': 15, 'axes.titlesize': 16})

    # Daily version: the authors' own pipeline (3_cdai_regimes.ipynb, cells 3-4)
    daily_panels = authors_daily()

    for out, data, style in [(OUT, panels, {}),
                             (OUT_DAILY, daily_panels, {'alpha': 0.4, 'linewidth': 0})]:
        fig, axes = plt.subplots(1, 3, figsize=(16, 5.6), sharex=True, sharey=not style)
        for ax, (label, v) in zip(axes, data):
            v = v.dropna()
            if style:   # daily, paper-style version: reproduce distplot's binning too
                print(f'  {label}: {distplot_bins(v)} bins')
                sns.histplot(v, ax=ax, bins=distplot_bins(v), **style)
                # the paper's axes: x ticks every 0.02, integer counts, no y-axis label
                ax.set_xticks(np.round(np.arange(-0.02, 0.121, 0.02), 2))
                ax.set_xlim(-0.032, 0.128)
                ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
                ax.set_ylabel('')
                ax.tick_params(axis='x', labelsize=12)
            else:
                sns.histplot(v, ax=ax, **style)
            ax.axvline(0, color='0.35', linestyle='--', linewidth=1.2)
            ax.set_title(f'{label}\nmedian {np.median(v) * 100:+.2f} pp', fontsize=15)
            ax.set_xlabel(XLABEL)
        fig.tight_layout()
        fig.savefig(out, dpi=120)
        plt.close(fig)
        print('Saved', out)

if __name__ == '__main__':
    main()
