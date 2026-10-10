"""
QLRisk - Main Engine Module
==========================================

High-performance, multi-threaded counterparty credit risk (CCR) engine.

Features:
- Concurrent calculator execution
- Multiple implementation support (Python/QuantLib)
- Configurable calculation pipelines
- Real-time analytics processing
- Comprehensive result aggregation

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from threading import Lock
import time
import traceback

from ..core.logger import get_logger
from ..core.timer import Timer, get_global_stats
from ..core.thread_pool import ThreadPoolManager
from ..core.properties_configurator import PropertiesConfigurator
from ..calculator.factory import CalculatorFactory, get_calculator_factory
from ..calculator.base import CalculatorType, ImplementationType, CalculationResult


logger = get_logger(__name__)


class EngineStatus(Enum):
    """Engine status states."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class CalculationPriority(Enum):
    """Calculation priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class CalculationTask:
    """Represents a calculation task."""
    task_id: str
    calculator_type: CalculatorType
    input_data: Any
    implementation: Optional[ImplementationType] = None
    priority: CalculationPriority = CalculationPriority.NORMAL
    callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CalculationJob:
    """Represents a batch calculation job."""
    job_id: str
    tasks: List[CalculationTask]
    parallel: bool = True
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result of a single calculation task."""
    task_id: str
    calculator_type: CalculatorType
    result: Any
    success: bool
    execution_time_ms: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobResult:
    """Result of a calculation job."""
    job_id: str
    task_results: List[TaskResult]
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_execution_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class CCREngine:
    """
    Main QLRisk.
    
    High-performance, multi-threaded engine for counterparty
    credit risk calculations.
    
    Features:
    - Concurrent execution of multiple calculators
    - Support for Python and QuantLib implementations
    - Configurable calculation pipelines
    - Real-time analytics processing
    - Comprehensive result aggregation
    
    Usage:
        engine = CCREngine()
        engine.start()
        
        # Single calculation
        result = engine.calculate(CalculatorType.PD, input_data)
        
        # Batch calculation
        job = CalculationJob(
            job_id="job1",
            tasks=[task1, task2, task3]
        )
        job_result = engine.submit_job(job)
        
        engine.stop()
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        properties_file: Optional[str] = None
    ):
        """
        Initialize CCR Engine.
        
        Args:
            config: Configuration dictionary
            properties_file: Path to properties file
        """
        self._config = config or {}
        
        # Load properties if provided
        if properties_file:
            props = PropertiesConfigurator(properties_file)
            self._config.update(props.as_dict())
        
        # Engine settings
        self._max_workers = self._config.get("engine.max_workers", 8)
        self._default_implementation = ImplementationType(
            self._config.get("engine.default_implementation", "python")
        )
        self._timeout = self._config.get("engine.timeout", 300)  # seconds
        
        # Initialize components
        self._calculator_factory = get_calculator_factory()
        self._calculator_factory.set_default_implementation(self._default_implementation)
        
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._status = EngineStatus.IDLE
        self._lock = Lock()
        
        # Statistics
        self._stats = {
            "total_calculations": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "total_execution_time_ms": 0
        }
        
        # Calculator cache
        self._calculators: Dict[str, Any] = {}
        
        logger.info(
            f"CCR Engine initialized - workers: {self._max_workers}, "
            f"implementation: {self._default_implementation.value}"
        )
    
    def start(self) -> None:
        """Start the engine."""
        with self._lock:
            if self._status == EngineStatus.RUNNING:
                logger.warning("Engine already running")
                return
            
            self._thread_pool = ThreadPoolExecutor(
                max_workers=self._max_workers,
                thread_name_prefix="ccr_engine"
            )
            self._status = EngineStatus.RUNNING
            logger.info("CCR Engine started")
    
    def stop(self) -> None:
        """Stop the engine."""
        with self._lock:
            if self._status != EngineStatus.RUNNING:
                logger.warning("Engine not running")
                return
            
            if self._thread_pool:
                self._thread_pool.shutdown(wait=True)
                self._thread_pool = None
            
            self._status = EngineStatus.STOPPED
            logger.info("CCR Engine stopped")
    
    def pause(self) -> None:
        """Pause the engine (no new tasks accepted)."""
        with self._lock:
            if self._status == EngineStatus.RUNNING:
                self._status = EngineStatus.PAUSED
                logger.info("CCR Engine paused")
    
    def resume(self) -> None:
        """Resume the engine."""
        with self._lock:
            if self._status == EngineStatus.PAUSED:
                self._status = EngineStatus.RUNNING
                logger.info("CCR Engine resumed")
    
    @property
    def status(self) -> EngineStatus:
        """Get engine status."""
        return self._status
    
    @property
    def statistics(self) -> Dict[str, Any]:
        """Get engine statistics."""
        return self._stats.copy()
    
    def calculate(
        self,
        calculator_type: CalculatorType,
        input_data: Any,
        implementation: Optional[ImplementationType] = None,
        calculator_config: Optional[Dict[str, Any]] = None
    ) -> CalculationResult:
        """
        Perform a single calculation.
        
        Args:
            calculator_type: Type of calculation
            input_data: Input data for calculation
            implementation: Implementation type (optional)
            calculator_config: Calculator configuration (optional)
            
        Returns:
            CalculationResult
        """
        if self._status != EngineStatus.RUNNING:
            raise RuntimeError(f"Engine not running (status: {self._status.value})")
        
        impl = implementation or self._default_implementation
        config = calculator_config or {}
        
        # Get or create calculator
        cache_key = f"{calculator_type.value}:{impl.value}"
        if cache_key not in self._calculators:
            self._calculators[cache_key] = self._calculator_factory.create(
                calculator_type,
                f"{calculator_type.value}_calc",
                config,
                impl
            )
        
        calculator = self._calculators[cache_key]
        
        # Execute calculation
        start_time = time.time()
        try:
            result = calculator.calculate(input_data)
            execution_time = (time.time() - start_time) * 1000
            
            self._stats["total_calculations"] += 1
            self._stats["successful_calculations"] += 1
            self._stats["total_execution_time_ms"] += execution_time
            
            return result
            
        except Exception as e:
            self._stats["total_calculations"] += 1
            self._stats["failed_calculations"] += 1
            logger.error(f"Calculation failed: {e}")
            raise
    
    def calculate_async(
        self,
        calculator_type: CalculatorType,
        input_data: Any,
        implementation: Optional[ImplementationType] = None,
        callback: Optional[Callable] = None
    ) -> Future:
        """
        Perform asynchronous calculation.
        
        Args:
            calculator_type: Type of calculation
            input_data: Input data
            implementation: Implementation type
            callback: Optional callback function
            
        Returns:
            Future object
        """
        if self._status != EngineStatus.RUNNING:
            raise RuntimeError(f"Engine not running (status: {self._status.value})")
        
        def task():
            result = self.calculate(calculator_type, input_data, implementation)
            if callback:
                callback(result)
            return result
        
        return self._thread_pool.submit(task)
    
    def submit_task(self, task: CalculationTask) -> Future:
        """
        Submit a single calculation task.
        
        Args:
            task: Calculation task
            
        Returns:
            Future object
        """
        if self._status != EngineStatus.RUNNING:
            raise RuntimeError(f"Engine not running (status: {self._status.value})")
        
        def execute_task():
            start_time = time.time()
            try:
                result = self.calculate(
                    task.calculator_type,
                    task.input_data,
                    task.implementation
                )
                execution_time = (time.time() - start_time) * 1000
                
                task_result = TaskResult(
                    task_id=task.task_id,
                    calculator_type=task.calculator_type,
                    result=result,
                    success=True,
                    execution_time_ms=execution_time,
                    metadata=task.metadata
                )
                
                if task.callback:
                    task.callback(task_result)
                
                return task_result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                task_result = TaskResult(
                    task_id=task.task_id,
                    calculator_type=task.calculator_type,
                    result=None,
                    success=False,
                    execution_time_ms=execution_time,
                    error=str(e),
                    metadata=task.metadata
                )
                
                if task.callback:
                    task.callback(task_result)
                
                return task_result
        
        return self._thread_pool.submit(execute_task)
    
    def submit_job(self, job: CalculationJob) -> JobResult:
        """
        Submit a batch calculation job.
        
        Args:
            job: Calculation job with multiple tasks
            
        Returns:
            JobResult with all task results
        """
        if self._status != EngineStatus.RUNNING:
            raise RuntimeError(f"Engine not running (status: {self._status.value})")
        
        start_time = time.time()
        task_results = []
        
        if job.parallel:
            # Execute tasks in parallel
            futures = {
                self.submit_task(task): task
                for task in job.tasks
            }
            
            for future in as_completed(futures, timeout=job.timeout):
                try:
                    result = future.result()
                    task_results.append(result)
                except Exception as e:
                    task = futures[future]
                    task_results.append(TaskResult(
                        task_id=task.task_id,
                        calculator_type=task.calculator_type,
                        result=None,
                        success=False,
                        execution_time_ms=0,
                        error=str(e)
                    ))
        else:
            # Execute tasks sequentially
            for task in job.tasks:
                try:
                    future = self.submit_task(task)
                    result = future.result(timeout=job.timeout)
                    task_results.append(result)
                except Exception as e:
                    task_results.append(TaskResult(
                        task_id=task.task_id,
                        calculator_type=task.calculator_type,
                        result=None,
                        success=False,
                        execution_time_ms=0,
                        error=str(e)
                    ))
        
        total_time = (time.time() - start_time) * 1000
        successful = sum(1 for r in task_results if r.success)
        
        return JobResult(
            job_id=job.job_id,
            task_results=task_results,
            total_tasks=len(job.tasks),
            successful_tasks=successful,
            failed_tasks=len(job.tasks) - successful,
            total_execution_time_ms=total_time,
            metadata=job.metadata
        )
    
    def calculate_ccr_metrics(
        self,
        trade_data: Dict[str, Any],
        counterparty_data: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive CCR metrics for a trade/counterparty.
        
        Calculates all major CCR metrics in a coordinated pipeline:
        - PD, LGD, EAD
        - Expected Loss
        - Current/Expected/Potential Future Exposure
        - CVA
        - Economic Capital
        - RAROC
        - Initial Margin
        
        Args:
            trade_data: Trade information (can contain counterparty and market data)
            counterparty_data: Counterparty information (optional, extracted from trade_data if not provided)
            market_data: Market data (optional, extracted from trade_data if not provided)
            implementation: Implementation type
            
        Returns:
            Dictionary with all CCR metrics
        """
        if self._status != EngineStatus.RUNNING:
            raise RuntimeError(f"Engine not running")
        
        # Extract values from trade_data with defaults
        notional = trade_data.get("notional", 10_000_000)
        mtm = trade_data.get("mtm", 0)
        maturity = trade_data.get("maturity", 5.0)
        volatility = trade_data.get("volatility", 0.20)
        rating = trade_data.get("rating", "BBB")
        pd_value = trade_data.get("counterparty_pd", 0.02)
        lgd_value = trade_data.get("counterparty_lgd", 0.45)
        discount_rate = trade_data.get("discount_rate", 0.05)
        recovery_rate = trade_data.get("recovery_rate", 1 - lgd_value)
        confidence_level = trade_data.get("confidence_level", 0.95)
        
        impl = implementation or self._default_implementation
        results = {}
        timer = Timer("ccr_metrics")
        timer.start()
        
        # PD: use the supplied counterparty PD; otherwise derive it from the rating
        if "counterparty_pd" in trade_data:
            results["pd"] = pd_value
        else:
            try:
                pd_result = self.calculate(CalculatorType.PD, {"credit_rating": rating}, impl,
                                           calculator_config={"model": "transition_matrix"})
                results["pd"] = float(pd_result.value)
            except Exception as e:
                results["pd"] = pd_value
                results["pd_error"] = str(e)
        
        # LGD: use the supplied LGD, else 1 - recovery rate
        if "counterparty_lgd" in trade_data:
            results["lgd"] = lgd_value
        else:
            results["lgd"] = 1.0 - recovery_rate
        
        # Calculate EAD
        try:
            ead_input = {
                "current_exposure": max(mtm, 0),
                "notional": notional,
                "credit_conversion_factor": 1.0,
            }
            ead_result = self.calculate(CalculatorType.EAD, ead_input, impl)
            if hasattr(ead_result.value, 'ead'):
                results["ead"] = ead_result.value.ead
            elif isinstance(ead_result.value, dict):
                results["ead"] = ead_result.value.get("ead", max(mtm, 0))
            else:
                results["ead"] = ead_result.value
        except Exception as e:
            results["ead"] = max(mtm, 0)
            results["ead_error"] = str(e)
        
        # Calculate Expected Loss
        try:
            el_input = {
                "pd": results.get("pd", pd_value),
                "lgd": results.get("lgd", lgd_value),
                "ead": results.get("ead", max(mtm, 0)),
                "time_horizon": 1.0,
            }
            el_result = self.calculate(CalculatorType.EL, el_input, impl)
            if hasattr(el_result.value, 'expected_loss'):
                results["el"] = el_result.value.expected_loss
            elif isinstance(el_result.value, dict):
                results["el"] = el_result.value.get("expected_loss", 0)
            else:
                results["el"] = el_result.value
        except Exception as e:
            results["el"] = results.get("pd", pd_value) * results.get("lgd", lgd_value) * results.get("ead", max(mtm, 0))
            results["el_error"] = str(e)
        
        # Calculate Current Exposure
        try:
            ce_input = {
                "mark_to_market": mtm,
                "collateral_held": 0,
                "collateral_posted": 0,
            }
            ce_result = self.calculate(CalculatorType.CE, ce_input, impl)
            if hasattr(ce_result.value, 'net_ce'):
                results["current_exposure"] = ce_result.value.net_ce
            elif isinstance(ce_result.value, dict):
                results["current_exposure"] = ce_result.value.get("net_ce", max(mtm, 0))
            else:
                results["current_exposure"] = ce_result.value
        except Exception as e:
            results["current_exposure"] = max(mtm, 0)
            results["ce_error"] = str(e)
        
        # Calculate Expected Exposure
        try:
            ee_input = {
                "current_mtm": mtm,
                "notional": notional,
                "remaining_maturity": maturity,
                "volatility": volatility,
                "product_type": "irs",
            }
            ee_result = self.calculate(CalculatorType.EE, ee_input, impl)
            if hasattr(ee_result.value, 'ee'):
                results["expected_exposure"] = ee_result.value.ee
            elif isinstance(ee_result.value, dict):
                results["expected_exposure"] = ee_result.value.get("ee", max(mtm, 0))
            else:
                results["expected_exposure"] = ee_result.value
        except Exception as e:
            results["expected_exposure"] = max(mtm, 0)
            results["ee_error"] = str(e)
        
        # Calculate PFE
        try:
            pfe_input = {
                "current_mtm": mtm,
                "notional": notional,
                "remaining_maturity": maturity,
                "volatility": volatility,
                "product_type": "irs",
            }
            pfe_result = self.calculate(CalculatorType.PFE, pfe_input, impl)
            if hasattr(pfe_result.value, 'pfe'):
                results["pfe"] = pfe_result.value.pfe
            elif isinstance(pfe_result.value, dict):
                results["pfe"] = pfe_result.value.get("pfe", 0)
            else:
                results["pfe"] = pfe_result.value
        except Exception as e:
            results["pfe"] = None
            results["pfe_error"] = str(e)
        
        # Calculate CVA
        try:
            # Build EE profile for CVA
            time_grid = [0.25, 0.5, 1.0, 2.0, 3.0, min(maturity, 5.0)]
            ee_profile = [max(mtm, 0) * (1 + 0.05 * t) for t in time_grid]
            
            cva_input = {
                "ee_profile": ee_profile,
                "time_grid": time_grid,
                "credit_spread": trade_data.get("spread", 0.01),
                "recovery_rate": recovery_rate,
                "risk_free_rate": discount_rate,
            }
            cva_result = self.calculate(CalculatorType.CVA, cva_input, impl)
            if hasattr(cva_result.value, 'cva'):
                results["cva"] = cva_result.value.cva
            elif isinstance(cva_result.value, dict):
                results["cva"] = cva_result.value.get("cva", 0)
            else:
                results["cva"] = cva_result.value
        except Exception as e:
            results["cva"] = None
            results["cva_error"] = str(e)
        
        # Calculate Economic Capital
        try:
            ec_input = {
                "exposures": [results.get("ead", max(mtm, 0))],
                "pds": [results.get("pd", pd_value)],
                "lgds": [results.get("lgd", lgd_value)],
                "asset_correlation": 0.20,
            }
            ec_result = self.calculate(CalculatorType.EC, ec_input, impl)
            if hasattr(ec_result.value, 'economic_capital'):
                results["economic_capital"] = ec_result.value.economic_capital
            elif isinstance(ec_result.value, dict):
                results["economic_capital"] = ec_result.value.get("economic_capital", 0)
            else:
                results["economic_capital"] = ec_result.value
        except Exception as e:
            results["economic_capital"] = None
            results["ec_error"] = str(e)
        
        # RAROC = (revenue - expected loss) / economic capital; revenue = spread x notional per year
        try:
            ec_value = results.get("economic_capital")
            raroc_input = {
                "revenue": trade_data.get("revenue", trade_data.get("spread", 0.0) * notional),
                "operating_cost": trade_data.get("operating_cost", 0.0),
                "funding_cost": trade_data.get("funding_cost", 0.0),
                "expected_loss": results.get("el", 0.0),
                "economic_capital": ec_value or 0.0,
            }
            raroc_result = self.calculate(CalculatorType.RAROC, raroc_input, impl)
            value = raroc_result.value
            results["raroc"] = getattr(value, "raroc", value.get("raroc") if isinstance(value, dict) else value)
        except Exception as e:
            results["raroc"] = None
            results["raroc_error"] = str(e)
        
        # Calculate Initial Margin
        try:
            im_input = {
                "notional": notional,
                "product_type": "irs",
                "remaining_maturity": maturity,
                "volatility": volatility,
            }
            im_result = self.calculate(CalculatorType.IM, im_input, impl)
            if hasattr(im_result.value, 'initial_margin'):
                results["initial_margin"] = im_result.value.initial_margin
            elif isinstance(im_result.value, dict):
                results["initial_margin"] = im_result.value.get("initial_margin", 0)
            else:
                results["initial_margin"] = im_result.value
        except Exception as e:
            results["initial_margin"] = None
            results["im_error"] = str(e)
        
        timer.stop()
        results["calculation_time_ms"] = timer.elapsed_ms
        results["implementation"] = impl.value
        
        return results
    
    def benchmark(
        self,
        calculator_type: CalculatorType,
        input_data: Any,
        iterations: int = 100
    ) -> Dict[str, Any]:
        """
        Benchmark Python vs QuantLib performance.
        
        Args:
            calculator_type: Calculator to benchmark
            input_data: Input data
            iterations: Number of iterations
            
        Returns:
            Benchmark results with keys:
            - python_avg_time: Average Python calculation time in seconds
            - quantlib_avg_time: Average QuantLib calculation time in seconds
            - speedup: QuantLib speedup ratio
        """
        results = {
            "calculator": calculator_type.value,
            "iterations": iterations
        }
        
        # Benchmark Python
        python_times = []
        for _ in range(iterations):
            start = time.time()
            self.calculate(calculator_type, input_data, ImplementationType.PYTHON)
            python_times.append(time.time() - start)
        
        results["python_avg_time"] = sum(python_times) / len(python_times)
        results["python_min_time"] = min(python_times)
        results["python_max_time"] = max(python_times)
        
        # Benchmark QuantLib (if available)
        try:
            qlib_times = []
            for _ in range(iterations):
                start = time.time()
                self.calculate(calculator_type, input_data, ImplementationType.QUANTLIB)
                qlib_times.append(time.time() - start)
            
            results["quantlib_avg_time"] = sum(qlib_times) / len(qlib_times)
            results["quantlib_min_time"] = min(qlib_times)
            results["quantlib_max_time"] = max(qlib_times)
            
            # Speedup ratio (Python time / QuantLib time)
            if results["quantlib_avg_time"] > 0:
                results["speedup"] = results["python_avg_time"] / results["quantlib_avg_time"]
            else:
                results["speedup"] = 1.0
            
        except Exception as e:
            results["quantlib_avg_time"] = 0
            results["quantlib_error"] = str(e)
            results["speedup"] = 1.0
        
        return results
    
    def __enter__(self) -> 'CCREngine':
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


def create_engine(
    config: Optional[Dict[str, Any]] = None,
    properties_file: Optional[str] = None
) -> CCREngine:
    """
    Create a CCR Engine instance.
    
    Args:
        config: Configuration dictionary
        properties_file: Path to properties file
        
    Returns:
        CCREngine instance
    """
    return CCREngine(config, properties_file)
