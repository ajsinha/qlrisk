# QLRisk - Backtesting, P&L Attribution and Stress Testing v2.2.0

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
```

---

## VaR backtesting (`qlrisk.backtesting.backtest_var`)

An exception occurs on day t when the P&L is below −VaRₜ. With x exceptions in n days and p = 1 − confidence:

| Test | Statistic | Distribution |
|------|-----------|--------------|
| Kupiec POF | −2 ln[(1−p)ⁿ⁻ˣ pˣ / (1−p̂)ⁿ⁻ˣ p̂ˣ], p̂ = x/n | χ²(1) |
| Christoffersen independence | Markov-chain likelihood ratio on the transitions n₀₀, n₀₁, n₁₀, n₁₁ | χ²(1) |
| Conditional coverage | LR_POF + LR_IND | χ²(2) |
| Basel traffic light | Cumulative binomial P(X ≤ x): green < 95%, yellow < 99.99%, red otherwise | 250 days at 99%: green 0–4, yellow 5–9, red 10+ |

The multiplier is 3 plus the plus factor: 0.40, 0.50, 0.65, 0.75 and 0.85 for 5 to 9 exceptions, and 1.0 in the red zone.
The count is scaled to a 250-day equivalent.

## ES backtesting (`backtest_es`, Acerbi-Székely 2014)

Z₁ = Σ Xₜ Iₜ / ESₜ / N_T + 1, and Z₂ = Σ Xₜ Iₜ / (T α ESₜ) + 1. Both equal 0 under a correct model, and negative values mean ES is underestimated.
Z₂ zones at α = 2.5% are green (> −0.70), yellow (> −1.80) and red otherwise.

## Engine backtest (`MarketRiskEngine.backtest`)

The engine treats the portfolio as static. On each test day:

- **Forecasts:** VaR and ES come from the previous `lookback` days of risk-theoretical P&L (Taylor, using today's sensitivities).
- **Realised P&L:** hypothetical P&L from full revaluation between the reconstructed market data of consecutive days.
- **Output:** the VaR, ES and PLA test results, plus the daily series.

## P&L explain (`qlrisk.pnl.explain_pnl`)

Actual = PV(end) − PV(start) = θ + Σ_factors (δ Δx + ½ Γ Δx²) + unexplained.

- θ is the move from rolling the valuation date with the market unchanged.
- Sensitivities are taken at the start.
- Results are reported per trade, per risk class and per factor.

## FRTB P&L attribution test (`pla_test`, MAR32)

The test compares the Spearman correlation and the Kolmogorov-Smirnov distance between HPL and RTPL:

| Zone | Rule |
|------|------|
| Green | ρ > 0.80 and KS < 0.09 |
| Red | ρ < 0.70 or KS > 0.12 |
| Amber | Otherwise |

## Stress library (`qlrisk.scenarios.STRESS_LIBRARY`)

Each scenario is a stylised one-shot move per risk class: equity (relative), vols (relative), rates (parallel or
twist), credit spreads (relative), USD against other currencies with per-currency overrides, and commodities. The
magnitudes are rounded approximations of each episode, **for illustration**. Calibrate them to your own data for production use.

| Scenario | Equity | Vol | Rates | Credit | USD (XXXUSD) | Commodity |
|----------|--------|-----|-------|--------|--------------|-----------|
| 1987 Black Monday | −22% | +150% | −50bp | +30% | 0 | −5% |
| 1998 LTCM / Russia | −18% | +100% | −75bp | +100% | +3% (JPY +12%) | −10% |
| 2008 GFC / Lehman | −40% | +200% | −200/−100bp | +200% | −12% | −45% |
| 2010 Euro crisis | −15% | +100% | −60bp | +60% | −10% (EUR −14%) | −12% |
| 2013 Taper tantrum | −6% | +40% | +20/+110bp | +20% | −3% | −5% |
| 2016 Brexit | −6% | +50% | −30bp | +20% | −3% (GBP −11%) | −3% |
| 2020 COVID | −34% | +250% | −150/−100bp | +150% | −5% | −55% |
| 2022 Rates shock | −22% | +30% | +350/+250bp | +60% | −14% | +20% |
| 2023 Regional banks | −8% | +60% | −120/−40bp | +30% | 0 | −8% |

In the rates column, "a/b" is a twist: a at 2Y and below, b at 10Y and above, linear in between.

## Reverse stress test (`reverse_stress_test`)

Under the delta approximation P&L = eᵀr with return covariance C, the minimum-Mahalanobis move that loses L
is r* = −L C e / (eᵀ C e), at a distance of L / √(eᵀCe) one-day sigmas. A full-revaluation root search then
scales r* until the actual loss is exactly L. The result reports the largest factor moves in units of their own sigma.

## Liquidity-adjusted VaR (`calculator/python/liquidity_var.py`)

LVaR = VaR × √(liquidity horizon) + Σ ½ |position value| × proportional bid-ask spread.

## Validation (`tests/test_validation.py`)

- The Basel zones and multipliers are reproduced.
- Kupiec separates a correct model from an undersized one; Christoffersen detects clustered exceptions.
- A correct model passes and an undersized one fails, for both VaR and ES.
- The PLA test gives green for a near-identical series and red for an unrelated one.
- P&L explain leaves less than 2% unexplained.
- The stress-library signs are correct, and the reverse stress test hits its target to 0.1%.
- The engine backtest runs end to end.

---

*QLRisk v2.2.0 — Every risk. One engine. | Copyright © 2025-2030 Ashutosh Sinha*
