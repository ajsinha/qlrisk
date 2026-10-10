# MVA Calculator Documentation v1.2.0

## Overview

The MVA (Margin Valuation Adjustment) Calculator computes the cost of funding Initial Margin (IM) posted to CCPs or bilateral counterparties under margin requirements.

## Formula

$$MVA = \sum_{i=1}^{n} s_f \times IM(t_i) \times DF(t_i) \times \Delta t_i$$

Where:
- $s_f$ = Funding spread
- $IM(t_i)$ = Initial margin at time $t_i$
- $DF(t_i)$ = Discount factor

## Initial Margin Methods

| Method | Description |
|--------|-------------|
| **SIMM** | ISDA Standard Initial Margin Model |
| **Grid/Schedule** | Regulatory schedule-based |
| **CCP Model** | CCP-specific model (VaR/SPAN) |
| **Historical VaR** | Historical simulation VaR |

## Class: MVACalculator

### Input: MVAInput

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `initial_margin_profile` | List[float] | [] | IM values over time |
| `time_grid` | List[float] | [] | Time points in years |
| `funding_spread` | float | 0.01 | Funding spread |
| `discount_curve` | Dict[float, float] | {} | Discount rates |

### Output: MVAResult

| Field | Type | Description |
|-------|------|-------------|
| `mva` | float | Margin Valuation Adjustment |
| `average_margin` | float | Average IM requirement |

## Usage Example

```python
from calculator.python import MVACalculator, MVAInput

calculator = MVACalculator()

result = calculator.calculate(MVAInput(
    initial_margin_profile=[5e6, 6e6, 5.5e6, 5e6, 4e6],
    time_grid=[0.0, 1.0, 2.0, 3.0, 4.0],
    funding_spread=0.015,  # 150 bps
    discount_curve={1.0: 0.05, 2.0: 0.05, 3.0: 0.05, 4.0: 0.05}
))

print(f"MVA: ${result.mva:,.2f}")
print(f"Average Margin: ${result.average_margin:,.2f}")
```

## Regulatory Context

- **UMR**: Uncleared Margin Rules (2016-2022 phased)
- **SIMM**: Industry standard for bilateral IM
- **CCP Clearing**: Mandatory for standardized derivatives

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
