# Replication of Gudgeon et al. (2020)

This repository contains a replication of the following paper:

Lewis Gudgeon, Sam M. Werner, Daniel Perez, and William J. Knottenbelt. 2020. DeFi Protocols for Loanable Funds: Interest Rates, Liquidity and Market Efficiency. In *Proceedings of the 2nd ACM Conference on Advances in Financial Technologies (AFT '20)*, pages 92–112. https://doi.org/10.1145/3419614.3423254

Results were compared with the arXiv version of the paper, arXiv:2006.13922v3 (15 October 2020).

The original code and data were published by the authors at https://github.com/danhper/defi-plf-analysis. The replication was carried out by Luyao Wang at Macquarie University for COMP8240 Applications of Data Science (2026). The authors' original README is retained unchanged in `README_original.md`; `README.md` describes the replication, and the final report is in `report/`. The original paper should be cited in any work that uses this repository.

The replication has three parts:

1. **Reproduction**: the authors' code run on the authors' data, with results compared against the paper.
2. **Investigation**: checks of the original data and results against the primary record on the Ethereum blockchain.
3. **Replication on new data**: the paper's claim about clustering at the kink of the interest-rate model, tested on one dataset constructed for this project (on-chain cDAI, 2019–2025) and one existing dataset collected for this project from its official source (Aave V3, 2023–2025).

**Two readings of the kink claim.** The paper states that "realized interest rates tend to cluster around the kink" (Sections 1 and 5.2). It motivates this by expecting the kink to "become a Schelling point of convergence among agents" (Section 4.3), and it reads the rates in terms of utilisation ("corresponding to a utilization of above 90%", Section 5.2). The literal statement concerns rates; the interpretation concerns where agents push utilisation. The two coincide only if the rate rises noticeably with utilisation around the kink. Below the kink, the cDAI models of 2020 were almost flat, so the rate stays near the kink rate however low utilisation falls. The pre-specified tests therefore judge clustering by utilisation, the reading that bears on the paper's interpretation, and report the reading by rates alongside without a decision. A negative result by utilisation is a re-test of the interpretation, not a contradiction of the literal statement.

## Summary of results

| Paper | Claim or result | Code | Criterion | Verdict |
|---|---|---|---|---|
| Table 2 | Median funds locked | `scripts/reproduce_exploration.py` | `analysis_plans/reproduction_liquidity_wealth_criterion.md` | 13 of 15 cells exact; the two dYdX cells (ETH, DAI) differ by a factor of about 10¹² because of a unit divisor in the committed code (DAI by 1.000 × 10¹², ETH by 0.986 × 10¹²; the remaining 1.4 per cent for ETH is unexplained) |
| Figure 1 | Utilisation and borrow rates by token | `scripts/reproduce_exploration.py` | same | Reproduced (ordering of the three protocols identical for every token) |
| Figures 2–5 | Liquidity of ETH, DAI and USDC markets | `scripts/reproduce_exploration.py` | same | Reproduced (all four qualitative statements hold; shading agrees at the resolution of the figures) |
| Figure 6 | Wealth concentration | `scripts/reproduce_concentration.py` | same | Numerically reproduced (pre-specified tolerance: within 1 percentage point) when the event log is cut at the date in the caption: 50.63 / 59.93 / 47.97 per cent against 50.3 / 60.0 / 47.3 (differences of 0.33, 0.07 and 0.67 percentage points). Without the cut-off: 32.6 / 31.2 / 49.9 |
| Tables A2–A5 | Uncovered interest parity | `notebooks/compound/5_uip_compound.ipynb`, `scripts/compare_uip.py` | criterion fixed after the first run (see limitations) | Test decisions largely reproduced (77 of 80 agree at 1%, 74 of 80 at 5%); coefficients not reproduced (14 of 80 within 5% of the authors' value; 11 of opposite sign). See "Exchange-rate replacement" |
| Tables A6–A7, Figures 11–14, A1–A6 | VECM of cross-protocol rates | `scripts/vecm_replication.do` | `analysis_plans/vecm_replication_criteria.md` | DAI reproduced numerically; USDC reproduced inferentially (one long-run constant differs in the last reported digit); all ten figures agree |
| Section 5.2, Figure 9 | Clustering at the kink (paper's three periods) | `scripts/kink_clustering_analysis.py` | `analysis_plans/kink_clustering_criterion.md` | By rates: the authors' figure is reproduced (median +0.33 percentage points above the kink rate), but the gap is an artefact of units (see "Units of the original rate series"). By utilisation: clustering holds in 0 of 3 periods |
| — (new data) | Clustering at the kink on cDAI, May 2020 to November 2025 (six periods) | `scripts/kink_clustering_analysis.py` | `analysis_plans/kink_clustering_criterion.md` | **Mixed evidence**, a verdict defined in advance for 3 of 6 periods: clustering by utilisation holds in May–December 2020, 2021 (not robust) and January–November 2025, but not in 2022, 2023 or 2024 (4 were needed for "generalises", 2 or fewer would have meant "does not generalise") |
| — (new data) | Clustering at the kink on Aave V3, 2023–2025 | `scripts/aave_kink_analysis.py` | `analysis_plans/aave_kink_criterion.md` | **Mixed evidence**, a verdict defined in advance for 5 to 7 of 12 reserve-periods: clustering by utilisation holds in 7 of 12 (8 were needed for "holds", 4 or fewer would have meant "does not hold") |

Apart from the UIP comparison, whose criterion was fixed after a first run (and whose weekly sample was later corrected, with the predicted effects committed before the corrected run), every criterion was committed before the results it governs. The commit history records this order; it is an auditable record rather than proof, since local commit times can be altered and a commit records when a file was saved, not when an analysis was first run. The times at which GitHub received each push are kept in the private repository that holds the original history (see "History of this repository"). Amendments and post-hoc notes are appended to the criterion files and do not change earlier text.

| Test | Criterion first committed | Results first committed |
|---|---|---|
| Regime 1 re-analysis | `regime1_criterion.md`, a3b5832, 2 Oct 2026 15:43 | `regime1_results.json`, e1c1c16, 2 Oct 18:38 |
| Kink clustering, cDAI | `kink_clustering_criterion.md`, ed4f268, 2 Oct 19:01 | `kink_clustering_results.json`, 23e6e63, 2 Oct 20:25 |
| Kink clustering, Aave V3 | `aave_kink_criterion.md`, 03ea829, 3 Oct 20:19 | `aave_kink_results.json`, dd5371f, 3 Oct 23:11 |
| Regime annotation | `regime_annotation_rules.md`, 3d5603a, 3 Oct 20:24 | `regime_annotation.csv`, 739389a, 3 Oct 20:25 |
| Section 5.1 reproduction | `reproduction_liquidity_wealth_criterion.md`, 5060d4f, 7 Oct 20:51 | `reproduction_table2.csv`, 6193197, 7 Oct 21:18 |
| VECM reproduction | `vecm_replication_criteria.md`, 23902d4, 27 Oct 17:05 | `results/vecm/`, 9e63b11, 27 Oct 17:13 (Stata log opened 17:06:59) |
| VECM normalisation check | `vecm_normalisation_check.md`, b62aa0d, 29 Oct 12:19 | `normalisation_log.txt`, 4af76f5, 29 Oct 14:19 (Stata log opened 12:19:58) |
| VECM weak exogeneity | follow-up in the same file, eb48413, 29 Oct | `weak_exogeneity_log.txt`, 77cae7f, 29 Oct 14:23 (Stata log opened 14:22:06) |
| Second-provider check | `second_provider_check_criterion.md`, c9ea715, 29 Oct 15:48 | `second_provider_check.json`, a0362d8, 29 Oct 15:56 |
| UIP window correction | `uip_window_correction.md`, 5295a57, 29 Oct 16:10 | `uip_comparison.csv`, 7d94806, 29 Oct 16:17 |
| Governance annotation | `governance_rationale_codebook.md`, bec9659, 2 Nov 17:18 | `governance_agreement.json`, c08aaf2, 3 Nov 22:12 |

Times are Sydney time, as recorded in the commits. Hashes are those of the published history; the original hash of each commit is in `REPLICATION_commit_map.tsv`.

The regime annotation rules state that some of the inputs had already been examined in exploratory analyses; the rules fix the labels and thresholds, not the data.

## Repository structure

The `master` branch contains the authors' code without modification. The `replication-fixes` branch, which is the default branch, contains the original code with the changes needed to run it in 2026, together with everything added for the replication. All modifications to the authors' files can be inspected at:
https://github.com/wlysunny/defi-plf-replication/compare/master...replication-fixes

| Path | Contents |
|---|---|
| `README.md`, `README_original.md` | Overview of the replication; the authors' README, unchanged |
| `report/` | The final report (PDF) and its LaTeX source |
| `LICENSE` | Which terms cover which files (see "Data, licence and ethics") |
| `compounds_research/`, `simulator/`, `notebooks/` | The authors' code, changed only as described under "Modifications to the original code" |
| `scripts/` | All code written for the replication; see `scripts/README.md` for what each script reads and writes |
| `analysis_plans/` | Criteria fixed before each test, with appended amendments and post-hoc notes; annotation rules; the LLM labelling prompt and output |
| `data/compound/`, `data/aave/`, `data/dydx/`, `data/stata/` | The authors' data, unchanged |
| `data/manual/`, `data/derived/` | Replacement exchange rates and the block-time table |
| `data/onchain/`, `data/aave_v3/` | The constructed dataset and the collected existing dataset; see "New datasets" |
| `data/governance/`, `annotation/` | Aave governance forum threads (posts with a CC0 waiver in full, others as URL and SHA-256), the annotation units, and the researcher's, model's, arbitrated and final labels |
| `figures/` | The authors' figures; `figures/reproduction/` (Section 5.1 reproduced), `figures/report_*` and `figures/appx_*` (report), `figures/update/` (progress presentation) |
| `results/` | Outputs of the scripts; `results/exploratory/` holds post hoc analyses that do not change any pre-specified decision |

## Computational environment

- macOS (Apple Silicon), Anaconda base environment, Python 3.14.6, NumPy 2.4.6, pandas 3.0.3, matplotlib 3.11.0, statsmodels 0.14.6, web3 7.16.0. The full package list is in `environment_snapshot.txt`.
- StataNow/MP 19.5 for Mac (Apple Silicon), revision 08 Apr 2025, run under the Macquarie University site licence, with automatic updates disabled for the duration of the project. The authors' do-file requires the user-written package `estout` (version 2.1.4, 13 April 2026, installed with `ssc install estout`), which the authors do not declare.
- Large data files are stored with Git LFS.
- `environment_snapshot.txt` is a `conda list --export` file of the Anaconda base environment for the `osx-arm64` platform, so it lists far more packages than the analyses use and `conda create --file` is intended to reproduce the recorded environment on Apple Silicon Macs only, subject to package availability and channel configuration. No cross-platform list was prepared; on other systems the packages named above, with seaborn and, for `scripts/make_vecm_comparison.py`, PyMuPDF (`pip install pymupdf`), are the ones the code imports directly.
- Scripts that read blockchain state need an archive-capable Ethereum RPC endpoint in the environment variable `ETH_RPC_URL`; the Aave V3 subgraph collector needs a Graph API key in `GRAPH_API_KEY`. No key is stored in the repository.

## Reproducing the results

```bash
git clone --branch replication-fixes https://github.com/wlysunny/defi-plf-replication.git
cd defi-plf-replication
git lfs pull
conda create --name defi-plf --file environment_snapshot.txt
conda activate defi-plf
```

All commands below are run from the repository root.

**Exchange rates.** `python scripts/clean_manual_prices.py` produces the REP and SAI series from the raw downloads. The DefiLlama prices for the other tokens are fetched and cached by the second cell of `notebooks/compound/5_uip_compound.ipynb`; an existing cache is reused only if it covers the full sample window, and a cache that ends early is extended by appending the missing days, without downloading or rewriting the existing values.

**Authors' notebooks.** The notebooks in `notebooks/compound/` are run in numerical order, followed by `compound-wealth.ipynb`, `notebooks/aave/deposits.ipynb` and `notebooks/dydx/analysis.ipynb`. In the dYdX notebook, the cells that connect to the authors' private Ethereum node are skipped; the analysis and plotting cells read only local files. Running a notebook overwrites the authors' figures in `figures/`; `git restore figures/` returns them.

**Section 5.1.** `python scripts/reproduce_exploration.py` (Table 2, Figures 1–5) and `python scripts/reproduce_concentration.py` (Figure 6).

**UIP.** `python scripts/compare_uip.py` compares the parity tests with the authors' saved notebook output, pair by pair.

**VECM.** In Stata: `cd` to the repository root, then `do scripts/vecm_replication.do`. Outputs go to `results/vecm/`. `scripts/vecm_normalisation_check.do` and `scripts/vecm_weak_exogeneity.do` run the two follow-up checks described below.

**New data and tests.** For each test, the `simulate_` script first, then the analysis script, then the `exploratory_` scripts; the order of execution is listed in `scripts/README.md`. Data collection needs network access and is slow, but all collected data are committed, so it is needed only to rebuild them. Analyses use fixed random seeds. In a fresh clone of the published repository on 5 November 2026, in the recorded environment, re-running `kink_clustering_analysis.py`, `aave_kink_analysis.py`, `annotate_regimes.py`, `exploratory_apy_check.py`, `governance_agreement.py`, `governance_final_labels.py` and `reproduce_concentration.py` reproduced the committed result files byte for byte; exact equality in other environments is not guaranteed.

**Governance texts.** Forum posts without a CC0 waiver are stored as URL and SHA-256 only. `python scripts/restore_governance_texts.py` downloads them from the forum's public endpoint, checks every hash and restores the threads, the annotation units and the model's raw outputs; in the same fresh clone all twelve restored files were byte-identical to the originals.

**Figures of the report.** `python scripts/make_report_figures.py` and `python scripts/make_appendix_figures.py`; `python scripts/make_vecm_comparison.py` also needs the paper's PDF at `figures/paper/2006.13922v3.pdf` (download from https://arxiv.org/pdf/2006.13922v3; not redistributed). The report compiles from `report/main.tex`.

## Modifications to the original code

1. **Library changes.** NumPy, pandas, matplotlib, web3.py and eth_abi have renamed or removed functions since 2020, for example `np.NaN` → `np.nan`, `fillna(method=...)` → `.ffill()`, `DataFrame.append` → `pd.concat`, and `fig.gca(projection=...)` → `fig.add_subplot(projection=...)`. These changes do not alter the computations.
2. **Author-specific paths.** Absolute paths on the authors' machine, and output paths pointing to their LaTeX project, were replaced with paths relative to the repository. In the Stata do-file this is the only change; the copy is `scripts/vecm_replication.do`, and `notebooks/VECM.do` is unchanged.
3. **One restored line.** `notebooks/exploration.ipynb` uses a global variable `aave` that no cell in the final version defines. The defining line, `aave = analyze_aave.load_data()`, is present in commits 48ca0d2, 8b00d27 and cfcbabf and was deleted in f4f9d28 (31 August 2020). `scripts/reproduce_exploration.py` restores it unchanged; nothing else in the notebook is altered.
4. **Exchange-rate source.** The UIP analysis retrieved exchange rates from the CryptoCompare API, which now requires a paid key. They were rebuilt from the DefiLlama historical price endpoint (`compounds_research/compound/fetch_exchange_rates_defillama.py`). REP and SAI, which DefiLlama does not provide, were collected manually; the raw downloads are kept unchanged in `data/manual/raw/`.

### Consequences of the exchange-rate replacement

- DefiLlama provides US dollar prices only, so each pair rate is a cross rate (US dollar price of the base token divided by that of the quote token). For thinly traded tokens this may differ from the direct market price the authors used.
- The REP and SAI series come from other providers and were cleaned by hand.
- The REP series has 10 missing days within the period of the daily regressions (2 April 2019 to 8 May 2020), six between 12 and 26 October 2019, and 11 within the exchange-rate window, which also includes 9 May 2020. They are not imputed, which reduces the number of observations for REP pairs.
- The exchange-rate window (1 April 2019 to 10 May 2020) is defined in one place, `UIP_SAMPLE_START` and `UIP_SAMPLE_END` in `fetch_exchange_rates_defillama.py`. It ends on 10 May 2020, the label of the last weekly interest-rate period, after a correction described below.

### UIP results compared with the authors' output

The comparison (`results/uip_comparison.csv`) covers 80 tests: 20 token pairs in each of four regressions (daily and weekly, borrow and supply rates).

| Dimension | Agreement with the authors' output |
|---|---|
| Test decision at the 1% level | 77 of 80 |
| Test decision at the 5% level | 74 of 80 |
| Sign of the coefficient | 69 of 80 |
| Coefficient within 5% of the authors' value, \|β_rep − β_orig\| / \|β_orig\| ≤ 0.05 | 14 of 80 (within 1%: 4 of 80) |
| Number of observations | 40 of 80 |

The relative difference is unstable where the authors' coefficient is close to zero (the smallest is 0.0034, for ETH–SAI daily supply rates, where the relative difference is 14.8), so medians are reported below rather than means.

- **Disagreeing decisions.** At 1%: BAT–REP (daily supply; authors' p = 0.0006, here 0.90), DAI–SAI (weekly supply; 0.24 against < 0.001) and ETH–USDC (weekly supply; 0.0098 against 0.012, on either side of the threshold). At 5%: BAT–REP and DAI–SAI again, ETH–REP (weekly supply; 0.031 against 0.28), and three weekly tests in which the authors' p-value was close to the threshold: BAT–ZRX borrow (0.102 against 0.044), ZRX–DAI borrow (0.058 against 0.026) and ZRX–DAI supply (0.067 against 0.0496).
- **Opposite signs.** 11 coefficients, all in pairs involving DAI or REP: DAI–SAI in all four regressions, ETH–DAI (2), USDC–DAI (2), BAT–DAI, ZRX–DAI and ETH–REP.
- **Observations.** The differences follow the tokens. The 20 pairs containing neither DAI nor REP, among them four of the five SAI pairs, have the same number of observations as the authors' in both the daily and the weekly regressions (40 tests). (The SAI–REP pair does not appear, because the authors' notebook skips it.) In the daily regressions, pairs with DAI have 6 fewer (the DefiLlama DAI series lacks 6 days that the authors' data contained), pairs with REP 9 fewer (missing days in the hand-collected series) and DAI–REP 9 fewer; in the weekly regressions, pairs with DAI or REP have 2 fewer and DAI–REP 3 fewer.

**Correction of the weekly sample.** In a first run every weekly regression had one observation fewer than the authors'. The cause was the exchange-rate window chosen for this replication: it ended on 9 May 2020, while the last weekly interest-rate period is labelled Sunday 10 May, so that week was dropped, and with it the following-week exchange-rate change of the week of 3 May. The window was extended to 10 May after this was found, a post-hoc correction. Its predicted effects were written and committed before the corrected regressions were run (`analysis_plans/uip_window_correction.md`, commit 5295a57), and all four held: only one price per token was added, existing prices were unchanged, the 40 daily regressions were identical, and every weekly regression gained exactly one observation. The correction lowered agreement in decisions at the 5% level from 77 to 74 of 80, because three tests whose p-values were near 5% moved across the threshold, and raised the number of coefficients within 5% of the authors' from 8 to 14. The restored week is influential in some regressions: for ZRX–USDC the weekly coefficient changes sign when it is added (from +0.09 to −0.62 for borrow rates, against the authors' −0.56). This sensitivity was not examined in advance and is reported as an exploratory observation. The corrected results were committed in 7d94806; the comparison before the correction remains in the repository history (`results/uip_comparison.csv` at commit 1e70992).

**Is the sample the cause?** Among the 40 tests with the same number of observations, the coefficients still differ substantially: 9 of 40 are within 5% of the authors' value, and the median relative difference is 0.24 (0.38 for the 20 daily and 0.21 for the 20 weekly tests), against 5 of 40 and 0.43 for the other 40. All 40 have the same sign as the authors'. The 11 sign changes occur only in pairs with DAI or REP, where the price source and the sample changed together, so their causes cannot be separated. Equal counts do not guarantee identical dates, but a difference is unlikely when no token in the pair has missing days.

**Interpretation.** The test decisions are largely reproduced, but the regressions are not: only 14 of 80 coefficients are within 5% of the authors'. Agreement in decisions is a weak criterion in both directions. Most p-values are far below either threshold (for example 10⁻¹³⁰), so a decision can survive a large change in the coefficient; where a p-value is near the threshold, a single added week can reverse the decision, as the correction of the weekly sample showed. The coefficients already differ widely in the 40 regressions whose observation counts match, where neither token has missing days, which suggests that differences in the exchange-rate values are an important contributor to the numerical non-reproduction; the regression code is unchanged apart from library compatibility. Differences in observation dates, and the different token composition of the two groups, cannot be fully ruled out. Which property of the replacement data matters (cross rates from US dollar prices instead of direct pair prices, or the providers' prices themselves) cannot be determined, because the original CryptoCompare series can no longer be obtained. The paper's qualitative conclusion, that UIP is rejected for most pairs, is reproduced; its coefficient estimates are not.

## New datasets

### Dataset 1: on-chain cDAI regime dataset (constructed for this project)

**Why it was built.** The paper's rate and utilisation series came from the Compound API, which was shut down on 15 April 2023. The series' units are not documented, and in some periods they disagree with the blockchain. The blockchain records the rates the contract actually charged.

| Stage | What was done | Script |
|---|---|---|
| Collection | Contract state of cDAI and its interest-rate model read from an archive node at fixed block intervals: a long panel sampled every 6,000 blocks (about 22 hours before September 2022 and 20 hours after, when block times fell to 12 seconds), 2,489 samples from 23 November 2019 to 30 November 2025; and a dense panel sampled every 300 blocks (about one hour), 1,319 samples from 21 February to 21 April 2020. Neither panel has duplicate blocks, and the largest gap between consecutive samples equals the sampling interval, so both panels are complete with respect to their sampling grids. Changes that occur and are reversed between two sampled blocks, such as a brief parameter change or a short spike in utilisation, are not observed. Each sample records the borrow and supply rates, cash, borrows, reserves, reserve factor, and the address and parameters of the model in force. Collection resumes after interruption, retries on rate limits, fails loudly rather than saving incomplete data, and records its provenance (host name only, no key) in a JSON file next to each panel | `collect_onchain_cdai.py` |
| Events | 1,085 `LiquidateBorrow` events taken from the authors' event log | `annotate_regimes.py` |
| Preprocessing | Block numbers converted to timestamps by interpolating a sampled block-time table (median error 112 seconds); utilisation computed with the contract's own formula; all rates expressed as simple annual rates | `build_block_times.py` |
| Annotation | Each of the authors' eleven rate regimes labelled by pre-specified rules (`analysis_plans/regime_annotation_rules.md`): matching on-chain change, source of the change, whether parameters match the chain, reliability of the original series, and number of liquidations | `annotate_regimes.py` |
| Annotation | The authors' own judgement of fit for each regime, coded from their code comments into Good fit / Poor fit / Not stated (see "Annotation and agreement") | `analysis_plans/regime1_criterion.md` |

**Tests of the dataset.**

| Test | Result |
|---|---|
| Rates computed from the recorded model parameters, compared with the rates read directly from the contract | Differ by at most 0.003 percentage points |
| Agreement with the original API series after converting it from a compounded yield to a simple rate (regime 6, 490 hourly points) | Median absolute difference 0.004 percentage points (borrow) |
| Liquidations around the crash of 12 March 2020 | The regime with most liquidations contains the crash, as expected |
| Re-reading a sample of blocks | Identical values |
| Re-reading a stratified random sample from a second RPC provider (Infura): 15 rows of `cdai_panel.csv`, 5 of `cdai_panel_dense_2020.csv` and 10 of the Aave V3 parameter file, compared field by field with exact equality. Criterion and script committed before the run (`analysis_plans/second_provider_check_criterion.md`, commit c9ea715), self-check on the original provider first (`scripts/second_provider_check.py`) | **Pass**: all compared fields identical in 30 of 30 rows (`results/second_provider_check.json`, commit a0362d8). The first run stopped without a verdict on a transient provider error (JSON-RPC −32603), after four rows without differences; Amendment 1, appended to the criterion (commit 78b937d), classified such errors as query failures with up to three attempts, and the self-check and run were repeated in full on the same sample. One row needed a second attempt. Limits: both providers were read with the same collection code, so errors in that code would not be detected; Aave validation columns were populated, and compared, in only 1 of the 10 Aave rows (4 values) |

### Dataset 2: Aave V3 (existing dataset, Ethereum Core market)

| Stage | What was done | Script |
|---|---|---|
| Collection | Daily reserve data for USDC, USDT, DAI and WETH from the official Aave V3 subgraph, 1 February 2023 to 30 November 2025: 4,123 asset-day observations out of 4 × 1,034 = 4,136 possible, with no duplicate days. The 13 missing are all USDT, from 1 to 13 February 2023: the earliest state of the USDT reserve in the subgraph is at 21:00 UTC on 13 February 2023, after that day's midnight sample; the on-chain Pool contract returned no USDT reserve at any of the 13 sampled blocks from 1 to 13 February (recorded as `not listed` in the rate-parameter file), so the reserve was not yet listed. DAI, USDC and WETH are complete. The USDT period for 2023 therefore starts on 14 February | `collect_aave_v3_subgraph.py` |
| Collection | The historical kink (`optimalUsageRatio`) and the other rate-model parameters read from the chain at each sampled block, because the subgraph does not record parameter history | `collect_aave_v3_rate_params.py` |
| Test design | Criterion committed before the data were examined (commit 03ea829): clustering must hold in at least 8 of 12 asset-periods and, for at least 3 assets, in at least 2 of 3 periods. The rule was checked on simulated data with known answers (180 of 180 and 15 of 15 correct) | `simulate_aave_kink.py`, `aave_kink_analysis.py` |

**Tests of the dataset.**

| Test | Result |
|---|---|
| Subgraph utilisation compared with utilisation computed from on-chain balances, on every seventh day (pre-specified, threshold 0.5 percentage points) | Departs by 0.7 to 1.9 percentage points in four reserve-periods; for these, the decision is made on the on-chain values, as the rule requires |
| Utilisation implied by the on-chain borrow rate and the recorded model parameters (exploratory) | Same verdict in all 12 reserve-periods (`results/exploratory/aave_validation.json`). This is a consistency check rather than an independent measurement, because the contract computes the rate from utilisation through the same model |
| Re-reading 10 random rows of the rate-parameter file from a second RPC provider | Identical; see the same check under Dataset 1 |

## Annotation and agreement

**Rule-based labels.** The regime annotations in Dataset 1 are produced by deterministic rules written and committed before the script was run (`analysis_plans/regime_annotation_rules.md`, commit 3d5603a). The same inputs always give the same labels, so an inter-annotator agreement measure is not informative for them; their quality rests on the tests listed above.

**Judgement labels: the authors' assessment of fit.** Coding the authors' free-text comments into three categories requires judgement. The researcher assigned the labels using written definitions committed in `analysis_plans/regime1_criterion.md` (commit a3b5832, 2 October 2026, 15:43). As an auxiliary check, GPT-5, through the ChatGPT web interface, was given the same definitions and the eleven comments, without the researcher's labels, and asked for one category per comment. The prompt and the full output are in `analysis_plans/llm_labelling_prompt.md` and `analysis_plans/llm_labelling_raw_output.txt`; the output was committed after the researcher's labels.

- Agreement: 11 of 11, Cohen's κ = 1.00.
- What this shows: in this small exercise the definitions were applied consistently by two annotators. It does not establish that the labels are valid or that the definitions are free of ambiguity. The task is easy, because the authors reuse fixed phrases; the model received the same definitions, so it is not an independent second annotator; and n = 11.
- Deviation from the plan: the criterion stated that the temperature (0) would be recorded, but the ChatGPT web interface does not allow it to be set, and the model version behind the interface is not fixed. The labelling cannot be repeated exactly.

**Judgement labels: governance rationales for Aave's kink changes.** The Aave V3 test asks whether utilisation clusters at the kink; this annotation asks how Aave governance itself described the kink when it moved it. Each of the 16 changes of the kink on Aave V3 Ethereum Core between February 2023 and November 2025 (19 asset-level changes in the daily on-chain data, merged by date) was paired with the forum post that first specifies the new value. Eight forum threads were downloaded through the forum's public raw endpoint (the posts used come from seven of them), with their SHA-256 recorded (`scripts/collect_governance_threads.py`, `data/governance/manifest.json`), and the units were extracted by a fixed rule (`scripts/build_governance_units.py`). Each unit received three labels defined in `analysis_plans/governance_rationale_codebook.md`: the main reason given for the change (`rationale`, six categories), how the text frames the kink relative to utilisation (`kink_framing`: a level utilisation settles at, a level it should stay below, or only a parameter), and whether the change is described as temporary.

The codebook, units, prompt and scripts were committed before any labelling (bec9659). The researcher labelled all units and committed the labels (75407c2) before a locally run open-weight model, `qwen2.5:7b-instruct` through Ollama 0.40.13 (digest 845dbda0…, temperature 0, seed 8240), labelled the same units with the codebook as its prompt (1f19150; `scripts/label_governance_llm.py` refuses to run unless the researcher's labels are committed and the units, codebook and script are unchanged since). A first model run stopped after one unit when the local server closed the connection; as specified, the partial output was kept and all units were labelled again.

| Label | Agreement | Cohen's κ |
|---|---|---|
| `rationale` | 12 of 16 | 0.64 |
| `kink_framing` | 8 of 16 | 0.21 |
| `temporary` | 15 of 16 | 0.85 |

Agreement was computed before arbitration (`results/governance_agreement.json`, c08aaf2). Most disagreements on `kink_framing` reflect the model's tendency to assign one category: it labelled 14 of 16 units `KEEP_BELOW`. Each disagreement was then resolved by the researcher, assisted by an AI assistant (Claude), using the codebook rules, the passages concerning the kink and the researcher's labelling notes; the assistant drafted a decision and reason for each, and the researcher reviewed and accepted them (`annotation/arbitration.csv`). The final label is the researcher's in 3 of the 13 disagreements, the model's in 5 and neither in 5. Only disagreements were arbitrated; labels on which both agreed were not reviewed and may share errors (for example A02).

| Final labels (`results/governance_final_summary.json`) | Governance votes, 2023–2024 (6) | Risk Steward process, 2025 (10) |
|---|---|---|
| `rationale` | capital efficiency 4, liquidity buffer 2 | rate stability 5, alignment 2, liquidity buffer 2, capital efficiency 1 |
| `kink_framing` | parameter only 4, settle at 1, keep below 1 | keep below 6, settle at 4 |
| described as temporary | 0 | 4 |

In 2023–2024 the kink was mostly changed as a parameter, for capital efficiency. In 2025 the risk manager treated it as a ceiling during periods of stress, raising it temporarily to dampen rate spikes, and described it as a target when restoring it ("its standard target of 92%", "our utilization target"). The second framing parallels, in governance language, the paper's reading of the kink as a point of convergence, but it is not evidence that agents coordinate on it. It records what governance intended, not how often utilisation lies near the target; the Aave V3 test of the latter gave mixed evidence. Governance process and calendar period coincide, so the difference between the two groups cannot be attributed to the process; with 16 units the comparison is descriptive.

What the agreement shows: the categories for the reason and for temporary changes were applied consistently; the framing of the kink was not, by a small model, and needed arbitration in half of the units. The codebook was written after the texts had been read, by the researcher with an AI assistant, and the model received the same definitions, so agreement shows that the definitions can be applied, not that the labels are valid.

## Further checks of the VECM

Two follow-up checks were run after the reproduction, each with predictions committed before it was run (`analysis_plans/vecm_normalisation_check.md`).

1. **Normalisation.** With rank 2, Stata's default Johansen normalisation sets the coefficients of the first two variables to an identity matrix. Re-estimating with the variables in a different order (dYdX, Compound, Aave) leaves the log likelihood and the long-run matrix Π unchanged, but the reported long-run relationships change from "Compound–dYdX and Aave–dYdX" to "dYdX–Aave and Compound–Aave". The data identify a cointegration space of rank two; the specific pairwise representation reported in the paper depends on the normalisation and the variable order, rather than being uniquely identified by that space.
2. **Weak exogeneity (exploratory).** A joint test that a protocol's adjustment coefficients are all zero does not depend on the normalisation. The statistics are identical in both variable orders.

| Protocol | DAI | USDC |
|---|---|---|
| Compound | χ²(2) = 2.57, p = 0.28 | χ²(2) = 11.07, p = 0.004 |
| Aave | χ²(2) = 22.98, p < 0.001 | χ²(2) = 24.72, p < 0.001 |
| dYdX | χ²(2) = 32.91, p < 0.001 | χ²(2) = 17.68, p < 0.001 |

For DAI, weak exogeneity of Compound is not rejected while Aave and dYdX adjust, which is consistent with, but does not establish, the paper's reading that Compound "has market power"; failing to reject does not show that Compound's adjustment is zero. For USDC, weak exogeneity is rejected for all three protocols, so the paper's statement that "again Compound has market power" is not supported for USDC. The comparison of adjustment speeds in the paper (Aave 0.607, dYdX 0.115) also depends on the normalisation. The residuals show autocorrelation at lag 3 and are not normal, so these p-values are approximate.

## Observations on the original code

These concern reproducibility rather than the correctness of the results.

- **Results depend on steps that are not in the code.** Table 2 and Figure 1 rely on a variable whose definition was deleted from the final notebook; no committed version of `load_dydx_market` gives correct units for all three dYdX tokens, although the paper's table and figures are correct; Figure 6 requires a cut-off date that appears only in the caption; and the long-run parts of Tables A6 and A7 are not produced by the committed `esttab` commands, which output the adjustment coefficients, lagged differences and short-run constants but no long-run coefficients.
- **Undeclared environment.** The Stata do-file has no `version` statement and depends on an undeclared package; paths point to the authors' machine and LaTeX project.
- **Dates of rate regimes.** The dates in `simulator/engine/dai_rate_params.py` mark governance decisions. The two model replacements took effect on-chain about 50 and 129 hours later (`results/exploratory/timelock_check.json`). The parameters themselves match the chain.
- **Units of the original rate series.** The Compound API reported compounded annual yields, while the model gives simple annual rates. In the paper's first kink period this difference accounts for the reported rates lying a median 0.33 percentage points above the kink rate; after conversion, and on-chain, the median is −0.01 (`results/exploratory/apy_check.json`).
- **UIP notebook.** The SAI–REP pair is skipped by an unexplained `continue` statement that the paper does not mention. The paper reports tests at the 1% level, while the notebook prints "UIP holds" at 5%.

## Corrections made during the project

Statements made during the project, in notes or earlier versions of this file, that were later found to be wrong:

| Earlier statement | Correction |
|---|---|
| The dYdX block-time file was referenced but never committed, so dYdX could not be reproduced | The file was in the repository throughout; the dYdX notebook fails only in the cells that connect to the authors' private node |
| The original rate data are inaccurate | Their units are undocumented (compounded yield rather than simple rate); some periods still disagree with the chain for reasons not established |
| An early UIP run agreed with the paper in only 49 of 80 tests | That run used the liquidity analysis's sample window by mistake; with the correct window 77 of 80 decisions agree |
| UIP reproduced (77 of 80), as stated in the update presentation | Only the test decisions agree; the coefficients do not (8 of 80 within 5%), which was found when the comparison was broken down on 29 October. After the correction of the weekly sample the figures are 77 (1%) and 74 (5%) of 80 decisions and 14 of 80 coefficients |

## Data, licence and ethics

- **The authors' code and data.** The original repository has no licence (checked on 15 October and 4 November 2026). This repository is a fork of it on GitHub, so the authors' files are reproduced under GitHub's terms for forks (Terms of Service, section D.5); `LICENSE` grants no licence to them. The authors were contacted on 27 October 2026 about redistribution; there was no reply by submission.
- **Files written for this project.** Code in `scripts/` is licensed under the MIT License; all other files written or constructed for this project under CC BY 4.0, except the third-party material listed in `LICENSE`.
- **Governance forum posts.** `data/governance/raw/` holds the eight downloaded threads. Posts that end in a CC0 waiver are stored in full (19 of the 73 posts, including 13 of the 16 annotated); the other 54 posts, and the unit texts A01, A04 and A06, are replaced by their URL and the SHA-256 of their text. `data/governance/post_manifest.json` records the licence status of every post and `data/governance/redaction_record.json` each replacement; `scripts/restore_governance_texts.py` restores the originals (see "Reproducing the results"). The content remains its authors'; the report quotes only short passages.
- **Addresses.** The authors' event logs, redistributed here unchanged because the original code needs them, contain borrower and liquidator addresses. The datasets built for this project contain only aggregates (for example, liquidation counts per regime) and no account addresses.
- **Third-party data.** The raw price downloads in `data/manual/raw/` remain subject to their providers' terms. The paper itself is not redistributed.

## History of this repository

The work was first committed to a private repository. Before publication, the history from the first commit written for this project onward was rewritten three times on 5 November 2026 with `git filter-repo`, for three reasons:

1. **Forum text without a licence** (`scripts/rewrite_governance_history.py`): the 54 posts and three unit texts described above were replaced, in every commit from the one that first added them (originally 5c8508a), by the same URL-and-hash placeholders. A search of all 140 commits for every replaced text found none.
2. **A revoked API key**: one exploratory notebook (`notebooks/dydx/analysis.ipynb`, from the commit originally 01673d1, 28 September 2026) contained an Alchemy RPC key. The key was revoked on 5 November 2026 and replaced by `<key>` in every commit.
3. **Author identity**: the author's commits were re-attributed to the name and GitHub no-reply address used in the published repository.

The authors' commits, including their final commit 41e1ae8 and every commit cited from their history, are unchanged. Commit dates and messages were kept; the content of the files changed only as described in 1 and 2. The hashes of the 65 commits written for this project changed: `REPLICATION_commit_map.tsv` maps each original hash to its published hash. Hashes in this file refer to the published history. Hashes cited inside files committed earlier (for example in `analysis_plans/`, `results/` and commit messages) refer to the original history and can be translated with the same map; the private repository, which keeps the original history and GitHub's record of when each push was received, can be made available for verification.

## Limitations

- The UIP criterion was fixed after the first run and compared test decisions only, which concealed the differences in coefficients until the comparison was broken down; every later test was pre-specified.
- The VECM was run in a newer version of Stata than the authors'; the version they used is unknown.
- The first LLM labelling used a web interface whose model and settings cannot be fixed; the second used a local model with recorded weights and settings, but 16 units and a single model.
- The VECM was checked against arXiv v3; the text of the ACM version may differ.
- The order of criteria and results in the published history rests on commit dates that were preserved through the rewrite; the original commits and push times are in the private repository, not in this one.
