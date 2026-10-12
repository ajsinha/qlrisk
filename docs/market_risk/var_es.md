# QLRisk - VaR and Expected Shortfall Methodology v2.4.0

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
```

---

## Conventions

- **P&L**: gains are positive. **VaR and ES are positive losses.**
- α = 1 − confidence. Scenario probabilities pᵢ are equal unless weights are supplied (age weighting).

## Definitions (`calculator/python/var_calculators.py`)

Sort scenario P&L ascending (worst first) with probabilities pᵢ, and let Cₖ be their running sum.

| Measure | Formula |
|---------|---------|
| VaR | −P&L₍ₖ₎ for the first k with Cₖ ≥ α. With 250 scenarios at 99%, this is the 3rd-worst loss. |
| ES | −(1/α) Σᵢ mᵢ P&Lᵢ, where mᵢ = min(Cᵢ, α) − Cᵢ₋₁ is the tail mass, with the boundary scenario weighted fractionally |
| Parametric VaR | −(μ + z_cf σ), z = Φ⁻¹(α), Cornish-Fisher z_cf when skew and excess kurtosis are given |
| Parametric ES | −(μ − σ φ(z)/α) |

## Scenario generation (`qlrisk.scenarios`)

| Method | Construction |
|--------|-------------|
| Historical | Last *N* one-day returns, or h-day returns (overlapping or not), or 1-day × √h |
| Age-weighted (BRW) | pᵢ ∝ λ^(age), with λ = 0.99 typical |
| Filtered historical | rₜ × σ_today / σₜ, using RiskMetrics EWMA volatility (λ = 0.94) per factor |
| Monte Carlo | Zero-mean multivariate normal or Student-t with the sample or EWMA covariance of 1-day returns, × √h |
| Hypothetical | `ScenarioSet.from_shocks({...})` |

Returns follow the factor conventions: absolute for rates and spreads, log for prices, spots and vols.
They are applied to **today's** market data.

## Revaluation (`qlrisk.pnl`)

- **Full revaluation**: P&L = PV(shocked market) − PV(base), for every trade and scenario, converted to the reporting currency in each scenario.
- **Taylor**: Σ δᵢ Δxᵢ + ½ Σ Γᵢ Δxᵢ², using natural-unit sensitivities from `SensitivityEngine` (diagonal gamma). Here Δx = r for absolute returns and x(eʳ − 1) for log returns.

## Parametric delta-normal

Exposure eⱼ = ∂PV/∂xⱼ for absolute-return factors and ∂PV/∂xⱼ · xⱼ for log or relative ones.
σ_P = √(eᵀ C e · h), with C the sample or EWMA covariance of 1-day returns.

## Decomposition (`PnLMatrix`)

| Measure | Definition | Adds up to the total? |
|---------|-----------|-----------------------|
| Component ES | −(1/α) Σ tail mass × trade P&L | Yes (Euler) |
| Component VaR | −trade P&L in the VaR scenario | Yes |
| Parametric component | z · e_tradeᵀ C e · h / σ_P | Yes |
| Incremental | Total − total without the trade | No |
| Standalone | The trade's own VaR or ES | No; the shortfall from the total is the diversification benefit |

`PnLMatrix.group(mapping)` re-aggregates trades into desks, books or asset classes before measuring.

## Stressed VaR

1. Compute 1-day Taylor P&L over the whole history.
2. Slide a 250-day window and pick the one with the maximum VaR (or ES).
3. Revalue that window in full, scaled by √h (10 days by default).

The result's `metadata` reports the window dates.

## Validation (`tests/test_var.py`)

- VaR and ES definitions are checked on known vectors.
- Weighted and unweighted results agree when the weights are equal.
- The parametric constants are correct: 2.326 for VaR at 99% and 2.338 for ES at 97.5%.
- Euler contributions sum to the total.
- Full and Taylor VaR agree within 2% for a linear book.
- Parametric VaR agrees with Monte Carlo delta VaR within 3%, and scales with √h.
- The stressed window overlaps the injected stress, and SVaR is larger than normal VaR.

---

*QLRisk v2.4.0 — Every risk. One engine. | Copyright © 2025-2030 Ashutosh Sinha*
