# FX Forward

## Product Overview

An FX Forward is a contract to exchange a specified amount of one currency for another at a predetermined exchange rate on a future date.

## Product Specifications

| Attribute | Description |
|-----------|-------------|
| Notional | Amount in base currency |
| Currency Pair | e.g., EUR/USD, USD/JPY |
| Forward Rate | Agreed exchange rate |
| Settlement Date | Delivery date |
| Delivery | Physical or cash settled |

## Forward Rate Calculation

```
Forward Rate = Spot × (1 + r_d × T) / (1 + r_f × T)

or with continuous compounding:
F = S × exp[(r_d - r_f) × T]

where:
S = Spot rate
r_d = Domestic interest rate
r_f = Foreign interest rate
T = Time to maturity
```

## Forward Points

```
Forward Points = Forward Rate - Spot Rate

= Spot × [(r_d - r_f) × T] / (1 + r_f × T)
```

## Valuation

### Mark-to-Market
```
MTM = Notional_f × DF_f × (F_current - F_contract) × Spot

or equivalently:
MTM = Notional_f × [DF_f × F_current - DF_d × F_contract]
```

## CCR Characteristics

### Exposure Profile
```
     ^
     |              ****
     |          ****
     |      ****
     |  ****
     |**
     +-------------------> Time
        Generally increasing to maturity
```

### Key Risk Factors
- Spot FX rate movements
- Interest rate differentials
- Cross-currency basis

## Risk Measures

### Delta
```
FX Delta = Notional in foreign currency
```

### FX Sensitivity
```
∂MTM/∂Spot ≈ Notional_f × DF_f
```

## CCR Calculator Inputs

```python
# FX Forward CCR calculation
trade_data = {
    "product_type": "fx_forward",
    "notional": 50_000_000,  # USD notional
    "current_mtm": 1_250_000,
    "remaining_maturity": 1.0,
    "volatility": 0.10,  # FX volatility
    "currency_pair": "EURUSD",
    "forward_rate": 1.1250
}
```

## Add-On Factors (SA-CCR)

| Maturity | Add-On Factor |
|----------|---------------|
| ≤ 1 year | 4.00% |
| 1-5 years | 6.00% |
| > 5 years | 8.00% |

## Settlement Risk

### Herstatt Risk
- Risk of paying one leg before receiving the other
- Mitigated by:
  - CLS (Continuous Linked Settlement)
  - Payment-versus-Payment (PvP)

### CLS Settlement
```
Reduces settlement exposure to:
Residual Risk = Net position after CLS netting
```

## Netting Considerations

- CSA netting reduces exposure
- Same-currency-pair netting most effective
- Cross-currency netting limited

## Collateral Treatment

### Standard Practices
- Daily margin for longer-dated forwards
- Weekly for shorter-dated
- Threshold often applies

## Use Cases

1. **Hedging**: Corporate FX exposure
2. **Carry Trade**: Interest rate differential
3. **Speculation**: FX views
4. **Arbitrage**: Covered interest parity

## Regulatory Classification

- **Basel**: Subject to SA-CCR
- **Clearing**: Not typically cleared (< 3 days often exempt)
- **Margin**: UMR applies for longer-dated

## References

- Hull, J. - "Options, Futures, and Other Derivatives"
- Basel SA-CCR Framework
- CLS Settlement Process

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

