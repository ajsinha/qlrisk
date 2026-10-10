"""
QLRisk - Engine Module v2.0.1
============================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

High-performance risk engines: RiskEngine (every risk, one call), MarketRiskEngine (VaR, ES, SVaR,
stress, backtesting) and CCREngine (counterparty credit risk calculators).

Features:
- Concurrent calculator execution via ThreadPoolExecutor
- Multiple implementation support (Python/QuantLib)
- Configurable calculation pipelines
- Real-time analytics processing
- Comprehensive result aggregation
- Batch job processing with priority queues
- Performance benchmarking (Python vs QuantLib)

Components:
- CCREngine: Main orchestrator for CCR calculations
- MarketRiskEngine: Sensitivities, scenario P&L, VaR / ES / parametric VaR / stressed VaR
- EngineStatus: Engine state enumeration (IDLE, RUNNING, PAUSED, STOPPED, ERROR)
- CalculationTask: Single calculation task definition
- CalculationJob: Batch of calculation tasks
- TaskResult: Individual task result
- JobResult: Aggregated job results

Usage:
    from qlrisk.engine import CCREngine
    
    with CCREngine() as engine:
        result = engine.calculate(CalculatorType.CVA, input_data)
        metrics = engine.calculate_ccr_metrics(trade_data)
"""

__version__ = "2.0.1"

from .ccr_engine import (
    CCREngine,
    EngineStatus,
    CalculationPriority,
    CalculationTask,
    CalculationJob,
    TaskResult,
    JobResult,
    create_engine,
)

from .market_risk_engine import MarketRiskEngine, FULL, TAYLOR
from .risk_engine import RiskEngine, ALL_MEASURES, DEFAULT_MEASURES

__all__ = [
    "__version__",
    "CCREngine",
    "MarketRiskEngine",
    "RiskEngine",
    "ALL_MEASURES",
    "DEFAULT_MEASURES",
    "FULL",
    "TAYLOR",
    "EngineStatus",
    "CalculationPriority",
    "CalculationTask",
    "CalculationJob",
    "TaskResult",
    "JobResult",
    "create_engine",
]
