# Potential Future Exposure (PFE) Metric

## Definition

PFE is the maximum expected credit exposure at a specified confidence level over a time horizon. It captures tail risk of exposure increases due to adverse market movements.

## Formula

```
PFE(t, α) = Quantileα[max(0, V(t))]

where:
V(t) = Portfolio value at time t
α = Confidence level (typically 95% or 99%)
```

## Key Properties

| Property | Description |
|----------|-------------|
| Point-in-time | Calculated at each future date |
| Percentile-based | Captures tail of distribution |
| Additive at percentile | PFE profile, not single number |
| Peak PFE | Maximum of PFE profile |

## Confidence Levels

| Purpose | Confidence Level |
|---------|------------------|
| Credit limits | 95% - 97.5% |
| Regulatory capital | 97.5% - 99% |
| Stress testing | 99% - 99.9% |

## PFE Profile Shapes

### Interest Rate Swap
```
     ^
     |     ***
     |   **   **
     |  *       **
     | *          ***
     +-------------------> Time
        Hump shape, peak ~40% of maturity
```

### FX Forward
```
     ^
     |              ***
     |          ****
     |      ****
     |  ****
     +-------------------> Time
        Increasing to maturity
```

## Use Cases

### Credit Limits
- Set counterparty credit limits
- Monitor limit utilization
- Approve new trades

### Capital
- Input to regulatory EAD
- Economic capital calculations

### Pricing
- Risk-based pricing adjustments
- Collateral requirements

## Peak vs Average PFE

| Metric | Use Case |
|--------|----------|
| Peak PFE | Credit limit management |
| Average PFE | Capital calculation |
| PFE at maturity | Settlement risk |

## Factors Affecting PFE

| Factor | Impact |
|--------|--------|
| Volatility ↑ | PFE ↑ |
| Maturity ↑ | PFE ↑ (initially) |
| Current MTM ↑ | PFE ↑ |
| Collateral ↑ | PFE ↓ |
| Netting | PFE ↓ |

## Netting Impact

Without netting:
```
Gross PFE = Σᵢ PFEᵢ
```

With netting:
```
Net PFE < Gross PFE

Netting benefit typically 40-70%
```

## Best Practices

1. Calculate at netting set level
2. Use appropriate confidence level for purpose
3. Account for collateral properly
4. Update volatility estimates regularly
5. Include wrong-way risk adjustments

## References

- Basel Committee SA-CCR
- Gregory, J. - "Counterparty Credit Risk"
- Pykhtin, M. - "Modeling Credit Exposure"

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

