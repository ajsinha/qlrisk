"""
QLRisk - Models Module v2.3.0
============================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

Comprehensive domain models for QLRisk.

Modules (14):
- base: Abstract base model with common functionality
- trade: Trade and TradeType, TradeStatus definitions
- portfolio: Portfolio aggregation and snapshots
- counterparty: Counterparty, NettingSet, CollateralAgreement
- curve: YieldCurve, CreditCurve, VolatilitySurface
- market_data: MarketData snapshots and quotes
- products: 27 financial product type definitions
- scenario: Stress testing scenarios and Monte Carlo
- exposure: Exposure profiles and SA-CCR results
- rating: Credit ratings and transition matrices
- collateral: Collateral models and haircuts
- agreement: Legal agreement definitions (CSA, ISDA)
- limit: Credit limit structures
- factory: Model factory for object creation

Total Classes: 55+
"""

__version__ = "2.3.0"

# Trade models
from .trade import Trade, TradeType, TradeStatus

# Portfolio models
from .portfolio import (
    PortfolioType, AggregationLevel, PortfolioSummary,
    Portfolio, PortfolioSnapshot
)

# Counterparty models
from .counterparty import Counterparty, NettingSet, CollateralAgreement

# Curve models
from .curve import Curve, CurveType, YieldCurve, CreditCurve, VolatilitySurface

# Market data models
from .market_data import MarketData, MarketDataSnapshot, Quote

# Product models
from .products import (
    PaymentFrequency, OptionType, OptionStyle, AssetClass,
    Product,
    InterestRateSwap, OvernightIndexSwap, ForwardRateAgreement,
    InterestRateCap, InterestRateFloor, Swaption,
    FXForward, FXSwap, FXOption, NonDeliverableForward,
    CreditDefaultSwap, CDSIndex, TotalReturnSwap,
    EquityOption, EquitySwap, VarianceSwap,
    CommoditySwap, CommodityForward,
    CrossCurrencySwap, Repo,
    Bond, FloatingRateNote,
)

# Scenario models
from .scenario import (
    ScenarioType, ShockType,
    RiskFactorShock, CurveShock,
    Scenario, ScenarioSet,
    SimulationPath, MonteCarloScenarioSet,
    REGULATORY_SCENARIOS,
)

# Exposure models
from .exposure import (
    ExposureType, ExposureMethod,
    ExposureProfile, ExposureResult,
    SACCRResult, NettingSetExposure,
)

# Rating models
from .rating import (
    RatingAgency, RatingScale,
    RATING_PD_MAP, RATING_SCORE_MAP,
    CreditRating, RatingHistory,
    TransitionMatrix, create_default_transition_matrix,
)

# Factory
from .factory import ModelFactory

__all__ = [
    "__version__",
    
    # Trade
    "Trade", "TradeType", "TradeStatus",
    
    # Portfolio
    "PortfolioType", "AggregationLevel", "PortfolioSummary",
    "Portfolio", "PortfolioSnapshot",
    
    # Counterparty
    "Counterparty", "NettingSet", "CollateralAgreement",
    
    # Curves
    "Curve", "CurveType", "YieldCurve", "CreditCurve", "VolatilitySurface",
    
    # Market Data
    "MarketData", "MarketDataSnapshot", "Quote",
    
    # Product Enums
    "PaymentFrequency", "OptionType", "OptionStyle", "AssetClass",
    
    # Products (27)
    "Product",
    "InterestRateSwap", "OvernightIndexSwap", "ForwardRateAgreement",
    "InterestRateCap", "InterestRateFloor", "Swaption",
    "FXForward", "FXSwap", "FXOption", "NonDeliverableForward",
    "CreditDefaultSwap", "CDSIndex", "TotalReturnSwap",
    "EquityOption", "EquitySwap", "VarianceSwap",
    "CommoditySwap", "CommodityForward",
    "CrossCurrencySwap", "Repo",
    "Bond", "FloatingRateNote",
    
    # Scenario
    "ScenarioType", "ShockType",
    "RiskFactorShock", "CurveShock",
    "Scenario", "ScenarioSet",
    "SimulationPath", "MonteCarloScenarioSet",
    "REGULATORY_SCENARIOS",
    
    # Exposure
    "ExposureType", "ExposureMethod",
    "ExposureProfile", "ExposureResult",
    "SACCRResult", "NettingSetExposure",
    
    # Rating
    "RatingAgency", "RatingScale",
    "RATING_PD_MAP", "RATING_SCORE_MAP",
    "CreditRating", "RatingHistory",
    "TransitionMatrix", "create_default_transition_matrix",
    
    # Factory
    "ModelFactory",
]
