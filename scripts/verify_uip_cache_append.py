"""Check the DefiLlama price caches after the UIP window correction (analysis_plans/uip_window_correction.md).

Run from the repository root after the caches have been updated and before they are committed:
    python scripts/verify_uip_cache_append.py

For each of the six cache files it checks, against the version committed in git (HEAD), that
  - the committed file is real CSV content, not a Git LFS pointer;
  - the committed bytes are an unchanged prefix of the new file;
  - exactly one data record was added, dated 2020-05-10, with a finite positive price.
It cannot detect a price that was cut short by an interrupted write yet still forms a valid number.
Exits with status 1 if any check fails for any file, or if the six files are not all present.
"""
import io
import math
import subprocess
import sys

import pandas as pd

TOKENS = ['bat', 'dai', 'eth', 'usdc', 'wbtc', 'zrx']
ADDED_DATE = pd.Timestamp('2020-05-10')


def committed_bytes(path):
    out = subprocess.run(['git', 'show', f'HEAD:{path}'], capture_output=True)
    if out.returncode != 0:
        raise RuntimeError(f'not in HEAD: {out.stderr.decode().strip()}')
    if out.stdout.startswith(b'version https://git-lfs'):
        raise RuntimeError('HEAD holds a Git LFS pointer, so the byte comparison is not possible')
    return out.stdout


def check(path):
    old = committed_bytes(path)
    with open(path, 'rb') as f:
        new = f.read()
    if not new.startswith(old):
        return False, 'committed bytes are not an unchanged prefix of the new file'
    old_df = pd.read_csv(io.BytesIO(old), index_col=0, parse_dates=True)
    new_df = pd.read_csv(io.BytesIO(new), index_col=0, parse_dates=True)
    added = new_df.iloc[len(old_df):]
    if len(new_df) - len(old_df) != 1 or len(added) != 1:
        return False, f'{len(new_df) - len(old_df)} records added, expected 1'
    if added.index[0] != ADDED_DATE:
        return False, f'added record dated {added.index[0]}, expected {ADDED_DATE.date()}'
    price = pd.to_numeric(added.iloc[0, 0], errors='coerce')
    if pd.isna(price) or not math.isfinite(float(price)) or price <= 0:
        return False, f'added price is not a finite positive number: {added.iloc[0, 0]!r}'
    if not new_df.iloc[:len(old_df)].equals(old_df):
        return False, 'existing records differ after parsing'
    return True, f'{len(old_df)} -> {len(new_df)} records; added {ADDED_DATE.date()} price {price}'


def main():
    ok_all = True
    for token in TOKENS:
        path = f'data/manual/{token}_usd_prices_cached.csv'
        try:
            ok, msg = check(path)
        except (OSError, RuntimeError) as e:
            ok, msg = False, str(e)
        ok_all &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {path}: {msg}")
    print('All six cache files pass.' if ok_all else 'At least one cache file FAILED. Do not commit; investigate first.')
    sys.exit(0 if ok_all else 1)


if __name__ == '__main__':
    main()
