# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Initial Margin (IM) Calculator.

Implements ISDA SIMM, Schedule-based, and VaR-based IM methodologies.

SIMM: IM = √(Σ IM_i² + 2Σρ_ij × IM_i × IM_j)
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


class IMMethod(Enum):
    """Initial Margin calculation methodology."""
    SIMM = "isda_simm"
    SCHEDULE = "schedule_based"
    VAR = "var_based"


class AssetClass(Enum):
    """SIMM Asset Classes."""
    INTEREST_RATE = "interest_rate"
    FX = "fx"
    EQUITY = "equity"
    CREDIT_QUALIFYING = "credit_qualifying"
    CREDIT_NON_QUALIFYING = "credit_non_qualifying"
    COMMODITY = "commodity"


@dataclass
class QLIMInput:
    """Input parameters for QuantLib Initial Margin calculation."""
    notional: float
    product_type: str = "irs"
    maturity_years: float = 5.0
    volatility: float = 0.01
    delta_sensitivities: Optional[Dict[str, float]] = None  # By risk factor
    vega_sensitivities: Optional[Dict[str, float]] = None
    curvature_sensitivities: Optional[Dict[str, float]] = None
    margin_period_of_risk: float = 10.0 / 252.0  # 10 days
    confidence_level: float = 0.99
    asset_class: str = "interest_rate"
    currency: str = "USD"
    method: IMMethod = IMMethod.SIMM
    net_gross_ratio: float = 0.6  # NGR for schedule method


@dataclass
class QLIMResult:
    """Result of QuantLib Initial Margin calculation."""
    initial_margin: float
    im_as_pct_notional: float
    method: str
    asset_class_breakdown: Dict[str, float] = field(default_factory=dict)
    risk_class_breakdown: Dict[str, float] = field(default_factory=dict)
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibIMCalculator(BaseCalculator):
    """
    QuantLib-based Initial Margin Calculator.
    
    Implements ISDA SIMM methodology with proper risk weights and correlations.
    """
    
    # SIMM Risk Weights (simplified)
    SIMM_RISK_WEIGHTS = {
        "interest_rate": {
            "delta": {
                "2w": 77, "1m": 77, "3m": 72, "6m": 75, "1y": 70,
                "2y": 67, "3y": 62, "5y": 60, "10y": 61, "15y": 62,
                "20y": 63, "30y": 61
            },
            "vega": 0.16,
            "curvature": 0.5,
        },
        "fx": {
            "delta": {"regular": 7.9, "high_volatility": 11.6},
            "vega": 0.30,
            "curvature": 0.5,
        },
        "equity": {
            "delta": {"bucket_1": 21, "bucket_2": 25, "bucket_3": 28, "bucket_4": 24},
            "vega": 0.26,
            "curvature": 0.5,
        },
        "credit_qualifying": {
            "delta": {"ig": 39, "hy": 57},
            "vega": 0.27,
            "curvature": 0.5,
        },
        "commodity": {
            "delta": {"energy": 16, "metals": 18, "agriculture": 15},
            "vega": 0.36,
            "curvature": 0.5,
        },
    }
    
    # SIMM Correlations (simplified)
    SIMM_CORRELATIONS = {
        "interest_rate": {
            "intra_bucket": 0.98,
            "inter_bucket": 0.27,
        },
        "fx": {
            "intra_bucket": 0.60,
            "inter_bucket": 0.60,
        },
        "equity": {
            "intra_bucket": 0.16,
            "inter_bucket": 0.16,
        },
        "credit_qualifying": {
            "intra_bucket": 0.65,
            "inter_bucket": 0.45,
        },
        "commodity": {
            "intra_bucket": 0.22,
            "inter_bucket": 0.22,
        },
    }
    
    # Schedule-based add-on rates
    SCHEDULE_RATES = {
        "irs": {0: 0.00, 2: 0.005, 5: 0.01, 10: 0.015, 30: 0.02, float('inf'): 0.04},
        "fx": {0: 0.01, 1: 0.02, 3: 0.04, 5: 0.06, float('inf'): 0.08},
        "equity": {0: 0.08, 1: 0.10, 3: 0.12, 5: 0.15, float('inf'): 0.18},
        "credit": {0: 0.02, 2: 0.03, 5: 0.05, 10: 0.08, float('inf'): 0.10},
        "commodity": {0: 0.10, 1: 0.12, 3: 0.15, 5: 0.18, float('inf'): 0.20},
    }
    
    def __init__(self, name: str = "QuantLibIMCalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.INITIAL_MARGIN
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibIMCalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLIMInput) -> CalculationResult:
        """
        Calculate Initial Margin.
        
        Args:
            data: QLIMInput containing sensitivity and product parameters
            
        Returns:
            CalculationResult containing QLIMResult
        """
        self._validate_input(data)
        
        if data.method == IMMethod.SIMM:
            result = self._calculate_simm(data)
        elif data.method == IMMethod.SCHEDULE:
            result = self._calculate_schedule(data)
        elif data.method == IMMethod.VAR:
            result = self._calculate_var(data)
        else:
            raise ValueError(f"Unknown IM method: {data.method}")
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "method": data.method.value,
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A",
            }
        )
    
    def _validate_input(self, data: QLIMInput) -> None:
        """Validate input parameters."""
        if data.notional < 0:
            raise ValueError("Notional must be non-negative")
        if data.maturity_years <= 0:
            raise ValueError("Maturity must be positive")
        if not 0 < data.confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
    
    def _calculate_simm(self, data: QLIMInput) -> QLIMResult:
        """
        Calculate IM using ISDA SIMM methodology.
        
        IM = √(Delta² + Vega² + Curvature²)
        where each component aggregates across risk factors.
        """
        asset_class = data.asset_class
        
        # Get or estimate sensitivities
        delta_sens = data.delta_sensitivities or self._estimate_delta(data)
        vega_sens = data.vega_sensitivities or self._estimate_vega(data)
        curv_sens = data.curvature_sensitivities or {}
        
        # Calculate Delta margin
        delta_im = self._calculate_delta_margin(delta_sens, asset_class)
        
        # Calculate Vega margin
        vega_im = self._calculate_vega_margin(vega_sens, asset_class)
        
        # Calculate Curvature margin
        curv_im = self._calculate_curvature_margin(curv_sens, asset_class)
        
        # Total IM with diversification
        # Using simplified aggregation
        total_im = math.sqrt(delta_im**2 + vega_im**2 + curv_im**2)
        
        # Apply MPOR scaling
        mpor_scale = math.sqrt(data.margin_period_of_risk * 252 / 10)
        total_im *= mpor_scale
        
        # IM as percentage of notional
        im_pct = total_im / data.notional * 100 if data.notional > 0 else 0
        
        return QLIMResult(
            initial_margin=total_im,
            im_as_pct_notional=im_pct,
            method=IMMethod.SIMM.value,
            asset_class_breakdown={asset_class: total_im},
            risk_class_breakdown={
                "delta": delta_im,
                "vega": vega_im,
                "curvature": curv_im,
            },
            components={
                "mpor_scale": mpor_scale,
                "delta_sensitivities": sum(delta_sens.values()) if delta_sens else 0,
                "vega_sensitivities": sum(vega_sens.values()) if vega_sens else 0,
            }
        )
    
    def _calculate_delta_margin(self, sensitivities: Dict[str, float], 
                                 asset_class: str) -> float:
        """Calculate delta margin contribution."""
        if not sensitivities:
            return 0.0
        
        weights = self.SIMM_RISK_WEIGHTS.get(asset_class, {}).get("delta", {})
        correlations = self.SIMM_CORRELATIONS.get(asset_class, {})
        
        # Weight sensitivities
        weighted_sens = []
        for tenor, sens in sensitivities.items():
            if isinstance(weights, dict):
                weight = weights.get(tenor, 60)  # Default weight
            else:
                weight = weights
            weighted_sens.append(weight * sens / 10000)  # Convert to decimal
        
        if not weighted_sens:
            return 0.0
        
        # Aggregate with correlation
        intra_corr = correlations.get("intra_bucket", 0.5)
        
        # Simplified: sum of squared weighted sens + 2 × correlation × cross products
        n = len(weighted_sens)
        margin_sq = sum(w**2 for w in weighted_sens)
        
        for i in range(n):
            for j in range(i+1, n):
                margin_sq += 2 * intra_corr * weighted_sens[i] * weighted_sens[j]
        
        return math.sqrt(max(0, margin_sq))
    
    def _calculate_vega_margin(self, sensitivities: Dict[str, float], 
                                asset_class: str) -> float:
        """Calculate vega margin contribution."""
        if not sensitivities:
            return 0.0
        
        vega_weight = self.SIMM_RISK_WEIGHTS.get(asset_class, {}).get("vega", 0.20)
        
        weighted_sens = [vega_weight * sens for sens in sensitivities.values()]
        
        # Simple sum of squares
        return math.sqrt(sum(w**2 for w in weighted_sens))
    
    def _calculate_curvature_margin(self, sensitivities: Dict[str, float], 
                                     asset_class: str) -> float:
        """Calculate curvature margin contribution."""
        if not sensitivities:
            return 0.0
        
        curv_weight = self.SIMM_RISK_WEIGHTS.get(asset_class, {}).get("curvature", 0.5)
        
        weighted_sens = [curv_weight * sens for sens in sensitivities.values()]
        
        return math.sqrt(sum(w**2 for w in weighted_sens))
    
    def _estimate_delta(self, data: QLIMInput) -> Dict[str, float]:
        """Estimate delta sensitivities from product parameters."""
        # Simplified estimation based on product type
        if data.product_type in ["irs", "swap"]:
            # IRS has duration-based sensitivity
            duration = min(data.maturity_years, 10) * 0.8
            sens = data.notional * duration / 10000  # DV01
            return {"5y": sens}
        
        elif data.product_type in ["fx", "fx_forward"]:
            sens = data.notional * 0.01
            return {"spot": sens}
        
        elif data.product_type in ["equity", "equity_option"]:
            sens = data.notional * 0.05
            return {"equity": sens}
        
        return {"default": data.notional * 0.01}
    
    def _estimate_vega(self, data: QLIMInput) -> Dict[str, float]:
        """Estimate vega sensitivities from product parameters."""
        if data.volatility > 0:
            vega = data.notional * data.volatility * math.sqrt(data.maturity_years)
            return {"atm": vega * 0.01}
        return {}
    
    def _calculate_schedule(self, data: QLIMInput) -> QLIMResult:
        """
        Calculate IM using Schedule/Grid approach.
        
        IM = NGR × Gross Notional × Add-on Rate
        """
        # Get schedule rate
        rates = self.SCHEDULE_RATES.get(data.product_type, self.SCHEDULE_RATES["irs"])
        
        addon_rate = 0.0
        for threshold, rate in sorted(rates.items()):
            if data.maturity_years <= threshold:
                addon_rate = rate
                break
        
        # IM = NGR × Notional × Add-on
        im = data.net_gross_ratio * data.notional * addon_rate
        
        # Apply MPOR scaling
        mpor_scale = math.sqrt(data.margin_period_of_risk * 252 / 10)
        im *= mpor_scale
        
        im_pct = im / data.notional * 100 if data.notional > 0 else 0
        
        return QLIMResult(
            initial_margin=im,
            im_as_pct_notional=im_pct,
            method=IMMethod.SCHEDULE.value,
            components={
                "addon_rate": addon_rate,
                "ngr": data.net_gross_ratio,
                "mpor_scale": mpor_scale,
            }
        )
    
    def _calculate_var(self, data: QLIMInput) -> QLIMResult:
        """
        Calculate IM using VaR-based approach.
        
        IM = σ × √MPOR × Z(α) × |Sensitivity|
        """
        # Get confidence level quantile using QuantLib
        inv_norm = ql.InverseCumulativeNormal()
        z_alpha = inv_norm(data.confidence_level)
        
        # Estimate sensitivity if not provided
        if data.delta_sensitivities:
            sensitivity = sum(abs(s) for s in data.delta_sensitivities.values())
        else:
            # Duration-based for IR
            if data.product_type in ["irs", "swap"]:
                duration = min(data.maturity_years, 10) * 0.8
                sensitivity = data.notional * duration / 10000
            else:
                sensitivity = data.notional * 0.01
        
        # VaR-based IM
        im = data.volatility * math.sqrt(data.margin_period_of_risk) * z_alpha * sensitivity
        
        im_pct = im / data.notional * 100 if data.notional > 0 else 0
        
        return QLIMResult(
            initial_margin=im,
            im_as_pct_notional=im_pct,
            method=IMMethod.VAR.value,
            components={
                "z_alpha": z_alpha,
                "volatility": data.volatility,
                "mpor": data.margin_period_of_risk,
                "sensitivity": sensitivity,
            }
        )
    
    def calculate_portfolio_im(self, 
                                trades: List[QLIMInput],
                                diversification_factor: float = 0.7) -> Dict[str, Any]:
        """
        Calculate portfolio-level Initial Margin.
        
        Args:
            trades: List of trade inputs
            diversification_factor: Diversification benefit factor
            
        Returns:
            Portfolio IM results
        """
        if not trades:
            return {"portfolio_im": 0.0}
        
        # Calculate individual IMs
        individual_ims = []
        asset_class_ims = {}
        
        for trade in trades:
            result = self.calculate(trade)
            individual_ims.append(result.result.initial_margin)
            
            # Track by asset class
            ac = trade.asset_class
            asset_class_ims[ac] = asset_class_ims.get(ac, 0) + result.result.initial_margin
        
        # Gross IM
        gross_im = sum(individual_ims)
        
        # Portfolio IM with diversification
        # Simplified: apply diversification factor to non-nettable portion
        portfolio_im = gross_im * diversification_factor
        
        # Cross-asset class diversification
        if len(asset_class_ims) > 1:
            # Additional diversification for multiple asset classes
            cross_asset_div = 0.8
            portfolio_im *= cross_asset_div
        
        return {
            "portfolio_im": portfolio_im,
            "gross_im": gross_im,
            "diversification_benefit": gross_im - portfolio_im,
            "diversification_factor": diversification_factor,
            "asset_class_breakdown": asset_class_ims,
            "num_trades": len(trades),
        }
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "methods": [m.value for m in IMMethod],
            "asset_classes": [ac.value for ac in AssetClass],
            "default_mpor": "10 days",
            "quantlib_available": QUANTLIB_AVAILABLE,
        }
