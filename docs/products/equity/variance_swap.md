# Variance Swap v1.2.0

<!-- generated:implementation -->
> **Implementation status:** `VarianceSwap` currently uses **placeholder pricing** (`notional × discount factor × 1%`), so its PV and risk are not meaningful yet. It is on the roadmap for a real model.
>
> The narrative below describes the instrument; the example in this page is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.
<!-- /generated:implementation -->

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Variance Swap |
| **Product Class** | Equity Derivatives - Volatility |
| **Asset Class** | Equity |
| **Product Type** | VARIANCE_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Variance Swap is a forward contract on realized variance. It provides pure exposure to volatility without delta hedging requirements.

### Key Characteristics

- **Payoff:** Based on realized vs strike variance
- **Variance Notional:** Per variance point
- **Vega Notional:** Conversion to volatility terms
- **Uses:** Volatility trading, hedging

---

## Mathematical Framework

### Realized Variance

$$\sigma^2_{realized} = \frac{252}{n} \sum_{i=1}^{n} \left(\ln\frac{S_i}{S_{i-1}}\right)^2$$

### Payoff

$$Payoff = N_{var} \times (\sigma^2_{realized} - K_{var})$$

### Vega Notional Conversion

$$N_{vega} = N_{var} \times 2 \times K_{vol}$$

---

## Implementation Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import VarianceSwap
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
trade = VarianceSwap("VARIANCE-SWAP-1", md.valuation_date, md.valuation_date, date(2031, 10, 9), 5_000_000, Currency.USD, "CP-1")

result = trade.price(md)
print(f"NPV: {result.npv:,.2f} {result.currency}")

risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")
print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})
print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
