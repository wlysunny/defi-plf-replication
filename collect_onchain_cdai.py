"""
Collect an on-chain panel of the Compound V2 cDAI market directly from the
Ethereum blockchain, at a fixed block interval, from the market's launch to the
end of November 2025 (before Compound V2's deprecation in December 2025).

Why:
The original paper's rate series came from the Compound V2 API, which was shut
down on 2023-04-15, and spot checks against on-chain state show that series
departs from the true borrow rate (results/exploratory/onchain_rate_check.json).
The blockchain state is the primary record, so this script reads it directly.
The 2019-11 to 2020-05 part overlaps the paper's sample and is used to validate
the pipeline; the remainder (2020-05 to 2025-11) is the newly constructed data.

What is recorded at each sampled block:
  block number and exact block timestamp;
  cDAI: borrowRatePerBlock, supplyRatePerBlock, getCash, totalBorrows,
        totalReserves, reserveFactorMantissa, interestRateModel (address);
  the active interest-rate model: baseRatePerBlock, multiplierPerBlock,
        jumpMultiplierPerBlock, kink (blank if the model has no such getter).
All on-chain integers are stored as exact decimal strings.

The script deliberately prints no summary statistics of the collected values,
so that the test criterion can be fixed before the data are examined.

It can be interrupted and re-run: rows already in the output file are skipped.

Usage (from the repository root, archive-capable RPC endpoint required):
    export ETH_RPC_URL="https://eth-mainnet.g.alchemy.com/v2/<key>"
    python collect_onchain_cdai.py
"""

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests
from web3 import Web3

CDAI = '0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643'
START_BLOCK = 8_983_575          # cDAI deployment block (first event in the repository's log)
END_DATE = '2025-12-01'          # stop before Compound V2's deprecation
BLOCK_STEP = 6_000               # about one sample per day (13 s blocks before Sep 2022, 12 s after)
OUT_PATH = 'data/onchain/cdai_panel.csv'
META_PATH = 'data/onchain/cdai_panel_provenance.json'
PAUSE_SECONDS = 1.0
MAX_RETRIES = 6

CDAI_GETTERS = ['borrowRatePerBlock()', 'supplyRatePerBlock()', 'getCash()', 'totalBorrows()',
                'totalReserves()', 'reserveFactorMantissa()', 'interestRateModel()']
MODEL_GETTERS = ['baseRatePerBlock()', 'multiplierPerBlock()', 'jumpMultiplierPerBlock()', 'kink()']
COLUMNS = (['block', 'timestamp', 'utc']
           + ['cdai_' + g[:-2] for g in CDAI_GETTERS]
           + ['irm_' + g[:-2] for g in MODEL_GETTERS])


def selector(signature):
    return '0x' + Web3.keccak(text=signature)[:4].hex().removeprefix('0x')


class RateLimited(Exception):
    pass


def rpc_batch(url, calls):
    """
    Send a batch of JSON-RPC calls [(method, params), ...] and return the list of
    results in order. Rate-limit responses are retried with exponential backoff;
    a reverted eth_call returns None; any other error stops the run.
    """
    payload = [{'jsonrpc': '2.0', 'id': i, 'method': m, 'params': p} for i, (m, p) in enumerate(calls)]
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 429:
                raise RateLimited()
            response.raise_for_status()
            replies = {r['id']: r for r in response.json()}
            out = []
            for i in range(len(calls)):
                r = replies[i]
                err = r.get('error')
                if err:
                    if err.get('code') == 429 or 'exceeded' in str(err.get('message', '')).lower():
                        raise RateLimited()
                    if 'revert' in str(err.get('message', '')).lower():
                        out.append(None)
                        continue
                    raise RuntimeError(f'RPC error for {calls[i]}: {err}')
                out.append(r.get('result'))
            return out
        except RateLimited:
            wait = PAUSE_SECONDS * 2 ** (attempt + 1)
            print(f'  rate limited, retrying in {wait:.0f} s')
            time.sleep(wait)
    raise RuntimeError('Still rate limited after retries; re-run later to resume.')


def to_int(hex_value):
    if hex_value in (None, '0x'):
        return None
    return int(hex_value, 16)


def block_timestamp(url, block):
    (result,) = rpc_batch(url, [('eth_getBlockByNumber', [hex(block), False])])
    return int(result['timestamp'], 16)


def find_end_block(url, end_date):
    """Last block before END_DATE (UTC), by binary search on block timestamps."""
    target = int(datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc).timestamp())
    (latest,) = rpc_batch(url, [('eth_blockNumber', [])])
    lo, hi = START_BLOCK, int(latest, 16)
    if block_timestamp(url, hi) < target:
        return hi
    while lo < hi:
        mid = (lo + hi) // 2
        if block_timestamp(url, mid) < target:
            lo = mid + 1
        else:
            hi = mid
    return lo - 1


def sample_block(url, block):
    """Read one row of the panel at `block`."""
    tag = hex(block)
    calls = [('eth_getBlockByNumber', [tag, False])]
    calls += [('eth_call', [{'to': CDAI, 'data': selector(g)}, tag]) for g in CDAI_GETTERS]
    results = rpc_batch(url, calls)
    timestamp = int(results[0]['timestamp'], 16)
    cdai_values = [to_int(r) for r in results[1:]]
    irm_int = cdai_values[-1]
    irm = Web3.to_checksum_address('0x' + format(irm_int, '064x')[-40:]) if irm_int is not None else None
    model_values = [None] * len(MODEL_GETTERS)
    if irm:
        model_results = rpc_batch(url, [('eth_call', [{'to': irm, 'data': selector(g)}, tag])
                                        for g in MODEL_GETTERS])
        model_values = [to_int(r) for r in model_results]
    utc = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    row = [block, timestamp, utc] + [str(v) if v is not None else '' for v in cdai_values[:-1]]
    row += [irm or ''] + [str(v) if v is not None else '' for v in model_values]
    return row


def already_done(path):
    if not os.path.exists(path):
        return set()
    with open(path, newline='') as f:
        return {int(r['block']) for r in csv.DictReader(f)}


def main():
    url = os.environ.get('ETH_RPC_URL')
    if not url:
        sys.exit('Set the ETH_RPC_URL environment variable first (see the docstring).')
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    end_block = find_end_block(url, END_DATE)
    blocks = list(range(START_BLOCK, end_block + 1, BLOCK_STEP))
    done = already_done(OUT_PATH)
    todo = [b for b in blocks if b not in done]
    print(f'Blocks {START_BLOCK} to {end_block}, step {BLOCK_STEP}: {len(blocks)} samples, '
          f'{len(done)} already collected, {len(todo)} to go.')

    new_file = not os.path.exists(OUT_PATH)
    with open(OUT_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(COLUMNS)
        for i, block in enumerate(todo, 1):
            writer.writerow(sample_block(url, block))
            f.flush()                      # every row is saved immediately, so a crash loses nothing
            if i % 50 == 0 or i == len(todo):
                print(f'  {i}/{len(todo)} samples')
            time.sleep(PAUSE_SECONDS)

    with open(META_PATH, 'w') as f:
        json.dump({'source': 'Ethereum mainnet state read via eth_call at historical blocks',
                   'rpc_provider': requests.utils.urlparse(url).hostname,
                   'collected_utc': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                   'contract': CDAI, 'start_block': START_BLOCK, 'end_block': end_block,
                   'end_date_exclusive': END_DATE, 'block_step': BLOCK_STEP, 'rows': len(blocks),
                   'columns': COLUMNS,
                   'notes': ['All on-chain integers are exact decimal strings; rates are per block, scaled by 1e18.',
                             'Compound V2 annualises with 2,102,400 blocks per year (15 s blocks); actual block '
                             'times were about 13 s before September 2022 and 12 s after.',
                             'Blank model fields mean the model contract has no such getter.']},
                  f, indent=2)
    print(f'Saved {OUT_PATH} and {META_PATH}')


if __name__ == '__main__':
    main()
