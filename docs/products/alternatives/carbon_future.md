# Carbon Future v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Carbon Future |
| **Product Class** | Environmental - Derivatives |
| **Asset Class** | Alternative |
| **Product Type** | CARBON_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures contracts on carbon emission allowances, primarily traded on ICE.

---

## Implementation Example

```python
from products.python.alternatives import CarbonFuture

carbon_fut = CarbonFuture(
    trade_id="CARBFUT-001",
    market="EU_ETS",
    contracts=100,
    contract_size=1000,  # 1000 tonnes per contract
    entry_price=90.0,
    expiry_date=date(2024, 12, 15),
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
