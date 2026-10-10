# QLRisk - Models Documentation v1.3.0

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
from qlrisk.models import Trade, TradeType, TradeStatus

trade = Trade(
    trade_id='IRS-001',
    trade_type=TradeType.IRS,
    counterparty_id='CP-001',
    notional=10_000_000,
    currency='USD',
    effective_date=date(2024, 1, 1),
    maturity_date=date(2029, 1, 1),
    status=TradeStatus.ACTIVE
)
```

### Portfolio Model

```python
from qlrisk.models import Portfolio

portfolio = Portfolio(
    portfolio_id='PF-001',
    name='Trading Book',
    owner='Desk A'
)
portfolio.add_trade(trade)
summary = portfolio.get_summary()
```

### Counterparty Model

```python
from qlrisk.models import Counterparty, NettingSet

counterparty = Counterparty(
    counterparty_id='CP-001',
    name='ABC Corp',
    rating='BBB',
    pd=0.02,
    lgd=0.45
)

netting_set = NettingSet(
    netting_set_id='NS-001',
    counterparty_id='CP-001',
    trades=['IRS-001', 'FX-001']
)
```

### Curve Models

```python
from qlrisk.models import YieldCurve, CreditCurve

yield_curve = YieldCurve(
    curve_id='USD-SOFR',
    currency='USD',
    reference_date=date.today(),
    tenors=[0.25, 0.5, 1, 2, 5, 10],
    rates=[0.03, 0.032, 0.035, 0.038, 0.042, 0.045]
)

df = yield_curve.discount_factor(2.0)
fwd = yield_curve.forward_rate(1.0, 2.0)
```

### Scenario Models

```python
from qlrisk.models import Scenario, ScenarioType

scenario = Scenario(
    scenario_id='STRESS-001',
    name='2008 Crisis',
    scenario_type=ScenarioType.HISTORICAL,
    shocks={
        'equity': -0.40,
        'credit_spread': 0.03,
        'volatility': 1.5,
        'rates': -0.02
    }
)
```

### Exposure Models

```python
from qlrisk.models import ExposureProfile, ExposureResult

profile = ExposureProfile(
    profile_id='EP-001',
    time_grid=[0.25, 0.5, 1.0, 2.0, 5.0],
    expected_exposure=[100, 150, 200, 180, 100],
    pfe_95=[180, 250, 350, 300, 180],
    pfe_99=[220, 300, 420, 360, 220]
)

epe = profile.effective_epe()
peak = profile.peak_exposure()
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
from qlrisk.models import ModelFactory

factory = ModelFactory.get_instance()

# Create models via factory
trade = factory.create_trade('IRS', {...})
curve = factory.create_curve('yield', {...})
scenario = factory.create_scenario('historical', {...})
```

---

## See Also

- [Architecture](../architecture.md) - System design
- [Products](../products/README.md) - Product documentation
- [Calculators](../calculators/README.md) - Calculator documentation

---

*Document Version: 1.3.0*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
