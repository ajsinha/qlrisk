# Counterparty Model Documentation v1.2.0

## Overview

The Counterparty module provides models for managing counterparty information, netting sets, and collateral agreements essential for CCR calculations.

## Classes

### Counterparty (Dataclass)

Represents a trading counterparty.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `counterparty_id` | str | auto-generated | Unique identifier |
| `name` | str | '' | Legal name |
| `legal_name` | str | '' |  |
| `counterparty_type` | CounterpartyType | CounterpartyType.CORPORATE |  |
| `ratings` | List | list() |  |
| `probability_of_default` | float | 0.01 |  |
| `loss_given_default` | float | 0.45 |  |
| `lei` | Union | None | Legal Entity Identifier |
| `ticker` | Union | None |  |
| `country` | str | 'US' | Country of incorporation |
| `sector` | str | '' | Industry sector |
| `parent_id` | Union | None |  |
| `netting_set_ids` | List | list() |  |

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
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `netting_set_id` | str | auto-generated | Unique identifier |
| `name` | str | '' |  |
| `counterparty_id` | str | '' | Parent counterparty |
| `trade_ids` | List | list() | Trades in netting set |
| `collateral_agreement` | Union | None |  |
| `has_netting_agreement` | bool | True |  |
| `gross_exposure` | float | 0.0 |  |
| `net_exposure` | float | 0.0 |  |
| `collateralized_exposure` | float | 0.0 |  |

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
| `id` | str | auto-generated |  |
| `created_at` | datetime | now() |  |
| `updated_at` | datetime | now() |  |
| `metadata` | Dict | dict() |  |
| `agreement_id` | str | auto-generated | Unique identifier |
| `netting_set_id` | str | '' | Associated netting set |
| `threshold_self` | float | 0.0 |  |
| `threshold_counterparty` | float | 0.0 | CP threshold |
| `minimum_transfer_amount` | float | 0.0 |  |
| `independent_amount_self` | float | 0.0 |  |
| `independent_amount_counterparty` | float | 0.0 |  |
| `margin_period_of_risk` | int | 10 |  |
| `eligible_collateral` | List | auto-generated | Eligible types |
| `haircuts` | Dict | dict() | Collateral haircuts |
| `posted_collateral` | float | 0.0 |  |
| `received_collateral` | float | 0.0 |  |

## Usage Examples

```python
from qlrisk.models import Counterparty, NettingSet, CollateralAgreement

cp = Counterparty(counterparty_id="CP-GBL", name="Global Bank Ltd", legal_name="Global Bank Limited",
                  lei="549300ABCDEF12345678", country="US", sector="Banking",
                  probability_of_default=0.005, loss_given_default=0.45)

csa = CollateralAgreement(agreement_id="CSA-001", netting_set_id="NS-GBL-1", threshold_counterparty=1_000_000,
                          minimum_transfer_amount=250_000, margin_period_of_risk=10)
ns = NettingSet(netting_set_id="NS-GBL-1", counterparty_id="CP-GBL", trade_ids=["IRS-1", "IRS-2"],
                collateral_agreement=csa)
print(cp.name, cp.probability_of_default, ns.trade_ids, csa.threshold_counterparty)
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
