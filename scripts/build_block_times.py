"""
Build a block-number-to-timestamp table for Ethereum mainnet by sampling
blocks at a fixed interval and interpolating between them.

Why this is needed:
Compound event logs (data/compound/events/*.jsonl.gz) and dYdX market data
(data/dydx/*_market_dydx.csv.gz) are indexed by block number only, while
interest rates and prices are indexed by time. The original authors built a
full per-block table (eth_block_times.csv.gz) with dydx/block_times.py, but
that file is registered in .gitattributes and was never committed, and the
script queried every block through a private node that is no longer
available.

Approach:
Blocks are produced at a fairly regular pace (about 13 seconds in 2019-2020),
so querying the timestamp of every SAMPLE_STEP-th block and interpolating
linearly gives timestamps accurate to within minutes. This is sufficient for
aligning events with daily or hourly rate data. The accuracy is measured, not
assumed: a set of held-out blocks between the sampled points is also queried,
and the interpolation error on those blocks is reported.

Usage (from the repository root):
    export ETH_RPC_URL="https://eth-mainnet.g.alchemy.com/v2/<your-key>"
    python scripts/build_block_times.py

The RPC URL contains a private key, so it is read from an environment
variable and must never be written into code or committed.

Other code can then convert block numbers to timestamps with:
    from build_block_times import block_to_datetime
    times = block_to_datetime(df['blockNumber'])
"""

import os
import sys
import time

import numpy as np
import pandas as pd
import requests

START_BLOCK = 8_980_000     # before the earliest cDAI event (8,983,575)
END_BLOCK = 10_610_000      # after the latest cDAI event (10,600,823)
SAMPLE_STEP = 1_000
VALIDATION_OFFSET = 500     # held-out blocks halfway between sampled points
VALIDATION_EVERY = 20       # validate on every 20th interval
BATCH_SIZE = 10             # small batches stay within free-plan throughput limits
PAUSE_SECONDS = 1.0
MAX_RETRIES = 5
OUT_PATH = 'data/derived/eth_block_times_sampled.csv'


def _request_batch(blocks, rpc_url):
    """Send one batched request; return ({block: timestamp}, [blocks to retry])."""
    payload = [{'jsonrpc': '2.0', 'id': b, 'method': 'eth_getBlockByNumber',
                'params': [hex(b), False]} for b in blocks]
    response = requests.post(rpc_url, json=payload, timeout=60)
    if response.status_code == 429:
        return {}, list(blocks)
    response.raise_for_status()
    found, retry = {}, []
    for item in response.json():
        block = int(item['id'])
        if item.get('result') is not None:
            found[block] = int(item['result']['timestamp'], 16)
        elif (item.get('error') or {}).get('code') == 429:
            retry.append(block)
        else:
            raise RuntimeError(f"No block data for block {block}: {item.get('error')}")
    return found, retry


def fetch_timestamps(blocks, rpc_url, batch_size=BATCH_SIZE, max_retries=MAX_RETRIES):
    """
    Return {block_number: unix_timestamp} using small batched JSON-RPC requests.

    Free RPC plans limit compute units per second. Requests rejected with
    code 429 (rate limit) are retried with exponential backoff; any other
    error stops the run, so that a partial table is never saved silently.
    """
    result = {}
    blocks = list(blocks)
    for start in range(0, len(blocks), batch_size):
        pending = blocks[start:start + batch_size]
        for attempt in range(max_retries + 1):
            found, pending = _request_batch(pending, rpc_url)
            result.update(found)
            if not pending:
                break
            wait = PAUSE_SECONDS * 2 ** (attempt + 1)
            print(f'  rate limited on {len(pending)} blocks, retrying in {wait:.0f} s')
            time.sleep(wait)
        else:
            raise RuntimeError(f'Still rate limited after {max_retries} retries: blocks {pending}')
        done = min(start + batch_size, len(blocks))
        if done % 200 == 0 or done == len(blocks):
            print(f'  {done}/{len(blocks)} blocks')
        time.sleep(PAUSE_SECONDS)
    return result


def interpolate(blocks, sampled):
    """Linearly interpolate unix timestamps for block numbers from a sampled table."""
    return np.interp(np.asarray(blocks, dtype='float64'),
                     sampled['block_number'].to_numpy(dtype='float64'),
                     sampled['timestamp'].to_numpy(dtype='float64'))


def block_to_datetime(blocks, table_path=OUT_PATH):
    """Convert block numbers to UTC datetimes using the sampled table."""
    sampled = pd.read_csv(table_path)
    lo, hi = sampled['block_number'].min(), sampled['block_number'].max()
    blocks = np.asarray(blocks)
    if blocks.min() < lo or blocks.max() > hi:
        raise ValueError(f'Blocks outside the sampled range {lo}-{hi}; rebuild the table.')
    return pd.to_datetime(interpolate(blocks, sampled), unit='s')


def main():
    rpc_url = os.environ.get('ETH_RPC_URL')
    if not rpc_url:
        sys.exit('Set the ETH_RPC_URL environment variable first (see the docstring).')

    sample_blocks = list(range(START_BLOCK, END_BLOCK + 1, SAMPLE_STEP))
    print(f'Fetching {len(sample_blocks)} sampled blocks...')
    sampled_ts = fetch_timestamps(sample_blocks, rpc_url)
    sampled = pd.DataFrame(sorted(sampled_ts.items()), columns=['block_number', 'timestamp'])

    if not sampled['timestamp'].is_monotonic_increasing:
        raise RuntimeError('Sampled timestamps are not increasing; check the RPC responses.')

    check_blocks = sample_blocks[:-1][::VALIDATION_EVERY]
    check_blocks = [b + VALIDATION_OFFSET for b in check_blocks]
    print(f'Fetching {len(check_blocks)} held-out blocks for validation...')
    actual = fetch_timestamps(check_blocks, rpc_url)
    predicted = interpolate(check_blocks, sampled)
    errors = np.abs(predicted - np.array([actual[b] for b in check_blocks]))
    print(f'Interpolation error on held-out blocks: median {np.median(errors):.0f} s, '
          f'95th percentile {np.percentile(errors, 95):.0f} s, max {errors.max():.0f} s')

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    sampled.to_csv(OUT_PATH, index=False)
    first, last = pd.to_datetime(sampled['timestamp'].iloc[[0, -1]], unit='s')
    print(f'Saved {len(sampled)} rows to {OUT_PATH} ({first} to {last} UTC)')


if __name__ == '__main__':
    main()
