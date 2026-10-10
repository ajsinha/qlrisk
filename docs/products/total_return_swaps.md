# Total Return Swaps (TRS)

<!-- legacy-examples -->
> ⚠️ **Some code samples on this page predate v2.0 and no longer match the API** (1 of 4 fail). Use the [user guides](../guides/README.md), whose examples are executed by the test suite, until this page is revised.
<!-- /legacy-examples -->

## Overview

A Total Return Swap (TRS) is a derivative contract where one party (total return payer) pays the total return of an underlying asset (including price appreciation, dividends/coupons, and any principal changes) while receiving a financing rate (typically SOFR + spread) from the counterparty.

## QLRisk - TRS v2.2.0

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
```

---

## TRS Types

### Equity Total Return Swap (EquityTRS)

Provides synthetic exposure to equity assets without direct ownership.

**Underlying Types:**
| Type | Code | SA-CCR Factor |
|------|------|---------------|
| Single Stock | `SINGLE_STOCK` | 32% |
| Equity Index | `EQUITY_INDEX` | 20% |
| ETF | `ETF` | 20% |
| Basket | `BASKET` | 32% |
| Custom Index | `CUSTOM_INDEX` | 20% |

### Bond Total Return Swap (BondTRS)

Provides synthetic exposure to bonds or bond portfolios.

**Underlying Types:**
| Type | Code | Asset Class |
|------|------|-------------|
| Single Bond | `SINGLE_BOND` | Credit |
| Bond Index | `BOND_INDEX` | Credit |
| Government Bond | `GOVERNMENT_BOND` | Interest Rate |
| Corporate Bond | `CORPORATE_BOND` | Credit |
| High Yield | `HIGH_YIELD_BOND` | Credit |
| Investment Grade | `INVESTMENT_GRADE` | Credit |
| Emerging Market | `EMERGING_MARKET` | Credit |
| MBS | `MBS` | Credit |
| ABS | `ABS` | Credit |
| CLO | `CLO` | Credit |

---

## Use Cases

### Equity TRS
- Synthetic equity exposure without direct ownership
- Leverage and financing strategies
- Balance sheet optimization
- Tax-efficient equity exposure
- Prime brokerage financing
- Dividend capture strategies

### Bond TRS
- Synthetic bond/credit exposure
- Leverage for fixed income portfolios
- Balance sheet optimization (off-balance sheet financing)
- Regulatory capital optimization
- Credit spread trading
- CLO/ABS portfolio exposure

---

## Usage Examples

### Creating an Equity TRS

```python
from datetime import date
from qlrisk.products.python.equity import (
    EquityTRS, 
    EquityTRSType, 
    EquityTRSTerms,
    TRSReturnType,
    TRSResetType
)
from qlrisk.products.base import Currency, FloatingRateIndex

# Create equity TRS on Apple stock
equity_trs = EquityTRS(
    trade_id="EQ-TRS-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2025, 12, 31),
    notional=10_000_000,  # $10M notional
    currency=Currency.USD,
    counterparty_id="CPTY-001",
    terms=EquityTRSTerms(
        underlying_type=EquityTRSType.SINGLE_STOCK,
        underlying_ticker="AAPL",
        underlying_name="Apple Inc.",
        initial_price=180.00,
        current_price=185.50,
        dividend_yield=0.005,  # 0.5% dividend yield
        return_type=TRSReturnType.TOTAL_RETURN,
        reset_type=TRSResetType.PERIODIC,
        financing_index=FloatingRateIndex.SOFR,
        financing_spread=50,  # 50 bps over SOFR
        is_funded=True
    ),
    is_receiver=True  # Receive total return, pay financing
)
```

### Creating an Index TRS

```python
# Create S&P 500 index TRS
index_trs = EquityTRS(
    trade_id="EQ-TRS-002",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2026, 6, 30),
    notional=50_000_000,  # $50M notional
    currency=Currency.USD,
    counterparty_id="CPTY-002",
    terms=EquityTRSTerms(
        underlying_type=EquityTRSType.EQUITY_INDEX,
        underlying_ticker="SPX",
        underlying_name="S&P 500 Index",
        initial_price=4500.00,
        dividend_yield=0.015,  # 1.5% dividend yield
        financing_spread=25  # 25 bps over SOFR
    ),
    is_receiver=True
)
```

### Creating a Bond TRS

```python
from qlrisk.products.python.fixed_income import (
    BondTRS,
    BondTRSTerms,
    BondTRSUnderlyingType,
    BondTRSReturnType
)

# Create corporate bond TRS
bond_trs = BondTRS(
    trade_id="BOND-TRS-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2026, 12, 31),
    notional=25_000_000,  # $25M notional
    currency=Currency.USD,
    counterparty_id="CPTY-003",
    terms=BondTRSTerms(
        underlying_type=BondTRSUnderlyingType.CORPORATE_BOND,
        underlying_identifier="US123456789",
        underlying_name="ABC Corp 5.0% 2030",
        issuer="ABC Corporation",
        initial_price=98.50,  # As % of face value
        current_price=99.25,
        coupon_rate=0.05,  # 5% coupon
        credit_rating="BBB",
        spread_over_benchmark=150,  # 150 bps spread
        modified_duration=5.5,
        financing_spread=75  # 75 bps over SOFR
    ),
    is_receiver=True
)
```

### Pricing and Risk Calculation

```python
from qlrisk.models import MarketData

# Create market data
market_data = MarketData(
    valuation_date=date.today(),
    discount_curve={0.25: 0.05, 0.5: 0.051, 1.0: 0.052, 2.0: 0.053},
    equity_prices={"AAPL": 185.50, "SPX": 4525.00}
)

# Price the equity TRS
result = equity_trs.price(market_data)
print(f"NPV: ${result.npv:,.2f}")
print(f"Equity Leg: ${result.components['equity_leg']:,.2f}")
print(f"Financing Leg: ${result.components['financing_leg']:,.2f}")
print(f"Total Return: {result.components['total_return']:.2%}")

# Calculate CCR exposure
exposure = equity_trs.calculate_ccr_exposure(
    market_data,
    time_horizon=2.0,
    confidence_level=0.95
)
print(f"EPE: ${exposure.epe:,.2f}")
print(f"CVA: ${exposure.cva:,.2f}")

# Calculate SA-CCR EAD
saccr = equity_trs.calculate_saccr(market_data)
print(f"EAD: ${saccr.ead:,.2f}")
print(f"Supervisory Factor: {saccr.details['supervisory_factor']:.0%}")
```

---

## Economics

### Cash Flows

**Total Return Receiver:**
```
Receives: Total Return = Notional × (P_t/P_0 - 1) + Dividends/Coupons
Pays:     Financing = Notional × (SOFR + Spread) × Δt
```

**Total Return Payer:**
```
Pays:     Total Return = Notional × (P_t/P_0 - 1) + Dividends/Coupons
Receives: Financing = Notional × (SOFR + Spread) × Δt
```

### NPV Calculation

```
NPV = Direction × (Equity_Leg - Financing_Leg) × DF
```

Where:
- `Direction` = +1 for receiver, -1 for payer
- `Equity_Leg` = Notional × Total Return
- `Financing_Leg` = Notional × Financing Rate × Time
- `DF` = Discount factor

---

## SA-CCR Treatment

### Equity TRS

| Underlying Type | Asset Class | Supervisory Factor |
|-----------------|-------------|-------------------|
| Single Stock | Equity | 32% |
| Equity Index | Equity | 20% |
| ETF | Equity | 20% |
| Basket | Equity | 32% |

**EAD Calculation:**
```
EAD = α × (RC + PFE_AddOn)
RC = max(0, NPV)
PFE_AddOn = SF × |Adjusted_Notional| × MF
```

### Bond TRS

| Underlying Type | Asset Class | Supervisory Factor |
|-----------------|-------------|-------------------|
| Government Bond | Interest Rate | 0.5% |
| IG Corporate (AAA-AA) | Credit | 0.38% |
| IG Corporate (A) | Credit | 0.42% |
| IG Corporate (BBB) | Credit | 0.54% |
| HY (BB) | Credit | 1.06% |
| HY (B) | Credit | 1.60% |
| Distressed (CCC-) | Credit | 6.00% |

**Duration Adjustment:**
For bond TRS, the adjusted notional is duration-weighted:
```
Adjusted_Notional = Notional × Duration / 5.0
```

---

## CCR Exposure Characteristics

### Equity TRS
- Exposure driven by equity price volatility
- Dividend uncertainty adds risk
- Directional exposure to underlying
- Financing spread affects break-even

### Bond TRS
- Exposure influenced by interest rates and credit spreads
- Duration and convexity affect exposure sensitivity
- Coupon carry benefit for receivers
- Credit migration risk for corporate underlyings

### Risk Factors
| Factor | Equity TRS | Bond TRS |
|--------|------------|----------|
| Price Risk | High | Medium |
| Rate Risk | Low | High |
| Credit Risk | Low | High |
| Dividend/Coupon Risk | Medium | Low |

---

## See Also

- [Equity Products](../products/README.md#equity-derivatives)
- [Fixed Income Products](../products/README.md#fixed-income)
- [SA-CCR Documentation](../saccr.md)
- [XVA Calculations](../calculators/cva_calculator.md)

---

*QLRisk v2.2.0*
