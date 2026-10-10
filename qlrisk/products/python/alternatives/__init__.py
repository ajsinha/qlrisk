"""
QLRisk - Alternatives Products v1.2.0
============================================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from .crypto_spot import CryptoSpot
from .crypto_future import CryptoFuture
from .crypto_perpetual import CryptoPerpetual
from .reit import REIT
from .carbon_credit import CarbonCredit
from .carbon_future import CarbonFuture
from .private_equity_interest import PrivateEquityInterest
from .hedge_fund_interest import HedgeFundInterest

__all__ = [
    "CryptoSpot",
    "CryptoFuture",
    "CryptoPerpetual",
    "REIT",
    "CarbonCredit",
    "CarbonFuture",
    "PrivateEquityInterest",
    "HedgeFundInterest",
]
