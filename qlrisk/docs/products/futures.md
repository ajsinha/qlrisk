# Futures Products v1.1.0

## Overview

Exchange-traded standardized contracts for future delivery.

## Index Futures

| Product | Exchange | Multiplier | Underlying |
|---------|----------|------------|------------|
| **E-mini S&P 500 (ES)** | CME | $50 | S&P 500 |
| **E-mini NASDAQ (NQ)** | CME | $20 | NASDAQ-100 |
| **E-mini Dow (YM)** | CBOT | $5 | DJIA |
| **FTSE 100** | ICE | £10 | FTSE 100 |
| **DAX** | Eurex | €25 | DAX 40 |
| **Nikkei 225** | CME/OSE | ¥500 | Nikkei 225 |

## Interest Rate Futures

| Product | Exchange | Contract Size |
|---------|----------|---------------|
| **SOFR Future** | CME | $1,000,000 |
| **Eurodollar** | CME | $1,000,000 |
| **Fed Funds** | CBOT | $5,000,000 |

## Bond Futures

| Product | Tenor | Contract Size |
|---------|-------|---------------|
| **2-Year Note** | 2Y | $200,000 |
| **5-Year Note** | 5Y | $100,000 |
| **10-Year Note** | 10Y | $100,000 |
| **30-Year Bond** | 30Y | $100,000 |
| **Ultra Bond** | 20Y+ | $100,000 |

## VIX Futures

- Exchange: CFE
- Multiplier: $1,000
- Settlement: Cash
- Term structure: Typically in contango

## Pricing

Fair futures price:
```
F = S × exp((r - q) × T)
```

Where:
- S = Spot price
- r = Risk-free rate
- q = Dividend yield
- T = Time to expiry

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
