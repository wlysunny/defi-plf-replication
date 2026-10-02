# Pre-specified criterion: regime 1 re-analysis

Written before the regime 1 analysis was re-run with corrected parameters. Any departure from this plan will be listed, with reasons, in the report.

## Background

`3_cdai_regimes.ipynb` compares observed cDAI interest rates with the rates implied by a table of interest-rate-model parameters (`simulator/engine/dai_rate_params.py`), divided into eleven regimes (0-10). The original authors judged the fit of each regime visually and recorded their judgement as a code comment; regimes 1-3 are described as "Not a good mapping to predicted surface --> unsure why".

The parameter table dates the switch to the `dai_rate` interest-rate model at 2019-12-17 21:57:22. The cDAI event log shows the new model was set on-chain at 2019-12-20 00:26:19 UTC (block 9,133,122), so between these times the table applies the wrong model.

This analysis is a reproducibility check of the original regime analysis (original data and code) combined with a correction to one of its inputs, the parameter table.

Hypothesis: the mis-dated model switch contributes to the poor fit of regime 1.

## Data and model inputs

- Observations come from `data/compound/cdai.pkl` and are averaged within each hour. Hours without observations are dropped.
- The modelled borrow rate is computed from the observed `utilization_ratio`, using the rate functions in `simulator/engine/dai_rate_model.py`, with inputs constructed so that the model's utilisation equals the observed value and reserves are zero. This avoids the arbitrary reserves value used in the original notebook. Both model types in the parameter table (`dai_rate` and `jump_rate`) are implemented there, and in both the borrow rate depends only on utilisation.
- The observed `utilization_ratio` is computed in the repository as total borrows divided by total supply (`fetch_compound.py`), whereas the model defines utilisation as borrows / (cash + borrows - reserves). The two coincide only if total supply equals cash plus borrows minus reserves. This is assumed; a violation would show up as large errors in regimes 0 and 4 in the construct validity check.
- Modelled and observed rates are expressed on the same annual scale.
- Supply rates are not used, because they also depend on the reserve factor, which has separate recording errors.
- Unless stated otherwise, regime boundaries are those of the original parameter table.

## Metric

For each hourly observation, the absolute difference between the modelled and observed borrow rates, in annual percentage points. Fit is summarised by the median absolute error (MdAE). The mean absolute error is reported as a secondary measure. Uncertainty in each MdAE is expressed as a 95% confidence interval from a moving-block bootstrap (block length 24 hours, 2,000 resamples, fixed random seed), because hourly rates are strongly autocorrelated.

## Labelling the authors' fit judgements

The authors' comments mix three different statements: whether observations match the modelled surface (fit), where utilisation lies relative to the kink (location), and whether the protocol behaved as intended (performance). Only fit is relevant here, so each comment is assigned to one of three categories:

- **Good fit**: the comment expresses a positive or "as desired" judgement and does not mention a mismatch.
- **Poor fit**: the comment states that observations do not match the modelled surface, or describes the regime as broken.
- **Not stated**: the comment describes only location, or is internally contradictory.

Applying these rules gives:

| Regime | Comment | Category |
|---|---|---|
| 0 | Started out below the kink, performance perhaps as desired. | Good fit |
| 1 | Not a good mapping to predicted surface --> unsure why. | Poor fit |
| 2 | Not a good mapping to predicted surface --> unsure why. | Poor fit |
| 3 | Not a good mapping to predicted surface --> unsure why. | Poor fit |
| 4 | OK, below kink, performance perhaps as desired | Good fit |
| 5 | Tightly clustered at kink | Not stated |
| 6 | Tightly clustered at kink and above | Not stated |
| 7 | Performance improved - base rate dropped, worse performance | Not stated |
| 8 | Completely broken again | Poor fit |
| 9 | Tightly clustered just above kink | Not stated |
| 10 | Tightly clustered at kink | Not stated |

Assigning regimes 0 and 4 to "good fit" is an interpretation: the comments do not mention fit directly, but they use positive wording and lack the fixed phrase the authors use for poor fit.

The labels were assigned by the researcher alone; no second human annotator was available. As an auxiliary check, a large language model is given the three category definitions above and each comment, and asked to return one category per comment. The exact model identifier, date, prompt, temperature (0) and raw outputs are saved with the analysis. Agreement with the researcher's labels is reported. If the model assigns a different category to any regime labelled "good fit" or "poor fit", the construct validity check below is reported under both sets of labels. The researcher's labels remain the primary labels.

## Checks before the main comparison

1. **Time alignment.** The index of `cdai.pkl` and the times in the parameter table carry no time zone and are assumed to be UTC. This is checked by confirming that the observed borrow rate changes near the on-chain model switch at 2019-12-20 00:26:19 UTC. If the change appears offset by a whole number of hours, the offset is corrected and reported.
2. **Construct validity.** Under the original parameters, the MdAE is computed for every regime. The metric is considered to capture the authors' judgement only if every regime labelled "poor fit" (1, 2, 3, 8) has a higher MdAE than every regime labelled "good fit" (0, 4). If any of the eight pairwise comparisons is reversed, the metric does not capture what the authors observed, the comparison below is reported as inconclusive, and this is the result. A large error in regimes 0 or 4 additionally prompts a check of the implementation before any conclusion is drawn.

## Comparison

1. Primary: the window from 2019-12-17 21:57:22 to 2019-12-20 00:26:19, under the original parameters versus the corrected parameters (regime 0 parameters until the on-chain switch).
2. Secondary: the whole of regime 1 under the same two parameter sets.

## Decision rules

The benchmark is the larger of the MdAE values for regimes 0 and 4.

- **Inconclusive** if the construct validity check fails, if the window contains fewer than 24 hourly observations, or if the confidence interval of the corrected window MdAE contains the benchmark.
- **The correction explains the fit within the window** if the corrected window MdAE and its entire confidence interval are at or below the benchmark, and the original window MdAE is above it.
- **The correction explains the fit of regime 1 as a whole** if, in addition, the corrected MdAE for the whole of regime 1 is at or below the benchmark.
- **Otherwise**, the mis-dated switch is not the main cause of the poor fit. The next hypothesis to test is that parameter changes within regime 1, which are linked to MakerDAO's Dai Savings Rate and stability fee, occurred at times different from those recorded in the parameter table.

All results, including the checks and the auxiliary labelling, are reported regardless of which rule applies.
