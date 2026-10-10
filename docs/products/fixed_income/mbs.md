# Mortgage-Backed Securities (MBS)

<!-- generated:implementation -->
> **Implementation:** `MBS` is priced by `price_mbs` in `products/python/_pricing.py`. Product terms are keyword arguments: `coupon`, `wac`, `base_cpr`, `refi_multiplier`, `oas`, `is_long`. Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Mortgage-Backed Securities (MBS) |
| **Product Class** | Fixed Income - Securitized Products |
| **Asset Class** | Interest Rate |
| **Product Type** | MBS |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Mortgage-Backed Securities are bonds secured by a pool of residential mortgages. Cash flows from the underlying mortgages (principal and interest) are passed through to investors. Key risk is prepayment risk—borrowers can refinance when rates fall.

### Types of MBS

| Type | Guarantee | Issuer |
|------|-----------|--------|
| **Agency Pass-Through** | Government/GSE | GNMA, FNMA, FHLMC |
| **Non-Agency MBS** | None | Private label |
| **CMO** | Structured tranches | Various |

---

## Mathematical Framework

### Prepayment Models

#### Single Monthly Mortality (SMM)

$$SMM = 1 - (1 - CPR)^{1/12}$$

Where CPR is the Conditional Prepayment Rate (annualized).

#### PSA Model

$$CPR = \min\left(\frac{t}{30}, 1\right) \times 6\%$$

Where $t$ is the age in months. 100 PSA = 6% CPR at month 30.

### Pool Factor

$$PF = \frac{\text{Current Principal}}{\text{Original Principal}}$$

### Weighted Average Life (WAL)

$$WAL = \frac{\sum_{t=1}^{n} t \times P_t}{\sum_{t=1}^{n} P_t}$$

---

## Cash Flow Modeling

Monthly cash flow includes:
1. Scheduled principal
2. Scheduled interest
3. Prepayments

$$CF_t = Interest_t + Scheduled Principal_t + Prepayment_t$$

---

## Key Metrics

| Metric | Description |
|--------|-------------|
| **WAC** | Weighted Average Coupon |
| **WAM** | Weighted Average Maturity |
| **WAL** | Weighted Average Life |
| **WALA** | Weighted Average Loan Age |
| **OAS** | Option-Adjusted Spread |

---

## Option-Adjusted Analysis

### OAS Calculation

$$P = \sum_{\text{paths}} \sum_{t} \frac{E[CF_t]}{(1 + r_t + OAS)^t}$$

### Effective Duration

$$D_{eff} = \frac{P_{-\Delta r} - P_{+\Delta r}}{2 \times P \times \Delta r}$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import MBS
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = MBS("MBS-1", md.valuation_date, md.valuation_date, date(2056, 10, 9), 5_000_000, Currency.USD, "CP-1", coupon=0.055)

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
