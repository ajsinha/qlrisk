# Commodity Futures

## Overview

Commodity futures are standardized exchange-traded contracts obligating the buyer to purchase (or seller to sell) a specific quantity of a commodity at a predetermined price on a specified future date.

## QLRisk - Commodity Futures v2.3.0

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
```

---

## Supported Commodity Types

### Energy Commodities
| Type | Code | Supervisory Factor | Typical Volatility |
|------|------|-------------------|-------------------|
| Crude Oil (WTI) | `CRUDE_OIL_WTI` | 18% | 35% |
| Crude Oil (Brent) | `CRUDE_OIL_BRENT` | 18% | 35% |
| Natural Gas | `NATURAL_GAS` | 18% | 50% |
| Heating Oil | `HEATING_OIL` | 18% | 35% |
| RBOB Gasoline | `RBOB_GASOLINE` | 18% | 40% |
| Coal | `COAL` | 18% | 30% |
| Electricity | `ELECTRICITY` | **40%** | 80% |

### Precious Metals
| Type | Code | Supervisory Factor | Typical Volatility |
|------|------|-------------------|-------------------|
| Gold | `GOLD` | 18% | 15% |
| Silver | `SILVER` | 18% | 25% |
| Platinum | `PLATINUM` | 18% | 25% |
| Palladium | `PALLADIUM` | 18% | 30% |

### Base Metals
| Type | Code | Supervisory Factor | Typical Volatility |
|------|------|-------------------|-------------------|
| Copper | `COPPER` | 18% | 25% |
| Aluminum | `ALUMINUM` | 18% | 20% |
| Zinc | `ZINC` | 18% | 25% |
| Nickel | `NICKEL` | 18% | 30% |
| Lead | `LEAD` | 18% | 25% |
| Tin | `TIN` | 18% | 25% |

### Agriculture - Grains
| Type | Code | Supervisory Factor | Typical Volatility |
|------|------|-------------------|-------------------|
| Corn | `CORN` | 18% | 25% |
| Wheat | `WHEAT` | 18% | 30% |
| Soybeans | `SOYBEANS` | 18% | 25% |
| Soybean Oil | `SOYBEAN_OIL` | 18% | 25% |
| Soybean Meal | `SOYBEAN_MEAL` | 18% | 25% |
| Oats | `OATS` | 18% | 30% |
| Rice | `RICE` | 18% | 25% |

### Agriculture - Softs
| Type | Code | Supervisory Factor | Typical Volatility |
|------|------|-------------------|-------------------|
| Coffee | `COFFEE` | 18% | 35% |
| Sugar | `SUGAR` | 18% | 30% |
| Cocoa | `COCOA` | 18% | 30% |
| Cotton | `COTTON` | 18% | 30% |
| Orange Juice | `ORANGE_JUICE` | 18% | 35% |
| Lumber | `LUMBER` | 18% | 40% |

### Livestock
| Type | Code | Supervisory Factor | Typical Volatility |
|------|------|-------------------|-------------------|
| Live Cattle | `LIVE_CATTLE` | 18% | 15% |
| Lean Hogs | `LEAN_HOGS` | 18% | 25% |
| Feeder Cattle | `FEEDER_CATTLE` | 18% | 15% |

---

## SA-CCR Treatment

### Asset Class
Commodity futures are treated as **Commodity** asset class under SA-CCR.

### Hedging Sets
Commodities are divided into sub-classes for hedging set aggregation:
- **Energy**: Oil, Gas, Coal, Electricity
- **Precious Metals**: Gold, Silver, Platinum, Palladium
- **Base Metals**: Copper, Aluminum, Zinc, Nickel, Lead, Tin
- **Agriculture**: Grains and Softs
- **Livestock**: Cattle and Hogs

### Supervisory Factors
- **Electricity**: 40% (highest volatility)
- **All Other Commodities**: 18%

### Adjusted Notional
For commodity futures:
```
Adjusted Notional = Quantity × Spot Price × Delta
```

Where Delta = +1 for long, -1 for short positions.

---

## Usage Examples

### Creating a WTI Crude Oil Future

```python
from datetime import date
from qlrisk.products.python.futures import (
    CommodityFuture, 
    CommodityType, 
    CommodityFutureTerms
)
from qlrisk.products.base import Currency

# Create WTI crude oil future
future = CommodityFuture(
    trade_id="WTI-FUT-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2027, 6, 30),
    notional=750_000,  # 10 contracts × 1000 barrels × $75
    currency=Currency.USD,
    counterparty_id="CME",
    terms=CommodityFutureTerms(
        commodity_type=CommodityType.CRUDE_OIL_WTI,
        contract_size=1000,  # 1000 barrels per contract
        num_contracts=10,
        futures_price=75.00,
        spot_price=74.50,
        exchange="NYMEX",
        contract_month="M25",  # June 2025
        settlement_type="physical"
    ),
    is_long=True
)
```

### Creating a Gold Future

```python
gold_future = CommodityFuture(
    trade_id="GOLD-FUT-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2027, 8, 31),
    notional=1_950_000,  # 10 contracts × 100 oz × $1950
    currency=Currency.USD,
    counterparty_id="CME",
    terms=CommodityFutureTerms(
        commodity_type=CommodityType.GOLD,
        contract_size=100,  # 100 troy oz per contract
        num_contracts=10,
        futures_price=1950.00,
        spot_price=1945.00,
        exchange="COMEX",
        contract_month="Q25"  # Aug 2025
    ),
    is_long=True
)
```

### Pricing and Exposure Calculation

```python
from qlrisk.products.base import MarketData

# Create market data
market_data = MarketData(
    valuation_date=date.today(),
    discount_curve={0.25: 0.05, 0.5: 0.051, 1.0: 0.052}
)

# Price the future
result = future.price(market_data)
print(f"NPV: ${result.npv:,.2f}")
print(f"Delta: {result.greeks['delta']:,.0f} barrels")

# Calculate CCR exposure
exposure = future.calculate_ccr_exposure(
    market_data,
    time_horizon=1.0,
    confidence_level=0.95
)
print(f"EPE: ${exposure.epe:,.2f}")
print(f"Peak Exposure: ${exposure.peak_exposure:,.2f}")

# Calculate SA-CCR EAD
saccr = future.calculate_saccr(market_data)
print(f"EAD: ${saccr.ead:,.2f}")
print(f"Supervisory Factor: {saccr.metadata['supervisory_factor']:.0%}")
```

---

## Pricing Model

### Cost of Carry Formula

```
F = S × exp((r + u - y) × T)
```

Where:
- `F` = Futures price
- `S` = Spot price
- `r` = Risk-free rate
- `u` = Storage cost rate (annual)
- `y` = Convenience yield (annual)
- `T` = Time to maturity (years)

### P&L Calculation

```
NPV = (F_market - F_contract) × Quantity × Direction × DF
```

Where:
- `F_market` = Current futures market price
- `F_contract` = Contracted futures price
- `Quantity` = Contract size × Number of contracts
- `Direction` = +1 for long, -1 for short
- `DF` = Discount factor

---

## CCR Exposure Calculation

### Exposure Profile
The exposure profile is generated using Monte Carlo simulation with GBM dynamics:

```
dS = μ × S × dt + σ × S × dW
```

Where σ is the commodity-specific volatility.

### Key Metrics
| Metric | Description |
|--------|-------------|
| Current Exposure | max(0, NPV) |
| Expected Exposure | E[max(0, NPV_t)] |
| PFE | 95th percentile of positive exposure |
| Peak Exposure | Maximum PFE over time horizon |

---

## See Also

- [SA-CCR Documentation](../saccr.md)
- [Futures Products Overview](../products/README.md)
- [Mathematical Formulas](../mathematical_formulas.md)

---

*QLRisk v2.3.0*
