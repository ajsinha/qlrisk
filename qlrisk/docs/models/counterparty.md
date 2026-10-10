# Counterparty Model Documentation v1.2.0

## Overview

The Counterparty module provides models for managing counterparty information, netting sets, and collateral agreements essential for CCR calculations.

## Classes

### Counterparty (Dataclass)

Represents a trading counterparty.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `counterparty_id` | str | Auto-generated | Unique identifier |
| `name` | str | "" | Legal name |
| `short_name` | str | "" | Trading name |
| `lei` | str | "" | Legal Entity Identifier |
| `country` | str | "" | Country of incorporation |
| `sector` | str | "" | Industry sector |
| `rating` | str | "BBB" | Credit rating |
| `pd` | float | 0.01 | Probability of default |
| `lgd` | float | 0.45 | Loss given default |
| `is_financial` | bool | True | Financial institution flag |
| `is_central_counterparty` | bool | False | CCP flag |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `validate()` | bool | Validate attributes |
| `get_risk_weight()` | float | Basel risk weight |

### NettingSet (Dataclass)

Legal netting agreement for exposure aggregation.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `netting_set_id` | str | Auto-generated | Unique identifier |
| `counterparty_id` | str | "" | Parent counterparty |
| `agreement_type` | str | "ISDA" | Agreement type |
| `is_margined` | bool | False | Collateralized flag |
| `threshold` | float | 0.0 | Collateral threshold |
| `minimum_transfer_amount` | float | 0.0 | MTA |
| `margin_period_of_risk` | float | 10.0 | MPOR in days |
| `independent_amount` | float | 0.0 | Initial margin |
| `trade_ids` | List[str] | [] | Trades in netting set |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add_trade(trade_id)` | None | Add trade to NS |
| `remove_trade(trade_id)` | bool | Remove trade |
| `get_trade_count()` | int | Number of trades |

### CollateralAgreement (Dataclass)

Credit Support Annex (CSA) details.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `agreement_id` | str | Auto-generated | Unique identifier |
| `netting_set_id` | str | "" | Associated netting set |
| `agreement_type` | str | "CSA" | Type (CSA, VM, IM) |
| `currency` | str | "USD" | Collateral currency |
| `threshold_party` | float | 0.0 | Our threshold |
| `threshold_counterparty` | float | 0.0 | CP threshold |
| `mta_party` | float | 0.0 | Our MTA |
| `mta_counterparty` | float | 0.0 | CP MTA |
| `rounding` | float | 0.0 | Rounding amount |
| `eligible_collateral` | List[str] | [] | Eligible types |
| `haircuts` | Dict[str, float] | {} | Collateral haircuts |
| `valuation_frequency` | str | "daily" | Valuation freq |
| `dispute_resolution_days` | int | 2 | Dispute period |

## Usage Examples

```python
from models import Counterparty, NettingSet, CollateralAgreement

# Create counterparty
cp = Counterparty(
    name="Global Bank Ltd",
    short_name="GBL",
    lei="549300ABCDEF123456",
    country="US",
    sector="Banking",
    rating="A",
    pd=0.005,
    lgd=0.45
)

# Create netting set
ns = NettingSet(
    counterparty_id=cp.counterparty_id,
    agreement_type="ISDA",
    is_margined=True,
    threshold=10_000_000,
    minimum_transfer_amount=500_000,
    margin_period_of_risk=10
)

# Create collateral agreement
csa = CollateralAgreement(
    netting_set_id=ns.netting_set_id,
    currency="USD",
    threshold_party=10_000_000,
    threshold_counterparty=10_000_000,
    eligible_collateral=["cash", "treasury"],
    haircuts={"cash": 0.0, "treasury": 0.02}
)
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
