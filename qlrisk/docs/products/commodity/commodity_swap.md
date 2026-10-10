# Commodity Swap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Commodity Swap |
| **Product Class** | Commodity Derivatives |
| **Asset Class** | Commodity |
| **Product Type** | COMMODITY_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Commodity Swap exchanges a fixed price for a floating commodity price. Used by producers and consumers to hedge commodity price risk.

### Commodity Types

| Category | Examples |
|----------|----------|
| Energy | Crude oil, natural gas, electricity |
| Metals | Gold, copper, aluminum |
| Agriculture | Corn, wheat, soybeans |

---

## SA-CCR Treatment

| Commodity | SF |
|-----------|-----|
| Electricity | 40% |
| Oil/Gas | 18% |
| Metals | 18% |
| Agriculture | 18% |

---

## Implementation Example

```python
from products.python.commodity import CommoditySwap

swap = CommoditySwap(
    trade_id="COMSWP-001",
    commodity="WTI",
    fixed_price=75.0,
    notional_quantity=100000,  # barrels
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
