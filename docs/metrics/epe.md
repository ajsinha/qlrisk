# Expected Positive Exposure (EPE) Metric

## Definition

EPE (Expected Positive Exposure) is the weighted average of Expected Exposures over time, representing the average credit exposure over the life of a derivatives portfolio.

## Formulas

### Expected Exposure (EE)
```
EE(t) = E[max(0, V(t))]
```

### EPE (Time-Weighted Average)
```
EPE = (1/T) × ∫₀ᵀ EE(t) dt

Discrete:
EPE = (1/n) × Σᵢ EE(tᵢ)
```

### Effective EPE
```
Effective EPE = (1/T) × ∫₀ᵀ EEE(t) dt

where EEE(t) = max(EE(t), EEE(t-Δt))  [non-decreasing]
```

## Regulatory Usage

### Basel III IMM
```
EAD = α × Effective EPE

α = 1.4 (supervisory multiplier)
```

### Maturity Factor
```
Effective Maturity = max(1, Σ(t × ΔEE(t)) / EPE)
```

## Key Properties

| Property | Description |
|----------|-------------|
| Time horizon | Min(1 year, longest maturity) |
| Non-negativity | Always ≥ 0 |
| Averaging | Smooths exposure volatility |
| EEE | Captures rollover risk |

## EPE vs EE vs PFE

| Metric | Definition | Use |
|--------|------------|-----|
| EE(t) | Expected exposure at t | CVA calculation |
| EPE | Average EE over time | Regulatory capital |
| PFE | Percentile of exposure | Credit limits |
| Effective EPE | Non-decreasing average | Conservative capital |

## Calculation Methods

### Monte Carlo
```text
for each simulation:
    for each time t:
        Exposure[t] = max(0, Value[t])
    
EE[t] = mean(Exposure[t] across simulations)
EPE = mean(EE[t] across time)
```

### Analytical (Simple Cases)
For positive drift process:
```
EPE ≈ MTM₀ × exp(μT/2) × N(d₁)
```

## Impact of Collateral

Margined EPE significantly lower:
```
EPE_margined << EPE_unmargined

due to exposure capped at MPOR horizon
```

## Best Practices

1. Use Effective EPE for conservative capital
2. Calculate at netting set level
3. Model MPOR properly for margined trades
4. Validate against historical exposures
5. Stress test EPE under adverse scenarios

## References

- Basel Committee - IMM Framework
- Pykhtin & Zhu - "Exposure Modeling and Credit Risk"
- Gregory, J. - "Counterparty Credit Risk"

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

