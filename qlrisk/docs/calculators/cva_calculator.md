# Credit Valuation Adjustment (CVA) Calculator

## Overview

The Credit Valuation Adjustment (CVA) Calculator computes the market value of counterparty credit risk. CVA represents the expected loss due to counterparty default and is both an accounting adjustment (fair value) and a regulatory capital requirement.

## Core Formula

**Unilateral CVA:**
```
CVA = LGD × ∫₀ᵀ EE(t) × dPD(t) × DF(t)

Discrete approximation:
CVA = LGD × Σᵢ EE(tᵢ) × [PD(tᵢ₋₁) - PD(tᵢ)] × DF(tᵢ)

where:
LGD = Loss Given Default (1 - Recovery)
EE(t) = Expected Exposure at time t
PD(t) = Cumulative default probability to time t
DF(t) = Discount factor to time t
```

## CVA Variants

### 1. Unilateral CVA (Standard)
Accounts only for counterparty default risk:
```
CVA = E[LGD × max(V(τ), 0) × 1{τ<T}]
```

### 2. Bilateral CVA (BCVA)
Accounts for both counterparty and own default:
```
BCVA = CVA - DVA

DVA = Own LGD × ∫₀ᵀ NEE(t) × dPD_own(t) × DF(t)

where NEE(t) = Negative Expected Exposure
```

### 3. Funding Valuation Adjustment (FVA)
Funding cost of uncollateralized exposure:
```
FVA = ∫₀ᵀ (EE(t) - ENE(t)) × spread(t) × DF(t) dt
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ee_profile` | List[float] | Yes | Expected Exposure profile |
| `time_grid` | List[float] | Yes | Time points in years |
| `credit_spread` | float | Yes | Credit spread (bps or decimal) |
| `recovery_rate` | float | No | Recovery rate (default 0.4) |
| `discount_rates` | List[float] | No | Discount curve |
| `risk_free_rate` | float | No | Flat risk-free rate |
| `spread_term_structure` | List[float] | No | Term structure of spreads |
| `own_credit_spread` | float | No | For DVA calculation |
| `bilateral` | bool | No | Calculate BCVA if True |

## Usage Examples

### Basic CVA Calculation

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
cva_calc = factory.get_cva_calculator()

# EE profile from EE calculator or simulation
time_grid = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0]
ee_profile = [100_000, 150_000, 200_000, 180_000, 150_000, 100_000]

result = cva_calc.calculate({
    "ee_profile": ee_profile,
    "time_grid": time_grid,
    "credit_spread": 0.01,      # 100 bps
    "recovery_rate": 0.40,
    "risk_free_rate": 0.05
})

print(f"CVA: ${result.value.cva:,.2f}")
print(f"CVA as % of exposure: {result.value.cva_pct:.4%}")
```

### Bilateral CVA

```python
result = cva_calc.calculate({
    "ee_profile": ee_profile,
    "time_grid": time_grid,
    "credit_spread": 0.01,
    "own_credit_spread": 0.005,  # 50 bps
    "recovery_rate": 0.40,
    "bilateral": True
})

print(f"CVA: ${result.value.cva:,.2f}")
print(f"DVA: ${result.value.dva:,.2f}")
print(f"BCVA (Net): ${result.value.bcva:,.2f}")
```

### With Term Structure of Spreads

```python
# Credit spread term structure
spread_term = [0.008, 0.009, 0.010, 0.012, 0.014, 0.015]

result = cva_calc.calculate({
    "ee_profile": ee_profile,
    "time_grid": time_grid,
    "spread_term_structure": spread_term,
    "recovery_rate": 0.40
})

print(f"CVA (term structure): ${result.value.cva:,.2f}")
```

## Output Structure

```python
@dataclass
class CVAResult:
    cva: float                    # Unilateral CVA amount
    cva_pct: float                # CVA as % of notional
    dva: Optional[float]          # Debit Valuation Adjustment
    bcva: Optional[float]         # Bilateral CVA
    marginal_cva: List[float]     # CVA by time bucket
    components: Dict[str, Any]    # Survival probs, discounts
```

## CVA Decomposition

### By Time Period
```
CVA(t₁, t₂) = LGD × EE(avg) × [SP(t₁) - SP(t₂)] × DF(avg)

where SP(t) = Survival probability to time t
```

### Marginal CVA
Contribution of each time bucket to total CVA:
```
Marginal CVA(tᵢ) = LGD × EE(tᵢ) × ΔPD(tᵢ) × DF(tᵢ)
```

## Credit Spread to Default Probability

Convert market spreads to default probabilities:

```
Hazard Rate λ = spread / LGD

Survival Probability SP(t) = exp(-λt)

Default Probability PD(t) = 1 - SP(t)
```

## Regulatory CVA Capital

### Basel III Standardized CVA (SA-CVA)
```
K_CVA = 2.33 × √[Σᵢ(wᵢ × Mᵢ × EADᵢ)²]

where:
wᵢ = Risk weight based on rating
Mᵢ = Effective maturity
EADᵢ = Exposure at Default
```

### Basel III Basic CVA (BA-CVA)
```
K_CVA = Σᶜ[SCVAᶜ × Σᵢ(wᵢ × Mᵢ × EADᵢᶜ × DFᵢᶜ)]

where:
SCVAᶜ = Supervisory CVA risk weight
DFᵢᶜ = Supervisory discount factor
```

## CVA Sensitivities (Greeks)

### CVA Spread Sensitivity
```
∂CVA/∂spread ≈ LGD × Σᵢ EE(tᵢ) × tᵢ × SP(tᵢ) × DF(tᵢ)
```

### CVA Interest Rate Sensitivity
```
∂CVA/∂r ≈ CVA × Average Duration
```

## Wrong-Way Risk (WWR)

When exposure increases as counterparty credit deteriorates:

```
CVA_WWR = CVA × (1 + α × ρ)

where:
α = WWR multiplier (typically 1.1-1.4)
ρ = Correlation between exposure and credit
```

Types of WWR:
1. **Specific WWR**: Structural relationship (e.g., put on own stock)
2. **General WWR**: Macro correlation (e.g., EM sovereign + EM corporate)

## Accounting vs Regulatory CVA

| Aspect | Accounting (IFRS 13) | Regulatory (Basel III) |
|--------|---------------------|------------------------|
| Objective | Fair value | Capital requirement |
| Bilateral | Yes (BCVA) | No (CVA only) |
| Hedging | Recognized | Limited recognition |
| Methodology | Market-implied | Often historical |

## Best Practices

1. **EE Profile**: Use Monte Carlo simulation for complex portfolios
2. **Spreads**: Use CDS spreads when available, bond spreads otherwise
3. **WWR**: Assess wrong-way risk for all counterparties
4. **Hedging**: Implement CVA hedge program with CDS
5. **XVA Desk**: Centralize CVA management

## CVA Hedging

### Instruments
- Single-name CDS on counterparty
- CDS index hedges for systematic risk
- Contingent CDS (bespoke)

### Hedge Effectiveness
```
Hedge Ratio = ∂CVA/∂spread / ∂CDS/∂spread

Consider:
- Basis risk (bond-CDS)
- Maturity mismatch
- Recovery rate assumptions
```

## References

1. Gregory, J. - "The xVA Challenge"
2. Brigo, D. et al. - "Counterparty Credit Risk, Collateral and Funding"
3. Basel Committee - CVA Risk Framework
4. IFRS 13 - Fair Value Measurement

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

