# Loss Given Default (LGD) Calculator

## Overview

The Loss Given Default (LGD) Calculator estimates the percentage of exposure that would be lost if a counterparty defaults. LGD = 1 - Recovery Rate. It is a critical component in Expected Loss calculations and credit risk capital requirements.

## Calculation Methods

### 1. Seniority-Based LGD (Default)

Uses predefined LGD rates based on debt seniority in the capital structure.

**Built-in Seniority LGDs:**
| Seniority | LGD |
|-----------|-----|
| Senior Secured | 25% |
| Senior Unsecured | 45% |
| Subordinated | 75% |
| Junior Subordinated | 85% |

### 2. Collateral-Adjusted LGD

Adjusts LGD based on collateral value and haircuts.

**Formula:**
```
LGD = max(0, 1 - (Collateral Value × (1 - Haircut)) / EAD)

Effective LGD = Base LGD × (1 - Collateral Coverage)
```

**Required Inputs:**
- `collateral_value`: Market value of collateral
- `exposure_value`: Exposure at Default (EAD)
- `collateral_haircut`: Haircut percentage (default varies by type)

### 3. Collateral Type-Based

Uses regulatory haircuts based on collateral type.

**Built-in Collateral Haircuts:**
| Collateral Type | Haircut |
|-----------------|---------|
| Cash | 0% |
| Government Bonds | 2% |
| Corporate Bonds (IG) | 10% |
| Corporate Bonds (HY) | 25% |
| Equities | 25% |
| Real Estate | 35% |
| Commodities | 25% |

### 4. Workout LGD Model

Estimates LGD based on historical recovery data and workout costs.

**Formula:**
```
LGD = 1 - (Recovery Value - Workout Costs) / EAD × Discount Factor

Discount Factor = 1 / (1 + r)^t
where t = average time to recovery
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `seniority` | str | No | Debt seniority level |
| `collateral_type` | str | No | Type of collateral held |
| `collateral_value` | float | No | Market value of collateral |
| `exposure_value` | float | No | Exposure at default |
| `collateral_haircut` | float | No | Override haircut percentage |
| `recovery_rate` | float | No | Direct recovery rate input |
| `workout_costs` | float | No | Expected workout costs |
| `time_to_recovery` | float | No | Expected years to recovery |

## Usage Examples

### Basic Seniority-Based LGD

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
lgd_calc = factory.get_lgd_calculator()

# Senior secured debt
result = lgd_calc.calculate({
    "seniority": "senior_secured"
})
print(f"LGD: {result.value:.2%}")  # Output: LGD: 25.00%

# Senior unsecured debt
result = lgd_calc.calculate({
    "seniority": "senior_unsecured"
})
print(f"LGD: {result.value:.2%}")  # Output: LGD: 45.00%
```

### Collateral-Adjusted LGD

```python
# With real estate collateral
result = lgd_calc.calculate({
    "seniority": "senior_secured",
    "collateral_type": "real_estate",
    "collateral_value": 5_000_000,
    "exposure_value": 10_000_000
})
print(f"Collateral-Adjusted LGD: {result.value:.2%}")
```

### Direct Recovery Rate

```python
# Using known recovery rate
result = lgd_calc.calculate({
    "recovery_rate": 0.55  # 55% recovery
})
print(f"LGD: {result.value:.2%}")  # Output: LGD: 45.00%
```

## Output

The calculator returns a `CalculationResult` containing:
- `value`: The calculated LGD as a decimal (e.g., 0.45 for 45%)
- `metadata`: Calculation details including method used

## LGD by Asset Class (Regulatory Guidelines)

| Asset Class | Typical LGD Range |
|-------------|-------------------|
| Corporate (Senior Secured) | 25-35% |
| Corporate (Senior Unsecured) | 40-50% |
| Retail Mortgages | 10-20% |
| Retail Revolving | 75-85% |
| SME | 40-50% |
| Sovereign | 45% |

## Regulatory Context

### Basel II/III Foundation IRB
- Senior claims on corporates: 45%
- Subordinated claims: 75%

### Basel II/III Advanced IRB
- Banks may use own LGD estimates subject to:
  - Minimum 7-year data history
  - Economic downturn adjustments
  - Collateral recognition criteria

### IFRS 9
- Point-in-time (PIT) LGD for ECL
- Forward-looking macroeconomic adjustments

## Best Practices

1. **Downturn LGD**: Use stressed LGD estimates for regulatory capital
2. **Time Value**: Discount recoveries to default date
3. **Costs**: Include all direct and indirect workout costs
4. **Collateral Updates**: Regularly revalue collateral
5. **Cure Rates**: Consider possibility of cure (return to performing)

## References

1. Basel Committee - IRB Approach to Credit Risk
2. Moody's Ultimate Recovery Database
3. S&P LossStats Database
4. ISDA Recovery Rate Studies

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

