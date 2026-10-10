"""
QLRisk - Scenario Generators
============================

    historical_scenarios(history, lookback=500, horizon=10)
    filtered_historical_scenarios(history, ewma_lambda=0.94)      # volatility-rescaled (FHS)
    historical_scenarios(history, age_weighting=0.99)             # BRW exponential weights
    monte_carlo_scenarios(history, n=10_000, distribution="t")    # from the return covariance

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Mapping, Optional

import numpy as np

from ..riskfactors.shocks import ShockType
from ..riskfactors.taxonomy import RiskFactorLike
from ..riskfactors.timeseries import RiskFactorTimeSeries
from .scenario_set import ScenarioSet


def _window(history: RiskFactorTimeSeries, lookback: Optional[int]) -> RiskFactorTimeSeries:
    if lookback is None or lookback + 1 >= len(history):
        return history
    return history.window(start=history.dates[-(lookback + 1)])


def age_weights(n: int, decay: float) -> np.ndarray:
    """Boudoukh-Richardson-Whitelaw weights: most recent scenario weighted highest, decay**age."""
    w = decay ** np.arange(n - 1, -1, -1, dtype=float)
    return w / w.sum()


def historical_scenarios(
    history: RiskFactorTimeSeries,
    lookback: Optional[int] = None,
    horizon: int = 1,
    overlapping: bool = True,
    sqrt_scaling: bool = False,
    age_weighting: Optional[float] = None,
    return_types: Optional[Mapping[RiskFactorLike, ShockType]] = None,
) -> ScenarioSet:
    """
    Historical-simulation scenarios.
    
    Args:
        history: Factor levels
        lookback: Number of most recent 1-day returns to use (None = all)
        horizon: Holding period in days
        overlapping: Overlapping h-day windows (ignored with sqrt_scaling)
        sqrt_scaling: Use 1-day returns x sqrt(horizon) instead of h-day returns
        age_weighting: Decay factor for BRW age weights (e.g. 0.99); None = equal weights
        return_types: Per-factor return convention overrides
    """
    hist = _window(history, lookback)
    if sqrt_scaling or horizon == 1:
        labels, ret = hist.returns(1, return_types=return_types)
        ret = ret * np.sqrt(horizon)
    else:
        labels, ret = hist.returns(horizon, overlapping, return_types)
    weights = age_weights(len(labels), age_weighting) if age_weighting else None
    method = "historical_age_weighted" if age_weighting else "historical"
    return ScenarioSet(hist.factors, ret, hist.return_types(return_types), labels, weights, horizon, method,
                       {"lookback": lookback, "sqrt_scaling": sqrt_scaling, "overlapping": overlapping,
                        "age_weighting": age_weighting})


def ewma_volatility(returns: np.ndarray, decay: float = 0.94, seed_obs: int = 20):
    """
    RiskMetrics EWMA volatility per column.
    
    Returns (sigma_t, sigma_next): sigma_t[i] is the forecast for row i using rows < i;
    sigma_next is the forecast for the day after the last row. NaN returns are ignored.
    """
    r = np.nan_to_num(returns, nan=0.0)
    n = r.shape[0]
    var = np.nanvar(returns[: max(min(seed_obs, n), 2)], axis=0)
    var = np.where(np.isfinite(var) & (var > 0), var, np.nanmean(r ** 2, axis=0) + 1e-18)
    sig = np.empty_like(r)
    for i in range(n):
        sig[i] = np.sqrt(var)
        var = decay * var + (1 - decay) * r[i] ** 2
    return sig, np.sqrt(var)


def filtered_historical_scenarios(
    history: RiskFactorTimeSeries,
    ewma_lambda: float = 0.94,
    lookback: Optional[int] = None,
    horizon: int = 1,
    return_types: Optional[Mapping[RiskFactorLike, ShockType]] = None,
) -> ScenarioSet:
    """
    Filtered historical simulation (Hull-White volatility updating):
    each 1-day return is rescaled by current_vol / vol_at_the_time (EWMA), then x sqrt(horizon).
    The EWMA runs over the full history; the lookback limits the scenarios kept.
    """
    labels, ret = history.returns(1, return_types=return_types)
    sig, sig_now = ewma_volatility(ret, ewma_lambda)
    with np.errstate(divide="ignore", invalid="ignore"):
        scaled = np.where(sig > 0, ret * sig_now / sig, ret)
    if lookback is not None:
        labels, scaled = labels[-lookback:], scaled[-lookback:]
    return ScenarioSet(history.factors, scaled * np.sqrt(horizon), history.return_types(return_types), labels,
                       None, horizon, "filtered_historical", {"ewma_lambda": ewma_lambda, "lookback": lookback})


def covariance(returns: np.ndarray, ewma_lambda: Optional[float] = None) -> np.ndarray:
    """Sample covariance (pairwise-complete), or EWMA covariance with the given decay (most recent heaviest)."""
    r = np.nan_to_num(returns - np.nanmean(returns, axis=0), nan=0.0)
    if ewma_lambda is None:
        return np.cov(r, rowvar=False)
    w = ewma_lambda ** np.arange(r.shape[0] - 1, -1, -1, dtype=float)
    w /= w.sum()
    return (r * w[:, None]).T @ r


def monte_carlo_scenarios(
    history: RiskFactorTimeSeries,
    n: int = 10_000,
    horizon: int = 1,
    lookback: Optional[int] = None,
    ewma_lambda: Optional[float] = None,
    distribution: str = "normal",
    dof: float = 5.0,
    seed: Optional[int] = None,
    return_types: Optional[Mapping[RiskFactorLike, ShockType]] = None,
) -> ScenarioSet:
    """
    Monte Carlo scenarios from the (sample or EWMA) covariance of 1-day returns, zero mean,
    multivariate normal or Student-t (scaled to the same covariance), x sqrt(horizon).
    """
    hist = _window(history, lookback)
    _, ret = hist.returns(1, return_types=return_types)
    cov = covariance(ret, ewma_lambda)
    vals, vecs = np.linalg.eigh(cov)
    root = vecs * np.sqrt(np.clip(vals, 0.0, None))          # PSD-safe square root
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n, cov.shape[0]))
    if distribution == "t":
        z *= np.sqrt((dof - 2.0) / rng.chisquare(dof, size=(n, 1)))
    elif distribution != "normal":
        raise ValueError("distribution must be 'normal' or 't'")
    sims = (z @ root.T) * np.sqrt(horizon)
    return ScenarioSet(hist.factors, sims, hist.return_types(return_types), list(range(n)), None, horizon,
                       "monte_carlo", {"distribution": distribution, "dof": dof, "ewma_lambda": ewma_lambda,
                                       "lookback": lookback, "seed": seed})


__all__ = ["historical_scenarios", "filtered_historical_scenarios", "monte_carlo_scenarios",
           "age_weights", "ewma_volatility", "covariance"]
