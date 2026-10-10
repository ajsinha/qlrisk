# Expected Loss (EL) Calculator

## Overview

The Expected Loss (EL) Calculator computes the average loss expected from credit events over a specified time horizon. EL is the primary measure for credit risk provisioning and is fundamental to loan loss reserves, IFRS 9 ECL, and CECL calculations.

## Core Formula

```
EL = PD × LGD × EAD

where:
PD  = Probability of Default
LGD = Loss Given Default
EAD = Exposure at Default
```

For annualized expected loss rate:
```
EL Rate = EL / EAD = PD × LGD
```

## Calculation Variants

### 1. Point-in-Time (PIT) EL

Uses current economic conditions for PD/LGD estimation.

```text
# PIT calculation
EL_pit = PD_pit × LGD_pit × EAD
```

### 2. Through-the-Cycle (TTC) EL

Uses long-term average PD/LGD across economic cycles.

```text
# TTC calculation (for regulatory capital)
EL_ttc = PD_ttc × LGD_ttc × EAD
```

### 3. Term Structure EL

Calculates EL over the full exposure lifetime.

**Formula:**
```
Lifetime EL = Σ [EADₜ × PDₜ × LGDₜ × DFₜ]

where:
EADₜ = Exposure at time t
PDₜ = Marginal PD for period t
LGDₜ = LGD at time t
DFₜ = Discount factor to time t
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pd` | float | Yes | Probability of Default (0-1) |
| `lgd` | float | Yes | Loss Given Default (0-1) |
| `ead` | float | Yes | Exposure at Default (currency) |
| `time_horizon` | float | No | Time horizon in years (default 1.0) |
| `maturity` | float | No | Remaining maturity for lifetime EL |
| `recovery_rate` | float | No | Alternative to LGD (LGD = 1 - RR) |
| `pd_term_structure` | List[float] | No | PD curve for lifetime EL |
| `time_points` | List[float] | No | Time points for term structure |

## Usage Examples

### Basic EL Calculation

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
el_calc = factory.get_el_calculator()

result = el_calc.calculate({
    "pd": 0.02,      # 2% PD
    "lgd": 0.45,     # 45% LGD
    "ead": 10_000_000,
    "time_horizon": 1.0
})

print(f"Expected Loss: ${result.value.expected_loss:,.2f}")
print(f"EL Rate: {result.value.expected_loss_rate:.4%}")
```

### Lifetime EL with Term Structure

```python
# Multi-period EL calculation
result = el_calc.calculate({
    "pd": 0.02,
    "lgd": 0.45,
    "ead": 10_000_000,
    "pd_term_structure": [0.02, 0.025, 0.03, 0.035, 0.04],
    "time_points": [1.0, 2.0, 3.0, 4.0, 5.0]
})

print(f"Lifetime EL: ${result.value.expected_loss:,.2f}")
```

### Using Recovery Rate

```python
# Alternative: specify recovery rate instead of LGD
result = el_calc.calculate({
    "pd": 0.02,
    "recovery_rate": 0.55,  # 55% recovery = 45% LGD
    "ead": 10_000_000
})
print(f"Expected Loss: ${result.value.expected_loss:,.2f}")
```

## Output Structure

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class ELResult:
    """Result of Expected Loss calculation."""
    expected_loss: float
    expected_loss_rate: float
    annualized_el: float
    components: Dict[str, float]
    term_structure: Optional[Dict[str, List[float]]] = None
```

## EL Interpretation

| EL Rate | Risk Category | Typical Rating |
|---------|---------------|----------------|
| < 0.05% | Very Low | AAA-AA |
| 0.05-0.20% | Low | A-BBB |
| 0.20-1.00% | Medium | BB |
| 1.00-5.00% | High | B |
| > 5.00% | Very High | CCC and below |

## Regulatory Context

### Basel III
- EL is deducted from capital (EL = PD × LGD × EAD)
- Shortfall = max(0, EL - Provisions) deducted from Tier 1

### IFRS 9 ECL Stages
| Stage | Condition | ECL Horizon |
|-------|-----------|-------------|
| Stage 1 | Performing | 12-month EL |
| Stage 2 | SICR | Lifetime EL |
| Stage 3 | Credit-impaired | Lifetime EL |

### CECL (US GAAP)
- Lifetime ECL from day one
- Reasonable and supportable forecasts
- Historical loss experience for remaining life

## Portfolio EL

For a portfolio of N exposures:
```
Portfolio EL = Σᵢ ELᵢ = Σᵢ (PDᵢ × LGDᵢ × EADᵢ)
```

Note: Unlike Unexpected Loss, EL is simply additive across the portfolio.

## Best Practices

1. **Data Quality**: Ensure accurate PD, LGD, EAD inputs
2. **Time Consistency**: Match PD/LGD time horizons
3. **Economic Scenarios**: Use forward-looking estimates
4. **Discounting**: Apply appropriate discount rates for lifetime EL
5. **Stress Testing**: Calculate stressed EL scenarios

## Relationship to Other Metrics

```
Unexpected Loss (UL) = EAD × √[PD × LGD² × σ²(LGD) + LGD² × σ²(PD)]

Economic Capital ≈ α × (UL - EL)  where α is confidence multiplier

CVA relates to risk-neutral EL across exposure profile
```

## References

1. Basel Committee on Banking Supervision - IRB Approach
2. IFRS 9 - Financial Instruments
3. FASB ASC 326 - CECL Standard
4. Moody's Analytics - EL Modeling Guide

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

