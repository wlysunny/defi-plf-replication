"""
Annotate the authors' eleven cDAI interest-rate regimes with facts from the
on-chain panels and the repository's event log. Rules, written before this
script was run: analysis_plans/regime_annotation_rules.md.

Outputs:
  results/regime_annotation.csv          one row per regime (the annotation table)
  results/regime_onchain_changes.csv     every on-chain change detected in the panels
  results/regime_annotation.json         both, with the thresholds used

Run from the repository root:
    python annotate_regimes.py
"""

import gzip
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath('.'))
from simulator.engine.dai_rate_params import PARAM_REGIMES, PARAM_REGIME_NUMS  # noqa: E402

PANELS = ['data/onchain/cdai_panel.csv', 'data/onchain/cdai_panel_dense_2020.csv']
API_PATH = 'data/compound/cdai.pkl'
EVENTS_PATH = 'data/compound/events/cdai.jsonl.gz'
BLOCK_TIMES_PATH = 'data/derived/eth_block_times_sampled.csv'
OUT_DIR = 'results'

BLOCKS_PER_YEAR = 2_102_400
NEAR_DAYS = 7
RELIABLE_PP = 0.25

MODEL_FIELDS = {          # authors' key -> panel column
    'base_rate_per_block': 'irm_baseRatePerBlock',
    'multiplier_per_block': 'irm_multiplierPerBlock',
    'jump_multiplier_per_block': 'irm_jumpMultiplierPerBlock',
    'kink': 'irm_kink',
}
RESERVE_FACTOR = ('reserve_factor', 'cdai_reserveFactorMantissa')


def load_panels():
    frames = [pd.read_csv(p, dtype=str) for p in PANELS]
    df = pd.concat(frames).fillna('').drop_duplicates('block')    # blank getters read as NaN, and NaN != NaN
    df['block'] = df['block'].astype(int)
    df = df.sort_values('block').reset_index(drop=True)
    df['utc'] = pd.to_datetime(df['utc'])
    df['rate_pct'] = df['cdai_borrowRatePerBlock'].astype(float) * BLOCKS_PER_YEAR / 1e18 * 100
    return df


def detect_changes(df):
    model_cols = ['cdai_interestRateModel'] + list(MODEL_FIELDS.values())
    rows = []
    for i in range(1, len(df)):
        prev, cur = df.iloc[i - 1], df.iloc[i]
        types = []
        if prev['cdai_interestRateModel'] != cur['cdai_interestRateModel']:
            types.append('new model contract')
        elif any(prev[c] != cur[c] for c in model_cols[1:]):
            types.append('in-model parameter update')
        if prev[RESERVE_FACTOR[1]] != cur[RESERVE_FACTOR[1]]:
            types.append('reserve factor change')
        if types:
            rows.append({'after_block': int(prev['block']), 'by_block': int(cur['block']),
                         'after_utc': prev['utc'], 'by_utc': cur['utc'], 'type': '; '.join(types),
                         'model_before': prev['cdai_interestRateModel'], 'model_after': cur['cdai_interestRateModel']})
    return pd.DataFrame(rows)


def time_to_block(times):
    table = pd.read_csv(BLOCK_TIMES_PATH)
    ts = (pd.to_datetime(pd.Series(times)) - pd.Timestamp('1970-01-01')) // pd.Timedelta(seconds=1)
    return np.interp(ts, table['timestamp'], table['block_number']).round().astype(int)


def liquidation_blocks():
    blocks = []
    with gzip.open(EVENTS_PATH, 'rt') as f:
        for line in f:
            e = json.loads(line)
            if e.get('event') == 'LiquidateBorrow':
                b = e['blockNumber']
                blocks.append(int(b, 16) if isinstance(b, str) and b.startswith('0x') else int(b))
    return np.array(sorted(blocks))


def match_change(start, changes):
    inside = changes[(changes['after_utc'] < start) & (changes['by_utc'] >= start)]
    if len(inside):
        c = inside.iloc[0]
        return 'consistent', 0.0, c
    mid = changes['after_utc'] + (changes['by_utc'] - changes['after_utc']) / 2
    lag = (mid - start) / pd.Timedelta(days=1)
    near = lag[lag.abs() <= NEAR_DAYS]
    if len(near):
        j = near.abs().idxmin()
        return f'differs by {lag[j]:+.1f} days', float(lag[j]), changes.loc[j]
    return f'no on-chain change within {NEAR_DAYS} days', None, None


def main():
    df = load_panels()
    changes = detect_changes(df)
    api = pd.read_pickle(API_PATH)[['borrow_rates']].resample('h').mean() * 100
    liq = liquidation_blocks()

    starts = sorted((int(k), pd.Timestamp(v)) for k, v in PARAM_REGIME_NUMS.items())
    data_end = api.index.max()
    matched_changes = set()
    rows = []
    for idx, (num, start) in enumerate(starts):
        end = starts[idx + 1][1] if idx + 1 < len(starts) else data_end
        params = PARAM_REGIMES[PARAM_REGIME_NUMS[str(num)]]
        row = {'regime': num, 'author_start': start, 'end': end}

        # 1-2. matching change and its source
        if num == 0:
            row.update({'onchain_match': 'not applicable (market launch)', 'lag_days': None,
                        'source': 'not applicable'})
            excl_until = start
        else:
            label, lag, c = match_change(start, changes)
            row.update({'onchain_match': label, 'lag_days': lag,
                        'source': c['type'] if c is not None else 'not determined'})
            if c is not None:
                matched_changes.add(int(c['by_block']))
            excl_until = max(start, c['by_utc']) if c is not None else start

        # 3. parameters match the chain
        inside = df[(df['utc'] >= excl_until) & (df['utc'] < end)]
        compared, mismatched = [], []
        for key, col in list(MODEL_FIELDS.items()) + [RESERVE_FACTOR]:
            if key not in params:
                continue
            vals = inside[col].replace('', np.nan).dropna()
            if vals.empty:
                continue
            compared.append(key)
            if not (vals.astype(int) == int(params[key])).all():
                mismatched.append(key)
        row.update({'n_onchain_samples': int(len(inside)),
                    'params_compared': ', '.join(compared),
                    'params_match': 'yes' if compared and not mismatched else
                                    ('no: ' + ', '.join(mismatched) if mismatched else 'not compared')})

        # 4. reliability of the observed series
        s = inside.set_index('utc')['rate_pct']
        nearest = api['borrow_rates'].reindex(s.index.floor('h'))
        gap = (nearest.to_numpy() - s.to_numpy())
        gap = np.abs(gap[~np.isnan(gap)])
        med = float(np.median(gap)) if len(gap) else None
        row.update({'n_rate_comparisons': int(len(gap)), 'median_abs_rate_gap_pp': med,
                    'observed_series': ('reliable' if med is not None and med <= RELIABLE_PP else
                                        'unreliable' if med is not None else 'not assessed')})

        # 5. liquidations
        b0, b1 = time_to_block([start, end])
        row['liquidations'] = int(((liq >= b0) & (liq < b1)).sum())
        rows.append(row)

    table = pd.DataFrame(rows)
    in_sample = changes[(changes['by_utc'] >= starts[0][1]) & (changes['after_utc'] < data_end)].copy()
    in_sample['matches_author_regime'] = in_sample['by_block'].isin(matched_changes)

    os.makedirs(OUT_DIR, exist_ok=True)
    table.to_csv(f'{OUT_DIR}/regime_annotation.csv', index=False)
    in_sample.to_csv(f'{OUT_DIR}/regime_onchain_changes.csv', index=False)
    with open(f'{OUT_DIR}/regime_annotation.json', 'w') as f:
        json.dump({'rules': 'analysis_plans/regime_annotation_rules.md',
                   'thresholds': {'near_days': NEAR_DAYS, 'reliable_pp': RELIABLE_PP},
                   'regimes': table.to_dict('records'),
                   'onchain_changes_in_sample': in_sample.to_dict('records')}, f, indent=2, default=str)

    with pd.option_context('display.width', 200, 'display.max_columns', 20):
        print(table[['regime', 'author_start', 'onchain_match', 'source', 'params_match',
                     'median_abs_rate_gap_pp', 'observed_series', 'liquidations']].to_string(index=False))
    unmatched = in_sample[~in_sample['matches_author_regime']]
    print(f'\nOn-chain changes in the sample period: {len(in_sample)}; '
          f'not matching any author regime: {len(unmatched)}')
    if len(unmatched):
        print(unmatched[['after_utc', 'by_utc', 'type']].to_string(index=False))
    print(f'Total liquidations assigned: {table["liquidations"].sum()} of {len(liq)} events')
    print(f'\nSaved {OUT_DIR}/regime_annotation.csv, regime_onchain_changes.csv, regime_annotation.json')


if __name__ == '__main__':
    main()
