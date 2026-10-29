"""Re-read a random sample of the on-chain datasets from a second RPC provider.

Criterion: analysis_plans/second_provider_check_criterion.md, committed with this script before it was run.

Usage, from the repository root:
    source ~/.defi_env
    python scripts/second_provider_check.py --self-check   # 3 rows, one per stratum, via ETH_RPC_URL (original provider)
    python scripts/second_provider_check.py                # 30 rows via ETH_RPC_URL_2 (second provider)

Both runs refuse to start unless the criterion and this script are committed and unmodified.
The self-check writes results/second_provider_self_check.json and exits with status 1 if any row differs
or cannot be read. The main run refuses to start unless that file records a passed self-check made with
the same criterion, script and input files (SHA-256), and writes results/second_provider_check.json.
Verdicts: Pass, Fail or Incomplete; Fail takes precedence over Incomplete (see the criterion).
Query failures (requests exceptions, and JSON-RPC error responses raised by rpc_batch() as RuntimeError
'RPC error for ...') are retried up to 3 attempts per row; a row that still fails is incomplete
(criterion, Amendment 1). Any other exception stops the script with a traceback and no verdict. No provider key is written anywhere.
"""
import csv
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect_onchain_cdai as cdai          # noqa: E402
import collect_aave_v3_rate_params as aave   # noqa: E402

SEED = 20261029
CDAI_LONG = 'data/onchain/cdai_panel.csv'
CDAI_DENSE = 'data/onchain/cdai_panel_dense_2020.csv'
AAVE = 'data/aave_v3/aave_v3_rate_params_daily.csv'
CRITERION = 'analysis_plans/second_provider_check_criterion.md'
SELF_CHECK_OUT = 'results/second_provider_self_check.json'
MAX_ATTEMPTS = 3
RETRY_PAUSE_SECONDS = 5
MAIN_OUT = 'results/second_provider_check.json'
AAVE_COMPARED = ['strategy', 'strategy_version', 'pool_currentVariableBorrowRate',
                 'irm_optimalUsageRatio', 'irm_baseVariableBorrowRate', 'irm_variableRateSlope1',
                 'irm_variableRateSlope2', 'val_aToken_totalSupply', 'val_variableDebt_totalSupply',
                 'val_stableDebt_totalSupply', 'val_underlying_balanceOf_aToken']


def sha256(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def script_sha256():
    return sha256(os.path.abspath(__file__))


def input_sha256():
    return {path: sha256(path) for path in (CDAI_LONG, CDAI_DENSE, AAVE)}


def require_committed():
    """Refuse to run unless the criterion and this script are committed and unmodified. Returns HEAD."""
    script = os.path.relpath(os.path.abspath(__file__))
    for path in (CRITERION, script):
        tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', path], capture_output=True)
        changed = subprocess.run(['git', 'status', '--porcelain', '--', path], capture_output=True, text=True)
        if tracked.returncode != 0 or changed.stdout.strip():
            sys.exit(f'{path} is not committed, or has been modified since the last commit. Commit it first.')
    return subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()


def is_query_failure(e):
    """Network/HTTP failure, or a JSON-RPC error response as raised by rpc_batch() (Amendment 1)."""
    return (isinstance(e, requests.exceptions.RequestException)
            or (type(e) is RuntimeError and str(e).startswith('RPC error for')))


def read_rows(path):
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def as_text(v):
    return '' if v is None else str(v)


def reread_cdai(url, columns, stored):
    """Row produced by the original collection function, compared column by column."""
    new = [as_text(v) for v in cdai.sample_block(url, int(stored['block']))]
    diffs = []
    if len(new) != len(columns):
        diffs.append({'field': '(row length)', 'stored': len(columns), 'second': len(new)})
    for col, value in zip(columns, new):
        if stored[col] != value:
            diffs.append({'field': col, 'stored': stored[col], 'second': value})
    return diffs


def reread_aave(url, stored):
    """Repeat the reading sequence of collect_aave_v3_rate_params.main() for one asset and block,
    using the helper functions as they are available in that module."""
    asset, block = stored['asset'], int(stored['block'])
    tag = hex(block)
    rd = aave.rpc_batch(url, [('eth_call', [{'to': aave.POOL, 'data': aave.selector('getReserveData(address)')
                                             + aave.pad_address(asset)}, tag])])[0]
    strategy = aave.address_from_word(aave.word(rd, 11))
    variable_rate = int(aave.word(rd, 4), 16)
    version = aave.strategy_version(url, strategy, asset, block)
    if version == 1:
        calls = [('eth_call', [{'to': strategy, 'data': aave.selector(g)}, tag]) for g in aave.V1_GETTERS]
    else:
        calls = [('eth_call', [{'to': strategy, 'data': aave.selector(g) + aave.pad_address(asset)}, tag])
                 for g in aave.V2_GETTERS]
    a_token, stable_debt, variable_debt = (aave.address_from_word(aave.word(rd, i)) for i in (8, 9, 10))
    calls += [('eth_call', [{'to': a_token, 'data': aave.selector('totalSupply()')}, tag]),
              ('eth_call', [{'to': variable_debt, 'data': aave.selector('totalSupply()')}, tag]),
              ('eth_call', [{'to': stable_debt, 'data': aave.selector('totalSupply()')}, tag]),
              ('eth_call', [{'to': asset, 'data': aave.selector('balanceOf(address)')
                             + aave.pad_address(a_token)}, tag])]
    values = [as_text(aave.to_int(r)) for r in aave.rpc_batch(url, calls)]
    new = dict(zip(AAVE_COMPARED, [strategy, str(version), str(variable_rate)] + values))
    diffs = []
    for col in AAVE_COMPARED:
        if col.startswith('val_') and stored[col] == '':
            continue  # validation columns are compared only where populated in the stored file
        if stored[col] != new[col]:
            diffs.append({'field': col, 'stored': stored[col], 'second': new[col]})
    return diffs


def draw_sample():
    rng = random.Random(SEED)
    long_cols, long_rows = read_rows(CDAI_LONG)
    dense_cols, dense_rows = read_rows(CDAI_DENSE)
    aave_cols, aave_rows = read_rows(AAVE)
    missing = [c for c in AAVE_COMPARED if c not in aave_cols]
    if missing:
        sys.exit(f'Aave file lacks expected columns: {missing}')
    aave_rows = [r for r in aave_rows if r['strategy'] not in ('not listed', '')]
    sample = [('cdai_long', long_cols, r) for r in rng.sample(long_rows, 15)]
    sample += [('cdai_dense', dense_cols, r) for r in rng.sample(dense_rows, 5)]
    sample += [('aave_v3', None, r) for r in rng.sample(aave_rows, 10)]
    return sample


def run(url, sample):
    rows = []
    for dataset, columns, stored in sample:
        entry = {'dataset': dataset, 'block': int(stored['block']), 'asset': stored.get('symbol', 'cDAI')}
        if dataset == 'aave_v3':
            entry['validation_fields_populated'] = sum(stored[c] != '' for c in AAVE_COMPARED if c.startswith('val_'))
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                diffs = reread_cdai(url, columns, stored) if dataset != 'aave_v3' else reread_aave(url, stored)
                entry.update(status='compared', attempts=attempt, n_differences=len(diffs), differences=diffs)
                break  # a completed comparison is final; differences are never re-read
            except BaseException as e:
                if not is_query_failure(e):  # anything else is a defect to investigate, not a data result
                    traceback.print_exc()
                    sys.exit(f'Stopped without a verdict at {dataset} block {entry["block"]}: unexpected error '
                             '(see traceback). Rows printed above were completed before the error.')
                entry.setdefault('errors', []).append(f'attempt {attempt}: {type(e).__name__}: {e}')
                if attempt == MAX_ATTEMPTS:
                    entry.update(status='incomplete', attempts=attempt)
                else:
                    time.sleep(RETRY_PAUSE_SECONDS)
        rows.append(entry)
        shown = entry.get('n_differences', 'INCOMPLETE')
        print(f"{dataset:10} block {entry['block']:>9} {entry['asset']:5} differences: {shown}"
              f"  (attempts: {entry['attempts']})")
    n_incomplete = sum(r['status'] == 'incomplete' for r in rows)
    n_diff = sum(r.get('n_differences', 0) > 0 for r in rows)
    aave_done = [r for r in rows if r['dataset'] == 'aave_v3' and r['status'] == 'compared']
    coverage = {'aave_rows_compared': len(aave_done),
                'aave_rows_with_validation_compared': sum(r['validation_fields_populated'] > 0 for r in aave_done),
                'aave_validation_values_compared': sum(r['validation_fields_populated'] for r in aave_done)}
    print('Aave validation coverage:', coverage)
    verdict = 'Fail' if n_diff else ('Incomplete' if n_incomplete else 'Pass')  # Fail takes precedence
    return rows, n_diff, n_incomplete, verdict, coverage


def save(path, url, rows, n_diff, n_incomplete, verdict, coverage, kind, commit):
    os.makedirs('results', exist_ok=True)
    with open(path, 'w') as f:
        json.dump({'check': kind, 'criterion': CRITERION, 'repository_head': commit,
                   'criterion_sha256': sha256(CRITERION), 'script_sha256': script_sha256(),
                   'input_sha256': input_sha256(),
                   'provider_host': urlparse(url).hostname,
                   'run_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'seed': SEED,
                   'n_rows': len(rows), 'rows_with_differences': n_diff, 'rows_incomplete': n_incomplete,
                   'verdict': verdict, 'coverage': coverage, 'rows': rows}, f, indent=2)
    print(f'Saved {path}')


def main():
    self_check = '--self-check' in sys.argv
    var = 'ETH_RPC_URL' if self_check else 'ETH_RPC_URL_2'
    url = os.environ.get(var)
    if not url:
        sys.exit(f'Set {var} first (source ~/.defi_env).')
    commit = require_committed()
    sample = draw_sample()

    if self_check:
        rows, n_diff, n_inc, verdict, coverage = run(url, [sample[0], sample[15], sample[20]])
        print(f'SELF-CHECK: rows with differences {n_diff}/3, incomplete {n_inc}/3 -> {verdict}')
        for r in rows:
            for d in r.get('differences', []):
                print('   ', r['dataset'], r['block'], d)
            if r['status'] == 'incomplete':
                print('   ', r['dataset'], r['block'], r['errors'])
        save(SELF_CHECK_OUT, url, rows, n_diff, n_inc, verdict, coverage, 'self-check (original provider)', commit)
        sys.exit(0 if verdict == 'Pass' else 1)

    try:
        with open(SELF_CHECK_OUT) as f:
            sc = json.load(f)
    except FileNotFoundError:
        sys.exit('No self-check found. Run with --self-check first.')
    if sc.get('verdict') != 'Pass':
        sys.exit('The last self-check did not pass. Investigate and document it, then run --self-check again.')
    if sc.get('criterion_sha256') != sha256(CRITERION):
        sys.exit('The criterion differs from the version used in the self-check. Run --self-check again.')
    if sc.get('script_sha256') != script_sha256():
        sys.exit('The self-check was made with a different version of this script. Run --self-check again.')
    if sc.get('input_sha256') != input_sha256():
        sys.exit('The input CSV files differ from those used in the self-check. Investigate before continuing.')
    rows, n_diff, n_inc, verdict, coverage = run(url, sample)
    print(f'MAIN RUN: rows with differences {n_diff}/{len(rows)}, incomplete {n_inc}/{len(rows)} -> {verdict}')
    save(MAIN_OUT, url, rows, n_diff, n_inc, verdict, coverage, 'main run (second provider)', commit)
    sys.exit(0 if verdict == 'Pass' else 1)


if __name__ == '__main__':
    main()
