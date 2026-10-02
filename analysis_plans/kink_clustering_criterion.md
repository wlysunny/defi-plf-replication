# Pre-specified criterion: does utilisation cluster at the kink?

Written while the on-chain panels were being collected and before any of their values were examined. The decision rules were checked on simulated data with known answers before this criterion was committed (`simulate_kink_clustering.py`, results in `results/kink_clustering_simulation_check.csv`). Any departure from this plan will be listed, with reasons, in the report.

## Claim being tested

Gudgeon et al. (2020), Section 5.2, report for three periods of the cDAI market (21 February to 13 March, 14 March to 5 April, and 6 April to 21 April 2020) that "there appears to be a clustering of the realized interest rates at the kink of the interest rate function" and that "otherwise, interest rates are typically higher than the kink". Section 5.3 summarises: "during all the observation periods, the interest rates appeared clustered around the kink of the interest rate function."

Because the borrow rate is an increasing function of utilisation, rates clustering at the kink is equivalent to utilisation clustering at the kink utilisation. The test is therefore carried out on utilisation, which is read directly from the blockchain.

The paper assessed clustering visually and did not define it. The definition below is ours.

## Data

- Sources, both collected by `collect_onchain_cdai.py` directly from blockchain state:
  - `data/onchain/cdai_panel.csv`: one sample every 6,000 blocks (roughly daily), 2019-11-23 to 2025-11-30. Used for the new-data periods.
  - `data/onchain/cdai_panel_dense_2020.csv`: one sample every 300 blocks (roughly hourly), 2020-02-21 to 2020-04-21. Used for the paper's periods, which last 16 to 23 days and would contain fewer than 30 daily samples. Hourly sampling also matches the resolution of the data the paper used.
- Utilisation at each sample: U = totalBorrows / (cash + totalBorrows - totalReserves), the definition used by Compound's contracts.
- Kink at each sample: the `kink` value of the interest-rate model active at that block, divided by 1e18.
- Distance from the kink: d = U - kink, in percentage points of utilisation.
- Excluded samples: those where totalBorrows is zero, where the active model has no `kink` getter, or where any required value is missing. The number excluded in each period is reported.

## Definition of clustering

Utilisation distances d are grouped into bins 5 percentage points wide, aligned so that one bin is centred on the kink: [-2.5, 2.5), [2.5, 7.5), [-7.5, -2.5), and so on. The bin [-2.5, 2.5) is the kink bin.

In a given period, **utilisation clusters at the kink** if the kink bin contains a larger share of samples than every other bin, that is, if the most common utilisation level is the one at the kink.

The following are reported for every period but do not enter the decision: the share of samples in the kink bin; the share above the kink bin (d >= 2.5), which corresponds to the paper's second observation; and the result of the same rule with bins 2 and 10 percentage points wide, as a sensitivity check.

Samples within a period are autocorrelated, so uncertainty is assessed with a moving-block bootstrap (2,000 resamples, fixed random seed), with blocks of 14 consecutive samples (about two weeks) for the daily panel and 24 consecutive samples (about one day) for the hourly panel. For each period the bootstrap proportion of resamples in which the kink bin is the most common bin is reported.

## Periods

1. **Paper's periods (consistency check).** The three periods listed above, using the paper's dates, from the hourly panel.
2. **New data.** From the daily panel, calendar periods after the paper's sample: 2020-05-01 to 2020-12-31, then each calendar year 2021, 2022, 2023 and 2024, then 2025-01-01 to 2025-11-30. Six periods in total.

## Decision rules

For each period:

- **Holds** if the kink bin is the most common bin and the bootstrap proportion is at least 0.8.
- **Holds, but not robustly** if the kink bin is the most common bin and the bootstrap proportion is below 0.8.
- **Does not hold** otherwise.
- **Insufficient data** if fewer than 30 samples remain after exclusions.

Overall:

- **Consistency check.** If the claim does not hold in at least two of the paper's three periods, our definition does not reproduce the paper's own finding on on-chain data. The new-data results are still reported, but any conclusion about generalisation is qualified accordingly, and the discrepancy is discussed as a finding in its own right.
- **Generalisation.** The paper's finding is considered to hold beyond its original sample if it holds (robustly or not) in at least four of the six new-data periods, and not to hold if it holds in two or fewer. Three of six is reported as mixed evidence.

All results are reported regardless of which rule applies.

## Simulation check

Synthetic panels with a known utilisation process were analysed with the same code. In three scenarios with a clear answer (utilisation tightly around the kink; well below it; mostly 3-7 points above it), all 81 period decisions (3 scenarios x 9 periods x 3 random seeds) matched the known answer. An earlier version of this plan used only the daily panel; the simulation showed the paper's periods would then always be classed as insufficient data, so the consistency check could never run. The hourly panel was added for that reason, before any real data were examined.

## Limitations recorded in advance

- The rule detects concentrated clustering. In a simulated scenario where utilisation is centred on the kink but widely spread (standard deviation of 6 points) and highly persistent, the rule returned "does not hold" in 16 of 27 period decisions. A "does not hold" result therefore means that the kink is not the single most common utilisation level, not that utilisation is unrelated to the kink.
- The definition of clustering is an operationalisation of a visual judgement in the paper and may not capture exactly what the authors observed.
- Roughly daily sampling cannot detect clustering on shorter time scales, and the results describe where utilisation sat at the sampled moments rather than averages over time. The paper's periods are assessed at hourly resolution and the new-data periods at daily resolution, so the two are not measured identically.
- With only 16 to 23 days per paper period, a one-day bootstrap block may understate uncertainty if utilisation is persistent over several days.
- The kink and the rest of the rate model changed several times over the period; measuring distance from the active kink at each sample accounts for this, but periods may mix different rate models.
- After September 2022 Ethereum blocks are about 12 seconds apart rather than 13, so a fixed block step gives slightly more frequent samples in later periods. This affects the number of samples per period, not the definition.
