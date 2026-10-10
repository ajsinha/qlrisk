# Cryptocurrency Spot v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Cryptocurrency Spot |
| **Product Class** | Digital Assets |
| **Asset Class** | Alternative |
| **Product Type** | CRYPTO_SPOT |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Direct ownership of cryptocurrencies like Bitcoin (BTC), Ethereum (ETH), and other digital assets. Highly volatile with 24/7 trading.

### Key Characteristics

- **24/7 Trading:** No market close
- **High Volatility:** 60-100% annual vol typical
- **Custody:** Self or exchange custody
- **Settlement:** T+0 (blockchain confirmation)

---

## Volatility Characteristics

| Asset | Typical Annual Vol |
|-------|-------------------|
| BTC | 60-80% |
| ETH | 70-100% |
| Altcoins | 100-200% |

---

## SA-CCR Treatment

No specific SA-CCR treatment; typically use equity SF (32%) or higher.

---

## Implementation Example

```python
from datetime import date
from products.python.alternatives import CryptoSpot
from products.base import Currency, MarketData

btc = CryptoSpot(
    trade_id="CRYPTO-001",
    trade_date=date(2024, 1, 15),
    symbol="BTC",
    quantity=10.0,
    purchase_price=42000.0,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    exchange="Coinbase",
    is_long=True
)

market_data.forward_curves["BTC"] = {"spot": 67000.0}
result = btc.price(market_data)
print(f"Market Value: ${result.npv:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
