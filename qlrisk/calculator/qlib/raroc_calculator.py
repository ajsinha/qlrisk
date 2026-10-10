# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Risk-Adjusted Return on Capital (RAROC) Calculator.

Calculates RAROC using comprehensive revenue and risk adjustments.

RAROC = (Revenue - Costs - EL - XVAs) / Economic Capital
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import math

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import BaseCalculator, CalculationResult, CalculatorType


@dataclass
class QLRAROCInput:
    """Input parameters for QuantLib RAROC calculation."""
    # Revenue components
    interest_income: float = 0.0
    fee_income: float = 0.0
    trading_income: float = 0.0
    other_income: float = 0.0
    
    # Cost components
    funding_cost: float = 0.0
    operating_cost: float = 0.0
    
    # Risk adjustments
    expected_loss: float = 0.0
    cva: float = 0.0
    dva: float = 0.0
    fva: float = 0.0  # Funding Valuation Adjustment
    kva: float = 0.0  # Capital Valuation Adjustment
    colva: float = 0.0  # Collateral Valuation Adjustment
    mva: float = 0.0  # Margin Valuation Adjustment
    
    # Capital
    economic_capital: float = 0.0
    regulatory_capital: float = 0.0
    
    # Other parameters
    tax_rate: float = 0.25
    hurdle_rate: float = 0.15  # Minimum required return
    
    # Optional exposure info for detailed calculation
    notional: float = 0.0
    maturity_years: float = 1.0


@dataclass
class QLRAROCResult:
    """Result of QuantLib RAROC calculation."""
    raroc: float
    raroc_pct: float
    economic_profit: float  # EVA
    exceeds_hurdle: bool
    net_income: float
    total_revenue: float
    total_costs: float
    total_xva: float
    return_on_regulatory_capital: float = 0.0
    break_even_spread: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibRAROCCalculator(BaseCalculator):
    """
    QuantLib-based RAROC Calculator.
    
    Comprehensive risk-adjusted performance measurement including
    all XVA adjustments.
    """
    
    def __init__(self, name: str = "QuantLibRAROCCalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.RAROC
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibRAROCCalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLRAROCInput) -> CalculationResult:
        """
        Calculate RAROC.
        
        Args:
            data: QLRAROCInput containing revenue and risk parameters
            
        Returns:
            CalculationResult containing QLRAROCResult
        """
        self._validate_input(data)
        
        # Total revenue
        total_revenue = (
            data.interest_income +
            data.fee_income +
            data.trading_income +
            data.other_income
        )
        
        # Total costs
        total_costs = data.funding_cost + data.operating_cost
        
        # Total XVA (net impact)
        # CVA is a cost, DVA is a benefit
        total_xva = data.cva - data.dva + data.fva + data.kva + data.colva + data.mva
        
        # Net income before tax
        net_income_before_tax = total_revenue - total_costs - data.expected_loss - total_xva
        
        # Net income after tax
        net_income = net_income_before_tax * (1 - data.tax_rate)
        
        # RAROC
        if data.economic_capital > 0:
            raroc = net_income / data.economic_capital
        else:
            raroc = 0.0
        
        raroc_pct = raroc * 100
        
        # Economic Profit (EVA)
        economic_profit = net_income - (data.hurdle_rate * data.economic_capital)
        
        # Exceeds hurdle rate?
        exceeds_hurdle = raroc >= data.hurdle_rate
        
        # Return on Regulatory Capital
        if data.regulatory_capital > 0:
            rorc = net_income / data.regulatory_capital
        else:
            rorc = 0.0
        
        # Break-even spread
        break_even_spread = self._calculate_break_even_spread(data)
        
        result = QLRAROCResult(
            raroc=raroc,
            raroc_pct=raroc_pct,
            economic_profit=economic_profit,
            exceeds_hurdle=exceeds_hurdle,
            net_income=net_income,
            total_revenue=total_revenue,
            total_costs=total_costs,
            total_xva=total_xva,
            return_on_regulatory_capital=rorc,
            break_even_spread=break_even_spread,
            components={
                "interest_income": data.interest_income,
                "fee_income": data.fee_income,
                "trading_income": data.trading_income,
                "funding_cost": data.funding_cost,
                "operating_cost": data.operating_cost,
                "expected_loss": data.expected_loss,
                "cva": data.cva,
                "dva": data.dva,
                "fva": data.fva,
                "kva": data.kva,
                "colva": data.colva,
                "mva": data.mva,
                "economic_capital": data.economic_capital,
                "regulatory_capital": data.regulatory_capital,
                "tax_rate": data.tax_rate,
                "hurdle_rate": data.hurdle_rate,
            }
        )
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A",
            }
        )
    
    def _validate_input(self, data: QLRAROCInput) -> None:
        """Validate input parameters."""
        if data.economic_capital < 0:
            raise ValueError("Economic capital cannot be negative")
        if not 0 <= data.tax_rate <= 1:
            raise ValueError("Tax rate must be between 0 and 1")
        if data.hurdle_rate < 0:
            raise ValueError("Hurdle rate must be non-negative")
    
    def _calculate_break_even_spread(self, data: QLRAROCInput) -> float:
        """
        Calculate break-even spread required to achieve hurdle rate.
        
        Break-even spread = (Hurdle × EC + Costs + EL + XVA) / (Notional × Maturity)
        """
        if data.notional <= 0 or data.maturity_years <= 0:
            return 0.0
        
        # Required income to meet hurdle
        required_income = data.hurdle_rate * data.economic_capital / (1 - data.tax_rate)
        
        # Total costs to cover
        total_to_cover = (
            required_income +
            data.funding_cost +
            data.operating_cost +
            data.expected_loss +
            data.cva - data.dva + data.fva + data.kva + data.colva + data.mva
        )
        
        # Break-even spread (annualized)
        break_even = total_to_cover / (data.notional * data.maturity_years)
        
        # Convert to basis points
        return break_even * 10000
    
    def calculate_marginal_raroc(self, 
                                  portfolio: QLRAROCInput,
                                  new_trade: QLRAROCInput) -> Dict[str, Any]:
        """
        Calculate marginal RAROC for a new trade.
        
        Args:
            portfolio: Existing portfolio
            new_trade: New trade to add
            
        Returns:
            Marginal RAROC analysis
        """
        # Existing portfolio RAROC
        existing_result = self.calculate(portfolio)
        
        # Combined portfolio
        combined = QLRAROCInput(
            interest_income=portfolio.interest_income + new_trade.interest_income,
            fee_income=portfolio.fee_income + new_trade.fee_income,
            trading_income=portfolio.trading_income + new_trade.trading_income,
            other_income=portfolio.other_income + new_trade.other_income,
            funding_cost=portfolio.funding_cost + new_trade.funding_cost,
            operating_cost=portfolio.operating_cost + new_trade.operating_cost,
            expected_loss=portfolio.expected_loss + new_trade.expected_loss,
            cva=portfolio.cva + new_trade.cva,
            dva=portfolio.dva + new_trade.dva,
            fva=portfolio.fva + new_trade.fva,
            kva=portfolio.kva + new_trade.kva,
            colva=portfolio.colva + new_trade.colva,
            mva=portfolio.mva + new_trade.mva,
            economic_capital=portfolio.economic_capital + new_trade.economic_capital,
            regulatory_capital=portfolio.regulatory_capital + new_trade.regulatory_capital,
            tax_rate=portfolio.tax_rate,
            hurdle_rate=portfolio.hurdle_rate,
        )
        
        combined_result = self.calculate(combined)
        
        # Standalone trade RAROC
        standalone_result = self.calculate(new_trade)
        
        # Marginal RAROC
        # Marginal EC = Combined EC - Existing EC
        marginal_ec = combined.economic_capital - portfolio.economic_capital
        
        # Marginal income
        marginal_income = combined_result.result.net_income - existing_result.result.net_income
        
        if marginal_ec > 0:
            marginal_raroc = marginal_income / marginal_ec
        else:
            marginal_raroc = 0.0
        
        return {
            "marginal_raroc": marginal_raroc,
            "marginal_raroc_pct": marginal_raroc * 100,
            "standalone_raroc": standalone_result.result.raroc,
            "standalone_raroc_pct": standalone_result.result.raroc_pct,
            "existing_portfolio_raroc": existing_result.result.raroc,
            "combined_portfolio_raroc": combined_result.result.raroc,
            "marginal_ec": marginal_ec,
            "marginal_income": marginal_income,
            "meets_hurdle": marginal_raroc >= portfolio.hurdle_rate,
        }
    
    def calculate_optimal_pricing(self, 
                                   data: QLRAROCInput,
                                   target_raroc: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate optimal pricing to achieve target RAROC.
        
        Args:
            data: Current pricing and risk parameters
            target_raroc: Target RAROC (defaults to hurdle rate)
            
        Returns:
            Optimal pricing analysis
        """
        target = target_raroc if target_raroc is not None else data.hurdle_rate
        
        if data.notional <= 0 or data.maturity_years <= 0:
            return {"error": "Notional and maturity required for pricing"}
        
        # Current RAROC
        current_result = self.calculate(data)
        current_raroc = current_result.result.raroc
        
        # Required income to achieve target
        required_income = target * data.economic_capital
        
        # After tax, required gross income
        required_gross = required_income / (1 - data.tax_rate)
        
        # Required spread
        total_costs = (
            data.funding_cost +
            data.operating_cost +
            data.expected_loss +
            data.cva - data.dva + data.fva + data.kva + data.colva + data.mva
        )
        
        required_revenue = required_gross + total_costs
        required_spread = required_revenue / (data.notional * data.maturity_years)
        required_spread_bps = required_spread * 10000
        
        # Current spread
        current_revenue = data.interest_income + data.fee_income + data.trading_income
        current_spread = current_revenue / (data.notional * data.maturity_years) if data.notional > 0 else 0
        current_spread_bps = current_spread * 10000
        
        # Spread adjustment needed
        spread_adjustment = required_spread_bps - current_spread_bps
        
        return {
            "current_raroc": current_raroc,
            "current_raroc_pct": current_raroc * 100,
            "target_raroc": target,
            "target_raroc_pct": target * 100,
            "current_spread_bps": current_spread_bps,
            "required_spread_bps": required_spread_bps,
            "spread_adjustment_bps": spread_adjustment,
            "currently_meets_target": current_raroc >= target,
        }
    
    def calculate_raroc_sensitivity(self, 
                                     data: QLRAROCInput,
                                     parameter: str,
                                     shock_pct: float = 0.10) -> Dict[str, Any]:
        """
        Calculate RAROC sensitivity to parameter changes.
        
        Args:
            data: Base case parameters
            parameter: Parameter to shock
            shock_pct: Shock size as percentage
            
        Returns:
            Sensitivity analysis
        """
        base_result = self.calculate(data)
        base_raroc = base_result.result.raroc
        
        # Apply shock
        shocked_data = QLRAROCInput(
            interest_income=data.interest_income,
            fee_income=data.fee_income,
            trading_income=data.trading_income,
            other_income=data.other_income,
            funding_cost=data.funding_cost,
            operating_cost=data.operating_cost,
            expected_loss=data.expected_loss,
            cva=data.cva,
            dva=data.dva,
            fva=data.fva,
            kva=data.kva,
            colva=data.colva,
            mva=data.mva,
            economic_capital=data.economic_capital,
            regulatory_capital=data.regulatory_capital,
            tax_rate=data.tax_rate,
            hurdle_rate=data.hurdle_rate,
            notional=data.notional,
            maturity_years=data.maturity_years,
        )
        
        # Apply shock to specified parameter
        if hasattr(shocked_data, parameter):
            current_value = getattr(shocked_data, parameter)
            shocked_value = current_value * (1 + shock_pct)
            setattr(shocked_data, parameter, shocked_value)
        else:
            return {"error": f"Unknown parameter: {parameter}"}
        
        shocked_result = self.calculate(shocked_data)
        shocked_raroc = shocked_result.result.raroc
        
        # Sensitivity
        raroc_change = shocked_raroc - base_raroc
        sensitivity = raroc_change / shock_pct if shock_pct != 0 else 0
        
        return {
            "parameter": parameter,
            "shock_pct": shock_pct * 100,
            "base_raroc": base_raroc,
            "shocked_raroc": shocked_raroc,
            "raroc_change": raroc_change,
            "sensitivity": sensitivity,
        }
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "formula": "RAROC = (Revenue - Costs - EL - XVAs) / EC",
            "xva_components": ["CVA", "DVA", "FVA", "KVA", "ColVA", "MVA"],
            "quantlib_available": QUANTLIB_AVAILABLE,
        }
