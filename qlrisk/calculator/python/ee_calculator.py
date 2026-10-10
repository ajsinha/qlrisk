"""
QLRisk - Expected Exposure (EE) Calculator
=========================================================

Python implementation of Expected Exposure and Effective Expected Exposure.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import math
import random

from ..base import (
    filter_dict_for_dataclass,
    ExposureCalculator, CalculatorType, ImplementationType
)


@dataclass
class EEInput:
    """Input data for Expected Exposure calculation."""
    current_mtm: float
    notional: float
    remaining_maturity: float  # in years
    volatility: float
    product_type: str = "irs"
    
    # Risk factors
    interest_rate: float = 0.05
    drift: float = 0.0
    
    # Collateral
    collateral_held: float = 0.0
    margin_period_of_risk: float = 10/252
    
    # Simulation
    num_simulations: int = 10000
    time_grid: Optional[List[float]] = None
    
    # Pre-computed paths
    exposure_paths: Optional[List[List[float]]] = None


@dataclass
class EEResult:
    """Result of Expected Exposure calculation."""
    ee: float  # Expected Exposure at maturity
    ee_profile: List[float]  # EE over time
    eee_profile: List[float]  # Effective EE (non-decreasing)
    time_points: List[float]
    effective_epe: float  # Time-weighted average of EEE
    peak_ee: float
    components: Dict[str, Any]


class ExpectedExposureCalculator(ExposureCalculator):
    """
    Expected Exposure (EE) and Effective Expected Exposure (EEE) Calculator.
    
    EE(t) = E[max(0, V(t))]
    
    The expected exposure is the average positive exposure at a future time.
    
    Effective EE is the non-decreasing version:
    EEE(t) = max(EEE(t-1), EE(t))
    
    Effective EPE (Expected Positive Exposure) is the time-weighted average:
    EPE = (1/T) × ∫EEE(t)dt
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Expected Exposure calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - method: 'parametric' or 'monte_carlo'
                - num_simulations: Number of MC simulations
                - calculate_effective: Whether to calculate EEE
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._method = config.get("method", "monte_carlo")
        self._num_simulations = config.get("num_simulations", 10000)
        self._calculate_effective = config.get("calculate_effective", True)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.EE
    
    def _calculate_impl(self, data: Any) -> EEResult:
        """
        Calculate Expected Exposure.
        
        Args:
            data: EEInput or dictionary
            
        Returns:
            EEResult with EE and EEE profiles
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, EEInput)
            data = EEInput(**filtered_data)
        
        # Generate time grid
        if data.time_grid is None:
            data.time_grid = self._generate_time_grid(data.remaining_maturity)
        
        if self._method == "parametric":
            return self._calculate_parametric(data)
        else:
            return self._calculate_monte_carlo(data)
    
    def _generate_time_grid(self, maturity: float, num_points: int = 20) -> List[float]:
        """Generate time grid."""
        if maturity <= 0:
            return [0.0]
        step = maturity / num_points
        return [i * step for i in range(num_points + 1)]
    
    def _calculate_parametric(self, data: EEInput) -> EEResult:
        """
        Parametric EE calculation.
        
        For a zero-mean normal distribution:
        E[max(0, X)] = σ × φ(0) = σ / √(2π)
        
        For general case with drift:
        E[max(0, X)] = μ × Φ(μ/σ) + σ × φ(μ/σ)
        """
        ee_profile = []
        
        for t in data.time_grid:
            if t == 0:
                ee = max(0.0, data.current_mtm)
            else:
                # Expected MTM (with drift towards zero for swaps)
                decay = 1 - t / data.remaining_maturity if data.remaining_maturity > 0 else 0
                mu = data.current_mtm * decay
                
                # Time-scaled volatility
                sigma = data.volatility * data.notional * math.sqrt(t)
                
                if sigma > 0:
                    # E[max(0, X)] for normal X ~ N(mu, sigma²)
                    d = mu / sigma
                    ee = mu * self._norm_cdf(d) + sigma * self._norm_pdf(d)
                else:
                    ee = max(0.0, mu)
                
                # Collateral adjustment
                if data.collateral_held > 0 and t >= data.margin_period_of_risk:
                    ee = max(0.0, ee - data.collateral_held)
            
            ee_profile.append(ee)
        
        # Calculate Effective EE (non-decreasing)
        eee_profile = self._calculate_effective_ee(ee_profile)
        
        # Effective EPE
        effective_epe = self._calculate_effective_epe(eee_profile, data.time_grid)
        
        return EEResult(
            ee=ee_profile[-1] if ee_profile else 0.0,
            ee_profile=ee_profile,
            eee_profile=eee_profile,
            time_points=data.time_grid,
            effective_epe=effective_epe,
            peak_ee=max(ee_profile) if ee_profile else 0.0,
            components={
                "method": "parametric",
                "volatility": data.volatility,
                "maturity": data.remaining_maturity
            }
        )
    
    def _calculate_monte_carlo(self, data: EEInput) -> EEResult:
        """
        Monte Carlo EE calculation.
        
        EE(t) = (1/N) × Σ max(0, V_i(t))
        """
        time_grid = data.time_grid
        num_sims = data.num_simulations
        
        # Get or simulate exposure paths
        if data.exposure_paths is not None:
            paths = data.exposure_paths
        else:
            paths = self._simulate_paths(data, num_sims)
        
        # Calculate EE at each time point
        ee_profile = []
        
        for t_idx in range(len(time_grid)):
            # Positive exposures at this time
            positive_exposures = [max(0.0, path[t_idx]) for path in paths]
            
            # Expected value
            ee = sum(positive_exposures) / len(positive_exposures)
            
            # Collateral adjustment
            if data.collateral_held > 0 and time_grid[t_idx] >= data.margin_period_of_risk:
                ee = max(0.0, ee - data.collateral_held)
            
            ee_profile.append(ee)
        
        # Effective EE
        eee_profile = self._calculate_effective_ee(ee_profile)
        
        # Effective EPE
        effective_epe = self._calculate_effective_epe(eee_profile, time_grid)
        
        return EEResult(
            ee=ee_profile[-1] if ee_profile else 0.0,
            ee_profile=ee_profile,
            eee_profile=eee_profile,
            time_points=time_grid,
            effective_epe=effective_epe,
            peak_ee=max(ee_profile) if ee_profile else 0.0,
            components={
                "method": "monte_carlo",
                "num_simulations": num_sims
            }
        )
    
    def _simulate_paths(self, data: EEInput, num_sims: int) -> List[List[float]]:
        """Simulate exposure paths using GBM."""
        paths = []
        time_grid = data.time_grid
        
        for _ in range(num_sims):
            path = [data.current_mtm]
            current = data.current_mtm
            
            for i in range(1, len(time_grid)):
                dt = time_grid[i] - time_grid[i-1]
                z = random.gauss(0, 1)
                
                # GBM with mean reversion
                drift = data.drift * dt
                diffusion = data.volatility * math.sqrt(dt) * z
                
                # Mean reversion towards zero for swaps
                if data.product_type in ["irs", "cds"]:
                    reversion_speed = 0.1
                    mean_reversion = reversion_speed * (0 - current) * dt
                    current = current * math.exp(drift + diffusion) + mean_reversion
                else:
                    current = current * math.exp(drift + diffusion)
                
                path.append(current)
            
            paths.append(path)
        
        return paths
    
    def _calculate_effective_ee(self, ee_profile: List[float]) -> List[float]:
        """
        Calculate Effective EE (non-decreasing EE).
        
        EEE(t) = max(EEE(t-1), EE(t))
        """
        if not ee_profile:
            return []
        
        eee = [ee_profile[0]]
        for i in range(1, len(ee_profile)):
            eee.append(max(eee[-1], ee_profile[i]))
        
        return eee
    
    def _calculate_effective_epe(self, eee_profile: List[float], 
                                  time_grid: List[float]) -> float:
        """
        Calculate Effective EPE (time-weighted average of EEE).
        
        EPE = (1/T) × ∫EEE(t)dt ≈ (1/T) × Σ EEE(t_i) × Δt_i
        """
        if len(eee_profile) < 2:
            return eee_profile[0] if eee_profile else 0.0
        
        total_time = time_grid[-1] - time_grid[0]
        if total_time <= 0:
            return eee_profile[0]
        
        # Trapezoidal integration
        integral = 0.0
        for i in range(1, len(eee_profile)):
            dt = time_grid[i] - time_grid[i-1]
            avg_eee = (eee_profile[i] + eee_profile[i-1]) / 2
            integral += avg_eee * dt
        
        return integral / total_time
    
    def _norm_cdf(self, x: float) -> float:
        """Standard normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _norm_pdf(self, x: float) -> float:
        """Standard normal PDF."""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "method": self._method,
            "num_simulations": self._num_simulations,
            "calculate_effective": self._calculate_effective
        })
        return base_details


class EffectiveExpectedExposureCalculator(ExpectedExposureCalculator):
    """
    Dedicated Effective Expected Exposure (EEE) Calculator.
    
    EEE is used in regulatory capital calculations where the exposure
    profile must be non-decreasing to account for rollover risk.
    """
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.EEE
    
    def _calculate_impl(self, data: Any) -> EEResult:
        """Calculate with effective EE as primary output."""
        result = super()._calculate_impl(data)
        
        # Swap EE and EEE in the result emphasis
        result.components["effective_focused"] = True
        
        return result
