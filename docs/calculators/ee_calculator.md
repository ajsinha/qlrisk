# Expected Exposure (EE) Calculator

## Overview

The Expected Exposure (EE) Calculator computes the average expected positive credit exposure at future dates. EE is the risk-neutral expectation of exposure and is fundamental to CVA calculations and regulatory capital under the Internal Model Method (IMM).

## Core Formulas

### Expected Exposure at Time t
```
EE(t) = E[max(0, V(t))]

where:
V(t) = Portfolio value at time t under risk-neutral measure
E[·] = Risk-neutral expectation
```

### Effective Expected Exposure (EEE)
```
EEE(t) = max(EE(t), EEE(t-Δt))

Non-decreasing function that captures rollover risk
```

### Effective EPE
```
Effective EPE = (1/T) × ∫₀ᵀ EEE(t) dt

Average of EEE profile over exposure horizon
```

## Calculation Methods

### 1. Monte Carlo Simulation (Default)

```text
for each simulation path:
    for each time point t:
        Simulate risk factors
        Value portfolio
        Exposure(t) = max(0, Value(t))

EE(t) = mean(Exposures at time t across all paths)
```

### 2. Analytical Approximation

For simple products with known distributions:

```
EE(t) ≈ MTM₀ × exp(μt) × N(d₁) + σ√t × n(d₁)

where:
d₁ = (ln(MTM₀/0) + (μ + σ²/2)t) / (σ√t)
N(·) = Standard normal CDF
n(·) = Standard normal PDF
```

### 3. American Monte Carlo (AMC)

For portfolios with optionality:
```
Uses regression (Longstaff-Schwartz) to estimate 
continuation values at each time step
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_mtm` | float | Yes | Current mark-to-market value |
| `notional` | float | Yes | Notional amount |
| `remaining_maturity` | float | Yes | Time to maturity in years |
| `volatility` | float | Yes | Annualized volatility |
| `product_type` | str | No | Product type (default "irs") |
| `interest_rate` | float | No | Risk-free/drift rate |
| `drift` | float | No | Expected drift |
| `collateral_held` | float | No | Collateral value |
| `margin_period_of_risk` | float | No | MPOR for margined trades |
| `num_simulations` | int | No | Monte Carlo paths (default 10,000) |
| `time_steps` | int | No | Time grid points |

## Usage Examples

### Basic EE Calculation

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
ee_calc = factory.get_ee_calculator()

result = ee_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "product_type": "irs"
})

print(f"Final EE: ${result.value.ee:,.2f}")
print(f"Effective EPE: ${result.value.effective_epe:,.2f}")
print(f"Peak EE: ${result.value.peak_ee:,.2f}")
```

### EE Profile for CVA

```python
result = ee_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20
})

# EE profile for CVA integration
for t, ee, eee in zip(result.value.time_points, 
                       result.value.ee_profile,
                       result.value.eee_profile):
    print(f"  Year {t:.2f}: EE=${ee:,.0f}, EEE=${eee:,.0f}")
```

### With Collateral (Margined Trade)

```python
# CSA with daily margin
result = ee_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "collateral_held": 450_000,
    "margin_period_of_risk": 10/252  # 10 business days
})

print(f"Margined EE: ${result.value.ee:,.2f}")
# Much lower than unmargined due to collateral
```

## Output Structure

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class EEResult:
    """Result of Expected Exposure calculation."""
    ee: float  # Expected Exposure at maturity
    ee_profile: List[float]  # EE over time
    eee_profile: List[float]  # Effective EE (non-decreasing)
    time_points: List[float]
    effective_epe: float  # Time-weighted average of EEE
    peak_ee: float
    components: Dict[str, Any]
```

## EE Profile Characteristics

### Interest Rate Swap
```
EE Profile (hump-shaped):
     ^
     |     ***
     |   **   **
     |  *       **
     | *          ***
     |*               **
     +-------------------> Time
        Peak at ~30-40% of maturity
```

### Why IRS Has Hump Shape:
1. **Early**: Low uncertainty, low EE
2. **Middle**: Maximum accumulated uncertainty, peak EE
3. **Late**: Fewer remaining cash flows, declining EE

### Cross-Currency Swap
```
EE Profile (generally increasing):
     ^
     |              ****
     |          ****
     |      ****
     |  ****
     |**
     +-------------------> Time
        Notional exchange at maturity drives high final EE
```

## EE vs EEE (Effective Expected Exposure)

```
Time    EE        EEE
0.25    100,000   100,000  <- Start
0.50    150,000   150,000  <- EE increasing
0.75    200,000   200,000  <- Peak
1.00    180,000   200,000  <- EEE = max(EE, prior EEE)
1.25    160,000   200,000  <- EEE maintains maximum
1.50    140,000   200,000  
```

EEE captures **rollover risk** - the risk that exposure could increase if trades are rolled over at adverse levels.

## Regulatory Context

### Basel III IMM
- Effective EPE used for EAD calculation
- EAD = α × Effective EPE (α = 1.4)
- Time horizon: max(1 year, longest maturity)

### CVA Capital Calculation
- EE profile is primary input to CVA
- Uses risk-neutral simulation
- Discounting and survival probability integration

### Margin Requirements
- MPOR determines exposure horizon for margined trades
- Standard MPOR: 10 days (bilateral), 5 days (centrally cleared)

## Best Practices

1. **Simulation Count**: Use at least 10,000 paths for stable estimates
2. **Time Grid**: Finer grid for near-term, coarser for long-term
3. **Variance Reduction**: Apply antithetic variates, control variates
4. **Collateral Modeling**: Properly model MPOR for margined trades
5. **Netting**: Calculate EE at netting set level

## EE for Netting Sets

Portfolio EE is NOT the sum of individual trade EEs:

```
EE_portfolio ≤ Σ EE_individual

due to netting benefits
```

For correlated trades:
```
EE_netting_set = E[max(0, Σ Vᵢ(t))]
```

## Relationship to Other Metrics

| Metric | Definition | Relationship |
|--------|------------|--------------|
| EE | E[max(0, V)] | Base metric |
| PFE | Percentile[max(0, V)] | PFE > EE typically |
| EPE | Average EE | Used for capital |
| EEE | max(EE, prior EEE) | Captures rollover |

## References

1. Pykhtin, M. - "Modeling Credit Exposure for Collateralized Counterparties"
2. Gregory, J. - "Counterparty Credit Risk and CVA"
3. Basel Committee - IMM Guidelines
4. Brigo, D. & Capponi, A. - "Bilateral CVA"

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

