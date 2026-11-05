# Replicating "DeFi Protocols for Loanable Funds" (Gudgeon et al., AFT 2020)

This repository reproduces, investigates and extends Gudgeon, Werner, Perez and Knottenbelt (2020),
*DeFi Protocols for Loanable Funds: Interest Rates, Liquidity and Market Efficiency*
([AFT '20](https://doi.org/10.1145/3419614.3423254); [arXiv:2006.13922](https://arxiv.org/abs/2006.13922)).
It is a fork of the authors' repository ([danhper/defi-plf-analysis](https://github.com/danhper/defi-plf-analysis));
their code and data are kept, and everything added for the replication is listed below.
The work was carried out by Luyao Wang for COMP8240 Applications of Data Science, Macquarie University, 2026.

- **Report:** [`report/final_report.pdf`](report/final_report.pdf)
- **Full record** (results, commit hashes for every criterion and result, environment, deviations): [`REPLICATION.md`](REPLICATION.md)
- **Every change to the authors' code:** [compare `master` with `replication-fixes`](https://github.com/wlysunny/defi-plf-replication/compare/master...replication-fixes)

## Main findings

1. The descriptive results (Section 5.1) reproduce from the authors' code and data, with two documented exceptions (dYdX token units). The cross-protocol cointegration estimates also reproduce, but the paper's pairwise long-run relationships are not uniquely identified.
2. The uncovered-interest-parity tests reproduce in their decisions (77 of 80 at the 1% level) but not in their coefficients (14 of 80 within 5%), after the exchange-rate source had to be replaced.
3. Rates near the kink rate reproduce, but an almost flat rate model can produce them, so they cannot show that utilisation converges to the kink. Judged by utilisation with tests fixed in advance, clustering holds in 0 of 3 of the paper's periods, and in 3 of 6 (cDAI, 2020–2025) and 7 of 12 (Aave V3, 2023–2025) new periods: mixed evidence, and not a general pattern in these markets. The cDAI count includes 2021, which is not robust to a block bootstrap; without it, it is 2 of 6.
4. The paper's rate series were compounded yields compared with a simple-rate model; read from the chain, the reported gap above the kink disappears.

## What is where

| Path | From | Contents |
|---|---|---|
| `compounds_research/`, `simulator/`, `notebooks/`, `misc/`, `setup.py`, `package.json`, `yarn.lock`, `.eslintrc.js` | Authors | Original analysis code; changed only as listed in `REPLICATION.md` ("Modifications to the original code") |
| `data/compound/`, `data/aave/`, `data/dydx/`, `data/stata/`, `data/cdai_new.pkl`, `data/eth-prices.json` | Authors | Original data, unchanged (large files in Git LFS) |
| `figures/compound/`, `figures/aave/` | Authors | The authors' figures |
| `README_original.md` | Authors | The authors' README, unchanged |
| `report/` | This project | Final report: PDF and LaTeX source |
| `REPLICATION.md` | This project | Results, provenance and the order of every commit that matters |
| `analysis_plans/` | This project | Criteria committed **before** each test, with appended amendments and post-hoc notes; annotation rules; the first (web-model) labelling record |
| `scripts/` | This project | All code written for the replication; [`scripts/README.md`](scripts/README.md) lists what each script reads and writes, and the order to run them |
| `data/onchain/` | This project | Constructed dataset: cDAI contract and rate-model state read from an archive node, 2019–2025 |
| `data/aave_v3/` | This project | Existing dataset collected from the official Aave V3 subgraph, 2023–2025, and rate-model parameters read from the chain |
| `data/manual/`, `data/derived/` | This project | Replacement exchange rates and the block-time table |
| `data/governance/`, `annotation/` | This project | Aave governance texts (see "Licences"), annotation units, and the researcher's, model's, arbitrated and final labels |
| `results/` | This project | Outputs of the scripts; `results/exploratory/` holds post hoc analyses that change no pre-specified decision |
| `figures/reproduction/`, `figures/report_*.pdf`, `figures/appx_*.pdf`, `figures/update/` | This project | Reproduced figures of the paper, figures of the report, figures of the progress presentation |
| `LICENSE` | This project | Which terms cover which files (see "Licences") |

## Reproducing

### Setup

```bash
git clone --branch replication-fixes https://github.com/wlysunny/defi-plf-replication.git   # master holds the authors' code unchanged
cd defi-plf-replication
git lfs pull
conda create --name defi-plf --file environment_snapshot.txt   # Apple Silicon; see REPLICATION.md for other systems
conda activate defi-plf
```

### Regenerating the figures from committed data

```bash
python scripts/make_report_figures.py      # main-text Figures 1 and 3
python scripts/make_appendix_figures.py    # appendix figures
python scripts/reproduce_exploration.py    # the paper's Section 5.1 figures, with the authors' functions
```

The VECM comparison figures (`python scripts/make_vecm_comparison.py`) read the paper's Figures 11–14 as vector graphics from
the arXiv PDF, which is not redistributed here: download [arXiv:2006.13922v3](https://arxiv.org/abs/2006.13922v3) to
`figures/paper/2006.13922v3.pdf` (ignored by Git). This script also needs `pip install pymupdf`.
The report compiles from `report/main.tex` (`cd report && latexmk -pdf main.tex`; needs a LaTeX installation).

### Full replication

These commands only redraw figures. Rerunning the analyses themselves (the reproduction of Tables 2 and A2–A7, the
investigation, the tests on new data and the annotation agreement) follows the order in `REPLICATION.md`
("Reproducing the results"); `scripts/README.md` lists what each script reads and writes.
All collected data are committed, so no network access or API key is needed to rerun the analyses.
The VECM needs Stata (`do scripts/vecm_replication.do`), which is not part of the conda environment.
Rebuilding the data from scratch needs an archive Ethereum RPC endpoint (`ETH_RPC_URL`) and, for the subgraph, a Graph API key
(`GRAPH_API_KEY`); no key is stored in the repository.

## Pre-registration

Each test followed a criterion committed before its first result, except the UIP comparison, whose criterion was fixed after a first run.
The order is recorded in the commit history and summarised, with hashes, in `REPLICATION.md`.
Commit times are an auditable record, not proof.

## Licences

- The authors' repository has no licence; their code and data are included here as a fork on GitHub, under GitHub's terms for forks. Please cite the original paper.
- Files written for this project: those in `scripts/` under the MIT License; all other project files under CC BY 4.0, except the third-party material listed in [`LICENSE`](LICENSE).
- Governance forum posts are stored in full only where the post carries a CC0 waiver. Other posts are replaced by their URL and the SHA-256 of their text; `python scripts/restore_governance_texts.py` downloads and verifies them.
- Raw price downloads in `data/manual/raw/` remain subject to their providers' terms.

## Citation

Please cite the original paper:

```bibtex
@inproceedings{gudgeon2020defi,
  author    = {Gudgeon, Lewis and Werner, Sam M. and Perez, Daniel and Knottenbelt, William J.},
  title     = {DeFi Protocols for Loanable Funds: Interest Rates, Liquidity and Market Efficiency},
  booktitle = {Proceedings of the 2nd ACM Conference on Advances in Financial Technologies (AFT '20)},
  pages     = {92--112},
  year      = {2020},
  doi       = {10.1145/3419614.3423254}
}
```
