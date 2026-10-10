"""
QLRisk - Stressed and Peak Exposure Calculators
==============================================================

Python implementation of Stressed Exposure and Peak Exposure.

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
class StressedExposureInput:
    """Input for stressed exposure calculation."""
    current_mtm: float
    notional: float
    remaining_maturity: float
    volatility: float
    product_type: str = "irs"
    
    # Stress parameters
    stress_type: str = "historical"  # "historical", "hypothetical", "reverse"
    stress_scenario: Optional[str] = None  # e.g., "2008_crisis", "covid_2020"
    
    # Custom stress factors
    rate_shock: float = 0.0  # bps
    fx_shock: float = 0.0  # percentage
    credit_shock: float = 0.0  # bps
    volatility_shock: float = 0.0  # multiplier
    correlation_shock: float = 0.0  # absolute change
    
    # Historical parameters
    historical_returns: Optional[List[float]] = None
    lookback_period: int = 250  # trading days


@dataclass
class StressedExposureResult:
    """Result of stressed exposure calculation."""
    stressed_exposure: float
    stress_multiplier: float
    base_exposure: float
    stress_scenario: str
    components: Dict[str, Any]


@dataclass
class PeakExposureInput:
    """Input for peak exposure calculation."""
    current_mtm: float
    notional: float
    remaining_maturity: float
    volatility: float
    product_type: str = "irs"
    
    # Exposure profile (optional - will be simulated if not provided)
    ee_profile: Optional[List[float]] = None
    pfe_profile: Optional[List[float]] = None
    time_grid: Optional[List[float]] = None
    
    # Simulation parameters
    num_simulations: int = 10000
    confidence_level: float = 0.95
    
    # Collateral
    collateral_held: float = 0.0


@dataclass
class PeakExposureResult:
    """Result of peak exposure calculation."""
    peak_exposure: float
    peak_time: float
    average_exposure: float
    exposure_profile: List[float]
    time_grid: List[float]
    components: Dict[str, Any]


class StressedExposureCalculator(ExposureCalculator):
    """
    Stressed Exposure Calculator.
    
    Calculates exposure under stress scenarios:
    - Historical stress (using past crisis data)
    - Hypothetical stress (regulatory scenarios)
    - Reverse stress (find scenario causing target loss)
    
    Stressed Exposure = f(Base Exposure, Stress Factors)
    """
    
    # Historical stress scenarios
    HISTORICAL_SCENARIOS = {
        "2008_crisis": {
            "rate_shock": -200,  # bps
            "fx_shock": 0.20,  # 20% depreciation
            "credit_shock": 300,  # bps widening
            "volatility_shock": 2.5,  # vol multiplier
            "correlation_shock": 0.3
        },
        "covid_2020": {
            "rate_shock": -150,
            "fx_shock": 0.15,
            "credit_shock": 200,
            "volatility_shock": 3.0,
            "correlation_shock": 0.4
        },
        "eu_debt_2011": {
            "rate_shock": 100,
            "fx_shock": 0.10,
            "credit_shock": 400,
            "volatility_shock": 2.0,
            "correlation_shock": 0.2
        },
        "rate_shock_up": {
            "rate_shock": 200,
            "fx_shock": 0.0,
            "credit_shock": 50,
            "volatility_shock": 1.5,
            "correlation_shock": 0.0
        },
        "rate_shock_down": {
            "rate_shock": -200,
            "fx_shock": 0.0,
            "credit_shock": 50,
            "volatility_shock": 1.5,
            "correlation_shock": 0.0
        }
    }
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        """
        Initialize Stressed Exposure calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - stress_type: Type of stress to apply
                - default_scenario: Default scenario name
        """
        config = config or {}
        name = name or self.__class__.__name__
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._stress_type = config.get("stress_type", "historical")
        self._default_scenario = config.get("default_scenario", "2008_crisis")
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.STRESSED_EXPOSURE
    
    def _calculate_impl(self, data: Any) -> StressedExposureResult:
        """
        Calculate stressed exposure.
        
        Args:
            data: StressedExposureInput or dictionary
            
        Returns:
            StressedExposureResult with stressed exposure
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, StressedExposureInput)
            data = StressedExposureInput(**filtered_data)
        
        stress_type = data.stress_type or self._stress_type
        
        if stress_type == "historical":
            return self._calculate_historical_stress(data)
        elif stress_type == "hypothetical":
            return self._calculate_hypothetical_stress(data)
        elif stress_type == "reverse":
            return self._calculate_reverse_stress(data)
        else:
            raise ValueError(f"Unknown stress type: {stress_type}")
    
    def _calculate_historical_stress(self, data: StressedExposureInput) -> StressedExposureResult:
        """Apply historical stress scenario."""
        # Get scenario
        scenario_name = data.stress_scenario or self._default_scenario
        
        if scenario_name in self.HISTORICAL_SCENARIOS:
            scenario = self.HISTORICAL_SCENARIOS[scenario_name]
        else:
            # Use custom stress factors
            scenario = {
                "rate_shock": data.rate_shock,
                "fx_shock": data.fx_shock,
                "credit_shock": data.credit_shock,
                "volatility_shock": data.volatility_shock,
                "correlation_shock": data.correlation_shock
            }
        
        return self._apply_stress_scenario(data, scenario, scenario_name)
    
    def _calculate_hypothetical_stress(self, data: StressedExposureInput) -> StressedExposureResult:
        """Apply hypothetical/regulatory stress scenario."""
        # Regulatory stress factors (e.g., CCAR, DFAST)
        scenario = {
            "rate_shock": data.rate_shock if data.rate_shock != 0 else -300,
            "fx_shock": data.fx_shock if data.fx_shock != 0 else 0.25,
            "credit_shock": data.credit_shock if data.credit_shock != 0 else 400,
            "volatility_shock": data.volatility_shock if data.volatility_shock != 0 else 2.0,
            "correlation_shock": data.correlation_shock
        }
        
        return self._apply_stress_scenario(data, scenario, "hypothetical")
    
    def _calculate_reverse_stress(self, data: StressedExposureInput) -> StressedExposureResult:
        """
        Reverse stress testing.
        
        Find the stress scenario that would cause a specific level of loss.
        """
        # Target: double the current exposure
        target_multiplier = 2.0
        
        # Binary search for stress level
        low, high = 0.0, 5.0
        
        for _ in range(20):  # Max iterations
            mid = (low + high) / 2
            
            scenario = {
                "rate_shock": -200 * mid,
                "fx_shock": 0.20 * mid,
                "credit_shock": 300 * mid,
                "volatility_shock": 1 + mid,
                "correlation_shock": 0.3 * mid
            }
            
            result = self._apply_stress_scenario(data, scenario, "reverse_search")
            
            if result.stress_multiplier < target_multiplier:
                low = mid
            else:
                high = mid
        
        # Final scenario
        final_scenario = {
            "rate_shock": -200 * mid,
            "fx_shock": 0.20 * mid,
            "credit_shock": 300 * mid,
            "volatility_shock": 1 + mid,
            "correlation_shock": 0.3 * mid
        }
        
        return self._apply_stress_scenario(data, final_scenario, "reverse_stress")
    
    def _apply_stress_scenario(self, data: StressedExposureInput,
                                scenario: Dict[str, float],
                                scenario_name: str) -> StressedExposureResult:
        """Apply stress scenario to calculate stressed exposure."""
        # Base exposure
        base_exposure = max(0.0, data.current_mtm)
        
        # Calculate stress impacts
        impacts = {}
        
        # Rate shock impact
        if data.product_type in ["irs", "fra"]:
            # Duration-based approximation
            duration = min(data.remaining_maturity, 10) * 0.8
            rate_impact = abs(scenario["rate_shock"]) / 10000 * duration * data.notional
            impacts["rate"] = rate_impact
        else:
            impacts["rate"] = 0
        
        # FX shock impact
        if data.product_type in ["fx_forward", "fx_option"]:
            fx_impact = abs(scenario["fx_shock"]) * data.notional
            impacts["fx"] = fx_impact
        else:
            impacts["fx"] = 0
        
        # Credit shock impact
        if data.product_type in ["cds"]:
            credit_impact = abs(scenario["credit_shock"]) / 10000 * data.notional * data.remaining_maturity
            impacts["credit"] = credit_impact
        else:
            impacts["credit"] = 0
        
        # Volatility shock impact
        vol_multiplier = max(1.0, scenario["volatility_shock"])
        vol_impact = data.volatility * (vol_multiplier - 1) * data.notional * math.sqrt(data.remaining_maturity)
        impacts["volatility"] = vol_impact
        
        # Total stressed exposure
        total_impact = sum(impacts.values())
        stressed_exposure = base_exposure + total_impact
        
        # Stress multiplier
        stress_multiplier = stressed_exposure / base_exposure if base_exposure > 0 else 1.0
        
        return StressedExposureResult(
            stressed_exposure=stressed_exposure,
            stress_multiplier=stress_multiplier,
            base_exposure=base_exposure,
            stress_scenario=scenario_name,
            components={
                "scenario": scenario,
                "impacts": impacts,
                "total_impact": total_impact
            }
        )
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "stress_type": self._stress_type,
            "default_scenario": self._default_scenario,
            "available_scenarios": list(self.HISTORICAL_SCENARIOS.keys())
        })
        return base_details


class PeakExposureCalculator(ExposureCalculator):
    """
    Peak Exposure Calculator.
    
    Peak Exposure is the maximum exposure over the life of a transaction.
    
    Peak Exposure = max(EE(t)) for all t in [0, T]
    
    Or at a confidence level:
    Peak PFE = max(PFE(t)) for all t in [0, T]
    """
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        """
        Initialize Peak Exposure calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - method: 'ee_based' or 'pfe_based'
                - num_simulations: For Monte Carlo
                - confidence_level: For PFE-based peak
        """
        config = config or {}
        name = name or self.__class__.__name__
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._method = config.get("method", "pfe_based")
        self._num_simulations = config.get("num_simulations", 10000)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.PEAK_EXPOSURE
    
    def _calculate_impl(self, data: Any) -> PeakExposureResult:
        """
        Calculate peak exposure.
        
        Args:
            data: PeakExposureInput or dictionary
            
        Returns:
            PeakExposureResult with peak exposure
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, PeakExposureInput)
            data = PeakExposureInput(**filtered_data)
        
        # Generate time grid if not provided
        if data.time_grid is None:
            data.time_grid = self._generate_time_grid(data.remaining_maturity)
        
        # Use provided profiles or calculate
        if self._method == "ee_based":
            if data.ee_profile is not None:
                exposure_profile = data.ee_profile
            else:
                exposure_profile = self._calculate_ee_profile(data)
        else:  # pfe_based
            if data.pfe_profile is not None:
                exposure_profile = data.pfe_profile
            else:
                exposure_profile = self._calculate_pfe_profile(data)
        
        # Find peak
        peak_exposure = max(exposure_profile)
        peak_idx = exposure_profile.index(peak_exposure)
        peak_time = data.time_grid[peak_idx]
        
        # Average exposure
        average_exposure = sum(exposure_profile) / len(exposure_profile)
        
        return PeakExposureResult(
            peak_exposure=peak_exposure,
            peak_time=peak_time,
            average_exposure=average_exposure,
            exposure_profile=exposure_profile,
            time_grid=data.time_grid,
            components={
                "method": self._method,
                "peak_index": peak_idx,
                "profile_length": len(exposure_profile),
                "collateral_held": data.collateral_held
            }
        )
    
    def _generate_time_grid(self, maturity: float, num_points: int = 20) -> List[float]:
        """Generate time grid."""
        if maturity <= 0:
            return [0.0]
        step = maturity / num_points
        return [i * step for i in range(num_points + 1)]
    
    def _calculate_ee_profile(self, data: PeakExposureInput) -> List[float]:
        """Calculate Expected Exposure profile via simulation."""
        ee_profile = []
        num_sims = self._num_simulations
        
        for t in data.time_grid:
            if t == 0:
                ee = max(0.0, data.current_mtm)
            else:
                # Simulate exposures at time t
                exposures = []
                for _ in range(num_sims):
                    z = random.gauss(0, 1)
                    future_value = data.current_mtm + data.volatility * math.sqrt(t) * data.notional * z
                    exposures.append(max(0.0, future_value))
                
                ee = sum(exposures) / num_sims
                
                # Collateral adjustment
                if data.collateral_held > 0:
                    ee = max(0.0, ee - data.collateral_held)
            
            ee_profile.append(ee)
        
        return ee_profile
    
    def _calculate_pfe_profile(self, data: PeakExposureInput) -> List[float]:
        """Calculate PFE profile via simulation."""
        pfe_profile = []
        num_sims = self._num_simulations
        z_alpha = self._norm_inv(data.confidence_level)
        
        for t in data.time_grid:
            if t == 0:
                pfe = max(0.0, data.current_mtm)
            else:
                # Simulate exposures at time t
                exposures = []
                for _ in range(num_sims):
                    z = random.gauss(0, 1)
                    future_value = data.current_mtm + data.volatility * math.sqrt(t) * data.notional * z
                    exposures.append(max(0.0, future_value))
                
                exposures.sort()
                pfe_idx = int(data.confidence_level * num_sims)
                pfe = exposures[min(pfe_idx, num_sims - 1)]
                
                # Collateral adjustment
                if data.collateral_held > 0:
                    pfe = max(0.0, pfe - data.collateral_held)
            
            pfe_profile.append(pfe)
        
        return pfe_profile
    
    def _norm_inv(self, p: float) -> float:
        """Inverse standard normal CDF (approximation)."""
        if p <= 0 or p >= 1:
            return 0.0
        
        a = [
            -3.969683028665376e+01, 2.209460984245205e+02,
            -2.759285104469687e+02, 1.383577518672690e+02,
            -3.066479806614716e+01, 2.506628277459239e+00
        ]
        b = [
            -5.447609879822406e+01, 1.615858368580409e+02,
            -1.556989798598866e+02, 6.680131188771972e+01,
            -1.328068155288572e+01
        ]
        
        q = p - 0.5
        r = q * q
        return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
               (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "method": self._method,
            "num_simulations": self._num_simulations
        })
        return base_details
