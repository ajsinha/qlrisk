# Hedge Fund Interest v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Hedge Fund Interest |
| **Product Class** | Private Markets |
| **Asset Class** | Alternatives - Hedge Funds |
| **Product Type** | HEDGE_FUND |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

Hedge fund interests represent investments in pooled investment vehicles that employ various strategies to generate returns. Unlike mutual funds, hedge funds have fewer regulatory constraints and can use leverage, short selling, and derivatives.

### Common Strategies

| Strategy | Description |
|----------|-------------|
| **Long/Short Equity** | Long winners, short losers |
| **Global Macro** | Macro-economic bets |
| **Event Driven** | M&A, restructuring |
| **Relative Value** | Arbitrage opportunities |
| **Quantitative** | Systematic trading |
| **Multi-Strategy** | Combination approach |

### Fee Structure

| Fee | Typical Range |
|-----|---------------|
| Management Fee | 1-2% of AUM |
| Performance Fee | 15-20% of profits |
| Hurdle Rate | 0-8% |
| High Water Mark | Yes (usually) |

---

## Implementation Example

```python
from products.python.alternatives import HedgeFundInterest

hf = HedgeFundInterest(
    trade_id="HF-001",
    trade_date=date(2024, 1, 15),
    fund_name="Global Macro Partners",
    investment=5000000,
    nav_per_share=1250.00,
    shares=4000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    strategy="global_macro",
    management_fee=0.02,
    performance_fee=0.20,
    hurdle_rate=0.05,
    lockup_period_months=12,
    redemption_notice_days=45
)

result = hf.price(market_data)
print(f"NAV: ${result.npv:,.2f}")
print(f"Estimated Fees: ${result.components['estimated_fees']:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
