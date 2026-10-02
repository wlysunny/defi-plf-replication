# LLM auxiliary labelling: prompt

Used for the auxiliary check described in `regime1_criterion.md`. The prompt below is pasted unchanged into a new conversation. The model's full response is saved to `llm_labelling_raw_output.txt`, and the model name and date are recorded in `llm_labelling_record.md`.

---

## Prompt (copy everything between the lines)

----------------------------------------------------------------
You will classify short code comments written by researchers. Each comment describes one period ("regime") of a lending market, after the researchers compared observed interest rates with the rates predicted by a model.

Classify each comment into exactly one category, using only the definitions below. Judge only what the comment says about how well the observations match the model's predictions (the "fit").

Categories:
- Good fit: the comment expresses a positive or "as desired" judgement and does not mention a mismatch.
- Poor fit: the comment states that observations do not match the modelled surface, or describes the regime as broken.
- Not stated: the comment describes only where the market sits relative to the "kink" (a threshold in the model), or is internally contradictory.

Comments:
0: Started out below the kink, performance perhaps as desired.
1: Not a good mapping to predicted surface --> unsure why.
2: Not a good mapping to predicted surface --> unsure why.
3: Not a good mapping to predicted surface --> unsure why.
4: OK, below kink, performance perhaps as desired
5: Tightly clustered at kink
6: Tightly clustered at kink and above
7: Performance improved - base rate dropped, worse performance
8: Completely broken again
9: Tightly clustered just above kink
10: Tightly clustered at kink

Answer with exactly 11 lines and nothing else, one per comment, in this format:
regime number|category|one short sentence explaining the choice

Example of the format (not an answer):
99|Not stated|The comment only describes the market's position.
----------------------------------------------------------------
