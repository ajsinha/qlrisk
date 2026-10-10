# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Exposure at Default (EAD) Calculator.

Leverages QuantLib for advanced exposure calculations, particularly for
derivative pricing and Monte Carlo simulations.

EAD Methods:
- Current Exposure Method (CEM)
- Standardized Approach for CCR (SA-CCR)
- Internal Model Method (IMM)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import math

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import BaseCalculator, CalculationResult, CalculatorType


class EADMethod(Enum):
    """EAD calculation methodology."""
    CEM = "current_exposure_method"
    SA_CCR = "standardized_approach_ccr"
    IMM = "internal_model_method"


@dataclass
class QLEADInput:
    """Input parameters for QuantLib EAD calculation."""
    current_exposure: float
    notional: float
    product_type: str = "irs"
    maturity_years: float = 5.0
    credit_conversion_factor: float = 1.0
    collateral_value: float = 0.0
    collateral_haircut: float = 0.0
    netting_benefit: float = 0.0
    margin_period_of_risk: float = 10.0 / 252.0  # 10 business days
    method: EADMethod = EADMethod.SA_CCR
    volatility: float = 0.15
    num_simulations: int = 10000
    alpha_factor: float = 1.4  # SA-CCR regulatory multiplier
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QLEADResult:
    """Result of QuantLib EAD calculation."""
    ead: float
    gross_exposure: float
    net_exposure: float
    collateralized_exposure: float
    pfe_addon: float
    method: str
    alpha_factor: float
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibEADCalculator(BaseCalculator):
    """
    QuantLib-based Exposure at Default Calculator.
    
    Uses QuantLib for:
    - Derivative pricing for current exposure
    - Monte Carlo simulation for PFE add-on under IMM
    - Day count and schedule generation
    """
    
    # SA-CCR Supervisory Factors by asset class
    SA_CCR_FACTORS = {
        "irs": {"sf": 0.005, "corr": 1.0},
        "fx": {"sf": 0.04, "corr": 1.0},
        "equity": {"sf": 0.32, "corr": 0.75},
        "commodity": {"sf": 0.18, "corr": 0.40},
        "credit_ig": {"sf": 0.0038, "corr": 0.80},
        "credit_hy": {"sf": 0.0540, "corr": 0.80},
    }
    
    # CEM Add-on Factors by product and maturity
    CEM_FACTORS = {
        "irs": {1: 0.0, 2: 0.005, 5: 0.015, 10: 0.03, float('inf'): 0.05},
        "fx": {1: 0.01, 2: 0.02, 5: 0.05, 10: 0.075, float('inf'): 0.10},
        "equity": {1: 0.06, 2: 0.08, 5: 0.10, 10: 0.12, float('inf'): 0.15},
        "commodity": {1: 0.10, 2: 0.12, 5: 0.15, 10: 0.18, float('inf'): 0.20},
        "credit": {1: 0.05, 2: 0.05, 5: 0.05, 10: 0.10, float('inf'): 0.15},
    }
    
    def __init__(self, name: str = "QuantLibEADCalculator", 
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.EAD
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibEADCalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLEADInput) -> CalculationResult:
        """
        Calculate EAD using QuantLib-enhanced methods.
        
        Args:
            data: QLEADInput containing exposure parameters
            
        Returns:
            CalculationResult containing QLEADResult
        """
        self._validate_input(data)
        
        if data.method == EADMethod.CEM:
            result = self._calculate_cem(data)
        elif data.method == EADMethod.SA_CCR:
            result = self._calculate_sa_ccr(data)
        elif data.method == EADMethod.IMM:
            result = self._calculate_imm(data)
        else:
            raise ValueError(f"Unknown EAD method: {data.method}")
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "method": data.method.value,
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A"
            }
        )
    
    def _validate_input(self, data: QLEADInput) -> None:
        """Validate input parameters."""
        if data.notional < 0:
            raise ValueError("Notional must be non-negative")
        if data.collateral_value < 0:
            raise ValueError("Collateral value must be non-negative")
        if not 0 <= data.collateral_haircut <= 1:
            raise ValueError("Collateral haircut must be between 0 and 1")
        if not 0 <= data.netting_benefit <= 1:
            raise ValueError("Netting benefit must be between 0 and 1")
    
    def _calculate_cem(self, data: QLEADInput) -> QLEADResult:
        """
        Calculate EAD using Current Exposure Method.
        
        EAD = CE + Add-on
        where Add-on = Notional × Add-on Factor
        """
        # Get add-on factor based on product type and maturity
        addon_factor = self._get_cem_addon_factor(
            data.product_type, data.maturity_years
        )
        
        # Calculate components
        current_exposure = max(0, data.current_exposure)
        potential_addon = data.notional * addon_factor
        
        # Gross EAD
        gross_ead = current_exposure + potential_addon
        
        # Apply netting
        net_ead = gross_ead * (1 - data.netting_benefit)
        
        # Apply collateral
        effective_collateral = data.collateral_value * (1 - data.collateral_haircut)
        collateralized_ead = max(0, net_ead - effective_collateral)
        
        # Apply CCF
        final_ead = collateralized_ead * data.credit_conversion_factor
        
        return QLEADResult(
            ead=final_ead,
            gross_exposure=gross_ead,
            net_exposure=net_ead,
            collateralized_exposure=collateralized_ead,
            pfe_addon=potential_addon,
            method=EADMethod.CEM.value,
            alpha_factor=1.0,
            components={
                "current_exposure": current_exposure,
                "addon_factor": addon_factor,
                "potential_addon": potential_addon,
                "effective_collateral": effective_collateral,
            }
        )
    
    def _calculate_sa_ccr(self, data: QLEADInput) -> QLEADResult:
        """
        Calculate EAD using Standardized Approach for CCR (Basel III).
        
        EAD = α × (RC + PFE)
        where:
        - α = 1.4 (regulatory multiplier)
        - RC = Replacement Cost
        - PFE = Potential Future Exposure add-on
        """
        # Get SA-CCR factors
        factors = self.SA_CCR_FACTORS.get(
            data.product_type, 
            self.SA_CCR_FACTORS["irs"]
        )
        sf = factors["sf"]
        
        # Replacement Cost (RC)
        current_exposure = max(0, data.current_exposure)
        effective_collateral = data.collateral_value * (1 - data.collateral_haircut)
        rc = max(0, current_exposure - effective_collateral)
        
        # Maturity factor for PFE
        mpor_years = data.margin_period_of_risk
        maturity_factor = self._calculate_maturity_factor_ql(
            data.maturity_years, mpor_years
        )
        
        # Supervisory delta (assume 1.0 for linear products)
        supervisory_delta = data.additional_params.get("supervisory_delta", 1.0)
        
        # Adjusted notional
        adjusted_notional = data.notional * supervisory_delta
        
        # Add-on = SF × MF × Adjusted Notional
        addon = sf * maturity_factor * adjusted_notional
        
        # Apply multiplier for overcollateralization
        if effective_collateral > 0:
            v = current_exposure
            c = effective_collateral
            floor = 0.05
            multiplier = min(1, floor + (1 - floor) * math.exp((v - c) / (2 * (1 - floor) * addon)) if addon > 0 else 1)
        else:
            multiplier = 1.0
        
        pfe_addon = multiplier * addon
        
        # Apply alpha factor
        ead = data.alpha_factor * (rc + pfe_addon)
        
        # Apply netting
        gross_ead = ead
        net_ead = ead * (1 - data.netting_benefit)
        
        return QLEADResult(
            ead=net_ead,
            gross_exposure=gross_ead,
            net_exposure=net_ead,
            collateralized_exposure=rc,
            pfe_addon=pfe_addon,
            method=EADMethod.SA_CCR.value,
            alpha_factor=data.alpha_factor,
            components={
                "replacement_cost": rc,
                "supervisory_factor": sf,
                "maturity_factor": maturity_factor,
                "adjusted_notional": adjusted_notional,
                "multiplier": multiplier,
                "addon_before_multiplier": addon,
            }
        )
    
    def _calculate_imm(self, data: QLEADInput) -> QLEADResult:
        """
        Calculate EAD using Internal Model Method with QuantLib Monte Carlo.
        
        EAD = α × Effective EPE
        where Effective EPE is calculated via Monte Carlo simulation.
        """
        # Set up QuantLib environment
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today
        
        # Create day counter and calendar
        day_counter = ql.Actual365Fixed()
        calendar = ql.TARGET()
        
        # Time grid for simulation
        maturity_date = calendar.advance(today, ql.Period(int(data.maturity_years * 12), ql.Months))
        time_steps = max(12, int(data.maturity_years * 4))  # Quarterly
        
        # Monte Carlo simulation using QuantLib
        effective_epe = self._simulate_effective_epe_ql(
            data, time_steps, data.num_simulations
        )
        
        # EAD = α × Effective EPE
        ead = data.alpha_factor * effective_epe
        
        # Apply netting and collateral
        gross_ead = ead
        net_ead = ead * (1 - data.netting_benefit)
        effective_collateral = data.collateral_value * (1 - data.collateral_haircut)
        collateralized_ead = max(0, net_ead - effective_collateral)
        
        return QLEADResult(
            ead=collateralized_ead,
            gross_exposure=gross_ead,
            net_exposure=net_ead,
            collateralized_exposure=collateralized_ead,
            pfe_addon=effective_epe - max(0, data.current_exposure),
            method=EADMethod.IMM.value,
            alpha_factor=data.alpha_factor,
            components={
                "effective_epe": effective_epe,
                "num_simulations": data.num_simulations,
                "time_steps": time_steps,
            }
        )
    
    def _simulate_effective_epe_ql(self, data: QLEADInput, 
                                    time_steps: int, 
                                    num_simulations: int) -> float:
        """
        Simulate Effective EPE using QuantLib Monte Carlo.
        """
        # Create random number generator
        rng = ql.MersenneTwisterUniformRng(42)
        gaussian_rng = ql.MersenneTwisterGaussianRng(rng)
        
        # Time grid
        dt = data.maturity_years / time_steps
        times = [i * dt for i in range(time_steps + 1)]
        
        # Initialize exposure arrays
        ee_profile = [0.0] * (time_steps + 1)
        
        # Monte Carlo simulation
        for _ in range(num_simulations):
            # Simulate path using GBM
            value = data.current_exposure
            drift = 0.0  # Risk-neutral
            vol = data.volatility
            
            for t_idx in range(1, time_steps + 1):
                z = gaussian_rng.next().value()
                value = value * math.exp((drift - 0.5 * vol**2) * dt + vol * math.sqrt(dt) * z)
                # Exposure is max(0, value)
                ee_profile[t_idx] += max(0, value)
        
        # Average to get EE
        ee_profile = [ee / num_simulations for ee in ee_profile]
        ee_profile[0] = max(0, data.current_exposure)
        
        # Calculate Effective EE (non-decreasing)
        eee_profile = [ee_profile[0]]
        for i in range(1, len(ee_profile)):
            eee_profile.append(max(eee_profile[-1], ee_profile[i]))
        
        # Effective EPE (time-weighted average of EEE)
        effective_epe = 0.0
        for i in range(1, len(times)):
            effective_epe += 0.5 * (eee_profile[i] + eee_profile[i-1]) * (times[i] - times[i-1])
        effective_epe /= data.maturity_years
        
        return effective_epe
    
    def _calculate_maturity_factor_ql(self, maturity_years: float, 
                                       mpor_years: float) -> float:
        """
        Calculate SA-CCR maturity factor using QuantLib day counting.
        
        MF = sqrt(min(M, 1) / 1)
        For margined trades: MF = 1.5 × sqrt(MPOR / 1)
        """
        if mpor_years > 0:
            # Margined trade
            return 1.5 * math.sqrt(mpor_years)
        else:
            # Non-margined
            return math.sqrt(min(maturity_years, 1.0))
    
    def _get_cem_addon_factor(self, product_type: str, 
                               maturity_years: float) -> float:
        """Get CEM add-on factor based on product and maturity."""
        factors = self.CEM_FACTORS.get(product_type, self.CEM_FACTORS["irs"])
        
        for threshold, factor in sorted(factors.items()):
            if maturity_years <= threshold:
                return factor
        
        return list(factors.values())[-1]
    
    def calculate_portfolio_ead(self, trades: List[QLEADInput], 
                                 netting_sets: Optional[Dict[str, List[int]]] = None) -> Dict[str, Any]:
        """
        Calculate portfolio-level EAD with netting set aggregation.
        
        Args:
            trades: List of trade inputs
            netting_sets: Optional mapping of netting set ID to trade indices
            
        Returns:
            Portfolio EAD results
        """
        if not trades:
            return {"portfolio_ead": 0.0, "netting_sets": {}}
        
        if netting_sets is None:
            # No netting - treat each trade independently
            total_ead = 0.0
            results = []
            for trade in trades:
                result = self.calculate(trade)
                total_ead += result.result.ead
                results.append(result.result)
            
            return {
                "portfolio_ead": total_ead,
                "trade_results": results,
                "netting_benefit": 0.0,
            }
        
        # Calculate with netting sets
        netting_set_results = {}
        total_ead = 0.0
        gross_ead = 0.0
        
        for ns_id, trade_indices in netting_sets.items():
            ns_trades = [trades[i] for i in trade_indices]
            
            # Aggregate current exposure
            total_ce = sum(max(0, t.current_exposure) for t in ns_trades)
            total_notional = sum(t.notional for t in ns_trades)
            
            # Use first trade's parameters as representative
            rep_trade = ns_trades[0]
            
            # Create aggregated input
            agg_input = QLEADInput(
                current_exposure=total_ce,
                notional=total_notional,
                product_type=rep_trade.product_type,
                maturity_years=max(t.maturity_years for t in ns_trades),
                collateral_value=sum(t.collateral_value for t in ns_trades),
                collateral_haircut=rep_trade.collateral_haircut,
                netting_benefit=0.0,  # Already aggregated
                method=rep_trade.method,
                alpha_factor=rep_trade.alpha_factor,
            )
            
            result = self.calculate(agg_input)
            netting_set_results[ns_id] = result.result
            total_ead += result.result.ead
            gross_ead += result.result.gross_exposure
        
        netting_benefit = 1 - (total_ead / gross_ead) if gross_ead > 0 else 0
        
        return {
            "portfolio_ead": total_ead,
            "netting_sets": netting_set_results,
            "netting_benefit": netting_benefit,
            "gross_ead": gross_ead,
        }
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "methods": [m.value for m in EADMethod],
            "supported_products": list(self.SA_CCR_FACTORS.keys()),
            "quantlib_available": QUANTLIB_AVAILABLE,
        }
