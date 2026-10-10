# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Potential Future Exposure (PFE) Calculator.

Calculates PFE using Monte Carlo simulation with QuantLib's advanced
random number generation and path simulation capabilities.

PFE_α(t) = Quantile_α(max(0, V(t)))
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import math

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import BaseCalculator, CalculationResult, CalculatorType


class PFEMethod(Enum):
    """PFE calculation methodology."""
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"
    REGULATORY_ADDON = "regulatory_addon"


@dataclass
class QLPFEInput:
    """Input parameters for QuantLib PFE calculation."""
    current_mtm: float
    notional: float
    maturity_years: float
    volatility: float = 0.15
    product_type: str = "irs"
    confidence_level: float = 0.95
    time_points: Optional[List[float]] = None
    num_simulations: int = 10000
    method: PFEMethod = PFEMethod.MONTE_CARLO
    drift: float = 0.0
    mean_reversion: float = 0.0  # For mean-reverting processes
    long_term_mean: float = 0.0
    correlation: float = 0.0  # For multi-factor models


@dataclass
class QLPFEResult:
    """Result of QuantLib PFE calculation."""
    pfe: float  # PFE at final time point
    pfe_profile: List[Tuple[float, float]] = field(default_factory=list)
    peak_pfe: float = 0.0
    peak_pfe_time: float = 0.0
    average_pfe: float = 0.0
    method: str = ""
    confidence_level: float = 0.95
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibPFECalculator(BaseCalculator):
    """
    QuantLib-based Potential Future Exposure Calculator.
    
    Uses QuantLib for:
    - High-quality random number generation (Mersenne Twister, Sobol)
    - Path simulation with various stochastic processes
    - Statistical functions for percentile calculations
    """
    
    # Regulatory add-on factors (Basel CEM)
    ADDON_FACTORS = {
        "irs": {1: 0.0, 5: 0.005, 10: 0.015, float('inf'): 0.03},
        "fx": {1: 0.01, 5: 0.05, 10: 0.075, float('inf'): 0.10},
        "equity": {1: 0.06, 5: 0.08, 10: 0.10, float('inf'): 0.15},
        "commodity": {1: 0.10, 5: 0.12, 10: 0.15, float('inf'): 0.20},
        "credit": {1: 0.05, 5: 0.05, 10: 0.075, float('inf'): 0.10},
    }
    
    def __init__(self, name: str = "QuantLibPFECalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.PFE
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibPFECalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLPFEInput) -> CalculationResult:
        """
        Calculate PFE using QuantLib-enhanced methods.
        
        Args:
            data: QLPFEInput containing exposure parameters
            
        Returns:
            CalculationResult containing QLPFEResult
        """
        self._validate_input(data)
        
        if data.method == PFEMethod.PARAMETRIC:
            result = self._calculate_parametric(data)
        elif data.method == PFEMethod.MONTE_CARLO:
            result = self._calculate_monte_carlo(data)
        elif data.method == PFEMethod.REGULATORY_ADDON:
            result = self._calculate_regulatory_addon(data)
        else:
            raise ValueError(f"Unknown PFE method: {data.method}")
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "method": data.method.value,
                "confidence_level": data.confidence_level,
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A",
            }
        )
    
    def _validate_input(self, data: QLPFEInput) -> None:
        """Validate input parameters."""
        if data.notional < 0:
            raise ValueError("Notional must be non-negative")
        if data.maturity_years <= 0:
            raise ValueError("Maturity must be positive")
        if data.volatility < 0:
            raise ValueError("Volatility must be non-negative")
        if not 0 < data.confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
    
    def _calculate_parametric(self, data: QLPFEInput) -> QLPFEResult:
        """
        Calculate PFE using parametric (analytical) approach.
        
        For a normally distributed exposure:
        PFE_α = MTM + σ√t × N^(-1)(α) × Factor × Notional
        """
        # Time grid
        time_points = data.time_points or self._default_time_grid(data.maturity_years)
        
        # Z-score for confidence level
        z_alpha = self._norm_inv(data.confidence_level)
        
        pfe_profile = []
        peak_pfe = 0.0
        peak_time = 0.0
        
        for t in time_points:
            if t > data.maturity_years:
                break
            
            # Exposure factor for product type
            factor = self._get_exposure_factor(data.product_type, t)
            
            # PFE at time t
            # For IRS-like products, exposure typically peaks at mid-life
            diffusion = data.volatility * math.sqrt(t) * factor * data.notional
            pfe_t = max(0, data.current_mtm) + z_alpha * diffusion
            
            pfe_profile.append((t, pfe_t))
            
            if pfe_t > peak_pfe:
                peak_pfe = pfe_t
                peak_time = t
        
        # Average PFE
        avg_pfe = sum(pfe for _, pfe in pfe_profile) / len(pfe_profile) if pfe_profile else 0
        
        # Final PFE
        final_pfe = pfe_profile[-1][1] if pfe_profile else 0
        
        return QLPFEResult(
            pfe=final_pfe,
            pfe_profile=pfe_profile,
            peak_pfe=peak_pfe,
            peak_pfe_time=peak_time,
            average_pfe=avg_pfe,
            method=PFEMethod.PARAMETRIC.value,
            confidence_level=data.confidence_level,
            components={
                "z_alpha": z_alpha,
                "volatility": data.volatility,
                "current_mtm": data.current_mtm,
            }
        )
    
    def _calculate_monte_carlo(self, data: QLPFEInput) -> QLPFEResult:
        """
        Calculate PFE using Monte Carlo simulation with QuantLib.
        """
        # Time grid
        time_points = data.time_points or self._default_time_grid(data.maturity_years)
        num_steps = len(time_points)
        
        # Set up QuantLib random number generator
        seed = 42
        rng = ql.MersenneTwisterUniformRng(seed)
        gaussian_rng = ql.MersenneTwisterGaussianRng(rng)
        
        # Storage for exposure paths at each time point
        exposures_at_t = {t: [] for t in time_points}
        
        # Simulate paths
        for _ in range(data.num_simulations):
            value = data.current_mtm
            prev_t = 0.0
            
            for t in time_points:
                dt = t - prev_t
                if dt <= 0:
                    exposures_at_t[t].append(max(0, value))
                    continue
                
                # Draw random number using QuantLib
                z = gaussian_rng.next().value()
                
                # Stochastic process
                if data.mean_reversion > 0:
                    # Mean-reverting process (Ornstein-Uhlenbeck)
                    theta = data.mean_reversion
                    mu = data.long_term_mean
                    sigma = data.volatility
                    
                    # dV = θ(μ - V)dt + σdW
                    value = value + theta * (mu - value) * dt + sigma * math.sqrt(dt) * z
                else:
                    # Geometric Brownian Motion
                    drift = data.drift
                    sigma = data.volatility
                    
                    # dV/V = μdt + σdW
                    value = value * math.exp(
                        (drift - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z
                    )
                
                # Record exposure (max with 0)
                exposures_at_t[t].append(max(0, value))
                prev_t = t
        
        # Calculate PFE at each time point
        pfe_profile = []
        peak_pfe = 0.0
        peak_time = 0.0
        
        for t in time_points:
            exposures = sorted(exposures_at_t[t])
            if exposures:
                # Percentile for PFE
                idx = int(data.confidence_level * len(exposures))
                idx = min(idx, len(exposures) - 1)
                pfe_t = exposures[idx]
            else:
                pfe_t = 0.0
            
            pfe_profile.append((t, pfe_t))
            
            if pfe_t > peak_pfe:
                peak_pfe = pfe_t
                peak_time = t
        
        # Average PFE
        avg_pfe = sum(pfe for _, pfe in pfe_profile) / len(pfe_profile) if pfe_profile else 0
        
        # Final PFE
        final_pfe = pfe_profile[-1][1] if pfe_profile else 0
        
        return QLPFEResult(
            pfe=final_pfe,
            pfe_profile=pfe_profile,
            peak_pfe=peak_pfe,
            peak_pfe_time=peak_time,
            average_pfe=avg_pfe,
            method=PFEMethod.MONTE_CARLO.value,
            confidence_level=data.confidence_level,
            components={
                "num_simulations": data.num_simulations,
                "num_time_points": len(time_points),
                "volatility": data.volatility,
            }
        )
    
    def _calculate_regulatory_addon(self, data: QLPFEInput) -> QLPFEResult:
        """
        Calculate PFE using regulatory add-on approach (Basel CEM).
        
        PFE = Notional × Add-on Factor
        """
        # Get add-on factor
        addon_factor = self._get_addon_factor(data.product_type, data.maturity_years)
        
        # PFE = Notional × Add-on
        pfe = data.notional * addon_factor
        
        # Profile (constant for regulatory approach)
        time_points = data.time_points or self._default_time_grid(data.maturity_years)
        pfe_profile = [(t, pfe) for t in time_points if t <= data.maturity_years]
        
        return QLPFEResult(
            pfe=pfe,
            pfe_profile=pfe_profile,
            peak_pfe=pfe,
            peak_pfe_time=data.maturity_years / 2,  # Typically peaks mid-life
            average_pfe=pfe,
            method=PFEMethod.REGULATORY_ADDON.value,
            confidence_level=data.confidence_level,
            components={
                "addon_factor": addon_factor,
                "notional": data.notional,
            }
        )
    
    def _default_time_grid(self, maturity: float) -> List[float]:
        """Generate default time grid for exposure profile."""
        # Monthly for first year, quarterly thereafter
        points = []
        
        # Monthly up to 1 year
        t = 0.0
        while t <= min(1.0, maturity):
            points.append(t)
            t += 1/12
        
        # Quarterly from 1 to 5 years
        t = 1.25
        while t <= min(5.0, maturity):
            points.append(t)
            t += 0.25
        
        # Semi-annually from 5 to 10 years
        t = 5.5
        while t <= min(10.0, maturity):
            points.append(t)
            t += 0.5
        
        # Annually beyond 10 years
        t = 11.0
        while t <= maturity:
            points.append(t)
            t += 1.0
        
        # Add maturity if not included
        if maturity not in points:
            points.append(maturity)
        
        return sorted(set(points))
    
    def _get_addon_factor(self, product_type: str, maturity: float) -> float:
        """Get regulatory add-on factor."""
        factors = self.ADDON_FACTORS.get(product_type, self.ADDON_FACTORS["irs"])
        
        for threshold, factor in sorted(factors.items()):
            if maturity <= threshold:
                return factor
        
        return list(factors.values())[-1]
    
    def _get_exposure_factor(self, product_type: str, time: float) -> float:
        """
        Get exposure factor for parametric PFE.
        
        This captures the typical exposure profile shape.
        """
        if product_type in ["irs", "ccs"]:
            # IRS: exposure increases then decreases (amortizing effect)
            # Peak around 30-40% of maturity
            return 1.0 - time / 10.0 if time < 5 else 0.5
        elif product_type in ["fx", "fx_forward"]:
            # FX: exposure typically increases over time
            return 1.0
        elif product_type in ["equity", "option"]:
            # Options: exposure can increase significantly
            return 1.5
        else:
            return 1.0
    
    def _norm_inv(self, p: float) -> float:
        """Inverse of standard normal CDF using QuantLib."""
        # Use QuantLib's inverse cumulative normal
        inv_normal = ql.InverseCumulativeNormal()
        return inv_normal(p)
    
    def calculate_portfolio_pfe(self, 
                                 trades: List[QLPFEInput],
                                 correlation_matrix: Optional[List[List[float]]] = None) -> Dict[str, Any]:
        """
        Calculate portfolio PFE with optional correlations.
        
        Args:
            trades: List of trade inputs
            correlation_matrix: Optional correlation matrix between trades
            
        Returns:
            Portfolio PFE results
        """
        if not trades:
            return {"portfolio_pfe": 0.0}
        
        if correlation_matrix is None:
            # Assume independence - use root sum of squares
            individual_pfes = []
            for trade in trades:
                result = self.calculate(trade)
                individual_pfes.append(result.result.pfe)
            
            # Sum for gross, RSS for diversified
            gross_pfe = sum(individual_pfes)
            diversified_pfe = math.sqrt(sum(p**2 for p in individual_pfes))
            
            return {
                "portfolio_gross_pfe": gross_pfe,
                "portfolio_diversified_pfe": diversified_pfe,
                "diversification_benefit": gross_pfe - diversified_pfe,
                "num_trades": len(trades),
            }
        
        # Calculate with correlations
        individual_results = []
        for trade in trades:
            result = self.calculate(trade)
            individual_results.append(result.result)
        
        pfes = [r.pfe for r in individual_results]
        n = len(pfes)
        
        # Portfolio PFE = sqrt(sum_i sum_j PFE_i × PFE_j × ρ_ij)
        portfolio_var = 0.0
        for i in range(n):
            for j in range(n):
                corr = correlation_matrix[i][j] if i != j else 1.0
                portfolio_var += pfes[i] * pfes[j] * corr
        
        portfolio_pfe = math.sqrt(max(0, portfolio_var))
        gross_pfe = sum(pfes)
        
        return {
            "portfolio_gross_pfe": gross_pfe,
            "portfolio_pfe": portfolio_pfe,
            "diversification_benefit": gross_pfe - portfolio_pfe,
            "individual_pfes": pfes,
            "num_trades": n,
        }
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "methods": [m.value for m in PFEMethod],
            "default_confidence": 0.95,
            "supports_monte_carlo": True,
            "quantlib_available": QUANTLIB_AVAILABLE,
        }
