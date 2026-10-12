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
import tempfile
from pathlib import Path
from typing import Optional, Union

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


# Temporary folder: set_tmp_dir() > $QLRISK_TMP_DIR > qlrisk.tmp_dir in application.properties > /tmp
DEFAULT_TMP_DIR = "/tmp"
TMP_DIR_ENV = "QLRISK_TMP_DIR"
TMP_DIR_PROPERTY = "qlrisk.tmp_dir"
_tmp_dir_override: Optional[Path] = None


def _property(key: str) -> Optional[str]:
    try:
        with open(DEFAULT_CONFIG_FILE) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = (s.strip() for s in line.split("=", 1))
                    if k == key and v:
                        return v
    except OSError:
        pass
    return None


def set_tmp_dir(path: Optional[Union[str, Path]]) -> None:
    """Override qlrisk's temporary folder for this process (None restores the configured default)."""
    global _tmp_dir_override
    _tmp_dir_override = Path(path).expanduser() if path else None


def get_tmp_dir() -> Path:
    """qlrisk's temporary folder (created if missing)."""
    path = _tmp_dir_override or Path(os.environ.get(TMP_DIR_ENV) or _property(TMP_DIR_PROPERTY)
                                     or DEFAULT_TMP_DIR).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path


def tmp_path(name: str) -> Path:
    """Path of a file named `name` inside qlrisk's temporary folder."""
    return get_tmp_dir() / name


def make_tmp_dir(prefix: str = "qlrisk-") -> Path:
    """A new, uniquely named directory inside qlrisk's temporary folder."""
    return Path(tempfile.mkdtemp(prefix=prefix, dir=get_tmp_dir()))


__all__ = [
    "CONFIG_DIR",
    "DEFAULT_CONFIG_FILE",
    "DEFAULT_TMP_DIR",
    "TMP_DIR_ENV",
    "get_config_path",
    "get_default_config_file",
    "get_tmp_dir",
    "set_tmp_dir",
    "tmp_path",
    "make_tmp_dir",
]
