# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Credit Valuation Adjustment (CVA) Calculator.

Calculates CVA using QuantLib's credit modeling and Monte Carlo capabilities.

CVA = LGD × ∫₀ᵀ EE(t) × dPD(t) × DF(t)

Bilateral CVA:
BCVA = CVA - DVA
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


class CVAMethod(Enum):
    """CVA calculation methodology."""
    ANALYTICAL = "analytical"
    MONTE_CARLO = "monte_carlo"
    SA_CVA = "standardized_approach"


@dataclass
class QLCVAInput:
    """Input parameters for QuantLib CVA calculation."""
    ee_profile: List[Tuple[float, float]]  # [(time, expected_exposure)]
    credit_spread: float  # Counterparty credit spread (bps)
    recovery_rate: float = 0.4
    discount_curve: Optional[List[Tuple[float, float]]] = None  # [(time, rate)]
    own_credit_spread: Optional[float] = None  # For DVA calculation
    own_recovery_rate: float = 0.4
    wrong_way_risk_factor: float = 0.0  # WWR adjustment
    maturity: Optional[float] = None
    notional: float = 1.0
    method: CVAMethod = CVAMethod.ANALYTICAL


@dataclass
class QLCVAResult:
    """Result of QuantLib CVA calculation."""
    cva: float
    cva_pct: float  # CVA as percentage of notional
    dva: float = 0.0  # Debit Valuation Adjustment
    bcva: float = 0.0  # Bilateral CVA
    marginal_cva: List[Tuple[float, float]] = field(default_factory=list)
    survival_probabilities: List[Tuple[float, float]] = field(default_factory=list)
    discounted_ee: List[Tuple[float, float]] = field(default_factory=list)
    method: str = ""
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibCVACalculator(BaseCalculator):
    """
    QuantLib-based CVA Calculator.
    
    Uses QuantLib for:
    - Credit curve construction
    - Survival probability calculation
    - Discount factor computation
    - Monte Carlo simulation for complex cases
    """
    
    def __init__(self, name: str = "QuantLibCVACalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.CVA
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibCVACalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLCVAInput) -> CalculationResult:
        """
        Calculate CVA using QuantLib.
        
        Args:
            data: QLCVAInput containing exposure and credit parameters
            
        Returns:
            CalculationResult containing QLCVAResult
        """
        self._validate_input(data)
        
        if data.method == CVAMethod.ANALYTICAL:
            result = self._calculate_analytical(data)
        elif data.method == CVAMethod.MONTE_CARLO:
            result = self._calculate_monte_carlo(data)
        elif data.method == CVAMethod.SA_CVA:
            result = self._calculate_sa_cva(data)
        else:
            raise ValueError(f"Unknown CVA method: {data.method}")
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "method": data.method.value,
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A",
            }
        )
    
    def _validate_input(self, data: QLCVAInput) -> None:
        """Validate input parameters."""
        if not data.ee_profile:
            raise ValueError("EE profile cannot be empty")
        if not 0 <= data.recovery_rate <= 1:
            raise ValueError("Recovery rate must be between 0 and 1")
        if data.credit_spread < 0:
            raise ValueError("Credit spread must be non-negative")
    
    def _calculate_analytical(self, data: QLCVAInput) -> QLCVAResult:
        """
        Calculate CVA using analytical integration.
        
        CVA = LGD × Σ EE(tᵢ) × (S(tᵢ₋₁) - S(tᵢ)) × DF(tᵢ)
        
        where S(t) is survival probability and DF(t) is discount factor.
        """
        # Set up QuantLib environment
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today
        day_counter = ql.Actual365Fixed()
        
        # Build credit curve
        lgd = 1 - data.recovery_rate
        hazard_rate = data.credit_spread / 10000 / lgd  # Convert bps to hazard
        
        credit_curve = ql.FlatHazardRate(today, hazard_rate, day_counter)
        
        # Build discount curve
        if data.discount_curve:
            rates = [r for _, r in data.discount_curve]
            avg_rate = sum(rates) / len(rates)
        else:
            avg_rate = 0.05
        
        discount_handle = ql.QuoteHandle(ql.SimpleQuote(avg_rate))
        discount_curve = ql.FlatForward(today, discount_handle, day_counter)
        
        # Calculate CVA
        cva = 0.0
        marginal_cva = []
        survival_probs = []
        discounted_ee = []
        
        prev_survival = 1.0
        
        for i, (t, ee) in enumerate(data.ee_profile):
            if t <= 0:
                continue
            
            # Get survival probability from QuantLib
            survival_t = credit_curve.survivalProbability(t)
            
            # Marginal default probability
            pd_marginal = prev_survival - survival_t
            
            # Discount factor
            df_t = discount_curve.discount(t)
            
            # Apply wrong-way risk adjustment
            wwr_adj = 1 + data.wrong_way_risk_factor * (1 - survival_t)
            ee_adj = ee * wwr_adj
            
            # Marginal CVA for this period
            marginal = lgd * ee_adj * pd_marginal * df_t
            cva += marginal
            
            marginal_cva.append((t, marginal))
            survival_probs.append((t, survival_t))
            discounted_ee.append((t, ee * df_t))
            
            prev_survival = survival_t
        
        # CVA as percentage
        cva_pct = cva / data.notional * 100 if data.notional > 0 else 0
        
        # Calculate DVA if own credit spread provided
        dva = 0.0
        if data.own_credit_spread is not None:
            dva = self._calculate_dva(data)
        
        # Bilateral CVA
        bcva = cva - dva
        
        return QLCVAResult(
            cva=cva,
            cva_pct=cva_pct,
            dva=dva,
            bcva=bcva,
            marginal_cva=marginal_cva,
            survival_probabilities=survival_probs,
            discounted_ee=discounted_ee,
            method=CVAMethod.ANALYTICAL.value,
            components={
                "lgd": lgd,
                "hazard_rate": hazard_rate,
                "discount_rate": avg_rate,
                "wwr_factor": data.wrong_way_risk_factor,
            }
        )
    
    def _calculate_dva(self, data: QLCVAInput) -> float:
        """
        Calculate Debit Valuation Adjustment (DVA).
        
        DVA = Own LGD × Σ NEE(tᵢ) × dPD_own(tᵢ) × DF(tᵢ)
        
        where NEE is negative expected exposure.
        """
        today = ql.Date.todaysDate()
        day_counter = ql.Actual365Fixed()
        
        own_lgd = 1 - data.own_recovery_rate
        own_hazard = data.own_credit_spread / 10000 / own_lgd
        
        own_credit_curve = ql.FlatHazardRate(today, own_hazard, day_counter)
        
        # For DVA, we need negative expected exposure
        # Approximate as symmetric to EE for now
        dva = 0.0
        prev_survival = 1.0
        
        for t, ee in data.ee_profile:
            if t <= 0:
                continue
            
            survival_t = own_credit_curve.survivalProbability(t)
            pd_marginal = prev_survival - survival_t
            
            # NEE approximation (symmetric exposure)
            nee = ee * 0.5  # Simplified
            
            dva += own_lgd * nee * pd_marginal
            prev_survival = survival_t
        
        return dva
    
    def _calculate_monte_carlo(self, data: QLCVAInput) -> QLCVAResult:
        """
        Calculate CVA using Monte Carlo simulation.
        
        Simulates default times and exposure paths jointly.
        """
        today = ql.Date.todaysDate()
        day_counter = ql.Actual365Fixed()
        
        lgd = 1 - data.recovery_rate
        hazard_rate = data.credit_spread / 10000 / lgd
        
        # Number of simulations
        n_sims = 10000
        
        # Set up RNG
        rng = ql.MersenneTwisterUniformRng(42)
        
        maturity = data.maturity or max(t for t, _ in data.ee_profile)
        
        cva_samples = []
        
        for _ in range(n_sims):
            # Simulate default time (exponential distribution)
            u = rng.next().value()
            if u > 0:
                tau = -math.log(u) / hazard_rate
            else:
                tau = float('inf')
            
            # If default occurs before maturity
            if tau <= maturity:
                # Interpolate EE at default time
                ee_at_default = self._interpolate_ee(tau, data.ee_profile)
                
                # Discount factor at default
                df = math.exp(-0.05 * tau)  # Using flat 5% rate
                
                # CVA contribution
                cva_samples.append(lgd * ee_at_default * df)
            else:
                cva_samples.append(0.0)
        
        # Average CVA
        cva = sum(cva_samples) / n_sims
        cva_pct = cva / data.notional * 100 if data.notional > 0 else 0
        
        # DVA
        dva = 0.0
        if data.own_credit_spread is not None:
            dva = self._calculate_dva(data)
        
        bcva = cva - dva
        
        return QLCVAResult(
            cva=cva,
            cva_pct=cva_pct,
            dva=dva,
            bcva=bcva,
            method=CVAMethod.MONTE_CARLO.value,
            components={
                "num_simulations": n_sims,
                "lgd": lgd,
                "hazard_rate": hazard_rate,
            }
        )
    
    def _calculate_sa_cva(self, data: QLCVAInput) -> QLCVAResult:
        """
        Calculate CVA using Standardized Approach (SA-CVA).
        
        Regulatory approach with standardized risk weights.
        """
        # SA-CVA risk weights by credit quality
        # Simplified: use single weight based on credit spread
        if data.credit_spread < 100:  # Investment grade
            rw = 0.05
        elif data.credit_spread < 300:
            rw = 0.10
        elif data.credit_spread < 500:
            rw = 0.15
        else:  # High yield
            rw = 0.25
        
        # EAD for CVA = sum of discounted EE
        ead = sum(ee * math.exp(-0.05 * t) for t, ee in data.ee_profile)
        
        # SA-CVA = RW × M × EAD × LGD
        lgd = 1 - data.recovery_rate
        maturity = data.maturity or max(t for t, _ in data.ee_profile)
        m_factor = min(1, maturity / 1)  # Maturity factor
        
        cva = rw * m_factor * ead * lgd
        cva_pct = cva / data.notional * 100 if data.notional > 0 else 0
        
        return QLCVAResult(
            cva=cva,
            cva_pct=cva_pct,
            dva=0.0,
            bcva=cva,
            method=CVAMethod.SA_CVA.value,
            components={
                "risk_weight": rw,
                "maturity_factor": m_factor,
                "ead": ead,
                "lgd": lgd,
            }
        )
    
    def _interpolate_ee(self, t: float, 
                         ee_profile: List[Tuple[float, float]]) -> float:
        """Linear interpolation of EE profile."""
        if not ee_profile:
            return 0.0
        
        # Find bracketing points
        below = None
        above = None
        
        for time, ee in ee_profile:
            if time <= t:
                below = (time, ee)
            if time >= t and above is None:
                above = (time, ee)
        
        if below is None:
            return ee_profile[0][1]
        if above is None:
            return below[1]
        if below[0] == above[0]:
            return below[1]
        
        # Linear interpolation
        weight = (t - below[0]) / (above[0] - below[0])
        return below[1] + weight * (above[1] - below[1])
    
    def calculate_incremental_cva(self, 
                                   existing_portfolio: List[QLCVAInput],
                                   new_trade: QLCVAInput) -> Dict[str, Any]:
        """
        Calculate incremental CVA for a new trade.
        
        Args:
            existing_portfolio: Existing trades
            new_trade: New trade to add
            
        Returns:
            Incremental CVA analysis
        """
        # Calculate existing portfolio CVA
        existing_cva = sum(self.calculate(trade).result.cva for trade in existing_portfolio)
        
        # Calculate new trade standalone CVA
        standalone_result = self.calculate(new_trade)
        standalone_cva = standalone_result.result.cva
        
        # Calculate combined portfolio CVA
        # Note: This is simplified; proper aggregation would consider netting
        combined_cva = existing_cva + standalone_cva
        
        # Incremental CVA
        incremental_cva = combined_cva - existing_cva
        
        return {
            "incremental_cva": incremental_cva,
            "standalone_cva": standalone_cva,
            "netting_benefit": standalone_cva - incremental_cva,
            "existing_portfolio_cva": existing_cva,
            "combined_portfolio_cva": combined_cva,
        }
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "methods": [m.value for m in CVAMethod],
            "supports_bilateral": True,
            "supports_wwr": True,
            "quantlib_available": QUANTLIB_AVAILABLE,
        }
