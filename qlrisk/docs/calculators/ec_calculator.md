# Economic Capital (EC) Calculator

## Overview

The Economic Capital (EC) Calculator estimates the capital required to absorb unexpected losses from credit risk at a specified confidence level. EC is the difference between Value-at-Risk (VaR) and Expected Loss, representing the capital buffer needed beyond provisions.

## Core Formula

```
Economic Capital = UL = VaR(α) - EL

where:
VaR(α) = Value-at-Risk at confidence level α
EL = Expected Loss = Σ(PD × LGD × EAD)
α = Confidence level (typically 99% or 99.9%)
```

## Calculation Methods

### 1. Vasicek Single-Factor Model (Default)

Based on the asymptotic single risk factor (ASRF) model:

```
EC = EAD × LGD × [N((N⁻¹(PD) + √ρ × N⁻¹(α)) / √(1-ρ)) - PD]

where:
N(·) = Standard normal CDF
N⁻¹(·) = Inverse standard normal
ρ = Asset correlation
α = Confidence level (e.g., 0.999)
```

### 2. Monte Carlo Simulation

For complex portfolios with multiple risk factors:

```python
for each simulation:
    Generate systematic risk factor Z ~ N(0,1)
    For each obligor i:
        Generate idiosyncratic factor εᵢ ~ N(0,1)
        Asset return: Rᵢ = √ρᵢ × Z + √(1-ρᵢ) × εᵢ
        Default if: Rᵢ < N⁻¹(PDᵢ)
        Loss = LGDᵢ × EADᵢ if default
    
    Portfolio Loss = Σ Individual Losses

VaR(α) = Percentile(Portfolio Losses, α)
EC = VaR(α) - E[Portfolio Loss]
```

### 3. CreditMetrics Approach

Full portfolio simulation with rating migrations:

```python
for each simulation:
    for each obligor:
        Simulate rating migration
        Revalue position at new rating
    
    Portfolio Value Change = Σ Position Changes
    
EC = VaR of value changes
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `exposures` | List[float] | Yes | EAD for each obligor |
| `pds` | List[float] | Yes | PD for each obligor |
| `lgds` | List[float] | Yes | LGD for each obligor |
| `asset_correlation` | float | No | Average correlation (default 0.20) |
| `correlation_matrix` | List[List[float]] | No | Full correlation matrix |
| `confidence_level` | float | No | VaR confidence (default 0.999) |
| `ead` | float | No | For single obligor |
| `pd` | float | No | For single obligor |
| `lgd` | float | No | For single obligor |

## Usage Examples

### Portfolio Economic Capital

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
ec_calc = factory.get_ec_calculator()

result = ec_calc.calculate({
    "exposures": [10_000_000, 5_000_000, 8_000_000, 12_000_000],
    "pds": [0.02, 0.01, 0.03, 0.015],
    "lgds": [0.45, 0.40, 0.50, 0.45],
    "asset_correlation": 0.20,
    "confidence_level": 0.999
})

print(f"Expected Loss: ${result.value.expected_loss:,.2f}")
print(f"Unexpected Loss (EC): ${result.value.unexpected_loss:,.2f}")
print(f"VaR (99.9%): ${result.value.var:,.2f}")
print(f"Expected Shortfall: ${result.value.es:,.2f}")
print(f"Capital Ratio: {result.value.capital_ratio:.2%}")
```

### Single Obligor EC

```python
result = ec_calc.calculate({
    "ead": 10_000_000,
    "pd": 0.02,
    "lgd": 0.45,
    "asset_correlation": 0.15,
    "confidence_level": 0.999
})

print(f"Single Obligor EC: ${result.value.economic_capital:,.2f}")
```

### With Custom Correlation Matrix

```python
# 4x4 correlation matrix
correlation = [
    [1.0, 0.3, 0.2, 0.25],
    [0.3, 1.0, 0.15, 0.2],
    [0.2, 0.15, 1.0, 0.3],
    [0.25, 0.2, 0.3, 1.0]
]

result = ec_calc.calculate({
    "exposures": [10_000_000, 5_000_000, 8_000_000, 12_000_000],
    "pds": [0.02, 0.01, 0.03, 0.015],
    "lgds": [0.45, 0.40, 0.50, 0.45],
    "correlation_matrix": correlation
})
```

## Output Structure

```python
@dataclass
class ECResult:
    economic_capital: float       # Unexpected Loss (UL)
    expected_loss: float          # Portfolio EL
    unexpected_loss: float        # Same as EC
    var: float                    # VaR at confidence level
    es: float                     # Expected Shortfall / CVaR
    capital_ratio: float          # EC / Total EAD
    components: Dict[str, Any]    # Method details
```

## Asset Correlation

### Basel II/III Correlation Functions

**Corporate, Bank, Sovereign:**
```
ρ = 0.12 × (1 - exp(-50 × PD)) / (1 - exp(-50))
  + 0.24 × [1 - (1 - exp(-50 × PD)) / (1 - exp(-50))]

Range: 0.12 (high PD) to 0.24 (low PD)
```

**Retail (Residential Mortgage):**
```
ρ = 0.15
```

**Retail (Revolving):**
```
ρ = 0.04
```

**SME:**
```
ρ = 0.12 × (1 - exp(-50 × PD)) / (1 - exp(-50))
  + 0.24 × [1 - (1 - exp(-50 × PD)) / (1 - exp(-50))]
  - 0.04 × (1 - (S - 5) / 45)

where S = annual sales in €M (5 ≤ S ≤ 50)
```

## EC Decomposition

### Contribution to Portfolio EC

```
Marginal EC(i) = ∂EC / ∂EAD(i)

Contribution(i) = EAD(i) × Marginal EC(i) × (PD(i) × LGD(i))
```

### Stand-alone vs Diversified

```
Stand-alone EC(i) = EC calculated for obligor i alone

Diversification Benefit = Σ Stand-alone EC(i) - Portfolio EC
```

## Regulatory Capital Comparison

| Framework | Confidence | Time Horizon |
|-----------|------------|--------------|
| Basel III IRB | 99.9% | 1 year |
| Basel III CVA | 99% | 1 year |
| Economic Capital (typical) | 99.9% - 99.97% | 1 year |
| Solvency II | 99.5% | 1 year |

## RAROC and Performance

Economic Capital enables risk-adjusted performance measurement:

```
RAROC = (Revenue - Costs - EL) / EC

Hurdle Rate: Cost of equity (typically 10-15%)
```

Value creation when RAROC > Hurdle Rate.

## Stress Testing EC

Stressed Economic Capital under adverse scenarios:

```
EC_stressed = VaR_stressed - EL_stressed

Consider:
- Increased PDs (rating migrations)
- Higher correlations
- Elevated LGDs
- Concentration increases
```

## Best Practices

1. **Granularity**: Use obligor-level data, not segment averages
2. **Correlation Estimation**: Historical default correlation + expert judgment
3. **Concentration Risk**: Adjust for name concentration (Herfindahl index)
4. **LGD Uncertainty**: Model LGD volatility, not just point estimates
5. **Validation**: Backtest EC models against actual losses

## Concentration Adjustments

### Granularity Adjustment
```
EC_adjusted = EC × (1 + GA)

GA ≈ Herfindahl Index × correlation factor
```

### Sector Concentration
```
Consider:
- Industry concentration
- Geographic concentration
- Product concentration
```

## References

1. Vasicek, O. - "Probability of Loss on Loan Portfolio"
2. Basel Committee - IRB Approach
3. Gordy, M. - "A Comparative Anatomy of Credit Risk Models"
4. CreditMetrics Technical Document
5. Moody's Analytics - Portfolio Manager

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

