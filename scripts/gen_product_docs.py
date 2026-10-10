#!/usr/bin/env python3
"""
Regenerate the implementation banner and the runnable example of every product page in
docs/products/<category>/<product>.md from the code, so the pages always match the API.

    python scripts/gen_product_docs.py

Narrative sections are left untouched. The first ```python block of each page is replaced by
the generated example; the banner sits between the generated-section markers below the title.
"""

import inspect
import pathlib
import re

import qlrisk.products.python as P
from qlrisk.products.base import BaseProduct

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs" / "products"
BEGIN, END = "<!-- generated:implementation -->", "<!-- /generated:implementation -->"
ALIASES = {"hedge_fund": "hedge_fund_interest", "private_equity": "private_equity_interest",
           "bond": "corporate_bond", "fx_digital": "fx_digital_option", "ndf": "non_deliverable_forward"}

# Example terms per pricer (keyword arguments after the common constructor arguments)
PRICER_TERMS = {
    "price_fixed_bond": ('coupon=0.05, issuer="ACME"', "`coupon`, `frequency` (2), `issuer` (credit curve), `is_long`"),
    "price_deposit": ("rate=0.045", "`rate`, `issuer`, `is_long`"),
    "price_frn": ('index="SOFR", spread=0.01, issuer="ACME"', "`index`, `spread`, `frequency` (4), `issuer`, `is_long`"),
    "price_cash_equity": ('ticker="AAPL"', "`ticker` (equity_prices key), `quantity` (default notional / price), `is_long`"),
    "price_equity_option": ('ticker="AAPL", strike=200.0, is_call=True', "`ticker`, `strike` (ATM), `is_call`, `quantity`, `is_long`"),
    "price_equity_forward": ('ticker="SPX"', "`ticker`, `strike` (fair forward), `quantity`, `is_future`, `is_long`"),
    "price_fx_option": ('pair="EURUSD", strike=1.10, is_call=True', "`pair`, `strike` (ATMF), `is_call`, `foreign_curve` / `foreign_rate`, `is_long`"),
    "price_fx_digital": ('pair="EURUSD", strike=1.10, payout=100_000', "`pair`, `strike`, `is_call`, `payout`, `is_long`"),
    "price_fx_barrier": ('pair="EURUSD", strike=1.10, barrier=1.25, barrier_type="UpOut"', "`pair`, `strike`, `barrier`, `barrier_type` (UpOut/UpIn/DownOut/DownIn), `rebate`, `is_call`"),
    "price_fx_ndf": ('pair="USDJPY", forward_rate=148.0', "`pair`, `forward_rate`, `is_long`"),
    "price_cds": ('reference="ACME", coupon=0.01', "`reference` (credit curve), `coupon`, `recovery` (0.4), `is_buyer`"),
    "price_commodity_forward": ('commodity="WTI", strike=75.0', "`commodity` (commodity_prices key), `strike`, `quantity`, `convenience_yield`, `is_long`"),
    "price_commodity_swap": ('commodity="BRENT", strike=80.0', "`commodity`, `strike` (fair), `quantity`, `convenience_yield`, `is_long`"),
    "price_commodity_option": ('commodity="GOLD", strike=2400.0, is_call=True', "`commodity`, `strike`, `is_call`, `quantity`, `is_long`"),
    "price_xccy_swap": ('pair="EURUSD", foreign_curve="ESTR"', "`pair`, `foreign_curve`, `domestic_coupon`, `foreign_coupon`, `frequency`, `is_long`"),
    "price_ir_future": ('index="SOFR", tenor=0.25', "`index`, `tenor` (0.25), `strike` (traded price), `is_long`"),
    "price_bond_future": ("bond_coupon=0.06, bond_maturity_years=10.0", "`bond_coupon`, `bond_maturity_years`, `conversion_factor`, `strike`, `is_long`"),
    "price_vix_future": ('ticker="SPX"', "`ticker`, `strike` (fair forward VIX), `quantity`, `is_long`"),
    "price_variance_swap": ('ticker="SPX", vega_notional=100_000', "`ticker`, `strike` (vol), `vega_notional`, `is_long`"),
    "price_dividend_swap": ('ticker="SPX"', "`ticker`, `strike` (fair), `quantity`, `is_long`"),
    "price_total_return": ('ticker="AAPL", spread=0.005', "`ticker` (equity) or `issuer` + `coupon` (bond), `spread`, `initial_price`, `is_long`"),
    "price_convertible": ('coupon=0.02, issuer="ACME", ticker="AAPL"', "`coupon`, `issuer`, `ticker`, `conversion_ratio`, `is_long`"),
    "price_mbs": ("coupon=0.055", "`coupon`, `wac`, `base_cpr`, `refi_multiplier`, `oas`, `is_long`"),
    "price_abs": ('coupon=0.05, cpr=0.10, issuer="ACME"', "`coupon`, `cpr`, `issuer` / `spread`, `is_long`"),
    "price_tranche": ('pool="GLOBEX", attachment=0.03, detachment=0.07, correlation=0.30', "`pool`, `attachment`, `detachment`, `correlation`, `recovery`, `coupon`, `is_long`"),
    "price_clo_tranche": ('pool="GLOBEX"', "`pool`, `attachment` (7%), `detachment` (10%), `correlation` (25%), `recovery`, `coupon`, `is_long`"),
}
COMMON = 'md.valuation_date, md.valuation_date, date({y}, 10, 9), {notional}, Currency.{ccy}, "CP-1"'
CUSTOM = {
    "InterestRateSwap": 'InterestRateSwap("IRS-1", d0, d0, date(2031, 10, 9), 10_000_000, Currency.USD, "CP-1", fixed_rate=0.043)',
    "OvernightIndexSwap": 'OvernightIndexSwap("OIS-1", d0, d0, date(2028, 10, 9), 10_000_000, Currency.USD, "CP-1", fixed_rate=0.042)',
    "ForwardRateAgreement": 'ForwardRateAgreement("FRA-1", d0, date(2027, 4, 7), date(2027, 4, 9), date(2027, 10, 9), 10_000_000, Currency.USD, "CP-1", fra_rate=0.043)',
    "InterestRateCap": 'InterestRateCap("CAP-1", d0, d0, date(2029, 10, 9), 10_000_000, Currency.USD, "CP-1", strike=0.045)',
    "InterestRateFloor": 'InterestRateFloor("FLOOR-1", d0, d0, date(2029, 10, 9), 10_000_000, Currency.USD, "CP-1", strike=0.035)',
    "Swaption": 'Swaption("SWPN-1", d0, date(2027, 10, 9), date(2027, 10, 9), date(2032, 10, 9), 10_000_000, Currency.USD, "CP-1", strike=0.043)',
    "BasisSwap": 'BasisSwap("BASIS-1", d0, d0, date(2031, 10, 9), 10_000_000, Currency.USD, "CP-1", spread=0.001)',
    "FXForward": 'FXForward("FXF-1", d0, date(2027, 10, 9), Currency.EUR, Currency.USD, 1_000_000, 1.10, "CP-1")',
    "FXSwap": 'FXSwap("FXSW-1", d0, date(2026, 10, 13), date(2027, 10, 9), Currency.EUR, Currency.USD, 1_000_000, 1.085, 1.10, "CP-1")',
}
LONG_DATED = {"common_stock", "adr", "gdr", "preferred_stock", "etf", "mutual_fund", "index_position",
              "money_market_fund", "reit", "crypto_spot", "carbon_credit", "hedge_fund_interest", "private_equity_interest"}
EXTRA_MARKET = {"crypto_spot": 'md.equity_prices["AAPL"] = 190.0', "crypto_perpetual": 'md.equity_prices["AAPL"] = 190.0'}


def classes():
    out = {}
    for name, obj in vars(P).items():
        if inspect.isclass(obj) and issubclass(obj, BaseProduct) and obj is not BaseProduct:
            out[obj.__module__.split(".")[-1]] = obj
    return out


def pricer_of(cls) -> str:
    src = inspect.getsource(cls)
    m = re.search(r"return (price_\w+)\(self, market_data\)", src)
    if m:
        return m.group(1)
    return "PLACEHOLDER" if "notional * df * 0.01" in src else "custom"


def example(cls, module: str, pricer: str) -> str:
    name = cls.__name__
    if name in CUSTOM:
        ctor = CUSTOM[name]
    else:
        ccy = "EUR" if pricer in ("price_fx_option", "price_fx_digital", "price_fx_barrier") else "USD"
        year = 2099 if module in LONG_DATED else (2031 if pricer in ("price_fixed_bond", "price_frn", "price_cds",
                                                                     "price_xccy_swap", "price_convertible", "price_abs", "price_tranche",
                                                                     "price_clo_tranche", "price_total_return") else
                                                 2056 if pricer == "price_mbs" else 2027)
        terms = PRICER_TERMS.get(pricer, ("", ""))[0]
        ctor = f'{name}("{module.upper().replace("_", "-")}-1", ' + COMMON.format(y=year, notional="5_000_000", ccy=ccy) \
            + (f", {terms}" if terms else "") + ")"
    lines = [
        "from datetime import date",
        "from qlrisk.data import create_sample_market_data",
        "from qlrisk.products.base import Currency",
        f"from qlrisk.products.python import {name}",
        "from qlrisk.sensitivities import SensitivityEngine",
        "",
        "md = create_sample_market_data(date(2026, 10, 9))",
        "d0 = md.valuation_date",
    ]
    if module in EXTRA_MARKET:
        lines.append(EXTRA_MARKET[module])
    lines += [
        f"trade = {ctor}",
        "",
        "result = trade.price(md)",
        'print(f"NPV: {result.npv:,.2f} {result.currency}")',
        "",
        'risk = SensitivityEngine().compute(trade, md, reporting_currency="USD")',
        'print({f"{rc.value} {m.value}": round(v, 2) for (rc, m), v in risk.aggregate(("risk_class", "measure")).items()})',
        'print(f"SA-CCR EAD: {trade.calculate_saccr(md).ead:,.2f}")',
    ]
    return "```python\n" + "\n".join(lines) + "\n```"


def banner(cls, pricer: str) -> str:
    name = cls.__name__
    if pricer == "PLACEHOLDER":
        body = (f"> **Implementation status:** `{name}` currently uses **placeholder pricing** "
                "(`notional × discount factor × 1%`), so its PV and risk are not meaningful yet. "
                "It is on the roadmap for a real model.")
    elif pricer == "custom":
        body = (f"> **Implementation:** `{name}` has its own pricer and constructor arguments "
                f"(see the example and `help(qlrisk.products.python.{name})`).")
    else:
        body = (f"> **Implementation:** `{name}` is priced by `{pricer}` in `products/python/_pricing.py`. "
                f"Product terms are keyword arguments: {PRICER_TERMS[pricer][1]}. "
                "Market inputs come from `MarketData` (see [pricers](../../market_risk/pricers.md)).")
    return (f"{BEGIN}\n{body}\n>\n> The narrative below describes the instrument; the example in this page "
            f"is generated from the code (`scripts/gen_product_docs.py`) and is executed by the test suite.\n{END}")


def main() -> None:
    by_module = classes()
    count = 0
    for page in sorted(DOCS.rglob("*.md")):
        if page.parent == DOCS:
            continue
        module = ALIASES.get(page.stem, page.stem)
        cls = by_module.get(module)
        if cls is None:
            print("skip (no class):", page)
            continue
        pricer = pricer_of(cls)
        text = page.read_text()
        text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n\n?", "", text, flags=re.S)
        lines = text.split("\n", 1)
        text = lines[0] + "\n\n" + banner(cls, pricer) + "\n" + (lines[1] if len(lines) > 1 else "")
        ex = example(cls, module, pricer)
        if "```python" in text:
            text = re.sub(r"```python\n.*?```", lambda m: ex, text, count=1, flags=re.S)
        else:
            text = text.rstrip("\n") + "\n\n## Example\n\n" + ex + "\n"
        page.write_text(text)
        count += 1
    print(f"regenerated {count} product pages")


if __name__ == "__main__":
    main()
