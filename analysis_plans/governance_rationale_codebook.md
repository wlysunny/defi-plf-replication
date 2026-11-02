# Codebook: governance rationales for changes of the kink on Aave V3

Committed before any unit was labelled, together with the units, the prompt and the scripts.

## Purpose

The paper reads the kink of the interest-rate model as a point at which rates change and argues that markets settle near it. Our Aave V3 test found mixed evidence (clustering by utilisation in 7 of 12 reserve-periods). This annotation asks what reasons Aave governance gave when it moved the kink, and how those texts frame the kink relative to utilisation: as a level the market settles at (the reading behind the paper's clustering claim), as a level utilisation should be kept below (a risk boundary), or only as a parameter. It is descriptive: with 16 units, no hypothesis is tested.

## Units

Each unit is one change of the optimal usage ratio (kink) on Aave V3 Ethereum Core between February 2023 and November 2025, as detected in `data/aave_v3/aave_v3_rate_params_daily.csv` (19 asset-level changes, merged by date into 16 actions). For each action, the unit text is the forum post that first specifies the new kink value that was implemented. The whole post is used, except where it has separate headed sections devoted to other assets, markets or parameters: those sections are removed, and the post's summary or opening and the section on this kink are kept. This applies to six units: A01 (a multi-asset report with a section per asset; the summary, abstract, objectives and USDT section are kept), A04 (separate sections on slope 1, the kink and the reserve factor), A05 (separate sections per asset and network), A06 (a follow-up post whose second part is devoted to the kink) and A12 and A13 (separate sections for the Ethereum Core and Prime markets; only Core is studied). Where other parameters are discussed in the same paragraphs as the kink, the whole post is kept. Image links and the Disclaimer and Copyright boilerplate are removed. The rule is implemented in `scripts/build_governance_units.py`, which checks each downloaded thread against the SHA-256 recorded in `data/governance/manifest.json`; the units are in `data/governance/units.jsonl` and, for the researcher, `data/governance/units_for_labelling.md`.

Disclosure: the units were identified, and this codebook written, by the researcher with an AI assistant (Claude) after reading the threads. The assistant does not label any unit.

## Labels

Every unit receives three labels. Labels describe what the text says, not whether the reason was correct or was accepted by others.

### 1. `rationale`: the main reason given for this change of the kink

Consider the reason attached to the kink change itself: sentences about the optimal ratio, UOptimal, Uopt or kink, or a purpose stated for the whole proposal that applies to all of its parameter changes (for example "to be competitive"). A purpose that concerns something else (for example onboarding a different asset) does not count.

| Code | Definition | Typical wording |
|---|---|---|
| `LIQUIDITY_BUFFER` | Keep or restore room between the kink and full utilisation, so that suppliers can withdraw and liquidations can be carried out; reduce the risk of 100% utilisation | "mitigate liquidity risks", "capacity for liquidations", "liquidity buffer" |
| `CAPITAL_EFFICIENCY` | Let more of the supplied funds be borrowed before rates rise steeply; increase revenue, borrowing or competitiveness | "capital efficiency", "increase borrow revenue", "competitive" |
| `RATE_STABILITY` | Dampen borrow-rate spikes or volatility that occur when utilisation is above the kink, for example after large withdrawals | "reduce rate volatility", "mitigate rate spikes", "buffer market stability" |
| `ALIGNMENT` | Match the parameters used in other markets or for other assets, or restore a standard or previous value, with no other reason given | "align with other markets", "revert to its parameters from before", "standard target" |
| `OTHER` | A reason is given for the kink change, but it fits none of the categories above | — |
| `NOT_STATED` | No reason is given for the kink change | — |

If several reasons are given, choose the one presented as the purpose of the kink change (for example after "to", "in order to", "aims to"); if several are so presented, choose the first. When one reason is presented as the means and another as its intended outcome, code the outcome that is stated; do not infer an unstated outcome from the mechanism. If the change covers several assets and the text gives different reasons for them, code the first reason given for a kink change. A vague reason that can be assigned to a category is coded with that category; `NOT_STATED` is used only when no reason for the kink change is given. For a change that reverses an earlier temporary change, label the reason given for the reversal: if the text says only that the earlier condition has ended and the previous or standard value is restored, use `ALIGNMENT`; if it gives another reason (for example restoring a liquidity buffer), use that.

### 2. `kink_framing`: how does the text frame the kink relative to utilisation?

| Code | Definition | Typical wording |
|---|---|---|
| `SETTLE_AT` | The kink is described as the level at which utilisation settles, or is intended or expected to settle: an equilibrium or target utilisation | "equilibrium around the optimal utilization", "our utilization target", "standard target of 92%" |
| `KEEP_BELOW` | Utilisation is meant to stay below the kink, or utilisation above the kink is presented as the problem the change addresses, without the kink being described as a target or equilibrium | "stabilize borrows under the UOptimal point", "revert utilization below the kink", "utilization above Uoptimal" |
| `PARAMETER_ONLY` | The kink is mentioned only as a parameter value, with no statement about where utilisation should be relative to it | — |

If a text contains both kinds of statement, code `SETTLE_AT` only if it explicitly calls the kink (or the new value) a target or equilibrium level of utilisation; otherwise code `KEEP_BELOW`. Mentioning the parameter's name ("optimal utilization") is not sufficient for either. Only `SETTLE_AT` corresponds to the reading behind the paper's clustering claim; `KEEP_BELOW` treats the kink as a boundary and is not evidence that markets cluster at it.

### 3. `temporary`: does the text say that this change is intended to be reversed later?

`yes` only if the change itself is described as temporary or short-term. A change that is a step in rolling back an earlier temporary change is `no` unless it is itself described as temporary.

## Procedure

1. The researcher labels all 16 units in `annotation/researcher_labels.csv`, using this codebook and `data/governance/units_for_labelling.md`, without seeing any model output, and commits the labels.
2. Only then is `scripts/label_governance_llm.py` run. It refuses to run unless the units, this codebook and the script itself are unchanged since the commit that added the researcher's labels, so that both label sets are based on the same texts and rules. It sends each unit with the prompt below to a locally run open-weight model through Ollama: `qwen2.5:7b-instruct` (Ollama ID 845dbda0ea48; the full digest is recorded at run time), temperature 0, seed 8240, context 8,192 tokens, JSON output. Raw requests and responses, the model digest and the Ollama version are saved in `annotation/llm_raw_outputs.jsonl` and the labels in `annotation/llm_labels.csv`. The model's `evidence` quote is explanatory only and does not affect whether a reply is valid; the script records whether it occurs verbatim in the unit text. A reply that is not valid JSON or uses a code outside the codebook is retried once with the same request; if it fails again it is recorded as `INVALID` and counted as a disagreement. Each request and response is appended to the raw file as soon as it is received. The script refuses to run if the output files already exist. If a run is interrupted, the partial file is kept under another name and documented, and all 16 units are labelled again with the unchanged prompt; outputs from different runs are not combined.
3. `scripts/governance_agreement.py` reports, for each label, the percentage agreement and Cohen's κ between the researcher's and the model's labels, which were produced without either seeing the other, with the confusion table. `INVALID` is treated as an additional, model-only category and counted as a disagreement; all 16 units remain in the denominator. If κ is undefined (for example when both label sets use a single category), it is reported as undefined. With 16 units, κ is reported as a descriptive measure of consistency, alongside the percentage agreement.
4. The researcher then reviews every disagreement against the text and records a final label with a short reason in `annotation/arbitration.csv`. Agreement is reported on the independent labels, before arbitration; the final labels are used for the description.

A local open-weight model is used so that its weights (identified by a digest), configuration and requests can be recorded and the labelling can be rerun under closely matched conditions; a model reached through a web interface cannot be pinned in this way. Identical outputs across different software and hardware are not guaranteed.

## Prompt

The prompt sent for each unit is built in `scripts/label_governance_llm.py` from this codebook: the three label definitions and decision rules above, the unit's assets, kink change and date, and the unit text, followed by the instruction to answer with a JSON object containing `rationale`, `kink_framing`, `temporary` and a short verbatim `evidence` quote.

## Reporting

The report gives the distribution of each label (overall, and for the six changes made through governance votes in 2023–2024, A01–A06, against the ten made through the Risk Steward process in 2025, A07–A16), the agreement statistics, and the arbitrated disagreements.

## Limitations recorded in advance

- 16 units, all from one market and a small number of authors (mainly Chaos Labs, Gauntlet and the Aave Chan Initiative); κ on 16 units has a wide margin of error.
- The codebook was written after the texts were read, by the researcher with an AI assistant, so the categories fit these texts; they are not drawn from an existing scheme.
- The researcher who labels is also the person who arbitrates.
- The model receives the same definitions as the researcher, and the researcher took part in building the units and the codebook, so agreement shows that the definitions can be applied consistently, not that the labels are valid.
- The labels describe the selected proposal posts, not the whole discussion thread or the views of all participants; a later post in a thread may explain a change more fully.
- The comparison between governance-vote actions (2023–2024) and Risk Steward actions (2025) is descriptive: governance process and calendar period coincide, so differences between the groups cannot be attributed to the process.
- A post states the proposer's reasons; other participants sometimes disagreed (for example Gauntlet opposed the change in A05), and those views are not labelled.
- A recommendation in the same thread to raise the USDT kink to 95% on 17 July 2025 (post 22279/7) has no corresponding change in the daily on-chain data and is not a unit; changes made and reversed within one day would not be detected by daily sampling.
