"""
QLRisk - Engine Module v1.3.0
============================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

High-performance, multi-threaded risk analytics engine (CCR today; market risk on the roadmap).

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

__version__ = "1.3.0"

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

__all__ = [
    "__version__",
    "CCREngine",
    "EngineStatus",
    "CalculationPriority",
    "CalculationTask",
    "CalculationJob",
    "TaskResult",
    "JobResult",
    "create_engine",
]
