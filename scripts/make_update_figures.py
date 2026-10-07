"""
Figures for the update presentation, drawn from the committed data so that every
number on a slide can be regenerated.

  figures/update/rate_minus_kink_period1.png
      Paper's first kink period (21 Feb - 13 Mar 2020): borrow rate minus the
      kink rate (simple annual rate), for (a) the original API series as the
      authors used it, (b) the same series converted from a compounded yield,
      and (c) the on-chain rate. One panel each, shared axis.
  figures/update/utilisation_paper_periods.png
      On-chain utilisation minus the kink in the paper's three periods (hourly),
      with the kink bin of the pre-specified test shaded.

Run from the repository root:
    python scripts/make_update_figures.py
"""

import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import exploratory_apy_check as apy  # noqa: E402
import kink_clustering_analysis as k  # noqa: E402

OUT_DIR = 'figures/update'
SURFACE, INK, INK_2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e2dc'
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'

plt.rcParams.update({
    'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE, 'savefig.facecolor': SURFACE,
    'font.size': 20, 'axes.titlesize': 22, 'axes.labelsize': 20,
    'xtick.labelsize': 18, 'ytick.labelsize': 18,
    'axes.edgecolor': INK_2, 'axes.labelcolor': INK, 'xtick.color': INK_2, 'ytick.color': INK_2,
    'text.color': INK, 'axes.spines.top': False, 'axes.spines.right': False,
})


def histogram_rows(ax_list, series, bins, xlabel):
    for ax, (label, values, colour) in zip(ax_list, series):
        ax.hist(values, bins=bins, color=colour, edgecolor=SURFACE, linewidth=1.5)
        ax.axvline(0, color=INK, linewidth=2)
        med = float(np.median(values))
        ax.set_yticks([])
        ax.spines['left'].set_visible(False)
        ax.grid(axis='x', color=GRID, linewidth=1)
        ax.set_axisbelow(True)
        ax.set_title(label, loc='left', fontsize=20, color=INK)
        ax.set_title(f'median {med:+.2f} pp', loc='right', fontsize=20, color=INK_2)
    ax_list[-1].set_xlabel(xlabel)


def rate_minus_kink():
    df = apy.load()
    s = df[(df['utc'] >= '2020-02-21') & (df['utc'] < '2020-03-14')]
    raw = (s['borrow_rates'] - s['kink_rate_apr']) * 100
    conv = (apy.to_apr(s['borrow_rates'], 'apy_N') - s['kink_rate_apr']) * 100
    chain = (s['chain_borrow_apr'] - s['kink_rate_apr']) * 100
    lo, hi = -1.0, 1.0
    bins = np.arange(lo, hi + 0.05, 0.05)
    clip = lambda v: np.clip(v, lo, hi)
    fig, axes = plt.subplots(3, 1, figsize=(16, 9), sharex=True)
    histogram_rows(axes, [
        ("Original API, as used by the authors (yield minus simple rate)", clip(raw), ORANGE),
        ("Original API converted to a simple annual rate", clip(conv), BLUE),
        ("On-chain borrow rate", clip(chain), AQUA),
    ], bins, 'Borrow rate minus kink rate (percentage points); 0 = at the kink')
    fig.suptitle('Paper period 1 (21 Feb - 13 Mar 2020): the "above the kink" shift is a unit mismatch',
                 x=0.01, ha='left', fontsize=24)
    fig.text(0.01, 0.005, f'Hourly samples, n = {len(s)}. Values beyond ±1 pp shown at the edge. '
             'Sources: data/compound/cdai.pkl, data/onchain/cdai_panel_dense_2020.csv',
             fontsize=14, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    path = f'{OUT_DIR}/rate_minus_kink_period1.png'
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def utilisation_periods():
    dense = k.load_panel(k.DENSE_PANEL_PATH)
    dense = dense[dense['excluded'].isna()]
    lo, hi = -52.5, 17.5
    bins = np.arange(lo, hi + 5, 5)              # same 5 pp bins as the pre-specified test: edges at 2.5 + 5k, kink bin = (-2.5, 2.5)
    fig, axes = plt.subplots(3, 1, figsize=(16, 9), sharex=True)
    for ax, (label, start, end) in zip(axes, k.PAPER_PERIODS):
        d = dense[(dense['utc'] >= start) & (dense['utc'] < end)]['distance_pp'].clip(lo, hi)
        ax.axvspan(-2.5, 2.5, color=GRID, zorder=0)
        ax.hist(d, bins=bins, color=BLUE, edgecolor=SURFACE, linewidth=1.5, zorder=2)
        ax.axvline(0, color=INK, linewidth=2, zorder=3)
        ax.set_yticks([])
        ax.spines['left'].set_visible(False)
        share = float(np.mean(np.abs(d) < 2.5))
        name = label.replace('paper: ', '')
        ax.set_title(name, loc='left', fontsize=20, color=INK)
        ax.set_title(f'in kink bin {share:.0%}', loc='right', fontsize=20, color=INK_2)
    axes[-1].set_xlabel('On-chain utilisation minus kink (percentage points); shaded = kink bin (±2.5)')
    fig.suptitle("Paper's three periods: utilisation is not concentrated at the kink (0 of 3)",
                 x=0.01, ha='left', fontsize=24)
    fig.text(0.01, 0.005, 'Hourly on-chain samples; pre-specified test in analysis_plans/kink_clustering_criterion.md. '
             'Bins of 5 pp as in the test; values beyond the axis are placed in the end bins.', fontsize=14, color=INK_2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    path = f'{OUT_DIR}/utilisation_paper_periods.png'
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for p in (rate_minus_kink(), utilisation_periods()):
        print('Saved', p)


if __name__ == '__main__':
    main()
