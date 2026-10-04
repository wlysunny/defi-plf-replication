# Scripts added for the replication

All scripts in this directory were written for the replication; the original authors' code is unchanged in `compounds_research/`, `simulator/` and `notebooks/`. Every script is run from the repository root, for example `python scripts/compare_uip.py`, because data and result paths are relative to the root.

Scripts that read blockchain state need an archive-capable Ethereum RPC endpoint in the environment variable `ETH_RPC_URL`; the Aave V3 subgraph collector needs a Graph API key in `GRAPH_API_KEY`. Neither key is written to any file. Collection scripts print no summary statistics, so that test criteria could be fixed before the data were examined.

File names indicate the role of each script: `collect_` and `build_` scripts create data, `simulate_` scripts check decision rules on synthetic data with known answers, analysis scripts implement the pre-specified tests in `analysis_plans/`, and `exploratory_` scripts are post hoc analyses that do not change any pre-specified decision.

## 1. Replication of the original analyses

| Script | Reads | Writes | Purpose |
|---|---|---|---|
| `clean_manual_prices.py` | `data/manual/raw/` | `data/manual/*_cleaned.csv` | Cleans the hand-collected REP and SAI prices that replace the discontinued CryptoCompare series |
| `compare_uip.py` | UIP notebook on `master` and on this branch | `results/uip_comparison.csv` | Compares the parity tests with the authors' saved output, pair by pair |
| `build_block_times.py` | chain (`ETH_RPC_URL`) | `data/derived/eth_block_times_sampled.csv` | Sampled block-number/timestamp table used to convert times to blocks |

The exchange-rate fetcher that replaces CryptoCompare is part of the original package structure: `compounds_research/compound/fetch_exchange_rates_defillama.py`.

## 2. Investigation of the cDAI rate regimes

| Script | Reads | Writes | Criterion |
|---|---|---|---|
| `simulate_regime1.py` | synthetic | `results/regime1_simulation_check.csv` | `regime1_criterion.md` |
| `regime1_analysis.py` | `data/compound/cdai.pkl`, LLM labels | `results/regime1_results.json`, `results/regime1_error_by_regime.csv` | `regime1_criterion.md` (with Amendment 1) |
| `exploratory_onchain_check.py` | chain | `results/exploratory/onchain_rate_check.json` | exploratory |
| `annotate_regimes.py` | on-chain panels, `cdai.pkl`, event log | `results/regime_annotation.*`, `results/regime_onchain_changes.csv` | `regime_annotation_rules.md` |

## 3. Newly constructed dataset: on-chain cDAI panel

| Script | Reads | Writes | Criterion |
|---|---|---|---|
| `collect_onchain_cdai.py` | chain | `data/onchain/cdai_panel.csv` (about daily, 2019-11 to 2025-11); with `--dense-2020`, `data/onchain/cdai_panel_dense_2020.csv` (about hourly) | — |
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

## Order of execution

Collection (network access, slow): `build_block_times.py`, `collect_onchain_cdai.py` (twice, with and without `--dense-2020`), `collect_aave_v3_subgraph.py --list-reserves`, `collect_aave_v3_subgraph.py`, `collect_aave_v3_rate_params.py`. All collected data are committed, so this step is only needed to rebuild them.

Analysis (offline, from committed data): the `simulate_` script of each test, then the corresponding analysis script, then the exploratory scripts. Analyses use fixed random seeds, so re-running them reproduces the committed result files exactly.
