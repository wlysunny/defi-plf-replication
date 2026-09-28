"""
REPLACEMENT for fetch_exchange_rates.py — uses DefiLlama's free historical
price API instead of CryptoCompare (which now returns 401 "API key required").

Background (see repo_verification_notes.md, Issue #12):
- CryptoCompare's histoday endpoint, used by the original repo, now requires
  a paid/registered API key.
- The two most commonly-cited free replacements (CryptoCompare's own paid
  tiers, and CoinGecko's public Demo plan) both restrict free-tier historical
  data to the past 365 days, which cannot reach back to the paper's original
  2020 sample period.
- DefiLlama's `coins.llama.fi` historical price endpoint is free, requires no
  API key, and DOES return correct 2020-era prices (verified manually for
  BAT, ZRX, USDC, DAI, WBTC, and ETH).
- REP (Augur) and SAI (single-collateral Dai) are NOT covered by DefiLlama at
  all (confirmed: even the *current* price lookup returns no data for REP),
  so they are excluded from TOKEN_CONTRACTS below. This narrows the UIP
  analysis from the original 8 tokens / 20 pairs to 6 tokens / 15 pairs.
  This is a genuine, documented data-availability boundary — not a bug to
  "fix" — and should be stated as such in the Justification / New Data
  sections rather than silently patched over.
"""

import requests
import pandas as pd
import time

# Ethereum mainnet contract addresses, each independently verified via
# https://coins.llama.fi/prices/historical/{unix_ts}/{key} against known
# 2020-03-01 prices before being used here.
TOKEN_CONTRACTS = {
    'bat':  'ethereum:0x0d8775f648430679a709e98d2b0cb6250d2887ef',
    'zrx':  'ethereum:0xE41d2489571d322189246DaFA5ebDe1F4699F498',
    'usdc': 'ethereum:0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    'dai':  'ethereum:0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'wbtc': 'ethereum:0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
    'eth':  'coingecko:ethereum',  # native asset: DefiLlama uses this key, not a contract address
}

# Excluded per the data-availability finding above. Kept here (commented, not
# deleted) so the exclusion is visible and documented rather than silently
# dropped from the token list.
# 'rep': not covered by DefiLlama at any date (checked both historical and current price lookups)
# 'sai': deprecated single-collateral Dai; expected to be unavailable, not yet independently tested


def get_defillama_price(token: str, unix_timestamp: int) -> float:
    '''
    Fetch a single token's USD price at a given UNIX timestamp from DefiLlama.
    Returns None if no price is available (rather than raising), so callers
    can decide how to handle missing points (e.g. forward-fill, or drop).
    '''
    key = TOKEN_CONTRACTS[token]
    url = f'https://coins.llama.fi/prices/historical/{unix_timestamp}/{key}'
    response = requests.get(url)
    if response.status_code != 200:
        print(f'HTTP {response.status_code} retrieving price for {token} at {unix_timestamp}')
        return None
    data = response.json().get('coins', {})
    entry = data.get(key)
    if entry is None:
        print(f'No DefiLlama price data for {token} at {unix_timestamp}')
        return None
    return entry['price']


def make_usd_price_series(token: str, start_date: str, end_date: str) -> pd.Series:
    '''
    Build a daily USD price series for one token over [start_date, end_date]
    (inclusive), e.g. start_date='2020-02-01', end_date='2020-05-31').
    Makes one API call per day — DefiLlama has no documented rate limit for
    this free endpoint, but a small delay is added defensively to avoid
    hammering the service.

    Prints progress every 20 days, since a multi-month window means
    hundreds of sequential requests and can otherwise look like it has
    hung with no feedback.
    '''
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    prices = {}
    print(f'Fetching {token}: {len(dates)} days...')
    for i, date in enumerate(dates):
        ts = int(date.timestamp())
        price = get_defillama_price(token, ts)
        prices[date] = price
        if (i + 1) % 20 == 0:
            print(f'  {token}: {i + 1}/{len(dates)} days fetched')
        time.sleep(0.1)  # be polite to the free API
    print(f'Finished fetching {token}.')
    series = pd.Series(prices, name=token)
    series.index.name = 'date'
    return series


def load_manual_price_series(token: str) -> pd.Series:
    '''
    Load a manually-downloaded, pre-cleaned USD price series (currently REP
    and SAI — see clean_manual_prices.py and repo_verification_notes.md,
    Issue #12, for why these two tokens bypass DefiLlama entirely).

    Strips any timezone information from the index before returning, since
    the two manual sources came from different exports with inconsistent
    timezone handling (SAI's cleaned index carries a UTC offset, REP's does
    not) — leaving this unresolved would silently produce all-NaN rows when
    concatenated with the (timezone-naive) DefiLlama series.
    '''
    path = f'data/manual/{token}_usd_prices_cleaned.csv'
    series = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    series.index = series.index.tz_localize(None)  # drop tz info if present; no-op if already naive
    series.name = token
    return series


def cache_all_token_usd_prices(start_date: str, end_date: str, cache_dir: str = 'data/manual') -> None:
    '''
    Fetch (or load) each of the 8 tokens' USD price series ONCE and save to
    individual CSVs. This must be run once before get_exchange_rates_defillama
    is used, so that pairwise exchange rates (bat/zrx, usdc/dai, etc.) can be
    computed by dividing two cached USD series instead of re-fetching from
    DefiLlama for every one of the 20 pairs the original regression_runner
    iterates over (which would multiply the ~15-minute fetch time by ~7x).
    '''
    import os
    os.makedirs(cache_dir, exist_ok=True)
    for token in TOKEN_CONTRACTS.keys():
        out_path = f'{cache_dir}/{token}_usd_prices_cached.csv'
        if os.path.exists(out_path):
            print(f'{token}: already cached, skipping.')
            continue
        series = make_usd_price_series(token, start_date, end_date)
        series.to_csv(out_path)
    print('Done. (rep, sai use the existing manually-cleaned files and need no separate caching step.)')


def _load_cached_usd_series(token: str, cache_dir: str = 'data/manual') -> pd.Series:
    '''Load one token's USD price series from whichever cache it lives in.'''
    if token in ('rep', 'sai'):
        path = f'{cache_dir}/{token}_usd_prices_cleaned.csv'
    else:
        path = f'{cache_dir}/{token}_usd_prices_cached.csv'
    series = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
    series.index = series.index.tz_localize(None)
    return series


def get_exchange_rates_defillama(base_symbol: str, quote_symbol: str, limit: int = None) -> pd.DataFrame:
    '''
    Drop-in replacement for the original (now-broken) get_exchange_rates()
    in fetch_exchange_rates.py. Same call signature and same 'close'-column
    output shape, so it can be substituted directly in utils.py's
    make_ex_rate_and_interest_rate_df without changing any other code.
    `limit` is accepted but ignored (kept only for interface compatibility) —
    the cached series already covers the full sample window.
    '''
    base_prices = _load_cached_usd_series(base_symbol)
    quote_prices = _load_cached_usd_series(quote_symbol)
    rate = (base_prices / quote_prices).rename('close')
    df = rate.to_frame()
    df.index.name = 'date'
    return df
    '''
    Full 8-token version of make_exchange_rate_df: combines the 6 tokens
    fetched live from DefiLlama (bat, zrx, usdc, dai, wbtc, eth) with the 2
    tokens loaded from manually-cleaned local files (rep, sai), producing a
    single exchange-rate DataFrame against `quote_symbol`, matching the
    paper's original 8-token / 20-pair UIP analysis.

    Requires clean_manual_prices.py to have already been run once to
    produce data/manual/rep_usd_prices_cleaned.csv and
    data/manual/sai_usd_prices_cleaned.csv.
    '''
    manual_tokens = ['rep', 'sai']
    defillama_tokens = list(TOKEN_CONTRACTS.keys())
    all_tokens = defillama_tokens + manual_tokens

    # Get the quote currency's USD price series, from whichever source it belongs to
    if quote_symbol in manual_tokens:
        quote_prices = load_manual_price_series(quote_symbol)
    else:
        quote_prices = make_usd_price_series(quote_symbol, start_date, end_date)

    master_df = pd.DataFrame()
    for token in all_tokens:
        if token == quote_symbol:
            continue
        if token in manual_tokens:
            base_prices = load_manual_price_series(token)
        else:
            base_prices = make_usd_price_series(token, start_date, end_date)
        rate = base_prices / quote_prices
        rate = rate.rename(token)
        master_df = pd.concat([master_df, rate], axis=1, join='outer')

    # Restrict to the requested window — manual series may cover a wider range
    master_df = master_df.loc[start_date:end_date]
    return master_df
    '''
    Drop-in replacement for the original make_exchange_rate_df(quote_symbol, limit).
    Builds a DataFrame of {other_token}/{quote_symbol} exchange rates by
    fetching each token's USD price separately and dividing, since DefiLlama
    prices are always quoted in USD (there is no direct token-to-token
    historical endpoint).

    :quote_symbol: the currency to use as the quote currency (the "to" symbol)
    :start_date, end_date: sample window, e.g. '2020-02-01', '2020-05-31'
        (use the paper's original window to reproduce results; extend the
        range for the New Data / extension analysis)
    '''
    token_list = list(TOKEN_CONTRACTS.keys())
    quote_prices = make_usd_price_series(quote_symbol, start_date, end_date)

    master_df = pd.DataFrame()
    for token in token_list:
        if token == quote_symbol:
            continue
        base_prices = make_usd_price_series(token, start_date, end_date)
        # token/quote exchange rate = (token in USD) / (quote in USD)
        rate = base_prices / quote_prices
        rate = rate.rename(token)
        master_df = pd.concat([master_df, rate], axis=1, join='outer')
    return master_df