# Cryptocurrency Future v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Cryptocurrency Future |
| **Product Class** | Digital Assets - Derivatives |
| **Asset Class** | Alternative |
| **Product Type** | CRYPTO_FUTURE |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Futures contracts on cryptocurrencies traded on regulated exchanges (CME) or crypto-native exchanges.

### Key Characteristics

- **CME Bitcoin Futures:** 5 BTC per contract
- **CME Micro Bitcoin:** 0.1 BTC per contract
- **Cash Settled:** No physical delivery
- **Margin:** Initial and maintenance margin

---

## Implementation Example

```python
from products.python.alternatives import CryptoFuture

btc_fut = CryptoFuture(
    trade_id="BTCFUT-001",
    symbol="BTC",
    contracts=10,
    contract_size=5.0,  # 5 BTC per contract
    entry_price=65000.0,
    expiry_date=date(2024, 6, 28),
    exchange="CME",
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
