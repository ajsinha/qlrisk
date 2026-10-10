"""
QLRisk - FRTB Standardised Approach Capital
===========================================

    result = frtb_sa_capital(trades, market_data, reporting_currency="USD",
                             equity_buckets={"SPX": 12}, credit_buckets={"ACME": 4},
                             ratings={"ACME": "BBB"})
    result.total = result.sbm.total + result.drc.total + result.rrao["total"]

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from ...sensitivities.engine import SensitivityEngine
from . import parameters as p
from .drc import DRCResult, drc_charge, drc_positions_from_trades
from .rrao import rrao_charge
from .sbm import SBMResult, frtb_sensitivities, sbm_capital


@dataclass
class FRTBSAResult:
    total: float
    sbm: SBMResult
    drc: DRCResult
    rrao: Dict[str, Any]
    
    def summary(self) -> Dict[str, float]:
        out = {f"{rc}_{rt}": v for (rc, rt), v in self.sbm.by_component.items()}
        out.update({"SBM": self.sbm.total, "DRC": self.drc.total, "RRAO": self.rrao["total"], "TOTAL": self.total})
        return out


def frtb_sa_capital(
    trades: Sequence[Any],
    market_data: Any,
    reporting_currency: str = "USD",
    curve_currency: Optional[Mapping[str, str]] = None,
    credit_buckets: Optional[Mapping[str, int]] = None,
    equity_buckets: Optional[Mapping[str, int]] = None,
    commodity_buckets: Optional[Mapping[str, int]] = None,
    vol_underlyings: Optional[Mapping[str, str]] = None,
    ratings: Optional[Mapping[str, str]] = None,
    seniority: Optional[Mapping[str, str]] = None,
    exotic: Iterable[str] = (),
    other_residual: Iterable[str] = (),
    csr_sector_gamma: float = p.CSR_SECTOR_GAMMA_DEFAULT,
    include_curvature: bool = True,
) -> FRTBSAResult:
    """Full FRTB SA capital: SBM (delta, vega, curvature) + DRC (non-securitisation) + RRAO."""
    trades = list(trades)
    sens = SensitivityEngine().compute(trades, market_data, reporting_currency=reporting_currency)
    fs, skipped = frtb_sensitivities(sens, market_data, reporting_currency, curve_currency, credit_buckets,
                                     equity_buckets, commodity_buckets, vol_underlyings)
    sbm = sbm_capital(fs, trades if include_curvature else None, market_data if include_curvature else None,
                      reporting_currency, curve_currency, credit_buckets, csr_sector_gamma, skipped)
    drc = drc_charge(drc_positions_from_trades(trades, market_data, ratings, seniority))
    rrao = rrao_charge(trades, exotic, other_residual)
    return FRTBSAResult(sbm.total + drc.total + rrao["total"], sbm, drc, rrao)


__all__ = ["FRTBSAResult", "frtb_sa_capital"]
