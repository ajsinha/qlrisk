# Collateralized Loan Obligation (CLO) v1.2.0

<!-- generated:implementation -->
> **Implementation:** `CLO` is priced by `price_clo_tranche` in `products/python/_pricing.py`. Product terms are keyword arguments: `pool`, `attachment` (7%), `detachment` (10%), `correlation` (25%), `recovery`, `coupon`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Collateralized Loan Obligation (CLO) |
| **Product Class** | Fixed Income - Structured Credit |
| **Asset Class** | Credit |
| **Product Type** | CLO |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A CLO is a type of CDO backed by a pool of leveraged loans (typically senior secured loans to sub-investment grade companies). CLOs are actively managed by portfolio managers who can trade the underlying loans.

### Key Characteristics

- **Collateral:** Senior secured leveraged loans
- **Active Management:** Manager can reinvest
- **Floating Rate:** Loans typically SOFR-based
- **Reinvestment Period:** Usually 4-5 years
- **Non-Call Period:** Protection for investors

---

## CLO Structure

| Tranche | Spread (bps) | Rating |
|---------|--------------|--------|
| **AAA** | 100-150 | Aaa/AAA |
| **AA** | 175-225 | Aa2/AA |
| **A** | 225-300 | A2/A |
| **BBB** | 350-450 | Baa2/BBB |
| **BB** | 600-800 | Ba2/BB |
| **Equity** | Residual | NR |

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| **WARF** | Weighted Average Rating Factor |
| **WALS** | Weighted Average Life Spread |
| **Diversity Score** | Portfolio concentration |
| **OC Ratio** | Overcollateralization test |
| **IC Ratio** | Interest coverage test |

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CLO
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = CLO("CLO-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1", pool="GLOBEX")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
