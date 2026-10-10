"""
QLRisk - Expected Shortfall Backtesting (Acerbi-Szekely 2014)
=============================================================

    Z1 = sum(X_t I_t / ES_t) / N_T + 1                    (conditional on exceptions)
    Z2 = sum(X_t I_t / (T alpha ES_t)) + 1                (unconditional)

X_t realised P&L, I_t = 1 if X_t < -VaR_t, ES_t and VaR_t positive forecasts.
Under a correct model E[Z] = 0; negative values mean ES is underestimated.
Z2 traffic light (alpha = 2.5%): green Z2 > -0.70, yellow > -1.80, red otherwise.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
from typing import Sequence

import numpy as np

Z2_GREEN, Z2_RED = -0.70, -1.80


@dataclass
class ESBacktestResult:
    n: int
    confidence: float
    exceptions: int
    z1: float
    z2: float
    zone: str


def backtest_es(
    pnl: Sequence[float],
    var_forecasts: Sequence[float],
    es_forecasts: Sequence[float],
    confidence: float = 0.975,
) -> ESBacktestResult:
    """Acerbi-Szekely Z1 / Z2 statistics and the Z2 traffic-light zone."""
    x, v, e = (np.asarray(a, dtype=float) for a in (pnl, var_forecasts, es_forecasts))
    if not (x.shape == v.shape == e.shape) or x.ndim != 1:
        raise ValueError("pnl, var_forecasts and es_forecasts must be 1-D arrays of equal length")
    alpha = 1.0 - confidence
    hits = x < -v
    k = int(hits.sum())
    z1 = float((x[hits] / e[hits]).sum() / k + 1.0) if k else 0.0
    z2 = float((x[hits] / e[hits]).sum() / (x.size * alpha) + 1.0)
    zone = "green" if z2 > Z2_GREEN else ("yellow" if z2 > Z2_RED else "red")
    return ESBacktestResult(x.size, confidence, k, z1, z2, zone)


__all__ = ["backtest_es", "ESBacktestResult", "Z2_GREEN", "Z2_RED"]
