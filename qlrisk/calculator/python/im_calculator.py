"""
QLRisk - Initial Margin (IM) Calculator
======================================================

Python implementation of Initial Margin calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import math
import random

from ..base import (
    filter_dict_for_dataclass,
    BaseCalculator, CalculatorType, ImplementationType
)


@dataclass
class IMInput:
    """Input data for Initial Margin calculation."""
    # Trade-level inputs
    notional: float
    product_type: str  # "irs", "fx", "equity", "credit", "commodity"
    remaining_maturity: float  # years
    
    # Risk factors
    volatility: float = 0.0  # If not provided, uses regulatory schedule
    delta: float = 1.0  # For options
    
    # Optional: sensitivity-based inputs (for SIMM)
    delta_sensitivities: Optional[Dict[str, float]] = None
    vega_sensitivities: Optional[Dict[str, float]] = None
    curvature_sensitivities: Optional[Dict[str, float]] = None
    
    # For portfolio
    correlation_within: float = 0.5  # Within bucket
    correlation_across: float = 0.25  # Across buckets
    
    # MPOR
    margin_period_of_risk: float = 10/252  # 10 days default
    
    # For schedule approach
    gross_notional: Optional[float] = None
    net_to_gross_ratio: float = 0.4


@dataclass
class IMResult:
    """Result of Initial Margin calculation."""
    initial_margin: float
    im_as_pct_notional: float
    method: str
    components: Dict[str, Any]


class InitialMarginCalculator(BaseCalculator[IMResult]):
    """
    Initial Margin (IM) Calculator.
    
    Initial Margin is collateral collected upfront to cover potential
    future exposure during the margin period of risk.
    
    Methods supported:
    - ISDA SIMM (Standard Initial Margin Model)
    - Grid/Schedule approach (regulatory)
    - Historical VaR (parametric approximation)
    
    SIMM formula:
    IM = √(Σ_i IM_i² + 2×Σ_{i<j} ρ_{ij}×IM_i×IM_j)
    
    Where IM_i is margin for each risk class.
    """
    
    # SIMM risk weights by asset class and bucket (simplified)
    SIMM_WEIGHTS = {
        "rates": {
            "2w": 0.0077, "1m": 0.0077, "3m": 0.0077, "6m": 0.0077,
            "1y": 0.0070, "2y": 0.0065, "3y": 0.0061, "5y": 0.0056,
            "10y": 0.0052, "15y": 0.0050, "20y": 0.0050, "30y": 0.0050
        },
        "fx": {"all": 0.30},
        "equity": {"large_cap": 0.21, "small_cap": 0.26, "emerging": 0.36},
        "credit": {"ig": 0.0039, "hy": 0.0085, "sovereign": 0.0028},
        "commodity": {"energy": 0.30, "metals": 0.22, "agriculture": 0.25}
    }
    
    # Schedule approach percentages
    SCHEDULE_RATES = {
        "irs": {(0, 2): 0.01, (2, 5): 0.02, (5, float('inf')): 0.04},
        "fx": {(0, 1): 0.01, (1, 5): 0.02, (5, float('inf')): 0.04},
        "equity": {(0, 1): 0.06, (1, 5): 0.08, (5, float('inf')): 0.10},
        "credit": {(0, 2): 0.02, (2, 5): 0.05, (5, float('inf')): 0.10},
        "commodity": {(0, 1): 0.10, (1, 5): 0.12, (5, float('inf')): 0.15}
    }
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        """
        Initialize Initial Margin calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - method: 'simm', 'schedule', or 'var'
                - confidence_level: VaR confidence level (default 0.99)
                - mpor_scaling: Whether to scale for MPOR
        """
        config = config or {}
        name = name or self.__class__.__name__
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._method = config.get("method", "schedule")
        self._confidence_level = config.get("confidence_level", 0.99)
        self._mpor_scaling = config.get("mpor_scaling", True)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.IM
    
    def _calculate_impl(self, data: Any) -> IMResult:
        """
        Calculate Initial Margin.
        
        Args:
            data: IMInput or dictionary
            
        Returns:
            IMResult with IM and components
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, IMInput)
            data = IMInput(**filtered_data)
        
        if self._method == "simm":
            return self._calculate_simm(data)
        elif self._method == "schedule":
            return self._calculate_schedule(data)
        elif self._method == "var":
            return self._calculate_var(data)
        else:
            raise ValueError(f"Unknown IM method: {self._method}")
    
    def _calculate_simm(self, data: IMInput) -> IMResult:
        """
        ISDA SIMM calculation.
        
        IM = Σ Risk_Class_IM aggregated with correlations
        """
        components = {}
        
        # Determine risk class
        risk_class = self._get_risk_class(data.product_type)
        
        # Get sensitivities (use delta if not provided)
        if data.delta_sensitivities:
            sensitivities = data.delta_sensitivities
        else:
            # Default: use notional × delta as sensitivity
            sensitivities = {"base": data.notional * data.delta}
        
        # Calculate delta margin
        delta_margin = self._calculate_simm_delta(
            risk_class, sensitivities, data
        )
        components["delta_margin"] = delta_margin
        
        # Calculate vega margin (if applicable)
        vega_margin = 0.0
        if data.vega_sensitivities:
            vega_margin = self._calculate_simm_vega(
                risk_class, data.vega_sensitivities, data
            )
        components["vega_margin"] = vega_margin
        
        # Calculate curvature margin (if applicable)
        curvature_margin = 0.0
        if data.curvature_sensitivities:
            curvature_margin = self._calculate_simm_curvature(
                risk_class, data.curvature_sensitivities, data
            )
        components["curvature_margin"] = curvature_margin
        
        # Aggregate across components
        # IM = sqrt(Delta² + Vega² + Curvature²)
        im = math.sqrt(delta_margin**2 + vega_margin**2 + curvature_margin**2)
        
        # MPOR scaling if needed
        if self._mpor_scaling:
            mpor_factor = math.sqrt(data.margin_period_of_risk * 252 / 10)
            im *= mpor_factor
            components["mpor_factor"] = mpor_factor
        
        im_pct = (im / data.notional * 100) if data.notional > 0 else 0
        
        return IMResult(
            initial_margin=im,
            im_as_pct_notional=im_pct,
            method="SIMM",
            components=components
        )
    
    def _calculate_simm_delta(self, risk_class: str,
                               sensitivities: Dict[str, float],
                               data: IMInput) -> float:
        """Calculate SIMM delta margin."""
        # Get risk weights
        weights = self.SIMM_WEIGHTS.get(risk_class, {"all": 0.10})
        
        # Apply weights to sensitivities
        weighted_sens = []
        for bucket, sens in sensitivities.items():
            weight = weights.get(bucket, weights.get("all", 0.10))
            weighted_sens.append(abs(sens) * weight)
        
        # Aggregate within risk class
        if len(weighted_sens) == 1:
            return weighted_sens[0]
        
        # With correlations
        rho = data.correlation_within
        total = 0.0
        for i, ws_i in enumerate(weighted_sens):
            for j, ws_j in enumerate(weighted_sens):
                if i == j:
                    total += ws_i ** 2
                else:
                    total += rho * ws_i * ws_j
        
        return math.sqrt(max(0, total))
    
    def _calculate_simm_vega(self, risk_class: str,
                              sensitivities: Dict[str, float],
                              data: IMInput) -> float:
        """Calculate SIMM vega margin."""
        # Simplified: apply vega risk weight
        vega_weight = 0.55  # Simplified constant
        
        total_vega = sum(abs(v) for v in sensitivities.values())
        return total_vega * vega_weight
    
    def _calculate_simm_curvature(self, risk_class: str,
                                   sensitivities: Dict[str, float],
                                   data: IMInput) -> float:
        """Calculate SIMM curvature margin."""
        # Curvature is the second-order effect
        curvature_weight = 0.5
        
        total_curv = sum(abs(c) for c in sensitivities.values())
        return total_curv * curvature_weight
    
    def _calculate_schedule(self, data: IMInput) -> IMResult:
        """
        Schedule/Grid approach for IM.
        
        IM = NGR × Gross Notional × Add-on Rate
        
        Where NGR = Net-to-Gross Ratio (regulatory factor)
        """
        # Get schedule rates for this product
        product = data.product_type.lower()
        if product in ["irs", "interest_rate_swap"]:
            schedule = self.SCHEDULE_RATES["irs"]
        elif product in ["fx_forward", "fx_option", "fx"]:
            schedule = self.SCHEDULE_RATES["fx"]
        elif product in ["equity", "equity_option"]:
            schedule = self.SCHEDULE_RATES["equity"]
        elif product in ["cds", "credit"]:
            schedule = self.SCHEDULE_RATES["credit"]
        else:
            schedule = self.SCHEDULE_RATES.get(product, self.SCHEDULE_RATES["fx"])
        
        # Find applicable rate based on maturity
        rate = 0.0
        for (lower, upper), r in schedule.items():
            if lower <= data.remaining_maturity < upper:
                rate = r
                break
        
        # Gross notional
        gross = data.gross_notional if data.gross_notional else data.notional
        
        # Net-to-Gross Ratio (NGR)
        ngr = data.net_to_gross_ratio
        
        # Initial Margin
        im = ngr * gross * rate
        
        # MPOR adjustment
        if self._mpor_scaling and data.margin_period_of_risk != 10/252:
            mpor_factor = math.sqrt(data.margin_period_of_risk * 252 / 10)
            im *= mpor_factor
        else:
            mpor_factor = 1.0
        
        im_pct = (im / data.notional * 100) if data.notional > 0 else 0
        
        return IMResult(
            initial_margin=im,
            im_as_pct_notional=im_pct,
            method="Schedule",
            components={
                "schedule_rate": rate,
                "ngr": ngr,
                "gross_notional": gross,
                "maturity": data.remaining_maturity,
                "mpor_factor": mpor_factor
            }
        )
    
    def _calculate_var(self, data: IMInput) -> IMResult:
        """
        VaR-based IM calculation.
        
        IM = VaR(MPOR, α) = σ × √MPOR × Z(α) × |Sensitivity|
        """
        # Use provided volatility or estimate
        if data.volatility > 0:
            vol = data.volatility
        else:
            vol = self._estimate_volatility(data.product_type)
        
        # MPOR in years
        mpor = data.margin_period_of_risk
        
        # Z-score for confidence level
        z = self._norm_inv(self._confidence_level)
        
        # Sensitivity (delta × notional for linear products)
        sensitivity = abs(data.delta * data.notional)
        
        # VaR
        im = vol * math.sqrt(mpor) * z * sensitivity
        
        im_pct = (im / data.notional * 100) if data.notional > 0 else 0
        
        return IMResult(
            initial_margin=im,
            im_as_pct_notional=im_pct,
            method="VaR",
            components={
                "volatility": vol,
                "mpor_years": mpor,
                "mpor_days": mpor * 252,
                "z_score": z,
                "confidence_level": self._confidence_level,
                "sensitivity": sensitivity
            }
        )
    
    def _get_risk_class(self, product_type: str) -> str:
        """Map product type to SIMM risk class."""
        mapping = {
            "irs": "rates",
            "interest_rate_swap": "rates",
            "fra": "rates",
            "fx_forward": "fx",
            "fx_option": "fx",
            "fx": "fx",
            "equity": "equity",
            "equity_option": "equity",
            "cds": "credit",
            "credit": "credit",
            "commodity": "commodity"
        }
        return mapping.get(product_type.lower(), "fx")
    
    def _estimate_volatility(self, product_type: str) -> float:
        """Estimate volatility for product type."""
        vol_estimates = {
            "irs": 0.005,  # 0.5% for rates
            "fx": 0.10,    # 10% for FX
            "equity": 0.20,  # 20% for equity
            "credit": 0.15,  # 15% for credit
            "commodity": 0.25  # 25% for commodity
        }
        return vol_estimates.get(product_type.lower(), 0.10)
    
    def _norm_inv(self, p: float) -> float:
        """Inverse standard normal CDF."""
        if p <= 0:
            return -10.0
        if p >= 1:
            return 10.0
        
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
        c = [
            -7.784894002430293e-03, -3.223964580411365e-01,
            -2.400758277161838e+00, -2.549732539343734e+00,
            4.374664141464968e+00, 2.938163982698783e+00
        ]
        d = [
            7.784695709041462e-03, 3.224671290700398e-01,
            2.445134137142996e+00, 3.754408661907416e+00
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
    
    def calculate_portfolio_im(self, positions: List[IMInput]) -> Dict[str, Any]:
        """
        Calculate portfolio-level Initial Margin.
        
        Aggregates across positions with netting benefits.
        """
        if not positions:
            return {"initial_margin": 0.0, "positions": []}
        
        # Calculate individual IMs
        individual_ims = []
        by_risk_class = {}
        
        for pos in positions:
            result = self._calculate_impl(pos)
            individual_ims.append(result)
            
            risk_class = self._get_risk_class(pos.product_type)
            if risk_class not in by_risk_class:
                by_risk_class[risk_class] = []
            by_risk_class[risk_class].append(result.initial_margin)
        
        # Aggregate by risk class
        risk_class_ims = {}
        for rc, ims in by_risk_class.items():
            # Within risk class: use correlation
            rho = 0.5  # Default within-class correlation
            total = sum(im**2 for im in ims)
            for i in range(len(ims)):
                for j in range(i+1, len(ims)):
                    total += 2 * rho * ims[i] * ims[j]
            risk_class_ims[rc] = math.sqrt(max(0, total))
        
        # Aggregate across risk classes
        rc_list = list(risk_class_ims.values())
        rho_cross = 0.25  # Cross-class correlation
        total_im_sq = sum(im**2 for im in rc_list)
        for i in range(len(rc_list)):
            for j in range(i+1, len(rc_list)):
                total_im_sq += 2 * rho_cross * rc_list[i] * rc_list[j]
        
        portfolio_im = math.sqrt(max(0, total_im_sq))
        
        # Diversification benefit
        gross_im = sum(r.initial_margin for r in individual_ims)
        diversification = gross_im - portfolio_im
        
        return {
            "initial_margin": portfolio_im,
            "gross_im": gross_im,
            "diversification_benefit": diversification,
            "diversification_pct": (diversification / gross_im * 100) if gross_im > 0 else 0,
            "by_risk_class": risk_class_ims,
            "num_positions": len(positions)
        }
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "method": self._method,
            "confidence_level": self._confidence_level,
            "mpor_scaling": self._mpor_scaling
        })
        return base_details
