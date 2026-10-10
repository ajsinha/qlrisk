"""
QLRisk - CVA Risk Capital: Basic Approach (BA-CVA, MAR50.12-26)
===============================================================

Reduced version:
    SCVA_c    = RW_c / alpha * sum_NS M_NS * EAD_NS * DF_NS,   DF = (1 - exp(-0.05 M)) / (0.05 M), alpha = 1.4
    K_reduced = sqrt( (rho * sum SCVA_c)^2 + (1 - rho^2) * sum SCVA_c^2 ),  rho = 50%
Full version (with eligible hedges):
    SNH_c = sum_h r_hc * RW_h * M_h * B_h * DF_h          HMA_c = sum_h (1 - r_hc^2) * (RW_h M_h B_h DF_h)^2
    IH    = sum_i RW_i * M_i * B_i * DF_i  (index RW = 0.7 x sector RW)
    K_hedged = sqrt( (rho * sum(SCVA_c - SNH_c) - IH)^2 + (1 - rho^2) * sum(SCVA_c - SNH_c)^2 + sum HMA_c )
    K_full = beta * K_reduced + (1 - beta) * K_hedged,  beta = 0.25
Capital = DS * K, DS = 0.65.

EAD per netting set typically comes from SA-CCR (qlrisk.regulatory.saccr).
SA-CVA is not implemented yet.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

ALPHA, RHO, BETA, DS = 1.4, 0.5, 0.25, 0.65
# (investment grade, high yield / unrated) risk weights by sector (MAR50.16)
BA_CVA_RW = {
    "sovereign": (0.005, 0.020), "local_government": (0.010, 0.040), "financial": (0.050, 0.120),
    "basic_materials": (0.030, 0.070), "consumer": (0.030, 0.085), "technology": (0.020, 0.055),
    "health": (0.015, 0.050), "other": (0.050, 0.120),
}


def supervisory_df(maturity: float) -> float:
    return 1.0 if maturity <= 0 else (1 - math.exp(-0.05 * maturity)) / (0.05 * maturity)


@dataclass
class CVAHedge:
    """Single-name CDS hedge (correlation r with the counterparty: 1.0 same name, 0.8 related, 0.5 same sector)."""
    notional: float
    maturity: float
    correlation: float = 1.0


@dataclass
class CVACounterparty:
    name: str
    sector: str = "other"
    investment_grade: bool = True
    netting_sets: List[Tuple[float, float]] = field(default_factory=list)   # (EAD, effective maturity)
    hedges: List[CVAHedge] = field(default_factory=list)
    
    @property
    def rw(self) -> float:
        ig, hy = BA_CVA_RW[self.sector]
        return ig if self.investment_grade else hy
    
    @property
    def scva(self) -> float:
        return self.rw / ALPHA * sum(m * ead * supervisory_df(m) for ead, m in self.netting_sets)


@dataclass
class CVAIndexHedge:
    notional: float
    maturity: float
    sector: str = "other"
    investment_grade: bool = True
    
    @property
    def weighted(self) -> float:
        ig, hy = BA_CVA_RW[self.sector]
        return 0.7 * (ig if self.investment_grade else hy) * self.maturity * self.notional * supervisory_df(self.maturity)


def ba_cva(counterparties: Sequence[CVACounterparty], index_hedges: Sequence[CVAIndexHedge] = ()) -> Dict[str, float]:
    """BA-CVA capital; uses the full version when any hedge is present."""
    scva = {c.name: c.scva for c in counterparties}
    k_reduced = math.sqrt((RHO * sum(scva.values())) ** 2 + (1 - RHO ** 2) * sum(v * v for v in scva.values()))
    hedged = any(c.hedges for c in counterparties) or bool(index_hedges)
    out = {"k_reduced": k_reduced, "capital_reduced": DS * k_reduced, "scva": scva}
    if not hedged:
        out["capital"] = out["capital_reduced"]
        return out
    net, hma = {}, 0.0
    for c in counterparties:
        snh = sum(h.correlation * c.rw * h.maturity * h.notional * supervisory_df(h.maturity) for h in c.hedges)
        hma += sum((1 - h.correlation ** 2) * (c.rw * h.maturity * h.notional * supervisory_df(h.maturity)) ** 2
                   for h in c.hedges)
        net[c.name] = scva[c.name] - snh
    ih = sum(i.weighted for i in index_hedges)
    k_hedged = math.sqrt((RHO * sum(net.values()) - ih) ** 2 + (1 - RHO ** 2) * sum(v * v for v in net.values()) + hma)
    k_full = BETA * k_reduced + (1 - BETA) * k_hedged
    out.update({"k_hedged": k_hedged, "k_full": k_full, "capital": DS * k_full})
    return out


__all__ = ["BA_CVA_RW", "CVACounterparty", "CVAHedge", "CVAIndexHedge", "ba_cva", "supervisory_df"]
