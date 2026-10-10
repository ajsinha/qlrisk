# RAROC Calculator Documentation v1.2.0

## Overview

The RAROC (Risk-Adjusted Return on Capital) Calculator computes the risk-adjusted profitability of trades and portfolios, comparing returns to the capital at risk.

## Formula

$$RAROC = \frac{Risk\text{-}Adjusted\ Return}{Economic\ Capital}$$

$$Risk\text{-}Adjusted\ Return = Revenue - Expected\ Loss - Operating\ Costs - Funding\ Costs$$

$$RAROC = \frac{NII + Fees - EL - OpCosts - FundingCosts}{EC}$$

Where:
- $NII$ = Net Interest Income
- $Fees$ = Fee income
- $EL$ = Expected Loss = PD × LGD × EAD
- $EC$ = Economic Capital

## Hurdle Rate

RAROC is compared against a hurdle rate (typically Cost of Equity):

$$Value\ Added = (RAROC - Hurdle\ Rate) \times EC$$

## Class: RAROCCalculator

### Input: RAROCInput

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `revenue` | float | 0.0 | Total revenue |
| `expected_loss` | float | 0.0 | Expected loss |
| `operating_costs` | float | 0.0 | Operating costs |
| `funding_costs` | float | 0.0 | Funding costs |
| `economic_capital` | float | 0.0 | Economic capital |
| `hurdle_rate` | float | 0.10 | Hurdle rate (10%) |
| `tax_rate` | float | 0.25 | Tax rate |

### Output: RAROCResult

| Field | Type | Description |
|-------|------|-------------|
| `raroc` | float | RAROC percentage |
| `risk_adjusted_return` | float | Numerator |
| `economic_capital` | float | Denominator |
| `value_added` | float | Economic profit |
| `exceeds_hurdle` | bool | Above hurdle rate |
| `after_tax_raroc` | float | After-tax RAROC |

## Usage Example

```python
from calculator.python import RAROCCalculator, RAROCInput

calculator = RAROCCalculator()

result = calculator.calculate(RAROCInput(
    revenue=5_000_000,
    expected_loss=500_000,
    operating_costs=1_000_000,
    funding_costs=500_000,
    economic_capital=20_000_000,
    hurdle_rate=0.12,
    tax_rate=0.25
))

print(f"RAROC: {result.raroc:.2%}")
print(f"Risk-Adjusted Return: ${result.risk_adjusted_return:,.2f}")
print(f"Economic Capital: ${result.economic_capital:,.2f}")
print(f"Value Added: ${result.value_added:,.2f}")
print(f"Exceeds Hurdle: {result.exceeds_hurdle}")
```

## Components Breakdown

### Revenue Components
- Spread income
- Fee income
- Trading gains
- Commission

### Cost Components
- Expected credit losses
- Operational costs
- Funding costs
- Capital costs

## Applications

1. **Trade Pricing**: Minimum spread to achieve target RAROC
2. **Portfolio Optimization**: Allocate capital to high-RAROC trades
3. **Performance Measurement**: Risk-adjusted profitability
4. **Limit Setting**: Capital-based limits

---

Copyright © 2025-2030, All Rights Reserved | Ashutosh Sinha
