# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Expected Exposure (EE) Calculator.

Calculates Expected Exposure and Effective Expected Exposure using
QuantLib's Monte Carlo simulation and numerical integration.

EE(t) = E[max(0, V(t))]
EEE(t) = max(EEE(t-1), EE(t))
Effective EPE = ∫ EEE(t) dt / T
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


class EEMethod(Enum):
    """EE calculation methodology."""
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


@dataclass
class QLEEInput:
    """Input parameters for QuantLib EE calculation."""
    current_mtm: float
    notional: float
    maturity_years: float
    volatility: float = 0.15
    drift: float = 0.0
    product_type: str = "irs"
    time_points: Optional[List[float]] = None
    num_simulations: int = 10000
    method: EEMethod = EEMethod.MONTE_CARLO
    mean_reversion: float = 0.0
    long_term_mean: float = 0.0


@dataclass
class QLEEResult:
    """Result of QuantLib EE calculation."""
    ee: float  # EE at final time point
    ee_profile: List[Tuple[float, float]] = field(default_factory=list)
    eee_profile: List[Tuple[float, float]] = field(default_factory=list)
    effective_epe: float = 0.0
    peak_ee: float = 0.0
    peak_ee_time: float = 0.0
    average_ee: float = 0.0
    method: str = ""
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibEECalculator(BaseCalculator):
    """
    QuantLib-based Expected Exposure Calculator.
    
    Uses QuantLib for:
    - High-quality random number generation
    - Path simulation
    - Numerical integration for Effective EPE
    """
    
    def __init__(self, name: str = "QuantLibEECalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.EXPECTED_EXPOSURE
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibEECalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLEEInput) -> CalculationResult:
        """
        Calculate Expected Exposure using QuantLib.
        
        Args:
            data: QLEEInput containing exposure parameters
            
        Returns:
            CalculationResult containing QLEEResult
        """
        self._validate_input(data)
        
        if data.method == EEMethod.PARAMETRIC:
            result = self._calculate_parametric(data)
        elif data.method == EEMethod.MONTE_CARLO:
            result = self._calculate_monte_carlo(data)
        else:
            raise ValueError(f"Unknown EE method: {data.method}")
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "method": data.method.value,
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A",
            }
        )
    
    def _validate_input(self, data: QLEEInput) -> None:
        """Validate input parameters."""
        if data.notional < 0:
            raise ValueError("Notional must be non-negative")
        if data.maturity_years <= 0:
            raise ValueError("Maturity must be positive")
        if data.volatility < 0:
            raise ValueError("Volatility must be non-negative")
    
    def _calculate_parametric(self, data: QLEEInput) -> QLEEResult:
        """
        Calculate EE using parametric (analytical) approach.
        
        For a normal distribution:
        EE = E[max(0, X)] = μ × Φ(μ/σ) + σ × φ(μ/σ)
        
        where Φ is the standard normal CDF and φ is the PDF.
        """
        # Time grid
        time_points = data.time_points or self._default_time_grid(data.maturity_years)
        
        ee_profile = []
        peak_ee = 0.0
        peak_time = 0.0
        
        for t in time_points:
            if t <= 0:
                ee_t = max(0, data.current_mtm)
            else:
                # Expected value grows with drift, variance grows with time
                mu_t = data.current_mtm * math.exp(data.drift * t)
                sigma_t = abs(data.current_mtm) * data.volatility * math.sqrt(t)
                
                if sigma_t > 0:
                    # E[max(0, X)] for normal X
                    d = mu_t / sigma_t
                    ee_t = mu_t * self._norm_cdf(d) + sigma_t * self._norm_pdf(d)
                else:
                    ee_t = max(0, mu_t)
            
            ee_profile.append((t, ee_t))
            
            if ee_t > peak_ee:
                peak_ee = ee_t
                peak_time = t
        
        # Calculate Effective EE (non-decreasing)
        eee_profile = self._calculate_effective_ee(ee_profile)
        
        # Effective EPE (time-weighted average of EEE)
        effective_epe = self._calculate_effective_epe(eee_profile, data.maturity_years)
        
        # Average EE
        avg_ee = sum(ee for _, ee in ee_profile) / len(ee_profile) if ee_profile else 0
        
        # Final EE
        final_ee = ee_profile[-1][1] if ee_profile else 0
        
        return QLEEResult(
            ee=final_ee,
            ee_profile=ee_profile,
            eee_profile=eee_profile,
            effective_epe=effective_epe,
            peak_ee=peak_ee,
            peak_ee_time=peak_time,
            average_ee=avg_ee,
            method=EEMethod.PARAMETRIC.value,
            components={
                "volatility": data.volatility,
                "drift": data.drift,
                "current_mtm": data.current_mtm,
            }
        )
    
    def _calculate_monte_carlo(self, data: QLEEInput) -> QLEEResult:
        """
        Calculate EE using Monte Carlo simulation with QuantLib.
        """
        # Time grid
        time_points = data.time_points or self._default_time_grid(data.maturity_years)
        
        # Set up QuantLib random number generator
        seed = 42
        rng = ql.MersenneTwisterUniformRng(seed)
        gaussian_rng = ql.MersenneTwisterGaussianRng(rng)
        
        # Storage for exposure at each time point
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
                
                # Draw random number
                z = gaussian_rng.next().value()
                
                # Stochastic process
                if data.mean_reversion > 0:
                    # Ornstein-Uhlenbeck
                    theta = data.mean_reversion
                    mu = data.long_term_mean
                    sigma = data.volatility
                    
                    value = value + theta * (mu - value) * dt + sigma * math.sqrt(dt) * z
                else:
                    # GBM
                    drift = data.drift
                    sigma = data.volatility
                    
                    value = value * math.exp(
                        (drift - 0.5 * sigma**2) * dt + sigma * math.sqrt(dt) * z
                    )
                
                # Record positive exposure
                exposures_at_t[t].append(max(0, value))
                prev_t = t
        
        # Calculate EE at each time point (mean of positive exposures)
        ee_profile = []
        peak_ee = 0.0
        peak_time = 0.0
        
        for t in time_points:
            exposures = exposures_at_t[t]
            ee_t = sum(exposures) / len(exposures) if exposures else 0
            
            ee_profile.append((t, ee_t))
            
            if ee_t > peak_ee:
                peak_ee = ee_t
                peak_time = t
        
        # Calculate Effective EE
        eee_profile = self._calculate_effective_ee(ee_profile)
        
        # Effective EPE
        effective_epe = self._calculate_effective_epe(eee_profile, data.maturity_years)
        
        # Average EE
        avg_ee = sum(ee for _, ee in ee_profile) / len(ee_profile) if ee_profile else 0
        
        # Final EE
        final_ee = ee_profile[-1][1] if ee_profile else 0
        
        return QLEEResult(
            ee=final_ee,
            ee_profile=ee_profile,
            eee_profile=eee_profile,
            effective_epe=effective_epe,
            peak_ee=peak_ee,
            peak_ee_time=peak_time,
            average_ee=avg_ee,
            method=EEMethod.MONTE_CARLO.value,
            components={
                "num_simulations": data.num_simulations,
                "num_time_points": len(time_points),
                "volatility": data.volatility,
            }
        )
    
    def _calculate_effective_ee(self, 
                                 ee_profile: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Calculate Effective Expected Exposure (EEE).
        
        EEE(t) = max(EEE(t-1), EE(t))
        
        This ensures the exposure profile is non-decreasing.
        """
        if not ee_profile:
            return []
        
        eee_profile = []
        max_ee = 0.0
        
        for t, ee in ee_profile:
            max_ee = max(max_ee, ee)
            eee_profile.append((t, max_ee))
        
        return eee_profile
    
    def _calculate_effective_epe(self, 
                                  eee_profile: List[Tuple[float, float]], 
                                  maturity: float) -> float:
        """
        Calculate Effective EPE (time-weighted average of EEE).
        
        Effective EPE = (1/T) × ∫₀ᵀ EEE(t) dt
        """
        if not eee_profile or maturity <= 0:
            return 0.0
        
        # Trapezoidal integration
        integral = 0.0
        for i in range(1, len(eee_profile)):
            t1, eee1 = eee_profile[i-1]
            t2, eee2 = eee_profile[i]
            
            # Trapezoidal rule
            integral += 0.5 * (eee1 + eee2) * (t2 - t1)
        
        return integral / maturity
    
    def _default_time_grid(self, maturity: float) -> List[float]:
        """Generate default time grid."""
        points = [0.0]
        
        # Monthly for first year
        t = 1/12
        while t <= min(1.0, maturity):
            points.append(t)
            t += 1/12
        
        # Quarterly thereafter
        t = 1.25
        while t <= maturity:
            points.append(t)
            t += 0.25
        
        # Add maturity
        if maturity not in points:
            points.append(maturity)
        
        return sorted(set(points))
    
    def _norm_cdf(self, x: float) -> float:
        """Standard normal CDF using QuantLib."""
        normal = ql.CumulativeNormalDistribution()
        return normal(x)
    
    def _norm_pdf(self, x: float) -> float:
        """Standard normal PDF using QuantLib."""
        normal = ql.NormalDistribution()
        return normal(x)
    
    def calculate_portfolio_ee(self, 
                                trades: List[QLEEInput],
                                correlation_matrix: Optional[List[List[float]]] = None) -> Dict[str, Any]:
        """
        Calculate portfolio-level EE.
        
        Args:
            trades: List of trade inputs
            correlation_matrix: Optional correlation matrix
            
        Returns:
            Portfolio EE results
        """
        if not trades:
            return {"portfolio_ee": 0.0}
        
        # Calculate individual EEs
        individual_results = []
        for trade in trades:
            result = self.calculate(trade)
            individual_results.append(result.result)
        
        # Aggregate profiles
        all_times = set()
        for result in individual_results:
            all_times.update(t for t, _ in result.ee_profile)
        
        time_grid = sorted(all_times)
        
        # Portfolio EE at each time point
        portfolio_ee_profile = []
        portfolio_eee_profile = []
        max_ee = 0.0
        
        for t in time_grid:
            # Sum of EEs (assuming no netting for simplicity)
            ee_t = sum(
                self._interpolate_profile(t, r.ee_profile) 
                for r in individual_results
            )
            
            portfolio_ee_profile.append((t, ee_t))
            
            # EEE
            max_ee = max(max_ee, ee_t)
            portfolio_eee_profile.append((t, max_ee))
        
        # Effective EPE
        maturity = max(t.maturity_years for t in trades)
        effective_epe = self._calculate_effective_epe(portfolio_eee_profile, maturity)
        
        # Summary stats
        portfolio_ee = portfolio_ee_profile[-1][1] if portfolio_ee_profile else 0
        peak_ee = max(ee for _, ee in portfolio_ee_profile) if portfolio_ee_profile else 0
        
        return {
            "portfolio_ee": portfolio_ee,
            "portfolio_effective_epe": effective_epe,
            "portfolio_peak_ee": peak_ee,
            "portfolio_ee_profile": portfolio_ee_profile,
            "portfolio_eee_profile": portfolio_eee_profile,
            "num_trades": len(trades),
        }
    
    def _interpolate_profile(self, t: float, 
                              profile: List[Tuple[float, float]]) -> float:
        """Linear interpolation of exposure profile."""
        if not profile:
            return 0.0
        
        # Find bracketing points
        below = None
        above = None
        
        for time, value in profile:
            if time <= t:
                below = (time, value)
            if time >= t and above is None:
                above = (time, value)
        
        if below is None:
            return profile[0][1]
        if above is None:
            return below[1]
        if below[0] == above[0]:
            return below[1]
        
        # Linear interpolation
        weight = (t - below[0]) / (above[0] - below[0])
        return below[1] + weight * (above[1] - below[1])
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "methods": [m.value for m in EEMethod],
            "calculates_effective_epe": True,
            "quantlib_available": QUANTLIB_AVAILABLE,
        }


class QuantLibEffectiveEECalculator(BaseCalculator):
    """
    Dedicated Effective Expected Exposure Calculator.
    
    Focuses on computing EEE and Effective EPE for regulatory purposes.
    """
    
    def __init__(self, name: str = "QuantLibEffectiveEECalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.EXPECTED_EXPOSURE
        self._ee_calculator = QuantLibEECalculator()
    
    def calculate(self, data: QLEEInput) -> CalculationResult:
        """
        Calculate Effective EE and Effective EPE.
        """
        # Use base EE calculator
        ee_result = self._ee_calculator.calculate(data)
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=ee_result.result,
            metadata={
                "effective_epe": ee_result.result.effective_epe,
                "peak_ee": ee_result.result.peak_ee,
            }
        )
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "focus": "effective_epe",
        }
