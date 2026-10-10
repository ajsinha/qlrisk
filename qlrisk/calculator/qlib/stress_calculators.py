"""
QLRisk - QuantLib Stressed and Peak Exposure Calculators
=======================================================================

QuantLib-enhanced implementation of Stressed Exposure and Peak Exposure.

Mathematical Framework:
----------------------
Stressed Exposure = Base Exposure × Stress Multiplier + Stress Impact

Where stress impacts are computed using:
- Duration-based rate sensitivity
- Delta-based FX sensitivity
- DV01-based credit sensitivity
- Vega-based volatility sensitivity

Peak Exposure = max(Exposure(t)) for t ∈ [0, T]

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from ..base import (
    ExposureCalculator, CalculatorType, ImplementationType
)


# Check for QuantLib availability
try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False
    ql = None


class StressType(Enum):
    """Stress testing type."""
    HISTORICAL = "historical"
    HYPOTHETICAL = "hypothetical"
    REVERSE = "reverse"
    SENSITIVITY = "sensitivity"
    SCENARIO = "scenario"


class PeakExposureMethod(Enum):
    """Peak exposure calculation method."""
    EE_BASED = "ee_based"
    PFE_BASED = "pfe_based"
    MONTE_CARLO = "monte_carlo"
    PARAMETRIC = "parametric"


@dataclass
class QLStressScenario:
    """Stress scenario definition."""
    name: str
    rate_shock: float = 0.0  # bps
    fx_shock: float = 0.0  # percentage
    credit_shock: float = 0.0  # bps
    volatility_shock: float = 1.0  # multiplier
    correlation_shock: float = 0.0  # absolute change
    equity_shock: float = 0.0  # percentage
    commodity_shock: float = 0.0  # percentage
    description: str = ""


@dataclass
class QLStressedExposureInput:
    """Input for QuantLib stressed exposure calculation."""
    current_mtm: float
    notional: float
    remaining_maturity: float
    volatility: float
    product_type: str = "irs"
    
    # Stress parameters
    stress_type: str = "historical"  # "historical", "hypothetical", "reverse", "sensitivity"
    stress_scenario: Optional[str] = None
    
    # Custom stress factors
    rate_shock: float = 0.0  # bps
    fx_shock: float = 0.0  # percentage
    credit_shock: float = 0.0  # bps
    volatility_shock: float = 1.0  # multiplier
    correlation_shock: float = 0.0  # absolute change
    
    # Sensitivity inputs (for more accurate stress calculation)
    duration: Optional[float] = None  # modified duration
    dv01: Optional[float] = None  # dollar value of 1bp
    fx_delta: Optional[float] = None  # FX delta
    vega: Optional[float] = None  # vega
    
    # Historical parameters
    historical_returns: Optional[List[float]] = None
    lookback_period: int = 250
    
    # Reverse stress target
    target_loss: Optional[float] = None


@dataclass
class QLStressedExposureResult:
    """Result of QuantLib stressed exposure calculation."""
    stressed_exposure: float
    stress_multiplier: float
    base_exposure: float
    stress_scenario: str
    stress_pnl: float
    components: Dict[str, Any] = field(default_factory=dict)
    sensitivities: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QLPeakExposureInput:
    """Input for QuantLib peak exposure calculation."""
    current_mtm: float
    notional: float
    remaining_maturity: float
    volatility: float
    product_type: str = "irs"
    
    # Exposure profiles (optional)
    ee_profile: Optional[List[float]] = None
    pfe_profile: Optional[List[float]] = None
    time_grid: Optional[List[float]] = None
    
    # Simulation parameters
    num_simulations: int = 10000
    confidence_level: float = 0.95
    num_time_steps: int = 20
    
    # Model parameters
    drift: float = 0.0
    mean_reversion: float = 0.0
    
    # Collateral
    collateral_held: float = 0.0
    threshold: float = 0.0
    mta: float = 0.0


@dataclass
class QLPeakExposureResult:
    """Result of QuantLib peak exposure calculation."""
    peak_exposure: float
    peak_time: float
    average_exposure: float
    effective_epe: float
    exposure_profile: List[float]
    time_grid: List[float]
    components: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class QLStressedExposureCalculator(ExposureCalculator):
    """
    QuantLib-enhanced Stressed Exposure Calculator.
    
    Calculates exposure under various stress scenarios:
    - Historical stress (using past crisis data)
    - Hypothetical stress (regulatory scenarios)
    - Reverse stress (find scenario causing target loss)
    - Sensitivity-based stress
    
    Uses QuantLib for:
    - Random number generation for Monte Carlo
    - Statistical distributions
    - Term structure construction
    
    Stress Impact = Σ (Sensitivity_i × Shock_i)
    """
    
    # Pre-defined historical stress scenarios
    HISTORICAL_SCENARIOS = {
        "2008_crisis": QLStressScenario(
            name="2008 Financial Crisis",
            rate_shock=-200,
            fx_shock=0.20,
            credit_shock=300,
            volatility_shock=2.5,
            correlation_shock=0.3,
            equity_shock=-0.40,
            commodity_shock=-0.30,
            description="Lehman Brothers collapse, global financial crisis"
        ),
        "covid_2020": QLStressScenario(
            name="COVID-19 Pandemic",
            rate_shock=-150,
            fx_shock=0.15,
            credit_shock=200,
            volatility_shock=3.0,
            correlation_shock=0.4,
            equity_shock=-0.35,
            commodity_shock=-0.50,
            description="COVID-19 pandemic market disruption"
        ),
        "eu_debt_2011": QLStressScenario(
            name="European Debt Crisis",
            rate_shock=100,
            fx_shock=0.10,
            credit_shock=400,
            volatility_shock=2.0,
            correlation_shock=0.2,
            equity_shock=-0.25,
            commodity_shock=-0.10,
            description="European sovereign debt crisis"
        ),
        "rate_shock_up": QLStressScenario(
            name="Interest Rate Shock Up",
            rate_shock=200,
            fx_shock=0.0,
            credit_shock=50,
            volatility_shock=1.5,
            correlation_shock=0.0,
            equity_shock=-0.10,
            description="Sudden rate increase scenario"
        ),
        "rate_shock_down": QLStressScenario(
            name="Interest Rate Shock Down",
            rate_shock=-200,
            fx_shock=0.0,
            credit_shock=50,
            volatility_shock=1.5,
            correlation_shock=0.0,
            equity_shock=0.05,
            description="Sudden rate decrease scenario"
        ),
        "fx_crisis": QLStressScenario(
            name="FX Crisis",
            rate_shock=100,
            fx_shock=0.30,
            credit_shock=150,
            volatility_shock=2.0,
            correlation_shock=0.2,
            equity_shock=-0.15,
            description="Currency crisis with sharp depreciation"
        ),
        "stagflation": QLStressScenario(
            name="Stagflation",
            rate_shock=300,
            fx_shock=0.05,
            credit_shock=200,
            volatility_shock=1.8,
            correlation_shock=0.1,
            equity_shock=-0.20,
            commodity_shock=0.40,
            description="High inflation with economic stagnation"
        )
    }
    
    # Regulatory stress scenarios (CCAR, DFAST)
    REGULATORY_SCENARIOS = {
        "severely_adverse": QLStressScenario(
            name="Severely Adverse",
            rate_shock=-300,
            fx_shock=0.25,
            credit_shock=400,
            volatility_shock=2.5,
            correlation_shock=0.35,
            equity_shock=-0.50,
            description="Federal Reserve severely adverse scenario"
        ),
        "adverse": QLStressScenario(
            name="Adverse",
            rate_shock=-100,
            fx_shock=0.15,
            credit_shock=200,
            volatility_shock=1.8,
            correlation_shock=0.2,
            equity_shock=-0.25,
            description="Federal Reserve adverse scenario"
        ),
        "baseline": QLStressScenario(
            name="Baseline",
            rate_shock=50,
            fx_shock=0.02,
            credit_shock=25,
            volatility_shock=1.0,
            correlation_shock=0.0,
            equity_shock=0.05,
            description="Federal Reserve baseline scenario"
        )
    }
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize QuantLib Stressed Exposure calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - stress_type: Type of stress
                - default_scenario: Default scenario name
                - use_sensitivities: Use provided sensitivities
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.QUANTLIB
        self._stress_type = config.get("stress_type", "historical")
        self._default_scenario = config.get("default_scenario", "2008_crisis")
        self._use_sensitivities = config.get("use_sensitivities", True)
        
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibStressedExposureCalculator. "
                "Install with: pip install QuantLib"
            )
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.STRESSED_EXPOSURE
    
    def _calculate_impl(self, data: Any) -> QLStressedExposureResult:
        """
        Calculate stressed exposure using QuantLib.
        
        Args:
            data: QLStressedExposureInput or dictionary
            
        Returns:
            QLStressedExposureResult with stressed exposure
        """
        if isinstance(data, dict):
            data = QLStressedExposureInput(**data)
        
        stress_type = data.stress_type or self._stress_type
        
        if stress_type == "historical":
            return self._calculate_historical_stress(data)
        elif stress_type == "hypothetical":
            return self._calculate_hypothetical_stress(data)
        elif stress_type == "reverse":
            return self._calculate_reverse_stress(data)
        elif stress_type == "sensitivity":
            return self._calculate_sensitivity_stress(data)
        else:
            raise ValueError(f"Unknown stress type: {stress_type}")
    
    def _calculate_historical_stress(
        self,
        data: QLStressedExposureInput
    ) -> QLStressedExposureResult:
        """Apply historical stress scenario."""
        scenario_name = data.stress_scenario or self._default_scenario
        
        if scenario_name in self.HISTORICAL_SCENARIOS:
            scenario = self.HISTORICAL_SCENARIOS[scenario_name]
        else:
            # Use custom stress factors
            scenario = QLStressScenario(
                name=scenario_name or "custom",
                rate_shock=data.rate_shock,
                fx_shock=data.fx_shock,
                credit_shock=data.credit_shock,
                volatility_shock=data.volatility_shock,
                correlation_shock=data.correlation_shock
            )
        
        return self._apply_stress_scenario(data, scenario)
    
    def _calculate_hypothetical_stress(
        self,
        data: QLStressedExposureInput
    ) -> QLStressedExposureResult:
        """Apply hypothetical/regulatory stress scenario."""
        scenario_name = data.stress_scenario or "severely_adverse"
        
        if scenario_name in self.REGULATORY_SCENARIOS:
            scenario = self.REGULATORY_SCENARIOS[scenario_name]
        else:
            # Custom hypothetical scenario
            scenario = QLStressScenario(
                name="hypothetical",
                rate_shock=data.rate_shock if data.rate_shock != 0 else -300,
                fx_shock=data.fx_shock if data.fx_shock != 0 else 0.25,
                credit_shock=data.credit_shock if data.credit_shock != 0 else 400,
                volatility_shock=data.volatility_shock if data.volatility_shock != 1.0 else 2.0,
                correlation_shock=data.correlation_shock
            )
        
        return self._apply_stress_scenario(data, scenario)
    
    def _calculate_reverse_stress(
        self,
        data: QLStressedExposureInput
    ) -> QLStressedExposureResult:
        """
        Reverse stress testing using QuantLib optimization.
        
        Find the stress scenario that would cause a specific level of loss.
        """
        # Target loss (default: 2x current exposure)
        target_loss = data.target_loss if data.target_loss else data.current_mtm * 2
        
        # Base exposure
        base_exposure = max(0.0, data.current_mtm)
        if base_exposure == 0:
            base_exposure = data.notional * 0.05
        
        # Required stress multiplier
        required_multiplier = target_loss / base_exposure if base_exposure > 0 else 2.0
        
        # Use QuantLib random number generator for sensitivity analysis
        rng = ql.MersenneTwisterUniformRng(42)
        
        # Estimate required shocks to achieve target
        # Iterative approach to find reverse stress parameters
        best_scenario = None
        best_diff = float('inf')
        
        for _ in range(100):
            # Random shock combinations
            rate_shock = (rng.next().value() - 0.5) * 600  # -300 to +300
            fx_shock = rng.next().value() * 0.4  # 0 to 40%
            credit_shock = rng.next().value() * 500  # 0 to 500 bps
            vol_shock = 1.0 + rng.next().value() * 2.0  # 1x to 3x
            
            test_scenario = QLStressScenario(
                name="reverse_test",
                rate_shock=rate_shock,
                fx_shock=fx_shock,
                credit_shock=credit_shock,
                volatility_shock=vol_shock
            )
            
            result = self._apply_stress_scenario(data, test_scenario)
            diff = abs(result.stressed_exposure - target_loss)
            
            if diff < best_diff:
                best_diff = diff
                best_scenario = test_scenario
        
        # Apply best found scenario
        best_scenario.name = "reverse_stress"
        return self._apply_stress_scenario(data, best_scenario)
    
    def _calculate_sensitivity_stress(
        self,
        data: QLStressedExposureInput
    ) -> QLStressedExposureResult:
        """Calculate stress using provided sensitivities."""
        scenario = QLStressScenario(
            name="sensitivity_based",
            rate_shock=data.rate_shock,
            fx_shock=data.fx_shock,
            credit_shock=data.credit_shock,
            volatility_shock=data.volatility_shock,
            correlation_shock=data.correlation_shock
        )
        
        return self._apply_stress_scenario(data, scenario, use_exact_sensitivities=True)
    
    def _apply_stress_scenario(
        self,
        data: QLStressedExposureInput,
        scenario: QLStressScenario,
        use_exact_sensitivities: bool = False
    ) -> QLStressedExposureResult:
        """
        Apply stress scenario to calculate stressed exposure.
        
        Uses sensitivity-based approach:
        Stress Impact = Σ (Sensitivity_i × Shock_i)
        """
        # Base exposure
        base_exposure = max(0.0, data.current_mtm)
        if base_exposure == 0:
            base_exposure = data.notional * 0.05
        
        # Calculate sensitivities
        sensitivities = self._calculate_sensitivities(data, use_exact_sensitivities)
        
        # Calculate stress impacts
        impacts = {}
        
        # Interest rate impact
        if scenario.rate_shock != 0:
            dv01 = sensitivities.get("dv01", 0)
            rate_impact = dv01 * abs(scenario.rate_shock)
            impacts["rate"] = rate_impact
        else:
            impacts["rate"] = 0
        
        # FX impact
        if scenario.fx_shock != 0:
            fx_delta = sensitivities.get("fx_delta", 0)
            fx_impact = fx_delta * abs(scenario.fx_shock)
            impacts["fx"] = fx_impact
        else:
            impacts["fx"] = 0
        
        # Credit impact
        if scenario.credit_shock != 0:
            credit_dv01 = sensitivities.get("credit_dv01", 0)
            credit_impact = credit_dv01 * abs(scenario.credit_shock)
            impacts["credit"] = credit_impact
        else:
            impacts["credit"] = 0
        
        # Volatility impact
        if scenario.volatility_shock != 1.0:
            vega = sensitivities.get("vega", 0)
            vol_impact = vega * (scenario.volatility_shock - 1.0) * data.volatility * 100
            impacts["volatility"] = vol_impact
        else:
            impacts["volatility"] = 0
        
        # Total impact and stressed exposure
        total_impact = sum(impacts.values())
        stressed_exposure = base_exposure + total_impact
        stress_pnl = -total_impact  # Loss is positive impact
        
        # Stress multiplier
        stress_multiplier = stressed_exposure / base_exposure if base_exposure > 0 else 1.0
        
        return QLStressedExposureResult(
            stressed_exposure=stressed_exposure,
            stress_multiplier=stress_multiplier,
            base_exposure=base_exposure,
            stress_scenario=scenario.name,
            stress_pnl=stress_pnl,
            components={
                "scenario": {
                    "rate_shock": scenario.rate_shock,
                    "fx_shock": scenario.fx_shock,
                    "credit_shock": scenario.credit_shock,
                    "volatility_shock": scenario.volatility_shock,
                    "correlation_shock": scenario.correlation_shock
                },
                "impacts": impacts,
                "total_impact": total_impact
            },
            sensitivities=sensitivities,
            metadata={
                "quantlib_version": ql.__version__ if hasattr(ql, '__version__') else "unknown",
                "scenario_description": scenario.description
            }
        )
    
    def _calculate_sensitivities(
        self,
        data: QLStressedExposureInput,
        use_exact: bool = False
    ) -> Dict[str, float]:
        """Calculate or use provided sensitivities."""
        sensitivities = {}
        
        if use_exact and self._use_sensitivities:
            # Use provided sensitivities if available
            if data.dv01 is not None:
                sensitivities["dv01"] = data.dv01
            if data.duration is not None:
                sensitivities["duration"] = data.duration
            if data.fx_delta is not None:
                sensitivities["fx_delta"] = data.fx_delta
            if data.vega is not None:
                sensitivities["vega"] = data.vega
        
        # Calculate missing sensitivities based on product type
        if "dv01" not in sensitivities:
            if data.product_type in ["irs", "swaption", "bond", "fra"]:
                # Estimate DV01 based on duration
                duration = data.duration if data.duration else min(data.remaining_maturity, 10) * 0.8
                sensitivities["dv01"] = duration * data.notional / 10000
                sensitivities["duration"] = duration
            else:
                sensitivities["dv01"] = 0
                sensitivities["duration"] = 0
        
        if "fx_delta" not in sensitivities:
            if data.product_type in ["fx_forward", "fx_option", "fx_swap"]:
                sensitivities["fx_delta"] = data.notional
            else:
                sensitivities["fx_delta"] = 0
        
        if "credit_dv01" not in sensitivities:
            if data.product_type in ["cds", "cdo"]:
                sensitivities["credit_dv01"] = data.notional * data.remaining_maturity / 10000
            else:
                sensitivities["credit_dv01"] = 0
        
        if "vega" not in sensitivities:
            if data.product_type in ["option", "swaption", "fx_option", "cap", "floor"]:
                # Estimate vega based on notional and maturity
                sensitivities["vega"] = data.notional * math.sqrt(data.remaining_maturity) / 100
            else:
                sensitivities["vega"] = data.notional * 0.001  # Small vega for non-options
        
        return sensitivities
    
    def calculate_portfolio_stress(
        self,
        positions: List[QLStressedExposureInput],
        scenario_name: str = "2008_crisis"
    ) -> Dict[str, Any]:
        """
        Calculate stressed exposure for a portfolio.
        
        Args:
            positions: List of position inputs
            scenario_name: Stress scenario to apply
            
        Returns:
            Portfolio stress results with aggregations
        """
        results = []
        for position in positions:
            position.stress_scenario = scenario_name
            result = self._calculate_impl(position)
            results.append(result)
        
        # Aggregate results
        total_base = sum(r.base_exposure for r in results)
        total_stressed = sum(r.stressed_exposure for r in results)
        total_pnl = sum(r.stress_pnl for r in results)
        
        # Impact breakdown
        impact_breakdown = {
            "rate": sum(r.components.get("impacts", {}).get("rate", 0) for r in results),
            "fx": sum(r.components.get("impacts", {}).get("fx", 0) for r in results),
            "credit": sum(r.components.get("impacts", {}).get("credit", 0) for r in results),
            "volatility": sum(r.components.get("impacts", {}).get("volatility", 0) for r in results)
        }
        
        return {
            "portfolio_base_exposure": total_base,
            "portfolio_stressed_exposure": total_stressed,
            "portfolio_stress_multiplier": total_stressed / total_base if total_base > 0 else 1.0,
            "portfolio_stress_pnl": total_pnl,
            "impact_breakdown": impact_breakdown,
            "scenario": scenario_name,
            "position_count": len(positions),
            "position_results": results
        }
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "stress_type": self._stress_type,
            "default_scenario": self._default_scenario,
            "use_sensitivities": self._use_sensitivities,
            "available_historical_scenarios": list(self.HISTORICAL_SCENARIOS.keys()),
            "available_regulatory_scenarios": list(self.REGULATORY_SCENARIOS.keys()),
            "quantlib_available": QUANTLIB_AVAILABLE
        })
        return base_details


class QLPeakExposureCalculator(ExposureCalculator):
    """
    QuantLib-enhanced Peak Exposure Calculator.
    
    Peak Exposure is the maximum exposure over the life of a transaction:
    
    Peak Exposure = max(Exposure(t)) for t ∈ [0, T]
    
    Methods:
    - EE-based: Peak of Expected Exposure profile
    - PFE-based: Peak of PFE profile at confidence level
    - Monte Carlo: Full simulation-based peak
    - Parametric: Analytical approximation
    
    Uses QuantLib for:
    - High-quality random number generation
    - Statistical distributions
    - Efficient simulation
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize QuantLib Peak Exposure calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - method: 'ee_based', 'pfe_based', 'monte_carlo', 'parametric'
                - num_simulations: For Monte Carlo
                - confidence_level: For PFE-based peak
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.QUANTLIB
        self._method = config.get("method", "pfe_based")
        self._num_simulations = config.get("num_simulations", 10000)
        self._confidence_level = config.get("confidence_level", 0.95)
        
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibPeakExposureCalculator. "
                "Install with: pip install QuantLib"
            )
        
        # Initialize QuantLib RNG
        self._rng = ql.MersenneTwisterUniformRng(42)
        self._gaussian_rng = None
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.PEAK_EXPOSURE
    
    def _calculate_impl(self, data: Any) -> QLPeakExposureResult:
        """
        Calculate peak exposure using QuantLib.
        
        Args:
            data: QLPeakExposureInput or dictionary
            
        Returns:
            QLPeakExposureResult with peak exposure
        """
        if isinstance(data, dict):
            data = QLPeakExposureInput(**data)
        
        # Generate time grid if not provided
        if data.time_grid is None:
            data.time_grid = self._generate_time_grid(
                data.remaining_maturity,
                data.num_time_steps
            )
        
        # Calculate based on method
        if self._method == "ee_based":
            return self._calculate_ee_based_peak(data)
        elif self._method == "pfe_based":
            return self._calculate_pfe_based_peak(data)
        elif self._method == "monte_carlo":
            return self._calculate_monte_carlo_peak(data)
        elif self._method == "parametric":
            return self._calculate_parametric_peak(data)
        else:
            raise ValueError(f"Unknown method: {self._method}")
    
    def _generate_time_grid(
        self,
        maturity: float,
        num_points: int = 20
    ) -> List[float]:
        """Generate time grid for exposure profile."""
        if maturity <= 0:
            return [0.0]
        step = maturity / num_points
        return [i * step for i in range(num_points + 1)]
    
    def _calculate_ee_based_peak(
        self,
        data: QLPeakExposureInput
    ) -> QLPeakExposureResult:
        """Calculate peak based on EE profile."""
        # Use provided profile or simulate
        if data.ee_profile is not None:
            ee_profile = data.ee_profile
        else:
            ee_profile = self._simulate_ee_profile(data)
        
        return self._find_peak_from_profile(data, ee_profile, "ee_based")
    
    def _calculate_pfe_based_peak(
        self,
        data: QLPeakExposureInput
    ) -> QLPeakExposureResult:
        """Calculate peak based on PFE profile."""
        # Use provided profile or simulate
        if data.pfe_profile is not None:
            pfe_profile = data.pfe_profile
        else:
            pfe_profile = self._simulate_pfe_profile(data)
        
        return self._find_peak_from_profile(data, pfe_profile, "pfe_based")
    
    def _calculate_monte_carlo_peak(
        self,
        data: QLPeakExposureInput
    ) -> QLPeakExposureResult:
        """Calculate peak using full Monte Carlo simulation."""
        # Initialize Gaussian RNG
        self._gaussian_rng = ql.MersenneTwisterGaussianRng(self._rng)
        
        num_sims = data.num_simulations
        time_grid = data.time_grid
        
        # Track peak for each path
        path_peaks = []
        path_peak_times = []
        
        # Parameters
        S0 = data.current_mtm if data.current_mtm != 0 else data.notional * 0.05
        sigma = data.volatility
        mu = data.drift
        
        for _ in range(num_sims):
            # Simulate full path
            path = [S0]
            max_exposure = max(0.0, S0)
            max_time = 0.0
            
            for i in range(1, len(time_grid)):
                dt = time_grid[i] - time_grid[i-1]
                z = self._gaussian_rng.next().value()
                
                # GBM evolution
                drift_term = (mu - 0.5 * sigma**2) * dt
                diffusion_term = sigma * math.sqrt(dt) * z
                new_value = path[-1] * math.exp(drift_term + diffusion_term)
                
                path.append(new_value)
                exposure = max(0.0, new_value - data.collateral_held)
                
                if exposure > max_exposure:
                    max_exposure = exposure
                    max_time = time_grid[i]
            
            path_peaks.append(max_exposure)
            path_peak_times.append(max_time)
        
        # Statistics
        path_peaks.sort()
        
        # Peak at confidence level
        pfe_idx = int(data.confidence_level * num_sims)
        peak_exposure = path_peaks[min(pfe_idx, num_sims - 1)]
        
        # Average peak time
        avg_peak_time = sum(path_peak_times) / num_sims
        
        # Calculate EE profile for reporting
        ee_profile = self._simulate_ee_profile(data)
        
        return QLPeakExposureResult(
            peak_exposure=peak_exposure,
            peak_time=avg_peak_time,
            average_exposure=sum(path_peaks) / num_sims,
            effective_epe=self._calculate_effective_epe(ee_profile, time_grid),
            exposure_profile=ee_profile,
            time_grid=time_grid,
            components={
                "method": "monte_carlo",
                "num_simulations": num_sims,
                "confidence_level": data.confidence_level,
                "mean_peak": sum(path_peaks) / num_sims,
                "median_peak": path_peaks[num_sims // 2],
                "max_peak": path_peaks[-1],
                "min_peak": path_peaks[0]
            },
            metadata={
                "quantlib_version": ql.__version__ if hasattr(ql, '__version__') else "unknown"
            }
        )
    
    def _calculate_parametric_peak(
        self,
        data: QLPeakExposureInput
    ) -> QLPeakExposureResult:
        """
        Calculate peak using parametric approximation.
        
        For GBM process, the peak occurs approximately at:
        t* = T / (1 + σ√T)
        
        Peak PFE ≈ S0 × exp(μT + σ√T × Φ^(-1)(α))
        """
        S0 = data.current_mtm if data.current_mtm != 0 else data.notional * 0.05
        sigma = data.volatility
        T = data.remaining_maturity
        mu = data.drift
        alpha = data.confidence_level
        
        # Approximate peak time
        if T > 0 and sigma > 0:
            t_star = T / (1 + sigma * math.sqrt(T))
        else:
            t_star = T / 2
        
        # Use QuantLib for inverse normal
        inv_normal = ql.InverseCumulativeNormal()
        z_alpha = inv_normal(alpha)
        
        # Peak PFE approximation
        peak_pfe = abs(S0) * math.exp(mu * t_star + sigma * math.sqrt(t_star) * z_alpha)
        peak_pfe = max(0.0, peak_pfe - data.collateral_held)
        
        # Generate profiles for reporting
        ee_profile = self._simulate_ee_profile(data)
        time_grid = data.time_grid
        
        # Average exposure
        average_exposure = sum(ee_profile) / len(ee_profile)
        
        return QLPeakExposureResult(
            peak_exposure=peak_pfe,
            peak_time=t_star,
            average_exposure=average_exposure,
            effective_epe=self._calculate_effective_epe(ee_profile, time_grid),
            exposure_profile=ee_profile,
            time_grid=time_grid,
            components={
                "method": "parametric",
                "z_alpha": z_alpha,
                "approximate_peak_time": t_star,
                "confidence_level": alpha
            },
            metadata={
                "quantlib_version": ql.__version__ if hasattr(ql, '__version__') else "unknown"
            }
        )
    
    def _simulate_ee_profile(
        self,
        data: QLPeakExposureInput
    ) -> List[float]:
        """Simulate Expected Exposure profile using QuantLib."""
        # Initialize Gaussian RNG
        self._gaussian_rng = ql.MersenneTwisterGaussianRng(self._rng)
        
        ee_profile = []
        time_grid = data.time_grid
        num_sims = min(data.num_simulations, 5000)  # Limit for EE
        
        S0 = data.current_mtm if data.current_mtm != 0 else data.notional * 0.05
        sigma = data.volatility
        mu = data.drift
        
        for t in time_grid:
            if t == 0:
                ee = max(0.0, S0 - data.collateral_held)
            else:
                exposures = []
                for _ in range(num_sims):
                    z = self._gaussian_rng.next().value()
                    
                    # GBM at time t
                    drift_term = (mu - 0.5 * sigma**2) * t
                    diffusion_term = sigma * math.sqrt(t) * z
                    future_value = S0 * math.exp(drift_term + diffusion_term)
                    
                    exposure = max(0.0, future_value - data.collateral_held)
                    exposures.append(exposure)
                
                ee = sum(exposures) / num_sims
            
            ee_profile.append(ee)
        
        return ee_profile
    
    def _simulate_pfe_profile(
        self,
        data: QLPeakExposureInput
    ) -> List[float]:
        """Simulate PFE profile using QuantLib."""
        # Initialize Gaussian RNG
        self._gaussian_rng = ql.MersenneTwisterGaussianRng(self._rng)
        
        pfe_profile = []
        time_grid = data.time_grid
        num_sims = data.num_simulations
        alpha = data.confidence_level
        
        S0 = data.current_mtm if data.current_mtm != 0 else data.notional * 0.05
        sigma = data.volatility
        mu = data.drift
        
        for t in time_grid:
            if t == 0:
                pfe = max(0.0, S0 - data.collateral_held)
            else:
                exposures = []
                for _ in range(num_sims):
                    z = self._gaussian_rng.next().value()
                    
                    # GBM at time t
                    drift_term = (mu - 0.5 * sigma**2) * t
                    diffusion_term = sigma * math.sqrt(t) * z
                    future_value = S0 * math.exp(drift_term + diffusion_term)
                    
                    exposure = max(0.0, future_value - data.collateral_held)
                    exposures.append(exposure)
                
                exposures.sort()
                pfe_idx = int(alpha * num_sims)
                pfe = exposures[min(pfe_idx, num_sims - 1)]
            
            pfe_profile.append(pfe)
        
        return pfe_profile
    
    def _find_peak_from_profile(
        self,
        data: QLPeakExposureInput,
        profile: List[float],
        method: str
    ) -> QLPeakExposureResult:
        """Find peak from exposure profile."""
        time_grid = data.time_grid
        
        # Find peak
        peak_exposure = max(profile)
        peak_idx = profile.index(peak_exposure)
        peak_time = time_grid[peak_idx]
        
        # Average exposure
        average_exposure = sum(profile) / len(profile)
        
        # Effective EPE
        effective_epe = self._calculate_effective_epe(profile, time_grid)
        
        return QLPeakExposureResult(
            peak_exposure=peak_exposure,
            peak_time=peak_time,
            average_exposure=average_exposure,
            effective_epe=effective_epe,
            exposure_profile=profile,
            time_grid=time_grid,
            components={
                "method": method,
                "peak_index": peak_idx,
                "profile_length": len(profile),
                "collateral_held": data.collateral_held
            },
            metadata={
                "quantlib_version": ql.__version__ if hasattr(ql, '__version__') else "unknown"
            }
        )
    
    def _calculate_effective_epe(
        self,
        ee_profile: List[float],
        time_grid: List[float]
    ) -> float:
        """
        Calculate Effective EPE.
        
        Effective EE is non-decreasing:
        EEE(t) = max(EEE(t-1), EE(t))
        
        Effective EPE = time-weighted average of EEE
        """
        if len(ee_profile) < 2:
            return ee_profile[0] if ee_profile else 0.0
        
        # Calculate EEE (non-decreasing)
        eee = [ee_profile[0]]
        for i in range(1, len(ee_profile)):
            eee.append(max(eee[-1], ee_profile[i]))
        
        # Time-weighted average (trapezoidal integration)
        total = 0.0
        for i in range(1, len(time_grid)):
            dt = time_grid[i] - time_grid[i-1]
            total += 0.5 * (eee[i] + eee[i-1]) * dt
        
        T = time_grid[-1] if time_grid[-1] > 0 else 1.0
        return total / T
    
    def calculate_portfolio_peak(
        self,
        positions: List[QLPeakExposureInput]
    ) -> Dict[str, Any]:
        """
        Calculate peak exposure for a portfolio.
        
        Args:
            positions: List of position inputs
            
        Returns:
            Portfolio peak exposure results
        """
        results = []
        for position in positions:
            result = self._calculate_impl(position)
            results.append(result)
        
        # Aggregate (conservative: sum of peaks)
        total_peak = sum(r.peak_exposure for r in results)
        total_average = sum(r.average_exposure for r in results)
        total_effective_epe = sum(r.effective_epe for r in results)
        
        # Weighted average peak time
        weights = [r.peak_exposure for r in results]
        total_weight = sum(weights)
        if total_weight > 0:
            weighted_peak_time = sum(
                r.peak_time * w for r, w in zip(results, weights)
            ) / total_weight
        else:
            weighted_peak_time = 0.0
        
        return {
            "portfolio_peak_exposure": total_peak,
            "portfolio_average_exposure": total_average,
            "portfolio_effective_epe": total_effective_epe,
            "weighted_peak_time": weighted_peak_time,
            "position_count": len(positions),
            "position_results": results
        }
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "method": self._method,
            "num_simulations": self._num_simulations,
            "confidence_level": self._confidence_level,
            "available_methods": ["ee_based", "pfe_based", "monte_carlo", "parametric"],
            "quantlib_available": QUANTLIB_AVAILABLE
        })
        return base_details
