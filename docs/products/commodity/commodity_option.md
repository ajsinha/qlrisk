# Commodity Option v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Commodity Option |
| **Product Class** | Commodity Derivatives |
| **Asset Class** | Commodity |
| **Product Type** | COMMODITY_OPTION |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Options on commodity prices, typically using Black model for pricing.

---

## Implementation Example

```python
from products.python.commodity import CommodityOption

opt = CommodityOption(
    trade_id="COMOPT-001",
    commodity="Gold",
    strike=2000.0,
    option_type=OptionType.CALL,
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
