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
