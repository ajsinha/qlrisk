# FVA Calculator Documentation v1.2.0

## Overview

The FVA (Funding Valuation Adjustment) Calculator computes the cost or benefit of funding uncollateralized derivatives positions.

## Components

$$FVA = FCA - FBA$$

Where:
- **FCA** (Funding Cost Adjustment): Cost of funding positive exposures
- **FBA** (Funding Benefit Adjustment): Benefit from funding negative exposures

## Formula

$$FCA = \sum_{i=1}^{n} s_f \times EE(t_i) \times S_{cp}(t_i) \times DF(t_i) \times \Delta t_i$$

$$FBA = \sum_{i=1}^{n} s_f \times ENE(t_i) \times S_{cp}(t_i) \times DF(t_i) \times \Delta t_i$$

Where:
- $s_f$ = Funding spread over risk-free rate
- $EE(t_i)$ = Expected positive exposure
- $ENE(t_i)$ = Expected negative exposure
- $S_{cp}(t_i)$ = Counterparty survival probability
- $DF(t_i)$ = Discount factor

## Class: FVACalculator

### Input: FVAInput

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `exposure_profile` | List[float] | [] | Exposure values |
| `time_grid` | List[float] | [] | Time points in years |
| `funding_spread` | float | 0.01 | Funding spread (1% = 0.01) |
| `discount_curve` | Dict[float, float] | {} | Discount rates |
| `counterparty_survival_curve` | Dict[float, float] | {} | CP survival probs |

### Output: FVAResult

| Field | Type | Description |
|-------|------|-------------|
| `fva` | float | Total FVA (FCA - FBA) |
| `fca` | float | Funding Cost Adjustment |
| `fba` | float | Funding Benefit Adjustment |

## Usage Example

```python
from calculator.python import FVACalculator, FVAInput

calculator = FVACalculator()

result = calculator.calculate(FVAInput(
    exposure_profile=[100000, 120000, 110000, 90000, 70000],
    time_grid=[0.0, 0.25, 0.5, 0.75, 1.0],
    funding_spread=0.015,  # 150 bps
    discount_curve={0.25: 0.05, 0.5: 0.05, 0.75: 0.05, 1.0: 0.05},
    counterparty_survival_curve={0.25: 0.99, 0.5: 0.98, 0.75: 0.97, 1.0: 0.96}
))

print(f"FVA: ${result.fva:,.2f}")
print(f"FCA: ${result.fca:,.2f}")
print(f"FBA: ${result.fba:,.2f}")
```

## Key Considerations

1. **Asymmetric Collateral**: FVA matters most for uncollateralized trades
2. **Treasury Integration**: Funding spread reflects actual funding costs
3. **Double Counting**: Avoid overlap with CVA in discounting

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
