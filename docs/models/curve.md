# Curve Model Documentation v1.2.0

## Overview

The Curve module provides models for yield curves, credit curves, and volatility surfaces used in pricing and risk calculations.

## Classes

### CurveType (Enum)

Types of market curves.

| Value | Description |
|-------|-------------|
| `YIELD` | Interest rate yield curve |
| `DISCOUNT` | Discount factor curve |
| `FORWARD` | Forward rate curve |
| `CREDIT` | Credit spread curve |
| `HAZARD` | Hazard rate curve |
| `VOLATILITY` | Volatility curve/surface |

### Curve (Dataclass)

Base curve representation.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `curve_id` | str | Auto-generated | Unique identifier |
| `curve_type` | CurveType | YIELD | Type of curve |
| `currency` | str | "USD" | Curve currency |
| `reference_date` | date | today | Valuation date |
| `tenors` | List[float] | [] | Tenor points (years) |
| `values` | List[float] | [] | Curve values |
| `interpolation` | str | "linear" | Interpolation method |
| `day_count` | str | "ACT/365" | Day count convention |

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
| `index_name` | str | "SOFR" | Reference index |
| `compounding` | str | "continuous" | Compounding method |
| `spot_rates` | List[float] | [] | Spot rates |
| `forward_rates` | List[float] | [] | Forward rates |
| `discount_factors` | List[float] | [] | Discount factors |

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
| `entity_id` | str | "" | Reference entity |
| `seniority` | str | "SENIOR" | Debt seniority |
| `recovery_rate` | float | 0.40 | Recovery assumption |
| `spreads` | List[float] | [] | Credit spreads |
| `hazard_rates` | List[float] | [] | Hazard rates |
| `survival_probs` | List[float] | [] | Survival probabilities |

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
| `underlying` | str | "" | Underlying asset |
| `surface_type` | str | "implied" | Vol type |
| `strikes` | List[float] | [] | Strike levels |
| `expiries` | List[float] | [] | Expiry times |
| `volatilities` | List[List[float]] | [] | Vol matrix |
| `atm_vols` | List[float] | [] | ATM volatilities |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_vol(strike, expiry)` | float | Interpolated vol |
| `get_atm_vol(expiry)` | float | ATM vol at expiry |

## Usage Examples

```python
from models import YieldCurve, CreditCurve, VolatilitySurface
from datetime import date

# Create yield curve
yield_curve = YieldCurve(
    currency="USD",
    index_name="SOFR",
    reference_date=date.today(),
    tenors=[0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    spot_rates=[0.045, 0.046, 0.047, 0.048, 0.05, 0.052, 0.055]
)

# Get interpolated rate
rate_3y = yield_curve.get_spot_rate(3.0)
df_5y = yield_curve.get_discount_factor(5.0)

# Create credit curve
credit_curve = CreditCurve(
    entity_id="CORP-001",
    recovery_rate=0.40,
    tenors=[1.0, 3.0, 5.0, 7.0, 10.0],
    spreads=[0.005, 0.008, 0.012, 0.015, 0.018]
)

# Get survival probability
surv_5y = credit_curve.get_survival_prob(5.0)
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
