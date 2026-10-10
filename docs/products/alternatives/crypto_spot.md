# Cryptocurrency Spot

<!-- generated:implementation -->
> **Implementation:** `CryptoSpot` is priced by `price_cash_equity` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker` (equity_prices key), `quantity` (default notional / price), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

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
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CryptoSpot
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
md.equity_prices["AAPL"] = 190.0
trade = CryptoSpot("CRYPTO-SPOT-1", md.valuation_date, md.valuation_date, date(2099, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
