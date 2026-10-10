"""
QLRisk - Synthetic Market Data and History
==========================================

Sample products.base.MarketData for demos and tests, and synthetic
correlated risk-factor histories (with an optional stress regime) that end
exactly at a given market-data snapshot.

    from qlrisk.data import create_sample_market_data, MarketHistoryGenerator

    md = create_sample_market_data()
    history = MarketHistoryGenerator(seed=7).generate(md, num_days=750, stress_start=200, stress_days=60)
    dates, returns = history.returns(horizon=10)

Return model (per business day, factor i in risk class c on curve k):

    r_i = vol_i * s_t * ( w_g * load_c * G_t + w_c * Z_c,t + w_k * C_k,t + w_e * e_i,t )

G, Z, C, e are independent unit-variance Student-t draws (fat tails),
load_c gives each risk class its sign in a sell-off (equities down, spreads
and vols up, rates down), s_t is the stress volatility multiplier, and in
the stress window G also drifts negative.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from datetime import date, timedelta
from typing import Dict, List, Mapping, Optional

import numpy as np

from ..products.base import MarketData
from ..riskfactors.mapping import enumerate_risk_factors, get_factor_value
from ..riskfactors.shocks import ShockType
from ..riskfactors.taxonomy import FactorKind, RiskClass, RiskFactorKey
from ..riskfactors.timeseries import DEFAULT_RETURN_TYPES, RiskFactorTimeSeries, apply_return

_STANDARD_PILLARS = (0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0)


def _curve(short: float, long: float, pillars=_STANDARD_PILLARS) -> Dict[float, float]:
    """Smooth upward-sloping curve from `short` to `long` (Nelson-Siegel-like shape)."""
    return {t: long + (short - long) * (1 - np.exp(-t / 3.0)) / (t / 3.0) for t in pillars}


def create_sample_market_data(valuation_date: Optional[date] = None) -> MarketData:
    """
    A realistic multi-asset MarketData snapshot for demos and tests.

    Contains USD discounting, SOFR / ESTR / SONIA forward curves, reference
    rates, FX spots, IR / FX / equity volatilities, credit curves, equity
    prices with dividend curves, and bond prices.
    """
    md = MarketData(
        valuation_date=valuation_date or date.today(),
        discount_curve=_curve(0.0430, 0.0420),
        forward_curves={
            "SOFR": _curve(0.0435, 0.0425),
            "ESTR": _curve(0.0300, 0.0270),
            "SONIA": _curve(0.0450, 0.0410),
        },
        fx_spots={"EURUSD": 1.0850, "GBPUSD": 1.2700, "USDJPY": 149.50},
        volatility_surfaces={
            "swaption_vol": 0.20,
            "cap_vol": {1.0: 0.22, 2.0: 0.21, 5.0: 0.19, 10.0: 0.18},
            "floor_vol": 0.20,
            "ir_vol": 0.010,
            "fx_vol": 0.09,
            "eq_vol": {0.25: 0.21, 0.5: 0.20, 1.0: 0.19, 2.0: 0.185},
            "cm_vol": 0.32,
        },
        credit_curves={
            "ACME": {1.0: 0.0080, 3.0: 0.0100, 5.0: 0.0120, 10.0: 0.0140},
            "GLOBEX": {1.0: 0.0150, 3.0: 0.0190, 5.0: 0.0220, 10.0: 0.0250},
            "INITECH": {1.0: 0.0040, 3.0: 0.0055, 5.0: 0.0065, 10.0: 0.0080},
        },
        dividend_curves={
            "AAPL": {1.0: 0.0050, 5.0: 0.0055},
            "SPX": {1.0: 0.0140, 5.0: 0.0150},
        },
        equity_prices={"AAPL": 190.0, "MSFT": 410.0, "SPX": 5200.0},
        bond_prices={"UST10Y": 98.50, "ACME_2030": 101.25},
        reference_rates={"SOFR": 0.0433, "ESTR": 0.0290, "SONIA": 0.0470},
        commodity_prices={"WTI": 78.0, "BRENT": 82.0, "GOLD": 2350.0, "NATGAS": 2.8},
    )
    return md


# Simulation dynamics per factor kind. Spreads and dividend yields are simulated
# in log space so they stay positive; their VaR return convention is unaffected.
_SIM_RETURN_TYPES: Dict[FactorKind, ShockType] = {
    **DEFAULT_RETURN_TYPES,
    FactorKind.SPREAD: ShockType.LOG,
    FactorKind.DIVIDEND: ShockType.LOG,
}

# Daily volatility by factor kind, in the units of _SIM_RETURN_TYPES (absolute or log).
DEFAULT_DAILY_VOLS: Dict[FactorKind, float] = {
    FactorKind.RATE: 0.0006,        # 6bp / day
    FactorKind.SPREAD: 0.0250,      # 2.5% of the spread level / day
    FactorKind.DIVIDEND: 0.0100,
    FactorKind.SCALAR: 0.0006,
    FactorKind.SPOT: 0.0060,        # 0.6% / day
    FactorKind.PRICE: 0.0120,       # 1.2% / day
    FactorKind.VOLATILITY: 0.0300,  # 3% / day of the vol level
}

# Sign of each risk class's move when the global factor falls (risk-off).
_GLOBAL_LOADING: Dict[RiskClass, float] = {
    RiskClass.EQUITY: 1.0,
    RiskClass.CREDIT: -1.0,
    RiskClass.INTEREST_RATE: 0.6,
    RiskClass.FX: 0.4,
    RiskClass.COMMODITY: 0.7,
    RiskClass.OTHER: 0.3,
}


def _business_days(end: date, count: int) -> List[date]:
    days: List[date] = []
    d = end
    while len(days) < count:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return days[::-1]


class MarketHistoryGenerator:
    """
    Generates correlated, fat-tailed risk-factor histories.

    Args:
        seed: Random seed (reproducible output)
        daily_vols: Per-FactorKind overrides of DEFAULT_DAILY_VOLS
        tail_dof: Student-t degrees of freedom for all shocks (None = Gaussian)
        global_weight / class_weight / curve_weight: Factor loadings (see module docstring)
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        daily_vols: Optional[Mapping[FactorKind, float]] = None,
        tail_dof: Optional[float] = 5.0,
        global_weight: float = 0.50,
        class_weight: float = 0.45,
        curve_weight: float = 0.70,
    ):
        self.rng = np.random.default_rng(seed)
        self.daily_vols = {**DEFAULT_DAILY_VOLS, **(daily_vols or {})}
        self.tail_dof = tail_dof
        self.global_weight = global_weight
        self.class_weight = class_weight
        self.curve_weight = curve_weight

    def _draw(self, *shape: int) -> np.ndarray:
        if self.tail_dof is None:
            return self.rng.standard_normal(shape)
        dof = self.tail_dof
        return self.rng.standard_t(dof, size=shape) * np.sqrt((dof - 2.0) / dof)

    def generate(
        self,
        market_data: MarketData,
        num_days: int = 500,
        end_date: Optional[date] = None,
        stress_start: Optional[int] = None,
        stress_days: int = 0,
        stress_vol_multiplier: float = 3.0,
        stress_drift: float = 0.35,
        factors: Optional[List[RiskFactorKey]] = None,
    ) -> RiskFactorTimeSeries:
        """
        Simulate a history whose last observation equals `market_data`.

        Args:
            market_data: Snapshot the history ends at
            num_days: Number of business-day observations
            end_date: Last date (default market_data.valuation_date)
            stress_start: Row index where the stress regime begins (None = no stress)
            stress_days: Length of the stress regime in observations
            stress_vol_multiplier: Volatility scale inside the stress regime
            stress_drift: Daily negative drift of the global factor (in its std units) during stress
            factors: Factors to simulate (default: all in market_data)

        Returns:
            RiskFactorTimeSeries of shape (num_days, n_factors)
        """
        if num_days < 2:
            raise ValueError("num_days must be >= 2")
        keys = factors or enumerate_risk_factors(market_data)
        dates = _business_days(end_date or market_data.valuation_date, num_days)
        n_ret = num_days - 1

        scale = np.ones(n_ret)
        drift = np.zeros(n_ret)
        if stress_start is not None and stress_days > 0:
            window = slice(max(0, stress_start - 1), min(n_ret, stress_start - 1 + stress_days))
            scale[window] = stress_vol_multiplier
            drift[window] = -stress_drift

        g = self._draw(n_ret) + drift
        classes = sorted({k.risk_class for k in keys}, key=lambda c: c.value)
        class_z = {c: self._draw(n_ret) for c in classes}
        curves = sorted({k.curve_id for k in keys if k.tenor is not None}, key=str)
        curve_z = {c: self._draw(n_ret) for c in curves}

        levels = np.empty((num_days, len(keys)))
        for col, key in enumerate(keys):
            base = get_factor_value(market_data, key)
            vol = self.daily_vols[key.kind]
            loading = _GLOBAL_LOADING[key.risk_class]
            class_sign = 1.0
            if key.kind is FactorKind.VOLATILITY:
                loading = -abs(loading)             # vols rise in a sell-off...
                class_sign = -1.0                   # ...and move against their underlying
            elif key.field == "bond_prices":
                loading = 0.2                       # mixed: govvies rally, credit sells off
            w_curve = self.curve_weight if key.tenor is not None else 0.0
            w_idio = np.sqrt(max(0.0, 1.0 - self.global_weight ** 2 - self.class_weight ** 2 - w_curve ** 2))
            shock = (self.global_weight * loading * g
                     + self.class_weight * class_sign * class_z[key.risk_class]
                     + (w_curve * curve_z[key.curve_id] if w_curve else 0.0)
                     + w_idio * self._draw(n_ret))
            returns = vol * scale * shock
            return_type = _SIM_RETURN_TYPES[key.kind]

            levels[-1, col] = base
            for t in range(n_ret - 1, -1, -1):      # walk back from today's level
                levels[t, col] = apply_return(levels[t + 1, col], returns[t], return_type, inverse=True)

        return RiskFactorTimeSeries(dates, keys, levels)


__all__ = ["create_sample_market_data", "MarketHistoryGenerator", "DEFAULT_DAILY_VOLS"]
