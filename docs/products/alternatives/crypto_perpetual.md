# Cryptocurrency Perpetual Swap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Cryptocurrency Perpetual |
| **Product Class** | Digital Assets - Derivatives |
| **Asset Class** | Alternative |
| **Product Type** | CRYPTO_PERPETUAL |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Perpetual futures with no expiry date, kept in line with spot through funding rate mechanism. Very popular on crypto exchanges.

### Key Characteristics

- **No Expiry:** Rolls indefinitely
- **Funding Rate:** Periodic payment between longs/shorts
- **High Leverage:** Up to 100x on some exchanges
- **Mark Price:** Used for liquidation

---

## Funding Rate

$$Funding = Position \times Mark Price \times Funding Rate$$

Typically paid every 8 hours.

---

## Implementation Example

```python
from products.python.alternatives import CryptoPerpetual

perp = CryptoPerpetual(
    trade_id="PERP-001",
    symbol="ETH",
    position_size=100.0,  # 100 ETH
    entry_price=3500.0,
    leverage=10,
    funding_rate=0.0001,  # 0.01% per 8h
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
