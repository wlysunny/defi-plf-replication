# Pre-specified criterion: re-reading the on-chain datasets from a second provider

Written before the check was run, and committed together with the script that implements it (`scripts/second_provider_check.py`). The script refuses to run unless both files are committed and unmodified. Each result file records the SHA-256 of this criterion, of the script that produced it (the primary evidence of the version actually run) and of the three input files, together with the repository commit at the time.

All on-chain data in `data/onchain/` and the rate-model parameters in `data/aave_v3/aave_v3_rate_params_daily.csv` were read through one provider (Alchemy). Agreement with the blockchain was checked so far only through that provider, so an error in that provider's archive data, or a transient error during collection, would not have been detected.

Before this criterion was written, a single query was used to confirm that the second provider serves historical state: the ETH balance of the cETH contract at block 9,000,000 was identical from both providers. No values from the datasets were compared.

## Provider

Infura (Ethereum mainnet), read through the environment variable `ETH_RPC_URL_2`. Only the host name is recorded.

## Sample

A stratified random sample is drawn with Python's `random.Random(20261029)`, without replacement within each dataset:

- 15 rows from `data/onchain/cdai_panel.csv` (every 6,000 blocks, 2019–2025);
- 5 rows from `data/onchain/cdai_panel_dense_2020.csv` (every 300 blocks, 2020);
- 10 rows from `data/aave_v3/aave_v3_rate_params_daily.csv`, excluding rows whose strategy is recorded as "not listed" or empty.

Because the sample depends on the order of rows as well as on the seed, the SHA-256 of each input file is recorded, and the main run refuses to start if the input files differ from those used in the self-check. The samples are not stratified by year, asset or interest-rate regime. The two cDAI panels may contain the same block.

## What is compared

The sampled rows are re-read at the same block numbers through the second provider, with the same contract calls and decoding functions as the original collection.

- **cDAI**: the complete output of the original function `sample_block()` in `scripts/collect_onchain_cdai.py`, unchanged, is compared with the stored row, column by column.
- **Aave V3**: the reading sequence of `scripts/collect_aave_v3_rate_params.py` is repeated for the sampled asset and block, and the following columns are compared: `strategy`, `strategy_version`, `pool_currentVariableBorrowRate`, the four rate-model parameters (`irm_optimalUsageRatio`, `irm_baseVariableBorrowRate`, `irm_variableRateSlope1`, `irm_variableRateSlope2`), and the four validation columns (`val_*`). Validation columns are compared only where they are populated in the stored file. Because they are populated only on some days, the sample may contain few or no such rows; the result file reports the number of sampled Aave rows, and of values, in which validation columns were compared. The other columns (`symbol`, `asset`, `sample_utc`, `block`, `block_timestamp`), the other fields returned by `getReserveData`, and the schedule on which validation columns were collected are not checked.

Values are compared as the text stored in the CSV files. Because the same decoding functions produce both, integers and addresses are represented in the same way; any difference in representation counts as a difference.

## Self-check

Before the main run, one row from each of the three strata (the first drawn in each) is re-read through the original provider. Any difference halts the procedure: the script exits with an error and the main run refuses to start until a self-check has passed with the same criterion, script and input files. A failed self-check is investigated and documented before the comparison code is corrected and the self-check repeated.

The self-check detects problems in the comparison code, such as formatting. Passing it does not establish that the original collection code is correct.

## Decision

- **Pass**: every compared field is identical in all 30 rows.
- **Fail**: at least one compared field differs, in a run made after a passed self-check.
- **Incomplete**: a required query cannot be completed (for example a timeout or an error from the provider), so that one or more rows cannot be compared. An incomplete check is not counted as a pass; the affected rows and errors are recorded. Only network and HTTP failures of a query, raised as `requests` exceptions, are classified this way; a query failure that the collection functions report as another kind of error stops the script as described below.

Fail takes precedence over Incomplete: if any completed comparison identifies a difference, the verdict is Fail, even when other rows could not be compared.

Any other error (for example an error in the comparison code, or an unknown interest-rate strategy interface) stops the script without a verdict. The error, and the rows already printed, are documented; the cause is corrected, and the self-check and the main run are repeated in full.

All differences are reported with both values. The stored data are not changed as part of this check. Investigations of any difference are documented separately and do not change the verdict.

## Limitations recorded in advance

- Both providers are commercial Ethereum node operators. Agreement is evidence that the sampled values do not depend on the provider; it does not independently validate the Ethereum client software that both may run.
- The same collection and decoding functions are used for both providers. Errors in the choice of contract call, field mapping, units or parsing would be repeated identically and remain undetected. The correctness of the collection code rests on other tests (for example, rates computed from the recorded parameters agree with the rates read from the contract).
- The 30 rows are a stratified spot check (15, 5 and 10 rows in three datasets), not 30 independent draws from one population, and provide no uniform statistical guarantee on the overall error rate. Rare errors, and errors concentrated in particular periods, assets or regimes, may be missed.
- The check concerns the sampled blocks only. It does not establish that the sampling grids captured every transient on-chain event.
- For Aave V3 only the columns listed above are checked; derived variables, timestamps and the completeness of the validation schedule are not reconstructed.
- A pass supports the reproducibility of the selected stored values across providers. It does not establish the correctness or completeness of either dataset as a whole.
