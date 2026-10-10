# Carbon Credit v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Carbon Credit |
| **Product Class** | Environmental |
| **Asset Class** | Alternative |
| **Product Type** | CARBON_CREDIT |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Carbon credits represent the right to emit one metric ton of CO2. Traded in compliance markets (EU ETS, California) and voluntary markets.

### Markets

| Market | Description |
|--------|-------------|
| EU ETS | European Emission Trading System |
| California Cap-and-Trade | US state system |
| RGGI | Regional Greenhouse Gas Initiative |
| Voluntary | Offset programs |

---

## Implementation Example

```python
from products.python.alternatives import CarbonCredit

carbon = CarbonCredit(
    trade_id="CARBON-001",
    market="EU_ETS",
    vintage=2024,
    quantity=10000,  # tonnes CO2
    purchase_price=85.0,  # EUR per tonne
    currency=Currency.EUR,
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
