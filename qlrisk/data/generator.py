"""
QLRisk - Data Generator Module
=============================================

Utilities for generating test data for CCR analytics.

Generates:
- Trade portfolios (IRS, FX, Options, CDS)
- Counterparty data with credit ratings
- Market data (curves, volatilities)
- Simulation scenarios

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import string
import math


class ProductType(Enum):
    """Product types for trade generation."""
    IRS = "irs"
    FX_FORWARD = "fx_forward"
    FX_OPTION = "fx_option"
    CDS = "cds"
    EQUITY_OPTION = "equity_option"
    COMMODITY_FORWARD = "commodity_forward"
    SWAPTION = "swaption"
    CAP = "cap"
    FLOOR = "floor"


class CreditRating(Enum):
    """Credit rating grades."""
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    CC = "CC"
    C = "C"
    D = "D"


# PD mapping by rating (annual PD in decimal)
RATING_PD_MAP = {
    CreditRating.AAA: 0.0001,
    CreditRating.AA: 0.0005,
    CreditRating.A: 0.001,
    CreditRating.BBB: 0.002,
    CreditRating.BB: 0.01,
    CreditRating.B: 0.04,
    CreditRating.CCC: 0.12,
    CreditRating.CC: 0.25,
    CreditRating.C: 0.40,
    CreditRating.D: 1.0
}


@dataclass
class GeneratedTrade:
    """Generated trade data."""
    trade_id: str
    product_type: ProductType
    notional: float
    currency: str
    start_date: datetime
    maturity_date: datetime
    counterparty_id: str
    mtm: float
    fixed_rate: Optional[float] = None
    float_spread: Optional[float] = None
    strike: Optional[float] = None
    underlying_price: Optional[float] = None
    volatility: Optional[float] = None
    direction: str = "pay"  # pay or receive
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trade_id": self.trade_id,
            "product_type": self.product_type.value,
            "notional": self.notional,
            "currency": self.currency,
            "start_date": self.start_date.isoformat(),
            "maturity_date": self.maturity_date.isoformat(),
            "counterparty_id": self.counterparty_id,
            "mtm": self.mtm,
            "fixed_rate": self.fixed_rate,
            "float_spread": self.float_spread,
            "strike": self.strike,
            "underlying_price": self.underlying_price,
            "volatility": self.volatility,
            "direction": self.direction,
            "remaining_maturity": (self.maturity_date - datetime.now()).days / 365.0,
            **self.metadata
        }


@dataclass
class GeneratedCounterparty:
    """Generated counterparty data."""
    counterparty_id: str
    name: str
    rating: CreditRating
    pd: float
    lgd: float
    sector: str
    country: str
    is_financial: bool
    netting_agreement: bool
    collateral_agreement: bool
    threshold: float = 0.0
    mta: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "counterparty_id": self.counterparty_id,
            "name": self.name,
            "rating": self.rating.value,
            "pd": self.pd,
            "lgd": self.lgd,
            "sector": self.sector,
            "country": self.country,
            "is_financial": self.is_financial,
            "netting_agreement": self.netting_agreement,
            "collateral_agreement": self.collateral_agreement,
            "threshold": self.threshold,
            "mta": self.mta,
            **self.metadata
        }


@dataclass
class GeneratedMarketData:
    """Generated market data."""
    valuation_date: datetime
    base_currency: str
    discount_rate: float
    fx_rates: Dict[str, float]
    yield_curves: Dict[str, List[Tuple[float, float]]]
    volatilities: Dict[str, float]
    credit_spreads: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valuation_date": self.valuation_date.isoformat(),
            "base_currency": self.base_currency,
            "discount_rate": self.discount_rate,
            "fx_rates": self.fx_rates,
            "yield_curves": {
                k: [{"tenor": t, "rate": r} for t, r in v]
                for k, v in self.yield_curves.items()
            },
            "volatilities": self.volatilities,
            "credit_spreads": self.credit_spreads,
            **self.metadata
        }


class DataGenerator:
    """
    Generator for CCR analytics test data.
    
    Generates realistic test data for:
    - Trade portfolios
    - Counterparties
    - Market data
    - Scenarios
    """
    
    SECTORS = [
        "Financial Services", "Technology", "Energy", "Healthcare",
        "Consumer Goods", "Industrial", "Utilities", "Real Estate",
        "Materials", "Telecommunications"
    ]
    
    COUNTRIES = [
        "US", "UK", "DE", "FR", "JP", "CH", "AU", "CA", "SG", "HK"
    ]
    
    CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD"]
    
    COMPANY_PREFIXES = [
        "Global", "National", "Pacific", "Atlantic", "Continental",
        "Premier", "Capital", "United", "International", "Alliance"
    ]
    
    COMPANY_SUFFIXES = [
        "Corp", "Inc", "Holdings", "Group", "Partners", "Capital",
        "Industries", "Financial", "Investment", "Trading"
    ]
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize data generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self._trade_counter = 0
        self._counterparty_counter = 0
    
    def generate_trade_id(self) -> str:
        """Generate unique trade ID."""
        self._trade_counter += 1
        return f"TRD-{self._trade_counter:08d}"
    
    def generate_counterparty_id(self) -> str:
        """Generate unique counterparty ID."""
        self._counterparty_counter += 1
        return f"CPY-{self._counterparty_counter:06d}"
    
    def generate_company_name(self) -> str:
        """Generate random company name."""
        prefix = random.choice(self.COMPANY_PREFIXES)
        suffix = random.choice(self.COMPANY_SUFFIXES)
        return f"{prefix} {suffix}"
    
    def generate_counterparty(
        self,
        rating: Optional[CreditRating] = None,
        sector: Optional[str] = None,
        country: Optional[str] = None
    ) -> GeneratedCounterparty:
        """
        Generate a counterparty.
        
        Args:
            rating: Credit rating (random if not specified)
            sector: Sector (random if not specified)
            country: Country (random if not specified)
            
        Returns:
            Generated counterparty
        """
        if rating is None:
            # Weighted towards investment grade
            weights = [0.05, 0.10, 0.20, 0.25, 0.15, 0.10, 0.08, 0.04, 0.02, 0.01]
            rating = random.choices(list(CreditRating), weights=weights)[0]
        
        pd = RATING_PD_MAP[rating]
        
        # LGD based on sector
        sector = sector or random.choice(self.SECTORS)
        is_financial = sector == "Financial Services"
        
        if is_financial:
            lgd = random.uniform(0.35, 0.55)
        else:
            lgd = random.uniform(0.40, 0.60)
        
        # Collateral based on rating
        has_collateral = rating.value <= "BBB" and random.random() < 0.7
        
        return GeneratedCounterparty(
            counterparty_id=self.generate_counterparty_id(),
            name=self.generate_company_name(),
            rating=rating,
            pd=pd,
            lgd=lgd,
            sector=sector,
            country=country or random.choice(self.COUNTRIES),
            is_financial=is_financial,
            netting_agreement=random.random() < 0.8,
            collateral_agreement=has_collateral,
            threshold=random.uniform(0, 10_000_000) if has_collateral else 0,
            mta=random.uniform(100_000, 1_000_000) if has_collateral else 0
        )
    
    def generate_trade(
        self,
        counterparty_id: str,
        product_type: Optional[ProductType] = None,
        notional_range: Tuple[float, float] = (1_000_000, 100_000_000),
        maturity_range: Tuple[int, int] = (30, 3650),  # days
        currency: Optional[str] = None
    ) -> GeneratedTrade:
        """
        Generate a trade.
        
        Args:
            counterparty_id: Counterparty ID
            product_type: Product type (random if not specified)
            notional_range: Range for notional amount
            maturity_range: Range for maturity in days
            currency: Currency (random if not specified)
            
        Returns:
            Generated trade
        """
        product = product_type or random.choice(list(ProductType))
        notional = random.uniform(*notional_range)
        currency = currency or random.choice(self.CURRENCIES)
        
        start_date = datetime.now()
        days_to_maturity = random.randint(*maturity_range)
        maturity_date = start_date + timedelta(days=days_to_maturity)
        
        remaining_maturity = days_to_maturity / 365.0
        
        # Generate product-specific data
        trade_data = {
            "trade_id": self.generate_trade_id(),
            "product_type": product,
            "notional": notional,
            "currency": currency,
            "start_date": start_date,
            "maturity_date": maturity_date,
            "counterparty_id": counterparty_id,
            "direction": random.choice(["pay", "receive"])
        }
        
        if product == ProductType.IRS:
            trade_data["fixed_rate"] = random.uniform(0.01, 0.06)
            trade_data["float_spread"] = random.uniform(-0.005, 0.01)
            trade_data["volatility"] = random.uniform(0.3, 0.8) / 100  # IR vol
            trade_data["mtm"] = self._simulate_irs_mtm(notional, remaining_maturity)
            
        elif product == ProductType.FX_FORWARD:
            trade_data["strike"] = random.uniform(0.8, 1.5)
            trade_data["underlying_price"] = trade_data["strike"] * random.uniform(0.95, 1.05)
            trade_data["volatility"] = random.uniform(0.08, 0.18)
            trade_data["mtm"] = self._simulate_fx_mtm(notional, remaining_maturity)
            
        elif product in [ProductType.FX_OPTION, ProductType.EQUITY_OPTION]:
            trade_data["strike"] = random.uniform(0.9, 1.1) * 100
            trade_data["underlying_price"] = random.uniform(80, 120)
            trade_data["volatility"] = random.uniform(0.15, 0.40)
            trade_data["mtm"] = self._simulate_option_mtm(
                notional, remaining_maturity, trade_data["volatility"]
            )
            
        elif product == ProductType.CDS:
            trade_data["fixed_rate"] = random.uniform(0.005, 0.03)  # spread
            trade_data["volatility"] = random.uniform(0.30, 0.60)
            trade_data["mtm"] = self._simulate_cds_mtm(notional, remaining_maturity)
            
        elif product == ProductType.SWAPTION:
            trade_data["fixed_rate"] = random.uniform(0.01, 0.05)
            trade_data["volatility"] = random.uniform(0.15, 0.35)
            trade_data["mtm"] = self._simulate_option_mtm(
                notional, remaining_maturity, trade_data["volatility"]
            )
            
        else:
            trade_data["volatility"] = random.uniform(0.10, 0.30)
            trade_data["mtm"] = self._simulate_generic_mtm(notional, remaining_maturity)
        
        return GeneratedTrade(**trade_data)
    
    def _simulate_irs_mtm(self, notional: float, maturity: float) -> float:
        """Simulate IRS MTM."""
        # Duration-based approximation
        duration = min(maturity, 10) * 0.8
        rate_move = random.gauss(0, 0.005)  # 50bp std
        return notional * duration * rate_move * random.choice([1, -1])
    
    def _simulate_fx_mtm(self, notional: float, maturity: float) -> float:
        """Simulate FX MTM."""
        fx_move = random.gauss(0, 0.02)  # 2% std
        return notional * fx_move * random.choice([1, -1])
    
    def _simulate_option_mtm(
        self,
        notional: float,
        maturity: float,
        vol: float
    ) -> float:
        """Simulate option MTM."""
        # Simplified Black-Scholes style
        time_value = vol * math.sqrt(maturity)
        return notional * time_value * random.uniform(0, 0.15)
    
    def _simulate_cds_mtm(self, notional: float, maturity: float) -> float:
        """Simulate CDS MTM."""
        spread_move = random.gauss(0, 0.01)  # 100bp std
        risky_duration = min(maturity, 5) * 0.9
        return notional * risky_duration * spread_move * random.choice([1, -1])
    
    def _simulate_generic_mtm(self, notional: float, maturity: float) -> float:
        """Simulate generic MTM."""
        return notional * random.gauss(0, 0.02) * random.choice([1, -1])
    
    def generate_market_data(
        self,
        valuation_date: Optional[datetime] = None,
        base_currency: str = "USD"
    ) -> GeneratedMarketData:
        """
        Generate market data snapshot.
        
        Args:
            valuation_date: Valuation date (now if not specified)
            base_currency: Base currency
            
        Returns:
            Generated market data
        """
        valuation_date = valuation_date or datetime.now()
        
        # FX rates vs base currency
        fx_rates = {
            "EUR": random.uniform(1.05, 1.15),
            "GBP": random.uniform(1.20, 1.35),
            "JPY": random.uniform(0.0065, 0.0075),
            "CHF": random.uniform(1.05, 1.15),
            "AUD": random.uniform(0.65, 0.75),
            "CAD": random.uniform(0.72, 0.78)
        }
        fx_rates[base_currency] = 1.0
        
        # Yield curves
        base_rate = random.uniform(0.02, 0.05)
        yield_curves = {}
        
        for ccy in self.CURRENCIES:
            ccy_rate = base_rate + random.uniform(-0.01, 0.02)
            curve = [
                (0.25, ccy_rate - 0.005),
                (0.5, ccy_rate - 0.003),
                (1.0, ccy_rate),
                (2.0, ccy_rate + 0.002),
                (3.0, ccy_rate + 0.004),
                (5.0, ccy_rate + 0.008),
                (7.0, ccy_rate + 0.011),
                (10.0, ccy_rate + 0.015),
                (15.0, ccy_rate + 0.018),
                (20.0, ccy_rate + 0.020),
                (30.0, ccy_rate + 0.022)
            ]
            yield_curves[ccy] = curve
        
        # Volatilities
        volatilities = {
            "ir_3m": random.uniform(0.003, 0.008),
            "ir_1y": random.uniform(0.004, 0.010),
            "fx_eurusd": random.uniform(0.08, 0.12),
            "fx_gbpusd": random.uniform(0.09, 0.13),
            "equity_sp500": random.uniform(0.15, 0.25),
            "equity_eurostoxx": random.uniform(0.18, 0.28)
        }
        
        # Credit spreads
        credit_spreads = {
            "AAA": random.uniform(0.002, 0.005),
            "AA": random.uniform(0.004, 0.008),
            "A": random.uniform(0.006, 0.012),
            "BBB": random.uniform(0.010, 0.020),
            "BB": random.uniform(0.025, 0.045),
            "B": random.uniform(0.050, 0.100)
        }
        
        return GeneratedMarketData(
            valuation_date=valuation_date,
            base_currency=base_currency,
            discount_rate=base_rate,
            fx_rates=fx_rates,
            yield_curves=yield_curves,
            volatilities=volatilities,
            credit_spreads=credit_spreads
        )
    
    def generate_portfolio(
        self,
        num_counterparties: int = 50,
        trades_per_counterparty: Tuple[int, int] = (5, 20),
        product_mix: Optional[Dict[ProductType, float]] = None
    ) -> Tuple[List[GeneratedCounterparty], List[GeneratedTrade]]:
        """
        Generate a full portfolio.
        
        Args:
            num_counterparties: Number of counterparties
            trades_per_counterparty: Range of trades per counterparty
            product_mix: Product type distribution (weights)
            
        Returns:
            Tuple of (counterparties, trades)
        """
        # Default product mix
        if product_mix is None:
            product_mix = {
                ProductType.IRS: 0.35,
                ProductType.FX_FORWARD: 0.20,
                ProductType.FX_OPTION: 0.15,
                ProductType.CDS: 0.10,
                ProductType.EQUITY_OPTION: 0.10,
                ProductType.SWAPTION: 0.05,
                ProductType.CAP: 0.025,
                ProductType.FLOOR: 0.025
            }
        
        products = list(product_mix.keys())
        weights = list(product_mix.values())
        
        counterparties = []
        trades = []
        
        for _ in range(num_counterparties):
            cp = self.generate_counterparty()
            counterparties.append(cp)
            
            num_trades = random.randint(*trades_per_counterparty)
            for _ in range(num_trades):
                product = random.choices(products, weights=weights)[0]
                trade = self.generate_trade(cp.counterparty_id, product)
                trades.append(trade)
        
        return counterparties, trades
    
    def generate_stress_scenarios(
        self,
        base_market_data: GeneratedMarketData,
        num_scenarios: int = 10
    ) -> List[GeneratedMarketData]:
        """
        Generate stress scenarios from base market data.
        
        Args:
            base_market_data: Base market data
            num_scenarios: Number of scenarios
            
        Returns:
            List of stressed market data scenarios
        """
        scenarios = []
        
        # Pre-defined stress types
        stress_types = [
            ("rate_up", {"rate_shock": 0.02}),
            ("rate_down", {"rate_shock": -0.02}),
            ("fx_crisis", {"fx_shock": 0.15}),
            ("credit_widening", {"credit_shock": 0.02}),
            ("vol_spike", {"vol_shock": 1.5}),
            ("combined_adverse", {
                "rate_shock": -0.01,
                "fx_shock": 0.10,
                "credit_shock": 0.015,
                "vol_shock": 1.3
            })
        ]
        
        for i in range(num_scenarios):
            if i < len(stress_types):
                stress_name, shocks = stress_types[i]
            else:
                # Random scenario
                shocks = {
                    "rate_shock": random.uniform(-0.03, 0.03),
                    "fx_shock": random.uniform(-0.10, 0.15),
                    "credit_shock": random.uniform(-0.005, 0.025),
                    "vol_shock": random.uniform(0.8, 1.8)
                }
                stress_name = f"random_{i}"
            
            # Apply shocks
            stressed = self._apply_market_shocks(base_market_data, shocks)
            stressed.metadata["scenario_name"] = stress_name
            stressed.metadata["shocks"] = shocks
            scenarios.append(stressed)
        
        return scenarios
    
    def _apply_market_shocks(
        self,
        base: GeneratedMarketData,
        shocks: Dict[str, float]
    ) -> GeneratedMarketData:
        """Apply shocks to market data."""
        rate_shock = shocks.get("rate_shock", 0)
        fx_shock = shocks.get("fx_shock", 0)
        credit_shock = shocks.get("credit_shock", 0)
        vol_shock = shocks.get("vol_shock", 1.0)
        
        # Shocked yield curves
        yield_curves = {}
        for ccy, curve in base.yield_curves.items():
            yield_curves[ccy] = [(t, r + rate_shock) for t, r in curve]
        
        # Shocked FX rates
        fx_rates = {k: v * (1 + fx_shock) for k, v in base.fx_rates.items()}
        
        # Shocked credit spreads
        credit_spreads = {k: v + credit_shock for k, v in base.credit_spreads.items()}
        
        # Shocked volatilities
        volatilities = {k: v * vol_shock for k, v in base.volatilities.items()}
        
        return GeneratedMarketData(
            valuation_date=base.valuation_date,
            base_currency=base.base_currency,
            discount_rate=base.discount_rate + rate_shock,
            fx_rates=fx_rates,
            yield_curves=yield_curves,
            volatilities=volatilities,
            credit_spreads=credit_spreads
        )


def create_test_dataset(
    num_counterparties: int = 50,
    trades_per_counterparty: Tuple[int, int] = (5, 20),
    seed: Optional[int] = 42,
    num_trades: Optional[int] = None  # Alias: if provided, overrides num_counterparties calculation
) -> Dict[str, Any]:
    """
    Create a complete test dataset.
    
    Args:
        num_counterparties: Number of counterparties
        trades_per_counterparty: Range of trades per counterparty
        seed: Random seed
        num_trades: Optional total number of trades (if provided, adjusts num_counterparties)
        
    Returns:
        Dictionary with counterparties, trades, and market data
    """
    # If num_trades is specified, calculate num_counterparties accordingly
    if num_trades is not None:
        avg_trades_per_cp = (trades_per_counterparty[0] + trades_per_counterparty[1]) / 2
        num_counterparties = max(1, int(num_trades / avg_trades_per_cp))
    
    generator = DataGenerator(seed=seed)
    
    counterparties, trades = generator.generate_portfolio(
        num_counterparties,
        trades_per_counterparty
    )
    
    market_data = generator.generate_market_data()
    stress_scenarios = generator.generate_stress_scenarios(market_data)
    
    return {
        "counterparties": [cp.to_dict() for cp in counterparties],
        "trades": [trade.to_dict() for trade in trades],
        "market_data": market_data.to_dict(),
        "stress_scenarios": [s.to_dict() for s in stress_scenarios],
        "summary": {
            "num_counterparties": len(counterparties),
            "num_trades": len(trades),
            "total_notional": sum(t.notional for t in trades),
            "total_mtm": sum(t.mtm for t in trades),
            "num_stress_scenarios": len(stress_scenarios)
        }
    }
