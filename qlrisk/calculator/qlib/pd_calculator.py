# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Probability of Default Calculator.

Uses QuantLib's statistical and financial functions for PD calculation
with improved numerical precision and performance.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import BaseCalculator, CalculatorType, CalculationResult


class QLPDMethod(Enum):
    """PD calculation methods using QuantLib."""
    MERTON = "merton"
    CREDIT_CURVE = "credit_curve"
    HAZARD_RATE = "hazard_rate"
    TRANSITION_MATRIX = "transition_matrix"


@dataclass
class QLPDInput:
    """Input parameters for QuantLib PD calculation."""
    # Merton model inputs
    asset_value: float = 0.0
    debt_value: float = 0.0
    asset_volatility: float = 0.0
    risk_free_rate: float = 0.0
    time_horizon: float = 1.0
    
    # Credit curve inputs
    credit_spreads: List[float] = field(default_factory=list)
    tenors: List[float] = field(default_factory=list)
    recovery_rate: float = 0.4
    
    # Hazard rate inputs
    hazard_rate: float = 0.0
    
    # Rating inputs
    current_rating: str = ""
    target_rating: str = "D"
    
    method: QLPDMethod = QLPDMethod.MERTON


@dataclass
class QLPDResult:
    """Result of QuantLib PD calculation."""
    pd: float
    pd_term_structure: Dict[float, float] = field(default_factory=dict)
    survival_probability: float = 0.0
    method: str = ""
    components: Dict[str, Any] = field(default_factory=dict)


class QLPDCalculator(BaseCalculator):
    """
    QuantLib-based Probability of Default Calculator.
    
    Implements PD calculation using QuantLib's credit analytics:
    - Merton structural model using QuantLib's normal distribution
    - Credit curve bootstrapping from CDS spreads
    - Hazard rate models
    - Default probability extraction from survival curves
    """
    
    def __init__(self, name: str = "QLPDCalculator", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.PROBABILITY_OF_DEFAULT
        
        if not QUANTLIB_AVAILABLE:
            raise ImportError("QuantLib is required for QLPDCalculator")
    
    def calculate(self, data: QLPDInput) -> CalculationResult:
        """Calculate PD using QuantLib methods."""
        self._validate_input(data)
        
        if data.method == QLPDMethod.MERTON:
            result = self._calculate_merton_pd(data)
        elif data.method == QLPDMethod.CREDIT_CURVE:
            result = self._calculate_credit_curve_pd(data)
        elif data.method == QLPDMethod.HAZARD_RATE:
            result = self._calculate_hazard_rate_pd(data)
        elif data.method == QLPDMethod.TRANSITION_MATRIX:
            result = self._calculate_transition_pd(data)
        else:
            raise ValueError(f"Unknown PD method: {data.method}")
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={"method": data.method.value, "quantlib_version": ql.version()}
        )
    
    def _calculate_merton_pd(self, data: QLPDInput) -> QLPDResult:
        """Calculate PD using Merton structural model with QuantLib."""
        # Distance to default
        # d2 = (ln(V/D) + (r - σ²/2)T) / (σ√T)
        
        normal = ql.NormalDistribution()
        cumulative_normal = ql.CumulativeNormalDistribution()
        
        V = data.asset_value
        D = data.debt_value
        sigma = data.asset_volatility
        r = data.risk_free_rate
        T = data.time_horizon
        
        import math
        
        d1 = (math.log(V / D) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # PD = N(-d2)
        pd = cumulative_normal(-d2)
        survival_prob = 1.0 - pd
        
        # Calculate term structure
        term_structure = {}
        for t in [0.25, 0.5, 1.0, 2.0, 3.0, 5.0]:
            if t <= T:
                d2_t = (math.log(V / D) + (r - 0.5 * sigma**2) * t) / (sigma * math.sqrt(t))
                term_structure[t] = cumulative_normal(-d2_t)
        
        return QLPDResult(
            pd=pd,
            pd_term_structure=term_structure,
            survival_probability=survival_prob,
            method="merton_quantlib",
            components={
                "d1": d1,
                "d2": d2,
                "asset_value": V,
                "debt_value": D,
                "volatility": sigma
            }
        )
    
    def _calculate_credit_curve_pd(self, data: QLPDInput) -> QLPDResult:
        """Calculate PD from credit spreads using QuantLib credit curve."""
        # Build default probability curve from credit spreads
        
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today
        
        calendar = ql.TARGET()
        day_count = ql.Actual365Fixed()
        
        # Create hazard rate term structure from spreads
        # Approximate: hazard_rate ≈ spread / (1 - recovery)
        recovery = data.recovery_rate
        
        hazard_rates = []
        dates = []
        for tenor, spread in zip(data.tenors, data.credit_spreads):
            hazard = spread / (1.0 - recovery)
            hazard_rates.append(hazard)
            dates.append(calendar.advance(today, ql.Period(int(tenor * 12), ql.Months)))
        
        # Build hazard rate curve
        hazard_curve = ql.HazardRateCurve(dates, hazard_rates, day_count)
        hazard_curve_handle = ql.DefaultProbabilityTermStructureHandle(hazard_curve)
        
        # Extract default probabilities
        term_structure = {}
        for t in data.tenors:
            target_date = calendar.advance(today, ql.Period(int(t * 12), ql.Months))
            dp = hazard_curve.defaultProbability(target_date)
            term_structure[t] = dp
        
        # Get 1Y PD
        one_year_date = calendar.advance(today, ql.Period(1, ql.Years))
        pd_1y = hazard_curve.defaultProbability(one_year_date)
        survival_1y = hazard_curve.survivalProbability(one_year_date)
        
        return QLPDResult(
            pd=pd_1y,
            pd_term_structure=term_structure,
            survival_probability=survival_1y,
            method="credit_curve_quantlib",
            components={
                "hazard_rates": dict(zip(data.tenors, hazard_rates)),
                "recovery_rate": recovery,
                "spreads": dict(zip(data.tenors, data.credit_spreads))
            }
        )
    
    def _calculate_hazard_rate_pd(self, data: QLPDInput) -> QLPDResult:
        """Calculate PD from constant hazard rate using QuantLib."""
        import math
        
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today
        
        calendar = ql.TARGET()
        day_count = ql.Actual365Fixed()
        
        # Flat hazard rate curve
        hazard_quote = ql.QuoteHandle(ql.SimpleQuote(data.hazard_rate))
        flat_hazard = ql.FlatHazardRate(today, hazard_quote, day_count)
        
        # Calculate term structure
        term_structure = {}
        for t in [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]:
            target_date = calendar.advance(today, ql.Period(int(t * 12), ql.Months))
            dp = flat_hazard.defaultProbability(target_date)
            term_structure[t] = dp
        
        # 1Y PD
        one_year_date = calendar.advance(today, ql.Period(1, ql.Years))
        pd_1y = flat_hazard.defaultProbability(one_year_date)
        survival_1y = flat_hazard.survivalProbability(one_year_date)
        
        return QLPDResult(
            pd=pd_1y,
            pd_term_structure=term_structure,
            survival_probability=survival_1y,
            method="hazard_rate_quantlib",
            components={
                "hazard_rate": data.hazard_rate,
                "expected_default_time": 1.0 / data.hazard_rate if data.hazard_rate > 0 else float('inf')
            }
        )
    
    def _calculate_transition_pd(self, data: QLPDInput) -> QLPDResult:
        """Calculate PD from rating transition matrix."""
        # Standard 1Y transition matrix (S&P style)
        # Simplified: use average historical default rates by rating
        
        rating_pds = {
            "AAA": 0.0001, "AA": 0.0002, "A": 0.0006,
            "BBB": 0.0020, "BB": 0.0100, "B": 0.0400,
            "CCC": 0.1500, "CC": 0.3000, "C": 0.5000, "D": 1.0
        }
        
        current = data.current_rating.upper()
        if current not in rating_pds:
            raise ValueError(f"Unknown rating: {current}")
        
        pd_1y = rating_pds[current]
        
        # Build multi-year PD term structure (cumulative)
        term_structure = {}
        survival = 1.0 - pd_1y
        for t in [1, 2, 3, 5, 7, 10]:
            cumulative_survival = survival ** t
            term_structure[float(t)] = 1.0 - cumulative_survival
        
        return QLPDResult(
            pd=pd_1y,
            pd_term_structure=term_structure,
            survival_probability=1.0 - pd_1y,
            method="transition_matrix",
            components={
                "current_rating": current,
                "rating_pd": rating_pds,
                "implied_hazard_rate": -ql.CumulativeNormalDistribution()(pd_1y)
            }
        )
    
    def _validate_input(self, data: QLPDInput) -> None:
        """Validate input parameters."""
        if data.method == QLPDMethod.MERTON:
            if data.asset_value <= 0:
                raise ValueError("Asset value must be positive")
            if data.debt_value <= 0:
                raise ValueError("Debt value must be positive")
            if data.asset_volatility <= 0:
                raise ValueError("Volatility must be positive")
            if data.time_horizon <= 0:
                raise ValueError("Time horizon must be positive")
        
        elif data.method == QLPDMethod.CREDIT_CURVE:
            if not data.credit_spreads or not data.tenors:
                raise ValueError("Credit spreads and tenors required")
            if len(data.credit_spreads) != len(data.tenors):
                raise ValueError("Spreads and tenors must have same length")
        
        elif data.method == QLPDMethod.HAZARD_RATE:
            if data.hazard_rate < 0:
                raise ValueError("Hazard rate cannot be negative")
        
        elif data.method == QLPDMethod.TRANSITION_MATRIX:
            if not data.current_rating:
                raise ValueError("Current rating required")
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "quantlib_version": ql.version() if QUANTLIB_AVAILABLE else "N/A",
            "methods": [m.value for m in QLPDMethod],
            "description": "Probability of Default calculator using QuantLib"
        }
