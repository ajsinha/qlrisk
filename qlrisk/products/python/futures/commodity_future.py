"""
QLRisk - CommodityFuture v2.0.1
==============================================

Commodity Futures contract implementation with full CCR analytics support.

Commodity futures are standardized exchange-traded contracts obligating the buyer
to purchase (or seller to sell) a specific quantity of a commodity at a predetermined
price on a specified future date.

Supported Commodity Types:
- Energy: Crude Oil (WTI, Brent), Natural Gas, Heating Oil, RBOB Gasoline
- Metals: Gold, Silver, Platinum, Palladium, Copper, Aluminum
- Agriculture: Corn, Wheat, Soybeans, Coffee, Sugar, Cotton, Cocoa
- Livestock: Live Cattle, Lean Hogs, Feeder Cattle

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from datetime import date
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass
import numpy as np

from ...base import curve_value
from ...base import (
    BaseProduct, ProductType, AssetClass, Currency,
    DayCountConvention, PaymentFrequency,
    MarketData, PricingResult, CCRExposureProfile, SACCRExposure,
    SACCRParameters, year_fraction
)


class CommodityType(Enum):
    """Types of commodities for futures contracts."""
    # Energy
    CRUDE_OIL_WTI = "crude_oil_wti"
    CRUDE_OIL_BRENT = "crude_oil_brent"
    NATURAL_GAS = "natural_gas"
    HEATING_OIL = "heating_oil"
    RBOB_GASOLINE = "rbob_gasoline"
    COAL = "coal"
    ELECTRICITY = "electricity"
    
    # Precious Metals
    GOLD = "gold"
    SILVER = "silver"
    PLATINUM = "platinum"
    PALLADIUM = "palladium"
    
    # Base Metals
    COPPER = "copper"
    ALUMINUM = "aluminum"
    ZINC = "zinc"
    NICKEL = "nickel"
    LEAD = "lead"
    TIN = "tin"
    
    # Agriculture - Grains
    CORN = "corn"
    WHEAT = "wheat"
    SOYBEANS = "soybeans"
    SOYBEAN_OIL = "soybean_oil"
    SOYBEAN_MEAL = "soybean_meal"
    OATS = "oats"
    RICE = "rice"
    
    # Agriculture - Softs
    COFFEE = "coffee"
    SUGAR = "sugar"
    COCOA = "cocoa"
    COTTON = "cotton"
    ORANGE_JUICE = "orange_juice"
    LUMBER = "lumber"
    
    # Livestock
    LIVE_CATTLE = "live_cattle"
    LEAN_HOGS = "lean_hogs"
    FEEDER_CATTLE = "feeder_cattle"


class CommoditySubClass(Enum):
    """SA-CCR commodity sub-classes for hedging set determination."""
    ENERGY = "energy"
    PRECIOUS_METALS = "precious_metals"
    BASE_METALS = "base_metals"
    AGRICULTURE = "agriculture"
    LIVESTOCK = "livestock"
    OTHER = "other"


# Supervisory factors by commodity type (SA-CCR)
COMMODITY_SUPERVISORY_FACTORS = {
    # Energy: 40% for electricity, 18% for others
    CommodityType.ELECTRICITY: 0.40,
    CommodityType.CRUDE_OIL_WTI: 0.18,
    CommodityType.CRUDE_OIL_BRENT: 0.18,
    CommodityType.NATURAL_GAS: 0.18,
    CommodityType.HEATING_OIL: 0.18,
    CommodityType.RBOB_GASOLINE: 0.18,
    CommodityType.COAL: 0.18,
    # Metals: 18%
    CommodityType.GOLD: 0.18,
    CommodityType.SILVER: 0.18,
    CommodityType.PLATINUM: 0.18,
    CommodityType.PALLADIUM: 0.18,
    CommodityType.COPPER: 0.18,
    CommodityType.ALUMINUM: 0.18,
    CommodityType.ZINC: 0.18,
    CommodityType.NICKEL: 0.18,
    CommodityType.LEAD: 0.18,
    CommodityType.TIN: 0.18,
    # Agriculture: 18%
    CommodityType.CORN: 0.18,
    CommodityType.WHEAT: 0.18,
    CommodityType.SOYBEANS: 0.18,
    CommodityType.SOYBEAN_OIL: 0.18,
    CommodityType.SOYBEAN_MEAL: 0.18,
    CommodityType.OATS: 0.18,
    CommodityType.RICE: 0.18,
    CommodityType.COFFEE: 0.18,
    CommodityType.SUGAR: 0.18,
    CommodityType.COCOA: 0.18,
    CommodityType.COTTON: 0.18,
    CommodityType.ORANGE_JUICE: 0.18,
    CommodityType.LUMBER: 0.18,
    # Livestock: 18%
    CommodityType.LIVE_CATTLE: 0.18,
    CommodityType.LEAN_HOGS: 0.18,
    CommodityType.FEEDER_CATTLE: 0.18,
}

# Commodity volatilities (annualized)
COMMODITY_VOLATILITIES = {
    CommodityType.CRUDE_OIL_WTI: 0.35,
    CommodityType.CRUDE_OIL_BRENT: 0.35,
    CommodityType.NATURAL_GAS: 0.50,
    CommodityType.HEATING_OIL: 0.35,
    CommodityType.RBOB_GASOLINE: 0.40,
    CommodityType.COAL: 0.30,
    CommodityType.ELECTRICITY: 0.80,
    CommodityType.GOLD: 0.15,
    CommodityType.SILVER: 0.25,
    CommodityType.PLATINUM: 0.25,
    CommodityType.PALLADIUM: 0.30,
    CommodityType.COPPER: 0.25,
    CommodityType.ALUMINUM: 0.20,
    CommodityType.ZINC: 0.25,
    CommodityType.NICKEL: 0.30,
    CommodityType.LEAD: 0.25,
    CommodityType.TIN: 0.25,
    CommodityType.CORN: 0.25,
    CommodityType.WHEAT: 0.30,
    CommodityType.SOYBEANS: 0.25,
    CommodityType.SOYBEAN_OIL: 0.25,
    CommodityType.SOYBEAN_MEAL: 0.25,
    CommodityType.OATS: 0.30,
    CommodityType.RICE: 0.25,
    CommodityType.COFFEE: 0.35,
    CommodityType.SUGAR: 0.30,
    CommodityType.COCOA: 0.30,
    CommodityType.COTTON: 0.30,
    CommodityType.ORANGE_JUICE: 0.35,
    CommodityType.LUMBER: 0.40,
    CommodityType.LIVE_CATTLE: 0.15,
    CommodityType.LEAN_HOGS: 0.25,
    CommodityType.FEEDER_CATTLE: 0.15,
}

# Map commodity type to sub-class
COMMODITY_TO_SUBCLASS = {
    CommodityType.CRUDE_OIL_WTI: CommoditySubClass.ENERGY,
    CommodityType.CRUDE_OIL_BRENT: CommoditySubClass.ENERGY,
    CommodityType.NATURAL_GAS: CommoditySubClass.ENERGY,
    CommodityType.HEATING_OIL: CommoditySubClass.ENERGY,
    CommodityType.RBOB_GASOLINE: CommoditySubClass.ENERGY,
    CommodityType.COAL: CommoditySubClass.ENERGY,
    CommodityType.ELECTRICITY: CommoditySubClass.ENERGY,
    CommodityType.GOLD: CommoditySubClass.PRECIOUS_METALS,
    CommodityType.SILVER: CommoditySubClass.PRECIOUS_METALS,
    CommodityType.PLATINUM: CommoditySubClass.PRECIOUS_METALS,
    CommodityType.PALLADIUM: CommoditySubClass.PRECIOUS_METALS,
    CommodityType.COPPER: CommoditySubClass.BASE_METALS,
    CommodityType.ALUMINUM: CommoditySubClass.BASE_METALS,
    CommodityType.ZINC: CommoditySubClass.BASE_METALS,
    CommodityType.NICKEL: CommoditySubClass.BASE_METALS,
    CommodityType.LEAD: CommoditySubClass.BASE_METALS,
    CommodityType.TIN: CommoditySubClass.BASE_METALS,
    CommodityType.CORN: CommoditySubClass.AGRICULTURE,
    CommodityType.WHEAT: CommoditySubClass.AGRICULTURE,
    CommodityType.SOYBEANS: CommoditySubClass.AGRICULTURE,
    CommodityType.SOYBEAN_OIL: CommoditySubClass.AGRICULTURE,
    CommodityType.SOYBEAN_MEAL: CommoditySubClass.AGRICULTURE,
    CommodityType.OATS: CommoditySubClass.AGRICULTURE,
    CommodityType.RICE: CommoditySubClass.AGRICULTURE,
    CommodityType.COFFEE: CommoditySubClass.AGRICULTURE,
    CommodityType.SUGAR: CommoditySubClass.AGRICULTURE,
    CommodityType.COCOA: CommoditySubClass.AGRICULTURE,
    CommodityType.COTTON: CommoditySubClass.AGRICULTURE,
    CommodityType.ORANGE_JUICE: CommoditySubClass.AGRICULTURE,
    CommodityType.LUMBER: CommoditySubClass.AGRICULTURE,
    CommodityType.LIVE_CATTLE: CommoditySubClass.LIVESTOCK,
    CommodityType.LEAN_HOGS: CommoditySubClass.LIVESTOCK,
    CommodityType.FEEDER_CATTLE: CommoditySubClass.LIVESTOCK,
}


@dataclass
class CommodityFutureTerms:
    """Terms specific to commodity futures contracts."""
    commodity_type: CommodityType = CommodityType.CRUDE_OIL_WTI
    contract_size: float = 1000.0  # Size of one contract (e.g., 1000 barrels for WTI)
    num_contracts: int = 1  # Number of contracts
    futures_price: float = 0.0  # Agreed futures price
    spot_price: Optional[float] = None  # Current spot price
    storage_cost: float = 0.0  # Annual storage cost rate
    convenience_yield: float = 0.0  # Convenience yield rate
    exchange: str = "CME"  # Exchange (CME, ICE, LME, etc.)
    contract_month: str = ""  # Contract month code (e.g., "F24" for Jan 2024)
    settlement_type: str = "physical"  # "physical" or "cash"
    margin_initial: float = 0.0  # Initial margin requirement
    margin_maintenance: float = 0.0  # Maintenance margin
    unit: str = ""  # Unit of measure (barrels, oz, bushels, etc.)


class CommodityFuture(BaseProduct):
    """
    Commodity Futures Contract.
    
    A standardized, exchange-traded contract to buy or sell a specific 
    quantity of a commodity at a predetermined price at a future date.
    
    Key Features:
    - Standardized contract sizes and delivery dates
    - Mark-to-market daily margining
    - Physical or cash settlement
    - Various commodity types (energy, metals, agriculture, livestock)
    
    Pricing (Cost of Carry Model):
        F = S × exp((r + u - y) × T)
        
        where:
        - S = spot price
        - r = risk-free rate
        - u = storage cost
        - y = convenience yield
        - T = time to maturity
    
    CCR Considerations:
    - Futures are typically exchange-cleared with daily margining
    - Low counterparty credit risk due to CCP guarantee
    - SA-CCR: Commodity asset class with 18% SF (40% for electricity)
    
    Example:
        future = CommodityFuture(
            trade_id="COM-FUT-001",
            trade_date=date.today(),
            effective_date=date.today(),
            maturity_date=date(2025, 6, 30),
            notional=1_000_000,
            currency=Currency.USD,
            counterparty_id="CME",
            terms=CommodityFutureTerms(
                commodity_type=CommodityType.CRUDE_OIL_WTI,
                contract_size=1000,  # 1000 barrels
                num_contracts=10,
                futures_price=75.50,
                spot_price=74.00,
                exchange="NYMEX"
            ),
            is_long=True
        )
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        effective_date: date,
        maturity_date: date,
        notional: float,
        currency: Currency,
        counterparty_id: str,
        terms: Optional[CommodityFutureTerms] = None,
        is_long: bool = True,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.COMMODITY_FUTURE,
            asset_class=AssetClass.COMMODITY,
            trade_date=trade_date,
            effective_date=effective_date,
            maturity_date=maturity_date,
            notional=notional,
            currency=currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.terms = terms or CommodityFutureTerms()
        self.is_long = is_long
        
    def get_subclass(self) -> CommoditySubClass:
        """Get the SA-CCR commodity sub-class."""
        return COMMODITY_TO_SUBCLASS.get(
            self.terms.commodity_type, 
            CommoditySubClass.OTHER
        )
    
    def get_supervisory_factor(self) -> float:
        """Get the SA-CCR supervisory factor."""
        return COMMODITY_SUPERVISORY_FACTORS.get(
            self.terms.commodity_type,
            0.18  # Default
        )
    
    def get_volatility(self) -> float:
        """Get the commodity's annualized volatility."""
        return COMMODITY_VOLATILITIES.get(
            self.terms.commodity_type,
            0.25  # Default
        )
    
    def calculate_fair_value(self, market_data: MarketData) -> float:
        """
        Calculate fair value using cost of carry model.
        
        F = S × exp((r + u - y) × T)
        
        Args:
            market_data: Current market data
            
        Returns:
            Fair value futures price
        """
        spot = self.terms.spot_price or self.terms.futures_price
        if spot <= 0:
            return self.terms.futures_price
            
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        if remaining <= 0:
            return spot
            
        # Get risk-free rate
        r = curve_value(market_data.discount_curve, remaining, 0.05)
        
        # Cost of carry
        carry = r + self.terms.storage_cost - self.terms.convenience_yield
        
        # Fair value
        fair_value = spot * np.exp(carry * remaining)
        
        return fair_value
    
    def price(self, market_data: MarketData) -> PricingResult:
        """
        Price the Commodity Future.
        
        NPV = (F_market - F_contract) × contract_size × num_contracts × direction
        
        Args:
            market_data: Current market data
            
        Returns:
            PricingResult with NPV and components
        """
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.currency.value)
        
        remaining = self.get_remaining_maturity(valuation_date)
        
        # Get current market price (use fair value as proxy)
        market_price = self.calculate_fair_value(market_data)
        contract_price = self.terms.futures_price
        
        if contract_price <= 0:
            contract_price = market_price
        
        # Calculate P&L per contract
        price_diff = market_price - contract_price
        
        # Direction
        direction = 1.0 if self.is_long else -1.0
        
        # Total P&L
        total_quantity = self.terms.contract_size * self.terms.num_contracts
        npv = price_diff * total_quantity * direction
        
        # Discount to present value
        discount_curve = market_data.discount_curve
        df = np.exp(-curve_value(discount_curve, remaining, 0.05) * remaining)
        npv *= df
        
        # Calculate delta (exposure to underlying)
        delta = total_quantity * direction
        
        return PricingResult(
            npv=npv,
            currency=self.currency.value,
            components={
                "market_price": market_price,
                "contract_price": contract_price,
                "price_difference": price_diff,
                "total_quantity": total_quantity,
                "remaining_maturity": remaining,
                "discount_factor": df
            },
            greeks={
                "delta": delta,
                "gamma": 0.0,  # Futures have zero gamma
                "theta": -npv * curve_value(discount_curve, remaining, 0.05) / 365,
                "commodity_delta": delta  # Exposure to commodity price
            },
            metadata={
                "product_type": "commodity_future",
                "commodity_type": self.terms.commodity_type.value,
                "subclass": self.get_subclass().value,
                "is_long": self.is_long,
                "exchange": self.terms.exchange
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """
        Calculate CCR exposure profile for the Commodity Future.
        
        Commodity futures cleared through CCPs have minimal counterparty risk.
        For bilateral/OTC commodity forwards, exposure follows GBM dynamics.
        
        Args:
            market_data: Current market data
            time_horizon: Time horizon in years
            num_scenarios: Number of Monte Carlo scenarios
            confidence_level: Confidence level for PFE
            
        Returns:
            CCRExposureProfile with exposure metrics
        """
        result = self.price(market_data)
        current_exposure = max(0, result.npv)
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining) if remaining > 0 else time_horizon
        
        # Time grid
        num_points = 20
        time_grid = list(np.linspace(0, max(0.1, horizon), num_points))
        
        # Get commodity volatility
        vol = self.get_volatility()
        
        # Total notional exposure
        total_quantity = self.terms.contract_size * self.terms.num_contracts
        spot_price = self.terms.spot_price or self.terms.futures_price
        notional_exposure = total_quantity * spot_price
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            time_to_end = max(0, remaining - t)
            if time_to_end <= 0:
                ee_profile.append(0.0)
                pfe_profile.append(0.0)
                continue
            
            # Expected exposure grows with sqrt(t) due to diffusion
            vol_factor = vol * np.sqrt(t) if t > 0 else 0
            
            # Base exposure with directional component
            base_ee = current_exposure * (time_to_end / remaining if remaining > 0 else 1)
            base_ee += abs(notional_exposure) * vol_factor * 0.4
            
            ee_profile.append(max(0, base_ee))
            
            # PFE at confidence level
            z_score = 1.645 if confidence_level == 0.95 else 2.326
            pfe = base_ee + abs(notional_exposure) * vol * np.sqrt(t) * z_score
            pfe_profile.append(max(0, pfe))
        
        # Effective EE (non-decreasing)
        effective_ee = []
        max_ee = 0
        for ee in ee_profile:
            max_ee = max(max_ee, ee)
            effective_ee.append(max_ee)
        
        # Calculate aggregates
        peak_exposure = max(pfe_profile) if pfe_profile else 0
        epe = np.mean(ee_profile) if ee_profile else 0
        effective_epe = np.mean(effective_ee) if effective_ee else 0
        
        # CVA (minimal for cleared futures)
        pd = 0.001  # Assume 0.1% for CCP
        lgd = 0.45
        cva = effective_epe * pd * lgd * horizon
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=effective_ee,
            peak_exposure=peak_exposure,
            epe=epe,
            effective_epe=effective_epe,
            cva=cva
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """
        Calculate SA-CCR exposure for the Commodity Future.
        
        For commodity derivatives:
        - Supervisory factor: 18% (40% for electricity)
        - Hedging sets based on commodity type
        - Maturity factor applies
        
        EAD = α × (RC + PFE)
        
        Args:
            market_data: Current market data
            
        Returns:
            SACCRExposure with regulatory capital components
        """
        result = self.price(market_data)
        
        # Replacement Cost
        rc = max(0, result.npv)
        
        # Remaining maturity
        remaining = self.get_remaining_maturity(market_data.valuation_date)
        
        # Supervisory factor
        sf = self.get_supervisory_factor()
        
        # Maturity factor
        mf = SACCRParameters.calculate_maturity_factor(remaining)
        
        # Delta
        delta = 1.0 if self.is_long else -1.0
        
        # Adjusted notional (commodity quantity × price)
        total_quantity = self.terms.contract_size * self.terms.num_contracts
        spot_price = self.terms.spot_price or self.terms.futures_price
        adjusted_notional = total_quantity * spot_price * delta
        
        # PFE Add-on
        pfe_addon = sf * abs(adjusted_notional) * mf
        
        # EAD
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.COMMODITY,
            details={
                "supervisory_factor": sf,
                "maturity_factor": mf,
                "delta": delta,
                "adjusted_notional": adjusted_notional,
                "commodity_type": self.terms.commodity_type.value,
                "subclass": self.get_subclass().value,
                "total_quantity": total_quantity,
                "spot_price": spot_price
            }
        )
    
    def get_margin_requirement(self) -> Dict[str, float]:
        """
        Get margin requirements for the position.
        
        Returns:
            Dictionary with initial and maintenance margin
        """
        if self.terms.margin_initial > 0:
            return {
                "initial_margin": self.terms.margin_initial * self.terms.num_contracts,
                "maintenance_margin": self.terms.margin_maintenance * self.terms.num_contracts
            }
        
        # Estimate based on notional
        total_quantity = self.terms.contract_size * self.terms.num_contracts
        spot_price = self.terms.spot_price or self.terms.futures_price
        notional = total_quantity * spot_price
        
        # Typical margin rates
        vol = self.get_volatility()
        initial_rate = min(0.20, vol * 0.4)  # ~40% of vol, capped at 20%
        maintenance_rate = initial_rate * 0.75
        
        return {
            "initial_margin": notional * initial_rate,
            "maintenance_margin": notional * maintenance_rate
        }
    
    def __repr__(self) -> str:
        return (
            f"CommodityFuture(trade_id='{self.trade_id}', "
            f"commodity={self.terms.commodity_type.value}, "
            f"contracts={self.terms.num_contracts}, "
            f"long={self.is_long})"
        )


__all__ = [
    "CommodityFuture",
    "CommodityType",
    "CommoditySubClass",
    "CommodityFutureTerms",
    "COMMODITY_SUPERVISORY_FACTORS",
    "COMMODITY_VOLATILITIES",
]
