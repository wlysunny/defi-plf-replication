"""
Clean the manually downloaded REP and SAI price files into daily USD price
series in the same format as the DefiLlama cache files.

Neither token is covered by DefiLlama's free price API, so their prices were
downloaded manually. The raw files are kept unmodified in data/manual/raw/ so
that the cleaning below can always be checked against the original source.

Raw sources:
- rep_usd.csv: CoinMarketCap-style export. Dates as text ("August 20 2026"),
  prices prefixed with "$", rows in descending date order.
- sai_usd.csv: data-warehouse-style export (column "event_date"), numeric,
  ascending date order.

The sample window is imported from fetch_exchange_rates_defillama.py so that
all exchange-rate inputs share one definition of the UIP sample period.

Run from the repository root:
    python scripts/clean_manual_prices.py
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.join('compounds_research', 'compound'))
from fetch_exchange_rates_defillama import UIP_SAMPLE_START, UIP_SAMPLE_END  # noqa: E402

RAW_DIR = 'data/manual/raw'
OUT_DIR = 'data/manual'


def clean_rep(path: str) -> pd.Series:
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['Date'], format='%B %d %Y')
    df['close_usd'] = df['Close'].replace(r'[\$,]', '', regex=True).astype(float)
    series = df.sort_values('date').set_index('date')['close_usd']
    series = series.loc[UIP_SAMPLE_START:UIP_SAMPLE_END]
    series.name = 'rep'
    return series


def clean_sai(path: str) -> pd.Series:
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['event_date']).dt.normalize().dt.tz_localize(None)
    series = df.sort_values('date').set_index('date')['close_price_usd']
    series = series.loc[UIP_SAMPLE_START:UIP_SAMPLE_END]
    series.name = 'sai'
    return series


def report(series: pd.Series) -> None:
    expected = pd.date_range(UIP_SAMPLE_START, UIP_SAMPLE_END, freq='D')
    missing = expected.difference(series.index)
    print(f'{series.name.upper()}: {len(series)} rows, '
          f'{series.index.min().date()} to {series.index.max().date()}, '
          f'{len(missing)} missing days in the sample window')


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    rep = clean_rep(f'{RAW_DIR}/rep_usd.csv')
    sai = clean_sai(f'{RAW_DIR}/sai_usd.csv')
    report(rep)
    report(sai)
    rep.to_csv(f'{OUT_DIR}/rep_usd_prices_cleaned.csv')
    sai.to_csv(f'{OUT_DIR}/sai_usd_prices_cleaned.csv')
    print(f'Saved cleaned REP and SAI prices to {OUT_DIR}/')
