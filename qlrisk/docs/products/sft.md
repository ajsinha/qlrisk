# Securities Financing Transactions (SFT)

## Overview

Securities Financing Transactions (SFT) are collateralized transactions used for financing and securities borrowing/lending purposes. These transactions involve the temporary exchange of securities for cash or other securities, with an agreement to reverse the exchange at a future date.

## QLRisk - SFT Products v1.3.0

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
```

---

## Product Summary

| Product | Description | Key Use Case |
|---------|-------------|--------------|
| **MarginLoan** | Lending against securities collateral | Leverage for investors |
| **MarginLending** | Securities-based lending facility | Portfolio financing |
| **CollateralSwap** | Exchange of collateral for other securities | Collateral transformation |
| **TriPartyRepo** | Tri-party repurchase agreement | Secured funding |
| **PrimeBrokerage** | Prime brokerage financing arrangements | Hedge fund services |
| **SecuritiesBorrowing** | Securities borrowing arrangement | Short selling |
| **StockLoan** | Stock lending/borrowing arrangement | Securities lending |

---

## Stock Loan

### Overview

A Stock Loan is a bilateral agreement where securities are lent from the lender to the borrower. The borrower posts collateral and pays a fee.

### Loan Types

| Type | Code | Typical Fee | Description |
|------|------|-------------|-------------|
| General Collateral | `GC` | 25 bps | Easy to borrow |
| Warm | `WARM` | 100 bps | Moderately hard to borrow |
| Special | `SPECIAL` | 500 bps | Hard to borrow |
| Hot | `HOT` | 1500 bps | Very hard to borrow |

### Collateral Types

| Type | Code | Haircut |
|------|------|---------|
| Cash | `CASH` | 0% |
| Treasury | `TREASURY` | 1% |
| Agency | `AGENCY` | 2% |
| Corporate Bond | `CORPORATE` | 8% |
| Equity | `EQUITY` | 15% |
| Letter of Credit | `LOC` | 0% |

### Usage Example

```python
from datetime import date
from qlrisk.products.python.sft import (
    StockLoan,
    StockLoanType,
    StockLoanTerms,
    LoanCollateralType,
    DividendTreatment
)
from qlrisk.products.base import Currency

# Create a stock loan (as lender)
loan = StockLoan(
    trade_id="SL-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2025, 12, 31),
    notional=5_000_000,  # $5M market value
    currency=Currency.USD,
    counterparty_id="HEDGE_FUND_001",
    terms=StockLoanTerms(
        stock_ticker="TSLA",
        stock_name="Tesla Inc.",
        quantity=10000,  # 10,000 shares
        loan_value=5_000_000,
        loan_type=StockLoanType.SPECIAL,  # Hard to borrow
        collateral_type=LoanCollateralType.CASH,
        collateral_margin=1.05,  # 105% collateral
        rebate_rate=0.02,  # 2% rebate on cash
        dividend_treatment=DividendTreatment.MANUFACTURED,
        stock_volatility=0.45
    ),
    is_lender=True
)

# Price the loan
from qlrisk.models import MarketData

market_data = MarketData(
    valuation_date=date.today(),
    discount_curve={0.5: 0.05, 1.0: 0.052},
    equity_prices={"TSLA": 500.00}
)

result = loan.price(market_data)
print(f"Stock Value: ${result.components['stock_value']:,.2f}")
print(f"Collateral Value: ${result.components['collateral_value']:,.2f}")
print(f"Net Exposure: ${result.components['net_exposure']:,.2f}")
print(f"Margin Call: ${result.components['margin_call']:,.2f}")
```

---

## Securities Borrowing

### Overview

In a securities borrowing transaction, the borrower receives securities from the lender, posts collateral, and pays a borrowing fee.

### Usage Example

```python
from qlrisk.products.python.sft import (
    SecuritiesBorrowing,
    CollateralType,
    SecuritiesType,
    BorrowedSecurity
)

# Create securities borrowing
borrowing = SecuritiesBorrowing(
    trade_id="SB-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2025, 6, 30),
    notional=2_000_000,
    currency=Currency.USD,
    counterparty_id="LENDER-001",
    borrowed_securities=[
        BorrowedSecurity(
            security_id="AAPL",
            security_type=SecuritiesType.EQUITY,
            ticker="AAPL",
            quantity=10000,
            market_value=1_850_000,
            volatility=0.28
        )
    ],
    collateral_type=CollateralType.CASH,
    margin_ratio=1.02,
    rebate_rate=-0.0025  # Borrower pays 25 bps
)
```

---

## Margin Loan

### Overview

Margin lending provides financing against securities collateral, typically used by investors for leverage.

### Usage Example

```python
from qlrisk.products.python.sft import (
    MarginLoan,
    MarginLoanTerms,
    MarginLoanType,
    CollateralCategory
)

margin_loan = MarginLoan(
    trade_id="ML-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2025, 12, 31),
    notional=1_000_000,  # $1M loan amount
    currency=Currency.USD,
    counterparty_id="INVESTOR-001",
    terms=MarginLoanTerms(
        loan_type=MarginLoanType.STANDARD,
        interest_rate=0.065,  # 6.5% interest
        initial_margin_ratio=0.50,  # 50% LTV
        maintenance_margin_ratio=0.70  # 70% maintenance
    )
)
```

---

## Collateral Swap

### Overview

A collateral swap involves exchanging one type of collateral for another, typically to transform lower-quality collateral into higher-quality collateral.

### Usage Example

```python
from qlrisk.products.python.sft import (
    CollateralSwap,
    CollateralQuality,
    CollateralLeg
)

coll_swap = CollateralSwap(
    trade_id="CS-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2025, 6, 30),
    notional=50_000_000,
    currency=Currency.USD,
    counterparty_id="CPTY-001",
    # Exchange corporate bonds for Treasuries
    deliver_leg=CollateralLeg(
        security_type="corporate_bond",
        quality=CollateralQuality.INVESTMENT_GRADE,
        market_value=50_000_000
    ),
    receive_leg=CollateralLeg(
        security_type="treasury",
        quality=CollateralQuality.HQLA_L1,
        market_value=48_000_000  # Net of transformation fee
    )
)
```

---

## Tri-Party Repo

### Overview

A tri-party repo is a repurchase agreement where a third-party agent (typically a custodian bank) manages the collateral and settlement process.

### Tri-Party Agents

| Agent | Code |
|-------|------|
| Bank of New York Mellon | `BNYM` |
| JPMorgan Chase | `JPM` |
| State Street | `STT` |
| Euroclear | `EUROCLEAR` |
| Clearstream | `CLEARSTREAM` |

### Usage Example

```python
from qlrisk.products.python.sft import (
    TriPartyRepo,
    TriPartyRepoTerms,
    TriPartyAgent,
    CollateralSchedule
)

repo = TriPartyRepo(
    trade_id="TPR-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2025, 3, 31),
    notional=100_000_000,  # $100M repo
    currency=Currency.USD,
    counterparty_id="DEALER-001",
    terms=TriPartyRepoTerms(
        agent=TriPartyAgent.BNYM,
        repo_rate=0.045,  # 4.5% repo rate
        haircut=0.02,  # 2% haircut
        collateral_schedule=CollateralSchedule.TREASURY_ONLY
    )
)
```

---

## Prime Brokerage

### Overview

Prime brokerage arrangements provide a suite of services to hedge funds and institutional clients, including financing, securities lending, trade execution, and custody.

### Service Types

| Service | Code | Description |
|---------|------|-------------|
| Margin Financing | `MARGIN` | Leverage for trading |
| Securities Lending | `SECURITIES_LENDING` | Borrow securities |
| Synthetic Financing | `SYNTHETIC` | TRS-based financing |
| Trade Execution | `EXECUTION` | Trade routing |
| Custody | `CUSTODY` | Asset safekeeping |

### Usage Example

```python
from qlrisk.products.python.sft import (
    PrimeBrokerage,
    PrimeBrokerageTerms,
    PBServiceType,
    PBAccountType
)

pb = PrimeBrokerage(
    trade_id="PB-001",
    trade_date=date.today(),
    effective_date=date.today(),
    maturity_date=date(2025, 12, 31),
    notional=500_000_000,  # $500M facility
    currency=Currency.USD,
    counterparty_id="HEDGE_FUND_001",
    terms=PrimeBrokerageTerms(
        services=[
            PBServiceType.MARGIN,
            PBServiceType.SECURITIES_LENDING,
            PBServiceType.CUSTODY
        ],
        account_type=PBAccountType.PORTFOLIO_MARGIN,
        margin_rate=0.055,  # 5.5% margin rate
        stock_borrow_rate=0.0050  # 50 bps stock borrow
    )
)
```

---

## SA-CCR Treatment for SFT

### Simplified Approach

For SFT transactions, SA-CCR uses a simplified approach:

```
EAD = max(0, E × (1 + H_s) - C × (1 - H_c) + H_fx)
```

Where:
- `E` = Securities (exposure) value
- `H_s` = Securities (volatility) haircut
- `C` = Collateral value
- `H_c` = Collateral haircut
- `H_fx` = FX haircut (if different currencies)

### Standard Supervisory Haircuts

| Asset Type | Residual Maturity | Haircut |
|------------|-------------------|---------|
| Main Index Equity | - | 15% |
| Other Equity | - | 25% |
| Sovereigns (AAA-AA) | ≤1Y | 0.5% |
| Sovereigns (AAA-AA) | 1-5Y | 2% |
| Sovereigns (AAA-AA) | >5Y | 4% |
| Other Sovereigns | ≤1Y | 1% |
| Other Sovereigns | 1-5Y | 3% |
| Other Sovereigns | >5Y | 6% |
| Corporate (IG) | ≤1Y | 1% |
| Corporate (IG) | 1-5Y | 4% |
| Corporate (IG) | >5Y | 8% |

---

## Risk Considerations

### Gap Risk
Risk that securities price moves faster than margin calls can be collected.

### Correlation Risk
Risk that collateral value is correlated with securities value (wrong-way risk).

### Concentration Risk
Risk from concentrated positions in securities or collateral.

### Operational Risk
Settlement failures, corporate action processing, dividend handling.

---

## See Also

- [Repo Products](../products/README.md#repo)
- [SA-CCR Documentation](../saccr.md)
- [Margin & Collateral](../margin.md)
- [XVA Calculations](../xva.md)

---

*QLRisk v1.3.0*
