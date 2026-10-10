# Pricing Products

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

All products share one constructor shape and one method:

```text
Product(trade_id, trade_date, effective_date, maturity_date, notional, currency, counterparty_id, **terms)
product.price(market_data) -> PricingResult(npv, currency, components, greeks, ...)
```

Terms are keyword arguments; full tables per pricer are in [pricers.md](../../market_risk/pricers.md).

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
import qlrisk.products.python as P

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
def show(trade):
    res = trade.price(md)
    print(f"{trade.trade_id:10} {res.npv:>15,.2f} {res.currency}")
    return res
```

## Rates

```python
show(P.InterestRateSwap("IRS", d0, d0, date(2036, 10, 9), 10e6, Currency.USD, "CP", fixed_rate=0.043, is_payer=True))
show(P.OvernightIndexSwap("OIS", d0, d0, date(2028, 10, 9), 10e6, Currency.USD, "CP", fixed_rate=0.042))
show(P.Swaption("SWPN", d0, date(2027, 10, 9), date(2027, 10, 9), date(2032, 10, 9), 10e6, Currency.USD, "CP", strike=0.043))
show(P.InterestRateCap("CAP", d0, d0, date(2029, 10, 9), 10e6, Currency.USD, "CP", strike=0.045))
```

## Bonds and money market

```python
show(P.TreasuryBond("UST", d0, d0, date(2036, 8, 15), 1e6, Currency.USD, "UST", coupon=0.0425))
show(P.CorporateBond("CORP", d0, d0, date(2031, 6, 1), 1e6, Currency.USD, "GLOBEX", coupon=0.055, issuer="GLOBEX"))
show(P.FloatingRateNote("FRN", d0, d0, date(2029, 10, 9), 1e6, Currency.USD, "ACME", index="SOFR", spread=0.008, issuer="ACME"))
show(P.TreasuryBill("BILL", d0, d0, date(2027, 4, 9), 1e6, Currency.USD, "UST"))
show(P.Repo("REPO", d0, d0, date(2026, 11, 9), 50e6, Currency.USD, "CP", rate=0.0435))
```

## FX

PVs are in the quote currency of `pair`.

```python
show(P.FXForward("FXF", d0, date(2027, 10, 9), Currency.EUR, Currency.USD, 5e6, 1.10, "CP"))
show(P.FXOption("FXO", d0, d0, date(2027, 4, 9), 5e6, Currency.EUR, "CP", pair="EURUSD", strike=1.10, is_call=True))
show(P.FXDigitalOption("DIG", d0, d0, date(2027, 4, 9), 1e6, Currency.EUR, "CP", pair="EURUSD", strike=1.10, payout=100_000))
show(P.FXBarrierOption("BAR", d0, d0, date(2027, 4, 9), 5e6, Currency.EUR, "CP", pair="EURUSD", strike=1.10,
                       barrier=1.20, barrier_type="UpOut"))
show(P.NonDeliverableForward("NDF", d0, d0, date(2027, 4, 9), 1e6, Currency.USD, "CP", pair="USDJPY", forward_rate=145.0))
```

## Equity, credit, commodity, cross-currency

```python
show(P.CommonStock("AAPL", d0, d0, date(2099, 1, 1), 1e6, Currency.USD, "CP", ticker="AAPL"))
show(P.EquityOption("SPXC", d0, d0, date(2027, 10, 9), 1e6, Currency.USD, "CP", ticker="SPX", strike=5400.0))
show(P.EquityForward("SPXF", d0, d0, date(2027, 10, 9), 1e6, Currency.USD, "CP", ticker="SPX", strike=5300.0))
cds = show(P.CreditDefaultSwap("CDS", d0, d0, date(2031, 12, 20), 10e6, Currency.USD, "CP", reference="ACME", coupon=0.01))
print("  par spread", round(cds.components["par_spread"] * 1e4, 1), "bp")
show(P.CommoditySwap("OILSW", d0, d0, date(2027, 10, 9), 1e6, Currency.USD, "CP", commodity="WTI", strike=76.0))
show(P.CommodityOption("GOLDC", d0, d0, date(2027, 10, 9), 1e6, Currency.USD, "CP", commodity="GOLD", strike=2500.0))
show(P.CrossCurrencySwap("XCCY", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "CP", pair="EURUSD", foreign_curve="ESTR"))
```

## Defaults fixed at first pricing

Omitted strikes default to at-the-money(-forward) and quantities to `notional / price`, **fixed the first time the
trade is priced** — later pricings show P&L against that fixing:

```python
atm = P.EquityOption("ATM", d0, d0, date(2027, 10, 9), 1e6, Currency.USD, "CP", ticker="AAPL")
before = atm.price(md).npv
print("fixed strike", atm.additional_params["strike"])
from qlrisk.riskfactors import apply_shocks, ShockType
print("P&L on +5%", round(atm.price(apply_shocks(md, {"EQ.AAPL": 0.05}, ShockType.RELATIVE)).npv - before))
```

12 complex products (MBS, ABS, CDO, CLO, convertible, variance/dividend/equity swaps, TRS, bond/IR/VIX
futures) still use placeholder pricing.
