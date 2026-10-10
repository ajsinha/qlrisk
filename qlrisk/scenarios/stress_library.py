"""
QLRisk - Historical Stress Scenario Library
===========================================

Stylised one-shot replays of well-known market crises, expressed per risk
class and applied to whatever risk factors the market data contains:

    equity     relative move of every equity price
    vol        relative move of every implied volatility (1.0 = vols double)
    rates      absolute move of every rate curve: a number (parallel) or (short, long) twist
    credit     relative move of every credit spread (1.0 = spreads double)
    fx_usd     relative move of XXXUSD pairs (negative = USD strengthens); USDXXX moves inversely
    fx         per-currency overrides of fx_usd, e.g. {"GBP": -0.11}
    commodity  relative move of every commodity price

Magnitudes are approximate peak-to-trough moves of the episodes, rounded; they
are illustrative calibrations, not data. Override or extend STRESS_LIBRARY.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from ..riskfactors.mapping import enumerate_risk_factors
from ..riskfactors.shocks import Shock, ShockType, twist
from ..riskfactors.taxonomy import FactorKind
from .scenario_set import ScenarioSet


@dataclass(frozen=True)
class StressDefinition:
    name: str
    description: str
    equity: float = 0.0
    vol: float = 0.0
    rates: Union[float, Tuple[float, float]] = 0.0
    credit: float = 0.0
    fx_usd: float = 0.0
    commodity: float = 0.0
    fx: Dict[str, float] = field(default_factory=dict)


STRESS_LIBRARY: Dict[str, StressDefinition] = {s.name: s for s in (
    StressDefinition("1987_black_monday", "Oct 1987 equity crash", -0.22, 1.50, -0.0050, 0.30, 0.0, -0.05),
    StressDefinition("1998_ltcm_russia", "Aug-Oct 1998 Russia default / LTCM", -0.18, 1.00, -0.0075, 1.00, 0.03, -0.10,
                     {"JPY": 0.12}),
    StressDefinition("2008_gfc_lehman", "Sep-Nov 2008 Lehman / GFC", -0.40, 2.00, (-0.0200, -0.0100), 2.00, -0.12, -0.45),
    StressDefinition("2010_euro_crisis", "Apr-Jun 2010 euro sovereign crisis", -0.15, 1.00, -0.0060, 0.60, -0.10, -0.12,
                     {"EUR": -0.14}),
    StressDefinition("2013_taper_tantrum", "May-Jun 2013 taper tantrum", -0.06, 0.40, (0.0020, 0.0110), 0.20, -0.03, -0.05),
    StressDefinition("2016_brexit", "Jun 2016 Brexit referendum", -0.06, 0.50, -0.0030, 0.20, -0.03, -0.03,
                     {"GBP": -0.11}),
    StressDefinition("2020_covid", "Feb-Mar 2020 COVID crash", -0.34, 2.50, (-0.0150, -0.0100), 1.50, -0.05, -0.55),
    StressDefinition("2022_rates_shock", "2022 inflation / rates shock", -0.22, 0.30, (0.0350, 0.0250), 0.60, -0.14, 0.20),
    StressDefinition("2023_regional_banks", "Mar 2023 SVB / regional banks", -0.08, 0.60, (-0.0120, -0.0040), 0.30, 0.0, -0.08),
)}


def stress_shocks(market_data: Any, stress: StressDefinition) -> List[Shock]:
    """Translate a stress definition into shocks on the market data's factors."""
    shape = twist(*stress.rates) if isinstance(stress.rates, tuple) else (lambda t, s=stress.rates: s)
    shocks = []
    for key in enumerate_risk_factors(market_data):
        kind, field_name = key.kind, key.field
        if kind is FactorKind.RATE:
            size = shape(key.tenor if key.tenor is not None else 1.0)
            if size:
                shocks.append(Shock(key, size, ShockType.ABSOLUTE))
        elif kind is FactorKind.SPREAD and stress.credit:
            shocks.append(Shock(key, stress.credit, ShockType.RELATIVE))
        elif kind is FactorKind.VOLATILITY and stress.vol:
            shocks.append(Shock(key, stress.vol, ShockType.RELATIVE))
        elif field_name == "equity_prices" and stress.equity:
            shocks.append(Shock(key, stress.equity, ShockType.RELATIVE))
        elif field_name == "commodity_prices" and stress.commodity:
            shocks.append(Shock(key, stress.commodity, ShockType.RELATIVE))
        elif field_name == "fx_spots" and len(key.name) == 6:
            base, quote = key.name[:3], key.name[3:]
            if quote == "USD":
                move = stress.fx.get(base, stress.fx_usd)
            elif base == "USD":
                move = 1.0 / (1.0 + stress.fx.get(quote, stress.fx_usd)) - 1.0
            else:
                move = (1 + stress.fx.get(base, stress.fx_usd)) / (1 + stress.fx.get(quote, stress.fx_usd)) - 1
            if move:
                shocks.append(Shock(key, move, ShockType.RELATIVE))
    return shocks


def historical_stress_scenarios(market_data: Any, names: Optional[Iterable[str]] = None) -> ScenarioSet:
    """ScenarioSet with one scenario per library stress (all by default)."""
    chosen = list(names) if names is not None else list(STRESS_LIBRARY)
    return ScenarioSet.from_shocks({n: stress_shocks(market_data, STRESS_LIBRARY[n]) for n in chosen},
                                   method="stress_library")


__all__ = ["StressDefinition", "STRESS_LIBRARY", "stress_shocks", "historical_stress_scenarios"]
