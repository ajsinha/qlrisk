# Credit Valuation Adjustment (CVA) Metric

## Definition

CVA is the market value of counterparty credit risk - the expected loss from counterparty default over the life of a derivatives portfolio.

## Formula

```
CVA = (1 - R) × ∫₀ᵀ EE(t) × dPD(t) × DF(t)

Discrete:
CVA = LGD × Σᵢ EE(tᵢ) × [S(tᵢ₋₁) - S(tᵢ)] × DF(tᵢ)

where:
R = Recovery rate
EE(t) = Expected Exposure at time t
S(t) = Survival probability to time t
DF(t) = Discount factor
```

## Key Drivers

| Driver | Impact on CVA |
|--------|---------------|
| Credit spread ↑ | CVA ↑ |
| Exposure ↑ | CVA ↑ |
| Maturity ↑ | CVA ↑ |
| Recovery ↑ | CVA ↓ |
| Collateral ↑ | CVA ↓ |

## CVA Variants

### Unilateral CVA
- Counterparty default risk only
- Standard accounting treatment

### Bilateral CVA (BCVA)
```
BCVA = CVA - DVA
```
- Includes own default benefit
- Controversial accounting treatment

### Funding CVA (FVA)
- Cost/benefit of funding uncollateralized exposure
- Separate from credit adjustment

## Accounting Treatment

### IFRS 13
- CVA required for fair value
- DVA also recognized
- Mark-to-market through P&L

### ASC 820 (US GAAP)
- Similar to IFRS 13
- CVA/DVA in fair value

## Regulatory Capital

### SA-CVA (Standardized)
```
K = 2.33 × √[Σ(wᵢ × Mᵢ × EADᵢ)²]
```

### BA-CVA (Basic)
- Simpler, more conservative
- Based on supervisory parameters

### Advanced CVA (IMA-CVA)
- Internal model approach
- VaR of CVA P&L

## CVA Hedging

### Instruments
- Single-name CDS
- CDS index
- Contingent CDS

### Greeks for Hedging
- CVA Spread01: ∂CVA/∂credit spread
- CVA Duration: ∂CVA/∂interest rate
- CVA Exposure: ∂CVA/∂market factors

## Wrong-Way Risk

When exposure and credit quality are correlated:
```
CVA_WWR = CVA × (1 + α × ρ_exposure,credit)
```

Types:
- **Specific WWR**: Structural (e.g., put on own stock)
- **General WWR**: Macro correlation

## CVA Desk Operations

### Functions
- CVA calculation and reporting
- CVA hedging
- Pricing adjustments
- XVA management

### KPIs
- CVA P&L volatility
- Hedge effectiveness
- Capital utilization

## Best Practices

1. Use market-implied spreads when available
2. Assess wrong-way risk for all counterparties
3. Implement dynamic hedging program
4. Regular model validation and backtesting
5. Integrate CVA into trade pricing

## References

- Gregory, J. - "The xVA Challenge"
- IFRS 13 Fair Value Measurement
- Basel III CVA Framework

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

