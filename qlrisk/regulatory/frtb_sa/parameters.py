"""
QLRisk - FRTB Standardised Approach Parameters (Basel MAR21, MAR22, MAR23)
=========================================================================

Risk weights, buckets and correlations used by the sensitivities-based
method (SBM), the default risk charge (DRC) and the residual risk add-on
(RRAO). Values follow the January 2019 Basel text (MAR, 2023 consolidation).
Simplifications are noted inline and in docs/market_risk/frtb.md.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math

# ----------------------------------------------------------------- GIRR (MAR21.41-50)
GIRR_VERTICES = (0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0, 30.0)
GIRR_RW = {0.25: 0.017, 0.5: 0.017, 1.0: 0.016, 2.0: 0.013, 3.0: 0.012,
           5.0: 0.011, 10.0: 0.011, 15.0: 0.011, 20.0: 0.011, 30.0: 0.011}
GIRR_SPECIFIED_CCY = {"EUR", "USD", "GBP", "AUD", "JPY", "SEK", "CAD"}     # RW / sqrt(2), plus domestic
GIRR_THETA = 0.03
GIRR_RHO_FLOOR = 0.40
GIRR_DIFFERENT_CURVE = 0.999
GIRR_GAMMA = 0.50
GIRR_CURVATURE_RW = 0.017            # highest prescribed delta RW, parallel shift (MAR21.98)

# Forward-curve index -> currency (override via sbm(curve_currency=...))
INDEX_CURRENCY = {
    "SOFR": "USD", "FEDFUNDS": "USD", "USD_LIBOR": "USD", "ESTR": "EUR", "EURIBOR": "EUR",
    "SONIA": "GBP", "TONA": "JPY", "TONAR": "JPY", "SARON": "CHF", "CORRA": "CAD", "AONIA": "AUD",
    "BBSW": "AUD", "STIBOR": "SEK",
}

# ----------------------------------------------------------------- CSR non-securitisation (MAR21.51-57)
CSR_VERTICES = (0.5, 1.0, 3.0, 5.0, 10.0)
CSR_RW = {1: 0.005, 2: 0.010, 3: 0.050, 4: 0.030, 5: 0.030, 6: 0.020, 7: 0.015, 8: 0.025,
          9: 0.020, 10: 0.040, 11: 0.120, 12: 0.070, 13: 0.085, 14: 0.055, 15: 0.050, 16: 0.120,
          17: 0.015, 18: 0.050}
CSR_IG_BUCKETS = set(range(1, 9)) | {17}
CSR_OTHER_BUCKET = 16
CSR_RHO_NAME, CSR_RHO_TENOR = 0.35, 0.65
CSR_INDEX_RHO_NAME = 0.80
CSR_GAMMA_RATING = 0.50
# Simplification: the MAR21.57 sector-pair table is replaced by one cross-sector value
# (same sector => 1.0). Configure via sbm(csr_sector_gamma=...).
CSR_SECTOR_GAMMA_DEFAULT = 0.20

# ----------------------------------------------------------------- Equity (MAR21.72-80)
EQ_RW = {1: 0.55, 2: 0.60, 3: 0.45, 4: 0.55, 5: 0.30, 6: 0.35, 7: 0.40, 8: 0.50,
         9: 0.70, 10: 0.50, 11: 0.70, 12: 0.15, 13: 0.25}
EQ_LARGE_EM, EQ_LARGE_ADV = {1, 2, 3, 4}, {5, 6, 7, 8}
EQ_RHO = {**{b: 0.15 for b in EQ_LARGE_EM}, **{b: 0.25 for b in EQ_LARGE_ADV},
          9: 0.075, 10: 0.125, 12: 0.80, 13: 0.80}
EQ_OTHER_BUCKET = 11


def eq_gamma(b: int, c: int) -> float:
    if EQ_OTHER_BUCKET in (b, c):
        return 0.0
    if {b, c} == {12, 13}:
        return 0.75
    if b in (12, 13) or c in (12, 13):
        return 0.45
    return 0.15


# ----------------------------------------------------------------- Commodity (MAR21.82-85)
CM_RW = {1: 0.30, 2: 0.35, 3: 0.60, 4: 0.80, 5: 0.40, 6: 0.45, 7: 0.20, 8: 0.35, 9: 0.25, 10: 0.35, 11: 0.50}
CM_RHO = {1: 0.55, 2: 0.95, 3: 0.40, 4: 0.80, 5: 0.60, 6: 0.65, 7: 0.55, 8: 0.45, 9: 0.15, 10: 0.40, 11: 0.15}
CM_GAMMA, CM_OTHER_BUCKET = 0.20, 11
COMMODITY_BUCKET = {"WTI": 2, "BRENT": 2, "CRUDE_OIL_WTI": 2, "HEATING_OIL": 2, "COAL": 1,
                    "POWER": 3, "ELECTRICITY": 3, "FREIGHT": 4, "COPPER": 5, "ALUMINIUM": 5, "ALUMINUM": 5,
                    "NATGAS": 6, "NATURAL_GAS": 6, "GOLD": 7, "SILVER": 7, "PLATINUM": 7,
                    "CORN": 8, "WHEAT": 8, "SOYBEANS": 8, "COFFEE": 9, "SUGAR": 9, "COTTON": 9, "CATTLE": 10}

# ----------------------------------------------------------------- FX (MAR21.86-89)
FX_RW = 0.15
FX_LIQUID_VS_USD = {"EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "MXN", "CNY", "NZD", "RUB", "HKD", "SGD",
                    "TRY", "KRW", "SEK", "ZAR", "INR", "NOK", "BRL"}           # RW / sqrt(2) (MAR21.88)
FX_GAMMA = 0.60

# ----------------------------------------------------------------- Vega (MAR21.92-95)
VEGA_MATURITIES = (0.5, 1.0, 3.0, 5.0, 10.0)
VEGA_ALPHA = 0.01
LIQUIDITY_HORIZON = {"IR": 60, "CR": 120, "EQ_LARGE": 20, "EQ_SMALL": 60, "CM": 120, "FX": 40}


def vega_rw(key: str) -> float:
    """RW_sigma = min(0.55 * sqrt(LH / 10), 100%)."""
    return min(0.55 * math.sqrt(LIQUIDITY_HORIZON[key] / 10.0), 1.0)


# ----------------------------------------------------------------- Correlation scenarios (MAR21.6)
def scenario_rho(rho: float, scenario: str) -> float:
    if scenario == "medium":
        return rho
    if scenario == "high":
        return min(1.25 * rho, 1.0)
    if scenario == "low":
        return max(2.0 * rho - 1.0, 0.75 * rho)
    raise ValueError(scenario)


# ----------------------------------------------------------------- DRC (MAR22)
DRC_RW = {"AAA": 0.005, "AA": 0.02, "A": 0.03, "BBB": 0.06, "BB": 0.15, "B": 0.30, "CCC": 0.50,
          "UNRATED": 0.15, "DEFAULTED": 1.00}
DRC_LGD = {"SENIOR": 0.75, "NON_SENIOR": 1.00, "EQUITY": 1.00, "COVERED": 0.25, "SOVEREIGN": 0.75}

# ----------------------------------------------------------------- RRAO (MAR23)
RRAO_EXOTIC, RRAO_OTHER = 0.01, 0.001

__all__ = [n for n in dir() if n.isupper() or n in ("eq_gamma", "vega_rw", "scenario_rho")]
