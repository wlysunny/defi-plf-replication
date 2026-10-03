"""
Read, from the blockchain, the interest-rate model in force for each Aave V3
reserve at each daily sample time of the Aave V3 subgraph panel.

Why:
The subgraph keeps only the current interest-rate parameters of each reserve,
but Aave governance changed them several times between 2023 and 2025. Measuring
distance from the kink requires the kink (optimalUsageRatio) that was in force
at each sample, which only the historical chain state records. The method is the
same as for the cDAI panel: eth_call at historical blocks.

The script also records three values that allow the subgraph data to be checked
against the chain on the same days: the Pool's current variable borrow rate, and
the supplies of the reserve's aToken and debt tokens with the underlying balance
held by the aToken (on every VALIDATION_EVERY-th day only, to save requests).

For each reserve and each day at 00:00 UTC (the same grid as the subgraph panel):
  block: the last block at or before that moment, and its timestamp;
  Pool.getReserveData(asset): interestRateStrategyAddress, currentVariableBorrowRate;
  the strategy's optimalUsageRatio, baseVariableBorrowRate, variableRateSlope1,
  variableRateSlope2 (ray, 1e27). Aave V3.0 strategies expose these without
  arguments; V3.1+ strategies (DefaultReserveInterestRateStrategyV2) take the
  reserve address. The version of each strategy contract is detected once.

No summary statistics are printed. Re-running resumes where it stopped.

Usage (from the repository root, archive-capable RPC endpoint required):
    export ETH_RPC_URL="https://eth-mainnet.g.alchemy.com/v2/<key>"
    python collect_aave_v3_rate_params.py
Requires data/aave_v3/aave_v3_reserves.json from
    python collect_aave_v3_subgraph.py --list-reserves
"""

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

from collect_onchain_cdai import rpc_batch, selector, to_int
from collect_aave_v3_subgraph import RESERVES_PATH, sample_times

POOL = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'      # Aave V3 Ethereum Core Pool (proxy)
OUT_PATH = 'data/aave_v3/aave_v3_rate_params_daily.csv'
META_PATH = 'data/aave_v3/aave_v3_rate_params_daily_provenance.json'
BATCH = 10
PAUSE_SECONDS = 0.5
VALIDATION_EVERY = 7             # chain-side validation values on every 7th day

V1_GETTERS = ['OPTIMAL_USAGE_RATIO()', 'getBaseVariableBorrowRate()',
              'getVariableRateSlope1()', 'getVariableRateSlope2()']
V2_GETTERS = ['getOptimalUsageRatio(address)', 'getBaseVariableBorrowRate(address)',
              'getVariableRateSlope1(address)', 'getVariableRateSlope2(address)']
PARAM_NAMES = ['optimalUsageRatio', 'baseVariableBorrowRate', 'variableRateSlope1', 'variableRateSlope2']
COLUMNS = (['symbol', 'asset', 'sample_utc', 'block', 'block_timestamp', 'strategy', 'strategy_version',
            'pool_currentVariableBorrowRate']
           + ['irm_' + p for p in PARAM_NAMES]
           + ['val_aToken_totalSupply', 'val_variableDebt_totalSupply', 'val_stableDebt_totalSupply',
              'val_underlying_balanceOf_aToken'])


def pad_address(address):
    return address.lower().removeprefix('0x').rjust(64, '0')


def word(hex_data, i):
    data = hex_data.removeprefix('0x')
    return data[64 * i: 64 * (i + 1)]


def address_from_word(w):
    return '0x' + w[-40:]


def chunks(items, n):
    for i in range(0, len(items), n):
        yield items[i:i + n]


def batched(url, calls):
    out = []
    for chunk in chunks(calls, BATCH):
        out.extend(rpc_batch(url, chunk))
        time.sleep(PAUSE_SECONDS)
    return out


def timestamps(url, blocks):
    blocks = sorted(set(blocks))
    res = batched(url, [('eth_getBlockByNumber', [hex(b), False]) for b in blocks])
    return {b: int(r['timestamp'], 16) for b, r in zip(blocks, res)}


def blocks_at_or_before(url, targets):
    """For each target timestamp, the last block whose timestamp is <= target."""
    (latest,) = rpc_batch(url, [('eth_blockNumber', [])])
    latest = int(latest, 16)
    latest_ts = timestamps(url, [latest])[latest]
    est = {t: latest - (latest_ts - t) // 12 for t in targets}       # 12 s slots since September 2022
    for _ in range(30):
        ts = timestamps(url, [b for b in est.values()] + [b + 1 for b in est.values()])
        pending = 0
        for t, b in est.items():
            if ts[b] > t:
                est[t] = b - max(1, (ts[b] - t + 11) // 12)
                pending += 1
            elif ts[b + 1] <= t:
                est[t] = b + 1 + (t - ts[b + 1]) // 12
                pending += 1
        print(f'  block search: {pending} dates not yet resolved')
        if pending == 0:
            return est, ts
    sys.exit('Block search did not converge.')


def strategy_version(url, strategy, asset, block):
    v1 = rpc_batch(url, [('eth_call', [{'to': strategy, 'data': selector(V1_GETTERS[0])}, hex(block)])])[0]
    if v1 not in (None, '0x'):
        return 1
    v2 = rpc_batch(url, [('eth_call', [{'to': strategy, 'data': selector(V2_GETTERS[0]) + pad_address(asset)},
                                       hex(block)])])[0]
    if v2 not in (None, '0x'):
        return 2
    sys.exit(f'Unknown interest-rate strategy interface at {strategy} (block {block}).')


def main():
    url = os.environ.get('ETH_RPC_URL')
    if not url:
        sys.exit('Set the ETH_RPC_URL environment variable first (see the docstring).')
    with open(RESERVES_PATH) as f:
        reserves = json.load(f)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    done = set()
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, newline='') as f:
            done = {(r['asset'], r['sample_utc']) for r in csv.DictReader(f)}
    times = list(sample_times())
    jobs = [(r['symbol'], r['underlyingAsset'], t, i) for r in reserves for i, t in enumerate(times)
            if (r['underlyingAsset'], t.strftime('%Y-%m-%dT%H:%M:%SZ')) not in done]
    print(f'{len(done)} samples already collected, {len(jobs)} to go.')
    if not jobs:
        return

    print('Finding the block at each sample time...')
    targets = sorted({int(t.timestamp()) for _, _, t, _ in jobs})
    block_of, ts_of = blocks_at_or_before(url, targets)

    versions = {}
    token_cache = {}
    new_file = not os.path.exists(OUT_PATH)
    with open(OUT_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(COLUMNS)
        for n, job_chunk in enumerate(chunks(jobs, BATCH), 1):
            reserve_data = batched(url, [('eth_call', [{'to': POOL, 'data': selector('getReserveData(address)')
                                                        + pad_address(asset)}, hex(block_of[int(t.timestamp())])])
                                         for _, asset, t, _ in job_chunk])
            for (symbol, asset, t, day_index), rd in zip(job_chunk, reserve_data):
                block = block_of[int(t.timestamp())]
                tag = hex(block)
                strategy = address_from_word(word(rd, 11))
                variable_rate = int(word(rd, 4), 16)
                if strategy not in versions:
                    versions[strategy] = strategy_version(url, strategy, asset, block)
                if versions[strategy] == 1:
                    calls = [('eth_call', [{'to': strategy, 'data': selector(g)}, tag]) for g in V1_GETTERS]
                else:
                    calls = [('eth_call', [{'to': strategy, 'data': selector(g) + pad_address(asset)}, tag])
                             for g in V2_GETTERS]
                validation = [''] * 4
                if day_index % VALIDATION_EVERY == 0:
                    a_token, stable_debt, variable_debt = (address_from_word(word(rd, i)) for i in (8, 9, 10))
                    calls += [('eth_call', [{'to': a_token, 'data': selector('totalSupply()')}, tag]),
                              ('eth_call', [{'to': variable_debt, 'data': selector('totalSupply()')}, tag]),
                              ('eth_call', [{'to': stable_debt, 'data': selector('totalSupply()')}, tag]),
                              ('eth_call', [{'to': asset, 'data': selector('balanceOf(address)')
                                             + pad_address(a_token)}, tag])]
                results = rpc_batch(url, calls)
                params = [to_int(r) for r in results[:4]]
                if day_index % VALIDATION_EVERY == 0:
                    validation = [to_int(r) for r in results[4:]]
                writer.writerow([symbol, asset, t.strftime('%Y-%m-%dT%H:%M:%SZ'), block, ts_of[block], strategy,
                                 versions[strategy], variable_rate]
                                + ['' if v is None else str(v) for v in params + validation])
                time.sleep(PAUSE_SECONDS / 2)
            f.flush()
            print(f'  {min(n * BATCH, len(jobs))}/{len(jobs)}', end='\r')
    print()

    with open(META_PATH, 'w') as f:
        json.dump({'source': 'Ethereum mainnet state read via eth_call at historical blocks',
                   'rpc_provider': requests.utils.urlparse(url).hostname,
                   'collected_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                   'pool': POOL, 'sampling': 'last block at or before each day 00:00 UTC',
                   'strategy_versions_seen': versions, 'validation_every_days': VALIDATION_EVERY,
                   'columns': COLUMNS,
                   'notes': ['Rates and model parameters are annual, in ray (1e27); token amounts in token units.',
                             'Strategy version 1 = Aave V3.0 interface (no arguments); '
                             'version 2 = DefaultReserveInterestRateStrategyV2 (reserve address argument).']},
                  f, indent=2)
    print(f'Saved {OUT_PATH} and {META_PATH}')


if __name__ == '__main__':
    main()
