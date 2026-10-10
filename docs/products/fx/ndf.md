# Non-Deliverable Forward (NDF) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Non-Deliverable Forward (NDF) |
| **Product Class** | Foreign Exchange |
| **Asset Class** | FX |
| **Product Type** | NDF |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Non-Deliverable Forward is a cash-settled FX forward used for currencies with capital controls or limited convertibility. Settlement is in a freely traded currency (usually USD) based on the difference between contracted and fixing rates.

### Common NDF Currencies

| Currency | Country |
|----------|---------|
| CNY | China |
| INR | India |
| KRW | South Korea |
| TWD | Taiwan |
| BRL | Brazil |

---

## Mathematical Framework

### Settlement Amount

$$Settlement = N \times \left(\frac{1}{F_{fix}} - \frac{1}{F_{contract}}\right)$$

Or equivalently:

$$Settlement = N \times \frac{F_{contract} - F_{fix}}{F_{fix}}$$

---

## Implementation Example

```python
from datetime import date
from products.python.fx import NonDeliverableForward
from products.base import Currency, MarketData

ndf = NonDeliverableForward(
    trade_id="NDF-001",
    trade_date=date(2024, 1, 15),
    fixing_date=date(2024, 7, 13),
    settlement_date=date(2024, 7, 17),
    base_currency=Currency.USD,
    non_deliverable_currency="CNY",
    notional=10000000,
    forward_rate=7.25,
    settlement_currency=Currency.USD,
    counterparty_id="CPY-001",
    is_buy_base=True
)

result = ndf.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
