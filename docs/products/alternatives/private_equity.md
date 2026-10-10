# Private Equity Interest v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Private Equity Interest |
| **Product Class** | Private Markets |
| **Asset Class** | Alternatives - Private Equity |
| **Product Type** | PRIVATE_EQUITY |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Private equity interests represent ownership stakes in private companies or private equity funds. These are illiquid investments with long holding periods and irregular valuations.

### PE Fund Types

| Type | Strategy |
|------|----------|
| **Buyout** | Acquire mature companies |
| **Growth** | Minority stakes in growing companies |
| **Venture Capital** | Early-stage investing |
| **Distressed** | Turnaround situations |
| **Secondaries** | Purchase existing LP interests |

### Key Metrics

| Metric | Description |
|--------|-------------|
| **IRR** | Internal Rate of Return |
| **TVPI** | Total Value to Paid-In |
| **DPI** | Distributions to Paid-In |
| **RVPI** | Residual Value to Paid-In |

---

## Valuation

### NAV-Based

$$Value = NAV \times (1 - Illiquidity Discount)$$

### IRR-Based

Solve for IRR:

$$0 = \sum_{t} \frac{CF_t}{(1 + IRR)^t}$$

---

## Implementation Example

```python
from products.python.alternatives import PrivateEquityInterest

pe = PrivateEquityInterest(
    trade_id="PE-001",
    trade_date=date(2020, 1, 15),
    fund_name="ABC Capital Fund V",
    commitment=10000000,
    called_capital=7500000,
    distributions=2000000,
    nav=8500000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    vintage_year=2020,
    strategy="buyout",
    unfunded_commitment=2500000
)

result = pe.price(market_data)
print(f"NAV: ${result.npv:,.2f}")
print(f"TVPI: {result.components['tvpi']:.2f}x")
print(f"DPI: {result.components['dpi']:.2f}x")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
