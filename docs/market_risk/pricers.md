# QLRisk - Analytic Pricers v2.2.1

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
```

---

## Overview

`qlrisk/products/python/_pricing.py` holds the shared pricers behind 71 product classes (every product without
a bespoke pricer). Each product keeps
its constructor `(trade_id, trade_date, effective_date, maturity_date, notional, currency, counterparty_id, **kwargs)`;
**product terms go in the kwargs**, and every market input is read from `MarketData`, so the products respond to
shocks and sensitivities.

Terms you omit that depend on the market (an ATM strike, a quantity of `notional / price`) are **fixed at first
pricing** and stored on the product. Later revaluations then show P&L against that fixing.

## Pricers and kwargs

| Pricer | Products | Key kwargs (defaults) | Model |
|--------|----------|----------------------|-------|
| `price_fixed_bond` | TreasuryBond/Note, Agency, Corporate, Municipal, Bund, Gilt, JGB, OAT, MTN, ZeroCouponBond, TIPS, CreditLinkedNote | `coupon` (0), `frequency` (2), `issuer` (credit spread), `is_long` | Discounted cash flows at r(t) + s(t) |
| `price_deposit` | TreasuryBill, CP, BA, CD, DiscountNote, Eurodollar, FedFunds, TimeDeposit, Repo, ReverseRepo, BuySellBack, SecuritiesLending | `rate` (0), `issuer` | Single payment at maturity |
| `price_frn` | FloatingRateNote | `index` (`SOFR`), `spread` (0), `frequency` (4), `issuer` | Projected forwards + margin, discounted with credit |
| `price_cash_equity` | CommonStock, ADR, GDR, Preferred, ETF, MutualFund, IndexPosition, MoneyMarketFund, REIT, CryptoSpot, CarbonCredit, CryptoPerpetual, HedgeFund/PE interest | `ticker`, `quantity` | quantity × `equity_prices[ticker]` |
| `price_equity_option` | EquityOption, Warrant | `ticker` (`SPX`), `strike` (ATM), `is_call`, `quantity` | Black-Scholes with dividend curve; vol `"{ticker}_vol"` or `eq_vol` |
| `price_equity_forward` | EquityForward, IndexFuture, SingleStockFuture, CryptoFuture, CarbonFuture | `ticker`, `strike` (fair), `quantity`, `is_future` | S·e^{(r−q)T} − K |
| `price_fx_option` | FXOption | `pair` (`EURUSD`), `strike` (ATMF), `is_call`, `foreign_curve`/`foreign_rate` | Garman-Kohlhagen; vol `"{pair}_vol"` or `fx_vol` |
| `price_fx_digital` | FXDigitalOption | as above + `payout` | Cash-or-nothing |
| `price_fx_barrier` | FXBarrierOption | as above + `barrier`, `barrier_type` (`UpOut`/`UpIn`/`DownOut`/`DownIn`), `rebate` | QuantLib `AnalyticBarrierEngine` |
| `price_fx_ndf` | NonDeliverableForward | `pair`, `forward_rate` | Discounted forward difference |
| `price_cds` | CreditDefaultSwap, CDSIndex | `reference`, `coupon` (1%), `recovery` (0.4), `is_buyer` | Credit-triangle hazard, quarterly premium |
| `price_commodity_forward` / `_swap` / `_option` | CommodityForward, CommoditySwap, CommodityOption | `commodity` (`WTI`), `strike`, `quantity`, `convenience_yield`, `is_call` | Cost-of-carry forward; monthly-average swap; Black-76 |
| `price_xccy_swap` | CrossCurrencySwap, CrossCurrencyBasisSwap, MTMCrossCurrencySwap | `pair`, `foreign_curve` (`ESTR`), `domestic_coupon`, `foreign_coupon`, `frequency` | Fixed-fixed with notional exchange (basis/MTM approximated) |

| `price_ir_future` | InterestRateFuture | `index` (`SOFR`), `tenor` (0.25), `strike` | 100 × (1 − forward rate); $25 per bp per 1mm for 3M |
| `price_bond_future` | BondFuture | `bond_coupon` (6%), `bond_maturity_years` (10), `conversion_factor` (1), `strike` | Forward price of one deliverable bond / CF |
| `price_vix_future` | VIXFuture | `ticker` (`SPX`), `strike`, `quantity` | 100 × forward 30-day implied vol from the term structure |
| `price_variance_swap` | VarianceSwap | `ticker`, `strike` (vol), `vega_notional` | N_var × (σ²_imp − K²), N_var = vega notional / 2K |
| `price_dividend_swap` | DividendSwap | `ticker`, `strike`, `quantity` | S(1 − e^{−qT}) − K, discounted |
| `price_total_return` | EquitySwap, TotalReturnSwap | `ticker` or `issuer` + `coupon`, `spread`, `initial_price` | qty × (S − S₀) − N × spread × annuity |
| `price_convertible` | ConvertibleBond | `coupon`, `issuer`, `ticker`, `conversion_ratio` (30% premium) | Bond floor + ratio × Black-Scholes call |
| `price_mbs` | MBS | `coupon`, `wac`, `base_cpr`, `refi_multiplier`, `oas` | Monthly pass-through, CPR = base + refi × max(WAC − r10y, 0) — negative convexity |
| `price_abs` | ABS | `coupon`, `cpr`, `issuer` / `spread` | Pass-through with constant CPR |
| `price_tranche` / `price_clo_tranche` | CDO, CLO | `pool`, `attachment`, `detachment`, `correlation`, `recovery`, `coupon` | Vasicek large-pool expected tranche loss; risky floating-coupon note |

FX option PVs are in the **quote** currency of `pair`. Commodity spots come from the new
`MarketData.commodity_prices` field (risk factors `CMDTY.<name>`).

## Example

```python
from datetime import date
from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency
from qlrisk.products.python import CorporateBond, FXOption, CreditDefaultSwap, EquityOption
from qlrisk.sensitivities import SensitivityEngine

md = create_sample_market_data(date(2026, 10, 9))
d0, mat = md.valuation_date, date(2031, 10, 9)

trades = [
    CorporateBond("BOND-1", d0, d0, mat, 1_000_000, Currency.USD, "ACME", coupon=0.05, issuer="ACME"),
    FXOption("FXO-1", d0, d0, date(2027, 10, 9), 1_000_000, Currency.EUR, "CP", pair="EURUSD", strike=1.10),
    CreditDefaultSwap("CDS-1", d0, d0, mat, 10_000_000, Currency.USD, "CP", reference="GLOBEX", coupon=0.01),
    EquityOption("EQO-1", d0, d0, date(2027, 10, 9), 1_000_000, Currency.USD, "CP", ticker="AAPL", strike=200.0),
]
for t in trades:
    print(t.trade_id, round(t.price(md).npv, 2))

risk = SensitivityEngine().compute(trades, md, reporting_currency="USD")
for (rc, measure), value in risk.aggregate(("risk_class", "measure")).items():
    print(rc.value, measure.value, round(value, 2))
```

## Validation (tests/test_pricers.py)

- Every pricer prices without error and has a non-zero sensitivity to its own risk class.
- A par bond prices at par (0.2%).
- A CDS par spread equals the curve spread (2%), and buyer and seller have opposite signs.
- FX put-call parity holds (1e-6), and barrier in-out parity holds against the vanilla (0.1%).
- ATM equity forwards, commodity forwards and swaps, and NDFs start at zero PV.

## Model Limitations

These are deliberately compact models. The bond future uses one deliverable (no cheapest-to-deliver switch or
delivery options), the MBS has a deterministic prepayment rule (no path dependence), tranches use the large
homogeneous pool approximation, and the convertible ignores call/put features and credit-equity linkage.

---

*QLRisk v2.2.1 — Every risk. One engine. | Copyright © 2025-2030 Ashutosh Sinha*
