# Interest Rate Swap (IRS)

## Product Overview

An Interest Rate Swap is a derivative contract where two parties exchange interest rate cash flows on a notional principal. The most common type exchanges fixed-rate for floating-rate payments.

## Product Specifications

| Attribute | Description |
|-----------|-------------|
| Notional | Principal amount (not exchanged) |
| Fixed Rate | Predetermined swap rate |
| Floating Rate | SOFR, EURIBOR, etc. |
| Payment Frequency | Quarterly, Semi-annual, Annual |
| Day Count | 30/360, ACT/360, ACT/365 |
| Maturity | 1 year to 30+ years |

## Cash Flow Structure

### Fixed Leg
```
Fixed Payment = Notional × Fixed Rate × Day Count Fraction
```

### Floating Leg
```
Floating Payment = Notional × Floating Rate × Day Count Fraction
```

## Valuation

### Mark-to-Market
```
MTM = PV(Fixed Leg) - PV(Floating Leg)  [for fixed payer]

PV(Leg) = Σᵢ CFᵢ × DF(tᵢ)
```

### Par Rate (Swap Rate)
```
Swap Rate = [1 - DF(T)] / Σᵢ DF(tᵢ) × τᵢ
```

## CCR Characteristics

### Exposure Profile
```
     ^
     |     ***
     |   **   **
     |  *       **
     | *          ***
     +-------------------> Time
        Hump shape, peak at ~40% maturity
```

### Key Risk Factors
- Interest rate level changes
- Yield curve shape (steepening/flattening)
- Basis risk (SOFR vs EURIBOR)

## Risk Measures

### Duration
```
Modified Duration = -(1/P) × ∂P/∂y
```

### DV01
```
DV01 = Change in value for 1bp rate move
     ≈ Notional × Duration × 0.0001
```

### Convexity
```
Convexity = (1/P) × ∂²P/∂y²
```

## CCR Calculator Inputs

```python
# IRS CCR calculation
trade_data = {
    "product_type": "irs",
    "notional": 100_000_000,
    "current_mtm": 2_500_000,
    "remaining_maturity": 7.0,
    "volatility": 0.15,  # IR volatility
    "fixed_rate": 0.025,
    "floating_index": "SOFR"
}
```

## Add-On Factors (SA-CCR)

| Maturity | Add-On Factor |
|----------|---------------|
| ≤ 1 year | 0.50% |
| 1-5 years | 1.00% |
| > 5 years | 1.50% |

## Netting Considerations

- IRS typically under ISDA Master Agreement
- Close-out netting reduces exposure significantly
- Payment netting reduces settlement risk

## Collateral Treatment

### Standard CSA Terms
- Daily margin calls
- Zero threshold common
- Cash collateral preferred

### Impact on Exposure
```
Margined EPE ≈ 10-20% of unmargined EPE
```

## Use Cases

1. **Hedging**: Convert floating debt to fixed
2. **Speculation**: View on interest rates
3. **Asset-Liability Management**: Match durations
4. **Relative Value**: Curve trades

## References

- Hull, J. - "Options, Futures, and Other Derivatives"
- ISDA Interest Rate Definitions
- Basel SA-CCR Framework

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

