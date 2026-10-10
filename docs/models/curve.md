# Curve Model Documentation v1.2.0

## Overview

The Curve module provides models for yield curves, credit curves, and volatility surfaces used in pricing and risk calculations.

## Classes

### CurveType (Enum)

Types of market curves.

| Value | Name | Description |
|-------|------|-------------|
| `yield` | `YIELD` | Interest rate yield curve |
| `discount` | `DISCOUNT` | Discount factor curve |
| `zero` | `ZERO` |  |
| `forward` | `FORWARD` | Forward rate curve |
| `credit` | `CREDIT` | Credit spread curve |
| `hazard` | `HAZARD` | Hazard rate curve |
| `volatility` | `VOLATILITY` | Volatility curve/surface |

### Curve (Dataclass)

Base curve representation.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `curve_id` | str | '' | Unique identifier |
| `curve_type` | CurveType | CurveType.YIELD | Type of curve |
| `currency` | str | 'USD' | Curve currency |
| `curve_date` | date | today() |  |
| `tenors` | List | list() | Tenor points (years) |
| `values` | List | list() | Curve values |
| `interpolation` | InterpolationMethod | InterpolationMethod.LOG_LINEAR | Interpolation method |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_value(tenor)` | float | Interpolated value |
| `get_discount_factor(t)` | float | DF at time t |
| `get_forward_rate(t1, t2)` | float | Forward rate |
| `shift(bps)` | Curve | Parallel shifted curve |
| `validate()` | bool | Validate curve |

### YieldCurve (Dataclass)

Interest rate yield curve.

#### Additional Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `curve_id` | str | '' |  |
| `curve_type` | CurveType | CurveType.YIELD |  |
| `currency` | str | 'USD' |  |
| `curve_date` | date | today() |  |
| `tenors` | List | list() |  |
| `values` | List | list() |  |
| `interpolation` | InterpolationMethod | InterpolationMethod.LOG_LINEAR |  |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_spot_rate(t)` | float | Spot rate at t |
| `get_forward_rate(t1, t2)` | float | Forward rate |
| `get_discount_factor(t)` | float | Discount factor |
| `bootstrap(instruments)` | None | Bootstrap curve |

### CreditCurve (Dataclass)

Credit spread/hazard rate curve.

#### Additional Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `curve_id` | str | '' |  |
| `curve_type` | CurveType | CurveType.HAZARD |  |
| `currency` | str | 'USD' |  |
| `curve_date` | date | today() |  |
| `tenors` | List | list() |  |
| `values` | List | list() |  |
| `interpolation` | InterpolationMethod | InterpolationMethod.LOG_LINEAR |  |
| `recovery_rate` | float | 0.4 | Recovery assumption |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_spread(t)` | float | Spread at t |
| `get_hazard_rate(t)` | float | Hazard rate at t |
| `get_survival_prob(t)` | float | Survival probability |
| `get_default_prob(t)` | float | Cumulative default prob |

### VolatilitySurface (Dataclass)

Volatility surface for options.

#### Additional Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `surface_id` | str | '' |  |
| `underlying` | str | '' | Underlying asset |
| `currency` | str | 'USD' |  |
| `surface_date` | date | today() |  |
| `expiries` | List | list() | Expiry times |
| `strikes` | List | list() | Strike levels |
| `volatilities` | List | list() | Vol matrix |
| `atm_tenors` | List | list() |  |
| `atm_vols` | List | list() | ATM volatilities |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_vol(strike, expiry)` | float | Interpolated vol |
| `get_atm_vol(expiry)` | float | ATM vol at expiry |

## Usage Examples

```python
from datetime import date
from qlrisk.models import YieldCurve, CreditCurve, VolatilitySurface

yield_curve = YieldCurve(curve_id="USD-SOFR", currency="USD", curve_date=date.today(),
                         tenors=[0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
                         values=[0.045, 0.046, 0.047, 0.048, 0.05, 0.052, 0.055])
print("3y zero rate", yield_curve.zero_rate(3.0), "DF(5y)", yield_curve.discount_factor(5.0),
      "1y-2y fwd", yield_curve.forward_rate(1.0, 2.0))

credit_curve = CreditCurve(curve_id="ACME-CDS", currency="USD", curve_date=date.today(),
                           tenors=[1.0, 3.0, 5.0], values=[0.010, 0.012, 0.015], recovery_rate=0.4)
print("5y survival", credit_curve.survival_probability(5.0), "5y PD", credit_curve.default_probability(5.0))

surface = VolatilitySurface(surface_id="SPX-VOL", underlying="SPX", currency="USD", surface_date=date.today(),
                            expiries=[0.5, 1.0], strikes=[90.0, 100.0, 110.0],
                            volatilities=[[0.24, 0.20, 0.18], [0.23, 0.20, 0.185]])
print("vol(0.75y, 100)", surface.get_volatility(0.75, 100.0))
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
