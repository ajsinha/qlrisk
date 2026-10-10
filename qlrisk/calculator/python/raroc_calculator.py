"""
QLRisk - RAROC Calculator
========================================

Python implementation of Risk-Adjusted Return on Capital calculation.

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
    BaseCalculator, CalculatorType, ImplementationType
)


@dataclass
class RAROCInput:
    """Input data for RAROC calculation."""
    # Revenue components
    revenue: float  # Total revenue from the transaction
    fee_income: float = 0.0  # Fee income
    spread_income: float = 0.0  # Spread/interest income
    trading_income: float = 0.0  # Trading P&L
    
    # Cost components
    operating_cost: float = 0.0  # Operating expenses
    funding_cost: float = 0.0  # Cost of funding
    hedging_cost: float = 0.0  # Cost of hedging
    
    # Risk components
    expected_loss: float = 0.0  # Expected credit loss
    economic_capital: float = 0.0  # Economic capital required
    regulatory_capital: float = 0.0  # Regulatory capital (if different)
    
    # Optional: detailed breakdown
    cva: float = 0.0  # Credit Valuation Adjustment
    fva: float = 0.0  # Funding Valuation Adjustment
    kva: float = 0.0  # Capital Valuation Adjustment
    
    # Tax rate
    tax_rate: float = 0.25
    
    # Hurdle rate for comparison
    hurdle_rate: Optional[float] = None


@dataclass
class RAROCResult:
    """Result of RAROC calculation."""
    raroc: float  # Risk-Adjusted Return on Capital
    raroc_pct: float  # As percentage
    economic_profit: float  # EVA
    risk_adjusted_revenue: float
    net_income: float
    exceeds_hurdle: Optional[bool]
    components: Dict[str, float]


class RAROCCalculator(BaseCalculator[RAROCResult]):
    """
    Risk-Adjusted Return on Capital (RAROC) Calculator.
    
    RAROC measures profitability relative to risk taken.
    
    RAROC = (Revenue - Costs - Expected Loss) / Economic Capital
    
    Or with XVAs:
    RAROC = (Revenue - Costs - EL - CVA - FVA - KVA) / EC
    
    Economic Profit (EVA) = RAROC - Hurdle Rate
    
    This metric helps:
    - Price transactions appropriately
    - Compare profitability across different risk levels
    - Make go/no-go decisions on trades
    """
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        """
        Initialize RAROC calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - hurdle_rate: Minimum acceptable return (default 0.15)
                - include_xva: Whether to include XVA adjustments
                - use_regulatory_capital: Use regulatory instead of EC
        """
        config = config or {}
        name = name or self.__class__.__name__
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._hurdle_rate = config.get("hurdle_rate", 0.15)
        self._include_xva = config.get("include_xva", True)
        self._use_regulatory_capital = config.get("use_regulatory_capital", False)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.RAROC
    
    def _calculate_impl(self, data: Any) -> RAROCResult:
        """
        Calculate RAROC.
        
        Args:
            data: RAROCInput or dictionary
            
        Returns:
            RAROCResult with RAROC and components
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, RAROCInput)
            data = RAROCInput(**filtered_data)
        
        # Total revenue
        total_revenue = data.revenue + data.fee_income + data.spread_income + data.trading_income
        
        # Total costs
        total_costs = data.operating_cost + data.funding_cost + data.hedging_cost
        
        # Risk adjustments
        risk_adjustments = data.expected_loss
        
        if self._include_xva:
            risk_adjustments += data.cva + data.fva + data.kva
        
        # Risk-adjusted revenue
        risk_adjusted_revenue = total_revenue - risk_adjustments
        
        # Pre-tax income
        pre_tax_income = risk_adjusted_revenue - total_costs
        
        # After-tax income
        net_income = pre_tax_income * (1 - data.tax_rate)
        
        # Capital base
        if self._use_regulatory_capital and data.regulatory_capital > 0:
            capital = data.regulatory_capital
        else:
            capital = data.economic_capital
        
        # RAROC
        if capital > 0:
            raroc = net_income / capital
        else:
            raroc = float('inf') if net_income > 0 else 0.0
        
        # Check against hurdle rate
        hurdle = data.hurdle_rate if data.hurdle_rate is not None else self._hurdle_rate
        exceeds_hurdle = raroc >= hurdle if hurdle is not None else None
        
        # Economic profit (EVA)
        economic_profit = net_income - (hurdle * capital) if hurdle else net_income
        
        return RAROCResult(
            raroc=raroc,
            raroc_pct=raroc * 100,
            economic_profit=economic_profit,
            risk_adjusted_revenue=risk_adjusted_revenue,
            net_income=net_income,
            exceeds_hurdle=exceeds_hurdle,
            components={
                "total_revenue": total_revenue,
                "total_costs": total_costs,
                "risk_adjustments": risk_adjustments,
                "pre_tax_income": pre_tax_income,
                "capital_used": capital,
                "hurdle_rate": hurdle,
                "tax_rate": data.tax_rate
            }
        )
    
    def calculate_marginal_raroc(self, base_portfolio: RAROCInput,
                                  incremental: RAROCInput) -> Dict[str, Any]:
        """
        Calculate marginal RAROC for an incremental trade.
        
        Marginal RAROC = ΔProfit / ΔCapital
        
        Args:
            base_portfolio: Current portfolio
            incremental: Incremental trade
            
        Returns:
            Dictionary with marginal RAROC analysis
        """
        # Base portfolio RAROC
        base_result = self._calculate_impl(base_portfolio)
        
        # Combined portfolio
        combined = RAROCInput(
            revenue=base_portfolio.revenue + incremental.revenue,
            fee_income=base_portfolio.fee_income + incremental.fee_income,
            spread_income=base_portfolio.spread_income + incremental.spread_income,
            trading_income=base_portfolio.trading_income + incremental.trading_income,
            operating_cost=base_portfolio.operating_cost + incremental.operating_cost,
            funding_cost=base_portfolio.funding_cost + incremental.funding_cost,
            hedging_cost=base_portfolio.hedging_cost + incremental.hedging_cost,
            expected_loss=base_portfolio.expected_loss + incremental.expected_loss,
            economic_capital=base_portfolio.economic_capital + incremental.economic_capital,
            cva=base_portfolio.cva + incremental.cva,
            fva=base_portfolio.fva + incremental.fva,
            kva=base_portfolio.kva + incremental.kva,
            tax_rate=base_portfolio.tax_rate
        )
        
        combined_result = self._calculate_impl(combined)
        
        # Incremental only
        incremental_result = self._calculate_impl(incremental)
        
        # Marginal contribution
        delta_profit = combined_result.net_income - base_result.net_income
        delta_capital = incremental.economic_capital
        
        marginal_raroc = delta_profit / delta_capital if delta_capital > 0 else 0
        
        return {
            "marginal_raroc": marginal_raroc,
            "marginal_raroc_pct": marginal_raroc * 100,
            "standalone_raroc": incremental_result.raroc,
            "portfolio_raroc_before": base_result.raroc,
            "portfolio_raroc_after": combined_result.raroc,
            "delta_profit": delta_profit,
            "delta_capital": delta_capital,
            "accretive": marginal_raroc > base_result.raroc
        }
    
    def calculate_breakeven_spread(self, data: RAROCInput,
                                    target_raroc: Optional[float] = None) -> float:
        """
        Calculate break-even spread to achieve target RAROC.
        
        Solves for spread such that RAROC = target
        
        Args:
            data: Input data (excluding spread income)
            target_raroc: Target RAROC (default: hurdle rate)
            
        Returns:
            Required spread income
        """
        target = target_raroc if target_raroc is not None else self._hurdle_rate
        capital = data.economic_capital
        
        # Required net income
        required_net_income = target * capital
        
        # Required pre-tax income
        required_pre_tax = required_net_income / (1 - data.tax_rate)
        
        # Current income without spread
        current_revenue = data.revenue + data.fee_income + data.trading_income
        total_costs = data.operating_cost + data.funding_cost + data.hedging_cost
        risk_adj = data.expected_loss
        if self._include_xva:
            risk_adj += data.cva + data.fva + data.kva
        
        current_pre_tax = current_revenue - risk_adj - total_costs
        
        # Required additional spread
        required_spread = required_pre_tax - current_pre_tax
        
        return max(0, required_spread)
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "hurdle_rate": self._hurdle_rate,
            "include_xva": self._include_xva,
            "use_regulatory_capital": self._use_regulatory_capital
        })
        return base_details
