"""
QLRisk - Configuration Module
============================================

Configuration management for QLRisk.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
"""

import os
from pathlib import Path

# Configuration directory path
CONFIG_DIR = Path(__file__).parent

# Default configuration file
DEFAULT_CONFIG_FILE = CONFIG_DIR / "application.properties"


def get_config_path() -> Path:
    """Get the path to the configuration directory."""
    return CONFIG_DIR


def get_default_config_file() -> Path:
    """Get the path to the default configuration file."""
    return DEFAULT_CONFIG_FILE


__all__ = [
    "CONFIG_DIR",
    "DEFAULT_CONFIG_FILE",
    "get_config_path",
    "get_default_config_file",
]
