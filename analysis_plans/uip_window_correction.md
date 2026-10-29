# Correction of the UIP sample window: predictions written before the re-run

Written and committed before the corrected notebook was run. This is a post-hoc correction: the problem it addresses (every weekly regression has one observation fewer than the authors') was found after the results had been compared. The values of the corrected regressions have not been seen.

## The problem

The exchange-rate window chosen for this replication ends on 9 May 2020 (`UIP_SAMPLE_END` in `compounds_research/compound/fetch_exchange_rates_defillama.py`). The Compound interest-rate data end on 7 or 8 May 2020, depending on the token. Resampled weekly with `resample('W')`, their last week is labelled Sunday 10 May. `make_ex_rate_and_interest_rate_df` joins the daily exchange rate to the weekly rates by date and drops incomplete rows, so the week of 10 May has no exchange rate and is dropped. The regression uses the next week's change in the exchange rate, so the week of 3 May is also lost, while 10 May itself has no following week: one observation fewer in every weekly regression. The authors retrieved exchange rates up to the date they ran the code, so their sample was limited only by the interest-rate data.

## The correction

1. `UIP_SAMPLE_END` is changed from `2020-05-09` to `2020-05-10`. This is the only change to the window. The start (`2019-04-01`) is unchanged.
2. `cache_all_token_usd_prices` previously downloaded the whole window again whenever the cache did not cover it. It is changed so that an existing cache file which covers the window without gaps up to an earlier end date is extended by downloading only the missing days at the end and appending them to the file. Existing cached values are not downloaded again or rewritten, so that the correction cannot also change previously used prices. Before anything is written, the function checks that the file's dates are unique, sorted, timezone-free whole days without gaps, and that a finite positive price was returned for every new day. All checks are completed before the file is opened for appending, and a failed check leaves the file unchanged; an existing file is never overwritten. An interrupted write could leave a partial append. The check below verifies the committed prefix, the number of added records, their date and that the price is a finite positive number, but it cannot detect a price that was cut short yet still forms a valid number.
3. `scripts/clean_manual_prices.py` is re-run; it takes the window from the same constant and rebuilds the REP and SAI series from the unchanged raw downloads in `data/manual/raw/`.
4. Before the updated caches are committed, `scripts/verify_uip_cache_append.py` (committed with this note) compares each of the six files with its committed version: the committed bytes must be an unchanged prefix of the new file, exactly one record dated 2020-05-10 with a finite positive price must have been added, and the committed version must be real content rather than a Git LFS pointer. It exits with an error if any check fails.

## Predictions

1. Each of the six DefiLlama cache files gains exactly one data record, dated 2020-05-10, with a finite positive price. The bytes of the committed file are an unchanged prefix of the new file (checked against the version in git).
2. In `rep_usd_prices_cleaned.csv` and `sai_usd_prices_cleaned.csv`, which `clean_manual_prices.py` rewrites in full, the price for every date already present is numerically identical. At most records for 9 May (REP only, which currently has none) and 10 May 2020 are added; the dates actually added are reported.
3. Daily regressions (40 tests): the number of observations, coefficients and p-values are identical to the current output, because no interest-rate row exists after 8 May 2020. Identical coefficients and p-values in all reported digits are taken as evidence that the samples are unchanged; the observation dates of each regression are not reconstructed separately.
4. Weekly regressions (40 tests): the number of observations increases by exactly one in every test in which both tokens have exchange rates on 3 and 10 May 2020 and the interest rates of the week of 3 May are available for both tokens. For the pairs containing neither DAI nor REP, it then equals the authors'. The weekly coefficients and p-values may change slightly.

If a prediction fails, the cause is investigated and documented before any further change. Both the previous and the corrected comparison remain in the repository history; the README reports the corrected one and states the change.

## What the correction does and does not establish

The correction removes an identified truncation at the end of the weekly sample, a matter of aligning dates. It does not make the weekly series a better measure of the economic relationship: the week labelled 10 May contains interest rates only up to 7 or 8 May, as it would have in the authors' run under the same code. Matching the authors' number of observations does not show that the observation dates or the exchange-rate values are the same as theirs. Remaining differences in the coefficients therefore cannot be attributed wholly to the replacement exchange-rate source.

## Results (appended after the re-run, 29 October 2026)

The prediction note, code change and verification script were committed in `0eb5c28`; the updated prices in `5bd90bb`. Before the notebook could be executed, 17 duplicate copies of the cell tag `outputPrepend` (added by an editor) were removed from the notebook metadata, because the current `nbconvert` rejects duplicate tags; no code or output was changed by this.

| Prediction | Outcome |
|---|---|
| 1. One record, 10 May 2020, appended to each DefiLlama cache; committed bytes unchanged | Holds: all six files pass `scripts/verify_uip_cache_append.py` |
| 2. REP and SAI: existing prices unchanged; at most 9 and 10 May added | Holds: existing dates and prices identical in both; 10 May added to both; REP has no price for 9 May in the raw download, so none was added |
| 3. Daily regressions identical | Holds: observations, coefficients and p-values identical in 40 of 40 tests |
| 4. Weekly regressions gain one observation; equal to the authors' for pairs without DAI or REP | Holds: +1 in 40 of 40 tests; the 20 tests on pairs without DAI or REP now have the authors' number of observations |

**Consequences for the comparison with the authors (not predicted).** Agreement in the test decision at the 1% level is unchanged (77 of 80), but at the 5% level it falls from 77 to 74 of 80. In three weekly tests the authors' p-values were close to 5% (BAT–ZRX borrow 0.102, ZRX–DAI borrow 0.058, ZRX–DAI supply 0.067); before the correction ours were also above 5% (0.072, 0.102, 0.093), and after it they are below (0.044, 0.026, 0.0496). Coefficients within 5% of the authors' rise from 8 to 14 of 80 and agreement in sign from 67 to 69 of 80.

**Exploratory observation.** The restored observation, the week of 3 May 2020, is influential in some weekly regressions. For ZRX–USDC the coefficient changes from +0.091 to −0.615 (borrow; authors −0.562) and from +0.096 to −0.824 (supply; authors −0.820) when this single week is added. Its influence was not examined before the re-run and is reported as an observation, not as a pre-specified result.
