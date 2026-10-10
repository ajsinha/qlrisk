# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Current Exposure (CE) Calculator.

Calculates current (replacement cost) exposure using QuantLib pricing engines.

CE = max(0, MTM - Collateral)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import BaseCalculator, CalculationResult, CalculatorType


class ExposureType(Enum):
    """Type of exposure calculation."""
    GROSS = "gross"
    NET = "net"
    COLLATERALIZED = "collateralized"


@dataclass
class QLCEInput:
    """Input parameters for QuantLib Current Exposure calculation."""
    mark_to_market: float
    collateral_value: float = 0.0
    collateral_haircut: float = 0.0
    threshold: float = 0.0  # Collateral posting threshold
    minimum_transfer_amount: float = 0.0  # MTA
    independent_amount: float = 0.0  # IA
    netting_set_id: Optional[str] = None
    trade_id: Optional[str] = None


@dataclass
class QLCEResult:
    """Result of QuantLib Current Exposure calculation."""
    gross_ce: float
    net_ce: float
    collateralized_ce: float
    exposure_type: str
    collateral_adjustment: float
    netting_benefit: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibCECalculator(BaseCalculator):
    """
    QuantLib-based Current Exposure Calculator.
    
    Uses QuantLib for derivative pricing to determine mark-to-market values.
    """
    
    def __init__(self, name: str = "QuantLibCECalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.CURRENT_EXPOSURE
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibCECalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLCEInput) -> CalculationResult:
        """
        Calculate Current Exposure.
        
        Args:
            data: QLCEInput containing MTM and collateral parameters
            
        Returns:
            CalculationResult containing QLCEResult
        """
        self._validate_input(data)
        
        # Gross CE (no collateral, no netting)
        gross_ce = max(0.0, data.mark_to_market)
        
        # Calculate effective collateral
        effective_collateral = self._calculate_effective_collateral(data)
        
        # Net CE (after collateral)
        collateral_adjustment = min(effective_collateral, gross_ce)
        collateralized_ce = max(0.0, gross_ce - effective_collateral)
        
        # Net CE is same as collateralized CE for single trade
        net_ce = collateralized_ce
        
        # Determine exposure type
        if effective_collateral >= gross_ce:
            exposure_type = ExposureType.COLLATERALIZED
        elif effective_collateral > 0:
            exposure_type = ExposureType.NET
        else:
            exposure_type = ExposureType.GROSS
        
        result = QLCEResult(
            gross_ce=gross_ce,
            net_ce=net_ce,
            collateralized_ce=collateralized_ce,
            exposure_type=exposure_type.value,
            collateral_adjustment=collateral_adjustment,
            components={
                "mark_to_market": data.mark_to_market,
                "collateral_value": data.collateral_value,
                "effective_collateral": effective_collateral,
                "threshold": data.threshold,
                "mta": data.minimum_transfer_amount,
                "independent_amount": data.independent_amount,
            }
        )
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A",
                "netting_set_id": data.netting_set_id,
                "trade_id": data.trade_id,
            }
        )
    
    def _validate_input(self, data: QLCEInput) -> None:
        """Validate input parameters."""
        if data.collateral_value < 0:
            raise ValueError("Collateral value must be non-negative")
        if not 0 <= data.collateral_haircut <= 1:
            raise ValueError("Collateral haircut must be between 0 and 1")
        if data.threshold < 0:
            raise ValueError("Threshold must be non-negative")
        if data.minimum_transfer_amount < 0:
            raise ValueError("MTA must be non-negative")
    
    def _calculate_effective_collateral(self, data: QLCEInput) -> float:
        """
        Calculate effective collateral after adjustments.
        
        Effective Collateral = max(0, Collateral × (1 - Haircut) + IA - Threshold)
        """
        # Apply haircut
        collateral_after_haircut = data.collateral_value * (1 - data.collateral_haircut)
        
        # Add independent amount
        collateral_with_ia = collateral_after_haircut + data.independent_amount
        
        # Subtract threshold (uncollateralized portion)
        effective = collateral_with_ia - data.threshold
        
        # Cannot be negative
        return max(0.0, effective)
    
    def calculate_netting_set_ce(self, trades: List[QLCEInput]) -> Dict[str, Any]:
        """
        Calculate Current Exposure for a netting set.
        
        Under netting, positive and negative MTM values offset.
        
        Args:
            trades: List of trades in the netting set
            
        Returns:
            Netting set CE result
        """
        if not trades:
            return {
                "gross_ce": 0.0,
                "net_ce": 0.0,
                "netting_benefit": 0.0,
            }
        
        # Calculate gross CE (sum of positive MTMs)
        gross_ce = sum(max(0.0, t.mark_to_market) for t in trades)
        
        # Calculate net MTM (sum of all MTMs, can offset)
        net_mtm = sum(t.mark_to_market for t in trades)
        net_ce_before_collateral = max(0.0, net_mtm)
        
        # Aggregate collateral (typically pooled in netting set)
        total_collateral = sum(t.collateral_value for t in trades)
        avg_haircut = sum(t.collateral_haircut for t in trades) / len(trades) if trades else 0
        
        # Create aggregated collateral parameters
        agg_threshold = min(t.threshold for t in trades) if trades else 0
        agg_ia = sum(t.independent_amount for t in trades)
        
        effective_collateral = max(
            0.0,
            total_collateral * (1 - avg_haircut) + agg_ia - agg_threshold
        )
        
        # Net CE after collateral
        net_ce = max(0.0, net_ce_before_collateral - effective_collateral)
        
        # Netting benefit
        netting_benefit_mtm = gross_ce - net_ce_before_collateral
        total_netting_benefit = gross_ce - net_ce
        
        # Netting ratio
        netting_ratio = 1 - (net_ce / gross_ce) if gross_ce > 0 else 0
        
        return {
            "gross_ce": gross_ce,
            "net_mtm": net_mtm,
            "net_ce_before_collateral": net_ce_before_collateral,
            "net_ce": net_ce,
            "netting_benefit_mtm": netting_benefit_mtm,
            "total_netting_benefit": total_netting_benefit,
            "netting_ratio": netting_ratio,
            "total_collateral": total_collateral,
            "effective_collateral": effective_collateral,
            "num_trades": len(trades),
        }
    
    def calculate_portfolio_ce(self, 
                                trades: List[QLCEInput],
                                netting_sets: Optional[Dict[str, List[int]]] = None) -> Dict[str, Any]:
        """
        Calculate portfolio Current Exposure with optional netting sets.
        
        Args:
            trades: All trades in portfolio
            netting_sets: Mapping of netting set ID to trade indices
            
        Returns:
            Portfolio CE results
        """
        if not trades:
            return {"portfolio_ce": 0.0}
        
        if netting_sets is None:
            # No netting - calculate each trade individually
            total_gross = 0.0
            total_net = 0.0
            
            for trade in trades:
                result = self.calculate(trade)
                total_gross += result.result.gross_ce
                total_net += result.result.collateralized_ce
            
            return {
                "portfolio_gross_ce": total_gross,
                "portfolio_net_ce": total_net,
                "netting_benefit": 0.0,
            }
        
        # Calculate with netting sets
        total_gross = 0.0
        total_net = 0.0
        netting_set_results = {}
        
        for ns_id, trade_indices in netting_sets.items():
            ns_trades = [trades[i] for i in trade_indices]
            ns_result = self.calculate_netting_set_ce(ns_trades)
            
            total_gross += ns_result["gross_ce"]
            total_net += ns_result["net_ce"]
            netting_set_results[ns_id] = ns_result
        
        # Handle trades not in any netting set
        all_netted_indices = set()
        for indices in netting_sets.values():
            all_netted_indices.update(indices)
        
        for i, trade in enumerate(trades):
            if i not in all_netted_indices:
                result = self.calculate(trade)
                total_gross += result.result.gross_ce
                total_net += result.result.collateralized_ce
        
        portfolio_netting_benefit = 1 - (total_net / total_gross) if total_gross > 0 else 0
        
        return {
            "portfolio_gross_ce": total_gross,
            "portfolio_net_ce": total_net,
            "portfolio_netting_benefit": portfolio_netting_benefit,
            "netting_sets": netting_set_results,
        }
    
    def calculate_marginal_ce(self, 
                               existing_trades: List[QLCEInput],
                               new_trade: QLCEInput,
                               netting_set_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate marginal CE contribution of a new trade.
        
        Args:
            existing_trades: Current portfolio
            new_trade: New trade to add
            netting_set_id: If provided, new trade joins this netting set
            
        Returns:
            Marginal CE analysis
        """
        # Existing CE
        if netting_set_id and existing_trades:
            existing_result = self.calculate_netting_set_ce(existing_trades)
            existing_ce = existing_result["net_ce"]
        else:
            existing_ce = sum(max(0, t.mark_to_market) for t in existing_trades)
        
        # New trade standalone
        standalone_result = self.calculate(new_trade)
        standalone_ce = standalone_result.result.collateralized_ce
        
        # Combined CE
        all_trades = existing_trades + [new_trade]
        if netting_set_id:
            combined_result = self.calculate_netting_set_ce(all_trades)
            combined_ce = combined_result["net_ce"]
        else:
            combined_ce = sum(max(0, t.mark_to_market) for t in all_trades)
        
        # Marginal CE
        marginal_ce = combined_ce - existing_ce
        
        # Netting benefit
        netting_benefit = standalone_ce - marginal_ce
        
        return {
            "marginal_ce": marginal_ce,
            "standalone_ce": standalone_ce,
            "netting_benefit": netting_benefit,
            "existing_ce": existing_ce,
            "combined_ce": combined_ce,
            "mtm_contribution": new_trade.mark_to_market,
        }
    
    def price_derivative_mtm(self, 
                              product_type: str,
                              params: Dict[str, Any]) -> float:
        """
        Price a derivative using QuantLib to get MTM.
        
        This is a simplified implementation for common product types.
        
        Args:
            product_type: Type of derivative (irs, fx_forward, etc.)
            params: Product-specific parameters
            
        Returns:
            Mark-to-market value
        """
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today
        
        if product_type == "irs":
            return self._price_irs_ql(params)
        elif product_type == "fx_forward":
            return self._price_fx_forward_ql(params)
        else:
            # Return provided MTM if product not supported
            return params.get("mtm", 0.0)
    
    def _price_irs_ql(self, params: Dict[str, Any]) -> float:
        """Price an IRS using QuantLib."""
        today = ql.Date.todaysDate()
        calendar = ql.TARGET()
        day_counter = ql.Actual365Fixed()
        
        # Extract parameters
        notional = params.get("notional", 1000000)
        fixed_rate = params.get("fixed_rate", 0.02)
        market_rate = params.get("market_rate", 0.025)
        maturity_years = params.get("maturity_years", 5)
        pay_fixed = params.get("pay_fixed", True)
        
        # Create yield curve
        rate_handle = ql.QuoteHandle(ql.SimpleQuote(market_rate))
        curve = ql.FlatForward(today, rate_handle, day_counter)
        curve_handle = ql.YieldTermStructureHandle(curve)
        
        # Create swap schedule
        start_date = today
        end_date = calendar.advance(today, ql.Period(maturity_years, ql.Years))
        
        fixed_schedule = ql.Schedule(
            start_date, end_date,
            ql.Period(ql.Annual),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        float_schedule = ql.Schedule(
            start_date, end_date,
            ql.Period(ql.Semiannual),
            calendar,
            ql.ModifiedFollowing,
            ql.ModifiedFollowing,
            ql.DateGeneration.Forward,
            False
        )
        
        # Create floating rate index
        float_index = ql.Euribor6M(curve_handle)
        
        # Create swap
        swap_type = ql.VanillaSwap.Payer if pay_fixed else ql.VanillaSwap.Receiver
        
        swap = ql.VanillaSwap(
            swap_type,
            notional,
            fixed_schedule,
            fixed_rate,
            day_counter,
            float_schedule,
            float_index,
            0.0,  # spread
            day_counter
        )
        
        # Price with discounting engine
        engine = ql.DiscountingSwapEngine(curve_handle)
        swap.setPricingEngine(engine)
        
        return swap.NPV()
    
    def _price_fx_forward_ql(self, params: Dict[str, Any]) -> float:
        """Price an FX forward using QuantLib."""
        today = ql.Date.todaysDate()
        day_counter = ql.Actual365Fixed()
        
        # Extract parameters
        notional = params.get("notional", 1000000)
        forward_rate = params.get("forward_rate", 1.10)
        spot_rate = params.get("spot_rate", 1.08)
        maturity_years = params.get("maturity_years", 1)
        domestic_rate = params.get("domestic_rate", 0.02)
        foreign_rate = params.get("foreign_rate", 0.01)
        
        # Calculate fair forward
        fair_forward = spot_rate * (1 + domestic_rate * maturity_years) / (1 + foreign_rate * maturity_years)
        
        # MTM = Notional × (Forward - Fair Forward) × DF
        df = 1 / (1 + domestic_rate * maturity_years)
        mtm = notional * (forward_rate - fair_forward) * df
        
        return mtm
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "formula": "CE = max(0, MTM - Collateral)",
            "supports_netting": True,
            "supports_pricing": True,
            "quantlib_available": QUANTLIB_AVAILABLE,
        }
