# Corporate Bond v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Corporate Bond |
| **Product Class** | Fixed Income - Corporate Securities |
| **Asset Class** | Interest Rate / Credit |
| **Product Type** | CORPORATE_BOND |
| **Implementation** | Python ✓ | QuantLib ✓ |

---

## Description

Corporate bonds are debt securities issued by corporations to raise capital. They offer higher yields than government bonds due to credit risk. The corporate bond market includes investment grade (IG) and high yield (HY) segments.

### Key Characteristics

- **Issuers:** Public and private corporations
- **Credit Risk:** Dependent on issuer's creditworthiness
- **Seniority:** Secured, Senior Unsecured, Subordinated
- **Covenants:** Financial and operational restrictions
- **Recovery:** Expected recovery in default

---

## Credit Rating Scale

| Rating | Category | Spread (bps) |
|--------|----------|--------------|
| AAA | Investment Grade | 20-40 |
| AA | Investment Grade | 40-70 |
| A | Investment Grade | 70-120 |
| BBB | Investment Grade | 120-200 |
| BB | High Yield | 250-400 |
| B | High Yield | 400-600 |
| CCC | High Yield | 600-1000+ |

---

## Mathematical Framework

### Credit Spread

$$s = y_{corp} - y_{rf}$$

Where:
- $y_{corp}$ = Corporate bond yield
- $y_{rf}$ = Risk-free (Treasury) yield

### Risk-Adjusted Pricing

$$P = \sum_{i=1}^{n} \frac{CF_i}{(1 + r_f + s)^{t_i}}$$

### Recovery-Adjusted Spread

$$s = \frac{PD \times LGD}{1 - PD \times LGD}$$

Where:
- $PD$ = Probability of Default
- $LGD$ = Loss Given Default = 1 - Recovery Rate

---

## Seniority and Recovery

| Seniority | Typical Recovery |
|-----------|-----------------|
| Senior Secured | 50-70% |
| Senior Unsecured | 35-50% |
| Senior Subordinated | 25-40% |
| Subordinated | 15-30% |
| Junior Subordinated | 10-20% |

---

## Risk Metrics

### CS01 (Credit Spread Sensitivity)

$$CS01 = D_{spread} \times P \times 0.0001$$

### Spread Duration

$$D_{spread} \approx D_{modified}$$

---

## SA-CCR Treatment

Corporate bonds are treated under credit asset class:

$$AddOn = SF_{credit}(rating) \times Notional \times MF$$

| Rating | SF |
|--------|----|
| AAA-AA | 0.38% |
| A | 0.42% |
| BBB | 0.54% |
| BB | 1.06% |
| B | 1.06% |
| CCC | 6.00% |

---

## Implementation Example

```python
from datetime import date
from products.python.fixed_income import CorporateBond, Seniority
from products.base import Currency, MarketData

corp = CorporateBond(
    trade_id="CORP-001",
    trade_date=date(2024, 1, 15),
    issue_date=date(2024, 1, 15),
    maturity_date=date(2029, 1, 15),
    face_value=5000000,
    currency=Currency.USD,
    counterparty_id="CPY-001",
    coupon_rate=0.055,
    issuer_name="ACME Corp",
    credit_rating="BBB",
    seniority=Seniority.SENIOR_UNSECURED,
    sector="technology",
    is_long=True
)

# Create market data with credit spread
market_data = MarketData(
    valuation_date=date(2024, 6, 15),
    discount_curve={1: 0.05, 5: 0.052, 10: 0.055},
    credit_spreads={"BBB": 0.015}  # 150 bps
)

result = corp.price(market_data)
print(f"Credit Spread: {result.components['credit_spread']:.0%}")
print(f"CS01: ${result.greeks['cs01']:,.2f}")
print(f"Recovery Rate: {result.components['recovery_rate']:.0%}")

# SA-CCR
saccr = corp.calculate_saccr(market_data)
print(f"EAD: ${saccr.ead:,.2f}")
```

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
