# Repo (Repurchase Agreement) v1.2.0

<!-- generated:implementation -->
> **Implementation:** `Repo` is priced by `price_deposit` in `products/python/_pricing.py`. Product terms are keyword arguments: `rate`, `issuer`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Repurchase Agreement (Repo) |
| **Product Class** | Securities Financing |
| **Asset Class** | Repo |
| **Product Type** | REPO |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Repo is a sale of securities with an agreement to repurchase at a higher price. It's effectively a collateralized loan where the securities serve as collateral.

### Key Characteristics

- **Cash Borrower:** Sells securities, agrees to repurchase
- **Cash Lender:** Buys securities, agrees to resell
- **Repo Rate:** Interest rate on the cash
- **Haircut:** Margin/overcollateralization

---

## Mathematical Framework

### Repo Rate

$$Repo Rate = \frac{Repurchase Price - Purchase Price}{Purchase Price} \times \frac{360}{Days}$$

### Haircut

$$Haircut = 1 - \frac{Cash}{Collateral MV}$$

---

## SA-CCR Treatment

Securities financing transactions (SFTs) have specific treatment:

$$EAD = max(0, E - C) + AddOn$$

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

## Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import Repo
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = Repo("REPO-1", md.valuation_date, md.valuation_date, date(2027, 10, 9), 5_000_000, Currency.USD, "CP-1", rate=0.045)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```
