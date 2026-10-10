# Credit Default Swap (CDS)

## Product Overview

A Credit Default Swap is a derivative contract providing protection against credit events (default, restructuring) of a reference entity. The protection buyer pays periodic premiums; the protection seller compensates for losses upon credit event.

## Product Specifications

| Attribute | Description |
|-----------|-------------|
| Reference Entity | Company, sovereign, or index |
| Notional | Protection amount |
| Premium (Spread) | Annualized payment (bps) |
| Maturity | Typically 1, 3, 5, 7, 10 years |
| Credit Events | Bankruptcy, failure to pay, restructuring |
| Settlement | Physical or cash (auction) |

## Cash Flow Structure

### Premium Leg (Protection Buyer Pays)
```
Premium Payment = Notional × Spread × Day Count Fraction
```

### Protection Leg (Seller Pays on Default)
```
Protection Payment = Notional × (1 - Recovery Rate)
```

## Valuation

### CDS Spread (Par Spread)
```
Premium PV = Protection PV

Σ(Spread × Notional × τᵢ × S(tᵢ) × DF(tᵢ)) = 
  LGD × Σ([S(tᵢ₋₁) - S(tᵢ)] × DF(tᵢ))

where:
S(t) = Survival probability to time t
DF(t) = Discount factor
LGD = 1 - Recovery Rate
```

### Mark-to-Market
```
MTM = (Spread_current - Spread_contract) × Risky DV01 × Notional
```

### Risky DV01
```
Risky DV01 = Σᵢ τᵢ × S(tᵢ) × DF(tᵢ)
```

## CCR Characteristics

### Exposure Profile

**Protection Buyer (Pay Premium):**
```
     ^
     |  ****
     | *    **
     |*       **
     |          ***
     +-------------------> Time
        Declining exposure (asset amortization)
```

**Protection Seller (Receive Premium):**
```
     ^
     |          ***
     |       ***
     |    ***
     | ***
     +-------------------> Time
        Increasing exposure (liability growth)
```

### Key Risk Factors
- Reference entity credit spread
- Recovery rate assumptions
- Interest rates (discounting)
- Default correlation (for indices)

## Risk Measures

### CS01 (Credit Spread Sensitivity)
```
CS01 = ∂MTM / ∂Spread (1bp)
     ≈ Risky DV01 × Notional / 10000
```

### Jump-to-Default
```
JTD = Notional × LGD × [1 or -1]

+1 for protection buyer
-1 for protection seller
```

## CCR Calculator Inputs

```python
# CDS CCR calculation
trade_data = {
    "product_type": "cds",
    "notional": 10_000_000,
    "current_mtm": 150_000,
    "remaining_maturity": 5.0,
    "volatility": 0.40,  # Credit spread vol
    "credit_spread": 0.0150,  # 150 bps
    "recovery_rate": 0.40,
    "reference_entity": "XYZ Corp"
}
```

## Add-On Factors (SA-CCR)

| Category | Add-On Factor |
|----------|---------------|
| Investment Grade | 0.38% |
| Speculative Grade | 1.06% |
| Sub-speculative | 1.06% |
| Index (IG) | 0.38% |
| Index (HY) | 1.06% |

## Wrong-Way Risk

CDS creates structural wrong-way risk:
```
If reference entity = counterparty:
   Specific WWR - protection worthless when needed
   
If reference entity correlated with counterparty:
   General WWR - exposure increases with credit deterioration
```

## Clearing

### Cleared CDS
- Major indices cleared (CDX, iTraxx)
- Single-name clearing growing
- Reduces bilateral CVA

### Uncleared CDS
- Bespoke/illiquid reference entities
- Subject to bilateral margin requirements

## Netting Considerations

- Protection bought/sold on same reference entity nets
- Index vs single-name basis exposure remains
- ISDA Credit Derivatives Definitions govern

## Use Cases

1. **Hedging**: Credit risk mitigation
2. **Trading**: Credit spread views
3. **Arbitrage**: Basis trading (bond vs CDS)
4. **Funding**: Synthetic funding trades
5. **CVA Hedging**: Hedge counterparty credit risk

## Credit Events

### Standard Credit Events (Corporate)
1. Bankruptcy
2. Failure to Pay
3. Restructuring (varies by documentation)

### Determination Process
- ISDA Determinations Committee
- Credit event auction for settlement

## References

- Hull, J. & White, A. - "Valuing Credit Default Swaps"
- ISDA Credit Derivatives Definitions
- Basel SA-CCR Framework
- Markit CDS Pricing

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

