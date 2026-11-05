"""Figures and data extract for the final report (main body).

Usage, from the repository root:  python scripts/make_report_figures.py

Writes
  figures/report_fig1_kink.pdf    the paper's three kink periods (early 2020), on-chain and API data
  figures/report_fig_aave.pdf     Aave V3 reserves 2023-2025: utilisation, kink and governance actions
and prints every number quoted in the captions, plus the rows used for the data-extract figure.

Conventions (as in the analysis scripts)
  cDAI utilisation follows the cToken formula, borrows / (cash + borrows - reserves). Per-block rates
  and model parameters (scaled by 1e18) are annualised as simple rates with the 2,102,400 blocks per
  year assumed by the Compound rate models of 2019-2020. The API series (data/compound/cdai.pkl) is the
  one the paper used; its rates are plotted as stored (compounded), as in the paper's comparison.
  Aave V3 rows are built by aave_kink_analysis.load(), unchanged; reserve-periods whose subgraph
  utilisation failed validation show the weekly on-chain values used in the test instead (line with markers).
  The utilisation axis starts at 20%; drawn values below it are marked at the lower edge, and their number is
  printed. Governance actions are drawn 3.5 pp above the new kink so that the kink line does not hide them.
"""
import json
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLOCKS_PER_YEAR = 2_102_400
SCALE = 1e18
BIN = 5.0                                # pp, as in analysis_plans/kink_clustering_criterion.md
NEAR = 0.25                              # pp, rate within this distance of the kink rate in force
PAPER_PERIODS = [                        # the paper's three parameter periods; end exclusive
    ('Period 1: 21 Feb - 13 Mar 2020', '2020-02-21', '2020-03-14'),
    ('Period 2: 14 Mar - 5 Apr 2020', '2020-03-14', '2020-04-06'),
    ('Period 3: 6 - 21 Apr 2020', '2020-04-06', '2020-04-22'),
]
# One style for every report figure: colour-blind-safe (Okabe-Ito), serif text matching the ACL template.
C_CHAIN, C_API, C_HIST, C_MODEL = '#D55E00', '0.55', '#0072B2', 'k'
C_BIN, C_KINKBIN = '#B8C4D1', '#0072B2'     # histogram: other bins muted, the kink bin emphasised
NOTE_BOX = dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='none', alpha=0.85)
FRAMING_COLOURS = {'SETTLE_AT': '#009E73', 'KEEP_BELOW': '#CC79A7', 'PARAMETER_ONLY': '#E69F00'}
STYLE = {'font.size': 7.5, 'font.family': 'serif', 'axes.titlesize': 7.5, 'axes.labelsize': 7.5,
         'legend.fontsize': 7, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
         'axes.spines.top': False, 'axes.spines.right': False, 'pdf.fonttype': 42}
FULL_WIDTH = 6.3                         # inches, ACL two-column text width


def load_cdai(path):
    d = pd.read_csv(path, dtype={'cdai_interestRateModel': str})
    d['time'] = pd.to_datetime(d['utc'])
    num = ['cdai_borrowRatePerBlock', 'cdai_getCash', 'cdai_totalBorrows', 'cdai_totalReserves',
           'irm_baseRatePerBlock', 'irm_multiplierPerBlock', 'irm_jumpMultiplierPerBlock', 'irm_kink']
    for c in num:
        d[c] = pd.to_numeric(d[c], errors='coerce').astype(float)
    denom = d.cdai_getCash + d.cdai_totalBorrows - d.cdai_totalReserves
    d['util'] = np.where(denom > 0, d.cdai_totalBorrows / denom, np.nan) * 100
    d['borrow_apr'] = d.cdai_borrowRatePerBlock * BLOCKS_PER_YEAR / SCALE * 100
    d['kink'] = d.irm_kink / SCALE * 100
    return d


def model_apr(u, base, mult, jump, kink):
    """Annual simple borrow rate (%) of a jump-rate model at utilisation u (%)."""
    u, kink = np.asarray(u) / 100, kink / 100
    per_block = np.where(u <= kink, base + u * mult, base + kink * mult + (u - kink) * jump)
    return per_block / SCALE * BLOCKS_PER_YEAR * 100


def load_api():
    api = pd.read_pickle('data/compound/cdai.pkl')[['borrow_rates', 'utilization_ratio']]
    api = api.resample('h').mean().dropna()
    if api.index.tz is not None:
        api.index = api.index.tz_convert('UTC').tz_localize(None)
    scale = 100 if api['utilization_ratio'].max() <= 1.5 else 1      # stored as a fraction or in %
    return pd.DataFrame({'util': api['utilization_ratio'] * scale, 'rate': api['borrow_rates'] * 100})


def kink_bin_edges(dist):
    lo = np.floor((dist.min() + BIN / 2) / BIN) * BIN - BIN / 2     # bins centred on the kink
    hi = np.ceil((dist.max() - BIN / 2) / BIN) * BIN + BIN / 2
    return np.arange(lo, hi + BIN / 2, BIN)


def figure1():
    params = ['irm_baseRatePerBlock', 'irm_multiplierPerBlock', 'irm_jumpMultiplierPerBlock', 'irm_kink']
    d = load_cdai('data/onchain/cdai_panel_dense_2020.csv').dropna(subset=['util'])
    api = load_api()
    plt.rcParams.update(STYLE)
    fig, axes = plt.subplots(2, 3, figsize=(FULL_WIDTH, 3.4), gridspec_kw={'height_ratios': [1.25, 1]})
    print('Figure 1 (on-chain: data/onchain/cdai_panel_dense_2020.csv; API: data/compound/cdai.pkl, hourly means)')
    for j, (title, start, end) in enumerate(PAPER_PERIODS):
        p = d[(d.time >= start) & (d.time < end)]
        if len(p) == 0:
            raise SystemExit(f'No on-chain samples in {title}; check the coverage of the dense panel.')
        if not np.isfinite(p[params].to_numpy()).all():
            raise SystemExit(f'Missing or non-finite rate-model parameters in {title}.')
        q = api[(api.index >= start) & (api.index < end)]
        # The DAI model of early 2020 updates its parameters within the same contract, so each sample
        # is compared with the model in force at its own block.
        kink_rate = model_apr(p.kink.values, p.irm_baseRatePerBlock.values, p.irm_multiplierPerBlock.values,
                              p.irm_jumpMultiplierPerBlock.values, p.kink.values)
        counts = p[params].apply(tuple, axis=1).value_counts()
        a, b = axes[0, j], axes[1, j]
        u = np.linspace(0, 100, 501)
        for k_, (pset, n_set) in enumerate(counts.items()):
            curve = model_apr(u, *pset[:3], pset[3] / SCALE * 100)
            a.plot(u, curve, color=C_MODEL, lw=0.9 if k_ == 0 else 0.6, ls='-' if k_ == 0 else '--', zorder=1,
                   label='rate model' if k_ == 0 else ('other parameter set in force' if k_ == 1 else None))
        a.scatter(q.util, q.rate, s=2.5, color=C_API, alpha=0.6, lw=0, zorder=2, label="API series (paper's data)")
        a.scatter(p.util, p.borrow_apr, s=2.5, color=C_CHAIN, alpha=0.7, lw=0, zorder=3, label='on-chain')
        kink = pset_kink = counts.index[0][3] / SCALE * 100
        a.axvline(pset_kink, color='0.3', ls=':', lw=0.7)
        xs = pd.concat([p.util, q.util])
        a.set_xlim(max(0, np.floor(xs.min() / 5) * 5 - 2), 101)
        ys = pd.concat([p.borrow_apr, q.rate])
        a.set_ylim(0, ys.quantile(0.995) * 1.15)
        a.set_title(f'{title}\n(n = {len(p)} on-chain, {len(q)} API)', loc='left')
        a.set_xlabel('Utilisation (%)')
        near = np.mean(np.abs(p.borrow_apr.values - kink_rate) <= NEAR)
        api_gap = np.nan
        if len(q):
            # both keys at nanosecond resolution: pandas 3 parses the CSV times at microseconds
            left = pd.DataFrame({'t': q.index.astype('datetime64[ns]'), 'rate': q.rate.values})
            right = pd.DataFrame({'t': p.time.astype('datetime64[ns]').values, 'kr': kink_rate})
            qk = pd.merge_asof(left.sort_values('t'), right.sort_values('t'),
                               on='t', direction='nearest', tolerance=pd.Timedelta('2h')).dropna()
            api_gap = np.median(qk.rate - qk.kr) if len(qk) else np.nan
        a.text(0.03, 0.96, f'{near:.0%} within {NEAR} pp\nof the kink rate', transform=a.transAxes,
               va='top', fontsize=6.5, bbox=NOTE_BOX, zorder=5)
        a.grid(axis='y', color='0.9', lw=0.5, zorder=0)
        dist = p.util - p.kink
        edges = kink_bin_edges(dist)
        _, _, bars = b.hist(dist, bins=edges, color=C_BIN, edgecolor='white', linewidth=0.6,
                            weights=np.ones(len(dist)) / len(dist), zorder=2)
        for bar in bars:                            # emphasise the bin centred on the kink
            if abs(bar.get_x() + bar.get_width() / 2) < 1e-9:
                bar.set_facecolor(C_KINKBIN)
        b.axvline(0, color='0.3', ls=':', lw=0.7, zorder=3)
        b.grid(axis='y', color='0.9', lw=0.5, zorder=0)
        b.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
        kink_bin = np.mean(np.abs(dist) <= BIN / 2)
        b.set_title(f'kink bin {kink_bin:.0%}, median {dist.median():+.1f} pp', loc='left', fontsize=7)
        b.set_xlim(min(-45, edges[0]), max(15, edges[-1]))
        b.set_xlabel('Utilisation minus kink (pp)')
        print(f'  {title}: n_chain={len(p)}, n_api={len(q)}, kink={kink:.0f}%, parameter sets={len(counts)}, '
              f'kink rate range={kink_rate.min():.2f}-{kink_rate.max():.2f}%, '
              f'on-chain within {NEAR} pp of kink rate={near:.2f}, kink-bin share={kink_bin:.2f}, '
              f'median utilisation minus kink={dist.median():+.1f} pp, '
              f'median API rate minus kink rate={api_gap:+.2f} pp, '
              f'share at or above 100% utilisation={np.mean(p.util >= 100):.2f}')
    axes[0, 0].set_ylabel('Borrow rate (% p.a.)')
    axes[1, 0].set_ylabel('Share of samples')
    h, l = axes[0, 0].get_legend_handles_labels()
    for ax in axes[0, 1:]:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            if ll not in l:
                h.append(hh), l.append(ll)
    from matplotlib.patches import Patch
    h += [Patch(facecolor=C_KINKBIN), Patch(facecolor=C_BIN)]
    l += ['kink bin (5 pp, centred)', 'other bins']
    fig.legend(h, l, loc='lower center', ncol=3, frameon=False, markerscale=3,
               bbox_to_anchor=(0.5, -0.01), columnspacing=1.5)
    fig.tight_layout(rect=(0, 0.08, 1, 1), h_pad=0.6)
    fig.savefig('figures/report_fig1_kink.pdf', bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


def governance_actions():
    units = [json.loads(line) for line in open('data/governance/units.jsonl', encoding='utf-8')]
    labels = pd.read_csv('annotation/final_labels.csv').set_index('action')
    rows = []
    for u in units:
        new = float(u['kink_change'].split('->')[1].strip().rstrip('%'))
        for sym in [s.strip() for s in u['assets'].split(',')]:
            rows.append({'action': u['action'], 'symbol': sym, 'date': pd.Timestamp(u['effective_date_utc']),
                         'new_kink': new, 'framing': labels.loc[u['action'], 'kink_framing']})
    return pd.DataFrame(rows)


def figure_aave():
    import aave_kink_analysis as aka            # scripts/ is on the path when run as scripts/...
    df = aka.load()
    res = json.load(open(aka.RESULTS_PATH))['results']
    failed = [(r['symbol'], r['period']) for r in res if not r['validation']['passes']]
    acts = governance_actions()
    plt.rcParams.update(STYLE)
    fig, axes = plt.subplots(len(aka.SYMBOLS), 1, figsize=(FULL_WIDTH, 3.6), sharex=True, sharey=True)
    print('Aave figure (aave_kink_analysis.load(); governance: data/governance/units.jsonl, '
          'annotation/final_labels.csv)')
    YMIN = 20                                       # values below are marked at the lower edge, not hidden
    for ax, sym in zip(axes, aka.SYMBOLS):
        weekly = []
        s = df[(df.symbol == sym) & (df.utc >= aka.PERIODS[0][1]) & (df.utc < aka.PERIODS[-1][2])].copy()
        # the kink bin of the test (kink +/- BIN/2), drawn as a band that follows the kink in force
        k = s.dropna(subset=['kink_pct'])
        ax.fill_between(k.utc, k.kink_pct - BIN / 2, k.kink_pct + BIN / 2, step='post', color='0.78',
                        alpha=0.7, lw=0, zorder=1, label=f'kink bin (kink \u00b1{BIN / 2:g} pp)')
        ax.step(k.utc, k.kink_pct, where='post', color='k', lw=0.8, zorder=3, label='kink')
        for label, start, end in aka.PERIODS:
            if any(f == sym and lab.endswith(label) for f, lab in failed):
                # subgraph utilisation failed validation here: weekly on-chain values are drawn instead
                s.loc[(s.utc >= start) & (s.utc < end), 'util_subgraph_pct'] = np.nan
                w = s[(s.utc >= start) & (s.utc < end)].dropna(subset=['util_chain_pct'])
                ax.plot(w.utc, w.util_chain_pct, '-o', ms=1.6, lw=0.6, color=C_HIST, zorder=2,
                        label='weekly, on-chain (where the subgraph failed its check)')
                weekly.append(w[['utc', 'util_chain_pct']].rename(columns={'util_chain_pct': 'u'}))
        ax.plot(s.utc, s.util_subgraph_pct, color=C_HIST, lw=0.6, zorder=2, label='daily, subgraph')
        for _, start, _ in aka.PERIODS[1:]:          # boundaries of the test's three periods
            ax.axvline(pd.Timestamp(start), color='0.6', ls='--', lw=0.5, zorder=0)
        a = acts[acts.symbol == sym]
        for fr, g in a.groupby('framing'):
            ax.scatter(g.date, np.minimum(g.new_kink + 3.5, 99), marker='v', s=18,
                       color=FRAMING_COLOURS.get(fr, '0.3'), edgecolor='k', lw=0.3, zorder=4, label=fr)
        ax.set_ylabel(sym, rotation=0, ha='right', va='center')
        # what is actually drawn: daily subgraph values (after the mask) and the weekly on-chain substitutes
        daily = s.dropna(subset=['util_subgraph_pct'])[['utc', 'util_subgraph_pct']].rename(
            columns={'util_subgraph_pct': 'u'})
        weekly = pd.concat(weekly) if weekly else daily.iloc[0:0]
        low_d, low_w = daily[daily.u < YMIN], weekly[weekly.u < YMIN]
        low_dates = pd.concat([low_d.utc, low_w.utc]).drop_duplicates()
        if len(low_dates):
            ax.scatter(low_dates, np.full(len(low_dates), YMIN + 1.5), marker=7, s=12, color='0.45', zorder=4,
                       clip_on=False, label=f'below {YMIN}% (off scale)')
        print(f'  {sym}: drawn below {YMIN}%: {len(low_d)} of {len(daily)} daily subgraph values, '
              f'{len(low_w)} of {len(weekly)} weekly on-chain values, {len(low_dates)} distinct dates; '
              f'lowest drawn value {pd.concat([daily.u, weekly.u]).min():.1f}%'
              + (f' ({", ".join(sorted(low_dates.dt.strftime("%Y-%m-%d")))})' if 0 < len(low_dates) <= 12 else ''))
        ok = s.dropna(subset=['util_subgraph_pct', 'kink_pct'])
        in_band = np.mean(np.abs(ok.util_subgraph_pct - ok.kink_pct) <= BIN / 2)
        print(f'  {sym}: subgraph days drawn={len(ok)}, kink values={sorted(s.kink_pct.dropna().unique())}, '
              f'actions={len(a)} {a.framing.value_counts().to_dict()}, share of drawn days in kink bin={in_band:.2f}, '
              f'weekly on-chain (subgraph failed check)={[lab for f, lab in failed if f == sym]}')
    axes[0].set_ylim(YMIN, 101)
    axes[0].set_xlim(pd.Timestamp(aka.PERIODS[0][1]), pd.Timestamp(aka.PERIODS[-1][2]))
    for ax in axes:
        ax.grid(axis='y', color='0.92', lw=0.5, zorder=0)
    fig.supylabel('Utilisation (%)', fontsize=7.5, x=0.01)
    handles = {}
    for ax in axes:
        for hh, ll in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(ll, hh)
    names = {'daily, subgraph': 'utilisation, daily (subgraph)',
             'weekly, on-chain (where the subgraph failed its check)': 'utilisation, weekly (on-chain)',
             'kink': 'kink', f'kink bin (kink \u00b1{BIN / 2:g} pp)': f'kink bin (\u00b1{BIN / 2:g} pp)',
             f'below {YMIN}% (off scale)': f'below {YMIN}% (off scale)'}
    order = [l for l in names if l in handles] + [f for f in FRAMING_COLOURS if f in handles]
    fig.legend([handles[l] for l in order], [names.get(l, f'action: {l}') for l in order], loc='upper center',
               ncol=4, frameon=False, bbox_to_anchor=(0.52, 1.0), columnspacing=1.2, handlelength=1.6)
    fig.tight_layout(rect=(0.02, 0, 1, 0.88), h_pad=0.3)
    fig.savefig('figures/report_fig_aave.pdf', bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


def extract():
    d = load_cdai('data/onchain/cdai_panel.csv').dropna(subset=['util'])
    print('Data extract (first sample on or after each date):')
    for day in ['2020-03-12', '2021-06-01', '2023-06-01', '2025-06-01']:
        r = d[d.time >= day].iloc[0]
        print(f"  {int(r.block)} | {r.time:%Y-%m-%d %H:%M} | util {r.util:.1f}% | borrow {r.borrow_apr:.2f}% | "
              f"kink {r.kink:.0f}% | model {str(r.cdai_interestRateModel)[:10]}")


if __name__ == '__main__':
    os.makedirs('figures', exist_ok=True)
    figure1()
    figure_aave()
    extract()
    print('Saved figures/report_fig1_kink.pdf and figures/report_fig_aave.pdf')
