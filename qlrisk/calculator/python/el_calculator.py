"""
QLRisk - Expected Loss (EL) Calculator
=====================================================

Python implementation of Expected Loss calculation.

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
    BaseCalculator, CreditRiskCalculator, CalculatorType,
    ImplementationType, CalculationResult,
    filter_dict_for_dataclass
)


@dataclass
class ELInput:
    """Input data for Expected Loss calculation."""
    pd: float  # Probability of Default (0-1)
    lgd: float  # Loss Given Default (0-1)
    ead: float  # Exposure at Default (currency units)
    time_horizon: float = 1.0  # Time horizon in years
    
    # Optional components
    maturity: Optional[float] = None  # Remaining maturity
    recovery_rate: Optional[float] = None  # Alternative to LGD
    
    # For term structure calculation
    pd_term_structure: Optional[List[float]] = None
    time_points: Optional[List[float]] = None


@dataclass
class ELResult:
    """Result of Expected Loss calculation."""
    expected_loss: float
    expected_loss_rate: float
    annualized_el: float
    components: Dict[str, float]
    term_structure: Optional[Dict[str, List[float]]] = None


class ExpectedLossCalculator(CreditRiskCalculator):
    """
    Expected Loss (EL) Calculator.
    
    Calculates Expected Loss using:
    EL = PD × LGD × EAD
    
    Also supports:
    - Term structure of expected losses
    - Annualized expected loss
    - Cumulative expected loss
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Expected Loss calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - time_horizon: Default time horizon in years
                - annualize: Whether to annualize results
                - use_term_structure: Whether to calculate term structure
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._time_horizon = config.get("time_horizon", 1.0)
        self._annualize = config.get("annualize", True)
        self._use_term_structure = config.get("use_term_structure", False)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.EL
    
    def _calculate_impl(self, data: Any) -> ELResult:
        """
        Calculate Expected Loss.
        
        Args:
            data: ELInput or dictionary with required fields
            
        Returns:
            ELResult with calculated expected loss and components
        """
        # Convert dict to ELInput if necessary
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, ELInput)
            data = ELInput(**filtered_data)
        
        # Validate inputs
        self._validate_inputs(data)
        
        # Use recovery rate if LGD not provided
        lgd = data.lgd
        if lgd is None and data.recovery_rate is not None:
            lgd = 1 - data.recovery_rate
        
        # Basic Expected Loss calculation
        # EL = PD × LGD × EAD
        expected_loss = data.pd * lgd * data.ead
        
        # Expected Loss Rate (per unit of exposure)
        expected_loss_rate = data.pd * lgd
        
        # Annualized Expected Loss
        time_horizon = data.time_horizon if data.time_horizon else self._time_horizon
        if time_horizon != 1.0 and self._annualize:
            annualized_el = expected_loss / time_horizon
        else:
            annualized_el = expected_loss
        
        # Build components
        components = {
            "pd": data.pd,
            "lgd": lgd,
            "ead": data.ead,
            "time_horizon": time_horizon
        }
        
        # Calculate term structure if requested
        term_structure = None
        if self._use_term_structure and data.pd_term_structure and data.time_points:
            term_structure = self._calculate_term_structure(
                data.pd_term_structure,
                data.time_points,
                lgd,
                data.ead
            )
        
        return ELResult(
            expected_loss=expected_loss,
            expected_loss_rate=expected_loss_rate,
            annualized_el=annualized_el,
            components=components,
            term_structure=term_structure
        )
    
    def _validate_inputs(self, data: ELInput) -> None:
        """Validate input parameters."""
        if data.pd < 0 or data.pd > 1:
            raise ValueError(f"PD must be between 0 and 1, got {data.pd}")
        
        if data.lgd is not None and (data.lgd < 0 or data.lgd > 1):
            raise ValueError(f"LGD must be between 0 and 1, got {data.lgd}")
        
        if data.ead < 0:
            raise ValueError(f"EAD must be non-negative, got {data.ead}")
        
        if data.recovery_rate is not None and (data.recovery_rate < 0 or data.recovery_rate > 1):
            raise ValueError(f"Recovery rate must be between 0 and 1, got {data.recovery_rate}")
    
    def _calculate_term_structure(self, pd_term_structure: List[float],
                                   time_points: List[float],
                                   lgd: float,
                                   ead: float) -> Dict[str, List[float]]:
        """
        Calculate term structure of expected losses.
        
        Args:
            pd_term_structure: PD values at each time point
            time_points: Time points in years
            lgd: Loss Given Default
            ead: Exposure at Default
            
        Returns:
            Dictionary with marginal and cumulative EL term structures
        """
        marginal_el = []
        cumulative_el = []
        cumulative = 0.0
        
        for i, (pd, t) in enumerate(zip(pd_term_structure, time_points)):
            # Marginal EL for this period
            if i == 0:
                marginal = pd * lgd * ead
            else:
                # Incremental PD for this period
                prev_cumulative_pd = sum(pd_term_structure[:i])
                survival_prob = 1 - prev_cumulative_pd
                conditional_pd = pd / survival_prob if survival_prob > 0 else pd
                marginal = conditional_pd * lgd * ead * survival_prob
            
            marginal_el.append(marginal)
            cumulative += marginal
            cumulative_el.append(cumulative)
        
        return {
            "time_points": time_points,
            "marginal_el": marginal_el,
            "cumulative_el": cumulative_el
        }
    
    def calculate_portfolio_el(self, exposures: List[ELInput],
                                correlation_matrix: Optional[List[List[float]]] = None) -> Dict[str, Any]:
        """
        Calculate Expected Loss for a portfolio.
        
        Args:
            exposures: List of individual exposure inputs
            correlation_matrix: Optional correlation matrix for joint default
            
        Returns:
            Dictionary with portfolio EL and contribution analysis
        """
        individual_els = []
        total_el = 0.0
        total_ead = 0.0
        
        for exp in exposures:
            result = self._calculate_impl(exp)
            individual_els.append(result)
            total_el += result.expected_loss
            total_ead += exp.ead
        
        # Calculate concentration metrics
        el_contributions = [r.expected_loss / total_el if total_el > 0 else 0 
                          for r in individual_els]
        
        # Herfindahl-Hirschman Index for concentration
        hhi = sum(c ** 2 for c in el_contributions)
        
        # Portfolio expected loss rate
        portfolio_el_rate = total_el / total_ead if total_ead > 0 else 0
        
        return {
            "total_el": total_el,
            "portfolio_el_rate": portfolio_el_rate,
            "total_ead": total_ead,
            "individual_results": individual_els,
            "el_contributions": el_contributions,
            "concentration_hhi": hhi,
            "effective_number_of_names": 1 / hhi if hhi > 0 else len(exposures)
        }
    
    def calculate_marginal_el(self, base_portfolio: List[ELInput],
                               new_exposure: ELInput) -> Dict[str, Any]:
        """
        Calculate marginal Expected Loss contribution of new exposure.
        
        Args:
            base_portfolio: Existing portfolio exposures
            new_exposure: New exposure to be added
            
        Returns:
            Dictionary with marginal EL analysis
        """
        # Calculate base portfolio EL
        base_result = self.calculate_portfolio_el(base_portfolio)
        base_el = base_result["total_el"]
        
        # Calculate new portfolio EL
        new_portfolio = base_portfolio + [new_exposure]
        new_result = self.calculate_portfolio_el(new_portfolio)
        new_el = new_result["total_el"]
        
        # Marginal contribution
        marginal_el = new_el - base_el
        
        # Stand-alone EL
        standalone_result = self._calculate_impl(new_exposure)
        standalone_el = standalone_result.expected_loss
        
        # Diversification benefit (if any)
        diversification = standalone_el - marginal_el
        
        return {
            "marginal_el": marginal_el,
            "standalone_el": standalone_el,
            "diversification_benefit": diversification,
            "diversification_ratio": diversification / standalone_el if standalone_el > 0 else 0,
            "base_portfolio_el": base_el,
            "new_portfolio_el": new_el
        }
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "time_horizon": self._time_horizon,
            "annualize": self._annualize,
            "use_term_structure": self._use_term_structure
        })
        return base_details
