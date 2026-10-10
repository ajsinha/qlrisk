# Regulatory Capital: FRTB SA, FRTB IMA, Basel 2.5, BA-CVA

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

```python
from datetime import date
from qlrisk.data import create_sample_market_data, MarketHistoryGenerator
from qlrisk.products.base import Currency
from qlrisk.engine import MarketRiskEngine
import qlrisk.products.python as P

md = create_sample_market_data(date(2026, 10, 9))
d0 = md.valuation_date
history = MarketHistoryGenerator(seed=7).generate(md, num_days=750, stress_start=300, stress_days=60)
book = [
    P.InterestRateSwap("IRS-10Y", d0, d0, date(2036, 10, 9), 25e6, Currency.USD, "RATES", fixed_rate=0.043),
    P.CorporateBond("ACME-31", d0, d0, date(2031, 10, 9), 10e6, Currency.USD, "CREDIT", coupon=0.05, issuer="ACME"),
    P.CreditDefaultSwap("GLX-CDS", d0, d0, date(2031, 12, 20), 5e6, Currency.USD, "CREDIT", reference="GLOBEX"),
    P.EquityOption("SPX-P", d0, d0, date(2027, 4, 9), 5e6, Currency.USD, "EQUITY", ticker="SPX", strike=5000.0, is_call=False),
    P.FXBarrierOption("EUR-KO", d0, d0, date(2027, 4, 9), 5e6, Currency.EUR, "FX", pair="EURUSD", strike=1.10, barrier=1.30),
    P.CommodityForward("WTI-F", d0, d0, date(2027, 10, 9), 5e6, Currency.USD, "CMDTY", commodity="WTI", strike=72.0),
]
```

## 1. FRTB Standardised Approach

The SA needs bucket assignments for credit names and equities (MAR21), ratings for the DRC, and the
underlying of each volatility surface:

```python
from qlrisk.regulatory import frtb_sa_capital

sa = frtb_sa_capital(
    book, md, reporting_currency="USD",
    credit_buckets={"ACME": 4, "GLOBEX": 12},          # 4 = IG basic materials/industrials, 12 = HY same sector
    equity_buckets={"SPX": 12},                         # 12 = large-cap advanced-economy indices
    ratings={"ACME": "BBB", "GLOBEX": "BB"},
    vol_underlyings={"eq_vol": "SPX", "fx_vol": "EURUSD"},
)
for k, v in sa.summary().items():
    print(f"{k:16} {v:>14,.0f}")
print("correlation scenario:", sa.sbm.scenario, {k: round(v) for k, v in sa.sbm.by_scenario.items()})
print("RRAO trades:", sa.rrao["by_trade"])
print("not mapped to FRTB factors:", sa.sbm.skipped_factors)
```

Work at a lower level when you already have FRTB sensitivities:

```python
from qlrisk.regulatory.frtb_sa import FRTBSensitivity, sbm_capital, DRCPosition, drc_charge

fs = [FRTBSensitivity("GIRR", "delta", "USD", "SOFR", 5.0, 2.0e7, 0.011 / 2 ** 0.5),
      FRTBSensitivity("GIRR", "delta", "USD", "SOFR", 10.0, -1.5e7, 0.011 / 2 ** 0.5),
      FRTBSensitivity("EQ", "delta", 12, "SPX", None, -3.0e6, 0.15)]
print(round(sbm_capital(fs).total))
print(drc_charge([DRCPosition("ACME", "BBB", 10e6, 9.9e6, 5.0), DRCPosition("GLOBEX", "BB", -5e6, -5e6, 5.0)]))
```

## 2. FRTB Internal Models Approach

```python
from qlrisk.regulatory import imcc, ses, rfet, ima_capital, ima_drc
from qlrisk.regulatory.frtb_sa import drc_positions_from_trades
from qlrisk.riskfactors import RiskFactorKey

engine = MarketRiskEngine(reporting_currency="USD")
ic = imcc(engine, book, md, history)                       # liquidity-adjusted, stress-calibrated
print(f"IMCC {ic.imcc:,.0f}  (unconstrained ES {ic.es_unconstrained:,.0f}, ratio {ic.ratio:.2f})")
print("stress window", ic.stress_window, {k: round(v) for k, v in ic.es_by_class.items()})

# modellability: a factor with sparse real prices fails the RFET and goes to SES
from datetime import timedelta
print("RFET:", rfet([d0 - timedelta(days=i) for i in range(0, 360, 30)], d0))
nmrf = [RiskFactorKey.parse("CR.GLOBEX.5Y")]
s = ses(engine, book, md, history, nmrf, ic.stress_window)
drc = ima_drc(drc_positions_from_trades(book, md, {"ACME": "BBB", "GLOBEX": "BB"}), n_sims=50_000)
print(f"SES {s['ses']:,.0f}  IMA DRC {drc['drc']:,.0f}")
print(f"IMA capital {ima_capital(ic.imcc, s['ses'], drc['drc'], multiplier=1.5):,.0f}")
```

## 3. Basel 2.5

```python
from qlrisk.regulatory import basel25_capital
from qlrisk.scenarios import historical_scenarios

var10 = engine.var(book, md, historical_scenarios(history, lookback=250, horizon=10, sqrt_scaling=True)).value
svar10 = engine.stressed_var(book, md, history, horizon_days=10).value
bt = engine.backtest(book, md, history, test_days=250)
print(basel25_capital([var10], [svar10], exceptions=bt["var"].exceptions))
```

In production, pass the last 60 daily VaR and SVaR figures; here one observation stands in for the average.

## 4. CVA capital (BA-CVA)

```python
from qlrisk.regulatory import ba_cva, CVACounterparty, CVAHedge, CVAIndexHedge

swap_ead = book[0].calculate_saccr(md).ead                  # SA-CCR EAD of the netting set
cps = [
    CVACounterparty("RATES", sector="financial", investment_grade=True, netting_sets=[(swap_ead, 10.0)]),
    CVACounterparty("CREDIT", sector="consumer", investment_grade=False, netting_sets=[(2e6, 3.0)]),
]
print(ba_cva(cps))
cps[0].hedges.append(CVAHedge(notional=1e6, maturity=5.0, correlation=1.0))
print("with hedges:", round(ba_cva(cps, [CVAIndexHedge(2e6, 5.0)])["capital"]))
```

## 5. CVA capital (SA-CVA)

SA-CVA needs a CVA that responds to market data. `cva_from_profile` builds one from an exposure profile and the
counterparty's credit curve; eligible hedges (e.g. a CDS on the counterparty) reduce the charge:

```python
from qlrisk.regulatory import sa_cva_capital, cva_from_profile

ee_profile = [2e6, 3e6, 3.5e6, 3e6, 2e6, 1e6]
cva_fn = cva_from_profile("ACME", time_grid=[0.5, 1, 2, 3, 4, 5], expected_exposure=ee_profile)
print(f"CVA {cva_fn(md):,.0f}")

bare = sa_cva_capital(cva_fn, md, counterparty_buckets={"ACME": ("3", True)})      # MAR50 bucket 3, IG
cds = P.CreditDefaultSwap("ACME-HEDGE", d0, d0, date(2031, 12, 20), 3e6, Currency.USD, "DEALER", reference="ACME")
hedged = sa_cva_capital(cva_fn, md, counterparty_buckets={"ACME": ("3", True)}, hedges=[cds])
print(f"SA-CVA {bare.total:,.0f} -> {hedged.total:,.0f} with hedge")
print({f"{rc} {rt}": round(v) for (rc, rt), v in bare.by_component.items() if v})
```

## 6. SA-CCR with netting and collateral

```python
from qlrisk.regulatory.saccr_netting import saccr_netting_sets, CSATerms

sets = saccr_netting_sets(book, md, csa={"RATES": CSATerms(margined=True, collateral=0.0)})
for name, ns in sets.items():
    print(f"{name:7} EAD {ns.ead:>13,.0f}  add-on {ns.addon:>12,.0f}  {dict((k, round(v)) for k, v in ns.addon_by_class.items())}")
```

Methodology, parameters and simplifications: [market_risk/frtb.md](../../market_risk/frtb.md).
