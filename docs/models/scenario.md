# Scenario Model Documentation
## Overview

The Scenario module provides models for stress testing and simulation scenarios, including market shocks and Monte Carlo path generation.

## Classes

### ScenarioType (Enum)

Types of market scenarios.

| Value | Name | Description |
|-------|------|-------------|
| `base` | `BASE` | Base/current market |
| `stress` | `STRESS` | Stress scenario |
| `historical` | `HISTORICAL` | Historical scenario |
| `monte_carlo` | `MONTE_CARLO` | Monte Carlo simulation |
| `hypothetical` | `HYPOTHETICAL` | Hypothetical scenario |

### ShockType (Enum)

Types of market shocks.

| Value | Name | Description |
|-------|------|-------------|
| `absolute` | `ABSOLUTE` | Absolute shift |
| `relative` | `RELATIVE` | Relative (percentage) shift |
| `parallel` | `PARALLEL` | Parallel curve shift |
| `twist` | `TWIST` | Curve twist (steepening/flattening) |
| `butterfly` | `BUTTERFLY` | Butterfly shift |

### RiskFactorShock (Dataclass)

Shock to a single risk factor.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `risk_factor` | str | '' | Risk factor name |
| `shock_type` | ShockType | ShockType.RELATIVE | Type of shock |
| `shock_value` | float | 0.0 | Shock magnitude |
| `shock_unit` | str | 'percent' | Unit of shock |

### CurveShock (Dataclass)

Shock to a yield curve.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `curve_name` | str | '' | Curve identifier |
| `shock_type` | ShockType | ShockType.PARALLEL | Type of shock |
| `parallel_shift` | float | 0.0 | Parallel shift (bps) |
| `short_end_shift` | float | 0.0 | Short end shift |
| `long_end_shift` | float | 0.0 | Long end shift |
| `pivot_point` | float | 5.0 | Pivot tenor (years) |

### Scenario (Dataclass)

Complete market scenario.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `scenario_id` | str | auto-generated | Unique identifier |
| `name` | str | '' | Scenario name |
| `description` | str | '' | Description |
| `scenario_type` | ScenarioType | ScenarioType.STRESS | Type |
| `scenario_date` | date | today() | Scenario date |
| `ir_shocks` | Dict | dict() | IR curve shocks |
| `fx_shocks` | Dict | dict() | FX rate shocks |
| `credit_shocks` | Dict | dict() | Credit spread shocks |
| `equity_shocks` | Dict | dict() | Equity price shocks |
| `vol_shocks` | Dict | dict() | Volatility shocks |
| `commodity_shocks` | Dict | dict() | Commodity shocks |
| `probability` | float | 1.0 | Scenario probability |
| `severity` | str | 'medium' | Severity level |
| `regulatory` | bool | False | Regulatory scenario flag |

### ScenarioSet (Dataclass)

Collection of scenarios for stress testing.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `set_id` | str | auto-generated | Unique identifier |
| `name` | str | '' | Set name |
| `scenarios` | List | list() | Scenario list |

### MonteCarloScenarioSet (Dataclass)

Monte Carlo simulation configuration.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `set_id` | str | auto-generated | Unique identifier |
| `num_paths` | int | 10000 | Number of paths |
| `time_horizon` | float | 5.0 | Time horizon (years) |
| `time_steps` | int | 60 | Number of time steps |
| `seed` | int | 42 | Random seed |
| `paths` | List | list() | Generated paths |

## Regulatory Scenarios

Pre-defined regulatory scenarios:

| Scenario | Description |
|----------|-------------|
| `CCAR_SEVERELY_ADVERSE` | CCAR severely adverse |
| `CCAR_ADVERSE` | CCAR adverse |
| `EBA_ADVERSE` | EBA adverse |

## Usage Examples

```python
from qlrisk.models import (
    Scenario, ScenarioType, ShockType,
    CurveShock, RiskFactorShock, ScenarioSet
)

# Create stress scenario
scenario = Scenario(
    name="Credit Crisis",
    scenario_type=ScenarioType.STRESS,
    severity="severe"
)

# Add IR shock (100 bps parallel shift)
scenario.add_ir_shock("USD", CurveShock(
    curve_name="USD-SOFR",
    shock_type=ShockType.PARALLEL,
    parallel_shift=100.0
))

# Add FX shock (20% depreciation)
scenario.add_fx_shock("EURUSD", RiskFactorShock(
    risk_factor="EURUSD",
    shock_type=ShockType.RELATIVE,
    shock_value=-20.0
))

# Add credit shock (200 bps widening)
scenario.add_credit_shock("IG", RiskFactorShock(
    risk_factor="CDX.NA.IG",
    shock_type=ShockType.ABSOLUTE,
    shock_value=200.0,
    shock_unit="bps"
))

# Create scenario set
scenario_set = ScenarioSet(name="Annual Stress Tests")
scenario_set.add_scenario(scenario)
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
