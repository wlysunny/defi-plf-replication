"""Appendix figures for the final report.

Usage, from the repository root:  python scripts/make_appendix_figures.py

Writes
  figures/appx_api_gap.pdf      median gap between the API series and the chain, per parameter regime,
                                with the API rate read as stored and converted to a simple rate
                                (from results/exploratory/apy_check.json, written by exploratory_apy_check.py)
  figures/appx_cdai_periods.pdf utilisation minus kink in the six new cDAI periods (data/onchain/cdai_panel.csv),
                                same bins as the pre-specified test
  figures/appx_confusion.pdf    researcher vs model labels before arbitration, for the three codebook labels
  figures/appx_concentration.pdf  the paper's Figure 6 at the paper's date: balances computed by the authors'
                                notebook cells, run unchanged through scripts/reproduce_concentration.py, with
                                events to the end of 4 June 2020; only the plotting is ours
and prints the numbers needed to check each figure against the report.
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import matplotlib.ticker as mticker

from make_report_figures import BIN, FULL_WIDTH, STYLE, kink_bin_edges, load_cdai

# The appendix figures need no colour: greys, marker shapes and fills carry every distinction.
C_API, C_CHAIN = '0.6', 'k'                 # appendix C: API rate as stored / converted to a simple rate
C_BIN, C_KINKBIN = '#B8C4D1', '#0072B2'     # appendix D: same colours as Figure 1

COLUMN = 3.03                      # inches: one ACL column (7.7 cm), so figures are included at 100%
# Fixed plot-area margins (inches) for every single-column figure, so that axes line up exactly when
# figures are stacked in a column. Figures are saved without automatic cropping for the same reason.
AX_LEFT, AX_RIGHT, YLABEL_X = 0.62, 0.10, 0.04


def column_layout(fig, top, bottom, ylabel=None, xlabel=None, hspace=None, wspace=None):
    """Place the plot area at fixed distances (inches) from the figure edges; add shared axis titles."""
    w, h = fig.get_size_inches()
    fig.subplots_adjust(left=AX_LEFT / w, right=1 - AX_RIGHT / w, top=1 - top / h, bottom=bottom / h,
                        hspace=hspace, wspace=wspace)
    mid_y, mid_x = (1 - top / h + bottom / h) / 2, (AX_LEFT / w + 1 - AX_RIGHT / w) / 2
    if ylabel:   # on the middle axis of the first column, placed by matplotlib just left of its tick labels
        first = sorted([a for a in fig.axes if abs(a.get_position().x0 - AX_LEFT / w) < 1e-6],
                       key=lambda a: a.get_position().y0)
        first[len(first) // 2].set_ylabel(ylabel, labelpad=3)
    if xlabel:
        fig.text(mid_x, 0.03 / h, xlabel, va='bottom', ha='center', fontsize=7.5)
NEW_PERIODS = [                    # Table 5, "cDAI, new periods"; end exclusive
    ('May-Dec 2020', '2020-05-01', '2021-01-01'),
    ('2021', '2021-01-01', '2022-01-01'),
    ('2022', '2022-01-01', '2023-01-01'),
    ('2023', '2023-01-01', '2024-01-01'),
    ('2024', '2024-01-01', '2025-01-01'),
    ('Jan-Nov 2025', '2025-01-01', '2025-12-01'),
]
CODEBOOK = {
    'rationale': ['LIQUIDITY_BUFFER', 'CAPITAL_EFFICIENCY', 'RATE_STABILITY', 'ALIGNMENT', 'OTHER', 'NOT_STATED'],
    'kink_framing': ['SETTLE_AT', 'KEEP_BELOW', 'PARAMETER_ONLY'],
    'temporary': ['yes', 'no'],
}


def api_gap():
    j = json.load(open('results/exploratory/apy_check.json'))
    r = pd.DataFrame(j['regimes']).sort_values('regime')
    r = r[r.n > 0]
    fig, ax = plt.subplots(figsize=(COLUMN, 2.3))
    x = np.arange(len(r))
    for xi, a, b in zip(x, r.borrow_gap_pp_raw, r.borrow_gap_pp_apy_N):
        if abs(np.log10(b) - np.log10(a)) > 0.08:        # arrow: effect of converting to a simple rate
            ax.annotate('', xy=(xi, b), xytext=(xi, a), zorder=2,
                        arrowprops=dict(arrowstyle='-|>', color='0.6', lw=0.8, mutation_scale=7,
                                        shrinkA=3, shrinkB=3))
    ax.scatter(x, r.borrow_gap_pp_raw, s=16, color=C_API, label='API rate as stored', zorder=3)
    ax.scatter(x, r.borrow_gap_pp_apy_N, s=16, color=C_CHAIN, marker='D', label='converted to simple rate',
               zorder=3)
    ax.axhline(0.25, color='k', ls=':', lw=0.7, zorder=1)
    ax.set_yscale('log')
    lo = min(r.borrow_gap_pp_raw.min(), r.borrow_gap_pp_apy_N.min())
    ax.set_ylim(lo / 2, max(r.borrow_gap_pp_raw.max(), r.borrow_gap_pp_apy_N.max()) * 2)
    ax.yaxis.set_major_locator(mticker.FixedLocator([0.001, 0.01, 0.1, 1, 10]))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:g}'))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
    ax.text(-0.45, 0.27, '0.25 pp', va='bottom', ha='left', fontsize=6.5)
    ax.set_xticks(x, [str(v) for v in r.regime])
    ax.set_xlim(-0.6, len(r) - 0.4)

    ax.grid(axis='y', color='0.92', lw=0.5, zorder=0)
    ax.legend(frameon=False, loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2, handletextpad=0.2,
              columnspacing=0.6, fontsize=6.5)
    column_layout(fig, top=0.30, bottom=0.40, ylabel='Median |API \u2212 chain| (pp)',
                  xlabel="Parameter regime (authors' numbering)")
    fig.savefig('figures/appx_api_gap.pdf')
    plt.close(fig)
    print(f"API gap: regimes={len(r)}, above 0.25 pp as stored={int((r.borrow_gap_pp_raw > 0.25).sum())}, "
          f"above 0.25 pp converted={int((r.borrow_gap_pp_apy_N > 0.25).sum())}")
    print(r[['regime', 'n', 'borrow_gap_pp_raw', 'borrow_gap_pp_apy_N']].round(3).to_string(index=False))


def cdai_periods():
    d = load_cdai('data/onchain/cdai_panel.csv').dropna(subset=['util', 'kink'])
    fig, axes = plt.subplots(3, 2, figsize=(COLUMN, 3.4), sharex=True, sharey=True)
    print('cDAI new periods (compare kink-bin shares with Table 5):')
    for ax, (title, start, end) in zip(axes.flat, NEW_PERIODS):
        p = d[(d.time >= start) & (d.time < end)]
        dist = p.util - p.kink
        _, _, bars = ax.hist(dist, bins=kink_bin_edges(dist), color=C_BIN, edgecolor='white', linewidth=0.6,
                             weights=np.ones(len(dist)) / len(dist), zorder=2)
        for bar in bars:
            if abs(bar.get_x() + bar.get_width() / 2) < 1e-9:
                bar.set_facecolor(C_KINKBIN)
        ax.axvline(0, color='0.3', ls=':', lw=0.7, zorder=3)
        ax.grid(axis='y', color='0.92', lw=0.5, zorder=0)
        share = np.mean(np.abs(dist) <= BIN / 2)
        ax.set_title(f'{title}: {share:.0%}', loc='left')
        ax.set_xlim(-45, 20)
        print(f'  {title}: n={len(p)}, kinks={sorted(p.kink.unique())}, kink-bin share={share:.2f}, '
              f'median distance={dist.median():+.1f} pp')
    axes[0, 0].yaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
    axes[0, 0].set_xticks([-40, -20, 0, 20])
    column_layout(fig, top=0.18, bottom=0.40, ylabel='Share of days', xlabel='Utilisation minus kink (pp)',
                  hspace=0.55, wspace=0.12)
    fig.savefig('figures/appx_cdai_periods.pdf')
    plt.close(fig)


def concentration():
    import reproduce_concentration as rc          # executes the authors' notebook cells unchanged
    ns = rc.notebook_namespace()
    events = ns['load_events']()
    bt = pd.read_csv(rc.BLOCK_TIMES).sort_values('block_number')
    ts = np.interp(np.array([int(e['blockNumber']) for e in events]), bt['block_number'], bt['timestamp'])
    ns['events'] = [e for e, t in zip(events, ts) if t < rc.CUTOFF.timestamp()]   # rule of rc.main()
    balances = ns['compute_balances']()
    names = {'cdai': 'DAI', 'ceth': 'ETH', 'cusdc': 'USDC'}
    fig, axes = plt.subplots(3, 1, figsize=(COLUMN, 4.6), sharex=True)
    print('Concentration, events to 2020-06-04 (compare with results/reproduction_concentration.csv):')
    for ax, (market, paper) in zip(axes, rc.PAPER.items()):
        pos = np.sort(np.array([v for _, v in balances[market] if v > 0], dtype=float))[::-1]
        cum = np.cumsum(pos) / pos.sum() * 100
        rank = np.arange(1, len(pos) + 1)
        ax.plot(rank, cum, color='k', lw=1.0)
        top = cum[rc.TOP_N - 1]
        ax.plot([rc.TOP_N], [top], 'o', mfc='white', mec='k', mew=0.8, ms=4)
        ax.annotate(f'top {rc.TOP_N}: {top:.1f}%\n(paper {paper:.1f}%)', (rc.TOP_N, top), xytext=(12, -22),
                    textcoords='offset points', fontsize=6.5)
        ax.set_xscale('log')
        ax.set_ylim(0, 102)
        ax.set_title(f'{names[market]} ({len(pos):,} accounts)', loc='left')
        ax.grid(axis='y', color='0.92', lw=0.5, zorder=0)
        print(f'  {market}: top {rc.TOP_N} {top:.2f}% (paper {paper}), accounts with positive balance {len(pos)}')
    column_layout(fig, top=0.18, bottom=0.40, ylabel='Cumulative share of funds (%)',
                  xlabel='Accounts, largest first (log scale)', hspace=0.45)
    fig.savefig('figures/appx_concentration.pdf')
    plt.close(fig)


def confusion():
    res = pd.read_csv('annotation/researcher_labels.csv', dtype=str).set_index('action')
    mod = pd.read_csv('annotation/llm_labels.csv', dtype=str).set_index('action').reindex(res.index)
    extra = sorted(set().union(*[set(mod[l].dropna()) - set(c) for l, c in CODEBOOK.items()]) | {'INVALID'})
    fig, axes = plt.subplots(3, 1, figsize=(COLUMN, 5.8),
                             gridspec_kw={'height_ratios': [len(c) + 2.2 for c in CODEBOOK.values()]})
    print('Confusion (researcher rows, model columns), before arbitration:')
    for ax, (lab, cats) in zip(axes, CODEBOOK.items()):
        r, m = res[lab].fillna('INVALID'), mod[lab].fillna('INVALID')
        rows = list(cats)                                       # the full codebook, used or not
        cols = rows + extra                                      # INVALID: model output outside the codebook
        mat = pd.crosstab(r, m).reindex(index=rows, columns=cols, fill_value=0)
        cmap = plt.get_cmap('Blues').copy()
        cmap.set_bad('white')                                    # empty cells stay white
        ax.imshow(np.ma.masked_equal(mat.values, 0), cmap=cmap, vmin=0, vmax=max(1, mat.values.max()) * 1.15,
                  aspect='equal')
        for (i, j), v in np.ndenumerate(mat.values):
            if v:
                ax.text(j, i, str(v), ha='center', va='center', fontsize=7,
                        color='white' if v > mat.values.max() / 2 else 'k')
        ax.set_xticks(range(len(cols)), [c.replace('_', '_\n', 1) for c in cols], fontsize=5.5, rotation=90)
        ax.set_ylabel('Researcher', fontsize=6.5)
        ax.set_yticks(range(len(rows)), rows, fontsize=5.5)
        ax.tick_params(length=0)
        ax.set_title(f'{lab}\n{int((r == m).sum())} of {len(r)} agree', loc='left')
        ax.spines[:].set_visible(True)
        print(f'  {lab}: agreement {int((r == m).sum())}/{len(r)}\n{mat.to_string()}')
    axes[-1].set_xlabel('Model (Qwen2.5-7B-Instruct)', fontsize=6.5)
    fig.tight_layout(h_pad=0.8)
    fig.savefig('figures/appx_confusion.pdf', bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


if __name__ == '__main__':
    os.makedirs('figures', exist_ok=True)
    plt.rcParams.update(STYLE)
    api_gap()
    cdai_periods()
    confusion()
    concentration()
    print('Saved figures/appx_api_gap.pdf, figures/appx_cdai_periods.pdf, figures/appx_confusion.pdf, '
          'figures/appx_concentration.pdf')
