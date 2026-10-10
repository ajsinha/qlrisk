"""
QLRisk - Product Models v1.2.0
=============================================

Domain models for financial products in QLRisk.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid

from .base import ModelBase


class PaymentFrequency(Enum):
    ANNUAL = 1
    SEMI_ANNUAL = 2
    QUARTERLY = 4
    MONTHLY = 12
    WEEKLY = 52
    DAILY = 365


class OptionType(Enum):
    CALL = "call"
    PUT = "put"


class OptionStyle(Enum):
    EUROPEAN = "european"
    AMERICAN = "american"
    BERMUDAN = "bermudan"


class AssetClass(Enum):
    INTEREST_RATE = "interest_rate"
    FX = "fx"
    CREDIT = "credit"
    EQUITY = "equity"
    COMMODITY = "commodity"
    REPO = "repo"


@dataclass
class Product(ModelBase):
    """Abstract base class for financial products."""
    product_id: str = field(default_factory=lambda: f"PRD-{uuid.uuid4().hex[:8].upper()}")
    product_type: str = ""
    asset_class: str = ""
    notional: float = 0.0
    currency: str = "USD"
    effective_date: date = field(default_factory=date.today)
    maturity_date: date = field(default_factory=date.today)
    counterparty_id: str = ""
    
    def validate(self) -> bool:
        if not self.product_id:
            raise ValueError("product_id is required")
        if self.notional <= 0:
            raise ValueError("notional must be positive")
        return True

    def time_to_maturity(self, from_date: Optional[date] = None) -> float:
        ref_date = from_date or date.today()
        days = (self.maturity_date - ref_date).days
        return max(days / 365.0, 0.0)

    def get_cash_flows(self) -> List[Dict[str, Any]]:
        return []


@dataclass
class InterestRateSwap(Product):
    product_type: str = "IRS"
    asset_class: str = "interest_rate"
    fixed_rate: float = 0.05
    fixed_frequency: PaymentFrequency = PaymentFrequency.SEMI_ANNUAL
    floating_index: str = "SOFR"
    floating_spread: float = 0.0
    is_payer: bool = True


@dataclass
class OvernightIndexSwap(Product):
    product_type: str = "OIS"
    asset_class: str = "interest_rate"
    fixed_rate: float = 0.05
    overnight_index: str = "SOFR"
    is_payer: bool = True


@dataclass
class ForwardRateAgreement(Product):
    product_type: str = "FRA"
    asset_class: str = "interest_rate"
    fra_rate: float = 0.05
    fixing_date: date = field(default_factory=date.today)
    is_payer: bool = True


@dataclass
class InterestRateCap(Product):
    product_type: str = "CAP"
    asset_class: str = "interest_rate"
    strike: float = 0.05
    floating_index: str = "SOFR"
    is_long: bool = True


@dataclass
class InterestRateFloor(Product):
    product_type: str = "FLOOR"
    asset_class: str = "interest_rate"
    strike: float = 0.02
    floating_index: str = "SOFR"
    is_long: bool = True


@dataclass
class Swaption(Product):
    product_type: str = "SWAPTION"
    asset_class: str = "interest_rate"
    strike: float = 0.05
    option_expiry: date = field(default_factory=date.today)
    swap_tenor: float = 5.0
    is_payer: bool = True
    is_long: bool = True


@dataclass
class FXForward(Product):
    product_type: str = "FX_FORWARD"
    asset_class: str = "fx"
    base_currency: str = "EUR"
    quote_currency: str = "USD"
    forward_rate: float = 1.10
    is_buy_base: bool = True


@dataclass
class FXSwap(Product):
    product_type: str = "FX_SWAP"
    asset_class: str = "fx"
    base_currency: str = "EUR"
    quote_currency: str = "USD"
    near_rate: float = 1.10
    far_rate: float = 1.12


@dataclass
class FXOption(Product):
    product_type: str = "FX_OPTION"
    asset_class: str = "fx"
    base_currency: str = "EUR"
    quote_currency: str = "USD"
    strike: float = 1.10
    option_type: OptionType = OptionType.CALL
    is_long: bool = True


@dataclass
class NonDeliverableForward(Product):
    product_type: str = "NDF"
    asset_class: str = "fx"
    base_currency: str = "CNY"
    quote_currency: str = "USD"
    forward_rate: float = 7.20


@dataclass
class CreditDefaultSwap(Product):
    product_type: str = "CDS"
    asset_class: str = "credit"
    reference_entity: str = ""
    spread: float = 0.01
    recovery_rate: float = 0.40
    is_protection_buyer: bool = True


@dataclass
class CDSIndex(Product):
    product_type: str = "CDS_INDEX"
    asset_class: str = "credit"
    index_name: str = "CDX.NA.IG"
    series: int = 40
    spread: float = 0.005
    is_protection_buyer: bool = True


@dataclass
class TotalReturnSwap(Product):
    product_type: str = "TRS"
    asset_class: str = "credit"
    reference_asset: str = ""
    funding_spread: float = 0.01


@dataclass
class EquityOption(Product):
    product_type: str = "EQUITY_OPTION"
    asset_class: str = "equity"
    underlying: str = ""
    strike: float = 100.0
    option_type: OptionType = OptionType.CALL
    is_long: bool = True


@dataclass
class EquitySwap(Product):
    product_type: str = "EQUITY_SWAP"
    asset_class: str = "equity"
    underlying: str = ""
    funding_spread: float = 0.005


@dataclass
class VarianceSwap(Product):
    product_type: str = "VARIANCE_SWAP"
    asset_class: str = "equity"
    underlying: str = ""
    strike_variance: float = 0.04


@dataclass
class CommoditySwap(Product):
    product_type: str = "COMMODITY_SWAP"
    asset_class: str = "commodity"
    commodity: str = "WTI"
    fixed_price: float = 75.0


@dataclass
class CommodityForward(Product):
    product_type: str = "COMMODITY_FORWARD"
    asset_class: str = "commodity"
    commodity: str = "GOLD"
    forward_price: float = 2000.0


@dataclass
class CrossCurrencySwap(Product):
    product_type: str = "XCCY_SWAP"
    asset_class: str = "fx"
    pay_currency: str = "USD"
    receive_currency: str = "EUR"
    pay_rate: float = 0.05
    receive_rate: float = 0.03


@dataclass
class Repo(Product):
    product_type: str = "REPO"
    asset_class: str = "repo"
    collateral_type: str = "TREASURY"
    repo_rate: float = 0.05
    haircut: float = 0.02


@dataclass
class Bond(Product):
    product_type: str = "BOND"
    asset_class: str = "interest_rate"
    coupon_rate: float = 0.05
    coupon_frequency: PaymentFrequency = PaymentFrequency.SEMI_ANNUAL
    face_value: float = 100.0


@dataclass
class FloatingRateNote(Product):
    product_type: str = "FRN"
    asset_class: str = "interest_rate"
    spread: float = 0.01
    floating_index: str = "SOFR"
    face_value: float = 100.0


__all__ = [
    "PaymentFrequency", "OptionType", "OptionStyle", "AssetClass",
    "Product",
    "InterestRateSwap", "OvernightIndexSwap", "ForwardRateAgreement",
    "InterestRateCap", "InterestRateFloor", "Swaption",
    "FXForward", "FXSwap", "FXOption", "NonDeliverableForward",
    "CreditDefaultSwap", "CDSIndex", "TotalReturnSwap",
    "EquityOption", "EquitySwap", "VarianceSwap",
    "CommoditySwap", "CommodityForward",
    "CrossCurrencySwap", "Repo",
    "Bond", "FloatingRateNote",
]
