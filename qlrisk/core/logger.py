"""
Logger - Thread-safe logging utility for QLRisk

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

import logging
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json


class Logger:
    """
    Thread-safe singleton logger with configurable formatting and output.
    Supports console and file logging with rotation capabilities.
    """
    _instance: Optional['Logger'] = None
    _lock = threading.Lock()
    _loggers: Dict[str, logging.Logger] = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        name: str = "qlrisk",
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        log_format: Optional[str] = None,
        json_format: bool = False
    ):
        """
        Initialize the Logger.

        Args:
            name: Logger name
            level: Logging level (default: INFO)
            log_file: Optional path to log file
            log_format: Custom log format string
            json_format: If True, output logs in JSON format
        """
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._name = name
        self._level = level
        self._json_format = json_format
        
        # Default format
        self._format = log_format or (
            "%(asctime)s | %(levelname)-8s | %(name)s | "
            "%(filename)s:%(lineno)d | %(message)s"
        )
        
        # Create root logger
        self._root_logger = self._create_logger(name, level, log_file)

    def _create_logger(
        self,
        name: str,
        level: int,
        log_file: Optional[str] = None
    ) -> logging.Logger:
        """Create and configure a logger."""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if self._json_format:
            console_handler.setFormatter(JsonFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(self._format))
        
        logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            
            if self._json_format:
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(self._format))
            
            logger.addHandler(file_handler)

        return logger

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a child logger.

        Args:
            name: Logger name (will be prefixed with root name)

        Returns:
            Configured logger instance
        """
        full_name = f"{self._name}.{name}"
        
        if full_name not in self._loggers:
            with self._lock:
                if full_name not in self._loggers:
                    child_logger = logging.getLogger(full_name)
                    child_logger.setLevel(self._level)
                    self._loggers[full_name] = child_logger
        
        return self._loggers[full_name]

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._root_logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._root_logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._root_logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._root_logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._root_logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self._root_logger.exception(message, **kwargs)

    def set_level(self, level: int):
        """Set logging level."""
        self._level = level
        self._root_logger.setLevel(level)
        for logger in self._loggers.values():
            logger.setLevel(level)


class JsonFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.threadName,
            "thread_id": record.thread,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


# Global logger instance
_logger_instance: Optional[Logger] = None


def get_logger(name: str = "qlrisk") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = Logger()
    
    if name == "qlrisk":
        return _logger_instance._root_logger
    
    return _logger_instance.get_logger(name)
