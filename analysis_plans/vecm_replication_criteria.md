# Replication criteria for the VECM analysis (Section 6.2, Tables A6–A7)

Written before `notebooks/VECM.do` was run in this project.

## Setup
- Software: StataNow/MP 19.5 for Mac (Apple Silicon), revision 08 Apr 2025. The authors' version is unknown; the script has no `version` statement.
- Inputs: the authors' committed files `data/stata/interest_rates_dai.csv` and `interest_rates_usdc.csv` (last changed in commit 27d6447), unchanged.
- Code: a copy of `notebooks/VECM.do` at `scripts/vecm_replication.do` in which only file paths are changed and a log is added. Model specifications (lags, rank, variable order) are kept as in the original.
- Dependency: `estout` (SSC), required by `eststo`/`esttab` but not declared by the authors.

## Targets (paper, Appendix Tables A6 and A7)
- DAI: N = 116, lags 5, rank 2; adjustment coefficients and long-run coefficients as in Table A6.
- USDC: N = 119, lags 3, rank 2; as in Table A7.

## Criteria (applied separately to DAI and USDC)
1. **Sample**: N equals the paper's. Otherwise the comparison stops and the cause is investigated.
2. **Numerical reproduction**: every adjustment coefficient (6 per currency) and every estimated long-run coefficient and constant equals the paper's value when rounded to the number of decimals the paper reports.
3. **Inferential reproduction** (if 2 fails): every coefficient has the same sign and the same significance stars as in the paper.
4. Otherwise: **not reproduced**; the differences are reported.

## Recorded but not judged
- Johansen trace test: the rank it selects at the 5% level, compared with the paper's statement of "at most two" cointegrating relationships.
- `varsoc`: the lag length each criterion suggests, compared with the lags used.
- Diagnostics: whether all companion-matrix roots lie inside the unit circle (`vecstable`), the LM test for residual autocorrelation (`veclmar`), and the normality test (`vecnorm`).

## Post-hoc note (2026-10-27, written after the run)

This note does not change the criteria or the verdicts. DAI meets criterion 2 (numerical reproduction). USDC meets criterion 3 but not criterion 2: the constant of the second cointegrating equation is 0.0028394, which rounds to 0.00284, against 0.00283 in Table A7.

The tables produced by the authors' `esttab` commands (`results/vecm/stata_results_*_original.tex`) contain the adjustment coefficients, the lagged differences and the short-run constants, but no long-run coefficients. Tables A6 and A7 in the paper omit the lagged differences and short-run constants and add the long-run coefficients, so the long-run part of each table was not produced by the committed code and was presumably transcribed by hand. Truncation of 0.0028394 would give 0.00283; this is an interpretation, not established.
