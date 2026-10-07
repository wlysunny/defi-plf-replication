# Criteria for comparing the liquidity and concentration results with the paper

Written on 2026-10-07, before the outputs of the notebooks concerned were compared with the paper. The notebooks have been run before to check that they execute; their outputs were not compared with the paper's figures or numbers.

Both comparisons are reproductions in the narrow sense: the authors' code applied to the authors' data, after the compatibility changes recorded in REPLICATION.md.

## Fund concentration (paper, Section 5.1.3 and Figure 6)

The paper reports that on 2020-06-04 the three largest accounts held 50.3 per cent of locked DAI, 60.0 per cent of ETH and 47.3 per cent of USDC on Compound.

For each market, the share held by the three largest accounts is read from the output of `notebooks/compound/compound-wealth.ipynb` (or, if the notebook does not print it, computed from the data the notebook plots, without changing the notebook's method).

- Exact reproduction: equal to the paper's value when rounded to one decimal place.
- Numerical reproduction: within 1 percentage point.
- Otherwise: not reproduced; the difference is reported together with any identified cause.

The verdict is given separately for each of the three markets.

## Liquidity across protocols (paper, Section 5.1, Figures 2 to 5)

The paper's claims are qualitative: (a) ETH markets keep high liquidity on all three protocols; (b) DAI and USDC markets have repeated periods with utilisation above 80 and 90 per cent; (c) such periods are shared across protocols, in particular for dYdX and Aave between January and mid-March 2020; (d) DAI utilisation reached or exceeded 100 per cent on Compound and dYdX but not on Aave.

The figures produced by the authors' code are placed next to Figures 2 to 5 of the paper and compared on these four statements and on whether the shaded periods (80 to 90 per cent, above 90 per cent, at or above 100 per cent) fall on the same dates, to within a day.

- Reproduced: all four statements hold in the regenerated figures and the shaded periods coincide.
- Partly reproduced: the statements hold but some shaded periods differ; the differences are listed.
- Not reproduced: any of the four statements fails.

This is a visual comparison and is reported as such; no numerical tolerance is claimed.


## Amendment 1 (2026-10-07, written before `notebooks/exploration.ipynb` was run or its stored outputs read)

A search of the whole repository found the code for the cross-protocol results in `notebooks/exploration.ipynb`, which an earlier search had missed because it covered only subfolders of `notebooks/`. Judging from its function names and code, the notebook computes the median locked funds (Table 2) and plots liquidity (`plot_liquidity`, apparently Figures 2 to 4), utilisation across protocols (`plot_utilization`, `plot_liquidity_util`, apparently Figure 5) and the average utilisation and borrow rate by market (apparently Figure 1); the mapping is confirmed when the notebook is run. The comparison of Figures 2 to 5 above therefore applies to the figures this notebook produces. Two comparisons are added:

- **Table 2** (median total supply in millions of USD, to 7 May 2020): for each of the 15 non-empty cells (Compound 5, Aave 7, dYdX 3), exact reproduction if equal at two decimal places; numerical reproduction if within 5 per cent of the paper's value; otherwise not reproduced. The verdict is reported cell by cell and as a count. The tolerance is wider than for the concentration shares because the conversion to USD depends on the prices in the notebook's `usd_markets`, which may differ from those used for the paper.
- **Figure 1**: visual comparison of the regenerated figure with the paper's; reproduced if every market shows the same ordering of the three protocols in average utilisation and in average borrow rate.

If the notebook stores outputs from the authors' own run, they are compared with both the paper and the regenerated outputs, and any difference between the stored outputs and the paper is reported separately, since it would indicate that the paper was produced from a different state of the code or data.


## Amendment 2 (2026-10-07, written after `compound-wealth.ipynb` was run and before any share was computed)

The notebook does not print the shares held by the largest accounts; it only plots cumulative distributions, whose y-axis labels are misplaced under the current version of matplotlib (the notebook sets tick labels without fixing tick positions, and matplotlib warns that they may be mislabelled). The shares are therefore computed by `scripts/reproduce_concentration.py`, which executes the notebook's cells that load events and compute balances unchanged and applies the same rule as the plotting function (`utils.plot_cumulative_hist` keeps positive balances only): the share of the three largest positive balances in the sum of positive balances.

The paper states the date of the distribution as 2020-06-04, whereas the committed event logs extend beyond it (to August 2020 for cDAI). Two versions are reported:

1. **As the notebook runs**: all committed events. This is what the authors' code produces today.
2. **At the paper's date**: only events in blocks up to the end of 2020-06-04 UTC, with block times interpolated from `data/derived/eth_block_times_sampled.csv`. This is the comparison with the paper; the verdict in the criterion above (exact at one decimal, numerical within one percentage point) is applied to this version.

As a secondary check, the number of accounts with a positive balance is compared with the right end of the x-axis of Figure 6, read approximately from the paper.
