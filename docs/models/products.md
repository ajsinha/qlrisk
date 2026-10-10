# Products Model Documentation
## Overview

The Products model module provides domain models for 27 financial product types used in CCR calculations. These are lightweight data models; for full pricing implementations, see `products/python/`.

## Base Classes

### PaymentFrequency (Enum)

| Value | Name | Description |
|-------|------|-------------|
| `1` | `ANNUAL` | 1 |
| `2` | `SEMI_ANNUAL` | 2 |
| `4` | `QUARTERLY` | 4 |
| `12` | `MONTHLY` | 12 |
| `52` | `WEEKLY` | 52 |
| `365` | `DAILY` | 365 |

### OptionType (Enum)

| Value | Name | Description |
|-------|------|-------------|
| `call` | `CALL` | Call option |
| `put` | `PUT` | Put option |

### OptionStyle (Enum)

| Value | Name | Description |
|-------|------|-------------|
| `european` | `EUROPEAN` | European exercise |
| `american` | `AMERICAN` | American exercise |
| `bermudan` | `BERMUDAN` | Bermudan exercise |

### AssetClass (Enum)

| Value | Name | Description |
|-------|------|-------------|
| `interest_rate` | `INTEREST_RATE` | IR products |
| `fx` | `FX` | FX products |
| `credit` | `CREDIT` | Credit products |
| `equity` | `EQUITY` | Equity products |
| `commodity` | `COMMODITY` | Commodity products |

### Product (Dataclass)

Base product class.

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `product_id` | str | auto-generated | Unique ID |
| `product_type` | str | '' | Product type |
| `asset_class` | str | '' | Asset class |
| `notional` | float | 0.0 | Notional amount |
| `currency` | str | 'USD' | Currency |
| `effective_date` | date | today() | Start date |
| `maturity_date` | date | today() | End date |
| `counterparty_id` | str | '' | Counterparty |

## Interest Rate Products

| Class | Type | Key Attributes |
|-------|------|----------------|
| `InterestRateSwap` | IRS | fixed_rate, floating_index, is_payer |
| `OvernightIndexSwap` | OIS | fixed_rate, overnight_index |
| `ForwardRateAgreement` | FRA | fra_rate, fixing_date |
| `InterestRateCap` | CAP | strike, floating_index |
| `InterestRateFloor` | FLOOR | strike, floating_index |
| `Swaption` | SWAPTION | strike, option_expiry, swap_tenor |

## FX Products

| Class | Type | Key Attributes |
|-------|------|----------------|
| `FXForward` | FX_FORWARD | base_currency, quote_currency, forward_rate |
| `FXSwap` | FX_SWAP | near_rate, far_rate |
| `FXOption` | FX_OPTION | strike, option_type |
| `NonDeliverableForward` | NDF | forward_rate, settlement_currency |

## Credit Products

| Class | Type | Key Attributes |
|-------|------|----------------|
| `CreditDefaultSwap` | CDS | reference_entity, spread, recovery_rate |
| `CDSIndex` | CDS_INDEX | index_name, series, spread |
| `TotalReturnSwap` | TRS | reference_asset, funding_spread |

## Equity Products

| Class | Type | Key Attributes |
|-------|------|----------------|
| `EquityOption` | EQUITY_OPTION | underlying, strike, option_type |
| `EquitySwap` | EQUITY_SWAP | underlying, funding_spread |
| `VarianceSwap` | VARIANCE_SWAP | underlying, strike_variance |

## Commodity Products

| Class | Type | Key Attributes |
|-------|------|----------------|
| `CommoditySwap` | COMMODITY_SWAP | commodity, fixed_price |
| `CommodityForward` | COMMODITY_FORWARD | commodity, forward_price |

## Other Products

| Class | Type | Key Attributes |
|-------|------|----------------|
| `CrossCurrencySwap` | XCCY_SWAP | pay_currency, receive_currency |
| `Repo` | REPO | collateral_type, repo_rate, haircut |
| `Bond` | BOND | coupon_rate, face_value |
| `FloatingRateNote` | FRN | spread, floating_index |

## Usage Examples

```python
from qlrisk.models import (
    InterestRateSwap, FXForward, CreditDefaultSwap,
    PaymentFrequency, OptionType
)
from datetime import date

# Interest Rate Swap
irs = InterestRateSwap(
    notional=10_000_000,
    currency="USD",
    effective_date=date(2024, 1, 1),
    maturity_date=date(2029, 1, 1),
    fixed_rate=0.05,
    floating_index="SOFR",
    is_payer=True
)

# FX Forward
fx_fwd = FXForward(
    notional=5_000_000,
    base_currency="EUR",
    quote_currency="USD",
    forward_rate=1.10,
    maturity_date=date(2024, 6, 1)
)

# Credit Default Swap
cds = CreditDefaultSwap(
    notional=10_000_000,
    reference_entity="CORP-ABC",
    spread=0.0100,  # 100 bps
    recovery_rate=0.40,
    maturity_date=date(2029, 1, 1)
)
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
