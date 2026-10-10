# Rating Model Documentation
## Overview

The Rating module provides models for credit ratings, rating histories, and transition matrices used in credit risk calculations.

## Classes

### RatingAgency (Enum)

Credit rating agencies.

| Value | Name | Description |
|-------|------|-------------|
| `S&P` | `SP` | Standard & Poor's |
| `Moody's` | `MOODYS` | Moody's |
| `Fitch` | `FITCH` | Fitch Ratings |
| `Internal` | `INTERNAL` | Internal rating |

### RatingScale (Enum)

Standard rating scale (S&P equivalent).

| Value | Name | Description |
|-------|------|-------------|
| `AAA` | `AAA` | Yes |
| `AA+` | `AA_PLUS` | Yes |
| `AA` | `AA` | Yes |
| `AA-` | `AA_MINUS` | Yes |
| `A+` | `A_PLUS` | Yes |
| `A` | `A` | Yes |
| `A-` | `A_MINUS` | Yes |
| `BBB+` | `BBB_PLUS` | Yes |
| `BBB` | `BBB` | Yes |
| `BBB-` | `BBB_MINUS` | Yes (boundary) |
| `BB+` | `BB_PLUS` | No |
| `BB` | `BB` | No |
| `BB-` | `BB_MINUS` | No |
| `B+` | `B_PLUS` | No |
| `B` | `B` | No |
| `B-` | `B_MINUS` | No |
| `CCC+` | `CCC_PLUS` | No (distressed) |
| `CCC` | `CCC` | No (distressed) |
| `CCC-` | `CCC_MINUS` | No (distressed) |
| `CC` | `CC` | No (distressed) |
| `C` | `C` | No (distressed) |
| `D` | `D` | Default |
| `NR` | `NR` |  |

### RATING_PD_MAP

Mapping of ratings to annual PD (basis points).

| Rating | PD (bps) | PD (%) |
|--------|----------|--------|
| AAA | 1 | 0.01% |
| AA | 3 | 0.03% |
| A | 7 | 0.07% |
| BBB | 25 | 0.25% |
| BB | 125 | 1.25% |
| B | 550 | 5.50% |
| CCC | 2500 | 25.00% |

### CreditRating (Dataclass)

Credit rating for an entity.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `entity_id` | str | "" | Entity identifier |
| `rating` | RatingScale | BBB | Current rating |
| `agency` | RatingAgency | INTERNAL | Rating agency |
| `rating_date` | date | today | Rating date |
| `outlook` | str | "stable" | Rating outlook |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_pd()` | float | Annual PD (decimal) |
| `get_score()` | int | Numeric score |
| `is_investment_grade()` | bool | IG check |
| `is_speculative()` | bool | Speculative check |
| `is_distressed()` | bool | Distressed check |

### RatingHistory (Dataclass)

Historical ratings for an entity.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `entity_id` | str | '' | Entity identifier |
| `history` | List | list() | (date, rating) pairs |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add_rating(date, rating)` | None | Add to history |
| `get_rating_at_date(date)` | RatingScale | Rating at date |
| `get_upgrades()` | int | Count of upgrades |
| `get_downgrades()` | int | Count of downgrades |

### TransitionMatrix (Dataclass)

Rating transition probability matrix.

#### Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `matrix_id` | str | auto-generated | Unique identifier |
| `time_horizon` | float | 1.0 | Time horizon (years) |
| `ratings` | List | list() | Rating categories |
| `probabilities` | List | list() | Transition probs |

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_transition_prob(from, to)` | float | Transition probability |
| `get_default_prob(from)` | float | Default probability |

### create_default_transition_matrix()

Creates a standard 1-year transition matrix.

## Usage Examples

```python
from qlrisk.models import (
    CreditRating, RatingScale, RatingAgency,
    RatingHistory, TransitionMatrix,
    create_default_transition_matrix, RATING_PD_MAP
)
from datetime import date

# Create credit rating
rating = CreditRating(
    entity_id="CORP-001",
    rating=RatingScale.BBB,
    agency=RatingAgency.SP,
    rating_date=date(2024, 1, 1),
    outlook="stable"
)

# Get PD
pd = rating.get_pd()  # 0.0025 (25 bps)
print(f"PD: {pd:.4f} ({pd*10000:.0f} bps)")

# Check grade
if rating.is_investment_grade():
    print("Investment Grade")

# Rating history
history = RatingHistory(entity_id="CORP-001")
history.add_rating(date(2020, 1, 1), RatingScale.A)
history.add_rating(date(2022, 1, 1), RatingScale.BBB_PLUS)
history.add_rating(date(2024, 1, 1), RatingScale.BBB)

downgrades = history.get_downgrades()  # 2

# Transition matrix
tm = create_default_transition_matrix()
prob_bbb_to_bb = tm.get_transition_prob(RatingScale.BBB, RatingScale.BB)
prob_bbb_default = tm.get_default_prob(RatingScale.BBB)
```

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
