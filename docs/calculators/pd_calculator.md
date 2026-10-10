# Probability of Default (PD) Calculator

## Overview

The Probability of Default (PD) Calculator estimates the likelihood that a counterparty will default on their obligations within a specified time horizon. PD is a fundamental component of credit risk measurement and is used in Expected Loss calculations, CVA, and regulatory capital requirements.

## Supported Models

### 1. Merton Structural Model (Default)

The Merton model treats a firm's equity as a call option on its assets, with default occurring when asset value falls below debt value at maturity.

**Formula:**
```
PD = N(-d2)

where:
d2 = [ln(V/D) + (r - σ²/2)T] / (σ√T)

V = Asset value
D = Debt value (default barrier)
r = Risk-free rate
σ = Asset volatility
T = Time horizon
N() = Standard normal CDF
```

**Required Inputs:**
- `asset_value`: Current market value of firm's assets
- `debt_value`: Face value of debt (default barrier)
- `asset_volatility`: Annualized volatility of asset returns
- `risk_free_rate`: Risk-free interest rate (optional, default 0)
- `time_horizon`: Time horizon in years (default 1.0)

### 2. Rating Transition Matrix Model

Uses historical rating transition matrices to estimate PD based on credit ratings.

**Formula:**
```
PD = P(Rating → Default | Time Horizon)
```

**Required Inputs:**
- `credit_rating`: Current credit rating (e.g., "AAA", "BBB", "B")
- `rating_pd`: Optional override for rating-based PD

**Built-in Rating PDs (1-year):**
| Rating | PD |
|--------|-----|
| AAA | 0.01% |
| AA | 0.02% |
| A | 0.05% |
| BBB | 0.20% |
| BB | 1.00% |
| B | 4.00% |
| CCC | 15.00% |
| CC | 30.00% |
| C | 50.00% |
| D | 100.00% |

### 3. Hazard Rate Model

Models default as a Poisson process with constant or time-varying hazard rate.

**Formula:**
```
PD = 1 - exp(-λT)

where:
λ = Hazard rate (instantaneous default intensity)
T = Time horizon
```

**Required Inputs:**
- `hazard_rate`: Instantaneous default probability
- `time_horizon`: Time horizon in years

### 4. Logistic Regression Model

Uses financial ratios and model coefficients for PD estimation.

**Formula:**
```
PD = 1 / (1 + exp(-z))

where:
z = β₀ + Σ(βᵢ × Xᵢ)

βᵢ = Model coefficients
Xᵢ = Financial ratios
```

**Required Inputs:**
- `financial_ratios`: Dictionary of ratio name to value
- `model_coefficients`: Dictionary of coefficient name to value

## Usage Examples

### Python Implementation

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()

# Rating-based PD
pd_calc = factory.get_pd_calculator(
    config={"model": "transition_matrix"}
)

result = pd_calc.calculate({
    "credit_rating": "BBB",
    "time_horizon": 1.0
})
print(f"PD: {result.value:.4%}")  # Output: PD: 0.2000%

# Merton model PD
pd_calc_merton = factory.get_pd_calculator(
    config={"model": "structural"}
)

result = pd_calc_merton.calculate({
    "asset_value": 100_000_000,
    "debt_value": 60_000_000,
    "asset_volatility": 0.25,
    "risk_free_rate": 0.05,
    "time_horizon": 1.0
})
print(f"Merton PD: {result.value:.4%}")
```

### Via CCR Engine

```python
from qlrisk.engine import CCREngine

with CCREngine() as engine:
    result = engine.calculate_ccr_metrics({
        "rating": "BBB",
        "counterparty_pd": 0.02,  # Fallback PD
        "notional": 10_000_000,
        "mtm": 500_000
    })
    print(f"PD: {result['pd']:.4%}")
```

## Output

The calculator returns a `CalculationResult` containing:
- `value`: The calculated PD as a decimal (e.g., 0.02 for 2%)
- `metadata`: Implementation details and calculation count

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | str | "structural" | PD model type: "structural", "transition_matrix", "hazard", "logistic" |
| `time_horizon` | float | 1.0 | Default time horizon in years |

## Regulatory Context

- **Basel II/III**: PD is a key input for IRB (Internal Ratings-Based) approach
- **IFRS 9**: Required for Expected Credit Loss (ECL) calculations
- **CECL**: Used in Current Expected Credit Loss model

## References

1. Merton, R.C. (1974). "On the Pricing of Corporate Debt"
2. Basel Committee on Banking Supervision - IRB Approach
3. Moody's and S&P Rating Transition Studies

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

