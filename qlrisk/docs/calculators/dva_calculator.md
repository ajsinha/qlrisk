# DVA Calculator Documentation v1.2.0

## Overview

The DVA (Debit Valuation Adjustment) Calculator computes the benefit from own default risk. DVA represents the expected gain to the institution if it defaults on its obligations.

## Formula

$$DVA = \sum_{i=1}^{n} LGD_{own} \times ENE(t_i) \times PD_{own}(t_{i-1}, t_i) \times DF(t_i)$$

Where:
- $LGD_{own}$ = Own Loss Given Default
- $ENE(t_i)$ = Expected Negative Exposure at time $t_i$
- $PD_{own}$ = Own marginal probability of default
- $DF(t_i)$ = Discount factor

## Class: DVACalculator

### Input: DVAInput

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exposure_profile` | List[float] | [] | Exposure values (negative = liability) |
| `time_grid` | List[float] | [] | Time points in years |
| `own_pd_curve` | Dict[float, float] | {} | Own PD curve |
| `own_lgd` | float | 0.60 | Own LGD |
| `discount_curve` | Dict[float, float] | {} | Discount rates |

### Output: DVAResult

| Field | Type | Description |
|-------|------|-------------|
| `dva` | float | Debit Valuation Adjustment |
| `expected_negative_exposure` | float | Average negative exposure |
| `own_default_probability` | float | Cumulative own PD |

## Usage Example

```python
from calculator.python import DVACalculator, DVAInput

calculator = DVACalculator()

result = calculator.calculate(DVAInput(
    exposure_profile=[-100000, -120000, -110000, -90000, -70000],
    time_grid=[0.0, 0.25, 0.5, 0.75, 1.0],
    own_pd_curve={0.25: 0.005, 0.5: 0.01, 0.75: 0.015, 1.0: 0.02},
    own_lgd=0.60,
    discount_curve={0.25: 0.05, 0.5: 0.05, 0.75: 0.05, 1.0: 0.05}
))

print(f"DVA: ${result.dva:,.2f}")
```

## Relationship to CVA

DVA is conceptually the mirror image of CVA:
- **CVA**: Loss from counterparty default (we are owed money)
- **DVA**: Benefit from own default (we owe money)

$$Total\ Bilateral\ CVA = CVA - DVA$$

## Regulatory Treatment

- DVA recognition varies by jurisdiction
- Basel III limits DVA in regulatory capital
- IFRS 13 requires DVA in fair value accounting

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
