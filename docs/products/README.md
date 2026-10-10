# QLRisk - Products Documentation v2.2.0

<!-- legacy-examples -->
> ⚠️ **Some code samples on this page predate v2.0 and no longer match the API** (1 of 1 fail). Use the [user guides](../guides/README.md), whose examples are executed by the test suite, until this page is revised.
<!-- /legacy-examples -->

```
Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This documentation and the software it describes are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
```

---

## Overview

The Products module provides 81 financial product implementations across 12 asset classes, with both Python and QuantLib implementations available.

---

## Product Summary

| Category | Count | Products |
|----------|-------|----------|
| [Interest Rate](#interest-rate-8-products) | 8 | IRS, OIS, FRA, Cap, Floor, Swaption, Basis Swap |
| [FX](#fx-6-products) | 6 | Forward, Swap, Option, Barrier, NDF, Digital |
| [Credit](#credit-4-products) | 4 | CDS, CDS Index, TRS, CLN |
| [Equity](#equity-5-products) | 5 | Swap, Option, Forward, Variance, Dividend |
| [Commodity](#commodity-3-products) | 3 | Swap, Option, Forward |
| [Cross-Currency](#cross-currency-3-products) | 3 | XCCY Swap, Basis Swap, MTM Swap |
| [Repo](#repo-4-products) | 4 | Repo, Reverse, Securities Lending, Buy/Sell Back |
| [Money Market](#money-market-7-products) | 7 | CD, BA, Eurodollar, Fed Funds, MMF, TD, Discount Note |
| [Stocks](#stocks-8-products) | 8 | Common, ADR, GDR, Preferred, Warrant, ETF, MF, Index |
| [Alternatives](#alternatives-8-products) | 8 | Crypto (3), REIT, Carbon (2), PE, Hedge Fund |
| [Futures](#futures-5-products) | 5 | Index, IR, Bond, VIX, Single Stock |
| [Fixed Income](#fixed-income-20-products) | 20 | Treasuries, Gilts, Bunds, MBS, CDO, CLO, etc. |
| **Total** | **81** | |

---

## Interest Rate (8 Products)

| Product | File | Description |
|---------|------|-------------|
| [Interest Rate Swap](interest_rate/interest_rate_swap.md) | `interest_rate_swap.py` | Fixed-float interest rate swap |
| [Overnight Index Swap](interest_rate/overnight_index_swap.md) | `overnight_index_swap.py` | SOFR/€STR OIS |
| [Forward Rate Agreement](interest_rate/forward_rate_agreement.md) | `forward_rate_agreement.py` | FRA contracts |
| [Interest Rate Cap](interest_rate/interest_rate_cap.md) | `interest_rate_cap.py` | Cap option |
| [Interest Rate Floor](interest_rate/interest_rate_floor.md) | `interest_rate_floor.py` | Floor option |
| [Swaption](interest_rate/swaption.md) | `swaption.py` | Option on swap |
| [Basis Swap](interest_rate/basis_swap.md) | `basis_swap.py` | Float-float swap |

```python
from qlrisk.products.python import InterestRateSwap

irs = InterestRateSwap(
    notional=10_000_000,
    fixed_rate=0.03,
    float_index='SOFR',
    effective_date=date(2024, 1, 1),
    maturity_date=date(2029, 1, 1),
    payment_frequency='quarterly'
)
npv = irs.calculate_npv(market_data)
```

---

## FX (6 Products)

| Product | File | Description |
|---------|------|-------------|
| [FX Forward](fx/fx_forward.md) | `fx_forward.py` | Currency forward |
| [FX Swap](fx/fx_swap.md) | `fx_swap.py` | FX swap |
| [FX Option](fx/fx_option.md) | `fx_option.py` | Vanilla FX option |
| [FX Barrier Option](fx/fx_barrier_option.md) | `fx_barrier_option.py` | Knock-in/out option |
| [Non-Deliverable Forward](fx/ndf.md) | `non_deliverable_forward.py` | NDF |
| [FX Digital Option](fx/fx_digital.md) | `fx_digital_option.py` | Binary FX option |

---

## Credit (4 Products)

| Product | File | Description |
|---------|------|-------------|
| [Credit Default Swap](credit/credit_default_swap.md) | `credit_default_swap.py` | Single-name CDS |
| [CDS Index](credit/cds_index.md) | `cds_index.py` | CDX/iTraxx |
| [Total Return Swap](credit/total_return_swap.md) | `total_return_swap.py` | TRS |
| [Credit Linked Note](credit/credit_linked_note.md) | `credit_linked_note.py` | CLN |

---

## Equity (5 Products)

| Product | File | Description |
|---------|------|-------------|
| [Equity Swap](equity/equity_swap.md) | `equity_swap.py` | Equity total return swap |
| [Equity Option](equity/equity_option.md) | `equity_option.py` | Stock/index option |
| [Equity Forward](equity/equity_forward.md) | `equity_forward.py` | Equity forward |
| [Variance Swap](equity/variance_swap.md) | `variance_swap.py` | Variance swap |
| [Dividend Swap](equity/dividend_swap.md) | `dividend_swap.py` | Dividend swap |

---

## Commodity (3 Products)

| Product | File | Description |
|---------|------|-------------|
| [Commodity Swap](commodity/commodity_swap.md) | `commodity_swap.py` | Commodity swap |
| [Commodity Option](commodity/commodity_option.md) | `commodity_option.py` | Commodity option |
| [Commodity Forward](commodity/commodity_forward.md) | `commodity_forward.py` | Commodity forward |

---

## Cross-Currency (3 Products)

| Product | File | Description |
|---------|------|-------------|
| [Cross Currency Swap](cross_currency/cross_currency_swap.md) | `cross_currency_swap.py` | XCCY swap |
| [Cross Currency Basis Swap](cross_currency/cross_currency_basis_swap.md) | `cross_currency_basis_swap.py` | Basis swap |
| [MTM Cross Currency Swap](cross_currency/mtm_cross_currency_swap.md) | `mtm_cross_currency_swap.py` | Mark-to-market XCCY |

---

## Repo (4 Products)

| Product | File | Description |
|---------|------|-------------|
| [Repo](repo/repo.md) | `repo.py` | Repurchase agreement |
| [Reverse Repo](repo/reverse_repo.md) | `reverse_repo.py` | Reverse repo |
| [Securities Lending](repo/securities_lending.md) | `securities_lending.py` | Stock lending |
| [Buy Sell Back](repo/buy_sell_back.md) | `buy_sell_back.py` | Buy/sell back |

---

## Money Market (7 Products)

| Product | File | Description |
|---------|------|-------------|
| [Certificate of Deposit](money_market/certificate_of_deposit.md) | `certificate_of_deposit.py` | CD |
| [Bankers Acceptance](money_market/bankers_acceptance.md) | `bankers_acceptance.py` | BA |
| [Eurodollar Deposit](money_market/eurodollar_deposit.md) | `eurodollar_deposit.py` | Eurodollar |
| [Federal Funds](money_market/federal_funds.md) | `federal_funds.py` | Fed funds |
| [Money Market Fund](money_market/money_market_fund.md) | `money_market_fund.py` | MMF |
| [Time Deposit](money_market/time_deposit.md) | `time_deposit.py` | Term deposit |
| [Discount Note](money_market/discount_note.md) | `discount_note.py` | Discount note |

---

## Stocks (8 Products)

| Product | File | Description |
|---------|------|-------------|
| [Common Stock](stocks/common_stock.md) | `common_stock.py` | Equity shares |
| [ADR](stocks/adr.md) | `adr.py` | American Depositary Receipt |
| [GDR](stocks/gdr.md) | `gdr.py` | Global Depositary Receipt |
| [Preferred Stock](stocks/preferred_stock.md) | `preferred_stock.py` | Preferred shares |
| [Warrant](stocks/warrant.md) | `warrant.py` | Equity warrant |
| [ETF](stocks/etf.md) | `etf.py` | Exchange-traded fund |
| [Mutual Fund](stocks/mutual_fund.md) | `mutual_fund.py` | Mutual fund |
| [Index Position](stocks/index_position.md) | `index_position.py` | Index position |

---

## Alternatives (8 Products)

| Product | File | Description |
|---------|------|-------------|
| [Crypto Spot](alternatives/crypto_spot.md) | `crypto_spot.py` | Cryptocurrency spot |
| [Crypto Future](alternatives/crypto_future.md) | `crypto_future.py` | Crypto futures |
| [Crypto Perpetual](alternatives/crypto_perpetual.md) | `crypto_perpetual.py` | Perpetual swap |
| [REIT](alternatives/reit.md) | `reit.py` | Real estate investment trust |
| [Carbon Credit](alternatives/carbon_credit.md) | `carbon_credit.py` | Carbon credits |
| [Carbon Future](alternatives/carbon_future.md) | `carbon_future.py` | Carbon futures |
| [Private Equity Interest](alternatives/private_equity_interest.md) | `private_equity_interest.py` | PE fund interest |
| [Hedge Fund Interest](alternatives/hedge_fund_interest.md) | `hedge_fund_interest.py` | HF interest |

---

## Futures (5 Products)

| Product | File | Description |
|---------|------|-------------|
| [Index Future](futures/index_future.md) | `index_future.py` | Equity index future |
| [Interest Rate Future](futures/interest_rate_future.md) | `interest_rate_future.py` | IR future |
| [Bond Future](futures/bond_future.md) | `bond_future.py` | Bond future |
| [VIX Future](futures/vix_future.md) | `vix_future.py` | Volatility future |
| [Single Stock Future](futures/single_stock_future.md) | `single_stock_future.py` | SSF |

---

## Fixed Income (20 Products)

| Product | File | Description |
|---------|------|-------------|
| [Treasury Bill](fixed_income/treasury_bill.md) | `treasury_bill.py` | T-Bill |
| [Treasury Note](fixed_income/treasury_note.md) | `treasury_note.py` | T-Note |
| [Treasury Bond](fixed_income/treasury_bond.md) | `treasury_bond.py` | T-Bond |
| [TIPS](fixed_income/tips.md) | `tips.py` | Inflation-linked |
| [UK Gilt](fixed_income/uk_gilt.md) | `uk_gilt.py` | UK government |
| [German Bund](fixed_income/german_bund.md) | `german_bund.py` | German government |
| [JGB](fixed_income/jgb.md) | `jgb.py` | Japanese government |
| [French OAT](fixed_income/french_oat.md) | `french_oat.py` | French government |
| [Municipal Bond](fixed_income/municipal_bond.md) | `municipal_bond.py` | Munis |
| [Agency Bond](fixed_income/agency_bond.md) | `agency_bond.py` | Agency bonds |
| [Corporate Bond](fixed_income/corporate_bond.md) | `corporate_bond.py` | Corporate bonds |
| [Floating Rate Note](fixed_income/floating_rate_note.md) | `floating_rate_note.py` | FRN |
| [Convertible Bond](fixed_income/convertible_bond.md) | `convertible_bond.py` | Convertibles |
| [Commercial Paper](fixed_income/commercial_paper.md) | `commercial_paper.py` | CP |
| [Medium Term Note](fixed_income/medium_term_note.md) | `medium_term_note.py` | MTN |
| [MBS](fixed_income/mbs.md) | `mbs.py` | Mortgage-backed |
| [ABS](fixed_income/abs.md) | `abs.py` | Asset-backed |
| [CDO](fixed_income/cdo.md) | `cdo.py` | Collateralized debt |
| [CLO](fixed_income/clo.md) | `clo.py` | Collateralized loan |
| [Zero Coupon Bond](fixed_income/bond.md) | `zero_coupon_bond.py` | Zero coupon |

---

## See Also

- [Architecture](../architecture.md) - System design
- [Models](../models/README.md) - Model documentation
- [Calculators](../calculators/README.md) - Calculator documentation

---

*Document Version: 2.2.0*  
*Last Updated: December 2025*  
*Copyright © 2025-2030 Ashutosh Sinha. All Rights Reserved.*
