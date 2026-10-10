# One Engine: Risk Reports, Hierarchies and Limits

```
Copyright © 2025-2030, All Rights Reserved — Ashutosh Sinha | ajsinha@gmail.com
```

> Every `python` block in this guide is executed by `tests/test_doc_examples.py`, top to bottom, in one namespace.

`RiskEngine.run()` produces every number for a book in one call: PV, sensitivities, VaR, ES, stressed VaR,
stress tests, backtests, FRTB SA capital and counterparty exposure. It rolls them up a reporting
hierarchy and checks them against limits.

## The book

```python
from qlrisk.demos import demo_book

book, md, history, tree, frtb_maps = demo_book()      # 6 trades, sample market, 750-day history, desks
for t in book:
    print(f"{t.trade_id:9} {type(t).__name__:18} {t.counterparty_id}")
```

`demo_book()` is a convenient starting point. Its source in `qlrisk/demos.py` shows how each piece is built.

## Run everything

```python
from qlrisk.engine import RiskEngine, ALL_MEASURES
from qlrisk.reporting import RiskLimit

engine = RiskEngine(reporting_currency="USD", confidence=0.99, lookback=250, horizon_days=10)
report = engine.run(
    book, md, history,
    measures=ALL_MEASURES,                      # PV, SENSITIVITIES, VAR, ES, PARAMETRIC_VAR, SVAR, STRESS, BACKTEST, FRTB_SA, EXPOSURE
    hierarchy=tree,
    frtb=frtb_maps,                             # bucket maps, ratings and vol underlyings for FRTB SA
    limits=[
        RiskLimit("Firm 1d VaR", "var.1d", 500_000),
        RiskLimit("Rates 1d VaR", "var.1d", 300_000, node="BankCo/Rates"),
        RiskLimit("Credit CS01", "cs01", 5_000, node="BankCo/Credit"),
        RiskLimit("Worst stress", "stress.worst", 3_000_000),
    ],
)
print(report)
```

## Drill down the hierarchy

Additive measures (PV, DV01, CS01, vega, exposure) are summed. VaR and ES are **recomputed** at every
node from the node's combined scenario P&L, so desk VaRs do not add up to the firm VaR:

```python
for node, vals in report.by_node.items():
    print(f"{node:20} pv {vals.get('pv', 0):>14,.0f}  var.1d {vals.get('var.1d', 0):>11,.0f}  dv01 {vals.get('dv01', 0):>9,.0f}")

print("diversification benefit:", {k: round(v) for k, v in tree.diversification(report.results["pnl"]).items()})
```

## Limits

```python
from qlrisk.reporting import breaches
for check in report.results["limits"]:
    print(check)
print("breaches:", [c.name for c in breaches(report.results["limits"])])
```

The thresholds are GREEN below 75%, AMBER below 90%, RED up to 100% and BREACH above 100%. Change them per limit
with `amber=` and `red=`.

## Full result objects

```python
print(report.results["var"])                      # RiskMeasureResult with contributions
print(report.results["svar"].metadata["window_start"], "->", report.results["svar"].metadata["window_end"])
print(report.results["backtest"]["var"].summary())
print(round(report.results["frtb_sa"].total))
```

## Export

```python
import os, tempfile
out = tempfile.mkdtemp()
report.to_json(os.path.join(out, "risk.json"))
report.to_csv(os.path.join(out, "risk.csv"))
print(sorted(os.listdir(out)), len(report.rows()), "rows")
```

## Configuration

`RiskEngine.from_config()` reads the `marketrisk.*` keys from `config/application.properties`, or from
any properties file you pass in. Keyword overrides take precedence:

```python
engine_cfg = RiskEngine.from_config(lookback=500)
print(engine_cfg.reporting_currency, engine_cfg.confidence, engine_cfg.lookback)
```

## Wrong-way risk

Wrong-way risk is exposure to a counterparty that grows as the counterparty's credit worsens:

```python
from qlrisk.scenarios import wrong_way_exposure
spx_put = [t for t in book if t.trade_id == "SPX-P"]
wwr = wrong_way_exposure(spx_put, md, history, "CR.ACME.5Y", shock_sigmas=3.0)
print(f"exposure {wwr.base_exposure:,.0f} -> {wwr.conditional_exposure:,.0f} (x{wwr.ratio:.2f}) when ACME widens {wwr.spread_move*1e4:.0f}bp")
```

## Netting sets (SA-CCR, CRE52)

`EXPOSURE` aggregates SA-CCR per netting set (`trade.netting_set_id`, defaulting to the counterparty) with
hedging-set netting: IR by currency and maturity bucket, FX by pair, credit / equity by entity, commodity by
type. Pass collateral terms per netting set with `csa=`:

```python
from qlrisk.regulatory.saccr_netting import CSATerms

margined = engine.run(book, md, measures=("EXPOSURE",),
                      csa={"BANK-A": CSATerms(margined=True, collateral=250_000, threshold=0, minimum_transfer_amount=0)})
for ns, agg in margined.results["netting_sets"].items():
    print(f"{ns:8} MtM {agg.mtm:>13,.0f}  RC {agg.replacement_cost:>12,.0f}  add-on {agg.addon:>12,.0f}  "
          f"multiplier {agg.multiplier:.2f}  EAD {agg.ead:>13,.0f}  {dict((k, round(v)) for k, v in agg.addon_by_class.items())}")
```

## Command line

```bash
qlrisk --market-risk     # this report on the demo book, with limits
qlrisk --frtb            # FRTB SA capital breakdown
```
