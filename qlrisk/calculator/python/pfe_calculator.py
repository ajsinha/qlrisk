"""
QLRisk - Potential Future Exposure (PFE) Calculator
==================================================================

Python implementation of PFE calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import math
import random

from ..base import (
    filter_dict_for_dataclass,
    ExposureCalculator, CalculatorType, ImplementationType
)


@dataclass
class PFEInput:
    """Input data for PFE calculation."""
    # Current state
    current_mtm: float
    notional: float
    remaining_maturity: float  # in years
    
    # Product parameters
    volatility: float  # Annual volatility
    product_type: str = "irs"  # irs, fx_forward, fx_option, cds, etc.
    
    # Risk factors
    interest_rate: float = 0.05
    fx_rate: float = 1.0
    credit_spread: float = 0.01
    
    # Collateral
    collateral_held: float = 0.0
    margin_period_of_risk: float = 10/252  # MPOR in years
    
    # Simulation parameters
    num_simulations: int = 10000
    time_grid: Optional[List[float]] = None
    
    # For Monte Carlo paths (optional - can be provided externally)
    exposure_paths: Optional[List[List[float]]] = None


@dataclass
class PFEResult:
    """Result of PFE calculation."""
    pfe: float  # PFE at specified confidence level
    pfe_profile: List[float]  # PFE over time
    time_points: List[float]
    peak_pfe: float
    average_pfe: float
    confidence_level: float
    components: Dict[str, Any]


class PFECalculator(ExposureCalculator):
    """
    Potential Future Exposure (PFE) Calculator.
    
    PFE estimates the maximum exposure at a future date at a given
    confidence level (e.g., 95% or 99%).
    
    Methods supported:
    - Parametric (analytical approximation)
    - Monte Carlo simulation
    - Add-on based (regulatory approach)
    
    PFE_α(t) = Quantile_α(max(0, V(t)))
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize PFE calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - confidence_level: PFE confidence level (default 0.95)
                - method: 'parametric', 'monte_carlo', or 'add_on'
                - num_simulations: Number of MC simulations
                - time_horizon: Maximum time horizon
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._method = config.get("method", "parametric")
        self._num_simulations = config.get("num_simulations", 10000)
        self._time_horizon = config.get("time_horizon", 1.0)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.PFE
    
    def _calculate_impl(self, data: Any) -> PFEResult:
        """
        Calculate PFE.
        
        Args:
            data: PFEInput or dictionary with required fields
            
        Returns:
            PFEResult with PFE profile and statistics
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, PFEInput)
            data = PFEInput(**filtered_data)
        
        # Generate time grid if not provided
        if data.time_grid is None:
            data.time_grid = self._generate_time_grid(data.remaining_maturity)
        
        # Calculate PFE profile based on method
        if self._method == "parametric":
            return self._calculate_parametric(data)
        elif self._method == "monte_carlo":
            return self._calculate_monte_carlo(data)
        elif self._method == "add_on":
            return self._calculate_add_on(data)
        else:
            raise ValueError(f"Unknown PFE method: {self._method}")
    
    def _generate_time_grid(self, maturity: float, num_points: int = 20) -> List[float]:
        """Generate time grid for PFE calculation."""
        if maturity <= 0:
            return [0.0]
        
        step = maturity / num_points
        return [i * step for i in range(num_points + 1)]
    
    def _calculate_parametric(self, data: PFEInput) -> PFEResult:
        """
        Parametric PFE calculation.
        
        Uses analytical approximation based on product type and volatility.
        
        For a derivative: PFE(t) = MTM(0) + σ × √t × N^(-1)(α) × Notional × Factor
        """
        pfe_profile = []
        z_score = self._norm_inv(self._confidence_level)
        
        for t in data.time_grid:
            if t == 0:
                pfe = max(0.0, data.current_mtm)
            else:
                # Time-scaled volatility
                vol_scaled = data.volatility * math.sqrt(t)
                
                # Product-specific factor
                factor = self._get_product_factor(data.product_type, t, data.remaining_maturity)
                
                # Potential increase in MTM
                potential_increase = z_score * vol_scaled * data.notional * factor
                
                # PFE = max(0, E[MTM(t)] + potential_increase)
                expected_mtm = self._get_expected_mtm(data, t)
                pfe = max(0.0, expected_mtm + potential_increase)
                
                # Adjust for collateral
                if data.collateral_held > 0:
                    pfe = max(0.0, pfe - data.collateral_held)
            
            pfe_profile.append(pfe)
        
        # Calculate summary statistics
        peak_pfe = max(pfe_profile)
        average_pfe = sum(pfe_profile) / len(pfe_profile)
        
        # PFE at the confidence level for the full horizon
        final_pfe = pfe_profile[-1] if pfe_profile else 0.0
        
        return PFEResult(
            pfe=peak_pfe,
            pfe_profile=pfe_profile,
            time_points=data.time_grid,
            peak_pfe=peak_pfe,
            average_pfe=average_pfe,
            confidence_level=self._confidence_level,
            components={
                "method": "parametric",
                "volatility": data.volatility,
                "z_score": z_score,
                "product_type": data.product_type
            }
        )
    
    def _calculate_monte_carlo(self, data: PFEInput) -> PFEResult:
        """
        Monte Carlo PFE calculation.
        
        Simulates exposure paths and calculates percentile.
        """
        num_sims = data.num_simulations
        time_grid = data.time_grid
        
        # Use provided paths or simulate
        if data.exposure_paths is not None:
            exposure_paths = data.exposure_paths
        else:
            exposure_paths = self._simulate_exposure_paths(data, num_sims)
        
        # Calculate PFE at each time point
        pfe_profile = []
        
        for t_idx in range(len(time_grid)):
            exposures_at_t = [max(0.0, path[t_idx]) for path in exposure_paths]
            exposures_at_t.sort()
            
            # Get percentile
            pfe_idx = int(self._confidence_level * len(exposures_at_t))
            pfe_at_t = exposures_at_t[min(pfe_idx, len(exposures_at_t) - 1)]
            
            # Adjust for collateral with MPOR
            if data.collateral_held > 0 and time_grid[t_idx] >= data.margin_period_of_risk:
                pfe_at_t = max(0.0, pfe_at_t - data.collateral_held)
            
            pfe_profile.append(pfe_at_t)
        
        peak_pfe = max(pfe_profile)
        average_pfe = sum(pfe_profile) / len(pfe_profile)
        
        return PFEResult(
            pfe=peak_pfe,
            pfe_profile=pfe_profile,
            time_points=time_grid,
            peak_pfe=peak_pfe,
            average_pfe=average_pfe,
            confidence_level=self._confidence_level,
            components={
                "method": "monte_carlo",
                "num_simulations": num_sims,
                "volatility": data.volatility
            }
        )
    
    def _simulate_exposure_paths(self, data: PFEInput, 
                                  num_sims: int) -> List[List[float]]:
        """
        Simulate exposure paths using geometric Brownian motion.
        """
        paths = []
        time_grid = data.time_grid
        dt = time_grid[1] - time_grid[0] if len(time_grid) > 1 else 0.01
        
        for _ in range(num_sims):
            path = [data.current_mtm]
            current_value = data.current_mtm
            
            for i in range(1, len(time_grid)):
                # GBM step
                z = random.gauss(0, 1)
                drift = (data.interest_rate - 0.5 * data.volatility ** 2) * dt
                diffusion = data.volatility * math.sqrt(dt) * z
                
                # Update value (simplified exposure dynamics)
                factor = math.exp(drift + diffusion)
                current_value = current_value * factor
                
                # Add some mean reversion for swaps
                if data.product_type in ["irs", "cds"]:
                    mean_reversion = 0.1 * (0 - current_value) * dt
                    current_value += mean_reversion
                
                path.append(current_value)
            
            paths.append(path)
        
        return paths
    
    def _calculate_add_on(self, data: PFEInput) -> PFEResult:
        """
        Regulatory add-on based PFE calculation.
        
        Uses standardized add-on factors by product type and maturity.
        """
        pfe_profile = []
        
        for t in data.time_grid:
            remaining = max(0.0, data.remaining_maturity - t)
            
            # Get add-on factor
            add_on_factor = self._get_add_on_factor(data.product_type, remaining)
            
            # PFE = Current Exposure + Add-on
            ce = max(0.0, self._get_expected_mtm(data, t))
            add_on = data.notional * add_on_factor
            pfe = ce + add_on
            
            # Adjust for collateral
            if data.collateral_held > 0:
                pfe = max(0.0, pfe - data.collateral_held)
            
            pfe_profile.append(pfe)
        
        peak_pfe = max(pfe_profile)
        average_pfe = sum(pfe_profile) / len(pfe_profile)
        
        return PFEResult(
            pfe=peak_pfe,
            pfe_profile=pfe_profile,
            time_points=data.time_grid,
            peak_pfe=peak_pfe,
            average_pfe=average_pfe,
            confidence_level=self._confidence_level,
            components={
                "method": "add_on",
                "product_type": data.product_type
            }
        )
    
    def _get_product_factor(self, product_type: str, t: float, maturity: float) -> float:
        """Get product-specific factor for parametric calculation."""
        remaining = max(0.0, maturity - t)
        
        factors = {
            "irs": min(1.0, remaining / 5.0),  # Duration-like factor
            "fx_forward": 1.0,
            "fx_option": 1.2,  # Higher for optionality
            "cds": min(1.0, remaining / 5.0),
            "equity_option": 1.5
        }
        
        return factors.get(product_type, 1.0)
    
    def _get_add_on_factor(self, product_type: str, remaining_maturity: float) -> float:
        """
        Get regulatory add-on factor.
        
        Based on Basel III standardized approach.
        """
        # Add-on factors by product type and maturity bucket
        if product_type == "irs":
            if remaining_maturity <= 1:
                return 0.005
            elif remaining_maturity <= 5:
                return 0.01
            else:
                return 0.015
        elif product_type in ["fx_forward", "fx_option"]:
            if remaining_maturity <= 1:
                return 0.04
            elif remaining_maturity <= 5:
                return 0.06
            else:
                return 0.08
        elif product_type == "cds":
            if remaining_maturity <= 1:
                return 0.05
            elif remaining_maturity <= 5:
                return 0.06
            else:
                return 0.08
        elif product_type in ["equity_option", "equity_forward"]:
            return 0.08
        else:
            return 0.05  # Default
    
    def _get_expected_mtm(self, data: PFEInput, t: float) -> float:
        """
        Get expected MTM at future time t.
        
        Simplified: linear interpolation towards zero at maturity.
        """
        if t >= data.remaining_maturity:
            return 0.0
        
        decay_factor = 1 - t / data.remaining_maturity
        return data.current_mtm * decay_factor
    
    def _norm_inv(self, p: float) -> float:
        """Inverse of standard normal CDF (approximation)."""
        if p <= 0 or p >= 1:
            raise ValueError("Probability must be between 0 and 1")
        
        # Rational approximation
        a = [
            -3.969683028665376e+01,
            2.209460984245205e+02,
            -2.759285104469687e+02,
            1.383577518672690e+02,
            -3.066479806614716e+01,
            2.506628277459239e+00
        ]
        b = [
            -5.447609879822406e+01,
            1.615858368580409e+02,
            -1.556989798598866e+02,
            6.680131188771972e+01,
            -1.328068155288572e+01
        ]
        c = [
            -7.784894002430293e-03,
            -3.223964580411365e-01,
            -2.400758277161838e+00,
            -2.549732539343734e+00,
            4.374664141464968e+00,
            2.938163982698783e+00
        ]
        d = [
            7.784695709041462e-03,
            3.224671290700398e-01,
            2.445134137142996e+00,
            3.754408661907416e+00
        ]
        
        p_low = 0.02425
        p_high = 1 - p_low
        
        if p < p_low:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                   ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
                   (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
        else:
            q = math.sqrt(-2 * math.log(1 - p))
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                    ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "method": self._method,
            "num_simulations": self._num_simulations
        })
        return base_details
