# Common Stock v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Common Stock |
| **Product Class** | Equities |
| **Asset Class** | Equity |
| **Product Type** | COMMON_STOCK |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Common stock represents ownership shares in a corporation with voting rights and residual claim on assets. Holders receive dividends (if declared) and benefit from capital appreciation.

### Key Characteristics

- **Voting Rights:** Typically 1 vote per share
- **Dividends:** Variable, at board discretion
- **Residual Claim:** Last in liquidation priority
- **Limited Liability:** Loss limited to investment

---

## Market Cap Categories

| Category | Market Cap | Typical Volatility |
|----------|------------|-------------------|
| Large Cap | >$10B | 15-20% |
| Mid Cap | $2B-$10B | 20-25% |
| Small Cap | $300M-$2B | 25-35% |
| Micro Cap | <$300M | 35-50% |

---

## SA-CCR Treatment

| Type | Supervisory Factor |
|------|-------------------|
| Single Stock | 32% |
| Index | 20% |

---

## Implementation Example

```python
from datetime import date
from products.python.stocks import CommonStock
from products.base import Currency, MarketData

stock = CommonStock(
    trade_id="STK-001",
    trade_date=date(2024, 1, 15),
    ticker="AAPL",
    shares=10000,
    purchase_price=185.0,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    market_cap_category="large",
    sector="technology",
    is_long=True
)

market_data = MarketData(
    valuation_date=date(2024, 6, 15),
    forward_curves={"AAPL": {"spot": 195.0, "div_yield": 0.005}}
)

result = stock.price(market_data)
print(f"Market Value: ${result.npv:,.2f}")
print(f"P&L: ${result.components['pnl']:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
