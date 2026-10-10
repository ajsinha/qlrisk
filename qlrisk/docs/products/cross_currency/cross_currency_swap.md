# Cross-Currency Swap v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Cross-Currency Swap |
| **Product Class** | Cross-Currency Derivatives |
| **Asset Class** | Interest Rate + FX |
| **Product Type** | XCCY_SWAP |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Cross-Currency Swap exchanges interest payments in different currencies. Includes initial and final exchange of principals at spot rate.

### Key Characteristics

- **Principal Exchange:** At start and maturity
- **Interest Payments:** In respective currencies
- **Basis Spread:** Additional spread on one leg
- **Uses:** Funding, hedging currency risk

---

## SA-CCR Treatment

XCCY swaps have both IR and FX components:

$$AddOn = AddOn_{IR,ccy1} + AddOn_{IR,ccy2} + AddOn_{FX}$$

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
