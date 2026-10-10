"""
QLRisk - VaR and Expected Shortfall
===================================

Pure functions on P&L vectors (gains positive, losses negative) plus
calculator classes for the CalculatorFactory.

    var = value_at_risk(pnl, 0.99)                 # positive loss number
    es  = expected_shortfall(pnl, 0.975)
    var_w = value_at_risk(pnl, 0.99, weights=w)     # age-weighted / FHS probabilities

Definitions (alpha = 1 - confidence, scenarios sorted worst first, probabilities p_i):

    VaR = -(P&L of the first scenario where cumulative probability >= alpha)
    ES  = -(1/alpha) * [ sum of P&L over scenarios fully inside the tail
                         + fractional weight of the boundary scenario ]

With equal weights and N*alpha integral, ES is the average of the N*alpha
worst outcomes and VaR is the N*alpha-th worst; otherwise VaR is the
ceil(N*alpha)-th worst (250 days at 99%: the 3rd worst).

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Any, Dict, Optional, Sequence

import numpy as np
from scipy.stats import norm

from ..base import BaseCalculator, CalculatorType


def _prepare(pnl: Sequence[float], weights: Optional[Sequence[float]]):
    x = np.asarray(pnl, dtype=float)
    if x.ndim != 1 or x.size == 0:
        raise ValueError("pnl must be a non-empty 1-D array")
    if weights is None:
        w = np.full(x.size, 1.0 / x.size)
    else:
        w = np.asarray(weights, dtype=float)
        if w.shape != x.shape or (w < 0).any() or w.sum() <= 0:
            raise ValueError("weights must be non-negative, same length as pnl, and not all zero")
        w = w / w.sum()
    order = np.argsort(x, kind="stable")
    return x[order], w[order], order


def _alpha(confidence: float) -> float:
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    return 1.0 - confidence


def value_at_risk(pnl: Sequence[float], confidence: float = 0.99,
                  weights: Optional[Sequence[float]] = None) -> float:
    """
    Historical (empirical) VaR as a positive loss.
    
    Returns minus the P&L of the first scenario, ordered worst first, at which
    the cumulative probability reaches 1 - confidence. With 250 equally weighted
    scenarios at 99%, alpha * N = 2.5, so VaR is the 3rd-worst loss.
    """
    x, w, _ = _prepare(pnl, weights)
    alpha = _alpha(confidence)
    idx = int(np.searchsorted(np.cumsum(w), alpha - 1e-12))
    return float(-x[min(idx, x.size - 1)])


def expected_shortfall(pnl: Sequence[float], confidence: float = 0.975,
                       weights: Optional[Sequence[float]] = None) -> float:
    """Expected Shortfall (tail average beyond VaR, with the boundary scenario weighted fractionally)."""
    x, w, _ = _prepare(pnl, weights)
    return float(-np.dot(_tail_weights(w, _alpha(confidence)), x) / _alpha(confidence))


def _tail_weights(sorted_w: np.ndarray, alpha: float) -> np.ndarray:
    """Probability mass each sorted scenario contributes to the alpha-tail."""
    cum = np.cumsum(sorted_w)
    prev = cum - sorted_w
    mass = np.minimum(cum, alpha) - prev
    mass[mass < 1e-12] = 0.0                    # drop floating-point residue beyond the tail
    return mass


def tail_indices(pnl: Sequence[float], confidence: float, weights: Optional[Sequence[float]] = None):
    """Original indices of the tail scenarios (worst first) and their tail probability mass."""
    x, w, order = _prepare(pnl, weights)
    tw = _tail_weights(w, _alpha(confidence))
    keep = tw > 0
    return order[keep], tw[keep]


def parametric_var(mean: float, std: float, confidence: float = 0.99,
                   skew: float = 0.0, excess_kurtosis: float = 0.0) -> float:
    """
    Normal (delta-normal) VaR, or Cornish-Fisher VaR when skew / excess kurtosis are given.
    
    VaR = -(mean + z_cf * std), z_cf = z + (z^2-1)S/6 + (z^3-3z)K/24 - (2z^3-5z)S^2/36, z = Phi^-1(alpha)
    """
    z = norm.ppf(_alpha(confidence))
    z_cf = z + (z * z - 1) * skew / 6 + (z ** 3 - 3 * z) * excess_kurtosis / 24 - (2 * z ** 3 - 5 * z) * skew ** 2 / 36
    return float(-(mean + z_cf * std))


def parametric_es(mean: float, std: float, confidence: float = 0.975) -> float:
    """Normal Expected Shortfall: -(mean - std * phi(z) / alpha)."""
    alpha = _alpha(confidence)
    return float(-(mean - std * norm.pdf(norm.ppf(alpha)) / alpha))


def scale_to_horizon(value: float, from_days: int, to_days: int) -> float:
    """Square-root-of-time scaling."""
    return value * np.sqrt(to_days / from_days)


# =============================================================================
# Calculators (CalculatorFactory integration)
# =============================================================================

class _PnLRiskCalculator(BaseCalculator[float]):
    """
    Input: dict with 'pnl' (sequence) and optional 'confidence', 'weights';
    or for the parametric method 'mean' and 'std' (and optional 'skew', 'excess_kurtosis').
    Config: 'confidence' default, 'method' ('historical' | 'parametric').
    """
    _default_confidence = 0.99
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        super().__init__(name or self.__class__.__name__, config or {})
    
    def _inputs(self, data: Dict[str, Any]):
        confidence = data.get("confidence", self.config.get("confidence", self._default_confidence))
        method = data.get("method", self.config.get("method", "historical"))
        return confidence, method


class VaRCalculator(_PnLRiskCalculator):
    """Value-at-Risk from a P&L vector (historical) or from mean/std (parametric, Cornish-Fisher)."""
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.VAR
    
    def _calculate_impl(self, data: Dict[str, Any]) -> float:
        confidence, method = self._inputs(data)
        if method == "parametric":
            return parametric_var(data["mean"], data["std"], confidence,
                                  data.get("skew", 0.0), data.get("excess_kurtosis", 0.0))
        return value_at_risk(data["pnl"], confidence, data.get("weights"))


class ExpectedShortfallCalculator(_PnLRiskCalculator):
    """Expected Shortfall from a P&L vector (historical) or from mean/std (parametric normal)."""
    _default_confidence = 0.975
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.EXPECTED_SHORTFALL
    
    def _calculate_impl(self, data: Dict[str, Any]) -> float:
        confidence, method = self._inputs(data)
        if method == "parametric":
            return parametric_es(data["mean"], data["std"], confidence)
        return expected_shortfall(data["pnl"], confidence, data.get("weights"))


__all__ = [
    "value_at_risk", "expected_shortfall", "tail_indices", "parametric_var", "parametric_es",
    "scale_to_horizon", "VaRCalculator", "ExpectedShortfallCalculator",
]
