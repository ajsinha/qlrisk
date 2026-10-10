# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Loss Given Default Calculator.

Uses QuantLib's statistical distributions and numerical methods for
LGD calculation with enhanced precision.
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


class QLLGDMethod(Enum):
    """LGD calculation methods using QuantLib."""
    MARKET_APPROACH = "market_approach"
    WORKOUT_APPROACH = "workout_approach"
    COLLATERAL_BASED = "collateral_based"
    STOCHASTIC = "stochastic"


@dataclass
class QLLGDInput:
    """Input parameters for QuantLib LGD calculation."""
    # Market approach
    recovery_rate: float = 0.0
    
    # Workout approach
    recovery_amount: float = 0.0
    exposure_at_default: float = 0.0
    workout_costs: float = 0.0
    discount_rate: float = 0.05
    workout_period: float = 1.0
    
    # Collateral based
    collateral_value: float = 0.0
    collateral_volatility: float = 0.0
    haircut: float = 0.0
    liquidation_period: float = 0.0
    
    # Stochastic model
    lgd_mean: float = 0.45
    lgd_std: float = 0.25
    correlation_with_pd: float = 0.0
    
    # Seniority
    seniority: str = "senior_secured"
    
    method: QLLGDMethod = QLLGDMethod.MARKET_APPROACH


@dataclass
class QLLGDResult:
    """Result of QuantLib LGD calculation."""
    lgd: float
    recovery_rate: float
    lgd_downturn: float = 0.0
    lgd_stress: float = 0.0
    method: str = ""
    components: Dict[str, Any] = field(default_factory=dict)


class QLLGDCalculator(BaseCalculator):
    """
    QuantLib-based Loss Given Default Calculator.
    
    Implements LGD calculation using QuantLib's numerical methods:
    - Market-implied LGD from recovery rates
    - Workout approach with present value calculations
    - Collateral-based with stochastic collateral valuation
    - Stochastic LGD using beta distribution
    """
    
    # Regulatory LGD floors by seniority
    LGD_FLOORS = {
        "senior_secured": 0.25,
        "senior_unsecured": 0.40,
        "subordinated": 0.75,
        "junior_subordinated": 0.90
    }
    
    def __init__(self, name: str = "QLLGDCalculator", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.LOSS_GIVEN_DEFAULT
        
        if not QUANTLIB_AVAILABLE:
            raise ImportError("QuantLib is required for QLLGDCalculator")
    
    def calculate(self, data: QLLGDInput) -> CalculationResult:
        """Calculate LGD using QuantLib methods."""
        self._validate_input(data)
        
        if data.method == QLLGDMethod.MARKET_APPROACH:
            result = self._calculate_market_lgd(data)
        elif data.method == QLLGDMethod.WORKOUT_APPROACH:
            result = self._calculate_workout_lgd(data)
        elif data.method == QLLGDMethod.COLLATERAL_BASED:
            result = self._calculate_collateral_lgd(data)
        elif data.method == QLLGDMethod.STOCHASTIC:
            result = self._calculate_stochastic_lgd(data)
        else:
            raise ValueError(f"Unknown LGD method: {data.method}")
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={"method": data.method.value, "quantlib_version": ql.version()}
        )
    
    def _calculate_market_lgd(self, data: QLLGDInput) -> QLLGDResult:
        """Calculate LGD from market-implied recovery rate."""
        lgd = 1.0 - data.recovery_rate
        
        # Apply regulatory floor
        floor = self.LGD_FLOORS.get(data.seniority, 0.45)
        lgd = max(lgd, floor)
        
        # Downturn LGD (add 20% stress)
        lgd_downturn = min(lgd * 1.2, 1.0)
        
        return QLLGDResult(
            lgd=lgd,
            recovery_rate=data.recovery_rate,
            lgd_downturn=lgd_downturn,
            lgd_stress=lgd_downturn,
            method="market_approach",
            components={
                "seniority": data.seniority,
                "floor": floor,
                "input_recovery": data.recovery_rate
            }
        )
    
    def _calculate_workout_lgd(self, data: QLLGDInput) -> QLLGDResult:
        """Calculate LGD using workout approach with QuantLib discounting."""
        import math
        
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today
        
        # Create discount curve
        rate_quote = ql.QuoteHandle(ql.SimpleQuote(data.discount_rate))
        day_count = ql.Actual365Fixed()
        calendar = ql.TARGET()
        
        flat_curve = ql.FlatForward(today, rate_quote, day_count)
        curve_handle = ql.YieldTermStructureHandle(flat_curve)
        
        # Discount recovered amount
        workout_date = calendar.advance(today, ql.Period(int(data.workout_period * 12), ql.Months))
        discount_factor = flat_curve.discount(workout_date)
        
        pv_recovery = (data.recovery_amount - data.workout_costs) * discount_factor
        pv_recovery = max(pv_recovery, 0.0)
        
        # Calculate LGD
        if data.exposure_at_default > 0:
            recovery_rate = pv_recovery / data.exposure_at_default
            lgd = 1.0 - recovery_rate
        else:
            lgd = 1.0
            recovery_rate = 0.0
        
        lgd = max(min(lgd, 1.0), 0.0)
        
        # Apply floor
        floor = self.LGD_FLOORS.get(data.seniority, 0.45)
        lgd = max(lgd, floor)
        
        return QLLGDResult(
            lgd=lgd,
            recovery_rate=recovery_rate,
            lgd_downturn=min(lgd * 1.15, 1.0),
            lgd_stress=min(lgd * 1.25, 1.0),
            method="workout_approach",
            components={
                "discount_factor": discount_factor,
                "pv_recovery": pv_recovery,
                "gross_recovery": data.recovery_amount,
                "workout_costs": data.workout_costs,
                "ead": data.exposure_at_default
            }
        )
    
    def _calculate_collateral_lgd(self, data: QLLGDInput) -> QLLGDResult:
        """Calculate LGD with collateral using stochastic valuation."""
        import math
        
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today
        
        # Model collateral value as GBM at liquidation
        # V(T) = V(0) * exp((μ - σ²/2)T + σ√T*Z)
        
        V0 = data.collateral_value * (1.0 - data.haircut)
        sigma = data.collateral_volatility
        T = data.liquidation_period
        
        # Expected value under risk-neutral measure (μ = 0 for simplicity)
        drift = -0.5 * sigma**2 * T
        vol_term = sigma * math.sqrt(T)
        
        # Expected collateral value
        expected_V = V0 * math.exp(drift + 0.5 * vol_term**2)
        
        # Use QuantLib normal for quantile calculation
        cumulative_normal = ql.CumulativeNormalDistribution()
        inverse_normal = ql.InverseCumulativeNormal()
        
        # 95% worst-case collateral value
        z_95 = inverse_normal(0.05)
        stressed_V = V0 * math.exp(drift + vol_term * z_95)
        
        # Calculate LGD
        ead = data.exposure_at_default
        if ead > 0:
            expected_recovery = min(expected_V / ead, 1.0)
            stressed_recovery = min(stressed_V / ead, 1.0)
            
            lgd = 1.0 - expected_recovery
            lgd_stress = 1.0 - stressed_recovery
        else:
            lgd = 1.0
            lgd_stress = 1.0
        
        # Apply floor
        floor = self.LGD_FLOORS.get(data.seniority, 0.25)
        lgd = max(lgd, floor)
        lgd_stress = max(lgd_stress, floor)
        
        return QLLGDResult(
            lgd=lgd,
            recovery_rate=1.0 - lgd,
            lgd_downturn=lgd_stress,
            lgd_stress=lgd_stress,
            method="collateral_based",
            components={
                "collateral_value": data.collateral_value,
                "haircut": data.haircut,
                "effective_collateral": V0,
                "expected_collateral": expected_V,
                "stressed_collateral": stressed_V,
                "volatility": sigma,
                "liquidation_period": T
            }
        )
    
    def _calculate_stochastic_lgd(self, data: QLLGDInput) -> QLLGDResult:
        """Calculate LGD using stochastic model with QuantLib."""
        import math
        
        # Use beta distribution for LGD bounded in [0,1]
        # Parameterize by mean and std
        mu = data.lgd_mean
        sigma = data.lgd_std
        
        # Beta distribution parameters
        # E[X] = α/(α+β), Var[X] = αβ/((α+β)²(α+β+1))
        variance = sigma**2
        
        # Ensure variance is feasible
        max_var = mu * (1 - mu)
        if variance >= max_var:
            variance = 0.99 * max_var
        
        alpha = mu * (mu * (1 - mu) / variance - 1)
        beta_param = (1 - mu) * (mu * (1 - mu) / variance - 1)
        
        # Expected LGD
        lgd = mu
        
        # Use QuantLib for normal approximation to beta
        cumulative_normal = ql.CumulativeNormalDistribution()
        inverse_normal = ql.InverseCumulativeNormal()
        
        # 99th percentile LGD (stress)
        z_99 = inverse_normal(0.99)
        lgd_stress = min(mu + z_99 * sigma, 1.0)
        
        # Apply floor
        floor = self.LGD_FLOORS.get(data.seniority, 0.45)
        lgd = max(lgd, floor)
        lgd_stress = max(lgd_stress, floor)
        
        return QLLGDResult(
            lgd=lgd,
            recovery_rate=1.0 - lgd,
            lgd_downturn=min(lgd * 1.15, 1.0),
            lgd_stress=lgd_stress,
            method="stochastic",
            components={
                "mean": mu,
                "std": sigma,
                "alpha": alpha,
                "beta": beta_param,
                "pd_correlation": data.correlation_with_pd
            }
        )
    
    def _validate_input(self, data: QLLGDInput) -> None:
        """Validate input parameters."""
        if data.method == QLLGDMethod.MARKET_APPROACH:
            if not 0.0 <= data.recovery_rate <= 1.0:
                raise ValueError("Recovery rate must be between 0 and 1")
        
        elif data.method == QLLGDMethod.WORKOUT_APPROACH:
            if data.exposure_at_default < 0:
                raise ValueError("EAD cannot be negative")
            if data.workout_period <= 0:
                raise ValueError("Workout period must be positive")
        
        elif data.method == QLLGDMethod.COLLATERAL_BASED:
            if data.collateral_value < 0:
                raise ValueError("Collateral value cannot be negative")
            if not 0.0 <= data.haircut <= 1.0:
                raise ValueError("Haircut must be between 0 and 1")
        
        elif data.method == QLLGDMethod.STOCHASTIC:
            if not 0.0 <= data.lgd_mean <= 1.0:
                raise ValueError("LGD mean must be between 0 and 1")
            if data.lgd_std <= 0:
                raise ValueError("LGD std must be positive")
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "quantlib_version": ql.version() if QUANTLIB_AVAILABLE else "N/A",
            "methods": [m.value for m in QLLGDMethod],
            "lgd_floors": self.LGD_FLOORS,
            "description": "Loss Given Default calculator using QuantLib"
        }
