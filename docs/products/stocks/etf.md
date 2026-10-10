# Exchange-Traded Fund (ETF) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Exchange-Traded Fund |
| **Product Class** | Equities - Funds |
| **Asset Class** | Equity |
| **Product Type** | ETF |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

ETFs are investment funds traded on stock exchanges that hold assets like stocks, bonds, or commodities. They combine diversification of mutual funds with intraday trading of stocks.

### ETF Types

| Type | Description | Examples |
|------|-------------|----------|
| Index | Track market indices | SPY, QQQ |
| Sector | Focus on industries | XLF, XLE |
| Leveraged | 2x or 3x returns | TQQQ, SOXL |
| Inverse | Short exposure | SH, SQQQ |
| Thematic | Specific themes | ARKK, BOTZ |

---

## SA-CCR Treatment

ETFs typically use index SF (20%) unless concentrated.

---

## Implementation Example

```python
from products.python.stocks import ETF

etf = ETF(
    trade_id="ETF-001",
    ticker="SPY",
    shares=5000,
    purchase_price=480.0,
    underlying_index="SPX",
    expense_ratio=0.0009,
    etf_type="index",
    leverage=1,
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
