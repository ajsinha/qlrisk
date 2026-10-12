# QLRisk - Models Documentation v2.4.0

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Overview

The Models module provides 55+ domain models for representing financial entities, market data, and calculation results in QLRisk.

---

## Model Categories

### Core Models

| Model | File | Description |
|-------|------|-------------|
| [Trade](trade.md) | `trade.py` | Trade representation with type and status |
| [Portfolio](portfolio.md) | `portfolio.py` | Portfolio aggregation and snapshots |
| [Counterparty](counterparty.md) | `counterparty.py` | Counterparty, NettingSet, CollateralAgreement |

### Market Data Models

| Model | File | Description |
|-------|------|-------------|
| [Curve](curve.md) | `curve.py` | YieldCurve, CreditCurve, VolatilitySurface |
| [MarketData](market_data.md) | `market_data.py` | MarketData, MarketDataSnapshot, Quote |

### Product Models

| Model | File | Description |
|-------|------|-------------|
| [Products](products.md) | `products.py` | 27 product type models |

### Risk Models

| Model | File | Description |
|-------|------|-------------|
| [Scenario](scenario.md) | `scenario.py` | Stress scenarios and Monte Carlo |
| [Exposure](exposure.md) | `exposure.py` | Exposure profiles and results |
| [Rating](rating.md) | `rating.py` | Credit ratings and transitions |

---

## Quick Reference

### Trade Model

```python
from datetime import date
from qlrisk.models import Trade, TradeType, TradeStatus

trade = Trade(
    trade_id="IRS-001",
    trade_type=TradeType.INTEREST_RATE_SWAP,
    counterparty_id="CP-001",
    notional=10_000_000,
    currency="USD",
    effective_date=date(2024, 1, 1),
    maturity_date=date(2029, 1, 1),
    status=TradeStatus.ACTIVE,
    mark_to_market=125_000,
)
print(trade.is_active(), trade.validate())
```

### Portfolio Model

```python
from qlrisk.models import Portfolio, PortfolioType

portfolio = Portfolio(portfolio_id="PF-001", name="Trading Book", portfolio_type=PortfolioType.TRADING,
                      owner_entity="Desk A")
portfolio.add_trade(trade)
print(portfolio.calculate_summary())
```

### Counterparty Model

```python
from qlrisk.models import Counterparty, NettingSet

counterparty = Counterparty(counterparty_id="CP-001", name="ABC Corp", probability_of_default=0.02,
                            loss_given_default=0.45, country="US", sector="Industrials")
netting_set = NettingSet(netting_set_id="NS-001", counterparty_id="CP-001", trade_ids=["IRS-001", "FX-001"])
print(counterparty.name, netting_set.trade_ids)
```

### Curve Models

```python
from datetime import date
from qlrisk.models import YieldCurve, CreditCurve

yield_curve = YieldCurve(curve_id="USD-SOFR", currency="USD", curve_date=date.today(),
                         tenors=[0.25, 0.5, 1, 2, 5, 10], values=[0.03, 0.032, 0.035, 0.038, 0.042, 0.045])
print(yield_curve.discount_factor(2.0), yield_curve.forward_rate(1.0, 2.0))

credit_curve = CreditCurve(curve_id="ABC-CDS", currency="USD", curve_date=date.today(),
                           tenors=[1, 3, 5], values=[0.010, 0.012, 0.015], recovery_rate=0.4)
print(credit_curve.survival_probability(5.0))
```

### Scenario Models

```python
from qlrisk.models import Scenario, ScenarioType, CurveShock, RiskFactorShock

scenario = Scenario(scenario_id="STRESS-001", name="2008 Crisis", scenario_type=ScenarioType.HISTORICAL)
scenario.add_ir_shock("USD", CurveShock(curve_name="USD", parallel_shift=-200))           # bp
scenario.add_credit_shock("ABC Corp", RiskFactorShock(risk_factor="credit_spread", shock_value=300, shock_unit="bp"))
print(scenario.get_shock_summary())
# To reprice a portfolio under scenarios, use qlrisk.scenarios (ScenarioSet, historical_stress_scenarios)
```

### Exposure Models

```python
from qlrisk.models import ExposureProfile

profile = ExposureProfile(profile_id="EP-001", time_grid=[0.25, 0.5, 1.0, 2.0, 5.0],
                          values=[100, 150, 200, 180, 100], currency="USD")
print(profile.peak(), profile.average())
```

---

## Model Hierarchy

```
Base
├── Trade
│   ├── TradeType (Enum)
│   └── TradeStatus (Enum)
├── Portfolio
│   ├── PortfolioType (Enum)
│   ├── PortfolioSummary
│   └── PortfolioSnapshot
├── Counterparty
│   ├── NettingSet
│   └── CollateralAgreement
├── Curve
│   ├── YieldCurve
│   ├── CreditCurve
│   └── VolatilitySurface
├── MarketData
│   ├── MarketDataSnapshot
│   └── Quote
├── Product (27 types)
├── Scenario
│   ├── ScenarioType (Enum)
│   ├── ShockType (Enum)
│   ├── RiskFactorShock
│   └── MonteCarloScenarioSet
├── Exposure
│   ├── ExposureProfile
│   ├── ExposureResult
│   ├── SACCRResult
│   └── NettingSetExposure
└── Rating
    ├── CreditRating
    ├── RatingHistory
    └── TransitionMatrix
```

---

## Factory Pattern

```python
from qlrisk.models import ModelFactory, TradeType

# class-level factory methods (no instance needed)
trade = ModelFactory.create_trade(TradeType.INTEREST_RATE_SWAP, counterparty_id="CP-001", notional=10e6)
curve = ModelFactory.create_yield_curve("USD", tenors=[1, 2, 5, 10], rates=[0.04, 0.041, 0.043, 0.045])
counterparty = ModelFactory.create_counterparty(name="ABC Corp")
print(trade.trade_type, curve.zero_rate(3.0), counterparty.name)
```

---

## See Also

- [Architecture](../architecture.md) - System design
- [Products](../products/README.md) - Product documentation
- [Calculators](../calculators/README.md) - Calculator documentation

---

*Document Version: 2.4.0*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
