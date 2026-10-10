# Private Equity Interest

<!-- generated:implementation -->
> **Implementation:** `PrivateEquityInterest` is priced by `price_cash_equity` in `products/python/_pricing.py`. Product terms are keyword arguments: `ticker` (equity_prices key), `quantity` (default notional / price), `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->
## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Private Equity Interest |
| **Product Class** | Private Markets |
| **Asset Class** | Alternative |
| **Product Type** | PE_INTEREST |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Limited Partner (LP) interest in a private equity fund. Illiquid, long-term investment with capital calls and distributions.

### Key Characteristics

- **Fund Life:** 10-12 years typical
- **J-Curve:** Initial losses, later gains
- **Capital Calls:** Drawdown over 3-5 years
- **Distributions:** Returned capital + profits
- **Carried Interest:** GP profit share (typically 20%)

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| IRR | Internal Rate of Return |
| TVPI | Total Value to Paid-In |
| DPI | Distributions to Paid-In |
| RVPI | Residual Value to Paid-In |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import PrivateEquityInterest
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = PrivateEquityInterest("PRIVATE-EQUITY-INTEREST-1", md.valuation_date, md.valuation_date, date(2099, 10, 9), 5_000_000, Currency.USD, "CP-1", ticker="AAPL")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
