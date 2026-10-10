# Sensitivity Reports

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
import qlrisk.products.python as P
from qlrisk.sensitivities import SensitivityEngine, SensitivityMeasure, FRTB_GIRR_VERTICES, FRTB_CSR_VERTICES
from qlrisk.riskfactors import RiskClass

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
book = [
    P.InterestRateSwap("IRS-10Y", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "CP", fixed_rate=0.043),
    P.InterestRateSwap("IRS-2Y", d0, d0, date(2028, 10, 9), -40e6, Currency.USD, "CP", fixed_rate=0.042),
    P.CorporateBond("ACME-31", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "ACME", coupon=0.05, issuer="ACME"),
    P.CreditDefaultSwap("CDS-GLX", d0, d0, date(2031, 12, 20), 10e6, Currency.USD, "CP", reference="GLOBEX"),
    P.FXOption("EURUSD-C", d0, d0, date(2027, 10, 9), 10e6, Currency.EUR, "CP", pair="EURUSD", strike=1.12),
    P.EquityOption("SPX-P", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "CP", ticker="SPX", strike=5000.0, is_call=False),
]
risk = SensitivityEngine().compute(book, md, reporting_currency="USD", include_theta=True)
print(risk)
```

## Summary by risk class

```python
for (rc, m), v in sorted(risk.aggregate(("risk_class", "measure")).items(), key=str):
    print(f"{rc.value:3} {m.value:6} {v:>14,.0f}")
print("IR DV01 total", round(risk.total(SensitivityMeasure.DV01, RiskClass.INTEREST_RATE)))
```

## Tenor ladders (native pillars and FRTB vertices)

```python
print(risk.ladder("forward_curves", "SOFR"))
print(risk.ladder("discount_curve", vertices=FRTB_GIRR_VERTICES))
print(risk.ladder("credit_curves", "ACME", vertices=FRTB_CSR_VERTICES))
```

## Per-trade drill-down, gamma, theta

```python
for trade_id, v in risk.aggregate("trade_id").items():
    print(f"{trade_id:9} first-order {v:>12,.0f}")
print("SPX gamma (per 1%^2):", round(risk.aggregate("factor", value="gamma")[next(k for k in risk.by_factor() if str(k) == "EQ.SPX")]))
print("theta:", {k: round(v) for k, v in risk.theta().items()})
```

## Cross-gamma (vanna) for a few factors

```python
cg = SensitivityEngine().cross_gamma(book[5], md, ["EQ.SPX", "VOL.eq_vol.6M", "VOL.eq_vol.1Y"])
for r in cg:
    print(r.factor, r.factor2, round(r.value, 2))
```

## Export

```python
import csv, io
buf = io.StringIO()
rows = risk.to_rows()
writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
writer.writeheader(); writer.writerows(rows)
print(buf.getvalue().splitlines()[:3])
```

Conventions: DV01/CS01 = PV change per +1bp, DELTA = per +1%, VEGA = per +1 vol point
(details in [sensitivities.md](../../market_risk/sensitivities.md)).
