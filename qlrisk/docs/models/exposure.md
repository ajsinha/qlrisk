# Exposure Model Documentation v1.2.0

## Overview

The Exposure module provides models for exposure calculation results, including time-series profiles and regulatory metrics like SA-CCR.

## Classes

### ExposureType (Enum)

Types of exposure measures.

| Value | Description |
|-------|-------------|
| `CURRENT` | Current Exposure (CE) |
| `POTENTIAL_FUTURE` | Potential Future Exposure (PFE) |
| `EXPECTED` | Expected Exposure (EE) |
| `EFFECTIVE_EXPECTED` | Effective Expected Exposure (EEE) |
| `PEAK` | Peak Exposure |
| `STRESSED` | Stressed Exposure |

### ExposureMethod (Enum)

Exposure calculation methods.

| Value | Description |
|-------|-------------|
| `CURRENT_EXPOSURE` | Current Exposure Method (CEM) |
| `STANDARDISED` | SA-CCR |
| `INTERNAL_MODEL` | Internal Model Method (IMM) |
| `MONTE_CARLO` | Monte Carlo simulation |

### ExposureProfile (Dataclass)

Time-series of exposure values.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `profile_id` | str | Auto-generated | Unique identifier |
| `exposure_type` | ExposureType | EXPECTED | Type of exposure |
| `time_grid` | List[float] | [] | Time points (years) |
| `values` | List[float] | [] | Exposure values |
| `currency` | str | "USD" | Currency |
| `confidence_level` | float | 0.95 | Confidence for PFE |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_value_at_time(t)` | float | Interpolated value |
| `peak()` | float | Maximum exposure |
| `average()` | float | Average exposure |
| `time_weighted_average()` | float | Time-weighted average |

### ExposureResult (Dataclass)

Complete exposure calculation result.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `result_id` | str | Auto-generated | Unique identifier |
| `calculation_date` | datetime | now | Calculation timestamp |
| `reference_id` | str | "" | Trade/NS/Portfolio ID |
| `reference_type` | str | "" | Reference type |
| `method` | ExposureMethod | MONTE_CARLO | Method used |
| `current_exposure` | float | 0.0 | CE |
| `potential_future_exposure` | float | 0.0 | PFE |
| `expected_exposure` | float | 0.0 | EE |
| `effective_expected_exposure` | float | 0.0 | EEE |
| `peak_exposure` | float | 0.0 | Peak |
| `ee_profile` | ExposureProfile | None | EE profile |
| `pfe_profile` | ExposureProfile | None | PFE profile |
| `ead` | float | 0.0 | Exposure at Default |
| `eepe` | float | 0.0 | Effective EPE |
| `currency` | str | "USD" | Currency |
| `confidence_level` | float | 0.95 | Confidence level |
| `time_horizon` | float | 1.0 | Time horizon |
| `num_scenarios` | int | 10000 | Number of scenarios |

### SACCRResult (Dataclass)

SA-CCR calculation result per Basel III/IV.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `result_id` | str | Auto-generated | Unique identifier |
| `calculation_date` | datetime | now | Calculation timestamp |
| `netting_set_id` | str | "" | Netting set |
| `replacement_cost` | float | 0.0 | RC component |
| `potential_future_exposure` | float | 0.0 | PFE component |
| `ir_addon` | float | 0.0 | IR add-on |
| `fx_addon` | float | 0.0 | FX add-on |
| `credit_addon` | float | 0.0 | Credit add-on |
| `equity_addon` | float | 0.0 | Equity add-on |
| `commodity_addon` | float | 0.0 | Commodity add-on |
| `multiplier` | float | 1.0 | PFE multiplier |
| `ead` | float | 0.0 | Final EAD |
| `collateral_value` | float | 0.0 | Collateral |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `calculate_ead(alpha)` | float | Calculate EAD with alpha |

### NettingSetExposure (Dataclass)

Aggregated netting set exposure.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `netting_set_id` | str | "" | NS identifier |
| `counterparty_id` | str | "" | Counterparty |
| `num_trades` | int | 0 | Trade count |
| `gross_positive` | float | 0.0 | Gross positive MTM |
| `gross_negative` | float | 0.0 | Gross negative MTM |
| `net_exposure` | float | 0.0 | Net exposure |
| `collateral` | float | 0.0 | Posted collateral |
| `net_collateralized` | float | 0.0 | Net after collateral |
| `netting_benefit` | float | 0.0 | Netting benefit % |

## Usage Examples

```python
from models import (
    ExposureProfile, ExposureResult, ExposureMethod,
    SACCRResult, NettingSetExposure
)

# Create exposure profile
ee_profile = ExposureProfile(
    exposure_type=ExposureType.EXPECTED,
    time_grid=[0.0, 0.25, 0.5, 0.75, 1.0],
    values=[0, 1.2e6, 1.5e6, 1.3e6, 1.0e6],
    currency="USD"
)

# Get metrics
peak = ee_profile.peak()  # 1.5M
avg = ee_profile.time_weighted_average()

# Create exposure result
result = ExposureResult(
    reference_id="NS-001",
    reference_type="netting_set",
    method=ExposureMethod.MONTE_CARLO,
    current_exposure=1_000_000,
    expected_exposure=1_200_000,
    potential_future_exposure=2_500_000,
    ee_profile=ee_profile
)

# SA-CCR result
saccr = SACCRResult(
    netting_set_id="NS-001",
    replacement_cost=1_000_000,
    ir_addon=500_000,
    fx_addon=200_000,
    multiplier=0.85
)
ead = saccr.calculate_ead(alpha=1.4)
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
