"""
Replacement for fetch_exchange_rates.py, using DefiLlama's free historical
price API instead of CryptoCompare.

Background:
- CryptoCompare's histoday endpoint, used by the original repository, now
  requires a paid API key. Free alternatives (CryptoCompare's free tier,
  CoinGecko's Demo plan) restrict historical data to the most recent 365
  days and cannot reach the 2019-2020 sample period.
- DefiLlama's coins.llama.fi historical endpoint is free, needs no key, and
  returns 2019-2020 prices for BAT, ZRX, USDC, DAI, WBTC and ETH.
- REP and SAI are not covered by DefiLlama. Their prices come from manually
  downloaded files cleaned by clean_manual_prices.py.

Methodological difference from the original:
The original code requested direct pair prices from CryptoCompare (e.g. the
BAT/ETH market). DefiLlama only provides USD prices, so pair exchange rates
are computed here as cross rates: (base in USD) / (quote in USD). For thinly
traded tokens these may differ from direct market prices.

Sample window:
The UIP sample period is defined once, in UIP_SAMPLE_START and
UIP_SAMPLE_END below. It must cover the Compound interest-rate data used in
the regressions (2019-04-02 to 2020-05-08), because the regression sample is
the intersection of the exchange-rate and interest-rate series. A shorter
exchange-rate window silently truncates the regression sample.
"""

import os
import time

import pandas as pd
import requests

# Single source of truth for the UIP sample period. One day of margin is
# added on each side of the interest-rate data range.
UIP_SAMPLE_START = '2019-04-01'
UIP_SAMPLE_END = '2020-05-09'

CACHE_DIR = 'data/manual'
MANUAL_TOKENS = ('rep', 'sai')

# Ethereum mainnet contract addresses, verified against known 2020 prices.
TOKEN_CONTRACTS = {
    'bat':  'ethereum:0x0d8775f648430679a709e98d2b0cb6250d2887ef',
    'zrx':  'ethereum:0xE41d2489571d322189246DaFA5ebDe1F4699F498',
    'usdc': 'ethereum:0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    'dai':  'ethereum:0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'wbtc': 'ethereum:0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    'eth':  'coingecko:ethereum',
}


def get_defillama_price(token: str, unix_timestamp: int):
    """Return one token's USD price at a UNIX timestamp, or None if unavailable."""
    key = TOKEN_CONTRACTS[token]
    url = f'https://coins.llama.fi/prices/historical/{unix_timestamp}/{key}'
    response = requests.get(url)
    if response.status_code != 200:
        print(f'HTTP {response.status_code} retrieving price for {token} at {unix_timestamp}')
        return None
    entry = response.json().get('coins', {}).get(key)
    if entry is None:
        return None
    return entry['price']


def make_usd_price_series(token: str, start_date: str, end_date: str) -> pd.Series:
    """Build a daily USD price series for one token over [start_date, end_date]."""
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    prices = {}
    missing = 0
    print(f'Fetching {token}: {len(dates)} days...')
    for i, date in enumerate(dates):
        price = get_defillama_price(token, int(date.timestamp()))
        prices[date] = price
        if price is None:
            missing += 1
        if (i + 1) % 50 == 0:
            print(f'  {token}: {i + 1}/{len(dates)} days fetched')
        time.sleep(0.1)
    print(f'Finished {token}: {len(dates) - missing} prices, {missing} days without data.')
    series = pd.Series(prices, name=token, dtype='float64')
    series.index.name = 'date'
    return series


def _cache_covers(path: str, start_date: str, end_date: str) -> bool:
    """True if a cached price file exists and spans the whole requested window."""
    if not os.path.exists(path):
        return False
    cached = pd.read_csv(path, index_col=0, parse_dates=True)
    return (cached.index.min() <= pd.Timestamp(start_date)
            and cached.index.max() >= pd.Timestamp(end_date))


def cache_all_token_usd_prices(start_date: str = UIP_SAMPLE_START,
                               end_date: str = UIP_SAMPLE_END,
                               cache_dir: str = CACHE_DIR) -> None:
    """
    Fetch each DefiLlama token's USD price series once and save it to CSV.

    An existing cache file is reused only if it covers the requested window.
    Otherwise it is fetched again, so that changing the sample period can
    never silently reuse data from a shorter window.
    """
    os.makedirs(cache_dir, exist_ok=True)
    for token in TOKEN_CONTRACTS:
        out_path = f'{cache_dir}/{token}_usd_prices_cached.csv'
        if _cache_covers(out_path, start_date, end_date):
            print(f'{token}: cache covers {start_date} to {end_date}, skipping.')
            continue
        series = make_usd_price_series(token, start_date, end_date)
        series.to_csv(out_path)
    print('Done. REP and SAI are produced separately by clean_manual_prices.py.')


def _load_cached_usd_series(token: str, cache_dir: str = CACHE_DIR) -> pd.Series:
    """Load one token's USD price series from the cache or the cleaned manual file."""
    if token in MANUAL_TOKENS:
        path = f'{cache_dir}/{token}_usd_prices_cleaned.csv'
    else:
        path = f'{cache_dir}/{token}_usd_prices_cached.csv'
    series = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    series.index = series.index.tz_localize(None)
    return series


def load_manual_price_series(token: str) -> pd.Series:
    """Load the cleaned REP or SAI USD price series (kept for compatibility)."""
    series = _load_cached_usd_series(token)
    series.name = token
    return series


def get_exchange_rates_defillama(base_symbol: str, quote_symbol: str, limit: int = None) -> pd.DataFrame:
    """
    Replacement for the original get_exchange_rates(). Returns a DataFrame
    with a 'close' column holding the base/quote cross rate, so it can be
    used in utils.make_ex_rate_and_interest_rate_df without other changes.
    `limit` is accepted for interface compatibility and ignored.
    """
    base_prices = _load_cached_usd_series(base_symbol)
    quote_prices = _load_cached_usd_series(quote_symbol)
    df = (base_prices / quote_prices).rename('close').to_frame()
    df.index.name = 'date'
    return df
