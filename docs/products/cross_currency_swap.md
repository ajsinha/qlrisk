# Cross-Currency Swap (XCCY)

## Product Overview

A Cross-Currency Swap is a derivative where two parties exchange principal and interest payments in different currencies. Unlike IRS, XCCY involves actual exchange of notional amounts at inception and maturity.

## Product Specifications

| Attribute | Description |
|-----------|-------------|
| Notional | Principal in each currency |
| Currencies | Two different currencies |
| Interest Rates | Fixed-fixed, fixed-float, or float-float |
| Payment Frequency | Typically quarterly |
| Principal Exchange | At inception, maturity, or both |

## Cash Flow Structure

### At Inception
```
Party A pays: Notional_A (currency A)
Party B pays: Notional_B (currency B)
```

### During Life (Interest)
```
Party A pays: Notional_A × Rate_A × τ
Party B pays: Notional_B × Rate_B × τ
```

### At Maturity
```
Reverse of inception exchange
(Original notionals returned)
```

## Valuation

### Mark-to-Market
```
MTM = PV(Receive Leg) - PV(Pay Leg)

where each leg includes:
- Interest payment PVs
- Final principal exchange PV
```

### Key Difference from IRS
```
FX risk on principal exchange creates large 
exposure spike at maturity
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
        Large increase at maturity (notional exchange)
```

### Key Risk Factors
- Interest rates in both currencies
- FX rate between currencies
- Cross-currency basis spread

## Risk Measures

### FX Delta
```
FX Delta ≈ Notional_foreign × DF(T)
```

### IR DV01 (each currency)
```
DV01_A = Sensitivity to currency A rates
DV01_B = Sensitivity to currency B rates
```

### Cross-Currency Basis
```
Basis DV01 = Sensitivity to XCCY basis spread
```

## CCR Calculator Inputs

```python
# Cross-Currency Swap CCR calculation
trade_data = {
    "product_type": "xccy_swap",
    "notional_domestic": 100_000_000,  # USD
    "notional_foreign": 90_000_000,    # EUR
    "current_mtm": 5_000_000,
    "remaining_maturity": 10.0,
    "volatility": 0.12,  # FX + IR combined
    "domestic_rate": 0.03,
    "foreign_rate": 0.02,
    "fx_rate": 1.10
}
```

## Add-On Factors

Combines IR and FX add-ons:
```
Total Add-On = IR Add-On + FX Add-On

where:
IR Add-On based on rate sensitivity
FX Add-On based on notional exchange exposure
```

## Settlement Risk

### Large Settlement Exposure
```
At maturity:
Settlement Risk = Full notional in each currency
```

### Mitigation
- CLS for FX component
- Staggered settlement
- Collateral arrangements

## Netting Considerations

- Effective against same counterparty XCCY
- Limited offset with plain IRS
- FX component may net with FX forwards

## Collateral Treatment

### Key Considerations
- Currency of collateral matters
- Wrong-way risk if collateral currency = exposure currency
- Haircuts for currency mismatch

## Use Cases

1. **Funding**: Access foreign currency funding
2. **Hedging**: Hedge foreign currency assets/liabilities
3. **Basis Trading**: Cross-currency basis views
4. **Regulatory Arbitrage**: Capital optimization

## Cross-Currency Basis

### Definition
```
Basis = (XCCY Swap Rate) - (IRS Rate Differential)
```

### Drivers
- Funding demand imbalances
- Counterparty credit concerns
- Regulatory constraints

## References

- Hull, J. - "Options, Futures, and Other Derivatives"
- ISDA Cross-Currency Definitions
- Basel SA-CCR Framework

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

