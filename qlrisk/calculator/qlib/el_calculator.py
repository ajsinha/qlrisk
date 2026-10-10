# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Expected Loss (EL) Calculator.

Computes Expected Loss using QuantLib's credit modeling capabilities.

EL = PD × LGD × EAD
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import math

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import BaseCalculator, CalculationResult, CalculatorType


@dataclass
class QLELInput:
    """Input parameters for QuantLib Expected Loss calculation."""
    pd: float  # Probability of default (annualized)
    lgd: float  # Loss given default (0-1)
    ead: float  # Exposure at default
    time_horizon: float = 1.0  # Years
    pd_term_structure: Optional[List[Tuple[float, float]]] = None  # [(time, pd)]
    lgd_term_structure: Optional[List[Tuple[float, float]]] = None  # [(time, lgd)]
    ead_profile: Optional[List[Tuple[float, float]]] = None  # [(time, ead)]
    recovery_rate: Optional[float] = None  # Alternative to LGD
    discount_rate: float = 0.05


@dataclass
class QLELResult:
    """Result of QuantLib Expected Loss calculation."""
    expected_loss: float
    el_rate: float  # EL as percentage of EAD
    annualized_el: float
    cumulative_el: float
    term_structure: List[Tuple[float, float]] = field(default_factory=list)
    marginal_el: List[Tuple[float, float]] = field(default_factory=list)
    discounted_el: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibELCalculator(BaseCalculator):
    """
    QuantLib-based Expected Loss Calculator.
    
    Uses QuantLib for:
    - Credit default probability modeling
    - Term structure interpolation
    - Discount factor calculations
    """
    
    def __init__(self, name: str = "QuantLibELCalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.EXPECTED_LOSS
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibELCalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLELInput) -> CalculationResult:
        """
        Calculate Expected Loss using QuantLib.
        
        Args:
            data: QLELInput containing PD, LGD, EAD parameters
            
        Returns:
            CalculationResult containing QLELResult
        """
        self._validate_input(data)
        
        # Set up QuantLib environment
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today
        
        # Handle LGD vs recovery rate
        lgd = data.lgd if data.recovery_rate is None else (1 - data.recovery_rate)
        
        if data.pd_term_structure or data.ead_profile:
            result = self._calculate_term_structure_el(data, lgd)
        else:
            result = self._calculate_simple_el(data, lgd)
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "time_horizon": data.time_horizon,
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A"
            }
        )
    
    def _validate_input(self, data: QLELInput) -> None:
        """Validate input parameters."""
        if not 0 <= data.pd <= 1:
            raise ValueError("PD must be between 0 and 1")
        if not 0 <= data.lgd <= 1:
            raise ValueError("LGD must be between 0 and 1")
        if data.ead < 0:
            raise ValueError("EAD must be non-negative")
        if data.time_horizon <= 0:
            raise ValueError("Time horizon must be positive")
    
    def _calculate_simple_el(self, data: QLELInput, lgd: float) -> QLELResult:
        """
        Calculate simple Expected Loss.
        
        EL = PD × LGD × EAD
        """
        # Convert annual PD to horizon PD
        horizon_pd = 1 - (1 - data.pd) ** data.time_horizon
        
        # Expected Loss
        expected_loss = horizon_pd * lgd * data.ead
        
        # EL rate
        el_rate = expected_loss / data.ead if data.ead > 0 else 0
        
        # Annualized EL
        annualized_el = expected_loss / data.time_horizon if data.time_horizon > 0 else expected_loss
        
        # Discounted EL using QuantLib
        discounted_el = self._calculate_discounted_el(
            expected_loss, data.time_horizon / 2, data.discount_rate
        )
        
        return QLELResult(
            expected_loss=expected_loss,
            el_rate=el_rate,
            annualized_el=annualized_el,
            cumulative_el=expected_loss,
            discounted_el=discounted_el,
            term_structure=[(data.time_horizon, expected_loss)],
            marginal_el=[(data.time_horizon, expected_loss)],
            components={
                "pd": data.pd,
                "horizon_pd": horizon_pd,
                "lgd": lgd,
                "ead": data.ead,
            }
        )
    
    def _calculate_term_structure_el(self, data: QLELInput, lgd: float) -> QLELResult:
        """
        Calculate Expected Loss with term structures.
        
        Integrates PD term structure with EAD profile.
        """
        # Build default probability curve using QuantLib
        pd_curve = self._build_pd_curve(data)
        
        # Get EAD profile or use constant
        ead_profile = data.ead_profile or [(data.time_horizon, data.ead)]
        
        # Get LGD term structure or use constant
        lgd_ts = data.lgd_term_structure or [(data.time_horizon, lgd)]
        
        # Calculate term structure of EL
        term_structure = []
        marginal_el = []
        cumulative_el = 0.0
        discounted_el = 0.0
        
        prev_time = 0.0
        prev_survival = 1.0
        
        # Create time grid
        times = sorted(set([t for t, _ in ead_profile] + [t for t, _ in lgd_ts]))
        if data.pd_term_structure:
            times = sorted(set(times + [t for t, _ in data.pd_term_structure]))
        
        for t in times:
            if t > data.time_horizon:
                break
            
            # Interpolate EAD
            ead_t = self._interpolate_value(t, ead_profile, data.ead)
            
            # Interpolate LGD
            lgd_t = self._interpolate_value(t, lgd_ts, lgd)
            
            # Get survival probability from QuantLib curve
            survival_t = pd_curve.survivalProbability(t)
            
            # Marginal PD for period
            marginal_pd = prev_survival - survival_t
            
            # Marginal EL for period
            period_el = marginal_pd * lgd_t * ead_t
            
            marginal_el.append((t, period_el))
            cumulative_el += period_el
            term_structure.append((t, cumulative_el))
            
            # Discounted EL
            df = math.exp(-data.discount_rate * (t + prev_time) / 2)
            discounted_el += period_el * df
            
            prev_time = t
            prev_survival = survival_t
        
        # Final EL
        final_el = cumulative_el
        el_rate = final_el / data.ead if data.ead > 0 else 0
        annualized_el = final_el / data.time_horizon if data.time_horizon > 0 else final_el
        
        return QLELResult(
            expected_loss=final_el,
            el_rate=el_rate,
            annualized_el=annualized_el,
            cumulative_el=cumulative_el,
            discounted_el=discounted_el,
            term_structure=term_structure,
            marginal_el=marginal_el,
            components={
                "pd": data.pd,
                "lgd": lgd,
                "ead": data.ead,
                "num_periods": len(term_structure),
            }
        )
    
    def _build_pd_curve(self, data: QLELInput) -> ql.DefaultProbabilityTermStructure:
        """
        Build QuantLib default probability term structure.
        """
        today = ql.Date.todaysDate()
        calendar = ql.TARGET()
        
        if data.pd_term_structure:
            # Build from term structure
            dates = [today]
            hazard_rates = [0.0]  # Placeholder for today
            
            for t, pd in data.pd_term_structure:
                date = calendar.advance(today, ql.Period(int(t * 365), ql.Days))
                # Convert cumulative PD to hazard rate
                # Cumulative PD = 1 - exp(-λt) => λ = -ln(1-PD)/t
                if pd < 1:
                    hazard_rate = -math.log(1 - pd) / t if t > 0 else 0
                else:
                    hazard_rate = 10.0  # Very high hazard for PD = 1
                dates.append(date)
                hazard_rates.append(hazard_rate)
            
            # Create piecewise flat hazard rate curve
            day_counter = ql.Actual365Fixed()
            
            # Use FlatHazardRate for simplicity with average hazard
            avg_hazard = sum(hazard_rates[1:]) / len(hazard_rates[1:]) if len(hazard_rates) > 1 else 0
            curve = ql.FlatHazardRate(today, avg_hazard, day_counter)
        else:
            # Build from single PD
            # λ = -ln(1-PD) for annual PD
            hazard_rate = -math.log(1 - data.pd) if data.pd < 1 else 10.0
            day_counter = ql.Actual365Fixed()
            curve = ql.FlatHazardRate(today, hazard_rate, day_counter)
        
        return curve
    
    def _interpolate_value(self, t: float, 
                           term_structure: List[Tuple[float, float]], 
                           default: float) -> float:
        """Linear interpolation of term structure value."""
        if not term_structure:
            return default
        
        # Find bracketing points
        below = None
        above = None
        
        for time, value in sorted(term_structure):
            if time <= t:
                below = (time, value)
            if time >= t and above is None:
                above = (time, value)
        
        if below is None:
            return term_structure[0][1] if term_structure else default
        if above is None:
            return below[1]
        if below[0] == above[0]:
            return below[1]
        
        # Linear interpolation
        weight = (t - below[0]) / (above[0] - below[0])
        return below[1] + weight * (above[1] - below[1])
    
    def _calculate_discounted_el(self, el: float, avg_time: float, 
                                  discount_rate: float) -> float:
        """Calculate present value of expected loss."""
        # Use QuantLib for discounting
        today = ql.Date.todaysDate()
        day_counter = ql.Actual365Fixed()
        
        # Create flat yield curve
        rate = ql.QuoteHandle(ql.SimpleQuote(discount_rate))
        curve = ql.FlatForward(today, rate, day_counter)
        
        # Get discount factor
        target_date = ql.Date(
            today.serialNumber() + int(avg_time * 365)
        )
        df = curve.discount(target_date)
        
        return el * df
    
    def calculate_portfolio_el(self, exposures: List[QLELInput]) -> Dict[str, Any]:
        """
        Calculate portfolio-level Expected Loss.
        
        Args:
            exposures: List of exposure inputs
            
        Returns:
            Portfolio EL with concentration metrics
        """
        if not exposures:
            return {"portfolio_el": 0.0, "exposures": []}
        
        results = []
        total_el = 0.0
        total_ead = 0.0
        
        for exp in exposures:
            result = self.calculate(exp)
            results.append(result.result)
            total_el += result.result.expected_loss
            total_ead += exp.ead
        
        # Concentration metrics
        el_contributions = [r.expected_loss for r in results]
        hhi = sum((el / total_el) ** 2 for el in el_contributions) if total_el > 0 else 0
        
        portfolio_el_rate = total_el / total_ead if total_ead > 0 else 0
        
        return {
            "portfolio_el": total_el,
            "portfolio_ead": total_ead,
            "portfolio_el_rate": portfolio_el_rate,
            "hhi": hhi,
            "effective_n": 1 / hhi if hhi > 0 else len(exposures),
            "exposures": results,
        }
    
    def calculate_marginal_el(self, portfolio: List[QLELInput], 
                               new_exposure: QLELInput) -> Dict[str, Any]:
        """
        Calculate marginal EL contribution of new exposure.
        
        Args:
            portfolio: Existing portfolio
            new_exposure: New exposure to add
            
        Returns:
            Marginal EL analysis
        """
        # Calculate existing portfolio EL
        existing = self.calculate_portfolio_el(portfolio)
        
        # Calculate with new exposure
        new_portfolio = portfolio + [new_exposure]
        with_new = self.calculate_portfolio_el(new_portfolio)
        
        marginal_el = with_new["portfolio_el"] - existing["portfolio_el"]
        
        # Standalone EL
        standalone = self.calculate(new_exposure)
        
        return {
            "marginal_el": marginal_el,
            "standalone_el": standalone.result.expected_loss,
            "diversification_benefit": standalone.result.expected_loss - marginal_el,
            "existing_portfolio_el": existing["portfolio_el"],
            "new_portfolio_el": with_new["portfolio_el"],
        }
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "formula": "EL = PD × LGD × EAD",
            "supports_term_structure": True,
            "quantlib_available": QUANTLIB_AVAILABLE,
        }
