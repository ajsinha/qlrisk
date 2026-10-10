# Potential Future Exposure (PFE) Calculator

## Overview

The Potential Future Exposure (PFE) Calculator estimates the maximum expected credit exposure at a specified confidence level over a time horizon. PFE captures the potential increase in exposure due to market movements and is critical for credit limit management and regulatory capital.

## Core Formula

For a given confidence level α (typically 95% or 99%):

```
PFE(t, α) = Quantile(Exposure(t), α)

where:
Exposure(t) = max(0, V(t))  at time t
V(t) = Portfolio value simulated under risk-neutral measure
```

## Calculation Methods

### 1. Parametric Method (Default)

Assumes log-normal distribution of future values.

**Formula:**
```
PFE(t) = MTM₀ × exp[(μ - σ²/2)t + z_α × σ × √t]

where:
MTM₀ = Current mark-to-market
μ = Drift rate
σ = Volatility
t = Time to maturity
z_α = Standard normal quantile at confidence α
```

For α = 95%: z_α = 1.645
For α = 99%: z_α = 2.326

### 2. Monte Carlo Simulation

Simulates thousands of price paths to build exposure distribution.

```python
for each path:
    Simulate risk factors over time grid
    Value portfolio at each time point
    Exposure(t) = max(0, Value(t))
    
PFE(t) = Percentile(Exposures at t, α)
```

### 3. Historical Simulation

Uses historical returns to project future exposures.

```python
for each historical scenario:
    Apply historical returns to current positions
    Calculate stressed portfolio value
    
PFE = Percentile(Stressed exposures, α)
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_mtm` | float | Yes | Current mark-to-market value |
| `notional` | float | Yes | Notional amount |
| `remaining_maturity` | float | Yes | Time to maturity in years |
| `volatility` | float | Yes | Annualized volatility |
| `product_type` | str | No | Product type for add-on factors |
| `interest_rate` | float | No | Risk-free rate (default 5%) |
| `fx_rate` | float | No | FX rate for FX products |
| `credit_spread` | float | No | Credit spread for CDS |
| `confidence_level` | float | No | Confidence level (default 0.95) |

## Usage Examples

### Basic PFE Calculation

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
pfe_calc = factory.get_pfe_calculator()

result = pfe_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "product_type": "irs"
})

print(f"PFE (95%): ${result.value.pfe:,.2f}")
print(f"Peak PFE: ${result.value.peak_pfe:,.2f}")
print(f"Average PFE: ${result.value.average_pfe:,.2f}")
```

### PFE Profile Over Time

```python
result = pfe_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "product_type": "irs"
})

# Access full PFE profile
for t, pfe in zip(result.value.time_points, result.value.pfe_profile):
    print(f"  Year {t:.2f}: ${pfe:,.0f}")
```

### Different Confidence Levels

```python
# 99% PFE for credit limits
result_99 = pfe_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "confidence_level": 0.99
})
print(f"PFE (99%): ${result_99.value.pfe:,.2f}")
```

## Output Structure

```python
@dataclass
class PFEResult:
    pfe: float                    # PFE at maturity
    pfe_profile: List[float]      # PFE at each time point
    time_points: List[float]      # Time grid
    peak_pfe: float               # Maximum PFE over life
    average_pfe: float            # Average PFE over life
    confidence_level: float       # Confidence level used
    components: Dict[str, Any]    # Calculation details
```

## PFE Profile Shapes

Different products exhibit characteristic PFE profiles:

### Interest Rate Swap
```
PFE Profile (typical hump shape):
     ^
     |     ***
     |   **   **
     |  *       **
     | *          ***
     |*               **
     +-------------------> Time
        Peak at ~40% of maturity
```

### FX Forward
```
PFE Profile (increasing):
     ^
     |              ***
     |          ****
     |      ****
     |  ****
     |**
     +-------------------> Time
        Increases to maturity
```

### Cross-Currency Swap
```
PFE Profile (increasing with notional exchange):
     ^
     |              *****
     |          ****
     |      ****
     |  ****
     |**
     +-------------------> Time
        Large jump at maturity (notional exchange)
```

## Product-Specific Volatility Guidelines

| Product | Typical Volatility | Notes |
|---------|-------------------|-------|
| IRS (USD) | 15-25% | Rate volatility × duration |
| FX Forward | 10-15% | FX pair volatility |
| CDS | 30-50% | Credit spread volatility |
| Equity Option | 20-40% | Underlying volatility |
| Commodity Swap | 25-35% | Commodity volatility |

## Regulatory Context

### Basel III
- PFE add-on is component of SA-CCR
- Used in IMM models for EAD

### Credit Limits
- Firms set counterparty limits based on PFE
- Typically use 95% or 97.5% confidence
- Peak PFE used for limit utilization

### CVA Capital
- PFE profile feeds into CVA calculation
- Regulatory CVA uses specific confidence levels

## Best Practices

1. **Time Grid**: Use appropriate granularity (monthly for <2yr, quarterly for >2yr)
2. **Volatility Updates**: Refresh volatility estimates regularly
3. **Wrong-Way Risk**: Adjust PFE for correlation with counterparty credit
4. **Netting**: Calculate PFE at netting set level
5. **Collateral**: Account for margin agreement terms

## PFE vs Other Metrics

| Metric | Definition | Typical Use |
|--------|------------|-------------|
| PFE | Percentile of future exposure | Credit limits |
| EE | Expected future exposure | CVA calculation |
| EPE | Average of EE profile | Regulatory capital |
| Max PFE | Peak of PFE profile | Limit utilization |

## Mathematical Details

### Time-Varying PFE

For IRS with duration D(t):
```
PFE(t) ≈ Notional × D(t) × σᵣ × √t × z_α

where:
D(t) = Duration at time t
σᵣ = Interest rate volatility
```

### Roll-Off Effect
As trade approaches maturity:
```
PFE(t) → 0 as t → T

due to:
- Decreasing time uncertainty
- Decreasing remaining cash flows
- Duration approaching zero
```

## References

1. Gregory, J. - "Counterparty Credit Risk"
2. Pykhtin, M. - "Measuring Counterparty Credit Exposure"
3. Basel Committee - SA-CCR Standard
4. ISDA SIMM Methodology

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

