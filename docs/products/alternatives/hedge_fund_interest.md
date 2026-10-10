# Hedge Fund Interest v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Hedge Fund Interest |
| **Product Class** | Private Markets |
| **Asset Class** | Alternative |
| **Product Type** | HF_INTEREST |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Investment in a hedge fund, typically structured as LP interest. Various strategies with different liquidity terms.

### Strategies

| Strategy | Description |
|----------|-------------|
| Long/Short Equity | Equity with hedging |
| Global Macro | Cross-asset, directional |
| Event-Driven | M&A, restructuring |
| Relative Value | Arbitrage strategies |
| CTA/Managed Futures | Trend following |
| Multi-Strategy | Diversified |

---

## Liquidity Terms

| Term | Description |
|------|-------------|
| Lock-Up | Initial restricted period |
| Redemption Frequency | Monthly, quarterly, annual |
| Notice Period | 30-90 days typical |
| Gates | Limits on withdrawals |

---

## Implementation Example

```python
from products.python.alternatives import HedgeFundInterest

hf = HedgeFundInterest(
    trade_id="HF-001",
    fund_name="XYZ Capital Partners",
    investment=5000000,
    current_nav=5750000,
    strategy="long_short_equity",
    lock_up_end=date(2025, 1, 15),
    redemption_frequency="quarterly",
    notice_days=45,
    # ...
)
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
