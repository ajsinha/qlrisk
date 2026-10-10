"""
QLRisk - Current Exposure (CE) Calculator
========================================================

Python implementation of Current Exposure calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..base import (
    filter_dict_for_dataclass,
    ExposureCalculator, CalculatorType, ImplementationType
)


@dataclass
class CEInput:
    """Input data for Current Exposure calculation."""
    mark_to_market: float  # Current MTM value
    collateral_held: float = 0.0  # Collateral received
    collateral_posted: float = 0.0  # Collateral posted
    collateral_haircut: float = 0.0  # Haircut on collateral
    threshold: float = 0.0  # Collateral threshold
    minimum_transfer_amount: float = 0.0  # MTA
    independent_amount: float = 0.0  # Initial margin / IA
    
    # Netting information
    netting_set_id: Optional[str] = None
    trades_in_netting_set: Optional[List[float]] = None  # MTM of trades in set


@dataclass
class CEResult:
    """Result of Current Exposure calculation."""
    gross_ce: float
    net_ce: float
    collateralized_ce: float
    exposure_type: str  # 'positive', 'negative', 'zero'
    components: Dict[str, float]


class CurrentExposureCalculator(ExposureCalculator):
    """
    Current Exposure (CE) Calculator.
    
    Calculates current exposure as the replacement cost of outstanding
    derivative transactions. CE represents the immediate loss if the
    counterparty defaults today.
    
    CE = max(0, MTM - Collateral)
    
    Features:
    - Gross and net exposure calculation
    - Collateral adjustment with haircuts
    - Netting set aggregation
    """
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        """
        Initialize Current Exposure calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - apply_netting: Whether to apply netting benefits
                - apply_collateral: Whether to apply collateral
                - include_threshold: Whether to include threshold in calculation
        """
        config = config or {}
        name = name or self.__class__.__name__
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._apply_netting = config.get("apply_netting", True)
        self._apply_collateral = config.get("apply_collateral", True)
        self._include_threshold = config.get("include_threshold", True)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.CE
    
    def _calculate_impl(self, data: Any) -> CEResult:
        """
        Calculate Current Exposure.
        
        Args:
            data: CEInput or dictionary with required fields
            
        Returns:
            CEResult with calculated current exposure
        """
        # Convert dict to CEInput if necessary
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, CEInput)
            data = CEInput(**filtered_data)
        
        # Calculate gross exposure
        if data.trades_in_netting_set and self._apply_netting:
            # Netting set calculation
            gross_ce = self._calculate_gross_netting_set(data.trades_in_netting_set)
            net_mtm = sum(data.trades_in_netting_set)
            net_ce = max(0.0, net_mtm)
        else:
            # Single trade or no netting
            gross_ce = max(0.0, data.mark_to_market)
            net_ce = gross_ce
        
        # Apply collateral if enabled
        if self._apply_collateral:
            collateralized_ce = self._apply_collateral_adjustment(
                net_ce, data
            )
        else:
            collateralized_ce = net_ce
        
        # Determine exposure type
        if data.mark_to_market > 0:
            exposure_type = "positive"
        elif data.mark_to_market < 0:
            exposure_type = "negative"
        else:
            exposure_type = "zero"
        
        # Build components
        components = {
            "mark_to_market": data.mark_to_market,
            "collateral_held": data.collateral_held,
            "collateral_posted": data.collateral_posted,
            "net_collateral": data.collateral_held - data.collateral_posted,
            "threshold": data.threshold,
            "independent_amount": data.independent_amount
        }
        
        if data.trades_in_netting_set:
            components["netting_benefit"] = gross_ce - net_ce
            components["netting_benefit_ratio"] = (gross_ce - net_ce) / gross_ce if gross_ce > 0 else 0
        
        return CEResult(
            gross_ce=gross_ce,
            net_ce=net_ce,
            collateralized_ce=collateralized_ce,
            exposure_type=exposure_type,
            components=components
        )
    
    def _calculate_gross_netting_set(self, trade_mtms: List[float]) -> float:
        """
        Calculate gross exposure for a netting set.
        
        Gross CE = sum of positive MTM values
        """
        return sum(max(0.0, mtm) for mtm in trade_mtms)
    
    def _apply_collateral_adjustment(self, exposure: float, data: CEInput) -> float:
        """
        Apply collateral adjustment to exposure.
        
        Collateralized CE = max(0, Exposure - Net Collateral + Threshold)
        """
        # Effective collateral after haircut
        effective_collateral = data.collateral_held * (1 - data.collateral_haircut)
        
        # Net collateral position
        net_collateral = effective_collateral - data.collateral_posted
        
        # Apply threshold if configured
        if self._include_threshold:
            # Threshold reduces the collateral benefit
            adjusted_collateral = max(0.0, net_collateral - data.threshold)
        else:
            adjusted_collateral = net_collateral
        
        # Add independent amount requirement
        adjusted_collateral -= data.independent_amount
        
        # Final collateralized exposure
        return max(0.0, exposure - adjusted_collateral)
    
    def calculate_netting_set_ce(self, trades: List[CEInput]) -> Dict[str, Any]:
        """
        Calculate Current Exposure for a complete netting set.
        
        Args:
            trades: List of trade inputs within the netting set
            
        Returns:
            Dictionary with netting set analysis
        """
        # Extract MTM values
        mtm_values = [t.mark_to_market for t in trades]
        
        # Gross exposure (sum of positive MTMs)
        gross_ce = sum(max(0.0, mtm) for mtm in mtm_values)
        
        # Net exposure (net MTM if positive)
        net_mtm = sum(mtm_values)
        net_ce = max(0.0, net_mtm)
        
        # Aggregate collateral
        total_collateral_held = sum(t.collateral_held for t in trades)
        total_collateral_posted = sum(t.collateral_posted for t in trades)
        avg_haircut = sum(t.collateral_haircut for t in trades) / len(trades) if trades else 0
        
        # Collateralized exposure
        effective_collateral = total_collateral_held * (1 - avg_haircut)
        net_collateral = effective_collateral - total_collateral_posted
        collateralized_ce = max(0.0, net_ce - net_collateral)
        
        # Netting benefit
        netting_benefit = gross_ce - net_ce
        netting_ratio = netting_benefit / gross_ce if gross_ce > 0 else 0
        
        # Trade-level contributions
        contributions = []
        for i, (trade, mtm) in enumerate(zip(trades, mtm_values)):
            contribution = {
                "trade_index": i,
                "mtm": mtm,
                "gross_contribution": max(0.0, mtm),
                "marginal_contribution": self._calculate_marginal_contribution(mtm_values, i)
            }
            contributions.append(contribution)
        
        return {
            "gross_ce": gross_ce,
            "net_ce": net_ce,
            "collateralized_ce": collateralized_ce,
            "netting_benefit": netting_benefit,
            "netting_ratio": netting_ratio,
            "net_mtm": net_mtm,
            "num_trades": len(trades),
            "trade_contributions": contributions,
            "collateral": {
                "held": total_collateral_held,
                "posted": total_collateral_posted,
                "net": net_collateral,
                "effective": effective_collateral
            }
        }
    
    def _calculate_marginal_contribution(self, mtm_values: List[float], 
                                          exclude_index: int) -> float:
        """
        Calculate marginal contribution of a trade to netting set CE.
        
        Marginal contribution = CE(set) - CE(set without trade)
        """
        # Full set CE
        full_net = sum(mtm_values)
        full_ce = max(0.0, full_net)
        
        # Set without this trade
        reduced_net = full_net - mtm_values[exclude_index]
        reduced_ce = max(0.0, reduced_net)
        
        return full_ce - reduced_ce
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "apply_netting": self._apply_netting,
            "apply_collateral": self._apply_collateral,
            "include_threshold": self._include_threshold
        })
        return base_details
