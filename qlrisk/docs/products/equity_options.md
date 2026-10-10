# Equity Options

## Product Overview

Equity options give the holder the right (but not obligation) to buy or sell an underlying equity at a specified price on or before a specified date. They create asymmetric exposure profiles that require careful CCR modeling.

## Product Specifications

| Attribute | Description |
|-----------|-------------|
| Underlying | Stock, ETF, or Index |
| Option Type | Call or Put |
| Strike Price | Exercise price |
| Expiry | Option maturity date |
| Style | European or American |
| Settlement | Physical or Cash |

## Valuation

### Black-Scholes Formula (European)

**Call Option:**
```
C = S × N(d₁) - K × e^(-rT) × N(d₂)

d₁ = [ln(S/K) + (r + σ²/2)T] / (σ√T)
d₂ = d₁ - σ√T
```

**Put Option:**
```
P = K × e^(-rT) × N(-d₂) - S × N(-d₁)
```

## Greeks

| Greek | Definition | CCR Impact |
|-------|------------|------------|
| Delta (Δ) | ∂V/∂S | Exposure direction |
| Gamma (Γ) | ∂²V/∂S² | Convexity risk |
| Vega (ν) | ∂V/∂σ | Vol sensitivity |
| Theta (Θ) | ∂V/∂t | Time decay |
| Rho (ρ) | ∂V/∂r | Rate sensitivity |

## CCR Characteristics

### Long Call Exposure Profile
```
     ^
     |    ****
     |   *    **
     |  *       *
     | *         *
     +-------------------> Time
        Decaying due to theta, but can spike up
```

### Short Put Exposure
```
     ^
     |*****
     |     ***
     |        ***
     |           ***
     +-------------------> Time
        Large initial exposure, declining with spot
```

### Key Risk Factors
- Underlying price movements
- Implied volatility changes
- Interest rates
- Dividends

## CCR Calculator Inputs

```python
# Equity Option CCR calculation
trade_data = {
    "product_type": "equity_option",
    "notional": 10_000_000,  # Notional exposure
    "current_mtm": 500_000,
    "remaining_maturity": 1.0,
    "volatility": 0.25,  # Implied vol
    "option_type": "call",
    "strike": 100,
    "spot": 105,
    "delta": 0.65
}
```

## Add-On Factors (SA-CCR)

| Category | Add-On Factor |
|----------|---------------|
| Single Stock | 32% |
| Index (Major) | 20% |
| Index (Other) | 32% |

### Delta Adjustment
```
Effective Notional = |Delta| × Notional
Add-On = SF × Effective Notional
```

## Option Strategies

### Long Call
- **CCR**: Positive exposure, loss limited to premium
- **Collateral**: May post margin on exchange

### Short Put
- **CCR**: Potential large exposure if spot falls
- **Collateral**: Typically requires margin

### Straddle/Strangle
- **CCR**: Complex exposure based on spot level
- **Netting**: Long/short legs may offset

## Netting Considerations

- Same underlying options can net
- Delta netting reduces exposure
- Gamma/vega risks remain

## Margining

### Exchange-Traded
- Daily margining via clearinghouse
- SPAN or VaR-based margins
- Low counterparty risk

### OTC Options
- Bilateral CSA arrangements
- Subject to UMR requirements
- Higher CCR considerations

## Volatility Surface

### Impact on CCR
```
Volatility term structure affects:
- Option values
- PFE calculations  
- Wrong-way risk (vol spikes in stress)
```

### Smile/Skew Effects
- OTM puts more expensive (protection premium)
- Affects CCR for different strikes

## Wrong-Way Risk

### Equity Put WWR
```
If counterparty = issuer of underlying:
   Put protection fails when most needed
   (company defaults when stock crashes)
```

### Mitigation
- Limit single-name exposure
- Diversification
- Collateral arrangements

## Use Cases

1. **Hedging**: Portfolio protection
2. **Income**: Premium collection
3. **Leverage**: Synthetic equity exposure
4. **Volatility Trading**: Vol views

## References

- Black, F. & Scholes, M. - "The Pricing of Options"
- Hull, J. - "Options, Futures, and Other Derivatives"
- Basel SA-CCR Framework
- ISDA Equity Definitions

---
Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is strictly
prohibited without explicit written permission from the copyright holder.
---

