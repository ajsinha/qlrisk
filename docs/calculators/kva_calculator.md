# KVA Calculator Documentation v1.2.0

## Overview

The KVA (Capital Valuation Adjustment) Calculator computes the cost of holding regulatory capital against counterparty credit risk over the life of a derivative.

## Formula

$$KVA = \sum_{i=1}^{n} CoC \times K(t_i) \times DF(t_i) \times \Delta t_i$$

Where:
- $CoC$ = Cost of Capital (hurdle rate, typically 10-15%)
- $K(t_i)$ = Capital requirement at time $t_i$
- $DF(t_i)$ = Discount factor

## Capital Calculation

Capital is computed using Basel IRB formula:

$$K = LGD \times \left( \Phi \left( \frac{\Phi^{-1}(PD) + \sqrt{\rho} \times \Phi^{-1}(0.999)}{\sqrt{1-\rho}} \right) - PD \right)$$

$$RWA = 12.5 \times K \times EAD$$

$$Capital = 8\% \times RWA$$

Where:
- $\rho$ = Asset correlation
- $\Phi$ = Standard normal CDF

## Class: KVACalculator

### Input: KVAInput

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ead_profile` | List[float] | [] | EAD values over time |
| `time_grid` | List[float] | [] | Time points in years |
| `counterparty_pd` | float | 0.01 | Annual PD |
| `counterparty_lgd` | float | 0.45 | LGD |
| `cost_of_capital` | float | 0.10 | Hurdle rate (10%) |
| `discount_curve` | Dict[float, float] | {} | Discount rates |
| `capital_floor` | float | 0.0003 | Basel floor |

### Output: KVAResult

| Field | Type | Description |
|-------|------|-------------|
| `kva` | float | Capital Valuation Adjustment |
| `average_capital` | float | Average capital requirement |
| `peak_capital` | float | Peak capital requirement |

## Usage Example

```python
from calculator.python import KVACalculator, KVAInput

calculator = KVACalculator()

result = calculator.calculate(KVAInput(
    ead_profile=[10e6, 12e6, 11e6, 9e6, 7e6],
    time_grid=[0.0, 1.0, 2.0, 3.0, 4.0],
    counterparty_pd=0.02,
    counterparty_lgd=0.45,
    cost_of_capital=0.12,  # 12% hurdle rate
    discount_curve={1.0: 0.05, 2.0: 0.05, 3.0: 0.05, 4.0: 0.05}
))

print(f"KVA: ${result.kva:,.2f}")
print(f"Average Capital: ${result.average_capital:,.2f}")
print(f"Peak Capital: ${result.peak_capital:,.2f}")
```

## Regulatory Framework

- **Basel III/IV**: Standardised or IRB approach
- **CVA Capital Charge**: Additional capital for CVA volatility
- **Output Floor**: Minimum capital requirements

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
