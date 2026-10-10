# CDS Index v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | CDS Index |
| **Product Class** | Credit Derivatives |
| **Asset Class** | Credit |
| **Product Type** | CDS_INDEX |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A CDS Index provides protection on a portfolio of reference entities. Major indices include CDX (North America), iTraxx (Europe), and regional variants.

### Major Indices

| Index | Region | Components |
|-------|--------|------------|
| CDX.NA.IG | North America | 125 IG names |
| CDX.NA.HY | North America | 100 HY names |
| iTraxx Europe | Europe | 125 IG names |
| iTraxx Crossover | Europe | 75 HY names |

---

## Mathematical Framework

### Index Spread

$$s_{index} = \sum_{i=1}^{n} w_i \times s_i$$

### Index Price

Quoted as price (e.g., 100.25):

$$Price = 100 + Duration \times (s_{index} - s_{coupon})$$

---

## SA-CCR Treatment

Index CDS use separate supervisory factors:

| Index Type | SF |
|------------|-----|
| IG Index | 0.38% |
| HY/SG Index | 1.06% |

---

## Implementation Example

```python
from datetime import date
from products.python.credit import CDSIndex
from products.base import Currency, MarketData

cdx = CDSIndex(
    trade_id="CDX-001",
    trade_date=date(2024, 1, 15),
    effective_date=date(2024, 3, 20),
    maturity_date=date(2029, 6, 20),
    notional=50000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    index_name="CDX.NA.IG",
    series=42,
    coupon=0.01,  # 100 bps running
    is_protection_buyer=True
)

result = cdx.price(market_data)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
