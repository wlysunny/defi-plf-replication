# Scripts added for the replication

All scripts in this directory were written for the replication (`vecm_replication.do` is a copy of the authors' `notebooks/VECM.do` with paths changed and a log added). The authors' code is preserved unchanged on the `master` branch; on `replication-fixes` it carries only the documented compatibility changes listed in `REPLICATION.md` ("Modifications to the original code"). Every script is run from the repository root, for example `python scripts/compare_uip.py`, because data and result paths are relative to the root. The three `.do` files are run in Stata from the repository root, for example `do scripts/vecm_replication.do`.

Scripts that read blockchain state need an archive-capable Ethereum RPC endpoint in the environment variable `ETH_RPC_URL` (the second-provider check also uses `ETH_RPC_URL_2`); the Aave V3 subgraph collector needs a Graph API key in `GRAPH_API_KEY`. No key is written to any file. Collection scripts print no summary statistics, so that test criteria could be fixed before the data were examined.

File names indicate the role of each script: `collect_` and `build_` scripts create data, `simulate_` scripts check decision rules on synthetic data with known answers, analysis scripts implement the pre-specified tests in `analysis_plans/`, `exploratory_` scripts are post hoc analyses that do not change any pre-specified decision, and `make_` scripts draw figures from committed data.

## 1. Replication of the original analyses

| Script | Reads | Writes | Criterion / purpose |
|---|---|---|---|
| `reproduce_exploration.py` | `notebooks/exploration.ipynb` (cells executed unchanged), the authors' data | `results/reproduction_table2.csv`, `figures/reproduction/` | Table 2 and Figures 1–5; `reproduction_liquidity_wealth_criterion.md` |
| `reproduce_concentration.py` | `notebooks/compound/compound-wealth.ipynb` (cells executed unchanged), `data/compound/events/` | `results/reproduction_concentration.csv` | Figure 6, all events and events to 2020-06-04; same criterion, Amendment 2 |
| `clean_manual_prices.py` | `data/manual/raw/` | `data/manual/*_cleaned.csv` | Cleans the hand-collected REP and SAI prices that replace the discontinued CryptoCompare series |
| `compare_uip.py` | UIP notebook on `master` and on this branch | `results/uip_comparison.csv` | Compares the parity tests with the authors' saved output, pair by pair |
| `verify_uip_cache_append.py` | DefiLlama price caches, their committed versions | printed only (exit status 1 on failure) | Checks the cache update of the UIP window correction; `uip_window_correction.md` |
| `vecm_replication.do` | `data/stata/` | `results/vecm/` (log, tables, ten figures) | Copy of `notebooks/VECM.do` with paths changed and a log added; `vecm_replication_criteria.md` |
| `vecm_normalisation_check.do` | `data/stata/` | `results/vecm/normalisation_log.txt` | Re-estimation with a different variable order; `vecm_normalisation_check.md` |
| `vecm_weak_exogeneity.do` | `data/stata/` | `results/vecm/weak_exogeneity_log.txt` | Joint tests of weak exogeneity; follow-up in `vecm_normalisation_check.md` |
| `build_block_times.py` | chain (`ETH_RPC_URL`) | `data/derived/eth_block_times_sampled.csv` | Sampled block-number/timestamp table used to convert times to blocks |

The exchange-rate fetcher that replaces CryptoCompare is part of the original package structure: `compounds_research/compound/fetch_exchange_rates_defillama.py`.

## 2. Investigation of the cDAI rate regimes

| Script | Reads | Writes | Criterion |
|---|---|---|---|
| `simulate_regime1.py` | synthetic | `results/regime1_simulation_check.csv` | `regime1_criterion.md` |
| `regime1_analysis.py` | `data/compound/cdai.pkl`, LLM labels | `results/regime1_results.json`, `results/regime1_error_by_regime.csv` | `regime1_criterion.md` (with Amendment 1) |
| `exploratory_onchain_check.py` | chain | `results/exploratory/onchain_rate_check.json` | exploratory |
| `exploratory_timelock_check.py` | chain (Timelock events in narrow windows) | `results/exploratory/timelock_check.json` | exploratory |
| `exploratory_apy_check.py` | on-chain panels, `data/compound/cdai.pkl` | `results/exploratory/apy_check.json` | exploratory (units of the API rates) |
| `annotate_regimes.py` | on-chain panels, `cdai.pkl`, event log | `results/regime_annotation.*`, `results/regime_onchain_changes.csv` | `regime_annotation_rules.md` |

## 3. Newly constructed dataset: on-chain cDAI panel

| Script | Reads | Writes | Criterion |
|---|---|---|---|
| `collect_onchain_cdai.py` | chain | `data/onchain/cdai_panel.csv` (about daily, 2019-11 to 2025-11); with `--dense-2020`, `data/onchain/cdai_panel_dense_2020.csv` (about hourly) | — |
| `second_provider_check.py` | both on-chain panels, `data/aave_v3/aave_v3_rate_params_daily.csv`, chain (`ETH_RPC_URL`, `ETH_RPC_URL_2`) | `results/second_provider_self_check.json` (`--self-check`), `results/second_provider_check.json` | `second_provider_check_criterion.md` |
| `simulate_kink_clustering.py` | synthetic | `results/kink_clustering_simulation_check.csv` | `kink_clustering_criterion.md` |
| `kink_clustering_analysis.py` | on-chain panels | `results/kink_clustering_results.json` | `kink_clustering_criterion.md` |
| `exploratory_kink_followup.py` | dense panel, `cdai.pkl` | `results/exploratory/kink_followup.json` | exploratory |

## 4. Existing dataset: Aave V3 (Ethereum, Core market)

| Script | Reads | Writes | Criterion |
|---|---|---|---|
| `collect_aave_v3_subgraph.py` | Aave V3 subgraph (`GRAPH_API_KEY`) | `data/aave_v3/aave_v3_reserves.json`, `data/aave_v3/aave_v3_daily_panel.csv` | — |
| `collect_aave_v3_rate_params.py` | chain | `data/aave_v3/aave_v3_rate_params_daily.csv`, `data/aave_v3/aave_v3_sample_blocks.csv` | — |
| `simulate_aave_kink.py` | synthetic | printed only | `aave_kink_criterion.md` |
| `aave_kink_analysis.py` | both Aave files | `results/aave_kink_results.json` | `aave_kink_criterion.md` |
| `exploratory_aave_validation.py` | both Aave files | `results/exploratory/aave_validation.json` | exploratory |

## 5. Annotation of governance rationales

| Script | Reads | Writes | Criterion |
|---|---|---|---|
| `collect_governance_threads.py` | Aave governance forum, public raw endpoint (no key) | `data/governance/raw/`, `data/governance/manifest.json` | `governance_rationale_codebook.md` |
| `build_governance_units.py` | `data/governance/raw/` (checked against the manifest), `data/aave_v3/aave_v3_rate_params_daily.csv` | `data/governance/units.jsonl`, `data/governance/units_for_labelling.md` | same |
| — (researcher) | `units_for_labelling.md`, codebook | `annotation/researcher_labels.csv`, committed before the model is run | same |
| `label_governance_llm.py` | units, codebook; Ollama with `qwen2.5:7b-instruct` | `annotation/llm_raw_outputs.jsonl`, `annotation/llm_labels.csv` | same; refuses to run before the researcher's labels are committed |
| `governance_agreement.py` | researcher and model labels | `results/governance_agreement.json` | same |
| — (researcher) | disagreements | `annotation/arbitration.csv` | same |
| `governance_final_labels.py` | researcher labels, `annotation/arbitration.csv` | `annotation/final_labels.csv`, `results/governance_final_summary.json` | same |

## 6. Figures

| Script | Reads | Writes |
|---|---|---|
| `make_report_figures.py` | on-chain panels, `data/compound/cdai.pkl`, Aave V3 data, final governance labels | `figures/report_fig1_kink.pdf`, `figures/report_fig_aave.pdf` (main-text Figures 1 and 3) |
| `make_appendix_figures.py` | `results/exploratory/apy_check.json`, on-chain panel, `data/compound/events/`, annotation labels | `figures/appx_api_gap.pdf`, `figures/appx_cdai_periods.pdf`, `figures/appx_concentration.pdf`, `figures/appx_confusion.pdf` |
| `make_vecm_comparison.py` | `results/vecm/*.pdf`, the paper's PDF at `figures/paper/2006.13922v3.pdf`: not redistributed; download it from https://arxiv.org/pdf/2006.13922v3 (Git ignores `figures/paper/`); needs `pip install pymupdf` | `figures/appx_vecm_rates.pdf`, `figures/appx_vecm_irf.pdf` |
| `make_update_figures.py` | committed data | `figures/update/` (figures of the progress presentation) |
| `make_fig9_paper_style.py` | committed data | `figures/update/` (the paper's Figure 9 in the authors' own format, for the progress presentation) |

## 7. Licensing of forum posts

| Script | Reads | Writes | Purpose |
|---|---|---|---|
| `redact_governance_texts.py` | `data/governance/`, `annotation/llm_raw_outputs*.jsonl` | same files; `data/governance/post_manifest.json`, `data/governance/redaction_record.json` | Keeps posts with a CC0 waiver; replaces the others by URL and SHA-256 |
| `restore_governance_texts.py` | forum (public raw endpoint), the two records | restored originals | Downloads the replaced posts, checks each hash and restores the files byte for byte |
| `rewrite_governance_history.py` | Git history | rewritten history | Removed the replaced texts from earlier commits before publication (run once) |

## Order of execution

**1. Collection** (network access, slow; all collected data are committed except governance forum posts without a CC0 waiver, which are stored as URL and SHA-256 and restored with `scripts/restore_governance_texts.py`; so this step is only needed to rebuild the data): `build_block_times.py`, `collect_onchain_cdai.py` (twice, with and without `--dense-2020`), `collect_aave_v3_subgraph.py --list-reserves`, `collect_aave_v3_subgraph.py`, `collect_aave_v3_rate_params.py`, `collect_governance_threads.py`. The UIP price caches are filled by `compounds_research/compound/fetch_exchange_rates_defillama.py`; the REP and SAI prices were downloaded by hand into `data/manual/raw/`.

**2. Analyses that read only committed data** (offline):
- Reproduction: `clean_manual_prices.py`, `reproduce_exploration.py`, `reproduce_concentration.py`, `compare_uip.py` (after a cache update, `verify_uip_cache_append.py` before committing the caches), and in Stata the three `.do` files.
- Pre-specified tests: for each test the `simulate_` script, then the analysis script (`regime1_analysis.py`, `kink_clustering_analysis.py`, `aave_kink_analysis.py`), and `annotate_regimes.py`.
- Exploratory analyses that read committed data: `exploratory_apy_check.py`, `exploratory_kink_followup.py`, `exploratory_aave_validation.py`.

**3. Checks that query the chain again** (network access, `ETH_RPC_URL`): `exploratory_onchain_check.py`, `exploratory_timelock_check.py`, and `second_provider_check.py` (first with `--self-check`, then the main run with `ETH_RPC_URL_2`).

**4. Governance annotation**, with two manual steps: `build_governance_units.py`; the researcher's labels in `annotation/researcher_labels.csv`, which must be complete and committed before the model is run (`label_governance_llm.py` refuses to run otherwise); `label_governance_llm.py` (needs Ollama running locally with `qwen2.5:7b-instruct`); `governance_agreement.py`; the researcher's arbitration of disagreements in `annotation/arbitration.csv`, which must exist before the final step; `governance_final_labels.py`.

**5. Figures** (offline): the three report scripts of section 6; `make_vecm_comparison.py` first needs the paper's PDF, downloaded as described there.

Analyses use fixed random seeds and the software versions recorded in `environment_snapshot.txt` and `REPLICATION.md`. The committed results were produced in that environment; exact equality of outputs in other environments (Python, Stata or numerical-library versions, operating system) is not guaranteed. The language-model labels are reproducible only under closely matched software and hardware (see the codebook).
