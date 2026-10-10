"""
QLRisk - Credit Valuation Adjustment (CVA) Calculator
====================================================================

Python implementation of CVA calculation.

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
    BaseCalculator, CalculatorType, ImplementationType
)


@dataclass
class CVAInput:
    """Input data for CVA calculation."""
    # Exposure profile
    ee_profile: List[float]  # Expected Exposure at each time point
    time_grid: List[float]  # Time points in years
    
    # Credit parameters
    credit_spread: float  # Credit spread in basis points or decimal
    recovery_rate: float = 0.4  # Recovery rate
    
    # Optional: term structure of credit
    spread_term_structure: Optional[List[float]] = None
    
    # Discount curve
    discount_rates: Optional[List[float]] = None
    risk_free_rate: float = 0.05
    
    # For bilateral CVA
    own_credit_spread: Optional[float] = None
    own_recovery_rate: float = 0.4
    
    # Notional (for normalization)
    notional: float = 1.0


@dataclass 
class CVAResult:
    """Result of CVA calculation."""
    cva: float  # Unilateral CVA
    cva_pct: float  # CVA as percentage of notional
    dva: Optional[float]  # Debt Valuation Adjustment (if bilateral)
    bcva: Optional[float]  # Bilateral CVA = CVA - DVA
    marginal_cva: List[float]  # CVA contribution by time bucket
    components: Dict[str, Any]


class CVACalculator(BaseCalculator[CVAResult]):
    """
    Credit Valuation Adjustment (CVA) Calculator.
    
    CVA represents the market price of counterparty credit risk.
    It is the expected loss due to counterparty default.
    
    Unilateral CVA:
    CVA = LGD × ∫ EE(t) × dPD(t) × DF(t)
    
    Where:
        LGD = 1 - Recovery Rate
        EE(t) = Expected Exposure at time t
        dPD(t) = Marginal probability of default
        DF(t) = Discount factor
    
    Bilateral CVA (BCVA):
    BCVA = CVA - DVA
    
    Where DVA is the Debt Valuation Adjustment representing
    the benefit from own default.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize CVA calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - method: 'analytical', 'monte_carlo', or 'sa_cva' (standardized)
                - bilateral: Whether to calculate bilateral CVA
                - wrong_way_risk: Whether to include WWR adjustment
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._method = config.get("method", "analytical")
        self._bilateral = config.get("bilateral", False)
        self._wrong_way_risk = config.get("wrong_way_risk", False)
        self._wwr_correlation = config.get("wwr_correlation", 0.0)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.CVA
    
    def _calculate_impl(self, data: Any) -> CVAResult:
        """
        Calculate CVA.
        
        Args:
            data: CVAInput or dictionary
            
        Returns:
            CVAResult with CVA and components
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, CVAInput)
            data = CVAInput(**filtered_data)
        
        # Validate inputs
        self._validate_inputs(data)
        
        if self._method == "analytical":
            return self._calculate_analytical(data)
        elif self._method == "monte_carlo":
            return self._calculate_monte_carlo(data)
        elif self._method == "sa_cva":
            return self._calculate_standardized(data)
        else:
            raise ValueError(f"Unknown CVA method: {self._method}")
    
    def _validate_inputs(self, data: CVAInput) -> None:
        """Validate CVA inputs."""
        if len(data.ee_profile) != len(data.time_grid):
            raise ValueError("EE profile and time grid must have same length")
        
        if data.recovery_rate < 0 or data.recovery_rate > 1:
            raise ValueError("Recovery rate must be between 0 and 1")
    
    def _calculate_analytical(self, data: CVAInput) -> CVAResult:
        """
        Analytical CVA calculation.
        
        CVA = LGD × Σ EE(t_i) × (S(t_{i-1}) - S(t_i)) × DF(t_i)
        
        Where S(t) is survival probability.
        """
        lgd = 1 - data.recovery_rate
        time_grid = data.time_grid
        ee_profile = data.ee_profile
        
        # Calculate survival probabilities
        survival_probs = self._calculate_survival_probabilities(
            data.credit_spread, 
            lgd,
            time_grid,
            data.spread_term_structure
        )
        
        # Calculate discount factors
        discount_factors = self._calculate_discount_factors(
            time_grid,
            data.discount_rates,
            data.risk_free_rate
        )
        
        # Calculate CVA
        cva = 0.0
        marginal_cva = []
        
        for i in range(1, len(time_grid)):
            # Marginal default probability
            marginal_pd = survival_probs[i-1] - survival_probs[i]
            
            # Average exposure in period
            avg_ee = (ee_profile[i] + ee_profile[i-1]) / 2
            
            # Discount factor at midpoint
            df = (discount_factors[i] + discount_factors[i-1]) / 2
            
            # Wrong-way risk adjustment
            if self._wrong_way_risk:
                wwr_adjustment = self._calculate_wwr_adjustment(
                    avg_ee, marginal_pd, self._wwr_correlation
                )
                avg_ee *= (1 + wwr_adjustment)
            
            # Marginal CVA for this period
            period_cva = lgd * avg_ee * marginal_pd * df
            marginal_cva.append(period_cva)
            cva += period_cva
        
        # CVA as percentage
        cva_pct = cva / data.notional if data.notional > 0 else 0
        
        # Bilateral CVA if requested
        dva = None
        bcva = None
        
        if self._bilateral and data.own_credit_spread is not None:
            dva = self._calculate_dva(data)
            bcva = cva - dva
        
        return CVAResult(
            cva=cva,
            cva_pct=cva_pct * 100,  # as percentage
            dva=dva,
            bcva=bcva,
            marginal_cva=marginal_cva,
            components={
                "method": "analytical",
                "lgd": lgd,
                "survival_probs": survival_probs,
                "discount_factors": discount_factors,
                "bilateral": self._bilateral
            }
        )
    
    def _calculate_monte_carlo(self, data: CVAInput) -> CVAResult:
        """
        Monte Carlo CVA calculation.
        
        Simulates default times and calculates expected loss.
        """
        lgd = 1 - data.recovery_rate
        num_simulations = self.config.get("num_simulations", 10000)
        
        # Calculate hazard rate from spread
        hazard_rate = data.credit_spread / lgd
        
        # Simulate default times
        total_cva = 0.0
        default_count = 0
        
        for _ in range(num_simulations):
            # Exponential default time
            u = random.random()
            if u > 0:
                default_time = -math.log(u) / hazard_rate
            else:
                default_time = float('inf')
            
            # Check if default within horizon
            max_time = data.time_grid[-1]
            if default_time <= max_time:
                default_count += 1
                
                # Interpolate exposure at default time
                exposure_at_default = self._interpolate_exposure(
                    data.ee_profile, data.time_grid, default_time
                )
                
                # Discount factor at default
                df = math.exp(-data.risk_free_rate * default_time)
                
                # Loss given default
                loss = lgd * exposure_at_default * df
                total_cva += loss
        
        cva = total_cva / num_simulations
        cva_pct = cva / data.notional if data.notional > 0 else 0
        
        return CVAResult(
            cva=cva,
            cva_pct=cva_pct * 100,
            dva=None,
            bcva=None,
            marginal_cva=[],
            components={
                "method": "monte_carlo",
                "num_simulations": num_simulations,
                "default_frequency": default_count / num_simulations
            }
        )
    
    def _calculate_standardized(self, data: CVAInput) -> CVAResult:
        """
        Standardized Approach CVA (SA-CVA) per Basel III.
        
        CVA = 2.33 × √(h × Σ(w_i × M_i × EAD_i)²)
        
        Simplified implementation.
        """
        lgd = 1 - data.recovery_rate
        
        # Effective maturity
        effective_maturity = data.time_grid[-1] if data.time_grid else 1.0
        
        # Effective EE (using EPE concept)
        effective_ee = sum(data.ee_profile) / len(data.ee_profile) if data.ee_profile else 0
        
        # Credit quality weight (based on spread)
        weight = self._get_sa_cva_weight(data.credit_spread)
        
        # Supervisory factor
        h = 1.0  # 1-year horizon
        
        # SA-CVA
        cva = 2.33 * math.sqrt(h) * weight * effective_maturity * effective_ee
        cva_pct = cva / data.notional if data.notional > 0 else 0
        
        return CVAResult(
            cva=cva,
            cva_pct=cva_pct * 100,
            dva=None,
            bcva=None,
            marginal_cva=[],
            components={
                "method": "sa_cva",
                "effective_maturity": effective_maturity,
                "weight": weight
            }
        )
    
    def _calculate_survival_probabilities(self, spread: float, lgd: float,
                                           time_grid: List[float],
                                           spread_ts: Optional[List[float]] = None) -> List[float]:
        """
        Calculate survival probabilities from credit spread.
        
        S(t) = exp(-λt) where λ = spread / LGD
        """
        hazard_rate = spread / lgd if lgd > 0 else spread
        
        survival_probs = []
        for i, t in enumerate(time_grid):
            if spread_ts and i < len(spread_ts):
                h = spread_ts[i] / lgd
            else:
                h = hazard_rate
            
            survival_probs.append(math.exp(-h * t))
        
        return survival_probs
    
    def _calculate_discount_factors(self, time_grid: List[float],
                                     rates: Optional[List[float]],
                                     flat_rate: float) -> List[float]:
        """Calculate discount factors."""
        dfs = []
        for i, t in enumerate(time_grid):
            if rates and i < len(rates):
                r = rates[i]
            else:
                r = flat_rate
            dfs.append(math.exp(-r * t))
        return dfs
    
    def _calculate_wwr_adjustment(self, exposure: float, pd: float, 
                                   correlation: float) -> float:
        """
        Calculate wrong-way risk adjustment.
        
        WWR increases exposure when counterparty is more likely to default.
        """
        # Simple linear WWR adjustment
        return correlation * math.sqrt(pd)
    
    def _calculate_dva(self, data: CVAInput) -> float:
        """
        Calculate DVA (Debt Valuation Adjustment).
        
        DVA is the CVA from counterparty's perspective - our benefit
        from own default.
        """
        own_lgd = 1 - data.own_recovery_rate
        
        # Use negative of expected exposure (counterparty's view)
        nee_profile = [-ee for ee in data.ee_profile]
        
        # Survival probabilities for own default
        survival_probs = self._calculate_survival_probabilities(
            data.own_credit_spread, own_lgd, data.time_grid, None
        )
        
        # Discount factors
        dfs = self._calculate_discount_factors(
            data.time_grid, data.discount_rates, data.risk_free_rate
        )
        
        dva = 0.0
        for i in range(1, len(data.time_grid)):
            marginal_pd = survival_probs[i-1] - survival_probs[i]
            avg_nee = (max(0, -nee_profile[i]) + max(0, -nee_profile[i-1])) / 2
            df = (dfs[i] + dfs[i-1]) / 2
            dva += own_lgd * avg_nee * marginal_pd * df
        
        return dva
    
    def _interpolate_exposure(self, ee_profile: List[float], 
                               time_grid: List[float],
                               target_time: float) -> float:
        """Interpolate exposure at a specific time."""
        if target_time <= time_grid[0]:
            return ee_profile[0]
        if target_time >= time_grid[-1]:
            return ee_profile[-1]
        
        for i in range(1, len(time_grid)):
            if time_grid[i] >= target_time:
                t0, t1 = time_grid[i-1], time_grid[i]
                e0, e1 = ee_profile[i-1], ee_profile[i]
                weight = (target_time - t0) / (t1 - t0)
                return e0 + weight * (e1 - e0)
        
        return ee_profile[-1]
    
    def _get_sa_cva_weight(self, spread: float) -> float:
        """Get SA-CVA risk weight based on credit quality."""
        # Spread in bps
        spread_bps = spread * 10000 if spread < 1 else spread
        
        if spread_bps <= 100:
            return 0.007
        elif spread_bps <= 250:
            return 0.015
        elif spread_bps <= 500:
            return 0.025
        elif spread_bps <= 1000:
            return 0.04
        else:
            return 0.06
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "method": self._method,
            "bilateral": self._bilateral,
            "wrong_way_risk": self._wrong_way_risk
        })
        return base_details
