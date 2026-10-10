"""
QLRisk - XVA Calculators v1.2.0
==============================================

Valuation adjustments calculators:
- DVA: Debit Valuation Adjustment
- FVA: Funding Valuation Adjustment  
- KVA: Capital Valuation Adjustment
- MVA: Margin Valuation Adjustment
- ColVA: Collateral Valuation Adjustment

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import math
import numpy as np

from ..base import BaseCalculator, CalculatorType, ImplementationType
from ...products.base import curve_value


# ============================================================================
# DVA - Debit Valuation Adjustment
# ============================================================================

@dataclass
class DVAInput:
    """Input for DVA calculation."""
    exposure_profile: List[float] = field(default_factory=list)
    time_grid: List[float] = field(default_factory=list)
    own_pd_curve: Dict[float, float] = field(default_factory=dict)
    own_lgd: float = 0.60
    discount_curve: Dict[float, float] = field(default_factory=dict)


@dataclass
class DVAResult:
    """DVA calculation result."""
    dva: float = 0.0
    expected_negative_exposure: float = 0.0
    own_default_probability: float = 0.0


class DVACalculator(BaseCalculator):
    """
    Debit Valuation Adjustment Calculator.
    
    DVA represents the benefit from own default risk.
    DVA = -CVA from counterparty's perspective.
    """
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        super().__init__(name or "dva_calc", config or {})
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.DVA
    
    def _calculate_impl(self, data: Any) -> DVAResult:
        """Accepts a DVAInput or a dict of its fields; returns DVAResult."""
        if isinstance(data, dict):
            data = DVAInput(**{k: v for k, v in data.items() if k in DVAInput.__dataclass_fields__})
        return self.compute(data)
    
    
    def compute(self, input_data: DVAInput) -> DVAResult:
        """Calculate DVA."""
        result = DVAResult()
        
        if not input_data.exposure_profile or not input_data.time_grid:
            return result
        
        dva = 0.0
        prev_survival = 1.0
        
        for i in range(1, len(input_data.time_grid)):
            t = input_data.time_grid[i]
            dt = t - input_data.time_grid[i-1]
            
            # Get negative exposure (what we owe counterparty)
            # This is opposite of CVA exposure
            ene = abs(min(0, input_data.exposure_profile[i]))
            
            # Own default probability
            pd = curve_value(input_data.own_pd_curve, t, 0.01)
            marginal_pd = prev_survival * pd * dt
            
            # Discount factor  
            r = curve_value(input_data.discount_curve, t, 0.05)
            df = math.exp(-r * t)
            
            # DVA contribution (benefit from own default)
            dva += input_data.own_lgd * ene * marginal_pd * df
            
            prev_survival *= (1 - pd * dt)
        
        result.dva = dva
        result.expected_negative_exposure = sum(
            abs(min(0, e)) for e in input_data.exposure_profile
        ) / len(input_data.exposure_profile)
        
        return result


# ============================================================================
# FVA - Funding Valuation Adjustment
# ============================================================================

@dataclass
class FVAInput:
    """Input for FVA calculation."""
    exposure_profile: List[float] = field(default_factory=list)
    time_grid: List[float] = field(default_factory=list)
    funding_spread: float = 0.01  # Own funding spread over risk-free
    discount_curve: Dict[float, float] = field(default_factory=dict)
    counterparty_survival_curve: Dict[float, float] = field(default_factory=dict)


@dataclass
class FVAResult:
    """FVA calculation result."""
    fva: float = 0.0
    fba: float = 0.0  # Funding benefit adjustment
    fca: float = 0.0  # Funding cost adjustment


class FVACalculator(BaseCalculator):
    """
    Funding Valuation Adjustment Calculator.
    
    FVA captures the cost/benefit of funding uncollateralized derivatives.
    FVA = FCA - FBA
    """
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        super().__init__(name or "fva_calc", config or {})
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.FVA
    
    def _calculate_impl(self, data: Any) -> FVAResult:
        """Accepts a FVAInput or a dict of its fields; returns FVAResult."""
        if isinstance(data, dict):
            data = FVAInput(**{k: v for k, v in data.items() if k in FVAInput.__dataclass_fields__})
        return self.compute(data)
    
    
    def compute(self, input_data: FVAInput) -> FVAResult:
        """Calculate FVA."""
        result = FVAResult()
        
        if not input_data.exposure_profile or not input_data.time_grid:
            return result
        
        fca = 0.0  # Funding cost (for positive exposure)
        fba = 0.0  # Funding benefit (for negative exposure)
        
        for i in range(1, len(input_data.time_grid)):
            t = input_data.time_grid[i]
            dt = t - input_data.time_grid[i-1]
            
            exposure = input_data.exposure_profile[i]
            
            # Discount factor
            r = curve_value(input_data.discount_curve, t, 0.05)
            df = math.exp(-r * t)
            
            # Counterparty survival
            surv = curve_value(input_data.counterparty_survival_curve, t, 0.99)
            
            if exposure > 0:
                # Positive exposure: funding cost
                fca += input_data.funding_spread * exposure * surv * df * dt
            else:
                # Negative exposure: funding benefit
                fba += input_data.funding_spread * abs(exposure) * surv * df * dt
        
        result.fca = fca
        result.fba = fba
        result.fva = fca - fba
        
        return result


# ============================================================================
# KVA - Capital Valuation Adjustment
# ============================================================================

@dataclass
class KVAInput:
    """Input for KVA calculation."""
    ead_profile: List[float] = field(default_factory=list)
    time_grid: List[float] = field(default_factory=list)
    counterparty_pd: float = 0.01
    counterparty_lgd: float = 0.45
    cost_of_capital: float = 0.10  # 10% hurdle rate
    discount_curve: Dict[float, float] = field(default_factory=dict)
    capital_floor: float = 0.0003  # Basel floor


@dataclass
class KVAResult:
    """KVA calculation result."""
    kva: float = 0.0
    average_capital: float = 0.0
    peak_capital: float = 0.0


class KVACalculator(BaseCalculator):
    """
    Capital Valuation Adjustment Calculator.
    
    KVA represents the cost of holding regulatory capital
    against counterparty credit risk.
    """
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        super().__init__(name or "kva_calc", config or {})
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.KVA
    
    def _calculate_impl(self, data: Any) -> KVAResult:
        """Accepts a KVAInput or a dict of its fields; returns KVAResult."""
        if isinstance(data, dict):
            data = KVAInput(**{k: v for k, v in data.items() if k in KVAInput.__dataclass_fields__})
        return self.compute(data)
    
    
    def compute(self, input_data: KVAInput) -> KVAResult:
        """Calculate KVA."""
        result = KVAResult()
        
        if not input_data.ead_profile or not input_data.time_grid:
            return result
        
        kva = 0.0
        capital_profile = []
        
        for i in range(1, len(input_data.time_grid)):
            t = input_data.time_grid[i]
            dt = t - input_data.time_grid[i-1]
            
            ead = input_data.ead_profile[i]
            
            # Risk weight (simplified Basel IRB)
            rw = self._calculate_risk_weight(
                input_data.counterparty_pd,
                input_data.counterparty_lgd
            )
            
            # Capital requirement
            capital = max(
                input_data.capital_floor * ead,
                0.08 * rw * ead
            )
            capital_profile.append(capital)
            
            # Discount factor
            r = curve_value(input_data.discount_curve, t, 0.05)
            df = math.exp(-r * t)
            
            # KVA contribution
            kva += input_data.cost_of_capital * capital * df * dt
        
        result.kva = kva
        result.average_capital = np.mean(capital_profile) if capital_profile else 0.0
        result.peak_capital = max(capital_profile) if capital_profile else 0.0
        
        return result
    
    def _calculate_risk_weight(self, pd: float, lgd: float) -> float:
        """Calculate Basel IRB risk weight."""
        # Simplified IRB formula
        r = 0.12 * (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)) + \
            0.24 * (1 - (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)))
        
        # Maturity adjustment (simplified)
        b = (0.11852 - 0.05478 * math.log(pd)) ** 2
        
        # Risk weight
        k = lgd * (self._norm_cdf(
            (self._norm_inv(pd) + math.sqrt(r) * self._norm_inv(0.999)) / 
            math.sqrt(1 - r)
        ) - pd)
        
        return max(0, 12.5 * k)
    
    def _norm_cdf(self, x: float) -> float:
        """Standard normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _norm_inv(self, p: float) -> float:
        """Inverse standard normal (approximate)."""
        if p <= 0:
            return -10.0
        if p >= 1:
            return 10.0
        
        a = [0, -3.969683028665376e+01, 2.209460984245205e+02,
             -2.759285104469687e+02, 1.383577518672690e+02,
             -3.066479806614716e+01, 2.506628277459239e+00]
        b = [0, -5.447609879822406e+01, 1.615858368580409e+02,
             -1.556989798598866e+02, 6.680131188771972e+01,
             -1.328068155288572e+01]
        c = [0, -7.784894002430293e-03, -3.223964580411365e-01,
             -2.400758277161838e+00, -2.549732539343734e+00,
             4.374664141464968e+00, 2.938163982698783e+00]
        d = [0, 7.784695709041462e-03, 3.224671290700398e-01,
             2.445134137142996e+00, 3.754408661907416e+00]
        
        p_low = 0.02425
        p_high = 1 - p_low
        
        if p < p_low:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[1]*q + c[2])*q + c[3])*q + c[4])*q + c[5])*q + c[6]) / \
                   ((((d[1]*q + d[2])*q + d[3])*q + d[4])*q + 1)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            return (((((a[1]*r + a[2])*r + a[3])*r + a[4])*r + a[5])*r + a[6])*q / \
                   (((((b[1]*r + b[2])*r + b[3])*r + b[4])*r + b[5])*r + 1)
        else:
            q = math.sqrt(-2 * math.log(1 - p))
            return -(((((c[1]*q + c[2])*q + c[3])*q + c[4])*q + c[5])*q + c[6]) / \
                    ((((d[1]*q + d[2])*q + d[3])*q + d[4])*q + 1)


# ============================================================================
# MVA - Margin Valuation Adjustment
# ============================================================================

@dataclass
class MVAInput:
    """Input for MVA calculation."""
    initial_margin_profile: List[float] = field(default_factory=list)
    time_grid: List[float] = field(default_factory=list)
    funding_spread: float = 0.01
    discount_curve: Dict[float, float] = field(default_factory=dict)


@dataclass
class MVAResult:
    """MVA calculation result."""
    mva: float = 0.0
    average_margin: float = 0.0


class MVACalculator(BaseCalculator):
    """
    Margin Valuation Adjustment Calculator.
    
    MVA represents the cost of funding initial margin.
    """
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        super().__init__(name or "mva_calc", config or {})
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.MVA
    
    def _calculate_impl(self, data: Any) -> MVAResult:
        """Accepts a MVAInput or a dict of its fields; returns MVAResult."""
        if isinstance(data, dict):
            data = MVAInput(**{k: v for k, v in data.items() if k in MVAInput.__dataclass_fields__})
        return self.compute(data)
    
    
    def compute(self, input_data: MVAInput) -> MVAResult:
        """Calculate MVA."""
        result = MVAResult()
        
        if not input_data.initial_margin_profile or not input_data.time_grid:
            return result
        
        mva = 0.0
        
        for i in range(1, len(input_data.time_grid)):
            t = input_data.time_grid[i]
            dt = t - input_data.time_grid[i-1]
            
            im = input_data.initial_margin_profile[i]
            
            # Discount factor
            r = curve_value(input_data.discount_curve, t, 0.05)
            df = math.exp(-r * t)
            
            # MVA contribution
            mva += input_data.funding_spread * im * df * dt
        
        result.mva = mva
        result.average_margin = np.mean(input_data.initial_margin_profile)
        
        return result


# ============================================================================
# Total XVA
# ============================================================================

@dataclass
class TotalXVAResult:
    """Combined XVA result."""
    cva: float = 0.0
    dva: float = 0.0
    fva: float = 0.0
    kva: float = 0.0
    mva: float = 0.0
    colva: float = 0.0
    total_xva: float = 0.0
    
    def calculate_total(self) -> float:
        """Calculate total XVA."""
        self.total_xva = self.cva + self.dva + self.fva + self.kva + self.mva + self.colva
        return self.total_xva


__all__ = [
    # DVA
    "DVAInput", "DVAResult", "DVACalculator",
    # FVA
    "FVAInput", "FVAResult", "FVACalculator",
    # KVA
    "KVAInput", "KVAResult", "KVACalculator",
    # MVA
    "MVAInput", "MVAResult", "MVACalculator",
    # Total
    "TotalXVAResult",
]
