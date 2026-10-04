"""
EXPLORATORY (post hoc) check, not part of the pre-specified regime 1 analysis.

Question: the observed cDAI borrow rate in data/compound/cdai.pkl is almost
constant (about 4.24%) from 16 to 20 December 2019, does not respond to
utilisation, and shows no change at either 2019-12-17 (the authors' regime
boundary) or 2019-12-20 (the on-chain model and implementation upgrade). The
authors' regime 0 parameters predict about 3.06% for the same period.

Three sources therefore disagree: the authors' parameter table, the observed
rate series (from the now-closed Compound API), and our reading of the event
log. The blockchain state itself is the ground truth, so this script queries it
directly at historical blocks:

  1. cDAI.borrowRatePerBlock() at selected times, compared with the observed
     series and with the authors' model.
  2. The parameters stored in each interest-rate-model contract the cDAI
     market used, compared with the authors' parameter table.

Requires an archive-capable RPC endpoint in ETH_RPC_URL (Alchemy's free plan
serves historical state). Run from the repository root:
    python scripts/exploratory_onchain_check.py
"""

import gzip
import json
import os
import sys

import numpy as np
import pandas as pd
import requests
from web3 import Web3

import regime1_analysis as a

OUT_PATH = 'results/exploratory/onchain_rate_check.json'
BLOCKS_PER_YEAR = 2102400

CHECK_TIMES = [
    ('regime 0', '2019-11-26 12:00'), ('regime 0', '2019-12-05 12:00'),
    ('regime 0', '2019-12-16 12:00'), ('authors regime 1, before on-chain switch', '2019-12-18 12:00'),
    ('after on-chain switch', '2019-12-21 12:00'), ('regime 2', '2020-01-15 12:00'),
    ('regime 3', '2020-01-30 12:00'), ('regime 4', '2020-02-06 12:00'),
    ('regime 8', '2020-04-10 12:00'), ('regime 10', '2020-05-01 12:00'),
]

# Interest-rate-model contracts used by cDAI, from NewMarketInterestRateModel events,
# with a block inside the period each was in use.
MODELS = [
    ('0x5562024784cc914069d67D89a28e3201bF7b57E7', 9_100_000, 'in use 2019-11-23 to 2019-12-20'),
    ('0xec163986cC9a6593D6AdDcBFf5509430D348030F', 9_500_000, 'in use 2019-12-20 to 2020-05-02'),
    ('0x000000007675b5E1dA008f037A0800B309e0C493', 10_100_000, 'in use 2020-05-02 to 2020-07-28'),
]
MODEL_GETTERS = ['baseRatePerBlock()', 'multiplierPerBlock()', 'jumpMultiplierPerBlock()', 'kink()']


def selector(signature):
    return Web3.keccak(text=signature)[:4].hex().removeprefix('0x')


def eth_call(url, to, signature, block):
    payload = {'jsonrpc': '2.0', 'id': 1, 'method': 'eth_call',
               'params': [{'to': to, 'data': '0x' + selector(signature)}, hex(block)]}
    reply = requests.post(url, json=payload, timeout=60).json()
    if 'error' in reply:
        return None, reply['error'].get('message')
    raw = reply.get('result', '0x')
    return (int(raw, 16) if raw not in ('0x', None) else None), None


def time_to_block(times):
    table = pd.read_csv('data/derived/eth_block_times_sampled.csv')
    # Seconds since the epoch, independent of the datetime resolution pandas chooses.
    ts = (pd.to_datetime(times) - pd.Timestamp('1970-01-01')) // pd.Timedelta(seconds=1)
    return np.interp(ts, table['timestamp'], table['block_number']).round().astype(int)


def cdai_address():
    with gzip.open('data/compound/events/cdai.jsonl.gz') as f:
        for line in f:
            e = json.loads(line)
            if 'event' in e:
                return Web3.to_checksum_address(e['address'])


def main():
    url = os.environ.get('ETH_RPC_URL')
    if not url:
        sys.exit('Set ETH_RPC_URL first.')
    cdai = cdai_address()
    print(f'cDAI address: {cdai}\n')

    hourly = a.load_hourly(a.DATA_PATH)
    regimes = a.assign_regimes(hourly.index, hourly.index.max())
    blocks = time_to_block([t for _, t in CHECK_TIMES])

    rate_rows = []
    print('1. Borrow rate (annual %): on-chain vs observed series vs authors\' model')
    print(f"{'time':17s} {'block':>9s} {'on-chain':>9s} {'observed':>9s} {'authors':>9s}  note")
    for (note, t), block in zip(CHECK_TIMES, blocks):
        value, err = eth_call(url, cdai, 'borrowRatePerBlock()', int(block))
        onchain = value * BLOCKS_PER_YEAR / 1e18 * 100 if value is not None else float('nan')
        ts = pd.Timestamp(t).floor('h')
        observed = model = float('nan')
        if ts in hourly.index:
            observed = hourly.loc[ts, 'borrow_rates'] * 100
            r = regimes.loc[ts]
            if not np.isnan(r):
                model = a.model_borrow_apr(hourly.loc[ts, 'utilization_ratio'], a.params_for(int(r))) * 100
        print(f'{t:17s} {int(block):9d} {onchain:9.3f} {observed:9.3f} {model:9.3f}  {note}'
              + (f'  [error: {err}]' if err else ''))
        rate_rows.append({'time': t, 'block': int(block), 'note': note, 'onchain_pct': onchain,
                          'observed_pct': observed, 'authors_model_pct': model, 'error': err})

    print('\n2. Parameters stored in each interest-rate-model contract (per block, scaled by 1e18)')
    model_rows = []
    for address, block, note in MODELS:
        values = {}
        for getter in MODEL_GETTERS:
            value, err = eth_call(url, Web3.to_checksum_address(address), getter, block)
            values[getter] = value if value is not None else f'n/a ({err})'
        print(f'{address} at block {block} ({note})')
        for k, v in values.items():
            print(f'    {k:26s} {v}')
        model_rows.append({'address': address, 'block': block, 'note': note, 'values': values})

    print('\nAuthors\' parameter table, for comparison:')
    for num, start in a.regime_starts():
        p = a.params_for(num)
        print(f"  regime {num:2d} from {start}  model={p['model']:9s} base={p['base_rate_per_block']} "
              f"multiplier={p['multiplier_per_block']} jump_mult={p.get('jump_multiplier_per_block')} "
              f"jump={p.get('jump')} kink={p['kink']}")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump({'status': 'exploratory, post hoc', 'cdai': cdai, 'rates': rate_rows,
                   'models': model_rows}, f, indent=2, default=str)
    print(f'\nSaved {OUT_PATH}')


if __name__ == '__main__':
    main()
