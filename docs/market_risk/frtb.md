# QLRisk - Regulatory Market Risk Capital v2.2.0

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
```

---

Package `qlrisk.regulatory` covers FRTB SA (MAR21–23), FRTB IMA (MAR31/33), Basel 2.5, BA-CVA (MAR50) and
SA-CCR (a re-export). Parameters follow the Basel MAR text and live in `regulatory/frtb_sa/parameters.py`.
**Simplifications are listed explicitly below.** Validate against your regulator's implementation before
using any figure for reporting.

## 1. FRTB SA: Sensitivities-Based Method (`frtb_sa.sbm`)

### From qlrisk sensitivities to FRTB sensitivities

| Risk class | Source factor | s_k | Bucket | RW |
|-----------|--------------|-----|--------|----|
| GIRR delta | `discount_curve`, `forward_curves`, `reference_rates` | DV01 / 0.0001, re-bucketed onto the 10 GIRR vertices | Currency (index → currency map; discounting = reporting currency) | MAR21.42, ÷ √2 for EUR, USD, GBP, AUD, JPY, SEK, CAD and the reporting currency |
| CSR delta | `credit_curves` | CS01 / 0.0001 on 0.5/1/3/5/10y | `credit_buckets` (default 16, "other sector") | MAR21.53 |
| EQ delta | `equity_prices` | ΔPV(+1%) / 0.01 | `equity_buckets` (default 11, "other") | MAR21.77 |
| CM delta | `commodity_prices` | ΔPV(+1%) / 0.01 | `COMMODITY_BUCKET` / `commodity_buckets` (default 11) | MAR21.82 |
| FX delta | `fx_spots` | ΔPV(+1%) / 0.01 per non-reporting currency (USDxxx sign-flipped; crosses split between both legs) | Currency | 15%, ÷ √2 for liquid pairs against USD |
| Vega (all classes) | `volatility_surfaces` | ∂PV/∂σ × σ, re-bucketed onto 0.5/1/3/5/10y | From `vol_underlyings`, or by parsing `<underlying>_vol` | min(0.55 √(LH/10), 1) |

Dividend curves, bond prices and ad-hoc scalar factors have no FRTB delta factor. They are reported in `skipped_factors`.

### Aggregation

- **Within a bucket:** K_b = √max(0, ΣΣ ρ WSₖ WSₗ). The intra-bucket correlations are:
  - GIRR: max(e^{−3%·|Δt|/min t}, 40%), × 99.9% across curves.
  - CSR: name (35%; 80% for indices) × tenor (65%).
  - EQ: 15%, 25%, 7.5% or 12.5% by size and region, and 80% for indices.
  - CM: per bucket.
  - Vega: × e^{−1%·|ΔT|/min T}.
- **"Other" buckets:** CSR bucket 16 and EQ bucket 11 use Σ|WS|, with no diversification.
- **Across buckets:** √(Σ K_b² + ΣΣ γ S_b S_c), where S_b = ΣWS is clipped to ±K_b, with the unclipped fallback when the radicand is negative. The cross-bucket correlations γ are:
  - GIRR 50% and FX 60%.
  - EQ: 15%, 75% between buckets 12 and 13, 45% between an index bucket and the others, and 0 for bucket 11.
  - CM 20%.
  - CSR: γ_rating × γ_sector.
- **Curvature:** CVR± = −Σ[V(x ± RW) − V(x) ∓ RW·s] by full revaluation. The shocks are:
  - GIRR: parallel ±1.7% on all curves of the currency.
  - CSR: ±the bucket RW on the issuer curve.
  - EQ and CM: relative ±RW.
  - FX: relative ±15% on every pair containing the currency.

  CVRs aggregate with ρ² and γ², with ψ = 0 when both terms are negative.
- **Correlation scenarios:** each charge is computed under low (max(2ρ−1, 0.75ρ)), medium and high (min(1.25ρ, 1)) correlations. The capital is the maximum total.

## 2. FRTB SA: DRC (`frtb_sa.drc`) and RRAO (`frtb_sa.rrao`)

- **Jump-to-default:** JTD = LGD × notional + (MV − notional), floored at 0 for longs and capped at 0 for shorts, then scaled by min(max(M, 0.25), 1).
- **LGD:** senior 75%, non-senior and equity 100%, covered 25%.
- **Netting and capital:** JTDs net per obligor. DRC_b = max(Σ RW·JTD_long − HBR·Σ RW·|JTD_short|, 0), with RW from AAA 0.5% to CCC 50% (unrated 15%).
- **`drc_positions_from_trades`** maps bonds (via `issuer`) to longs, bought CDS protection (via `reference`) to shorts, sold protection to longs, and cash equities to long equity.
- **RRAO:** 1.0% of notional for exotic underlyings and 0.1% for other residual risks. Barriers, digitals and variance swaps fall into the 0.1% class by default.

## 3. FRTB IMA (`frtb_ima`)

| Component | Implementation |
|-----------|----------------|
| Liquidity horizons | `default_liquidity_horizon` maps each factor to MAR33.12 horizons: 10/20 for IR by currency; 40, or 60 for HY, for credit; 10, or 20 for small caps, for equity; 10/20 for FX; 20/60 for commodities; vols at 20–120 |
| LH-adjusted ES | ES_T(P)² + Σⱼ (ES_T(P,j)·√((LHⱼ−LHⱼ₋₁)/10))², using 10-day overlapping returns |
| Stress calibration | ES_R,S × max(ES_F,C / ES_R,C, 1); the stress window maximises the reduced-set ES |
| IMCC | 0.5·ES_total + 0.5·Σ ES_risk class |
| RFET | ≥ 24 observations in 12 months with ≥ 4 in every 90-day period, or ≥ 100 observations |
| SES | Per-NMRF stressed ES × √(LH/10), aggregated as √Σ SES²_idio + √((0.6 Σ SES)² + 0.64 Σ SES²) |
| Capital | max(IMCC + SES, m_c·avg60(IMCC) + avg60(SES)) + DRC |
| IMA DRC | 1-year 99.9% loss from a Gaussian copula; PD from the rating table; JTD from `DRCPosition` |

## 4. Basel 2.5 (`basel25`)

capital = max(VaR, m·avg60 VaR) + max(SVaR, m·avg60 SVaR), with m = 3 + the backtesting plus factor.

## 5. BA-CVA (`cva_capital`)

- **Reduced version:** K_reduced = √((ρ ΣSCVA)² + (1−ρ²) ΣSCVA²), with SCVA_c = RW_c/1.4 · Σ M·EAD·DF and ρ = 50%.
- **Full version:** applies single-name hedges (r = 100%, 80% or 50%) and index hedges (0.7 × RW); then K = 0.25·K_reduced + 0.75·K_hedged.
- **Capital:** 0.65 × K.

## Simplifications and gaps

| Area | Simplification |
|------|----------------|
| CSR cross-bucket | The MAR21.57 sector table is replaced by one cross-sector γ (default 20%, `csr_sector_gamma=`); γ_rating is applied exactly |
| CSR | Securitisation (CTP / non-CTP) and the bond–CDS basis are not modelled |
| GIRR | No inflation or cross-currency-basis factors |
| CM | Delta by commodity only (no tenor or location dimensions) |
| Curvature | FX and EQ use the delta RW without the optional scalar; GIRR uses 1.7% |
| DRC | Netting ignores seniority; securitisation DRC is not modelled |
| IMA | One stress window is shared across IMCC components, and SES is ES-based |
| IMA DRC | One systematic factor (Basel requires two) and fixed correlation |
| Inputs | Bucket maps, ratings and vol underlyings must be supplied; unmapped names default to the conservative "other" buckets |
| SA-CVA | **Not implemented**; BA-CVA only |

## Validation (`tests/test_regulatory.py`)

- **Correlation scenarios:** the low, medium and high scaling is reproduced exactly.
- **GIRR bucket aggregation:** the two-tenor case matches the hand formula.
- **Cross-bucket and "other" buckets:** FX offsets aggregate with γ = 60%, and EQ bucket 11 sums |WS|.
- **Curvature sign:** a long option has 0 curvature charge and a short option a positive one.
- **DRC:** JTD, maturity scaling, obligor netting and the HBR all match hand calculations.
- **RRAO:** the 0.1% and 1% rates apply.
- **IMA:** the LH cascade gives √6 × ES when every horizon is 60 days; RFET passes and fails the expected cases; the capital formula is exact; and the single-obligor DRC equals its JTD.
- **Basel 2.5 and BA-CVA:** both match hand calculations, and hedges reduce BA-CVA.

---

*QLRisk v2.2.0 — Every risk. One engine. | Copyright © 2025-2030 Ashutosh Sinha*
