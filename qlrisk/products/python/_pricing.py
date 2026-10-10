"""
QLRisk - Shared Analytic Pricers
================================

Market-data-driven pricers used by the simpler product modules. Each
pricer reads product terms from the constructor kwargs
(`product.additional_params`) with sensible defaults, and reads every
market input from MarketData, so all products respond to risk-factor
shocks.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import numpy as np
from scipy.stats import norm

from ..base import MarketData, PricingResult, curve_value


def _p(product, name, default=None):
    return product.additional_params.get(name, default)


def _ccy(product) -> str:
    return product.currency.value


def _t(product, md: MarketData) -> float:
    return max((product.maturity_date - md.valuation_date).days / 365.25, 0.0)


def _t_effective(product, md: MarketData) -> float:
    return max((product.effective_date - md.valuation_date).days / 365.25, 0.0)


def _sign(product) -> float:
    return 1.0 if _p(product, "is_long", True) else -1.0


def _rate(md: MarketData, t: float, curve_name=None) -> float:
    curve = md.forward_curves.get(curve_name, md.discount_curve) if curve_name else md.discount_curve
    return curve_value(curve, t)


def _df(md: MarketData, t: float, spread: float = 0.0, curve_name=None) -> float:
    return float(np.exp(-(_rate(md, t, curve_name) + spread) * t))


def _vol(md: MarketData, names, t: float, default: float) -> float:
    """First vol surface found among `names`: flat number or tenor -> vol term structure."""
    for name in names:
        surface = md.volatility_surfaces.get(name)
        if isinstance(surface, dict) and surface and all(not isinstance(v, dict) for v in surface.values()):
            return curve_value(surface, t)
        if isinstance(surface, (int, float)):
            return float(surface)
    return default


def _credit_spread(md: MarketData, name, t: float) -> float:
    curve = md.credit_curves.get(name) if name else None
    return curve_value(curve, t, 0.0) if curve else 0.0


def _zero(product) -> PricingResult:
    return PricingResult(npv=0.0, currency=_ccy(product))


def _black(fwd: float, strike: float, t: float, vol: float, is_call: bool) -> float:
    """Undiscounted Black-76 price."""
    if t <= 0 or vol <= 0:
        return max(fwd - strike, 0.0) if is_call else max(strike - fwd, 0.0)
    sd = vol * np.sqrt(t)
    d1 = (np.log(fwd / strike) + 0.5 * sd * sd) / sd
    d2 = d1 - sd
    if is_call:
        return fwd * norm.cdf(d1) - strike * norm.cdf(d2)
    return strike * norm.cdf(-d2) - fwd * norm.cdf(-d1)


def _schedule(t: float, frequency: int):
    """Payment times (years) from the end backwards; frequency 0 = single payment at t."""
    if t <= 0:
        return []
    if not frequency:
        return [t]
    step = 1.0 / frequency
    times = []
    s = t
    while s > 1e-9:
        times.append(s)
        s -= step
    return sorted(times)


# =============================================================================
# Fixed income and money market
# =============================================================================

def bond_pv(md: MarketData, t: float, coupon: float, frequency: int, spread: float = 0.0,
            curve_name=None, notional: float = 1.0, after: float = 0.0) -> float:
    """PV of a fixed-coupon bullet bond per `notional`; coupons at or before `after` (years) are excluded."""
    times = [s for s in _schedule(t, frequency) if s > after + 1e-9]
    if not times:
        return 0.0
    pv = notional * _df(md, t, spread, curve_name)
    if coupon:
        if frequency:
            pv += sum(notional * coupon / frequency * _df(md, s, spread, curve_name) for s in times)
        else:
            pv += notional * coupon * t * _df(md, t, spread, curve_name)
    return pv


def price_fixed_bond(product, md: MarketData) -> PricingResult:
    """
    Fixed-coupon bond, bill, note, CP, deposit.

    kwargs: coupon (default 0.0), frequency (2; 0 = pay at maturity),
            issuer (credit_curves key for spread), is_long (True)
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    spread = _credit_spread(md, _p(product, "issuer"), t)
    pv = bond_pv(md, t, _p(product, "coupon", 0.0), _p(product, "frequency", 2), spread,
                 notional=product.notional, after=_t_effective(product, md))
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product),
                         components={"maturity": t, "credit_spread": spread})


def price_deposit(product, md: MarketData) -> PricingResult:
    """Single-payment deposit / CD / discount note: kwargs rate (default 0.0), issuer, is_long."""
    product.additional_params.setdefault("frequency", 0)
    product.additional_params.setdefault("coupon", _p(product, "rate", 0.0))
    return price_fixed_bond(product, md)


def price_frn(product, md: MarketData) -> PricingResult:
    """
    Floating-rate note on a forward curve.

    kwargs: index (forward_curves key, default 'SOFR'), spread (quoted margin, 0.0),
            frequency (4), issuer, is_long
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    freq = _p(product, "frequency", 4)
    index, margin = _p(product, "index", "SOFR"), _p(product, "spread", 0.0)
    credit = _credit_spread(md, _p(product, "issuer"), t)
    times = _schedule(t, freq)
    pv, prev = 0.0, 0.0
    for s in times:
        tau = s - prev
        df0 = _df(md, prev, curve_name=index) if prev > 0 else 1.0
        fwd = (df0 / _df(md, s, curve_name=index) - 1.0) / tau
        pv += (fwd + margin) * tau * _df(md, s, credit)
        prev = s
    pv = product.notional * (pv + _df(md, t, credit))
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product))


# =============================================================================
# Cash equity and funds
# =============================================================================

def price_cash_equity(product, md: MarketData) -> PricingResult:
    """
    Stock / ETF / fund / index position.

    kwargs: ticker (equity_prices key), quantity (default notional / price), is_long.
    Falls back to notional when the ticker has no price.
    """
    ticker = _p(product, "ticker")
    price = md.equity_prices.get(ticker) if ticker else None
    if price is None:
        return PricingResult(npv=_sign(product) * product.notional, currency=_ccy(product))
    qty = _p(product, "quantity")
    if qty is None:
        qty = product.notional / price
        product.additional_params["quantity"] = qty     # fix position size at first pricing
    return PricingResult(npv=_sign(product) * qty * price, currency=_ccy(product),
                         components={"price": price, "quantity": qty})


# =============================================================================
# Options and forwards
# =============================================================================

def _equity_inputs(product, md: MarketData, t: float):
    ticker = _p(product, "ticker", "SPX")
    spot = md.equity_prices.get(ticker, _p(product, "spot", 100.0))
    div_curve = md.dividend_curves.get(ticker)
    q = curve_value(div_curve, t, 0.0) if div_curve else 0.0
    return ticker, spot, q


def price_equity_option(product, md: MarketData) -> PricingResult:
    """
    European equity option / warrant (Black-Scholes with dividend yield).

    kwargs: ticker, strike (default spot at first pricing), is_call (True),
            quantity (default notional / strike), is_long
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    ticker, spot, q = _equity_inputs(product, md, t)
    strike = product.additional_params.setdefault("strike", spot)
    qty = product.additional_params.setdefault("quantity", product.notional / strike)
    vol = _vol(md, [f"{ticker}_vol", "eq_vol"], t, 0.20)
    r = _rate(md, t)
    fwd = spot * np.exp((r - q) * t)
    pv = qty * np.exp(-r * t) * _black(fwd, strike, t, vol, _p(product, "is_call", True))
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product),
                         components={"spot": spot, "strike": strike, "vol": vol, "forward": fwd})


def price_equity_forward(product, md: MarketData) -> PricingResult:
    """Equity forward / single-stock or index future: kwargs ticker, strike, quantity, is_long."""
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    ticker, spot, q = _equity_inputs(product, md, t)
    r = _rate(md, t)
    fwd = spot * np.exp((r - q) * t)
    strike = product.additional_params.setdefault("strike", fwd)
    qty = product.additional_params.setdefault("quantity", product.notional / strike)
    discount = 1.0 if _p(product, "is_future", False) else np.exp(-r * t)
    return PricingResult(npv=_sign(product) * qty * (fwd - strike) * discount, currency=_ccy(product),
                         components={"forward": fwd, "strike": strike})


def _fx_inputs(product, md: MarketData, t: float):
    pair = _p(product, "pair", f"{product.currency.value}USD" if product.currency.value != "USD" else "EURUSD")
    spot = md.fx_spots.get(pair, _p(product, "spot", 1.0))
    r_d = _rate(md, t, _p(product, "domestic_curve"))
    foreign = _p(product, "foreign_curve")
    r_f = _rate(md, t, foreign) if foreign in md.forward_curves else _p(product, "foreign_rate", 0.0)
    return pair, spot, r_d, r_f


def price_fx_option(product, md: MarketData) -> PricingResult:
    """
    FX vanilla (Garman-Kohlhagen); PV in the quote (domestic) currency.

    kwargs: pair ('EURUSD'), strike (default forward), is_call, foreign_curve / foreign_rate,
            notional = base-currency amount, is_long; digital: payout (quote ccy, default notional)
    """
    if product.is_expired(md.valuation_date):
        return PricingResult(npv=0.0, currency="USD")
    t = _t(product, md)
    pair, spot, r_d, r_f = _fx_inputs(product, md, t)
    fwd = spot * np.exp((r_d - r_f) * t)
    strike = product.additional_params.setdefault("strike", fwd)
    vol = _vol(md, [f"{pair}_vol", "fx_vol"], t, 0.10)
    is_call = _p(product, "is_call", True)
    df = np.exp(-r_d * t)
    if _p(product, "digital", False):
        sd = vol * np.sqrt(t)
        d2 = (np.log(fwd / strike) - 0.5 * sd * sd) / sd
        pv = _p(product, "payout", product.notional) * df * norm.cdf(d2 if is_call else -d2)
    else:
        pv = product.notional * df * _black(fwd, strike, t, vol, is_call)
    return PricingResult(npv=_sign(product) * pv, currency=pair[3:],
                         components={"spot": spot, "forward": fwd, "strike": strike, "vol": vol})


def price_fx_digital(product, md: MarketData) -> PricingResult:
    product.additional_params["digital"] = True
    return price_fx_option(product, md)


def price_fx_barrier(product, md: MarketData) -> PricingResult:
    """
    FX barrier option via QuantLib's analytic barrier engine.

    kwargs: as price_fx_option plus barrier (default 1.1 x spot for up, 0.9 x for down),
            barrier_type ('UpOut', 'UpIn', 'DownOut', 'DownIn'; default 'UpOut'), rebate (0)
    """
    import QuantLib as ql
    if product.is_expired(md.valuation_date):
        return PricingResult(npv=0.0, currency="USD")
    t = _t(product, md)
    pair, spot, r_d, r_f = _fx_inputs(product, md, t)
    fwd = spot * np.exp((r_d - r_f) * t)
    strike = product.additional_params.setdefault("strike", fwd)
    btype = _p(product, "barrier_type", "UpOut")
    barrier = product.additional_params.setdefault("barrier", spot * (1.1 if btype.startswith("Up") else 0.9))
    vol = _vol(md, [f"{pair}_vol", "fx_vol"], t, 0.10)

    today = ql.Date(md.valuation_date.day, md.valuation_date.month, md.valuation_date.year)
    ql.Settings.instance().evaluationDate = today
    expiry = today + max(int(round(t * 365.25)), 1)
    dc = ql.Actual365Fixed()
    process = ql.GarmanKohlagenProcess(
        ql.QuoteHandle(ql.SimpleQuote(spot)),
        ql.YieldTermStructureHandle(ql.FlatForward(today, r_f, dc)),
        ql.YieldTermStructureHandle(ql.FlatForward(today, r_d, dc)),
        ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, ql.NullCalendar(), vol, dc)),
    )
    option = ql.BarrierOption(
        getattr(ql.Barrier, btype), barrier, _p(product, "rebate", 0.0),
        ql.PlainVanillaPayoff(ql.Option.Call if _p(product, "is_call", True) else ql.Option.Put, strike),
        ql.EuropeanExercise(expiry),
    )
    option.setPricingEngine(ql.AnalyticBarrierEngine(process))
    pv = product.notional * option.NPV()
    return PricingResult(npv=_sign(product) * pv, currency=pair[3:],
                         components={"spot": spot, "barrier": barrier, "strike": strike, "vol": vol})


def price_fx_ndf(product, md: MarketData) -> PricingResult:
    """NDF settled in USD: kwargs pair, forward_rate (strike), is_long (buy base)."""
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    pair, spot, r_d, r_f = _fx_inputs(product, md, t)
    fwd = spot * np.exp((r_d - r_f) * t)
    strike = product.additional_params.setdefault("forward_rate", fwd)
    pv = product.notional * (fwd - strike) * np.exp(-r_d * t)
    return PricingResult(npv=_sign(product) * pv, currency=pair[3:], components={"forward": fwd})


# =============================================================================
# Credit
# =============================================================================

def price_cds(product, md: MarketData) -> PricingResult:
    """
    Single-name / index CDS (credit-triangle hazard rate, quarterly premium).

    kwargs: reference (credit_curves key), coupon (running spread, default 0.01),
            recovery (0.4), is_buyer (protection buyer, True)
    PV is from the protection buyer's side when is_buyer.
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    recovery = _p(product, "recovery", 0.4)
    spread = _credit_spread(md, _p(product, "reference"), t) or _p(product, "coupon", 0.01)
    hazard = spread / (1.0 - recovery)
    coupon = _p(product, "coupon", 0.01)
    times = _schedule(t, 4)
    protection = annuity = 0.0
    prev = 0.0
    for s in times:
        df = _df(md, s)
        surv_prev, surv = np.exp(-hazard * prev), np.exp(-hazard * s)
        protection += (1.0 - recovery) * (surv_prev - surv) * df
        annuity += (s - prev) * surv * df
        prev = s
    pv = product.notional * (protection - coupon * annuity)
    sign = 1.0 if _p(product, "is_buyer", True) else -1.0
    return PricingResult(npv=sign * pv, currency=_ccy(product),
                         components={"par_spread": protection / annuity if annuity else 0.0,
                                     "risky_annuity": annuity, "hazard_rate": hazard})


# =============================================================================
# Commodity
# =============================================================================

def _commodity_forward(product, md: MarketData, t: float):
    name = _p(product, "commodity", "WTI")
    spot = md.commodity_prices.get(name, _p(product, "spot", 75.0))
    r = _rate(md, t)
    return name, spot, spot * np.exp((r - _p(product, "convenience_yield", 0.0)) * t), r


def price_commodity_forward(product, md: MarketData) -> PricingResult:
    """kwargs: commodity (commodity_prices key), strike, quantity, convenience_yield, is_long."""
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    _, _, fwd, r = _commodity_forward(product, md, t)
    strike = product.additional_params.setdefault("strike", fwd)
    qty = product.additional_params.setdefault("quantity", product.notional / strike)
    return PricingResult(npv=_sign(product) * qty * (fwd - strike) * np.exp(-r * t), currency=_ccy(product),
                         components={"forward": fwd})


def price_commodity_swap(product, md: MarketData) -> PricingResult:
    """Fixed-for-floating swap on monthly average forwards: kwargs as commodity forward."""
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    name = _p(product, "commodity", "WTI")
    spot = md.commodity_prices.get(name, _p(product, "spot", 75.0))
    cy = _p(product, "convenience_yield", 0.0)
    times = _schedule(t, 12)
    fwds = [spot * np.exp((_rate(md, s) - cy) * s) for s in times]
    dfs = [_df(md, s) for s in times]
    strike = product.additional_params.setdefault("strike", float(np.dot(fwds, dfs) / sum(dfs)))
    qty = product.additional_params.setdefault("quantity", product.notional / strike / len(times))
    pv = sum(qty * (f - strike) * df for f, df in zip(fwds, dfs))
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product))


def price_commodity_option(product, md: MarketData) -> PricingResult:
    """Black-76 on the commodity forward: kwargs commodity, strike, is_call, quantity, is_long."""
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    name, _, fwd, r = _commodity_forward(product, md, t)
    strike = product.additional_params.setdefault("strike", fwd)
    qty = product.additional_params.setdefault("quantity", product.notional / strike)
    vol = _vol(md, [f"{name}_vol", "cm_vol", "commodity_vol"], t, 0.30)
    pv = qty * np.exp(-r * t) * _black(fwd, strike, t, vol, _p(product, "is_call", True))
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product), components={"forward": fwd, "vol": vol})


# =============================================================================
# Cross currency
# =============================================================================

def price_xccy_swap(product, md: MarketData) -> PricingResult:
    """
    Fixed-for-fixed cross-currency swap with notional exchange at maturity.

    Receive domestic leg (product.currency, discount_curve), pay foreign leg
    (foreign_curve in forward_curves) converted at fx_spots[pair].
    kwargs: pair ('EURUSD' = foreign/domestic), foreign_curve ('ESTR'), domestic_coupon,
            foreign_coupon (default: par-ish 0), foreign_notional (default notional / spot at
            first pricing), frequency (2), is_long (receive domestic)
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    freq = _p(product, "frequency", 2)
    pair = _p(product, "pair", "EURUSD")
    spot = md.fx_spots.get(pair, 1.0)
    f_curve = _p(product, "foreign_curve", "ESTR")
    f_notional = product.additional_params.setdefault("foreign_notional", product.notional / spot)
    dom = bond_pv(md, t, _p(product, "domestic_coupon", _rate(md, t)), freq, notional=product.notional)
    fgn = bond_pv(md, t, _p(product, "foreign_coupon", _rate(md, t, f_curve)), freq,
                  curve_name=f_curve, notional=f_notional)
    return PricingResult(npv=_sign(product) * (dom - fgn * spot), currency=_ccy(product),
                         components={"domestic_leg": dom, "foreign_leg_domestic": fgn * spot})


# =============================================================================
# Futures
# =============================================================================

def _futures_qty(product, price: float) -> float:
    return product.additional_params.setdefault("quantity", product.notional / price)


def price_ir_future(product, md: MarketData) -> PricingResult:
    """
    Short-term interest-rate future (e.g. 3M SOFR): price = 100 x (1 - forward rate over
    [T, T + tenor]); P&L = notional x tenor x (rate at trade - forward rate) per unit of price move.
    kwargs: index ('SOFR'), tenor (0.25), strike (traded price, default fair), is_long
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t, tau = _t(product, md), _p(product, "tenor", 0.25)
    index = _p(product, "index", "SOFR")
    fwd = (_df(md, t, curve_name=index) / _df(md, t + tau, curve_name=index) - 1.0) / tau
    price = 100.0 * (1.0 - fwd)
    strike = product.additional_params.setdefault("strike", price)
    pv = product.notional * tau * (price - strike) / 100.0
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product), components={"price": price, "forward_rate": fwd})


def price_bond_future(product, md: MarketData) -> PricingResult:
    """
    Bond future on a single (cheapest-to-deliver) bond: F = forward clean-ish price / conversion factor.
    kwargs: bond_coupon (0.06), bond_maturity_years (10 after delivery), conversion_factor (1.0),
            strike (default fair), is_long. Notional is face value; no discounting (daily margin).
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    coupon, life = _p(product, "bond_coupon", 0.06), _p(product, "bond_maturity_years", 10.0)
    full = bond_pv(md, t + life, coupon, 2) - bond_pv(md, t, coupon, 2) + _df(md, t)   # cash flows after delivery
    fwd_price = 100.0 * full / _df(md, t) / _p(product, "conversion_factor", 1.0)
    strike = product.additional_params.setdefault("strike", fwd_price)
    pv = product.notional * (fwd_price - strike) / 100.0
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product), components={"futures_price": fwd_price})


def _forward_vol(md: MarketData, names, t1: float, t2: float, default: float) -> float:
    v1, v2 = _vol(md, names, max(t1, 1e-6), default), _vol(md, names, t2, default)
    var = (v2 * v2 * t2 - v1 * v1 * t1) / (t2 - t1)
    return float(np.sqrt(max(var, 1e-8)))


def price_vix_future(product, md: MarketData) -> PricingResult:
    """
    VIX future = 100 x forward 30-day implied volatility of the index at expiry
    (from the equity vol term structure). kwargs: ticker ('SPX'), strike (default fair), quantity, is_long
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    ticker = _p(product, "ticker", "SPX")
    level = 100.0 * _forward_vol(md, [f"{ticker}_vol", "eq_vol"], t, t + 30 / 365.0, 0.18)
    strike = product.additional_params.setdefault("strike", level)
    qty = _futures_qty(product, strike)
    return PricingResult(npv=_sign(product) * qty * (level - strike), currency=_ccy(product), components={"vix_forward": level})


# =============================================================================
# Equity derivatives
# =============================================================================

def price_variance_swap(product, md: MarketData) -> PricingResult:
    """
    Variance swap (no realised variance yet): PV = N_var x (sigma_imp^2 - K^2) x DF, N_var = vega_notional / (2K).
    kwargs: ticker ('SPX'), strike (vol, default ATM implied), vega_notional (default notional), is_long
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    ticker = _p(product, "ticker", "SPX")
    sigma = _vol(md, [f"{ticker}_vol", "eq_vol"], t, 0.20)
    k = product.additional_params.setdefault("strike", sigma)
    n_var = _p(product, "vega_notional", product.notional) / (2.0 * k)
    pv = n_var * (sigma * sigma - k * k) * 100.0 * _df(md, t)          # vol points convention: (100 sigma)^2 / 100
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product), components={"implied_vol": sigma, "strike": k})


def price_dividend_swap(product, md: MarketData) -> PricingResult:
    """
    Dividend swap: receive dividends paid until maturity, pay fixed K.
    Expected dividends = S x (1 - exp(-q T)) per share. kwargs: ticker, strike (default fair), quantity, is_long
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    ticker, spot, q = _equity_inputs(product, md, t)
    divs = spot * (1.0 - np.exp(-q * t))
    strike = product.additional_params.setdefault("strike", divs)
    qty = product.additional_params.setdefault("quantity", product.notional / spot)
    return PricingResult(npv=_sign(product) * qty * (divs - strike) * _df(md, t), currency=_ccy(product),
                         components={"expected_dividends": divs})


def price_total_return(product, md: MarketData) -> PricingResult:
    """
    Funded total-return swap: receive the total return of the underlying, pay floating + spread on
    the initial notional. PV = qty x (S - S0) - N x spread x annuity.
    Underlying: `ticker` (equity) or, if `issuer` is given, a bond (coupon, issuer) valued per unit notional.
    kwargs: ticker / issuer + coupon, spread (0.0), initial_price (fixed at first pricing), is_long (receive TR)
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    if _p(product, "issuer"):
        price = bond_pv(md, t, _p(product, "coupon", 0.05), 2, _credit_spread(md, _p(product, "issuer"), t))
    else:
        price = _equity_inputs(product, md, t)[1]
    s0 = product.additional_params.setdefault("initial_price", price)
    qty = product.notional / s0
    annuity = sum(0.25 * _df(md, s) for s in _schedule(t, 4))
    pv = qty * (price - s0) - product.notional * _p(product, "spread", 0.0) * annuity
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product), components={"underlying_price": price})


def price_convertible(product, md: MarketData) -> PricingResult:
    """
    Convertible bond = straight bond (coupon, issuer spread) + conversion_ratio x European call on the stock
    with strike notional / conversion_ratio. kwargs: coupon (0.02), issuer, ticker ('AAPL'),
    conversion_ratio (default: notional / (1.3 x spot), a 30% conversion premium), is_long
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    bond = bond_pv(md, t, _p(product, "coupon", 0.02), 2, _credit_spread(md, _p(product, "issuer"), t),
                   notional=product.notional, after=_t_effective(product, md))
    ticker, spot, q = _equity_inputs(product, md, t)
    ratio = product.additional_params.setdefault("conversion_ratio", product.notional / (1.3 * spot))
    strike = product.notional / ratio
    r = _rate(md, t)
    vol = _vol(md, [f"{ticker}_vol", "eq_vol"], t, 0.25)
    option = ratio * np.exp(-r * t) * _black(spot * np.exp((r - q) * t), strike, t, vol, True)
    return PricingResult(npv=_sign(product) * (bond + option), currency=_ccy(product),
                         components={"bond_floor": bond, "conversion_option": option})


# =============================================================================
# Securitised products
# =============================================================================

def _pass_through(md: MarketData, t: float, coupon: float, cpr: float, spread: float, notional: float) -> float:
    """Monthly level-pay pool with constant CPR; cash flows discounted at r(t) + spread."""
    n = max(int(round(t * 12)), 1)
    rate, smm = coupon / 12.0, 1.0 - (1.0 - cpr) ** (1.0 / 12.0)
    balance, pv = notional, 0.0
    for k in range(1, n + 1):
        remaining = n - k + 1
        payment = balance * rate / (1.0 - (1.0 + rate) ** -remaining) if rate > 0 else balance / remaining
        interest = balance * rate
        scheduled = payment - interest
        prepay = (balance - scheduled) * smm
        pv += (interest + scheduled + prepay) * _df(md, k / 12.0, spread)
        balance -= scheduled + prepay
    return pv


def price_mbs(product, md: MarketData) -> PricingResult:
    """
    Agency MBS pass-through with rate-dependent prepayment (negative convexity):
    CPR = clip(base_cpr + refi_multiplier x max(wac - r10y, 0), 0, 60%).
    kwargs: coupon (0.055), wac (coupon + 0.5%), base_cpr (0.06), refi_multiplier (8), oas (0.005), is_long
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    coupon = _p(product, "coupon", 0.055)
    wac = _p(product, "wac", coupon + 0.005)
    incentive = max(wac - _rate(md, 10.0), 0.0)
    cpr = min(max(_p(product, "base_cpr", 0.06) + _p(product, "refi_multiplier", 8.0) * incentive, 0.0), 0.60)
    pv = _pass_through(md, t, coupon, cpr, _p(product, "oas", 0.005), product.notional)
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product), components={"cpr": cpr})


def price_abs(product, md: MarketData) -> PricingResult:
    """Amortising ABS with constant CPR, discounted at r(t) + issuer credit spread (or `spread`).
    kwargs: coupon (0.05), cpr (0.10), issuer, spread (0.01 if no issuer), is_long"""
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    spread = _credit_spread(md, _p(product, "issuer"), t) if _p(product, "issuer") else _p(product, "spread", 0.01)
    pv = _pass_through(md, t, _p(product, "coupon", 0.05), _p(product, "cpr", 0.10), spread, product.notional)
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product), components={"spread": spread})


_GH_X, _GH_W = np.polynomial.hermite_e.hermegauss(48)
_GH_W = _GH_W / _GH_W.sum()


def _tranche_expected_loss(pd: float, rho: float, recovery: float, attach: float, detach: float) -> float:
    """Vasicek large homogeneous pool: E[min(max(L - A, 0), D - A)] / (D - A)."""
    if pd <= 0:
        return 0.0
    from scipy.stats import norm as _n
    c = _n.ppf(min(pd, 1 - 1e-12))
    cond_pd = _n.cdf((c - np.sqrt(rho) * _GH_X) / np.sqrt(1 - rho))
    loss = (1 - recovery) * cond_pd
    tranche = np.clip(loss - attach, 0.0, detach - attach)
    return float(np.dot(_GH_W, tranche) / (detach - attach))


def price_tranche(product, md: MarketData) -> PricingResult:
    """
    CDO / CLO tranche (investor side) under the Vasicek large-pool model: a risky floating-coupon bond
    whose notional decays with the expected tranche loss.
    kwargs: pool (credit_curves key; hazard = spread / (1 - recovery)), attachment, detachment,
            correlation, recovery (0.4), coupon (tranche spread over the curve), is_long
    Defaults: CDO mezzanine 3-7% / rho 0.30 / pool GLOBEX; CLO BBB 7-10% / rho 0.25 (set by product module).
    """
    if product.is_expired(md.valuation_date):
        return _zero(product)
    t = _t(product, md)
    rec, rho = _p(product, "recovery", 0.4), _p(product, "correlation", 0.30)
    a, d = _p(product, "attachment", 0.03), _p(product, "detachment", 0.07)
    hazard = _credit_spread(md, _p(product, "pool", "GLOBEX"), t) / (1 - rec)
    spread = _p(product, "coupon", 0.03)
    pv, prev = 0.0, 0.0
    for s in _schedule(t, 4):
        surv = 1.0 - _tranche_expected_loss(1 - np.exp(-hazard * s), rho, rec, a, d)
        pv += (_rate(md, s) + spread) * (s - prev) * surv * _df(md, s)
        prev = s
    final = 1.0 - _tranche_expected_loss(1 - np.exp(-hazard * t), rho, rec, a, d)
    pv = product.notional * (pv + final * _df(md, t))
    return PricingResult(npv=_sign(product) * pv, currency=_ccy(product),
                         components={"expected_tranche_loss": 1 - final, "attachment": a, "detachment": d})


def price_clo_tranche(product, md: MarketData) -> PricingResult:
    for k, v in {"attachment": 0.07, "detachment": 0.10, "correlation": 0.25, "coupon": 0.035}.items():
        product.additional_params.setdefault(k, v)
    return price_tranche(product, md)
