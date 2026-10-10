"""
QLRisk - Market Risk and FRTB Demos (qlrisk --market-risk / --frtb)
===================================================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from datetime import date


def demo_book():
    """A small multi-asset book, sample market data, a synthetic history and a hierarchy."""
    from .data import MarketHistoryGenerator, create_sample_market_data
    from .products.base import Currency
    from .reporting import Hierarchy
    from . import products
    P = products.python
    md = create_sample_market_data(date.today())
    d0 = md.valuation_date
    y = lambda n: date(d0.year + n, d0.month, min(d0.day, 28))
    book = [
        P.InterestRateSwap("IRS-10Y", d0, d0, y(10), 25e6, Currency.USD, "BANK-A", fixed_rate=0.043),
        P.CorporateBond("ACME-5Y", d0, d0, y(5), 10e6, Currency.USD, "ACME", coupon=0.05, issuer="ACME"),
        P.CreditDefaultSwap("GLX-CDS", d0, d0, y(5), 5e6, Currency.USD, "BANK-B", reference="GLOBEX"),
        P.FXOption("EURUSD-C", d0, d0, y(1), 10e6, Currency.EUR, "BANK-B", pair="EURUSD", strike=1.12),
        P.EquityOption("SPX-P", d0, d0, y(1), 5e6, Currency.USD, "BANK-A", ticker="SPX", strike=5000.0, is_call=False),
        P.CommodityForward("WTI-F", d0, d0, y(1), 5e6, Currency.USD, "BANK-C", commodity="WTI", strike=72.0),
    ]
    history = MarketHistoryGenerator(seed=7).generate(md, num_days=750, stress_start=300, stress_days=60)
    tree = Hierarchy({"IRS-10Y": ("BankCo", "Rates"), "ACME-5Y": ("BankCo", "Credit"), "GLX-CDS": ("BankCo", "Credit"),
                      "EURUSD-C": ("BankCo", "FX"), "SPX-P": ("BankCo", "Equity"), "WTI-F": ("BankCo", "Commodities")})
    frtb = dict(credit_buckets={"ACME": 4, "GLOBEX": 12}, equity_buckets={"SPX": 12},
                ratings={"ACME": "BBB", "GLOBEX": "BB"}, vol_underlyings={"eq_vol": "SPX", "fx_vol": "EURUSD"})
    return book, md, history, tree, frtb


def run_market_risk_demo() -> None:
    from .engine import RiskEngine
    from .reporting import RiskLimit
    book, md, history, tree, frtb = demo_book()
    engine = RiskEngine.from_config()
    report = engine.run(book, md, history, measures=("PV", "SENSITIVITIES", "VAR", "ES", "SVAR", "STRESS", "BACKTEST"),
                        hierarchy=tree, limits=[RiskLimit("Firm 1d VaR", "var.1d", 1_500_000),
                                                RiskLimit("Rates 1d VaR", "var.1d", 1_000_000, node="BankCo/Rates")])
    print(report)
    print("\nVaR by node (non-additive):")
    for node, vals in report.by_node.items():
        if "var.1d" in vals:
            print(f"  {node:22} {vals['var.1d']:>14,.0f}")
    print("\nLimits:")
    for check in report.results["limits"]:
        print(" ", check)


def run_frtb_demo() -> None:
    from .engine import RiskEngine
    book, md, history, tree, frtb = demo_book()
    report = RiskEngine.from_config().run(book, md, history, measures=("FRTB_SA",), hierarchy=tree, frtb=frtb)
    for k, v in report.metrics.items():
        print(f"  {k:28} {v:>14,.0f}")
    print("\n".join(report.notes))


__all__ = ["demo_book", "run_market_risk_demo", "run_frtb_demo"]
