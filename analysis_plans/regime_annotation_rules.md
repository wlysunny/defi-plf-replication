# Annotation rules for the cDAI interest-rate regimes

Written before `annotate_regimes.py` was run. The annotation is descriptive: it records, for each of the eleven parameter regimes in the authors' table (`simulator/engine/dai_rate_params.py`, `PARAM_REGIME_NUMS`), facts that the on-chain panels and the repository's event log can establish. It is not a hypothesis test. Some of the data involved (the observed rate series, the on-chain rates in a few regimes) were already examined in the exploratory analyses of 2 October; the rules are fixed in advance so that labels and thresholds are not adjusted after the labels are seen.

## Inputs

- Authors' regimes: start times and parameters in `PARAM_REGIMES` and `PARAM_REGIME_NUMS`. Regime *i* runs from its start to the start of regime *i*+1; the last regime runs to the end of the observed series.
- On-chain state: `data/onchain/cdai_panel.csv` (one sample every 6,000 blocks, about 22 hours in 2020) and `data/onchain/cdai_panel_dense_2020.csv` (every 300 blocks, about one hour, 2020-02-21 to 2020-04-21), combined and ordered by block.
- Observed rates: `data/compound/cdai.pkl` (`borrow_rates`), resampled to hourly means.
- Liquidations: `LiquidateBorrow` events in `data/compound/events/cdai.jsonl.gz`.
- Block-time conversion: `data/derived/eth_block_times_sampled.csv` (median error 112 seconds).

## On-chain changes

A change is recorded between two consecutive samples whenever any of the following differs: the interest-rate model address, its base rate, multiplier, jump multiplier or kink, or cDAI's reserve factor. The time of the change is known only to lie in the interval between the two samples. Each change is typed:

- **New model contract**: the model address changed (a governance action replacing the model).
- **In-model parameter update**: the address is unchanged but a model parameter changed.
- **Reserve factor change**: only the reserve factor changed (a governance action on cDAI).

A change may have more than one type.

## Labels for each regime

1. **Matching on-chain change** (regimes 1 to 10). The author's start time is *consistent* if it lies within the interval of an on-chain change. Otherwise the nearest on-chain change within 7 days is reported with the signed difference in days (interval midpoint minus author's time); if there is none, the label is *no on-chain change within 7 days*. No further tolerance is applied: the interval already reflects the sampling resolution.
2. **Source of the change**: the type of the matching on-chain change, or *not determined* if there is none.
3. **Parameters match the chain**: for each model parameter given by the authors, whether it equals the on-chain value in every sample inside the regime, after excluding samples within the interval of the change at its start. Parameters the authors do not give, or the chain does not expose, are not compared.
4. **Reliability of the observed series**: the median absolute difference between the observed borrow rate (hourly mean nearest to each sample) and the on-chain borrow rate (per-block rate × 2,102,400), over the samples inside the regime. The series is labelled *reliable* if the median is at most 0.25 percentage points, otherwise *unreliable*. The threshold is the band used to define "near the kink rate" in the exploratory analysis of 2 October, so a series that misses the chain by more than this could misplace a rate relative to the kink. The median and the number of samples are reported.
5. **Liquidations**: the number of `LiquidateBorrow` events with a block number inside the regime, after converting the regime's start and end times to blocks.

On-chain changes that fall inside a regime and match none of the authors' start times are listed separately.

## Limitations recorded in advance

- Outside the dense period, sampling about every 22 hours locates changes only to within roughly a day, and two changes inside one interval appear as one.
- Labels 1 and 2 depend on the panels detecting the change; a parameter change that is reversed between two samples is invisible.
- The reliability threshold is a judgement. The median difference itself is reported so that readers can apply another threshold.
- Times converted to blocks carry the error of the block-time table, which is small relative to regime lengths.
- Regime 0 uses an earlier model type whose parameters are partly given in a different form (`jump` rather than a jump multiplier); only parameters with the same meaning are compared.

## Post-hoc note (2026-10-03, written after the annotation was run)

This note does not change the rules or the reported labels. It records a weakness in label 1 found when the output was read.

When an author's start time lies inside no change interval, the rule takes the nearest on-chain change within 7 days, without checking the type of the change and without preventing two regimes from being matched to the same change. For regime 10 this selects the in-model update of about 21 April 2020 (−5.4 days), which is also the change matched to regime 9. The on-chain change that introduces the parameters the authors give for regime 10 is the new model contract of 2 to 3 May 2020 (about +5.6 days), which the output lists among the changes that match no regime. Label 3 for regime 10 (multiplier does not match) is consistent with this reading: between the authors' date and early May the chain still applied the earlier parameters.

A better rule would match each regime to the change whose resulting parameters equal the authors' parameters. That rule was not specified in advance and is not applied here; the reading above is reported as an interpretation.

## Post-hoc note 2 (2026-10-06, written after an exploratory check)

This note does not change the rules or the reported labels. It records that label 4 (reliability of the observed series) compares two quantities that are not on the same basis.

The rule compares the original series with the on-chain borrow rate expressed as a simple annual rate (rate per block × 2,102,400). An exploratory check (`scripts/exploratory_apy_check.py`, results in `results/exploratory/apy_check.json`) indicates that the original Compound API reported compounded annual yields. In regime 6, reading the series as a yield compounded every block over 2,102,400 blocks and converting it back reduces the median absolute gap to the chain from 0.344 to 0.004 percentage points for borrow rates and from 0.319 to 0.010 for supply rates; a daily-compounding reading fits worse. The label "unreliable" for regime 6 therefore reflects a difference of units rather than of values.

The conversion does not remove the gaps in regimes 0, 1, 2, 4, 5 and 9, which remain between about 0.4 and 3.3 percentage points under every reading considered. Most of these comparisons rest on 10 to 34 roughly daily samples, so imperfect alignment in time may contribute; the cause is not established. In regimes 8 and 10 rates were low enough that the two readings cannot be distinguished.

The same difference of units affects the authors' analysis. Their notebook compares the API series with a kink rate computed from the model as a simple rate. In the paper's first period this places observed rates a median 0.33 percentage points above the kink, against a median of −0.01 once the series is converted or when on-chain rates are used. A rate 0.33 points above the kink corresponds under the model to utilisation of about 90.3 per cent, which matches the paper's statement that rates were otherwise "higher than the kink, corresponding to a utilization of above 90%", while on-chain utilisation in that period had a median of about 75 per cent.
