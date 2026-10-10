# Repo (Repurchase Agreement) v1.2.0

## Product Overview

| Attribute | Value |
|-----------|-------|
| **Product Name** | Repurchase Agreement (Repo) |
| **Product Class** | Securities Financing |
| **Asset Class** | Repo |
| **Product Type** | REPO |
| **Implementation** | Python ✓ | QuantLib ○ |

---

## Description

A Repo is a sale of securities with an agreement to repurchase at a higher price. It's effectively a collateralized loan where the securities serve as collateral.

### Key Characteristics

- **Cash Borrower:** Sells securities, agrees to repurchase
- **Cash Lender:** Buys securities, agrees to resell
- **Repo Rate:** Interest rate on the cash
- **Haircut:** Margin/overcollateralization

---

## Mathematical Framework

### Repo Rate

$$Repo Rate = \frac{Repurchase Price - Purchase Price}{Purchase Price} \times \frac{360}{Days}$$

### Haircut

$$Haircut = 1 - \frac{Cash}{Collateral MV}$$

---

## SA-CCR Treatment

Securities financing transactions (SFTs) have specific treatment:

$$EAD = max(0, E - C) + AddOn$$

---

Copyright © 2025-2030, All Rights Reserved  
Ashutosh Sinha | Email: ajsinha@gmail.com
