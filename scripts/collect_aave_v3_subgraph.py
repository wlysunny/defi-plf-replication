"""
Collect a daily panel of Aave V3 (Ethereum mainnet, Core market) reserves from
the official Aave V3 subgraph, published by Aave on The Graph network.

Why:
The Aave V3 subgraph is an existing, publicly maintained dataset: an index of
every reserve update emitted by the Aave V3 Pool, with the protocol's own
utilisation and rate fields. Aave V3 postdates the paper (launched on Ethereum
on 2023-01-27) and uses the same kinked interest-rate design, so the paper's
analyses have not been applied to it. This is the "existing dataset" of the
project; it is not modified, only sampled.

Sampling:
For each reserve and each day at 00:00 UTC, the script records the last
reserve update at or before that moment, i.e. the state of the reserve at that
time. This mirrors the cDAI panel, which reads the state at a sampled block.
The time since that update ("staleness") is kept so that stale samples can be
identified later.

What is recorded at each sample (raw values as returned, no conversion):
  sample time; the history item's id and timestamp;
  utilizationRate (computed by the subgraph), variableBorrowRate, liquidityRate,
  stableBorrowRate (rates are annual, in ray = 1e27);
  totalLiquidity, availableLiquidity, totalATokenSupply,
  totalCurrentVariableDebt, totalPrincipalStableDebt (token units, see decimals).

The script prints no summary statistics of the collected values, so that the
test criterion can be fixed before the data are examined. It can be interrupted
and re-run: samples already in the output file are skipped.

The interest-rate model parameters (including the kink, optimalUsageRatio) are
not kept historically by the subgraph; they are read from the chain separately.

Usage (from the repository root; a Graph API key is required, never commit it):
    export GRAPH_API_KEY="<key from Subgraph Studio>"
    python scripts/collect_aave_v3_subgraph.py --list-reserves   # step 1: check reserve ids
    python scripts/collect_aave_v3_subgraph.py                    # step 2: collect
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

SUBGRAPH_ID = 'Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g'   # Aave V3 Ethereum, listed in github.com/aave/protocol-subgraphs
SYMBOLS = ['USDC', 'USDT', 'DAI', 'WETH']
START_DATE = '2023-02-01'        # first full month after the Ethereum V3 launch on 2023-01-27
END_DATE = '2025-12-01'          # same end as the cDAI panel (exclusive)
SAMPLES_PER_REQUEST = 40         # aliased sub-queries per GraphQL request
OUT_PATH = 'data/aave_v3/aave_v3_daily_panel.csv'
RESERVES_PATH = 'data/aave_v3/aave_v3_reserves.json'
META_PATH = 'data/aave_v3/aave_v3_daily_panel_provenance.json'
PAUSE_SECONDS = 1.0
MAX_RETRIES = 6

HISTORY_FIELDS = ['id', 'timestamp', 'utilizationRate', 'variableBorrowRate', 'liquidityRate',
                  'stableBorrowRate', 'totalLiquidity', 'availableLiquidity', 'totalATokenSupply',
                  'totalCurrentVariableDebt', 'totalPrincipalStableDebt']
COLUMNS = ['symbol', 'reserve_id', 'sample_utc', 'sample_timestamp', 'staleness_seconds'] + \
          ['item_' + f for f in HISTORY_FIELDS]


def endpoint():
    key = os.environ.get('GRAPH_API_KEY')
    if not key:
        sys.exit('Set GRAPH_API_KEY first (see the docstring). Do not write the key into any file.')
    return f'https://gateway.thegraph.com/api/{key}/subgraphs/id/{SUBGRAPH_ID}'


def graphql(url, query):
    """POST a query; retry rate limits and transient errors with exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.post(url, json={'query': query}, timeout=60)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue
        if r.status_code in (429, 502, 503, 504):
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        body = r.json()
        if 'errors' in body:
            sys.exit(f'GraphQL error: {body["errors"]}')
        return body['data']
    sys.exit('Too many failed attempts; re-run later (completed samples are kept).')


def meta(url):
    return graphql(url, '{ _meta { deployment hasIndexingErrors block { number timestamp hash } } }')['_meta']


def list_reserves(url):
    symbols = json.dumps(SYMBOLS)
    q = f'{{ reserves(where: {{symbol_in: {symbols}}}) {{ id symbol name underlyingAsset decimals pool {{ id }} }} }}'
    return graphql(url, q)['reserves']


def sample_times():
    t = datetime.fromisoformat(START_DATE).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(END_DATE).replace(tzinfo=timezone.utc)
    while t < end:
        yield t
        t += timedelta(days=1)


def already_done(path):
    if not os.path.exists(path):
        return set()
    with open(path, newline='') as f:
        return {(row['reserve_id'], row['sample_utc']) for row in csv.DictReader(f)}


def build_query(jobs):
    fields = ' '.join(HISTORY_FIELDS)
    parts = []
    for i, (reserve_id, t) in enumerate(jobs):
        ts = int(t.timestamp())
        parts.append(f's{i}: reserveParamsHistoryItems(first: 1, orderBy: timestamp, orderDirection: desc, '
                     f'where: {{reserve: "{reserve_id}", timestamp_lte: {ts}}}) {{ {fields} }}')
    return '{ ' + ' '.join(parts) + ' }'


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--list-reserves', action='store_true',
                        help='only list matching reserves and save them; check that each symbol appears once')
    args = parser.parse_args(argv)
    url = endpoint()
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

    if args.list_reserves:
        reserves = list_reserves(url)
        for r in reserves:
            print(f"{r['symbol']:6s} decimals={r['decimals']:>2}  pool={r['pool']['id']}  id={r['id']}")
        with open(RESERVES_PATH, 'w') as f:
            json.dump(reserves, f, indent=2)
        print(f'\nSaved {RESERVES_PATH}. If a symbol appears more than once, stop and check before collecting.')
        return

    if not os.path.exists(RESERVES_PATH):
        sys.exit('Run with --list-reserves first.')
    with open(RESERVES_PATH) as f:
        reserves = json.load(f)
    counts = {s: sum(r['symbol'] == s for r in reserves) for s in SYMBOLS}
    if any(c != 1 for c in counts.values()):
        sys.exit(f'Each symbol must match exactly one reserve; found {counts}. Edit {RESERVES_PATH} deliberately.')

    meta_start = meta(url)
    done = already_done(OUT_PATH)
    jobs = [(r['id'], r['symbol'], t) for r in reserves for t in sample_times()
            if (r['id'], t.strftime('%Y-%m-%dT%H:%M:%SZ')) not in done]
    print(f'{len(done)} samples already collected, {len(jobs)} to go.')

    new_file = not os.path.exists(OUT_PATH)
    with open(OUT_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            writer.writeheader()
        for start in range(0, len(jobs), SAMPLES_PER_REQUEST):
            chunk = jobs[start:start + SAMPLES_PER_REQUEST]
            data = graphql(url, build_query([(rid, t) for rid, _, t in chunk]))
            for i, (rid, symbol, t) in enumerate(chunk):
                items = data[f's{i}']
                if not items:          # before the reserve's first update: nothing to record
                    continue
                item = items[0]
                row = {'symbol': symbol, 'reserve_id': rid,
                       'sample_utc': t.strftime('%Y-%m-%dT%H:%M:%SZ'),
                       'sample_timestamp': int(t.timestamp()),
                       'staleness_seconds': int(t.timestamp()) - int(item['timestamp'])}
                row.update({'item_' + k: str(item[k]) for k in HISTORY_FIELDS})
                writer.writerow(row)
            f.flush()
            print(f'  {min(start + SAMPLES_PER_REQUEST, len(jobs))}/{len(jobs)}', end='\r')
            time.sleep(PAUSE_SECONDS)
    print()

    with open(META_PATH, 'w') as f:
        json.dump({
            'source': 'Aave V3 subgraph (Ethereum mainnet), The Graph network',
            'subgraph_id': SUBGRAPH_ID,
            'subgraph_meta_at_start': meta_start,
            'subgraph_meta_at_end': meta(url),
            'collected_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'symbols': SYMBOLS, 'start_date': START_DATE, 'end_date_exclusive': END_DATE,
            'sampling': 'last ReserveParamsHistoryItem at or before each day 00:00 UTC',
            'script': os.path.basename(__file__),
            'note': 'API key deliberately not recorded.',
        }, f, indent=2)
    print(f'Saved {OUT_PATH} and {META_PATH}')


if __name__ == '__main__':
    main()
