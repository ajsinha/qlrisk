"""
QLRisk - Data Module v1.3.0
==========================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

Test data generation utilities for QLRisk.

Features:
- Trade portfolio generation (IRS, FX, Options, CDS, etc.)
- Counterparty data with credit ratings
- Market data generation (curves, volatilities, FX rates)
- Stress scenario generation
- Reproducible random data with seed control

Data Classes:
- GeneratedTrade: Complete trade data with MTM
- GeneratedCounterparty: Counterparty with rating, PD, LGD
- GeneratedMarketData: Full market data snapshot

Usage:
    from qlrisk.data import DataGenerator, create_test_dataset
    
    # Quick dataset
    dataset = create_test_dataset(num_trades=1000)
    
    # Detailed generation
    generator = DataGenerator(seed=42)
    counterparties, trades = generator.generate_portfolio(
        num_counterparties=50,
        trades_per_counterparty=(5, 20)
    )
"""

__version__ = "1.3.0"

from .generator import (
    ProductType,
    CreditRating,
    GeneratedTrade,
    GeneratedCounterparty,
    GeneratedMarketData,
    DataGenerator,
    create_test_dataset,
)

__all__ = [
    "__version__",
    "ProductType",
    "CreditRating",
    "GeneratedTrade",
    "GeneratedCounterparty",
    "GeneratedMarketData",
    "DataGenerator",
    "create_test_dataset",
]
