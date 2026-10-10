# QLRisk - Mathematical Formulas Documentation v2.3.1

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

---

## Table of Contents

1. [Core Credit Risk Metrics](#1-core-credit-risk-metrics)
2. [Exposure Measurement Metrics](#2-exposure-measurement-metrics)
3. [Advanced Pricing and Capital Metrics](#3-advanced-pricing-and-capital-metrics)
4. [Stochastic Processes](#4-stochastic-processes)
5. [Product Valuations](#5-product-valuations)
6. [Stress Testing Methodologies](#6-stress-testing-methodologies)

---

## 1. Core Credit Risk Metrics

### 1.1 Probability of Default (PD)

The probability that a counterparty will default over a specified time horizon.

**Point-in-Time (PIT) PD:**
$$PD_{PIT} = \frac{\text{Number of Defaults}}{\text{Number of Exposures}}$$

**Through-the-Cycle (TTC) PD:**
$$PD_{TTC} = \frac{1}{T} \sum_{t=1}^{T} PD_t$$

**Merton Model (Structural Approach):**
$$PD = N\left(-\frac{\ln(V_0/D) + (\mu - \sigma^2/2)T}{\sigma\sqrt{T}}\right)$$

Where:
- $V_0$ = Current asset value
- $D$ = Debt (default barrier)
- $\mu$ = Asset drift rate
- $\sigma$ = Asset volatility
- $T$ = Time horizon
- $N(\cdot)$ = Standard normal CDF

**Hazard Rate Approach:**
$$PD(t) = 1 - e^{-\lambda t}$$

**Cumulative PD from Marginal PD:**
$$PD_{cum}(T) = 1 - \prod_{t=1}^{T}(1 - PD_t)$$

**Survival Probability:**
$$S(t) = 1 - PD(t) = e^{-\lambda t}$$

### 1.2 Loss Given Default (LGD)

The expected loss as a percentage of exposure if default occurs.

**Basic LGD:**
$$LGD = 1 - \text{Recovery Rate}$$

**Collateralized LGD:**
$$LGD = \max\left(0, 1 - \frac{C \times (1 - H)}{EAD}\right)$$

Where:
- $C$ = Collateral value
- $H$ = Haircut percentage
- $EAD$ = Exposure at Default

**Workout LGD:**
$$LGD = \frac{EAD - PV(\text{Recoveries}) + PV(\text{Costs})}{EAD}$$

**Downturn LGD (Basel):**
$$LGD_{downturn} = 0.08 + 0.92 \times LGD_{base}$$

### 1.3 Exposure at Default (EAD)

The total value of exposure at the time of default.

**On-Balance Sheet:**
$$EAD = \text{Outstanding Balance}$$

**Off-Balance Sheet:**
$$EAD = \text{Drawn Amount} + CCF \times \text{Undrawn Commitment}$$

Where:
- $CCF$ = Credit Conversion Factor

**Derivatives (SA-CCR):**
$$EAD = \alpha \times (RC + PFE)$$

Where:
- $\alpha$ = 1.4 (regulatory multiplier)
- $RC$ = Replacement Cost
- $PFE$ = Potential Future Exposure

**Net EAD with Collateral:**
$$EAD_{net} = \max(0, EAD_{gross} - C)$$

### 1.4 Expected Loss (EL)

The average loss expected over a specific period.

**Basic Formula:**
$$EL = PD \times LGD \times EAD$$

**Time-Weighted EL:**
$$EL = \int_0^T PD(t) \times LGD(t) \times EE(t) \, dt$$

**Portfolio EL:**
$$EL_{portfolio} = \sum_{i=1}^{n} PD_i \times LGD_i \times EAD_i$$

---

## 2. Exposure Measurement Metrics

### 2.1 Current Exposure (CE)

The present replacement cost of transactions.

**Gross CE:**
$$CE_{gross} = \max(0, V)$$

Where $V$ = Mark-to-Market value

**Net CE (with netting):**
$$CE_{net} = \max\left(0, \sum_{i \in \text{netting set}} V_i\right)$$

**Net CE (with collateral):**
$$CE_{net,coll} = \max(0, CE_{net} - C)$$

### 2.2 Potential Future Exposure (PFE)

Maximum exposure at a future date at a given confidence level.

**Monte Carlo PFE:**
$$PFE_\alpha(t) = \text{Quantile}_\alpha\left(\max(0, V(t))\right)$$

**Parametric PFE (Normal):**
$$PFE_\alpha(t) = EE(t) + \Phi^{-1}(\alpha) \times \sigma(t)$$

Where:
- $\alpha$ = Confidence level (e.g., 0.95 or 0.99)
- $\Phi^{-1}$ = Inverse standard normal CDF
- $\sigma(t)$ = Standard deviation of exposure at time $t$

**Add-On Approach (Regulatory):**
$$PFE = \text{Notional} \times \text{Supervisory Factor} \times \text{Maturity Factor}$$

Maturity Factor:
$$MF = \sqrt{\min(M, 1)}$$

### 2.3 Expected Exposure (EE)

The average exposure expected at a future date.

**Monte Carlo EE:**
$$EE(t) = \mathbb{E}[\max(0, V(t))]$$

**Time-Averaged EE:**
$$\overline{EE} = \frac{1}{T} \int_0^T EE(t) \, dt$$

**Discretized EE:**
$$\overline{EE} = \frac{1}{n} \sum_{i=1}^{n} EE(t_i)$$

### 2.4 Effective Expected Exposure (EEE)

Non-decreasing EE to account for rollover risk.

$$EEE(t) = \max_{s \leq t} EE(s)$$

**Effective EPE:**
$$EPE_{eff} = \frac{1}{T} \int_0^T EEE(t) \, dt$$

### 2.5 Peak Exposure

The maximum exposure over the life of a transaction.

**Simulated Peak:**
$$\text{Peak} = \max_{t \in [0,T]} \text{Exposure}(t)$$

**Parametric Peak Time (approximation):**
$$t^* = \frac{T}{1 + \sigma\sqrt{T}}$$

**Parametric Peak PFE:**
$$\text{Peak PFE} \approx S_0 \times \exp\left(\mu t^* + \sigma\sqrt{t^*} \times \Phi^{-1}(\alpha)\right)$$

### 2.6 Stressed Exposure

Exposure under stress scenarios.

**Sensitivity-Based Stress:**
$$\text{Stressed Exposure} = \text{Base Exposure} + \sum_i \text{Sensitivity}_i \times \text{Shock}_i$$

**Historical Stress:**
$$\text{Stressed Exposure} = V(\text{Stressed Market Data})$$

---

## 3. Advanced Pricing and Capital Metrics

### 3.1 Credit Valuation Adjustment (CVA)

The market price of counterparty credit risk.

**Unilateral CVA:**
$$CVA = (1 - R) \int_0^T EE(t) \times \lambda(t) \times e^{-\int_0^t r(s) + \lambda(s) ds} \, dt$$

Where:
- $R$ = Recovery rate
- $\lambda(t)$ = Hazard rate at time $t$
- $r(s)$ = Risk-free rate

**Discretized CVA:**
$$CVA = (1 - R) \sum_{i=1}^{n} EE(t_i) \times [S(t_{i-1}) - S(t_i)] \times DF(t_i)$$

Where:
- $S(t)$ = Survival probability
- $DF(t)$ = Discount factor

**CVA with Wrong-Way Risk:**
$$CVA_{WWR} = CVA_{base} \times (1 + \rho_{WWR} \times \text{WWR Factor})$$

**Bilateral CVA (with DVA):**
$$BCVA = CVA - DVA$$

$$DVA = (1 - R_{own}) \int_0^T NEE(t) \times \lambda_{own}(t) \times e^{-\int_0^t r(s) ds} \, dt$$

### 3.2 Economic Capital (EC)

Capital required to cover unexpected losses.

**VaR-based EC:**
$$EC = VaR_\alpha(L) - EL$$

Where:
- $VaR_\alpha$ = Value at Risk at confidence level $\alpha$
- $L$ = Loss distribution

**Single-Factor Vasicek Model:**
$$EC = EAD \times LGD \times \left[N\left(\frac{N^{-1}(PD) + \sqrt{\rho} \times N^{-1}(\alpha)}{\sqrt{1-\rho}}\right) - PD\right]$$

Where:
- $\rho$ = Asset correlation
- $\alpha$ = Confidence level (e.g., 0.999)

**Portfolio EC:**
$$EC_{portfolio} = \sqrt{\sum_{i,j} EC_i \times EC_j \times \rho_{ij}}$$

### 3.3 Risk-Adjusted Return on Capital (RAROC)

Profitability relative to risk capital.

**Basic RAROC:**
$$RAROC = \frac{\text{Risk-Adjusted Revenue} - \text{Expected Loss}}{\text{Economic Capital}}$$

**Expanded RAROC:**
$$RAROC = \frac{\text{Revenue} - \text{Funding Cost} - \text{Operating Cost} - EL}{EC}$$

**Target RAROC:**
$$\text{Hurdle Rate} = r_f + \beta \times (\mathbb{E}[r_m] - r_f)$$

### 3.4 Initial Margin (IM)

Collateral to cover PFE during margin period of risk.

**VaR-Based IM:**
$$IM = VaR_\alpha(\Delta V, MPOR)$$

Where:
- $MPOR$ = Margin Period of Risk (typically 10 days)
- $\Delta V$ = Change in portfolio value

**SIMM (Standard Initial Margin Model):**
$$IM = \sqrt{\sum_{k} K_k^2 + \sum_{k \neq l} \gamma_{kl} S_k S_l K_k K_l}$$

Where:
- $K_k$ = Risk contribution from risk class $k$
- $\gamma_{kl}$ = Correlation between risk classes
- $S_k$ = Sign of net sensitivity

**Risk Class Margin:**
$$K = \sqrt{\sum_i WS_i^2 + \sum_{i \neq j} \rho_{ij} WS_i WS_j}$$

Where:
- $WS_i$ = Weighted Sensitivity = $s_i \times RW_i$
- $RW_i$ = Risk Weight
- $\rho_{ij}$ = Correlation

---

## 4. Stochastic Processes

### 4.1 Geometric Brownian Motion (GBM)

**SDE:**
$$dS = \mu S \, dt + \sigma S \, dW$$

**Exact Solution:**
$$S(t) = S_0 \exp\left[\left(\mu - \frac{\sigma^2}{2}\right)t + \sigma W(t)\right]$$

**Discrete Simulation:**
$$S(t+\Delta t) = S(t) \exp\left[\left(\mu - \frac{\sigma^2}{2}\right)\Delta t + \sigma \sqrt{\Delta t} \, Z\right]$$

Where $Z \sim N(0,1)$

### 4.2 Ornstein-Uhlenbeck (OU) Process

**SDE:**
$$dX = \theta(\mu - X) \, dt + \sigma \, dW$$

**Exact Solution:**
$$X(t) = \mu + (X_0 - \mu)e^{-\theta t} + \sigma \int_0^t e^{-\theta(t-s)} dW(s)$$

**Discrete Simulation:**
$$X(t+\Delta t) = X(t)e^{-\theta \Delta t} + \mu(1 - e^{-\theta \Delta t}) + \sigma\sqrt{\frac{1-e^{-2\theta \Delta t}}{2\theta}} Z$$

### 4.3 Cox-Ingersoll-Ross (CIR) Process

**SDE:**
$$dX = \theta(\mu - X) \, dt + \sigma \sqrt{X} \, dW$$

**Feller Condition:**
$$2\theta\mu > \sigma^2 \quad \text{(ensures positivity)}$$

**Full Truncation Euler:**
$$X(t+\Delta t) = X(t) + \theta(\mu - X^+(t))\Delta t + \sigma\sqrt{X^+(t)\Delta t} \, Z$$

Where $X^+ = \max(X, 0)$

### 4.4 Heston Stochastic Volatility

**SDEs:**
$$dS = \mu S \, dt + \sqrt{V} S \, dW_1$$
$$dV = \kappa(\theta - V) \, dt + \sigma_v \sqrt{V} \, dW_2$$
$$dW_1 \cdot dW_2 = \rho \, dt$$

**Discrete Simulation:**
$$V(t+\Delta t) = V(t) + \kappa(\theta - V^+(t))\Delta t + \sigma_v\sqrt{V^+(t)\Delta t} \, Z_V$$
$$S(t+\Delta t) = S(t) \exp\left[\left(\mu - \frac{V(t)}{2}\right)\Delta t + \sqrt{V(t)\Delta t} \, Z_S\right]$$

Where:
$$Z_S = \rho Z_V + \sqrt{1-\rho^2} Z_\perp$$

### 4.5 Merton Jump-Diffusion

**SDE:**
$$\frac{dS}{S} = (\mu - \lambda k) \, dt + \sigma \, dW + (J-1) \, dN$$

Where:
- $N$ = Poisson process with intensity $\lambda$
- $J$ = Jump size, $\ln J \sim N(\mu_J, \sigma_J^2)$
- $k = \mathbb{E}[J-1] = e^{\mu_J + \sigma_J^2/2} - 1$

**Discrete Simulation:**
$$S(t+\Delta t) = S(t) \exp\left[\left(\mu - \lambda k - \frac{\sigma^2}{2}\right)\Delta t + \sigma\sqrt{\Delta t} Z + \sum_{i=1}^{N_t} Y_i\right]$$

Where:
- $N_t \sim \text{Poisson}(\lambda \Delta t)$
- $Y_i \sim N(\mu_J, \sigma_J^2)$

### 4.6 Hull-White (One-Factor)

**SDE:**
$$dr = (\theta(t) - ar) \, dt + \sigma \, dW$$

**Mean Reversion:**
$$\mathbb{E}[r(t)] = r_0 e^{-at} + \int_0^t \theta(s) e^{-a(t-s)} ds$$

---

## 5. Product Valuations

### 5.1 Interest Rate Swap (IRS)

**Fixed Leg PV:**
$$PV_{fixed} = N \times K \times \sum_{i=1}^{n} \tau_i \times DF(t_i)$$

**Floating Leg PV:**
$$PV_{float} = N \times \sum_{i=1}^{n} L(t_{i-1}, t_i) \times \tau_i \times DF(t_i)$$

Where:
- $N$ = Notional
- $K$ = Fixed rate
- $\tau_i$ = Day count fraction
- $DF(t)$ = Discount factor
- $L(s,t)$ = Forward LIBOR rate

**Swap Value:**
$$V = PV_{float} - PV_{fixed}$$ (for pay fixed)

### 5.2 FX Forward

**Forward Rate:**
$$F = S_0 \times \frac{DF_f(T)}{DF_d(T)}$$

Where:
- $S_0$ = Spot FX rate
- $DF_f$ = Foreign discount factor
- $DF_d$ = Domestic discount factor

**Forward Value:**
$$V = N_f \times (F - K) \times DF_d(T)$$

### 5.3 European Options

**Black-Scholes Call:**
$$C = S_0 N(d_1) - K e^{-rT} N(d_2)$$

**Black-Scholes Put:**
$$P = K e^{-rT} N(-d_2) - S_0 N(-d_1)$$

Where:
$$d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}$$
$$d_2 = d_1 - \sigma\sqrt{T}$$

**Greeks:**
- Delta: $\Delta_C = N(d_1)$, $\Delta_P = N(d_1) - 1$
- Gamma: $\Gamma = \frac{n(d_1)}{S_0 \sigma \sqrt{T}}$
- Vega: $\mathcal{V} = S_0 n(d_1) \sqrt{T}$
- Theta: $\Theta_C = -\frac{S_0 n(d_1) \sigma}{2\sqrt{T}} - rK e^{-rT} N(d_2)$

### 5.4 Credit Default Swap (CDS)

**Premium Leg:**
$$PV_{premium} = s \times N \times \sum_{i=1}^{n} \tau_i \times S(t_i) \times DF(t_i)$$

**Protection Leg:**
$$PV_{protection} = (1-R) \times N \times \sum_{i=1}^{n} [S(t_{i-1}) - S(t_i)] \times DF(t_i)$$

**Fair Spread:**
$$s = \frac{(1-R) \times \sum_{i} [S(t_{i-1}) - S(t_i)] \times DF(t_i)}{\sum_{i} \tau_i \times S(t_i) \times DF(t_i)}$$

### 5.5 Swaption (Black's Model)

**Payer Swaption:**
$$V = A \times [S_0 N(d_1) - K N(d_2)]$$

**Receiver Swaption:**
$$V = A \times [K N(-d_2) - S_0 N(-d_1)]$$

Where:
- $A$ = Annuity factor = $\sum_i \tau_i DF(t_i)$
- $S_0$ = Forward swap rate
- $\sigma$ = Swaption volatility

---

## 6. Stress Testing Methodologies

### 6.1 Sensitivity-Based Stress

**DV01 (Dollar Value of 01):**
$$DV01 = -\frac{\partial V}{\partial y} \times 0.0001$$

**Duration:**
$$D = -\frac{1}{V} \frac{\partial V}{\partial y}$$

**Convexity:**
$$C = \frac{1}{V} \frac{\partial^2 V}{\partial y^2}$$

**Price Change (Second Order):**
$$\Delta V \approx -D \times V \times \Delta y + \frac{1}{2} C \times V \times (\Delta y)^2$$

**FX Delta:**
$$\Delta_{FX} = \frac{\partial V}{\partial S}$$

**Vega:**
$$\mathcal{V} = \frac{\partial V}{\partial \sigma}$$

### 6.2 Historical Stress Scenarios

**2008 Financial Crisis:**
- Equity decline: -40%
- Credit spread widening: +300bps
- Volatility spike: +150%
- Interest rate drop: -200bps

**COVID-19 (March 2020):**
- Equity decline: -35%
- Credit spread widening: +200bps
- Volatility spike: +200%
- Rate drop: -150bps

### 6.3 Regulatory Stress (CCAR/DFAST)

**Severely Adverse Scenario:**
- GDP decline, unemployment surge
- Equity -50%, rates -300bps
- Credit spreads +400bps

**Adverse Scenario:**
- Moderate recession
- Equity -25%, rates -100bps
- Credit spreads +150bps

### 6.4 Reverse Stress Testing

Find scenarios that cause portfolio failure:

$$\text{Find } \Delta \mathbf{x} : V(\mathbf{x} + \Delta \mathbf{x}) = V_{threshold}$$

Subject to:
$$\|\Delta \mathbf{x}\| \text{ minimized}$$

---

## Appendix: Statistical Distributions

### Normal Distribution
$$f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{(x-\mu)^2}{2\sigma^2}}$$

### Lognormal Distribution
$$f(x) = \frac{1}{x\sigma\sqrt{2\pi}} e^{-\frac{(\ln x - \mu)^2}{2\sigma^2}}$$

### Student's t Distribution
$$f(x) = \frac{\Gamma(\frac{\nu+1}{2})}{\sqrt{\nu\pi}\Gamma(\frac{\nu}{2})} \left(1 + \frac{x^2}{\nu}\right)^{-\frac{\nu+1}{2}}$$

### Chi-Squared Distribution
$$f(x) = \frac{1}{2^{k/2}\Gamma(k/2)} x^{k/2-1} e^{-x/2}$$

---

*Document Version: 2.3.1*  
*Last Updated: 2025*
