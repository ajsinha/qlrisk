"""
Model Factory - Factory for creating model instances

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Type, Optional
from datetime import date

from .base import ModelBase
from .trade import Trade, TradeType, TradeStatus, TradeDirection
from .curve import YieldCurve, CreditCurve, VolatilitySurface, CurveType
from .market_data import MarketData, MarketDataSnapshot
from .counterparty import Counterparty, NettingSet, CollateralAgreement
from .products import (
    Product,
    InterestRateSwap,
    ForwardRateAgreement,
    FXForward,
    FXOption,
    CreditDefaultSwap,
    EquityOption
)
from ..core.exceptions import ModelError
from ..core.date_utils import DateUtils


class ModelFactory:
    """
    Factory class for creating model instances.
    Provides a centralized way to instantiate domain models.
    """
    
    # Registry of product types to classes
    _product_registry: Dict[str, Type[Product]] = {
        "IRS": InterestRateSwap,
        "INTEREST_RATE_SWAP": InterestRateSwap,
        "FRA": ForwardRateAgreement,
        "FORWARD_RATE_AGREEMENT": ForwardRateAgreement,
        "FX_FWD": FXForward,
        "FX_FORWARD": FXForward,
        "FX_OPT": FXOption,
        "FX_OPTION": FXOption,
        "CDS": CreditDefaultSwap,
        "CREDIT_DEFAULT_SWAP": CreditDefaultSwap,
        "EQ_OPT": EquityOption,
        "EQUITY_OPTION": EquityOption,
    }
    
    # Registry of curve types to classes
    _curve_registry: Dict[str, Type] = {
        "YIELD": YieldCurve,
        "ZERO": YieldCurve,
        "DISCOUNT": YieldCurve,
        "CREDIT": CreditCurve,
        "HAZARD": CreditCurve,
        "VOLATILITY": VolatilitySurface,
    }

    @classmethod
    def create_trade(
        cls,
        trade_type: TradeType,
        counterparty_id: str,
        notional: float,
        currency: str = "USD",
        maturity_date: Optional[date] = None,
        **kwargs
    ) -> Trade:
        """
        Create a trade instance.

        Args:
            trade_type: Type of trade
            counterparty_id: Counterparty identifier
            notional: Notional amount
            currency: Currency code
            maturity_date: Maturity date
            **kwargs: Additional trade attributes

        Returns:
            Trade instance
        """
        if maturity_date is None:
#             from ..core.date_utils import DateUtils  # Removed - self-contained
            maturity_date = DateUtils.add_years(date.today(), 1)
        
        return Trade(
            trade_type=trade_type,
            counterparty_id=counterparty_id,
            notional=notional,
            currency=currency,
            maturity_date=maturity_date,
            **kwargs
        )

    @classmethod
    def create_product(
        cls,
        product_type: str,
        notional: float,
        currency: str = "USD",
        maturity_date: Optional[date] = None,
        **kwargs
    ) -> Product:
        """
        Create a product instance.

        Args:
            product_type: Type of product
            notional: Notional amount
            currency: Currency code
            maturity_date: Maturity date
            **kwargs: Product-specific attributes

        Returns:
            Product instance
        """
        product_type_upper = product_type.upper()
        
        if product_type_upper not in cls._product_registry:
            raise ValueError(
                f"Unknown product type: {product_type}",
                model_type="product"
            )
        
        product_class = cls._product_registry[product_type_upper]
        
        if maturity_date is None:
#             from ..core.date_utils import DateUtils  # Removed - self-contained
            maturity_date = DateUtils.add_years(date.today(), 1)
        
        return product_class(
            notional=notional,
            currency=currency,
            maturity_date=maturity_date,
            **kwargs
        )

    @classmethod
    def create_interest_rate_swap(
        cls,
        notional: float,
        fixed_rate: float,
        maturity_years: int = 5,
        currency: str = "USD",
        pay_fixed: bool = True,
        **kwargs
    ) -> InterestRateSwap:
        """
        Create an Interest Rate Swap.

        Args:
            notional: Notional amount
            fixed_rate: Fixed rate
            maturity_years: Maturity in years
            currency: Currency code
            pay_fixed: True if paying fixed
            **kwargs: Additional attributes

        Returns:
            InterestRateSwap instance
        """
#         from ..core.date_utils import DateUtils  # Removed - self-contained
        
        return InterestRateSwap(
            notional=notional,
            currency=currency,
            fixed_rate=fixed_rate,
            pay_fixed=pay_fixed,
            effective_date=date.today(),
            maturity_date=DateUtils.add_years(date.today(), maturity_years),
            **kwargs
        )

    @classmethod
    def create_fx_forward(
        cls,
        notional_base: float,
        forward_rate: float,
        base_currency: str,
        quote_currency: str,
        maturity_months: int = 3,
        buy_base: bool = True,
        **kwargs
    ) -> FXForward:
        """
        Create an FX Forward.

        Args:
            notional_base: Notional in base currency
            forward_rate: Forward exchange rate
            base_currency: Base currency
            quote_currency: Quote currency
            maturity_months: Maturity in months
            buy_base: True if buying base currency
            **kwargs: Additional attributes

        Returns:
            FXForward instance
        """
#         from ..core.date_utils import DateUtils  # Removed - self-contained
        
        return FXForward(
            notional_base=notional_base,
            notional=notional_base,
            forward_rate=forward_rate,
            base_currency=base_currency,
            quote_currency=quote_currency,
            currency=quote_currency,
            buy_base=buy_base,
            effective_date=date.today(),
            maturity_date=DateUtils.add_months(date.today(), maturity_months),
            **kwargs
        )

    @classmethod
    def create_cds(
        cls,
        notional: float,
        reference_entity: str,
        spread: float,
        maturity_years: int = 5,
        currency: str = "USD",
        protection_buyer: bool = True,
        **kwargs
    ) -> CreditDefaultSwap:
        """
        Create a Credit Default Swap.

        Args:
            notional: Notional amount
            reference_entity: Reference entity
            spread: CDS spread
            maturity_years: Maturity in years
            currency: Currency code
            protection_buyer: True if buying protection
            **kwargs: Additional attributes

        Returns:
            CreditDefaultSwap instance
        """
#         from ..core.date_utils import DateUtils  # Removed - self-contained
        
        return CreditDefaultSwap(
            notional=notional,
            currency=currency,
            reference_entity=reference_entity,
            spread=spread,
            protection_buyer=protection_buyer,
            effective_date=date.today(),
            maturity_date=DateUtils.add_years(date.today(), maturity_years),
            **kwargs
        )

    @classmethod
    def create_yield_curve(
        cls,
        currency: str,
        tenors: list,
        rates: list,
        curve_date: Optional[date] = None,
        **kwargs
    ) -> YieldCurve:
        """
        Create a Yield Curve.

        Args:
            currency: Currency code
            tenors: List of tenors in years
            rates: List of zero rates
            curve_date: Curve date
            **kwargs: Additional attributes

        Returns:
            YieldCurve instance
        """
        return YieldCurve(
            curve_id=f"{currency}_YIELD",
            currency=currency,
            tenors=tenors,
            values=rates,
            curve_date=curve_date or date.today(),
            **kwargs
        )

    @classmethod
    def create_credit_curve(
        cls,
        entity_id: str,
        tenors: list,
        hazard_rates: list,
        recovery_rate: float = 0.4,
        curve_date: Optional[date] = None,
        **kwargs
    ) -> CreditCurve:
        """
        Create a Credit Curve.

        Args:
            entity_id: Entity identifier
            tenors: List of tenors in years
            hazard_rates: List of hazard rates
            recovery_rate: Recovery rate
            curve_date: Curve date
            **kwargs: Additional attributes

        Returns:
            CreditCurve instance
        """
        return CreditCurve(
            curve_id=entity_id,
            tenors=tenors,
            values=hazard_rates,
            recovery_rate=recovery_rate,
            curve_date=curve_date or date.today(),
            **kwargs
        )

    @classmethod
    def create_counterparty(
        cls,
        name: str,
        pd: float = 0.01,
        lgd: float = 0.45,
        **kwargs
    ) -> Counterparty:
        """
        Create a Counterparty.

        Args:
            name: Counterparty name
            pd: Probability of default
            lgd: Loss given default
            **kwargs: Additional attributes

        Returns:
            Counterparty instance
        """
        return Counterparty(
            name=name,
            legal_name=name,
            probability_of_default=pd,
            loss_given_default=lgd,
            **kwargs
        )

    @classmethod
    def create_netting_set(
        cls,
        counterparty_id: str,
        name: str = "",
        has_collateral: bool = False,
        **kwargs
    ) -> NettingSet:
        """
        Create a Netting Set.

        Args:
            counterparty_id: Counterparty identifier
            name: Netting set name
            has_collateral: Whether has collateral agreement
            **kwargs: Additional attributes

        Returns:
            NettingSet instance
        """
        netting_set = NettingSet(
            counterparty_id=counterparty_id,
            name=name or f"NS-{counterparty_id}",
            **kwargs
        )
        
        if has_collateral:
            netting_set.collateral_agreement = CollateralAgreement(
                netting_set_id=netting_set.netting_set_id
            )
        
        return netting_set

    @classmethod
    def create_market_data_snapshot(
        cls,
        snapshot_date: Optional[date] = None
    ) -> MarketDataSnapshot:
        """
        Create an empty Market Data Snapshot.

        Args:
            snapshot_date: Snapshot date

        Returns:
            MarketDataSnapshot instance
        """
        return MarketDataSnapshot(
            snapshot_date=snapshot_date or date.today()
        )

    @classmethod
    def register_product(cls, product_type: str, product_class: Type[Product]):
        """
        Register a custom product type.

        Args:
            product_type: Product type identifier
            product_class: Product class
        """
        cls._product_registry[product_type.upper()] = product_class

    @classmethod
    def get_registered_products(cls) -> list:
        """Get list of registered product types."""
        return list(set(cls._product_registry.keys()))
