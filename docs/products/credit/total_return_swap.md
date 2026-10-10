# Total Return Swap (TRS) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Total Return Swap (TRS) |
| **Product Class** | Credit Derivatives |
| **Asset Class** | Credit |
| **Product Type** | TRS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Total Return Swap transfers the total economic performance of a reference asset (price changes plus income) to the receiver in exchange for a funding rate. It provides synthetic exposure without ownership.

### Key Characteristics

- **Total Return Leg:** Price appreciation + coupons/dividends
- **Funding Leg:** Reference rate + spread
- **No Initial Exchange:** Synthetic ownership
- **Uses:** Leverage, balance sheet management

---

## Mathematical Framework

### Total Return

$$TR = \Delta P + Coupons/Dividends$$

### TRS Spread

Fair spread $s$ satisfies:

$$E[TR] = (r + s) \times N \times T$$

---

## Implementation Example

```python
from datetime import date
from products.python.credit import TotalReturnSwap
from products.base import Currency, MarketData

trs = TotalReturnSwap(
    trade_id="TRS-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 1, 17),
    maturity_date=date(2025, 1, 17),
    notional=25000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    reference_asset="XYZ Corp 5% 2030",
    funding_spread=0.0025,  # 25 bps over SOFR
    is_total_return_receiver=True
)

result = trs.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
