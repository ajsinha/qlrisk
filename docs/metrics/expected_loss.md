# Expected Loss (EL) Metric

## Definition

Expected Loss (EL) is the average credit loss anticipated over a specified time horizon. It represents the "cost of doing business" in lending and derivatives trading.

## Formula

```
EL = PD × LGD × EAD

where:
PD  = Probability of Default
LGD = Loss Given Default
EAD = Exposure at Default
```

## Components

| Component | Range | Description |
|-----------|-------|-------------|
| PD | 0% - 100% | Likelihood of counterparty default |
| LGD | 0% - 100% | Loss severity given default (1 - Recovery) |
| EAD | Currency | Exposure amount at default |

## Interpretation

| EL Rate | Risk Level | Typical Action |
|---------|------------|----------------|
| < 0.1% | Very Low | Standard pricing |
| 0.1% - 0.5% | Low | Normal monitoring |
| 0.5% - 2% | Medium | Enhanced monitoring |
| 2% - 5% | High | Increased provisions |
| > 5% | Very High | Remediation required |

## Use Cases

### 1. Loan Loss Provisioning
- IFRS 9 Expected Credit Loss (ECL)
- US GAAP CECL
- General and specific provisions

### 2. Pricing
- Risk-adjusted pricing = Funding cost + EL + Capital cost
- Ensures adequate compensation for credit risk

### 3. Performance Measurement
- Risk-adjusted returns
- Business line comparison
- Portfolio optimization

### 4. Regulatory Capital
- Basel III: EL compared to provisions
- Shortfall deducted from capital

## IFRS 9 ECL Stages

| Stage | Condition | ECL Measurement |
|-------|-----------|-----------------|
| 1 | Performing | 12-month EL |
| 2 | Significant increase in credit risk | Lifetime EL |
| 3 | Credit-impaired | Lifetime EL |

## Aggregation

Portfolio EL is additive:
```
Portfolio EL = Σᵢ ELᵢ = Σᵢ (PDᵢ × LGDᵢ × EADᵢ)
```

Unlike Unexpected Loss, no correlation adjustment needed.

## Relationship to Other Metrics

- **Provisions**: Should cover EL
- **Economic Capital**: Covers Unexpected Loss beyond EL
- **CVA**: Risk-neutral EL discounted over exposure profile
- **Regulatory Capital**: Includes EL shortfall charge

## Best Practices

1. Use point-in-time (PIT) estimates for accounting
2. Use through-the-cycle (TTC) for regulatory capital
3. Apply forward-looking economic adjustments
4. Review and update parameters regularly
5. Stress test EL under adverse scenarios

## References

- Basel II/III IRB Approach
- IFRS 9 Financial Instruments
- FASB ASC 326 (CECL)

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

