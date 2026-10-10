"""
Thread Pool Manager - High-performance parallel processing utility

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

import threading
import queue
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, as_completed
from typing import Callable, Any, List, Optional, Dict, Tuple, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import multiprocessing


T = TypeVar('T')


class ExecutorType(Enum):
    """Executor type enumeration."""
    THREAD = "thread"
    PROCESS = "process"


@dataclass
class TaskResult(Generic[T]):
    """Result container for parallel tasks."""
    task_id: str
    success: bool
    result: Optional[T] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0


class ThreadPoolManager:
    """
    High-performance thread/process pool manager for parallel computation.
    Supports both thread pools and process pools with configurable workers.
    """
    _instance: Optional['ThreadPoolManager'] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        max_workers: Optional[int] = None,
        executor_type: ExecutorType = ExecutorType.THREAD
    ):
        """
        Initialize ThreadPoolManager.

        Args:
            max_workers: Maximum number of workers (default: CPU count * 2 for threads, CPU count for processes)
            executor_type: Type of executor (THREAD or PROCESS)
        """
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._executor_type = executor_type
        self._cpu_count = os.cpu_count() or 4
        
        if max_workers is None:
            if executor_type == ExecutorType.THREAD:
                max_workers = self._cpu_count * 2
            else:
                max_workers = self._cpu_count
        
        self._max_workers = max_workers
        self._thread_executor: Optional[ThreadPoolExecutor] = None
        self._process_executor: Optional[ProcessPoolExecutor] = None
        self._active_futures: Dict[str, Future] = {}
        self._results_queue: queue.Queue = queue.Queue()

    def _get_thread_executor(self) -> ThreadPoolExecutor:
        """Get or create thread executor."""
        if self._thread_executor is None:
            self._thread_executor = ThreadPoolExecutor(max_workers=self._max_workers)
        return self._thread_executor

    def _get_process_executor(self) -> ProcessPoolExecutor:
        """Get or create process executor."""
        if self._process_executor is None:
            self._process_executor = ProcessPoolExecutor(max_workers=self._max_workers)
        return self._process_executor

    def submit(
        self,
        func: Callable[..., T],
        *args,
        task_id: Optional[str] = None,
        use_process: bool = False,
        **kwargs
    ) -> Future:
        """
        Submit a task for execution.

        Args:
            func: Function to execute
            *args: Positional arguments for function
            task_id: Optional task identifier
            use_process: If True, use process pool instead of thread pool
            **kwargs: Keyword arguments for function

        Returns:
            Future object
        """
        if use_process:
            executor = self._get_process_executor()
        else:
            executor = self._get_thread_executor()
        
        future = executor.submit(func, *args, **kwargs)
        
        if task_id:
            self._active_futures[task_id] = future
        
        return future

    def map(
        self,
        func: Callable[[Any], T],
        items: List[Any],
        use_process: bool = False,
        chunk_size: int = 1
    ) -> List[T]:
        """
        Map function over items in parallel.

        Args:
            func: Function to apply
            items: List of items to process
            use_process: If True, use process pool
            chunk_size: Size of chunks for process pool

        Returns:
            List of results
        """
        if use_process:
            executor = self._get_process_executor()
            return list(executor.map(func, items, chunksize=chunk_size))
        else:
            executor = self._get_thread_executor()
            return list(executor.map(func, items))

    def submit_batch(
        self,
        tasks: List[Tuple[Callable, tuple, dict]],
        use_process: bool = False
    ) -> List[Future]:
        """
        Submit multiple tasks at once.

        Args:
            tasks: List of (function, args, kwargs) tuples
            use_process: If True, use process pool

        Returns:
            List of Future objects
        """
        futures = []
        for func, args, kwargs in tasks:
            future = self.submit(func, *args, use_process=use_process, **kwargs)
            futures.append(future)
        return futures

    def wait_all(
        self,
        futures: List[Future],
        timeout: Optional[float] = None
    ) -> List[TaskResult]:
        """
        Wait for all futures to complete.

        Args:
            futures: List of Future objects
            timeout: Optional timeout in seconds

        Returns:
            List of TaskResult objects
        """
        results = []
        
        for future in as_completed(futures, timeout=timeout):
            task_id = str(id(future))
            try:
                result = future.result()
                results.append(TaskResult(
                    task_id=task_id,
                    success=True,
                    result=result
                ))
            except Exception as e:
                results.append(TaskResult(
                    task_id=task_id,
                    success=False,
                    error=e
                ))
        
        return results

    def get_active_count(self) -> int:
        """Get count of active futures."""
        return len([f for f in self._active_futures.values() if not f.done()])

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task by ID.

        Args:
            task_id: Task identifier

        Returns:
            True if cancelled, False otherwise
        """
        if task_id in self._active_futures:
            return self._active_futures[task_id].cancel()
        return False

    def shutdown(self, wait: bool = True):
        """
        Shutdown all executors.

        Args:
            wait: If True, wait for pending tasks to complete
        """
        if self._thread_executor:
            self._thread_executor.shutdown(wait=wait)
            self._thread_executor = None
        
        if self._process_executor:
            self._process_executor.shutdown(wait=wait)
            self._process_executor = None
        
        self._active_futures.clear()

    @property
    def max_workers(self) -> int:
        """Get maximum workers."""
        return self._max_workers

    @property
    def cpu_count(self) -> int:
        """Get CPU count."""
        return self._cpu_count

    def __enter__(self) -> 'ThreadPoolManager':
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.shutdown()


class ParallelBatchProcessor:
    """
    Utility class for processing large datasets in parallel batches.
    """

    def __init__(
        self,
        batch_size: int = 1000,
        max_workers: Optional[int] = None
    ):
        """
        Initialize ParallelBatchProcessor.

        Args:
            batch_size: Size of each batch
            max_workers: Maximum number of workers
        """
        self.batch_size = batch_size
        self.max_workers = max_workers or (os.cpu_count() or 4)

    def process(
        self,
        items: List[Any],
        processor: Callable[[List[Any]], List[T]],
        use_process: bool = False
    ) -> List[T]:
        """
        Process items in parallel batches.

        Args:
            items: Items to process
            processor: Function to process each batch
            use_process: If True, use process pool

        Returns:
            Combined results from all batches
        """
        # Split into batches
        batches = [
            items[i:i + self.batch_size]
            for i in range(0, len(items), self.batch_size)
        ]
        
        pool_manager = ThreadPoolManager(max_workers=self.max_workers)
        
        try:
            # Submit all batches
            futures = [
                pool_manager.submit(processor, batch, use_process=use_process)
                for batch in batches
            ]
            
            # Collect results in order
            results = []
            for future in futures:
                batch_result = future.result()
                results.extend(batch_result)
            
            return results
        finally:
            pool_manager.shutdown()
