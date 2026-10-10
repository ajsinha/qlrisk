"""
QLRisk - Exposure at Default (EAD) Calculator
============================================================

Python implementation of EAD calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import math

from ..base import (
    filter_dict_for_dataclass,
    BaseCalculator, ExposureCalculator, CalculatorType, 
    ImplementationType, CalculationResult,
    filter_dict_for_dataclass
)


@dataclass
class EADInput:
    """Input data for EAD calculation."""
    current_exposure: float  # Current mark-to-market value
    notional: float  # Notional amount
    credit_conversion_factor: float = 1.0  # CCF for off-balance sheet items
    add_on_factor: float = 0.0  # Regulatory add-on factor
    collateral_value: float = 0.0  # Value of collateral held
    collateral_haircut: float = 0.0  # Haircut on collateral
    netting_benefit: float = 0.0  # Benefit from netting (0-1)
    margin_period_of_risk: float = 10/252  # MPOR in years (default 10 days)
    
    # For SA-CCR calculation
    replacement_cost: Optional[float] = None
    pfe_add_on: Optional[float] = None


@dataclass
class EADResult:
    """Result of EAD calculation."""
    ead: float
    gross_exposure: float
    net_exposure: float
    collateral_adjusted: float
    method: str
    components: Dict[str, float]


class EADCalculator(ExposureCalculator):
    """
    Exposure at Default (EAD) Calculator.
    
    Calculates EAD using various methodologies:
    - Current Exposure Method (CEM)
    - Standardized Approach for CCR (SA-CCR)
    - Internal Model Method (IMM)
    
    EAD represents the total value at risk at the time of default.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize EAD calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - method: 'cem', 'sa_ccr', or 'imm'
                - alpha: Multiplier for IMM (default 1.4)
                - include_margin: Whether to include margin in calculation
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._method = config.get("method", "cem")
        self._alpha = config.get("alpha", 1.4)  # Basel III alpha multiplier
        self._include_margin = config.get("include_margin", True)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.EAD
    
    def _calculate_impl(self, data: Any) -> EADResult:
        """
        Calculate EAD.
        
        Args:
            data: EADInput or dictionary with required fields
            
        Returns:
            EADResult with calculated EAD and components
        """
        # Convert dict to EADInput if necessary
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, EADInput)
            data = EADInput(**filtered_data)
        
        if self._method == "cem":
            return self._calculate_cem(data)
        elif self._method == "sa_ccr":
            return self._calculate_sa_ccr(data)
        elif self._method == "imm":
            return self._calculate_imm(data)
        else:
            raise ValueError(f"Unknown EAD method: {self._method}")
    
    def _calculate_cem(self, data: EADInput) -> EADResult:
        """
        Current Exposure Method (CEM).
        
        EAD = max(0, CE) + Add-on
        
        Where:
            CE = Current Exposure (mark-to-market)
            Add-on = Notional × Add-on Factor
        """
        # Current exposure (positive values only)
        ce = max(0.0, data.current_exposure)
        
        # Add-on for potential future exposure
        add_on = data.notional * data.add_on_factor
        
        # Gross exposure
        gross_exposure = ce + add_on
        
        # Apply netting benefit
        net_exposure = gross_exposure * (1 - data.netting_benefit)
        
        # Collateral adjustment
        effective_collateral = data.collateral_value * (1 - data.collateral_haircut)
        collateral_adjusted = max(0.0, net_exposure - effective_collateral)
        
        # Final EAD
        ead = collateral_adjusted
        
        return EADResult(
            ead=ead,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            collateral_adjusted=collateral_adjusted,
            method="CEM",
            components={
                "current_exposure": ce,
                "add_on": add_on,
                "netting_benefit_amount": gross_exposure * data.netting_benefit,
                "effective_collateral": effective_collateral
            }
        )
    
    def _calculate_sa_ccr(self, data: EADInput) -> EADResult:
        """
        Standardized Approach for Counterparty Credit Risk (SA-CCR).
        
        EAD = α × (RC + PFE)
        
        Where:
            α = 1.4 (regulatory multiplier)
            RC = Replacement Cost
            PFE = Potential Future Exposure add-on
        """
        # Replacement cost
        if data.replacement_cost is not None:
            rc = data.replacement_cost
        else:
            # Calculate RC from current exposure and collateral
            effective_collateral = data.collateral_value * (1 - data.collateral_haircut)
            rc = max(0.0, data.current_exposure - effective_collateral)
        
        # PFE add-on
        if data.pfe_add_on is not None:
            pfe = data.pfe_add_on
        else:
            # Simplified PFE calculation
            pfe = self._calculate_pfe_add_on(data)
        
        # Gross exposure before alpha
        gross_exposure = rc + pfe
        
        # Apply netting
        net_exposure = gross_exposure * (1 - data.netting_benefit)
        
        # Apply alpha multiplier
        ead = self._alpha * net_exposure
        
        return EADResult(
            ead=ead,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            collateral_adjusted=ead,
            method="SA-CCR",
            components={
                "replacement_cost": rc,
                "pfe_add_on": pfe,
                "alpha": self._alpha,
                "pre_alpha_exposure": net_exposure
            }
        )
    
    def _calculate_pfe_add_on(self, data: EADInput) -> float:
        """
        Calculate PFE add-on for SA-CCR.
        
        Simplified calculation - in practice would depend on asset class.
        """
        # Simplified: use add-on factor on notional with time scaling
        time_factor = math.sqrt(min(1.0, data.margin_period_of_risk))
        return data.notional * data.add_on_factor * time_factor
    
    def _calculate_imm(self, data: EADInput) -> EADResult:
        """
        Internal Model Method (IMM).
        
        EAD = α × Effective EPE
        
        Where:
            α = 1.4 (or bank-specific if approved)
            Effective EPE = max of EE profile (non-decreasing)
        """
        # For IMM, we would typically receive simulated exposure paths
        # Here we use a simplified approach based on current exposure
        
        # Effective collateral
        effective_collateral = data.collateral_value * (1 - data.collateral_haircut)
        
        # Gross exposure estimate
        gross_exposure = max(0.0, data.current_exposure) + \
                        data.notional * data.add_on_factor
        
        # Apply netting
        net_exposure = gross_exposure * (1 - data.netting_benefit)
        
        # Collateral adjustment
        collateral_adjusted = max(0.0, net_exposure - effective_collateral)
        
        # Apply alpha multiplier
        ead = self._alpha * collateral_adjusted
        
        return EADResult(
            ead=ead,
            gross_exposure=gross_exposure,
            net_exposure=net_exposure,
            collateral_adjusted=collateral_adjusted,
            method="IMM",
            components={
                "effective_epe": collateral_adjusted,
                "alpha": self._alpha,
                "effective_collateral": effective_collateral
            }
        )
    
    def calculate_portfolio_ead(self, exposures: List[EADInput], 
                                netting_sets: Optional[Dict[str, List[int]]] = None) -> Dict[str, Any]:
        """
        Calculate EAD for a portfolio of exposures.
        
        Args:
            exposures: List of individual exposure inputs
            netting_sets: Optional mapping of netting set ID to exposure indices
            
        Returns:
            Dictionary with total EAD and breakdown by netting set
        """
        if netting_sets is None:
            # No netting - calculate each exposure individually
            results = []
            total_ead = 0.0
            
            for exp in exposures:
                result = self._calculate_impl(exp)
                results.append(result)
                total_ead += result.ead
            
            return {
                "total_ead": total_ead,
                "individual_results": results,
                "netting_applied": False
            }
        
        # Calculate by netting set
        netting_set_results = {}
        total_ead = 0.0
        
        for ns_id, indices in netting_sets.items():
            ns_exposures = [exposures[i] for i in indices]
            
            # Aggregate within netting set
            total_ce = sum(e.current_exposure for e in ns_exposures)
            total_notional = sum(e.notional for e in ns_exposures)
            avg_ccf = sum(e.credit_conversion_factor for e in ns_exposures) / len(ns_exposures)
            total_collateral = sum(e.collateral_value for e in ns_exposures)
            
            # Calculate netting benefit (simplified)
            gross_sum = sum(max(0, e.current_exposure) for e in ns_exposures)
            net_sum = max(0, total_ce)
            netting_benefit = 1 - (net_sum / gross_sum) if gross_sum > 0 else 0
            
            # Create aggregated input
            agg_input = EADInput(
                current_exposure=total_ce,
                notional=total_notional,
                credit_conversion_factor=avg_ccf,
                collateral_value=total_collateral,
                netting_benefit=netting_benefit
            )
            
            result = self._calculate_impl(agg_input)
            netting_set_results[ns_id] = result
            total_ead += result.ead
        
        return {
            "total_ead": total_ead,
            "netting_set_results": netting_set_results,
            "netting_applied": True
        }
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "method": self._method,
            "alpha": self._alpha,
            "include_margin": self._include_margin
        })
        return base_details
