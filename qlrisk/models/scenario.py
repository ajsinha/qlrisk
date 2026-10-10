"""
QLRisk - Scenario Model v1.2.0
=============================================

Market scenario models for simulation and stress testing.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
import numpy as np


class ScenarioType(Enum):
    """Type of market scenario."""
    BASE = "base"
    STRESS = "stress"
    HISTORICAL = "historical"
    MONTE_CARLO = "monte_carlo"
    HYPOTHETICAL = "hypothetical"


class ShockType(Enum):
    """Type of market shock."""
    ABSOLUTE = "absolute"
    RELATIVE = "relative"
    PARALLEL = "parallel"
    TWIST = "twist"
    BUTTERFLY = "butterfly"


@dataclass
class RiskFactorShock:
    """Shock to a single risk factor."""
    risk_factor: str = ""
    shock_type: ShockType = ShockType.RELATIVE
    shock_value: float = 0.0
    shock_unit: str = "percent"
    
    def apply(self, base_value: float) -> float:
        """Apply shock to base value."""
        if self.shock_type == ShockType.ABSOLUTE:
            return base_value + self.shock_value
        elif self.shock_type == ShockType.RELATIVE:
            return base_value * (1 + self.shock_value / 100)
        else:
            return base_value + self.shock_value


@dataclass
class CurveShock:
    """Shock to a yield curve."""
    curve_name: str = ""
    shock_type: ShockType = ShockType.PARALLEL
    parallel_shift: float = 0.0  # bps
    short_end_shift: float = 0.0  # bps
    long_end_shift: float = 0.0  # bps
    pivot_point: float = 5.0  # years
    
    def apply_to_curve(self, tenors: List[float], rates: List[float]) -> List[float]:
        """Apply shock to curve rates."""
        shocked = []
        for tenor, rate in zip(tenors, rates):
            shift = self.parallel_shift / 10000
            if self.shock_type == ShockType.TWIST:
                if tenor < self.pivot_point:
                    shift += self.short_end_shift / 10000
                else:
                    shift += self.long_end_shift / 10000
            shocked.append(rate + shift)
        return shocked


@dataclass
class Scenario:
    """Market scenario for simulation or stress testing."""
    scenario_id: str = field(default_factory=lambda: f"SCN-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    description: str = ""
    scenario_type: ScenarioType = ScenarioType.STRESS
    scenario_date: date = field(default_factory=date.today)
    
    # Risk factor shocks
    ir_shocks: Dict[str, CurveShock] = field(default_factory=dict)
    fx_shocks: Dict[str, RiskFactorShock] = field(default_factory=dict)
    credit_shocks: Dict[str, RiskFactorShock] = field(default_factory=dict)
    equity_shocks: Dict[str, RiskFactorShock] = field(default_factory=dict)
    vol_shocks: Dict[str, RiskFactorShock] = field(default_factory=dict)
    commodity_shocks: Dict[str, RiskFactorShock] = field(default_factory=dict)
    
    # Metadata
    probability: float = 1.0
    severity: str = "medium"
    regulatory: bool = False
    
    def validate(self) -> bool:
        """Validate scenario."""
        return bool(self.scenario_id)
    
    def add_ir_shock(self, currency: str, shock: CurveShock) -> None:
        """Add interest rate curve shock."""
        self.ir_shocks[currency] = shock
    
    def add_fx_shock(self, pair: str, shock: RiskFactorShock) -> None:
        """Add FX rate shock."""
        self.fx_shocks[pair] = shock
    
    def add_credit_shock(self, entity: str, shock: RiskFactorShock) -> None:
        """Add credit spread shock."""
        self.credit_shocks[entity] = shock
    
    def get_shock_summary(self) -> Dict[str, int]:
        """Get summary of shocks in scenario."""
        return {
            "ir_shocks": len(self.ir_shocks),
            "fx_shocks": len(self.fx_shocks),
            "credit_shocks": len(self.credit_shocks),
            "equity_shocks": len(self.equity_shocks),
            "vol_shocks": len(self.vol_shocks),
            "commodity_shocks": len(self.commodity_shocks),
        }


@dataclass
class ScenarioSet:
    """Collection of scenarios for comprehensive stress testing."""
    set_id: str = field(default_factory=lambda: f"SCNSET-{uuid.uuid4().hex[:8].upper()}")
    name: str = ""
    scenarios: List[Scenario] = field(default_factory=list)
    
    def validate(self) -> bool:
        return bool(self.set_id)
    
    def add_scenario(self, scenario: Scenario) -> None:
        """Add a scenario to the set."""
        self.scenarios.append(scenario)
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get scenario by ID."""
        for scn in self.scenarios:
            if scn.scenario_id == scenario_id:
                return scn
        return None


@dataclass 
class SimulationPath:
    """Single simulation path for Monte Carlo."""
    path_id: int = 0
    time_grid: List[float] = field(default_factory=list)
    values: Dict[str, List[float]] = field(default_factory=dict)
    
    def get_value_at_time(self, risk_factor: str, time_index: int) -> float:
        """Get value of risk factor at time index."""
        if risk_factor in self.values:
            return self.values[risk_factor][time_index]
        return 0.0


@dataclass
class MonteCarloScenarioSet:
    """Monte Carlo generated scenarios."""
    set_id: str = field(default_factory=lambda: f"MC-{uuid.uuid4().hex[:8].upper()}")
    num_paths: int = 10000
    time_horizon: float = 5.0
    time_steps: int = 60
    seed: int = 42
    paths: List[SimulationPath] = field(default_factory=list)
    
    def validate(self) -> bool:
        return self.num_paths > 0
    
    def generate_time_grid(self) -> List[float]:
        """Generate time grid."""
        return list(np.linspace(0, self.time_horizon, self.time_steps + 1))


# Standard regulatory scenarios
REGULATORY_SCENARIOS = {
    "CCAR_SEVERELY_ADVERSE": Scenario(
        name="CCAR Severely Adverse",
        scenario_type=ScenarioType.STRESS,
        regulatory=True,
        severity="severe",
    ),
    "CCAR_ADVERSE": Scenario(
        name="CCAR Adverse", 
        scenario_type=ScenarioType.STRESS,
        regulatory=True,
        severity="adverse",
    ),
    "EBA_ADVERSE": Scenario(
        name="EBA Adverse",
        scenario_type=ScenarioType.STRESS,
        regulatory=True,
        severity="adverse",
    ),
}


__all__ = [
    "ScenarioType",
    "ShockType",
    "RiskFactorShock",
    "CurveShock",
    "Scenario",
    "ScenarioSet",
    "SimulationPath",
    "MonteCarloScenarioSet",
    "REGULATORY_SCENARIOS",
]
