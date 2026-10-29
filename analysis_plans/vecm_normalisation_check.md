# Planned check: is the long-run structure in Tables A6–A7 a normalisation?

Written before the check was run. Exploratory; it does not change the replication verdicts.

With rank 2, Stata's default Johansen normalisation sets the coefficients of the first two variables in the `vec` command to an identity matrix. In the authors' order (Compound, Aave, dYdX) this makes each cointegrating equation contain dYdX and exactly one of the other two protocols, which the paper reads as "Compound and dYdX share a long-run relationship, and Aave and dYdX share a long-run relationship".

Check: re-estimate both models with the same data, lags and rank, but in the order (dYdX, Compound, Aave).

Prediction if the structure is only a normalisation:
1. The log likelihood is identical (DAI 881.4047; USDC 1302.69).
2. The long-run impact matrix Pi = alpha * beta' is identical, after matching rows and columns by variable.
3. The reported beta changes: each equation now contains Aave and exactly one of dYdX and Compound, and the reported alpha changes accordingly.

If 1 or 2 fails, the prediction is rejected.

## Follow-up (written after the reordering check, before this test)

Exploratory. In the reordered USDC model one adjustment coefficient of Compound is significant (z = -3.07), although both are insignificant in the authors' order. Individual adjustment coefficients depend on the normalisation; the paper's claim that Compound "has market power" (does not adjust) should instead be judged by a joint test that the whole row of alpha for a protocol is zero (weak exogeneity), which does not depend on the normalisation.

Test: after each model, a Wald test that both adjustment coefficients of each protocol are zero, in both variable orders.

Predictions:
1. Each statistic is identical in the two orders.
2. If Compound "has market power" in the paper's sense, the test for Compound is not rejected at 5%, for DAI and for USDC.
