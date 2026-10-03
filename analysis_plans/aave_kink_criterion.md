# Pre-specified criterion: does utilisation cluster at the kink on Aave V3?

Written after the Aave V3 subgraph data were collected, while the interest-rate parameters were being collected, and before any values from either were examined. Neither collection script prints summary statistics. The decision rules were checked on simulated data with known answers before this criterion was committed (`simulate_aave_kink.py`). Any departure from this plan will be listed, with reasons, in the report.

## Purpose

The test of the same claim on the cDAI market (`kink_clustering_criterion.md`) used data constructed for this project. This test applies the same rule to an existing dataset, the official Aave V3 subgraph, for a protocol the paper did not study. Aave V3 uses the same kinked interest-rate design as Compound, so the paper's claim can be stated for it without change.

The two markets differ in one respect that matters for interpretation. In the cDAI models of 2020 the rate was almost flat below the kink (see the post-hoc note to the cDAI criterion), so clustering of rates near the kink rate did not imply clustering of utilisation near the kink. Aave V3 models have a non-negligible slope below the kink, so the two readings of the paper's claim are expected to diverge less.

## Data

- **Existing dataset.** `data/aave_v3/aave_v3_daily_panel.csv`, collected by `collect_aave_v3_subgraph.py` from the Aave V3 subgraph for Ethereum mainnet (subgraph `Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g`; deployment recorded in the provenance file). Reserves: USDC, USDT, DAI and WETH of the Core market (addresses provider `0x2f39d218133afab8f2b819b1066c7e434ad94e9e`). One sample per reserve per day at 00:00 UTC, 2023-02-01 to 2025-11-30: the last reserve update at or before that moment.
- **Interest-rate parameters.** `data/aave_v3/aave_v3_rate_params_daily.csv`, collected by `collect_aave_v3_rate_params.py` from blockchain state at the last block at or before each sample time. The subgraph keeps only current parameters, so the parameters in force at each sample are taken from the chain.
- Utilisation: the subgraph's `utilizationRate`, interpreted as a fraction.
- Kink: `optimalUsageRatio` of the strategy in force, divided by 1e27.
- Distance from the kink: d = utilisation − kink, in percentage points.
- Excluded samples: those missing from either file, without a kink parameter, or without a utilisation value. The number excluded in each period is reported.

## Validation of the existing dataset

The subgraph is a third-party index of on-chain events, and its utilisation field is computed by the subgraph's own code. Before it is used, it is checked against the chain for each reserve and period.

- Chain utilisation, on every seventh day: U = D / (B + D), where D is the total supply of the variable and stable debt tokens and B is the underlying balance held by the aToken. Stable debt is taken as zero where no stable-debt contract responds (stable borrowing was removed in Aave V3.2). From Aave V3.1 the protocol uses an internal ("virtual") balance in place of B, so small differences are expected.
- **Rule.** If the median absolute difference between subgraph and chain utilisation on the validation days is at most 0.5 percentage points, the subgraph is used. Otherwise the decision for that reserve and period is made on the weekly chain values instead, with bootstrap blocks of two samples (about two weeks), and the failure is reported. The threshold is one tenth of the 5-point bin width, so a difference of this size rarely moves a sample into another bin, while it leaves room for the expected small gap between the chain approximation and the protocol's internal balance.
- Reported but not part of the rule: the maximum difference; the share of all days on which the subgraph's variable borrow rate equals exactly the Pool's stored rate at the matching block; and the time since the last reserve update (staleness).

## Definition of clustering and decision rules

Identical to the cDAI test and implemented by the same functions (`kink_clustering_analysis.py`):

- Bins 5 percentage points wide, with [-2.5, 2.5) as the kink bin. Utilisation clusters at the kink in a period if the kink bin contains a larger share of samples than every other bin.
- Moving-block bootstrap, 2,000 resamples, fixed seed, blocks of 14 daily samples.
- **Holds** if the kink bin is the most common bin and the bootstrap proportion is at least 0.8; **Holds, but not robustly** if it is the most common bin and the proportion is below 0.8; **Does not hold** otherwise; **Insufficient data** if fewer than 30 samples remain.
- Also reported: share in the kink bin, share above it, modal bin, median distance, and the rule with 2- and 10-point bins.

## Periods

For each of the four reserves: 2023-02-01 to 2023-12-31, calendar year 2024, and 2025-01-01 to 2025-11-30. Twelve reserve-periods in total. The last two periods coincide with the cDAI periods for 2024 and 2025, and the first overlaps most of the cDAI period for 2023.

## Overall decision

- **Holds on Aave V3** if clustering holds (robustly or not) in at least 8 of the 12 reserve-periods **and** at least 3 of the 4 reserves hold in at least 2 of their 3 periods.
- **Does not hold on Aave V3** if it holds in 4 or fewer reserve-periods.
- **Mixed evidence** in every other case, including 8 or more reserve-periods concentrated in fewer than 3 reserves.

The count thresholds are the proportions used for the cDAI test (two thirds and one third), applied to twelve periods. The condition on reserves is added because the twelve reserve-periods are not independent: the three stablecoin markets respond to common conditions, and without the condition a verdict of "holds" could rest on one group of assets alone. A result in which clustering holds for the stablecoins but not for WETH is a finding in its own right and should not be reported as general support. The number of periods holding for each reserve is reported.

## Secondary analysis (reported, no decision)

- Share of days on which the variable borrow rate lies within 0.25 percentage points of the rate at the kink (base rate plus slope 1), the reading of the claim as a statement about rates.
- Median slope of the model below and above the kink in each period, for comparison with cDAI.
- Results for the matching cDAI periods are placed alongside, without a formal comparison.

## Simulation check

Synthetic files with the column layout of both collection scripts, kinks that change mid-sample, and parameters in ray units were analysed with the same code. Five scenarios, three random seeds each:

- utilisation tightly around the kink (expected: every period Holds, overall Holds);
- about 20 points below the kink, and about 5 points above it (expected: every period Does not hold, overall Does not hold);
- utilisation around the kink with the subgraph's value 3 points away from the chain's (expected: validation fails, weekly chain values used, every period Holds, overall Holds);
- USDC and USDT around the kink in every period, DAI only in 2023, WETH only in 2024, otherwise well below (expected: 8 of 12 hold, only two reserves in at least 2 of 3 periods, overall Mixed evidence).

All 180 period decisions and all 15 overall verdicts matched the expected answers and data sources.

## Limitations recorded in advance

- The limitations listed for the cDAI test apply: the rule detects concentrated clustering, it operationalises a visual judgement, and daily samples describe the state at one moment each day.
- Reserves are not independent. Stablecoin markets on the same protocol respond to common conditions, so twelve reserve-periods carry less information than twelve independent tests. The condition on reserves in the overall decision limits, but does not remove, this problem.
- A sample reflects the last update before midnight. For reserves with frequent activity this is minutes old; the staleness is reported.
- The chain utilisation used for validation approximates the protocol's internal definition from Aave V3.1 onward, so the validation can fail for reasons unrelated to the subgraph. The weekly fallback then also has fewer samples per period (about 48 to 52).
- The four reserves were chosen as the largest borrowing markets comparable with the paper's assets, not at random.
