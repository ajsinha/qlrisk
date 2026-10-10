# Index Future v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Index Future |
| **Product Class** | Futures |
| **Asset Class** | Equity |
| **Product Type** | INDEX_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures contracts on equity indices providing leveraged exposure to broad market movements. Most liquid derivative instruments globally.

### Major Index Futures

| Contract | Index | Multiplier | Exchange |
|----------|-------|------------|----------|
| ES | S&P 500 | $50 | CME |
| NQ | NASDAQ-100 | $20 | CME |
| YM | Dow Jones | $5 | CBOT |
| RTY | Russell 2000 | $50 | CME |
| FESX | Euro Stoxx 50 | €10 | Eurex |
| NKD | Nikkei 225 | $5 | CME |

---

## Mathematical Framework

### Fair Value

$$F = S \times e^{(r - q) \times T}$$

### Basis

$$Basis = F - S$$

### Cost of Carry

$$COC = S \times (r - q) \times T$$

---

## SA-CCR Treatment

Index futures use equity SF:

$$AddOn = 20\% \times Delta \times Notional \times MF$$

---

## Implementation Example

```python
from datetime import date
from products.python.futures import IndexFuture
from products.base import Currency, MarketData

es = IndexFuture(
    trade_id="ES-001",
    trade_date=date(2024, 1, 15),
    underlying_index="SPX",
    contracts=10,
    contract_multiplier=50.0,
    entry_price=4850.0,
    expiry_date=date(2024, 3, 15),
    currency=Currency.USD,
    counterparty_id="CPY-001",
    is_long=True
)

market_data.forward_curves["SPX"] = {"spot": 4900.0}
result = es.price(market_data)
print(f"Notional: ${es.contracts * es.contract_multiplier * es.entry_price:,.0f}")
print(f"P&L: ${result.npv:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
