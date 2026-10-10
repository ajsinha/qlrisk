# Initial Margin (IM) Calculator

## Overview

The Initial Margin (IM) Calculator estimates the collateral required upfront to cover potential future exposure over the margin period of risk (MPOR). IM protects against counterparty default during the closeout period and is mandatory for both cleared and uncleared OTC derivatives.

## Calculation Methods

### 1. Schedule-Based Approach (Default)

Uses regulatory notional-based percentages:

```
IM = NGR × Schedule Rate × Notional × MPOR Factor

where:
NGR = Net-to-Gross Ratio (netting benefit)
MPOR Factor = √(MPOR / 10 days)  [adjustment for non-standard MPOR]
```

**Regulatory Schedule Rates:**

| Asset Class | Rate (≤1yr) | Rate (1-5yr) | Rate (>5yr) |
|-------------|-------------|--------------|-------------|
| Interest Rate | 1% | 2% | 4% |
| FX | 6% | 8% | 10% |
| Credit | 2% | 5% | 10% |
| Equity | 15% | 15% | 15% |
| Commodity | 15% | 15% | 15% |

### 2. ISDA SIMM (Standard Initial Margin Model)

Risk-sensitivity based approach:

```
IM = √[Delta Risk² + Vega Risk² + Curvature Risk²]

Delta Risk = Σₖ Σᵢⱼ ρᵢⱼ × RWᵢ × sᵢ × RWⱼ × sⱼ

where:
sᵢ = Delta sensitivity to risk factor i
RWᵢ = Risk weight for factor i
ρᵢⱼ = Correlation between factors i and j
```

### 3. CCP Margin (SPAN-like)

For cleared derivatives:

```
IM = Scanning Risk + Intra-commodity Spread Charge 
   + Inter-commodity Spread Credit + Short Option Minimum

Scanning Risk = max(Portfolio Value Change across scenarios)
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notional` | float | Yes | Trade notional |
| `product_type` | str | Yes | "irs", "fx", "equity", "credit", "commodity" |
| `remaining_maturity` | float | Yes | Maturity in years |
| `volatility` | float | No | For VaR-based approaches |
| `delta` | float | No | Option delta (default 1.0) |
| `delta_sensitivities` | Dict | No | SIMM delta sensitivities |
| `vega_sensitivities` | Dict | No | SIMM vega sensitivities |
| `curvature_sensitivities` | Dict | No | SIMM curvature sensitivities |
| `mpor` | float | No | Margin period of risk in days |

## Usage Examples

### Schedule-Based IM

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
im_calc = factory.get_im_calculator()

# Interest Rate Swap
result = im_calc.calculate({
    "notional": 100_000_000,
    "product_type": "irs",
    "remaining_maturity": 5.0
})

print(f"Initial Margin: ${result.value.initial_margin:,.2f}")
print(f"IM as % of Notional: {result.value.im_as_pct_notional:.2%}")
print(f"Method: {result.value.method}")
```

### FX Forward

```python
result = im_calc.calculate({
    "notional": 50_000_000,
    "product_type": "fx",
    "remaining_maturity": 1.0
})

print(f"FX IM: ${result.value.initial_margin:,.2f}")
```

### With SIMM Sensitivities

```python
# SIMM-style calculation with sensitivities
result = im_calc.calculate({
    "notional": 100_000_000,
    "product_type": "irs",
    "remaining_maturity": 5.0,
    "delta_sensitivities": {
        "USD_1Y": 50_000,
        "USD_5Y": 150_000,
        "USD_10Y": 100_000
    },
    "vega_sensitivities": {
        "USD_5Y": 25_000
    }
})

print(f"SIMM IM: ${result.value.initial_margin:,.2f}")
```

## Output Structure

```python
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class IMResult:
    """Result of Initial Margin calculation."""
    initial_margin: float
    im_as_pct_notional: float
    method: str
    components: Dict[str, Any]
```

## ISDA SIMM Details

### Risk Classes
1. **Interest Rate**: Rate sensitivities by tenor/currency
2. **Credit (Qualifying)**: Investment grade credit
3. **Credit (Non-Qualifying)**: High yield credit
4. **Equity**: Stock/index sensitivities
5. **Commodity**: Commodity sensitivities
6. **FX**: Currency sensitivities

### SIMM Risk Weights (Sample)

**Interest Rate (USD):**
| Tenor | Risk Weight |
|-------|-------------|
| 2W | 77 |
| 1M | 77 |
| 3M | 77 |
| 6M | 70 |
| 1Y | 63 |
| 2Y | 56 |
| 5Y | 56 |
| 10Y | 56 |
| 15Y | 59 |
| 20Y | 66 |
| 30Y | 66 |

### SIMM Calculation Example

```
Delta IM for USD rates:
Weighted Sensitivity = RW × Sensitivity
Total = √(Σᵢⱼ ρᵢⱼ × WSᵢ × WSⱼ)

With:
WS_1Y = 63 × $50,000 = $3.15M
WS_5Y = 56 × $150,000 = $8.4M
WS_10Y = 56 × $100,000 = $5.6M

Apply correlation matrix and aggregate
```

## Regulatory Context

### BCBS-IOSCO Requirements

**Bilateral Uncleared:**
- Phase-in completed (all in-scope entities)
- Threshold: €50M / $50M
- MPOR: 10 business days minimum

**Centrally Cleared:**
- CCP-specific margin models
- MPOR: 5 business days (standard)
- 2-day for certain liquid products

### Margin Period of Risk

| Scenario | MPOR |
|----------|------|
| Cleared (standard) | 5 days |
| Bilateral (standard) | 10 days |
| Bilateral (illiquid) | 20 days |
| Bilateral (disputed) | 20 days |
| Large netting sets (>5000) | 20 days |

## IM vs VM Comparison

| Aspect | Initial Margin (IM) | Variation Margin (VM) |
|--------|--------------------|-----------------------|
| Purpose | Potential future exposure | Current exposure |
| Timing | Upfront | Daily |
| Calculation | SIMM/Schedule/CCP | Mark-to-market |
| Segregation | Yes (required) | No |
| Two-way | Yes | Yes |

## Best Practices

1. **Model Choice**: Use SIMM when approved, schedule as fallback
2. **Sensitivity Calculation**: Accurate bumped valuations
3. **Aggregation**: Proper netting set treatment
4. **Threshold Monitoring**: Track aggregate amounts vs thresholds
5. **Backtesting**: Validate IM coverage regularly

## IM Optimization

Strategies to reduce IM:

1. **Portfolio Compression**: Reduce notional through tear-ups
2. **Trade Restructuring**: Combine trades to offset sensitivities
3. **Clearing**: Move to CCP where IM may be lower
4. **Netting**: Maximize offsetting positions
5. **Collateral Upgrade**: Post eligible collateral efficiently

## Cross-Margining

Some CCPs allow cross-margining:

```
Combined IM < IM_rates + IM_credit + IM_equity

due to correlation offsets between asset classes
```

## References

1. ISDA SIMM Methodology
2. BCBS-IOSCO Margin Requirements
3. CME/ICE/LCH Margin Methodologies
4. EMIR/Dodd-Frank Margin Rules

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

