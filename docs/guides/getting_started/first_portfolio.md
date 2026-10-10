# Your First Portfolio: Price, Shock, Measure

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

This walk-through builds a small multi-asset book, prices it, applies a stress, and computes its risk.

## 1. Market data

```python
from datetime import date
from qlrisk.data import create_sample_market_data

md = create_sample_market_data(date(2026, 10, 9))
today = md.valuation_date
print(md.discount_curve[5.0], md.fx_spots["EURUSD"], md.equity_prices["SPX"])
```

## 2. Trades

Every product takes `(trade_id, trade_date, effective_date, maturity_date, notional, currency, counterparty_id)`
plus product-specific keyword terms (see [Pricing products](../pricing/pricing_products.md)).

```python
from qlrisk.products.base import Currency
from qlrisk.products.python import InterestRateSwap, CorporateBond, FXOption, EquityOption, CreditDefaultSwap

book = [
    InterestRateSwap("IRS-1", today, today, date(2031, 10, 9), 10_000_000, Currency.USD, "BANK-A", fixed_rate=0.042),
    CorporateBond("BOND-1", today, today, date(2030, 10, 9), 5_000_000, Currency.USD, "ACME", coupon=0.05, issuer="ACME"),
    FXOption("FXO-1", today, today, date(2027, 10, 9), 2_000_000, Currency.EUR, "BANK-B", pair="EURUSD", strike=1.10),
    EquityOption("EQO-1", today, today, date(2027, 4, 9), 1_000_000, Currency.USD, "BANK-B", ticker="SPX", strike=5200.0),
    CreditDefaultSwap("CDS-1", today, today, date(2031, 12, 20), 10_000_000, Currency.USD, "BANK-A", reference="GLOBEX"),
]
for trade in book:
    print(f"{trade.trade_id:7} {trade.price(md).npv:>15,.0f}")
```

## 3. A stress scenario

```python
from qlrisk.riskfactors import apply_shocks, curve_shocks, parallel, ShockType, RiskClass, Shock

risk_off = apply_shocks(md, [
    Shock("EQ.SPX", -0.20, ShockType.RELATIVE),
    Shock("FX.EURUSD", -0.05, ShockType.RELATIVE),
    Shock("CR.GLOBEX.5Y", 0.0100),
    Shock("CR.ACME.5Y", 0.0075),
    *curve_shocks(md, shape=parallel(-0.0050), risk_classes=[RiskClass.INTEREST_RATE]),
])
stress_pnl = {t.trade_id: t.price(risk_off).npv - t.price(md).npv for t in book}
print({k: round(v) for k, v in stress_pnl.items()}, "total", round(sum(stress_pnl.values())))
```

## 4. Sensitivities

```python
from qlrisk.sensitivities import SensitivityEngine

risk = SensitivityEngine().compute(book, md, reporting_currency="USD", include_theta=True)
for (risk_class, measure), value in sorted(risk.aggregate(("risk_class", "measure")).items(), key=str):
    print(f"{risk_class.value:3} {measure.value:6} {value:>12,.0f}")
print("theta", {k: round(v) for k, v in risk.theta().items()})
```

## 5. Counterparty exposure

```python
swap = book[0]
exposure = swap.calculate_ccr_exposure(md, time_horizon=5.0, num_scenarios=2000)
saccr = swap.calculate_saccr(md)
print(f"peak PFE {exposure.peak_exposure:,.0f}  EPE {exposure.epe:,.0f}  SA-CCR EAD {saccr.ead:,.0f}")
```

Next: [Market data](../market_data/building_market_data.md) · [Sensitivity reports](../market_risk/sensitivity_reports.md)
