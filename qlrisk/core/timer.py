"""
Timer - Performance timing utilities for QLRisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

import time
import functools
from typing import Callable, Any, Optional, Dict
from contextlib import contextmanager
import threading
from collections import defaultdict
import statistics


class Timer:
    """
    High-precision timer for performance measurement.
    Supports context manager and decorator patterns.
    """

    def __init__(self, name: str = "timer"):
        """
        Initialize Timer.

        Args:
            name: Timer name for identification
        """
        self.name = name
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._elapsed: float = 0.0
        self._lap_times: list = []
        self._is_running = False
        self._lock = threading.Lock()

    def start(self) -> 'Timer':
        """Start the timer."""
        with self._lock:
            self._start_time = time.perf_counter()
            self._is_running = True
        return self

    def stop(self) -> float:
        """
        Stop the timer and return elapsed time.

        Returns:
            Elapsed time in seconds
        """
        with self._lock:
            if self._is_running:
                self._end_time = time.perf_counter()
                self._elapsed = self._end_time - self._start_time
                self._is_running = False
        return self._elapsed

    def lap(self) -> float:
        """
        Record a lap time without stopping the timer.

        Returns:
            Lap time in seconds
        """
        with self._lock:
            if self._is_running:
                current_time = time.perf_counter()
                lap_time = current_time - self._start_time
                self._lap_times.append(lap_time)
                return lap_time
        return 0.0

    def reset(self):
        """Reset the timer."""
        with self._lock:
            self._start_time = None
            self._end_time = None
            self._elapsed = 0.0
            self._lap_times = []
            self._is_running = False

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        with self._lock:
            if self._is_running:
                return time.perf_counter() - self._start_time
            return self._elapsed

    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return self.elapsed * 1000

    @property
    def elapsed_us(self) -> float:
        """Get elapsed time in microseconds."""
        return self.elapsed * 1_000_000

    @property
    def is_running(self) -> bool:
        """Check if timer is running."""
        return self._is_running

    def __enter__(self) -> 'Timer':
        """Context manager entry."""
        return self.start()

    def __exit__(self, *args):
        """Context manager exit."""
        self.stop()

    def __repr__(self) -> str:
        return f"Timer(name='{self.name}', elapsed={self.elapsed:.6f}s)"


class TimerStats:
    """
    Aggregate timer statistics for performance analysis.
    Thread-safe collection of timing measurements.
    """

    def __init__(self):
        self._times: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def record(self, name: str, duration: float):
        """
        Record a timing measurement.

        Args:
            name: Timer name
            duration: Duration in seconds
        """
        with self._lock:
            self._times[name].append(duration)

    def get_stats(self, name: str) -> Dict[str, float]:
        """
        Get statistics for a timer.

        Args:
            name: Timer name

        Returns:
            Dictionary with count, min, max, mean, median, stdev
        """
        with self._lock:
            times = self._times.get(name, [])
            
            if not times:
                return {}
            
            stats = {
                "count": len(times),
                "total": sum(times),
                "min": min(times),
                "max": max(times),
                "mean": statistics.mean(times),
                "median": statistics.median(times),
            }
            
            if len(times) > 1:
                stats["stdev"] = statistics.stdev(times)
            else:
                stats["stdev"] = 0.0
            
            return stats

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics for all timers.

        Returns:
            Dictionary of timer names to statistics
        """
        with self._lock:
            return {name: self.get_stats(name) for name in self._times}

    def clear(self, name: Optional[str] = None):
        """
        Clear timing data.

        Args:
            name: Optional timer name to clear (clears all if None)
        """
        with self._lock:
            if name:
                self._times.pop(name, None)
            else:
                self._times.clear()


# Global timer stats instance
_global_stats = TimerStats()


def timed(name: Optional[str] = None, stats: Optional[TimerStats] = None):
    """
    Decorator to measure function execution time.

    Args:
        name: Optional timer name (defaults to function name)
        stats: Optional TimerStats instance (defaults to global)

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        timer_name = name or func.__qualname__
        timer_stats = stats or _global_stats

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with Timer(timer_name) as t:
                result = func(*args, **kwargs)
            timer_stats.record(timer_name, t.elapsed)
            return result

        return wrapper

    return decorator


@contextmanager
def timing(name: str, stats: Optional[TimerStats] = None):
    """
    Context manager for timing code blocks.

    Args:
        name: Timer name
        stats: Optional TimerStats instance

    Yields:
        Timer instance
    """
    timer_stats = stats or _global_stats
    timer = Timer(name)
    timer.start()
    try:
        yield timer
    finally:
        timer.stop()
        timer_stats.record(name, timer.elapsed)


def get_global_stats() -> TimerStats:
    """Get the global TimerStats instance."""
    return _global_stats
