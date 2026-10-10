# Private Equity Interest v1.2.0

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
from products.python.alternatives import PrivateEquityInterest

pe = PrivateEquityInterest(
    trade_id="PE-001",
    fund_name="ABC Buyout Fund V",
    commitment=10000000,
    called_capital=6000000,
    distributions=2000000,
    nav=7500000,
    vintage_year=2020,
    strategy="buyout",
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
