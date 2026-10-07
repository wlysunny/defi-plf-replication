# Reproduction of Section 5.1: Table 2 and Figures 1 to 5

Criteria: `analysis_plans/reproduction_liquidity_wealth_criterion.md` (a655959) and its Amendment 1 (7c31b7a), both committed before the outputs were compared. Outputs: `scripts/reproduce_exploration.py`, `results/reproduction_table2.csv`, `figures/reproduction/`. Comparison made on 2026-10-07 against the arXiv version (2006.13922v3).

## How the outputs were produced

The functions in `notebooks/exploration.ipynb` were executed unchanged and called with the arguments corresponding to the paper. Two changes were needed for the code to run:

- `aave = analyze_aave.load_data()` was restored. This line was present in the notebook in 48ca0d2, 8b00d27 and cfcbabf (17 to 29 May 2020) and was removed in f4f9d28 (31 August 2020), while six cells that use `aave` were kept. The final version of the notebook therefore raises `NameError` when run from a fresh kernel.
- `DataFrame.append`, removed in pandas 2, was replaced with `pd.concat` in `analyze_aave.load_data` and `fetch_compound` (ee0711e).

## Table 2

Under the pre-specified rule, 13 of 15 cells are reproduced exactly (equal at two decimal places): all five Compound cells, all seven Aave cells and dYdX USDC. dYdX ETH and dYdX DAI are not reproduced: the values obtained are larger than the paper's by a factor of about 10^12.

The cause is in `analyze_dydx.load_dydx_market`, which divides all token amounts by the same constant. In 8b00d27 the constant was 10^18, correct for DAI and WETH (18 decimals) but not for USDC (6 decimals); in f4f9d28 it was changed to 10^6, correct for USDC but not for DAI and WETH. No committed version of the function is correct for all three tokens.

Post hoc, and without changing the verdict above: dividing the two cells by 10^12 gives 4.638 for DAI (paper 4.64, equal at two decimals) and 19.142 for ETH (paper 19.41, a difference of 1.4 per cent). The reason for the ETH difference is not known; the two values share their digits in a different order, but there is no evidence to decide whether the paper's value is a transcription error.

## Figure 1

Reproduced. For every market, the ordering of the three protocols in average utilisation and in average borrow rate is the same as in the paper, and the plotted values agree to the resolution of the figure. In both figures the dYdX marker for DAI is hidden behind the Compound marker, which is drawn later. The legend is placed differently (upper left here, upper right in the paper); the code does not fix its position.

## Figures 2 to 5

Reproduced on the criterion's four statements:

| Statement | Result |
|---|---|
| (a) ETH markets keep high liquidity on all three protocols | holds: no shading in any panel of Figure 2 |
| (b) DAI and USDC markets have repeated periods with utilisation above 80 and 90 per cent | holds in Figures 3 and 4 |
| (c) these periods are shared across protocols, in particular dYdX and Aave between January and mid-March 2020 | holds for DAI and USDC |
| (d) DAI utilisation reached or exceeded 100 per cent on Compound and dYdX but not on Aave | holds in Figure 5 |

The shaded periods coincide with those in the paper panel by panel, as far as can be read from the figures. At the scale of the printed figures one day is about a millimetre, so agreement within one day, as the criterion specifies, cannot be confirmed by eye; the statement is limited to agreement at the resolution of the figures. Since the shading is a deterministic function of the committed data and the fixed thresholds, identical shading is expected if the data are unchanged.

Differences that do not affect the content:

- The dYdX panels for ETH and DAI have y-axes scaled by 10^12 (the divisor described under Table 2). The paper's figures show correct amounts for ETH, DAI and USDC at the same time, which again no committed version of the loader produces.
- Panel titles in Figure 5 read "Dai" in the code and "DAI" in the paper; date labels are formatted differently.
- In `plot_illiquidity` the Aave panel is shaded using the row index rather than the date column. Aave DAI utilisation never reached 100 per cent, so no shading is drawn and the error has no effect.
- In `plot_illiquidity` and `plot_liquidity_market` the line that limits dYdX data to 7 May 2020 assigns to a misspelt variable (`dydf_df`), so the dYdX series is not truncated. No difference from the paper is visible at the scale of the figures.

## What this implies

The paper's Section 5.1 results are reproduced from the authors' data and code. The differences in units, titles and formatting indicate that the published figures and Table 2 were produced from a state of the code that is not identical to any committed version; the repository's final version does not run as stored and gives wrong units for two dYdX markets.
