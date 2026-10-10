# Economic Capital (EC) Metric

## Definition

Economic Capital is the capital required to absorb unexpected losses at a target confidence level, typically aligned with desired credit rating (e.g., 99.9% for AA rating).

## Formula

```
EC = VaR(α) - EL = UL

where:
VaR(α) = Value-at-Risk at confidence α
EL = Expected Loss
UL = Unexpected Loss
```

## Key Properties

| Property | Value |
|----------|-------|
| Confidence Level | 99% - 99.97% |
| Time Horizon | 1 year (standard) |
| Purpose | Solvency protection |

## EC vs Regulatory Capital

| Aspect | Economic Capital | Regulatory Capital |
|--------|-----------------|-------------------|
| Calibration | Bank-specific | Regulatory formula |
| Risk Coverage | Comprehensive | Prescribed |
| Confidence | Target rating | 99.9% (IRB) |
| Uses | Internal management | Compliance |

## Capital Allocation

### RAROC Framework
```
RAROC = (Revenue - Costs - EL) / EC

Value creation when RAROC > Hurdle Rate
```

### Business Line Allocation
```
EC_allocated = Marginal Contribution × Total EC
```

## Concentration Adjustments

### Name Concentration
```
EC_adjusted = EC × (1 + Herfindahl × factor)
```

### Sector Concentration
- Industry concentration add-on
- Geographic concentration add-on

## Correlation Impact

Higher correlation → Higher EC:
```
EC ∝ √(Systematic Risk + Idiosyncratic Risk)
```

Basel correlation formula:
```
ρ = 0.12 × exp(-50 × PD) + 0.24 × (1 - exp(-50 × PD))
```

## Use Cases

1. **Capital Planning**: Ensure adequate capitalization
2. **Performance Measurement**: Risk-adjusted returns
3. **Pricing**: Risk-based pricing
4. **Limit Setting**: Risk appetite allocation
5. **M&A Analysis**: Target capital assessment

## Stress Testing

Stressed EC under adverse scenarios:
```
EC_stressed = VaR_stressed - EL_stressed

Consider:
- Elevated PDs
- Higher correlations
- Increased LGDs
```

## Best Practices

1. Align confidence with target rating
2. Include all material risks
3. Validate against actual losses
4. Stress test regularly
5. Integrate into decision-making

## References

- Basel Committee - Capital Requirements
- Gordy, M. - "Risk Factor Model Foundations"
- Moody's Analytics - Portfolio Manager

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

