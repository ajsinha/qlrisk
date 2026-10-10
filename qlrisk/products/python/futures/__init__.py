"""
QLRisk - Futures Products v2.2.1
===============================================

Exchange-traded futures contracts across multiple asset classes.

Products:
- IndexFuture: Equity index futures (S&P 500, NASDAQ, etc.)
- InterestRateFuture: Interest rate futures (Eurodollar, Fed Funds, etc.)
- BondFuture: Government bond futures (Treasury, Bund, JGB, etc.)
- VIXFuture: Volatility index futures
- SingleStockFuture: Single stock futures
- CommodityFuture: Commodity futures (Energy, Metals, Agriculture, Livestock)

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

__version__ = "2.2.1"

from .index_future import IndexFuture
from .interest_rate_future import InterestRateFuture
from .bond_future import BondFuture
from .vix_future import VIXFuture
from .single_stock_future import SingleStockFuture
from .commodity_future import (
    CommodityFuture, 
    CommodityFutureTerms,
    CommodityType, 
    CommoditySubClass,
    COMMODITY_SUPERVISORY_FACTORS,
    COMMODITY_VOLATILITIES,
)

__all__ = [
    "__version__",
    "IndexFuture",
    "InterestRateFuture",
    "BondFuture",
    "VIXFuture",
    "SingleStockFuture",
    "CommodityFuture",
    "CommodityFutureTerms",
    "CommodityType",
    "CommoditySubClass",
    "COMMODITY_SUPERVISORY_FACTORS",
    "COMMODITY_VOLATILITIES",
]
