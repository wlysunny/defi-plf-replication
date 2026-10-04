# Replication of Gudgeon et al. (2020)

This repository contains a replication of the following paper:

Lewis Gudgeon, Sam M. Werner, Daniel Perez, and William J. Knottenbelt. 2020. DeFi Protocols for Loanable Funds: Interest Rates, Liquidity and Market Efficiency. In Proceedings of the 2nd ACM Conference on Advances in Financial Technologies (AFT '20), pages 92-112. https://doi.org/10.1145/3419614.3423254

The original code and data were published by the authors at https://github.com/danhper/defi-plf-analysis. The replication was carried out by Luyao Wang at Macquarie University as part of COMP8240 Applications of Data Science (2026) and is currently in progress. The authors' original README is retained unchanged in README.md, and the original paper should be cited in any work that makes use of this repository.

## Repository structure

The `master` branch contains the authors' code without modification and serves as the baseline for comparison. The `replication-fixes` branch, which is the default branch, contains the original code together with the changes required to execute it in a 2026 computing environment. All modifications can be inspected by comparing the two branches:
https://github.com/wlysunny/defi-plf-replication/compare/master...replication-fixes

## Modifications to the original code

The original code was written in 2020, and executing it in the current environment required four categories of modification.

1. Dependency changes. Several libraries on which the code depends, including NumPy, pandas, matplotlib, web3.py and eth_abi, have since renamed or removed functions. Examples include the replacement of `np.NaN` with `np.nan`, `fillna(method=...)` with `.ffill()`, and `fig.gca(projection=...)` with `fig.add_subplot(projection=...)`. These changes do not alter the computations performed.

2. Author-specific paths. Absolute file paths referring to the original authors' machine were replaced with paths relative to the repository.

3. Replacement of the exchange-rate data source. The Uncovered Interest Parity (UIP) analysis retrieves historical exchange rates from the CryptoCompare API, which now requires a paid key, while freely available alternatives restrict historical data to the most recent 365 days and therefore do not cover the sample period. Exchange rates were instead reconstructed from the DefiLlama historical price endpoint (`compounds_research/compound/fetch_exchange_rates_defillama.py`). Prices for REP and SAI, which DefiLlama does not provide, were obtained manually and cleaned using `clean_manual_prices.py`; the raw downloads are kept unmodified in `data/manual/raw/` and the cleaned series are stored in `data/manual/`.

4. Unresolved retrieval of dYdX data. The dYdX notebook retrieves on-chain events using `create_filter`, a stateful filtering method that free Ethereum node providers such as Alchemy do not support. Requests therefore fail with an HTTP 400 error. A reimplementation based on `eth_getLogs` is planned but has not yet been completed.

## Differences in the exchange-rate data

The replacement of the exchange-rate source introduces three differences from the original analysis, each of which may affect the UIP results independently of the method.

First, the original code requested direct pair prices from CryptoCompare, for example the BAT/ETH market price. DefiLlama provides prices in US dollars only, so each pair exchange rate is computed here as a cross rate, dividing the US dollar price of the base token by that of the quote token. For thinly traded tokens, cross rates may deviate from direct market prices.

Second, the REP and SAI series come from different providers than the other tokens and were cleaned manually.

Third, the manually obtained REP price series has 10 missing days within the sample period, six of which fall between 12 and 26 October 2019. These days were not imputed; observations on missing days are dropped when the price and interest-rate series are merged, which reduces the number of observations for REP pairs.

## Sample period

The UIP regressions use the intersection of the exchange-rate series and the Compound interest-rate series, which cover 2 April 2019 to 8 May 2020. In the original code the exchange-rate request extends 1,000 days back from the date of execution, so the regression sample is determined entirely by the interest-rate data. In the replacement pipeline the exchange-rate window is set explicitly, and it is defined in a single place (`UIP_SAMPLE_START` and `UIP_SAMPLE_END` in `fetch_exchange_rates_defillama.py`) from which the cleaning script also reads.

An earlier run of the replication used an exchange-rate window of February to May 2020, which is the sample period of the paper's liquidity analysis rather than its UIP analysis. Because the regression sample is the intersection of the two series, this silently reduced the sample to approximately 95 daily and 13 weekly observations per pair, compared with approximately 390 and 56 in the paper. The smaller sample lowered the power of the hypothesis tests and produced fewer rejections of UIP. This error was identified by comparing the number of observations with the authors' saved notebook output, and the window has been corrected.

## Computational environment

The replication was performed on macOS (Apple Silicon) within the Anaconda base environment, using Python 3.14.6, NumPy 2.4.6, pandas 3.0.3, matplotlib 3.11.0, statsmodels 0.14.6 and web3 7.16.0. The complete list of installed packages is recorded in `environment_snapshot.txt`. Large data files are stored using Git LFS, and the VECM analysis in `notebooks/VECM.do` requires Stata.

## Reproducing the results

The environment can be recreated as follows:

```bash
git clone https://github.com/wlysunny/defi-plf-replication.git
cd defi-plf-replication
git lfs pull
conda create --name defi-plf --file environment_snapshot.txt
conda activate defi-plf
```

The exchange-rate inputs are then prepared from the repository root. The cleaning script produces the REP and SAI series from the raw downloads:

```bash
python scripts/clean_manual_prices.py
```

The DefiLlama prices for the remaining tokens are fetched and cached by the second cell of `notebooks/compound/5_uip_compound.ipynb`, which calls `cache_all_token_usd_prices` with the sample window defined above. An existing cache is reused only if it covers the full window.

The notebooks in `notebooks/compound/` should then be executed in numerical order, followed by `compound-wealth.ipynb` and `notebooks/aave/deposits.ipynb`.

## Current replication status

The notebooks covering Compound's interest-rate models, liquidity and rate dynamics (`1_first_look` to `4_cdai_dynamics`), the wealth concentration analysis (`compound-wealth`) and Aave deposits (`aave/deposits`) execute successfully. Their outputs have not yet been systematically compared with the figures reported in the paper.

The UIP regression (`5_uip_compound`) executes successfully. Results from the earlier run with the truncated sample are not comparable with the paper for the reason given above, and the regressions are being re-run with the corrected sample period. The regression code itself is unchanged from the original apart from pandas compatibility adjustments, so any remaining differences can be attributed to the exchange-rate data.

The dYdX analysis cannot yet be executed for the reason described above, and the VECM analysis has not yet been run.

[To be completed: pre-specified criteria for judging the success of each replicated result, and the comparison of the corrected UIP results with the paper.]

## Observations on the original code

The UIP notebook (`5_uip_compound.ipynb`) omits the SAI-REP token pair through an unexplained `continue` statement, and this omission is not mentioned in the paper. By contrast, the exclusion of WBTC from the UIP analysis is documented in a footnote of the paper, which attributes it to data quality issues.

The paper reports hypothesis tests at the 1% significance level, whereas the notebook classifies each pair as "UIP holds" or "UIP does not hold" using a 5% threshold. Counts of rejected pairs should therefore be taken from the reported p-values rather than from the notebook's printed classification. For the weekly supply-rate regression, the paper reports 12 rejections at the 1% level, which corresponds to the p-values after rounding to two decimal places; the unrounded p-values give 13 rejections at the 1% level, and the notebook's 5% classification gives 14.
