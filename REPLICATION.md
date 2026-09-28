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

3. Replacement of the exchange-rate data source. The Uncovered Interest Parity (UIP) analysis retrieves historical exchange rates from the CryptoCompare API, which now requires a paid key, while freely available alternatives restrict historical data to the most recent 365 days and therefore do not cover the 2020 sample period. Exchange rates were instead reconstructed from the DefiLlama historical price endpoint (`compounds_research/compound/fetch_exchange_rates_defillama.py`). Prices for REP and SAI, which DefiLlama does not provide, were obtained manually and cleaned using `clean_manual_prices.py`; the resulting files are stored in `data/manual/`.

   This modification has a direct bearing on the interpretation of the results. Because the UIP analysis is performed on reconstructed rather than original exchange-rate data, any discrepancy between the replicated and published results may reflect the change of data source rather than a failure of the method itself.

4. Unresolved retrieval of dYdX data. The dYdX notebook retrieves on-chain events using `create_filter`, a stateful filtering method that free Ethereum node providers such as Alchemy do not support. Requests therefore fail with an HTTP 400 error. A reimplementation based on `eth_getLogs` is planned but has not yet been completed.

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

[To be completed: the procedure for generating the exchange-rate data, including the order in which `fetch_exchange_rates_defillama.py` and `clean_manual_prices.py` are executed and whether they must be run before `5_uip_compound.ipynb`.]

The notebooks in `notebooks/compound/` should then be executed in numerical order, followed by `compound-wealth.ipynb` and `notebooks/aave/deposits.ipynb`.

## Current replication status

The notebooks covering Compound's interest-rate models, liquidity and rate dynamics (`1_first_look` to `4_cdai_dynamics`), the wealth concentration analysis (`compound-wealth`) and Aave deposits (`aave/deposits`) execute successfully. Their outputs have not yet been systematically compared with the figures reported in the paper.

The UIP regression (`5_uip_compound`) executes successfully for all four combinations of frequency and rate type. At the daily frequency, UIP is rejected for 19 of 20 token pairs, compared with 20 of 20 in the paper. At the weekly frequency, it is rejected for 9 of 20 pairs, compared with 12 of 20 in the paper. The replicated results therefore reproduce the qualitative pattern reported by the authors, namely strong rejection at the daily frequency and more mixed evidence at the weekly frequency, although the weekly results differ in the number of rejections.

The dYdX analysis cannot yet be executed for the reason described above, and the VECM analysis has not yet been run.

[To be completed: pre-specified criteria for judging the success of each replicated result.]

## Observations on the original code

The UIP notebook (`5_uip_compound.ipynb`) omits the SAI-REP token pair through an unexplained `continue` statement, and this omission is not mentioned in the paper. By contrast, the exclusion of WBTC from the UIP analysis is documented in a footnote of the paper, which attributes it to data quality issues.
