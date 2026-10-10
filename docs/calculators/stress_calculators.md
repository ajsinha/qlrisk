# Stress Testing Calculators

## Overview

The Stress Testing module provides calculators for assessing counterparty credit risk under adverse market conditions. It includes Stressed Exposure and Peak Exposure calculators for regulatory compliance (CCAR, DFAST, EBA) and internal risk management.

---

# Stressed Exposure Calculator

## Purpose

Estimates credit exposure under stress scenarios by applying shocks to market risk factors and recalculating portfolio value.

## Stress Types

### 1. Historical Stress

Applies observed market movements from past crisis periods:

```
Stressed Exposure = Base Exposure + Σ(Factor Shocks × Sensitivities)
```

**Built-in Scenarios:**

| Scenario | Rate Shock | FX Shock | Credit Shock | Vol Shock | Correlation |
|----------|------------|----------|--------------|-----------|-------------|
| 2008 Crisis | -200 bps | +20% | +300 bps | 2.5x | +0.30 |
| COVID 2020 | -150 bps | +15% | +200 bps | 3.0x | +0.40 |
| EU Debt 2011 | +100 bps | +10% | +400 bps | 2.0x | +0.20 |
| Rate Shock Up | +200 bps | 0% | +50 bps | 1.5x | 0 |
| Rate Shock Down | -200 bps | 0% | +100 bps | 2.0x | 0 |

### 2. Hypothetical Stress

Applies user-defined or regulatory shock scenarios:

```
Stressed Exposure = f(Base, Custom Shocks)
```

### 3. Reverse Stress

Finds the scenario that causes a target loss level:

```
Find shock multiplier α such that:
Loss(α × base_scenario) = Target Loss
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_mtm` | float | Yes | Current mark-to-market |
| `notional` | float | Yes | Notional amount |
| `remaining_maturity` | float | Yes | Maturity in years |
| `volatility` | float | Yes | Base volatility |
| `product_type` | str | No | Product type for shocks |
| `stress_type` | str | No | "historical", "hypothetical", "reverse" |
| `stress_scenario` | str | No | Named scenario |
| `rate_shock` | float | No | Rate shock in bps |
| `fx_shock` | float | No | FX shock as percentage |
| `credit_shock` | float | No | Credit spread shock in bps |
| `volatility_shock` | float | No | Volatility multiplier |
| `correlation_shock` | float | No | Correlation change |

## Usage Examples

### Historical Stress

```python
from qlrisk.calculator import CalculatorFactory

factory = CalculatorFactory()
stress_calc = factory.get_calculator("stressed_exposure")

result = stress_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "product_type": "irs",
    "stress_type": "historical",
    "stress_scenario": "2008_crisis"
})

print(f"Base Exposure: ${500_000:,.2f}")
print(f"Stressed Exposure: ${result.value.stressed_exposure:,.2f}")
print(f"Stress Multiplier: {result.value.stress_multiplier:.2f}x")
```

### Custom Hypothetical Stress

```python
result = stress_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "product_type": "irs",
    "stress_type": "hypothetical",
    "rate_shock": -300,      # -300 bps
    "volatility_shock": 2.5   # 2.5x vol increase
})

print(f"Custom Stressed Exposure: ${result.value.stressed_exposure:,.2f}")
```

### Reverse Stress

```python
result = stress_calc.calculate({
    "current_mtm": 500_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "stress_type": "reverse"
})

print(f"Stress multiplier for 2x exposure: {result.value.stress_multiplier:.2f}")
```

## Output Structure

```python
@dataclass
class StressedExposureResult:
    stressed_exposure: float      # Exposure under stress
    stress_multiplier: float      # Stressed / Base ratio
    base_exposure: float          # Original exposure
    stress_scenario: str          # Scenario name
    components: Dict[str, Any]    # Detailed breakdown
```

---

# Peak Exposure Calculator

## Purpose

Calculates the maximum expected exposure over the life of the trade at a specified confidence level.

## Core Formula

```
Peak Exposure = max(PFE(t)) for all t ∈ [0, T]

where PFE(t) = Quantile(Exposure distribution at t, α)
```

## Calculation Methods

### 1. Monte Carlo Simulation

```python
for each simulation path:
    for each time point t:
        Simulate future exposure
    
PFE_profile[t] = Percentile(Exposures[t], α)
Peak_Exposure = max(PFE_profile)
```

### 2. Analytical Approximation

For diffusion processes:

```
Peak Exposure ≈ MTM₀ + z_α × Notional × σ × √T_peak

where T_peak ≈ 0.4 × Maturity (for IRS)
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_mtm` | float | Yes | Current MTM |
| `notional` | float | Yes | Notional amount |
| `remaining_maturity` | float | Yes | Maturity in years |
| `volatility` | float | Yes | Annualized volatility |
| `product_type` | str | No | Product type |
| `ee_profile` | List[float] | No | Pre-computed EE profile |
| `pfe_profile` | List[float] | No | Pre-computed PFE profile |
| `time_grid` | List[float] | No | Time points |
| `num_simulations` | int | No | MC paths (default 10,000) |
| `confidence_level` | float | No | Percentile (default 0.95) |
| `collateral_held` | float | No | Collateral offset |

## Usage Examples

### Basic Peak Exposure

```python
peak_calc = factory.get_calculator("peak_exposure")

result = peak_calc.calculate({
    "current_mtm": 250_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "product_type": "irs",
    "num_simulations": 10_000,
    "confidence_level": 0.95
})

print(f"Peak Exposure (95%): ${result.value.peak_exposure:,.2f}")
print(f"Peak Time: {result.value.peak_time:.2f} years")
print(f"Average Exposure: ${result.value.average_exposure:,.2f}")
```

### With Pre-computed Profile

```python
# Use existing EE/PFE profiles
result = peak_calc.calculate({
    "current_mtm": 250_000,
    "notional": 10_000_000,
    "remaining_maturity": 5.0,
    "volatility": 0.20,
    "pfe_profile": [250_000, 500_000, 750_000, 600_000, 400_000, 200_000],
    "time_grid": [0, 1, 2, 3, 4, 5]
})

print(f"Peak from profile: ${result.value.peak_exposure:,.2f}")
```

## Output Structure

```python
@dataclass
class PeakExposureResult:
    peak_exposure: float          # Maximum exposure
    peak_time: float              # Time of peak
    average_exposure: float       # Mean exposure over life
    exposure_profile: List[float] # Full exposure profile
    time_grid: List[float]        # Time points
    components: Dict[str, Any]    # Simulation details
```

---

## Regulatory Applications

### CCAR/DFAST (US)
- Annual stress testing for large banks
- Severely Adverse scenario required
- 9-quarter projection horizon

### EBA Stress Tests (EU)
- Biennial EU-wide stress tests
- Baseline and Adverse scenarios
- 3-year horizon

### Bank-Specific
- ICAAP stress testing
- Counterparty-specific scenarios
- Concentration stress

## Stress Testing Best Practices

1. **Scenario Coverage**: Include historical, hypothetical, and reverse stress
2. **Risk Factor Consistency**: Ensure coherent joint movements
3. **Wrong-Way Risk**: Stress counterparty credit with exposures
4. **Netting**: Stress at netting set level
5. **Collateral**: Stress collateral values and haircuts
6. **Liquidity**: Consider close-out timing under stress

## Integration with Other Metrics

```
Stressed CVA = LGD × Σ EE_stressed(t) × ΔPD_stressed(t) × DF(t)

Stressed EC = VaR_stressed - EL_stressed

Stressed RAROC = (Revenue - Costs - EL_stressed) / EC_stressed
```

## References

1. Federal Reserve CCAR Instructions
2. EBA Stress Testing Methodology
3. Basel Committee - Stress Testing Principles
4. ISDA Stress Testing Best Practices

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

