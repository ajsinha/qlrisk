"""
QLRisk - FX Products (QuantLib Implementation) v1.2.0
====================================================================

QuantLib-based implementations of FX derivatives for CCR calculation.

Products Implemented:
- FX Forward
- FX Swap
- FX Option (Vanilla)
- FX Barrier Option

Requirements:
- QuantLib Python bindings: pip install QuantLib-Python

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, List, Optional
import numpy as np

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import (
    BaseProduct, AssetClass, Currency, OptionType, OptionStyle,
    DayCountConvention, MarketData, PricingResult, 
    CCRExposureProfile, SACCRExposure, SACCRParameters, year_fraction
)
from ..product_types import ProductType
from .interest_rate import to_ql_date, from_ql_date, build_yield_curve, get_ql_calendar


# =============================================================================
# FX Forward (QuantLib)
# =============================================================================

class FXForwardQL(BaseProduct):
    """
    FX Forward using QuantLib pricing.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        settlement_date: date,
        base_currency: Currency,
        quote_currency: Currency,
        base_notional: float,
        forward_rate: float,
        counterparty_id: str,
        is_buy_base: bool = True,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.FX_FORWARD,
            asset_class=AssetClass.FX,
            trade_date=trade_date,
            effective_date=trade_date,
            maturity_date=settlement_date,
            notional=base_notional,
            currency=base_currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.base_notional = base_notional
        self.quote_notional = base_notional * forward_rate
        self.forward_rate = forward_rate
        self.is_buy_base = is_buy_base
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price FX forward using QuantLib discounting."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        valuation_date = market_data.valuation_date
        
        if self.is_expired(valuation_date):
            return PricingResult(npv=0.0, currency=self.base_currency.value)
        
        ql.Settings.instance().evaluationDate = to_ql_date(valuation_date)
        
        # Get spot rate
        pair = f"{self.base_currency.value}{self.quote_currency.value}"
        spot_rate = market_data.fx_spots.get(pair, self.forward_rate)
        
        # Build curves for both currencies
        base_curve = build_yield_curve(
            valuation_date, 
            market_data.discount_curve,
            get_ql_calendar(self.base_currency)
        )
        
        quote_curve_data = market_data.forward_curves.get(
            f"{self.quote_currency.value}_curve", 
            market_data.discount_curve
        )
        quote_curve = build_yield_curve(
            valuation_date,
            quote_curve_data if isinstance(quote_curve_data, dict) else market_data.discount_curve,
            get_ql_calendar(self.quote_currency)
        )
        
        remaining_maturity = self.get_remaining_maturity(valuation_date)
        
        # Discount factors
        df_base = base_curve.discount(to_ql_date(self.maturity_date))
        df_quote = quote_curve.discount(to_ql_date(self.maturity_date))
        
        # Fair forward rate
        fair_forward = spot_rate * df_quote / df_base
        
        # NPV
        if self.is_buy_base:
            npv = self.base_notional * df_base - self.quote_notional * df_quote / spot_rate
        else:
            npv = self.quote_notional * df_quote / spot_rate - self.base_notional * df_base
        
        # Convert to base currency terms
        npv_base = npv
        
        return PricingResult(
            npv=npv_base,
            currency=self.base_currency.value,
            components={
                "spot_rate": spot_rate,
                "forward_rate": self.forward_rate,
                "fair_forward": fair_forward,
                "forward_points": (fair_forward - spot_rate) * 10000,
                "base_df": df_base,
                "quote_df": df_quote,
            },
            greeks={
                "fx_delta": self.base_notional * df_base * (1 if self.is_buy_base else -1),
            },
            metadata={
                "product_type": self.product_type.value,
                "pricing_engine": "QuantLib",
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile."""
        result = self.price(market_data)
        current_npv = result.npv
        fx_delta = result.greeks.get("fx_delta", self.base_notional)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        horizon = min(time_horizon, remaining_maturity)
        
        fx_vol = market_data.volatility_surfaces.get("fx_vol", 0.10)
        if isinstance(fx_vol, dict):
            fx_vol = 0.10
        
        time_grid = list(np.linspace(0, horizon, 10))
        spot = result.components.get("spot_rate", self.forward_rate)
        
        np.random.seed(42)
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            if t == 0:
                ee_profile.append(max(0, current_npv))
                pfe_profile.append(max(0, current_npv))
                continue
            
            fx_returns = np.random.normal(-0.5 * fx_vol**2 * t, fx_vol * np.sqrt(t), num_scenarios)
            fx_changes = spot * (np.exp(fx_returns) - 1)
            npv_changes = fx_delta * fx_changes / spot
            
            time_factor = max(0, 1 - t / remaining_maturity) if remaining_maturity > 0 else 0
            simulated_npvs = (current_npv + npv_changes) * time_factor
            
            exposures = np.maximum(0, simulated_npvs)
            
            ee_profile.append(np.mean(exposures))
            pfe_profile.append(np.percentile(exposures, confidence_level * 100))
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=ee_profile,
            peak_exposure=max(pfe_profile),
            epe=np.mean(ee_profile),
            effective_epe=np.mean(ee_profile),
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv)
        
        remaining_maturity = self.get_remaining_maturity(market_data.valuation_date)
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.FX)
        mf = SACCRParameters.calculate_maturity_factor(remaining_maturity)
        
        delta = 1.0 if self.is_buy_base else -1.0
        pfe_addon = sf * np.abs(delta) * self.base_notional * mf
        
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        pair = f"{self.base_currency.value}{self.quote_currency.value}"
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.FX,
            hedging_set_contributions={pair: pfe_addon}
        )


# =============================================================================
# FX Option (QuantLib)
# =============================================================================

class FXOptionQL(BaseProduct):
    """
    FX Vanilla Option using QuantLib Garman-Kohlhagen pricing.
    """
    
    def __init__(
        self,
        trade_id: str,
        trade_date: date,
        expiry_date: date,
        settlement_date: date,
        base_currency: Currency,
        quote_currency: Currency,
        base_notional: float,
        strike: float,
        counterparty_id: str,
        option_type: OptionType = OptionType.CALL,
        is_long: bool = True,
        premium: float = 0.0,
        volatility: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            trade_id=trade_id,
            product_type=ProductType.FX_OPTION,
            asset_class=AssetClass.FX,
            trade_date=trade_date,
            effective_date=expiry_date,
            maturity_date=settlement_date,
            notional=base_notional,
            currency=base_currency,
            counterparty_id=counterparty_id,
            **kwargs
        )
        
        self.expiry_date = expiry_date
        self.settlement_date = settlement_date
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.base_notional = base_notional
        self.strike = strike
        self.option_type = option_type
        self.is_long = is_long
        self.premium = premium
        self.volatility = volatility
    
    def price(self, market_data: MarketData) -> PricingResult:
        """Price FX option using QuantLib Garman-Kohlhagen."""
        if not QUANTLIB_AVAILABLE:
            raise RuntimeError("QuantLib not available")
        
        valuation_date = market_data.valuation_date
        
        if valuation_date >= self.expiry_date:
            # Expired - calculate intrinsic only
            pair = f"{self.base_currency.value}{self.quote_currency.value}"
            spot = market_data.fx_spots.get(pair, self.strike)
            
            if self.option_type == OptionType.CALL:
                intrinsic = max(0, spot - self.strike)
            else:
                intrinsic = max(0, self.strike - spot)
            
            npv = self.base_notional * intrinsic
            if not self.is_long:
                npv = -npv
            
            return PricingResult(npv=npv, currency=self.base_currency.value)
        
        ql.Settings.instance().evaluationDate = to_ql_date(valuation_date)
        
        # Get spot rate
        pair = f"{self.base_currency.value}{self.quote_currency.value}"
        spot_rate = market_data.fx_spots.get(pair, self.strike)
        
        # Build curves
        base_curve = build_yield_curve(
            valuation_date,
            market_data.discount_curve,
            get_ql_calendar(self.base_currency)
        )
        
        quote_curve_data = market_data.forward_curves.get(
            f"{self.quote_currency.value}_curve",
            market_data.discount_curve
        )
        quote_curve = build_yield_curve(
            valuation_date,
            quote_curve_data if isinstance(quote_curve_data, dict) else market_data.discount_curve,
            get_ql_calendar(self.quote_currency)
        )
        
        # Volatility
        vol = self.volatility or market_data.volatility_surfaces.get("fx_vol", 0.10)
        if isinstance(vol, dict):
            vol = 0.10
        
        # Create QuantLib objects
        spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot_rate))
        vol_handle = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(
                to_ql_date(valuation_date),
                ql.TARGET(),
                vol,
                ql.Actual365Fixed()
            )
        )
        
        # Option type
        ql_option_type = ql.Option.Call if self.option_type == OptionType.CALL else ql.Option.Put
        
        # Payoff and exercise
        payoff = ql.PlainVanillaPayoff(ql_option_type, self.strike)
        exercise = ql.EuropeanExercise(to_ql_date(self.expiry_date))
        
        # Build option
        option = ql.VanillaOption(payoff, exercise)
        
        # Garman-Kohlhagen process
        process = ql.GarmanKohlagenProcess(
            spot_handle,
            quote_curve,  # Foreign rate (quote currency)
            base_curve,   # Domestic rate (base currency)
            vol_handle
        )
        
        # Pricing engine
        engine = ql.AnalyticEuropeanEngine(process)
        option.setPricingEngine(engine)
        
        # Get results
        npv_per_unit = option.NPV()
        delta = option.delta()
        gamma = option.gamma()
        vega = option.vega() / 100  # Per 1% vol change
        
        npv = self.base_notional * npv_per_unit
        if not self.is_long:
            npv = -npv
            delta = -delta
        
        time_to_expiry = year_fraction(valuation_date, self.expiry_date, DayCountConvention.ACT_365)
        
        return PricingResult(
            npv=npv,
            currency=self.base_currency.value,
            components={
                "premium": npv,
                "unit_premium": npv_per_unit,
                "spot_rate": spot_rate,
                "strike": self.strike,
                "volatility": vol,
                "time_to_expiry": time_to_expiry,
            },
            greeks={
                "delta": delta * self.base_notional,
                "gamma": gamma * self.base_notional,
                "vega": vega * self.base_notional,
            },
            metadata={
                "product_type": self.product_type.value,
                "pricing_engine": "QuantLib.GarmanKohlhagen",
            }
        )
    
    def calculate_ccr_exposure(
        self,
        market_data: MarketData,
        time_horizon: float = 5.0,
        num_scenarios: int = 10000,
        confidence_level: float = 0.95
    ) -> CCRExposureProfile:
        """Calculate CCR exposure profile."""
        result = self.price(market_data)
        current_npv = max(0, result.npv) if self.is_long else 0
        
        option_maturity = year_fraction(
            market_data.valuation_date,
            self.expiry_date,
            DayCountConvention.ACT_365
        )
        horizon = min(time_horizon, option_maturity)
        
        time_grid = list(np.linspace(0, horizon, 10))
        
        ee_profile = []
        pfe_profile = []
        
        for t in time_grid:
            time_factor = np.sqrt(max(0, option_maturity - t) / option_maturity) if option_maturity > 0 else 0
            exposure = current_npv * time_factor
            ee_profile.append(exposure)
            pfe_profile.append(exposure * 1.4)
        
        return CCRExposureProfile(
            time_grid=time_grid,
            expected_exposure=ee_profile,
            potential_future_exposure=pfe_profile,
            effective_ee=ee_profile,
            peak_exposure=max(pfe_profile) if pfe_profile else 0,
            epe=np.mean(ee_profile),
            effective_epe=np.mean(ee_profile),
            cva=0.0
        )
    
    def calculate_saccr(self, market_data: MarketData) -> SACCRExposure:
        """Calculate SA-CCR exposure."""
        result = self.price(market_data)
        rc = max(0, result.npv) if self.is_long else 0
        
        option_maturity = year_fraction(
            market_data.valuation_date,
            self.expiry_date,
            DayCountConvention.ACT_365
        )
        
        sf = SACCRParameters.get_supervisory_factor(AssetClass.FX)
        mf = SACCRParameters.calculate_maturity_factor(option_maturity)
        
        vol = self.volatility or 0.15
        is_call = self.option_type == OptionType.CALL
        
        pair = f"{self.base_currency.value}{self.quote_currency.value}"
        spot = result.components.get("spot_rate", self.strike)
        
        delta = SACCRParameters.calculate_option_delta(
            is_call=is_call,
            underlying=spot,
            strike=self.strike,
            time_to_expiry=option_maturity,
            volatility=vol
        )
        
        if not self.is_long:
            delta = -delta
        
        pfe_addon = sf * np.abs(delta) * self.base_notional * mf
        ead = SACCRParameters.ALPHA * (rc + pfe_addon)
        
        return SACCRExposure(
            replacement_cost=rc,
            pfe_add_on=pfe_addon,
            ead=ead,
            asset_class=AssetClass.FX,
            hedging_set_contributions={pair: pfe_addon}
        )


__all__ = [
    "FXForwardQL",
    "FXOptionQL",
    "QUANTLIB_AVAILABLE",
]
