"""
EXPLORATORY (post hoc). Do the authors' regime dates record when a governance
change was queued rather than when it took effect?

Background: the regime annotation (results/regime_annotation.csv) found that
the model change the authors date to 2019-12-17 21:57 took effect on chain
about two days later, and that the parameters they give for 2020-04-27 only
took effect on 2020-05-02/03. Compound routes admin actions through a Timelock
contract: an action is first queued (QueueTransaction, with an earliest
execution time "eta") and can be executed (ExecuteTransaction) only after a
fixed delay. If the authors' dates match the queue times, the discrepancy is a
difference of definition, not an error.

The script:
  1. reads cDAI's admin at a block inside the sample, and that contract's delay();
  2. searches for ExecuteTransaction events targeting cDAI inside each
     governance-type change interval found by the regime annotation
     (results/regime_onchain_changes.csv), since a change must have been
     executed between the two samples that bracket it;
  3. for each execution, searches for the matching QueueTransaction (same
     transaction hash) in the window before eta - delay;
  4. decodes the call and puts each action next to the nearest author regime start.

The free RPC tier limits eth_getLogs to 10 blocks per call, so the search is
restricted to these windows instead of scanning the whole sample.

Run from the repository root (archive RPC endpoint in ETH_RPC_URL):
    python scripts/exploratory_timelock_check.py
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from eth_abi import decode
from web3 import Web3

sys.path.insert(0, os.path.abspath('.'))
from collect_onchain_cdai import CDAI, rpc_batch, selector, to_int  # noqa: E402
from simulator.engine.dai_rate_params import PARAM_REGIME_NUMS  # noqa: E402

PROBE_BLOCK = 9_500_000          # about 2020-02-17, to read cDAI's admin
LOG_RANGE = 10                   # free-tier limit on eth_getLogs block range
CALLS_PER_BATCH = 10
PAUSE_SECONDS = 1.0
QUEUE_LOOKBACK_HOURS = 36        # search for the queue event this long before eta - delay
CHANGES_PATH = 'results/regime_onchain_changes.csv'
BLOCK_TIMES_PATH = 'data/derived/eth_block_times_sampled.csv'
OUT_PATH = 'results/exploratory/timelock_check.json'

QUEUE_SIG = 'QueueTransaction(bytes32,address,uint256,string,bytes,uint256)'
EXECUTE_SIG = 'ExecuteTransaction(bytes32,address,uint256,string,bytes,uint256)'


def topic(signature):
    return '0x' + Web3.keccak(text=signature).hex().removeprefix('0x')


def utc(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def get_logs(url, address, topics, start, end):
    """eth_getLogs over [start, end] in 10-block calls, batched."""
    calls = [('eth_getLogs', [{'address': address, 'topics': topics,
                               'fromBlock': hex(lo), 'toBlock': hex(min(lo + LOG_RANGE - 1, end))}])
             for lo in range(start, end + 1, LOG_RANGE)]
    logs = []
    for i in range(0, len(calls), CALLS_PER_BATCH):
        for res in rpc_batch(url, calls[i:i + CALLS_PER_BATCH]):
            logs.extend(res or [])
        time.sleep(PAUSE_SECONDS)
    return logs


def time_to_block(ts):
    table = pd.read_csv(BLOCK_TIMES_PATH)
    return int(round(np.interp(ts, table['timestamp'], table['block_number'])))


def parse(log):
    value, signature, data, eta = decode(['uint256', 'string', 'bytes', 'uint256'],
                                         bytes.fromhex(log['data'].removeprefix('0x')))
    arg = ''
    if signature.endswith('(address)') and len(data) >= 32:
        arg = '0x' + data[-20:].hex()
    elif signature.endswith('(uint256)') and len(data) >= 32:
        arg = str(int.from_bytes(data[:32], 'big'))
    return {'tx_hash': log['topics'][1], 'target': '0x' + log['topics'][2][-40:],
            'signature': signature, 'argument': arg, 'eta': int(eta),
            'block': int(log['blockNumber'], 16)}


def block_times(url, blocks):
    blocks = sorted(set(blocks))
    res = rpc_batch(url, [('eth_getBlockByNumber', [hex(b), False]) for b in blocks])
    return {b: int(r['timestamp'], 16) for b, r in zip(blocks, res)}


def main():
    url = os.environ.get('ETH_RPC_URL')
    if not url:
        sys.exit('Set ETH_RPC_URL first.')
    (admin_raw,) = rpc_batch(url, [('eth_call', [{'to': CDAI, 'data': selector('admin()')}, hex(PROBE_BLOCK)])])
    admin = Web3.to_checksum_address('0x' + admin_raw[-40:])
    (delay_raw,) = rpc_batch(url, [('eth_call', [{'to': admin, 'data': selector('delay()')}, hex(PROBE_BLOCK)])])
    delay = to_int(delay_raw)
    print(f'cDAI admin at block {PROBE_BLOCK}: {admin}; delay(): '
          f'{delay} s ({delay / 86400:.1f} days)' if delay else f'cDAI admin: {admin}; no delay() getter')

    changes = pd.read_csv(CHANGES_PATH)
    gov = changes[changes['type'].str.contains('new model contract|reserve factor change')]
    target_topic = '0x' + CDAI.lower().removeprefix('0x').rjust(64, '0')
    executed, queued = {}, []
    for c in gov.itertuples(index=False):
        print(f'Searching blocks {c.after_block}-{c.by_block} ({c.type}) for executions...')
        for log in get_logs(url, admin, [topic(EXECUTE_SIG), None, target_topic], int(c.after_block), int(c.by_block)):
            e = parse(log)
            executed[e['tx_hash']] = e
    for e in executed.values():
        q_end = time_to_block(e['eta'] - (delay or 0)) + 300
        q_start = time_to_block(e['eta'] - (delay or 0) - QUEUE_LOOKBACK_HOURS * 3600)
        print(f"Searching blocks {q_start}-{q_end} for the queue event of {e['signature']}...")
        for log in get_logs(url, admin, [topic(QUEUE_SIG), e['tx_hash'], target_topic], q_start, q_end):
            queued.append(parse(log))
    found = {q['tx_hash'] for q in queued}
    for e in executed.values():                      # executions whose queue event was not found
        if e['tx_hash'] not in found:
            queued.append(dict(e, block=None))
    print(f'\nActions on cDAI: {len(executed)} executed, {len(found)} queue events found\n')

    times = block_times(url, [q['block'] for q in queued if q['block']] + [e['block'] for e in executed.values()])
    starts = sorted((int(n), pd.Timestamp(t)) for n, t in PARAM_REGIME_NUMS.items())
    rows = []
    for q in sorted(queued, key=lambda x: x['eta']):
        e = executed.get(q['tx_hash'])
        q_ts = pd.Timestamp(utc(times[q['block']])) if q['block'] else pd.Timestamp(utc(q['eta'] - (delay or 0)))
        e_ts = pd.Timestamp(utc(times[e['block']])) if e else None
        n, start = min(starts, key=lambda s: abs((s[1] - q_ts).total_seconds()))
        row = {'signature': q['signature'], 'argument': q['argument'],
               'queued_utc': str(q_ts) if q['block'] else f'not found (eta - delay = {q_ts})', 'eta_utc': utc(q['eta']), 'executed_utc': str(e_ts) if e else 'not executed',
               'nearest_author_regime': n, 'author_start': str(start),
               'author_minus_queued_hours': round((start - q_ts).total_seconds() / 3600, 2),
               'author_minus_executed_hours': round((start - e_ts).total_seconds() / 3600, 2) if e else None}
        rows.append(row)
        print(f"{row['signature']:32s} {row['argument'][:14]:14s}  queued {row['queued_utc']}  "
              f"executed {row['executed_utc']}  | regime {n} {row['author_start']}  "
              f"author - queued {row['author_minus_queued_hours']:+.1f} h, "
              f"author - executed {row['author_minus_executed_hours'] if e else float('nan'):+.1f} h")

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w') as f:
        json.dump({'status': 'exploratory, post hoc', 'admin': admin, 'delay_seconds': delay,
                   'actions_on_cdai': rows}, f, indent=2)
    print(f'\nSaved {OUT_PATH}')


if __name__ == '__main__':
    main()
