# Annotation units: governance rationales for kink changes

Label each unit with the codebook in analysis_plans/governance_rationale_codebook.md.

---

## A01 | USDT | kink 90% -> 80% | effective 2023-05-22

Source: https://governance.aave.com/t/12921/1 (wfu, 2023-04-28 04:51:25 UTC) — excerpt

[Text not redistributed: the post states no licence. Source: https://governance.aave.com/t/12921/1. SHA-256 of the original text: 5fcd6e2c03922498cc4b3267ca6715e4889aed9219b21da589ea33c8c130aec6. Restore with scripts/restore_governance_texts.py.]

---

## A02 | DAI, WETH | kink 80% -> 90% | effective 2023-08-28

Source: https://governance.aave.com/t/14410/1 (MarcZeller, 2023-08-22 09:15:16 UTC)

> Proposal edited following feedback

**Title**: [ARFC] sDAI Aave V3 Onboarding

**Author**: Marc Zeller @marczeller - Aave Chan Initiative, Chaos Labs

**Date**: 2023-08-09

**Summary**:

This proposal seeks to onboard sDAI as a collateral-only asset into the Aave V3 Ethereum pool. It outlines the specific parameters for integration and aims to create new synergies with the MakerDAO ecosystem.

**Motivation**:

The recent increase in the DSR (Dai Savings Rate) to 8%—though anticipated to decrease to 5%—presents a unique opportunity for Aave to forge new synergies with the MakerDAO ecosystem. By integrating liquid DSR deposit tokens (sDAI) as a collateral-only asset in the Aave V3 Ethereum pool, Aave can offer users the dual benefit of earning DSR yield while utilizing their assets as collateral. In the context of GHO, this integration would create a yield-generating stablecoin with a higher yield than the GHO borrow cost. It's important to note that this proposal does not conflict with the [DSR integration in aDAI reserve proposal](https://governance.aave.com/t/temp-check-integrating-makerdaos-dsr-into-aave-v3-ethereum-pool/13360), but rather complements it. However, current engineering constraints make immediate integration difficult in the short-term. Should governance approve this proposal, both sDAI and DAI would serve as reserves in the Aave V3 Ethereum pool, with sDAI primarily used as collateral and DAI as a borrowable asset.

**Specification**:

We propose the following modifications to the Aave V3 & V2 Ethereum pools:

sDAI contract: 0x83F20F44975D03b1b09e64809B757c47f942BEeA

| Parameter | Value |
| --- | --- |
| wETH Optimal Ratio on V3 | from 80% to 90% |
| wETH base rate on V3 | from 1% to 0% |
| DAI RF on V2 | from 15% to 25% |
| DAI RF on V3 | from 10% to 20% |
| DAI optimal ratio on V3 | from 80% to 90% |
| DAI Slope1 on V3 | from 4% to 5% |
| DAI Slope1 on V2 | from 4% to 5% |
| DAI stable Borrow | disabled on V2 |
| sDAI parameters | same as DAI but as collateral only |
| LTV | 77% |
| LT | 80% |
| Liquidation penalty | 4.5% |

---

## A03 | WETH | kink 90% -> 80% | effective 2023-11-16

Source: https://governance.aave.com/t/15110/1 (MarcZeller, 2023-10-13 10:33:47 UTC)

---
title: [ARFC] upgrade Aave V3 ETH pool wETH parameters 
author: @marczeller - Aave-chan Initiative, @Gauntlet 
date: 2023-10-13
---

## Summary

This ARFC proposes an update to the `slope1` parameters of WETH in the Aave V3 Ethereum pool. With the stabilization of [staking market](https://www.validatorqueue.com/), we believe it's time to adjust the `slope1` to better align with the current yields of stETH and reth.

## Motivation

The current yields of stETH and reth have been observed at 3.3% and 3.07% respectively. By adjusting the `slope1` parameter of WETH, we aim to:

1. **Enhance Profitability in Leverage Loops**: The proposed adjustment will make leverage loops more profitable for users.
2. **Align with stETH and reth Yields**: The adjustment aims to set the `slope1` slightly below the current yields of stETH and reth, ensuring Aave remains competitive.

Increased utilization of ETH reserve is expected to partly compensate for the slight loss of protocol revenue due to lower interest rate equilibrium.

## Specification

We propose two options for the `slope1` parameters:

1. **Conservative Option**: Set `slope1` to 3.2%. 10 bps below stETH yield but above rETH yield
2. **Aggressive Option**: Set `slope1` to 2.8%. 50 below stETH yield & 23bps below rETH yield allowing both to be profitable.

Additionally, we propose reducing the `optimalRatio` to 80% to mitigate liquidity risks.

According to the https://governance.aave.com/t/arfc-arfc-and-temp-check-framework/13828/ 320k YAE on either the conservative or aggressive option are necessary to meet quorum.

## Next Steps

1. Gather community feedback on the proposed changes.
2. If consensus is reached, escalate this proposal to ARFC snapshot stage.
3. If ARFC snapshot outcome is YAE, escalate to AIP stage.

---

## A04 | USDT | kink 80% -> 90% | effective 2023-11-27

Source: https://governance.aave.com/t/15096/2 (Gauntlet, 2023-10-28 01:41:09 UTC) — excerpt

[Text not redistributed: the post states no licence. Source: https://governance.aave.com/t/15096/2. SHA-256 of the original text: b79d3c3fca103e40caa1fd32ba8d85e0cd6c435bbe8b1a4a19ece6b03100eb55. Restore with scripts/restore_governance_texts.py.]

---

## A05 | WETH | kink 80% -> 90% | effective 2024-01-31

Source: https://governance.aave.com/t/16168/1 (ACI, 2024-01-12 16:24:41 UTC) — excerpt

# **Summary**

This ARFC proposes to update sETH and WETH risk parameters on the Aave V3 Ethereum Mainnet, OP Mainnet and Arbitrum.

## Motivation

We propose updating the stETH and WETH risk parameters to be optimal and competitive in the current market landscape. This will maintain Aave’s position as the prime liquidity protocol by increasing our protocol attractiveness for users looking to maximize their capital efficiency.

[...]

********WETH Ethereum********

| Risk Parameter | Current Value | Proposed Value |
| --- | --- | --- |
| Reserve Factor | 15% | 10% |
| Optimal Ratio | 80% | 90% |

Other parameters will remain unchanged.

---

## A06 | DAI, USDC, USDT | kink 90% -> 92% | effective 2024-04-10

Source: https://governance.aave.com/t/16864/2 (ChaosLabs, 2024-04-04 14:21:20 UTC) — excerpt

[Text not redistributed: the post states no licence. Source: https://governance.aave.com/t/16864/2. SHA-256 of the original text: 5ebbd1205c290c047a51ed3fec542e0b8473c4150b2ff970576082e95aa08d75. Restore with scripts/restore_governance_texts.py.]

---

## A07 | USDT | kink 92% -> 95% | effective 2025-06-09

Source: https://governance.aave.com/t/22279/2 (ChaosLabs, 2025-06-09 08:57:40 UTC)

## Overview

Following a renewed wave of USDT withdrawals by Huobi, further exacerbating rate volatility, we propose temporary adjustments to the IR parameters for USDT on the Aave V3 Ethereum deployment. Specifically, Chaos Labs recommends increasing the UOptimal from 92% to 95% and concurrently reducing the Slope2 parameter from 22.5% to 14%. These changes are intended as short-term measures to buffer market stability during this period of heightened utilization, with the original parameters to be reinstated upon the anticipated redeposit of USDT by Huobi.

Raising the UOptimal to 95% will meaningfully reduce the magnitude of liquidity needed to revert utilization below the kink, thereby enhancing the responsiveness of interest rates. At current utilization levels of 97%, with a total USDT supply of $3.51B and a UOptimal of 92%, the system requires either $150M in debt repayments or supply deposits to normalize rates. Increasing UOptimal to 95% reduces this requirement to approximately $50M, allowing smaller market actions to achieve faster rate corrections.

To maintain a consistent rate gradient in the post-kink region under the revised curve, a reduction in Slope2 to 14% is proposed. These parameter modifications are explicitly designed as temporary stabilization measures. Chaos Labs intends to revert to the existing USDT interest rate model once the supply-side liquidity is sufficiently restored.

## Recommendation

|**Asset**|**Market**|**Current Slope 2**|**Recommended Slope 2**|**Current UOptimal**|**Recommended UOptimal**|
| --- | --- | --- | --- | --- | --- |
|USDT|Ethereum Core|22.5%|14%|92%|95%|

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

---

## A08 | USDT | kink 95% -> 92% | effective 2025-06-14

Source: https://governance.aave.com/t/22279/3 (ChaosLabs, 2025-06-13 20:01:05 UTC)

### Summary

Chaos Labs recommends reverting the Slope2 parameter of USDT on Aave V3 Ethereum from  14% to 22.5% and UOptimal from 95% to 92% following significant new deposits.

### Motivation

Earlier this week, HTX, the largest USDT supplier on Aave, withdrew approximately 800 million USDT, which abruptly pushed the market utilization to 100%, triggering the jump in variable borrow rates to above UOptimal and spiking borrowing costs to around 40%. As a result, we responded with two actions: first reducing Slope 2 to 22.5%, then reducing Slope 2 to 14% and increasing UOptimal to 95%. 

However, beginning on June 10, the HTX account began depositing in the market again, beginning first with a 300M deposit, then adding more than 400M USDT total across multiple transactions

As a a result, utilization in the market has fallen to 86.2% as of this writing, far below the new UOptimal of 95%. 

To account for this significant change in the market, we propose reverting USDT’s IR curve to its parameters from before the withdrawal was conducted: increasing Slope 2 and decreasing UOptimal. 

### Specification

| **Asset** | **Market** | **Current Slope 2** | **Recommended Slope 2** | Current UOptimal | Recommended UOptimal |
| --- | --- | --- | --- | --- | --- |
| USDT | Ethereum Core | 14% | 22.5% | 95% | 92% |

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

---

## A09 | USDT | kink 92% -> 94% | effective 2025-08-13

Source: https://governance.aave.com/t/22279/16 (ChaosLabs, 2025-08-13 10:39:41 UTC)

# **Overview**

Following a renewed wave of 1B USDT withdrawals by Huobi, further exacerbating rate volatility, we propose temporary adjustments to the IR parameters for USDT on the Aave V3 Ethereum deployment. Specifically, Chaos Labs recommends increasing the UOptimal from 92% to 94% and concurrently reducing the Slope2 parameter from 22.5% to 14%. These changes are intended as short-term measures to buffer market stability during this period of heightened utilization, with the original parameters to be reinstated upon the anticipated redeposit of USDT by Huobi.

# Specification

| **Asset** | **Market** | **Current Slope 2** | **Recommended Slope 2** | **Current UOptimal** | **Recommended UOptimal** |
|:---|:---|:---|:---|:---|:---|
| USDT | Ethereum Core | 22.5% | 14% | 92% | 94% |

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

---

## A10 | USDT | kink 94% -> 92% | effective 2025-08-28

Source: https://governance.aave.com/t/22279/17 (ChaosLabs, 2025-08-27 21:44:59 UTC)

Following the recent inflow of $1B in redeposits originating from Huobi, an event that has contributed to market stabilization, Chaos Labs recommends restoring the Optimal Utilization parameter to its standard target of 92%. 

# Specification

| **Asset** | **Market** | **Current UOptimal** | **Recommended UOptimal** |
| --- | --- | --- | --- |
| USDT | Ethereum Core | 94% | 92% |

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

---

## A11 | WETH | kink 90% -> 93% | effective 2025-07-16

Source: https://governance.aave.com/t/22279/6 (ChaosLabs, 2025-07-16 13:18:30 UTC)

# **Summary**

Chaos Labs recommends reducing the Slope2 and increasing the UOptimal parameters for USDT and WETH on Aave V3 Ethereum following withdrawals by Huobi and increased demand for leverage. Specifically, we propose reducing Slope2 to 14% for USDT, 60% for WETH on Core and 65% for WETH on Prime instance. Additionally we proposre increasing UOptimal to 93% for WETH on Core and to 92% for WETH on Prime.

# **Motivation**

Huobi withdrew approximately 700 million USDT and 30,000 WETH from Aave V3 Ethereum, sharply increasing utilization on both assets. These actions have led to heightened interest rate volatility and elevated borrowing costs, impacting users reliant on rate stability.

At the same time, we observe increased demand for leverage across DeFi markets, further contributing to high utilization levels on Aave. In this context, preserving stable and predictable borrowing costs is critical for supporting healthy market functioning and user retention. We plan to provide a more detailed analysis on the overall increase in borrowing demand observed across the markets in a separate post, alongside optimal risk parameterization associated with such an increase.

To mitigate short-term rate spikes we propose temporary adjustments to the interest rate curves. These changes aim to soften the slope beyond the kink and expand the buffer before high rates are triggered.

We intend to revert these parameters once utilization levels normalize in accordance with traditional Huobi market operations.

# Specification

| Asset | Market | Current Slope2 | Recommended Slope2 | Current UOptimal | Recommended UOptimal |
| --- | --- | --- | --- | --- | --- |
| USDT | Ethereum Core | 22.5% | 14% | 92% | - |
| WETH | Ethereum Core | 80% | 60% | 90% | 93% |
| WETH | Ethereum Prime | 85% | 65% | 90% | 92% |

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

---

## A12 | WETH | kink 93% -> 94% | effective 2025-07-19

Source: https://governance.aave.com/t/22279/10 (ChaosLabs, 2025-07-19 09:37:28 UTC) — excerpt

# **Summary**

Chaos Labs recommends reducing the Slope2 and increasing the UOptimal parameters for WETH on Aave V3 Ethereum Core and Prime following more withdrawals by HTX and increased demand for leverage. 

Specifically, we propose reducing Slope2 by 20pp for both markets and increasing UOptimal by 1pp for WETH Ethereum Core. 

# **Motivation**

HTX continued withdrawing WETH from Aave V3 Ethereum, sharply increasing utilization and increasing borrow rates. The largest withdrawal was of 43K WETH, or about $150M. The [wallet](https://community.chaoslabs.xyz/aave/risk/wallets/0x18709e89bd403f470088abdacebe86cc60dda12e) maintains a balance of 22.63K WETH alongside 1.06B USDT as of this writing, raising the possibility that they could withdraw more WETH. 

The withdrawn ETH appears to have been moved to an HTX Hot Wallet before being moved to a Binance Deposit address, making it unclear whether this supply will return to Aave.

https://intel.arkm.com/explorer/address/0xa03400E098F4421b34a3a44A1B4e571419517687

When WETH borrow rates are high, users leveraging LSTs and LRTs with WETH are pushed into unprofitability. This may lead these users to unwind their positions, generally necessitating swapping the derivative for WETH on the open market. This can cause deviations form the peg, as has been observed in the (w)stETH market, for example, though the deviation is relatively minor and does not pose a threat to the protocol because of its use of fundamental pricing.

This has also been observed in the (w)eETH market, though again the deviation is relatively minor and does not pose a risk to the protocol.

However, while these depegs do not pose a risk to the protocol, it is in the interest of general market stability and a positive user experience on Aave to mitigate borrow rate spikes, especially on a highly leveraged asset. 

## Ethereum Core

ETH’s recent strong price performance has led to an increase in the USD value on both sides of the market, with suppliers increasingly borrowing stablecoins alongside growth in WETH borrowed against wstETH and weETH. 

Thus, unlike other periods of high utilization which may be caused by price declines, the market is not at risk of large-scale liquidations that could further increase utilization, with a relatively gentle liquidation curve. 

To put these values into perspective, at current price and supply levels, the buffer between a 94% UOptimal and full utilization would be just over $500M. This allows us to recommend a temporarily more permissive market, in which the UOptimal can be further increased.

[...]

## Recommendation

To reduce interest rate volatility we propose temporary adjustments to the interest rate curves which aim to further soften the slope beyond UOptimal and reduce stress on borrowers. 

We intend to revert these parameters once utilization levels normalize, whether through HTX redepositing or through normal market operations. A permanent solution to address these periods of rate volatility caused by HTX’s activities is being developed. 

# Specification

These changes currently cannot be implemented because of a Risk Steward timelock triggered by previous changes to this market. However, when the timelock expires tomorrow, we recommend implementing the following changes:

| Asset | Market | Current Slope2 | Recommended Slope2 | Current UOptimal | Recommended UOptimal |
| --- | --- | --- | --- | --- | --- |
| WETH | Ethereum Core | 60% | 40% | 93% | 94% |
| WETH | Ethereum Prime | 65% | 45% | 92% | - |

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

---

## A13 | WETH | kink 94% -> 95% | effective 2025-07-22

Source: https://governance.aave.com/t/22279/12 (ChaosLabs, 2025-07-22 19:44:02 UTC) — excerpt

# **Summary**

Chaos Labs recommends rolling back recent changes to USDT’s IR curve on Ethereum Core and increasing WETH’s Slope1 on Core and Prime to begin the process of rolling back recent changes to its IR curve.

[...]

## WETH — Ethereum Core

Similarly, the WETH Core market experienced significant outflows, largely due to the same HTX-related account. These outflows, however, have not returned, and have continued this week. In aggregate, 437K aWETH outflows stemming from two interlinked Huobi accounts have occurred, of which, in aggregate, only 27K aWETH remains.

This has caused significant rate volatility as utilization has consistently risen, the result of less elastic demand relative to USDT because of the high proportion of leveraged yield farming in this market. The associated demand response stemming from leveraged LST/LRT collateralized debt positions with such thin margins makes it such that the primary mechanism of action to neutralize interest rate spikes stems from deleveraging with significant notional size, leading to adverse second order affects such as market price deviations and liquidity contractions, and thus an uptick in protocol duration risk via exit-queue deposits.

To reduce volatility in the market and prepare to return the market to its original UOptimal, we recommend “flattening” the IR curve by increasing Slope1 slightly, to 3%, and reducing Slope2. Additionally, we recommend increasing UOptimal by 1pp to mitigate current rate fluctuations.

---

## A14 | WETH | kink 95% -> 94% | effective 2025-07-30

Source: https://governance.aave.com/t/22279/13 (ChaosLabs, 2025-07-30 11:12:09 UTC)

## **Summary**

Following our previous update to the WETH Core market IR curve, we are now proposing an adjustment to align more closely with current market conditions. As detailed in our [previous update](https://governance.aave.com/t/chaos-labs-risk-stewards-adjust-usdt-interest-rate-curve-on-aave-v3-06-05-25/22279/12), these parameters were introduced to address sustained high utilization and rate volatility stemming from HTX-linked outflows that reduced supply.

### WETH — Ethereum Core

Our prior adjustment increased Slope 1 from 2.7% to 3.0% and raised UOptimal to 95%. This change was intended to flatten the interest rate curve and reduce volatility above optimal utilization during a period of elevated outflows and market instability. The steeper slope 1 helped temper the borrow demand until additional supply was deposited by introducing stronger rate pressure on borrowers.

With market conditions now more stable, and the WETH utilization on Ethereum Core dropped below 92% we recommend gradually rolling back the previous changes to reintroduce a sufficient liquidity buffer between UOptimal and full utilization. We therefore propose adjusting our utilization target to a UOptimal value of 94%.

Simultaneously, we are also proposing a slight reduction in Slope1 to 2.90%. To target a profitable WETH borrow rate at the target utilization, while still discouraging excessive usage above target UOptimal without introducing unnecessary cost pressure below it.

## **Specification**

| **Asset** | **Market** | **Current Slope 1** | **Recommended Slope 1** | **Current UOptimal** | **Recommended UOptimal** |
|----|----|----|----|----|----|
| WETH | Ethereum Core | 3.00% | 2.90% | 95% | 94% |

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

---

## A15 | WETH | kink 94% -> 93% | effective 2025-08-08

Source: https://governance.aave.com/t/22279/14 (ChaosLabs, 2025-08-06 19:56:57 UTC)

## **Summary**

Following our previous updates to the WETH Core market IR curve, we are now proposing another adjustment to align more closely with current market conditions. As detailed in our previous updates, these parameters were introduced to address sustained high utilization and rate volatility stemming from HTX-linked outflows that reduced supply.

### WETH — Ethereum Core

Our prior adjustments increased Slope 1 from 2.7% to 3.0% and raised UOptimal to 95%. This change was intended to, and was successful at, reducing interest rate volatility during a period of elevated outflows and market instability. However, this was intended to be temporary, and our most recent adjustment — reducing Slope 1 and UOptimal — has not created any additional rate volatility.

With continuing stable market conditions and decreasing WETH utilization, we recommend continuing to gradually roll back the increases, reintroducing a sufficient liquidity buffer between UOptimal and full utilization. We therefore propose adjusting UOptimal to 93%.

Simultaneously, we recommend a slight reduction in Slope1 to 2.80%, which will create a profitable WETH borrow rate at the target utilization, while still discouraging excessive usage above target UOptimal.

## **Specification**

| **Asset** | **Market** | **Current Slope 1** | **Recommended Slope 1** | **Current UOptimal** | **Recommended UOptimal** |
|----|----|----|----|----|----|
| WETH | Ethereum Core | 2.90% | 2.80% | 94% | 93% |

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

---

## A16 | WETH | kink 93% -> 92% | effective 2025-08-11

Source: https://governance.aave.com/t/22279/15 (ChaosLabs, 2025-08-11 16:30:58 UTC)

## Summary

Following our most recent update to the WETH Core market IR curve, we propose a further adjustment to align with the current, improved market conditions. As described in prior proposals, the previous changes were enacted to stabilize rates during a period of elevated utilization driven by HTX-linked outflows and reduced supply.

### WETH — Ethereum Core

Our prior changes have reduced UOptimal from 95% to 93% and lowered Slope1 from 3.00% to 2.80%, reintroducing a healthier liquidity buffer while maintaining attractive yields at the target utilization. This adjustment proved effective, as utilization stabilized and interest rate volatility remained minimal.

Since then, we have seen:

* Further market inflows and net debt repayments, increasing liquidity availability.

* Notable improvement in the peg stability of LSTs and LRTs, reducing liquidity fragmentation and further supporting healthy market functioning.

* Borrow rates converging toward the previous market-priced equilibrium, in line with staking reward dynamics.

  

Given these developments, we recommend continuing the gradual rollback of temporary rate curve increases.

# Specification

| Parameter | Current | Proposed |
|----|----|----|
| UOptimal | 93% | 92% |
| Slope1 | 2.80% | 2.70% |

# **Next Steps**

We will move forward and implement these updates via the Risk Steward process.

