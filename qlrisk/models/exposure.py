"""
QLRisk - Exposure Model v1.2.0
=============================================

Exposure calculation result models.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
import numpy as np


class ExposureType(Enum):
    """Type of exposure measure."""
    CURRENT = "current_exposure"
    POTENTIAL_FUTURE = "potential_future_exposure"
    EXPECTED = "expected_exposure"
    EFFECTIVE_EXPECTED = "effective_expected_exposure"
    PEAK = "peak_exposure"
    STRESSED = "stressed_exposure"


class ExposureMethod(Enum):
    """Method used to calculate exposure."""
    CURRENT_EXPOSURE = "cem"
    STANDARDISED = "sa_ccr"
    INTERNAL_MODEL = "imm"
    MONTE_CARLO = "monte_carlo"


@dataclass
class ExposureProfile:
    """Time-series of exposure values."""
    profile_id: str = field(default_factory=lambda: f"EXP-{uuid.uuid4().hex[:8].upper()}")
    exposure_type: ExposureType = ExposureType.EXPECTED
    time_grid: List[float] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    currency: str = "USD"
    confidence_level: float = 0.95
    
    def validate(self) -> bool:
        return len(self.time_grid) == len(self.values)
    
    def get_value_at_time(self, t: float) -> float:
        """Interpolate value at time t."""
        if not self.time_grid or not self.values:
            return 0.0
        
        if t <= self.time_grid[0]:
            return self.values[0]
        if t >= self.time_grid[-1]:
            return self.values[-1]
        
        for i in range(len(self.time_grid) - 1):
            if self.time_grid[i] <= t <= self.time_grid[i + 1]:
                dt = self.time_grid[i + 1] - self.time_grid[i]
                if dt > 0:
                    alpha = (t - self.time_grid[i]) / dt
                    return self.values[i] + alpha * (self.values[i + 1] - self.values[i])
        
        return self.values[-1]
    
    def peak(self) -> float:
        """Get peak exposure."""
        return max(self.values) if self.values else 0.0
    
    def average(self) -> float:
        """Get average exposure."""
        return float(np.mean(self.values)) if self.values else 0.0
    
    def time_weighted_average(self) -> float:
        """Calculate time-weighted average."""
        if len(self.time_grid) < 2:
            return self.average()
        
        total = 0.0
        for i in range(len(self.time_grid) - 1):
            dt = self.time_grid[i + 1] - self.time_grid[i]
            avg_val = (self.values[i] + self.values[i + 1]) / 2
            total += avg_val * dt
        
        total_time = self.time_grid[-1] - self.time_grid[0]
        return total / total_time if total_time > 0 else 0.0


@dataclass
class ExposureResult:
    """Complete exposure calculation result."""
    result_id: str = field(default_factory=lambda: f"EXPR-{uuid.uuid4().hex[:8].upper()}")
    calculation_date: datetime = field(default_factory=datetime.now)
    reference_id: str = ""
    reference_type: str = ""
    method: ExposureMethod = ExposureMethod.MONTE_CARLO
    
    current_exposure: float = 0.0
    potential_future_exposure: float = 0.0
    expected_exposure: float = 0.0
    effective_expected_exposure: float = 0.0
    peak_exposure: float = 0.0
    
    ee_profile: Optional[ExposureProfile] = None
    pfe_profile: Optional[ExposureProfile] = None
    
    ead: float = 0.0
    eepe: float = 0.0
    
    currency: str = "USD"
    confidence_level: float = 0.95
    time_horizon: float = 1.0
    num_scenarios: int = 10000
    
    def validate(self) -> bool:
        return bool(self.result_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "calculation_date": self.calculation_date.isoformat(),
            "reference_id": self.reference_id,
            "method": self.method.value,
            "current_exposure": self.current_exposure,
            "potential_future_exposure": self.potential_future_exposure,
            "expected_exposure": self.expected_exposure,
            "effective_expected_exposure": self.effective_expected_exposure,
            "peak_exposure": self.peak_exposure,
            "ead": self.ead,
            "eepe": self.eepe,
            "currency": self.currency,
        }


@dataclass
class SACCRResult:
    """SA-CCR calculation result per Basel III/IV."""
    result_id: str = field(default_factory=lambda: f"SACCR-{uuid.uuid4().hex[:8].upper()}")
    calculation_date: datetime = field(default_factory=datetime.now)
    netting_set_id: str = ""
    
    replacement_cost: float = 0.0
    potential_future_exposure: float = 0.0
    
    ir_addon: float = 0.0
    fx_addon: float = 0.0
    credit_addon: float = 0.0
    equity_addon: float = 0.0
    commodity_addon: float = 0.0
    
    multiplier: float = 1.0
    ead: float = 0.0
    collateral_value: float = 0.0
    
    def validate(self) -> bool:
        return bool(self.result_id)
    
    def calculate_ead(self, alpha: float = 1.4) -> float:
        """Calculate EAD per SA-CCR formula."""
        total_addon = (self.ir_addon + self.fx_addon + self.credit_addon + 
                      self.equity_addon + self.commodity_addon)
        pfe = self.multiplier * total_addon
        self.potential_future_exposure = pfe
        self.ead = alpha * (self.replacement_cost + pfe)
        return self.ead


@dataclass
class NettingSetExposure:
    """Exposure aggregated at netting set level."""
    netting_set_id: str = ""
    counterparty_id: str = ""
    num_trades: int = 0
    
    gross_positive: float = 0.0
    gross_negative: float = 0.0
    net_exposure: float = 0.0
    
    collateral: float = 0.0
    net_collateralized: float = 0.0
    netting_benefit: float = 0.0
    
    def validate(self) -> bool:
        return bool(self.netting_set_id)
    
    def calculate_netting_benefit(self) -> float:
        """Calculate netting benefit percentage."""
        if self.gross_positive > 0:
            self.netting_benefit = 1 - (self.net_exposure / self.gross_positive)
        return self.netting_benefit


__all__ = [
    "ExposureType",
    "ExposureMethod",
    "ExposureProfile",
    "ExposureResult",
    "SACCRResult",
    "NettingSetExposure",
]
