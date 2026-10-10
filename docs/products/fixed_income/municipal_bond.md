# Municipal Bond v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Municipal Bond (Muni) |
| **Product Class** | Fixed Income - Municipal Securities |
| **Asset Class** | Interest Rate |
| **Product Type** | MUNICIPAL_BOND |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Municipal bonds are debt securities issued by states, cities, counties, and other governmental entities to fund public projects. A key feature is that interest income is typically exempt from federal income tax and may also be exempt from state and local taxes.

### Key Characteristics

- **Issuers:** States, cities, counties, school districts, public utilities
- **Tax Status:** Generally tax-exempt (federal)
- **Types:** General Obligation (GO) vs. Revenue bonds
- **Coupon:** Fixed or variable
- **Credit Enhancement:** Bond insurance, letters of credit

---

## Municipal Bond Types

| Type | Backing |
|------|---------|
| **General Obligation (GO)** | Full faith and credit, taxing power |
| **Revenue Bonds** | Specific project revenues |
| **Special Tax Bonds** | Dedicated tax revenues |
| **Build America Bonds** | Taxable with federal subsidy |

---

## Tax-Equivalent Yield

For comparison with taxable bonds:

$$y_{TE} = \frac{y_{muni}}{1 - t}$$

Where:
- $y_{muni}$ = Municipal bond yield
- $t$ = Marginal tax rate

---

## Credit Analysis

| Factor | GO Bonds | Revenue Bonds |
|--------|----------|---------------|
| Primary | Tax base, economic conditions | Project revenue, coverage ratio |
| Secondary | Debt burden, fund balance | Reserve funds, rate covenants |

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import MunicipalBond
from products.base import Currency, MarketData

muni = MunicipalBond(
    trade_id="MUNI-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2034, 1, 15),
    face_value=1000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.035,
    bond_type="GO",  # General Obligation
    state="CA",
    is_tax_exempt=True,
    is_long=True
)

result = muni.price(market_data)
print(f"Tax-Equivalent Yield: {result.components['tax_equivalent_yield']:.2%}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
