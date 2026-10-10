"""
QLRisk - Product Type Enumeration (v2.2.1)
=========================================================

Complete enumeration of all supported product types.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from enum import Enum, auto


class ProductType(Enum):
    """Enumeration of all supported product types."""
    
    # Interest Rate Derivatives
    IRS = "interest_rate_swap"
    OIS = "overnight_index_swap"
    FRA = "forward_rate_agreement"
    CAP = "interest_rate_cap"
    FLOOR = "interest_rate_floor"
    SWAPTION = "swaption"
    BASIS_SWAP = "basis_swap"
    
    # FX Products
    FX_FORWARD = "fx_forward"
    FX_SWAP = "fx_swap"
    FX_OPTION = "fx_option"
    FX_BARRIER = "fx_barrier_option"
    NDF = "non_deliverable_forward"
    FX_DIGITAL = "fx_digital_option"
    
    # Credit Products
    CDS = "credit_default_swap"
    CDS_INDEX = "cds_index"
    TRS = "total_return_swap"
    CLN = "credit_linked_note"
    
    # Equity Derivatives
    EQUITY_SWAP = "equity_swap"
    EQUITY_OPTION = "equity_option"
    EQUITY_FORWARD = "equity_forward"
    VARIANCE_SWAP = "variance_swap"
    DIVIDEND_SWAP = "dividend_swap"
    EQUITY_TRS = "equity_total_return_swap"
    
    # Commodity Products
    COMMODITY_SWAP = "commodity_swap"
    COMMODITY_OPTION = "commodity_option"
    COMMODITY_FORWARD = "commodity_forward"
    COMMODITY_FUTURE = "commodity_future"
    
    # Cross-Currency Products
    XCCY_SWAP = "cross_currency_swap"
    XCCY_BASIS = "cross_currency_basis_swap"
    MTM_XCCY = "mtm_cross_currency_swap"
    
    # Repo Products
    REPO = "repo"
    REVERSE_REPO = "reverse_repo"
    SECURITIES_LENDING = "securities_lending"
    BUY_SELL_BACK = "buy_sell_back"
    
    # Money Market Products
    CD = "certificate_of_deposit"
    BANKERS_ACCEPTANCE = "bankers_acceptance"
    EURODOLLAR = "eurodollar_deposit"
    FED_FUNDS = "federal_funds"
    MMF = "money_market_fund"
    TIME_DEPOSIT = "time_deposit"
    DISCOUNT_NOTE = "discount_note"
    
    # Stocks & ETFs
    COMMON_STOCK = "common_stock"
    ADR = "adr"
    GDR = "gdr"
    PREFERRED_STOCK = "preferred_stock"
    WARRANT = "warrant"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    INDEX_POSITION = "index_position"
    
    # Alternative Investments
    CRYPTO_SPOT = "crypto_spot"
    CRYPTO_FUTURE = "crypto_future"
    CRYPTO_PERPETUAL = "crypto_perpetual"
    REIT = "reit"
    CARBON_CREDIT = "carbon_credit"
    CARBON_FUTURE = "carbon_future"
    PE_INTEREST = "private_equity_interest"
    HF_INTEREST = "hedge_fund_interest"
    
    # Futures
    INDEX_FUTURE = "index_future"
    IR_FUTURE = "interest_rate_future"
    BOND_FUTURE = "bond_future"
    VIX_FUTURE = "vix_future"
    SSF = "single_stock_future"
    
    # Fixed Income - Government
    TREASURY_BILL = "treasury_bill"
    TREASURY_NOTE = "treasury_note"
    TREASURY_BOND = "treasury_bond"
    TIPS = "tips"
    UK_GILT = "uk_gilt"
    GERMAN_BUND = "german_bund"
    JGB = "jgb"
    FRENCH_OAT = "french_oat"
    
    # Fixed Income - Other
    MUNICIPAL_BOND = "municipal_bond"
    AGENCY_BOND = "agency_bond"
    CORPORATE_BOND = "corporate_bond"
    FRN = "floating_rate_note"
    CONVERTIBLE_BOND = "convertible_bond"
    COMMERCIAL_PAPER = "commercial_paper"
    MTN = "medium_term_note"
    BOND_TRS = "bond_total_return_swap"
    
    # Fixed Income - Structured
    MBS = "mortgage_backed_securities"
    ABS = "asset_backed_securities"
    CDO = "collateralized_debt_obligation"
    CLO = "collateralized_loan_obligation"
    ZERO_COUPON_BOND = "zero_coupon_bond"
    
    # Government Bond (generic)
    GOVERNMENT_BOND = "government_bond"
    
    # Securities Financing Transactions (SFT)
    SECURITIES_BORROWING = "securities_borrowing"
    MARGIN_LENDING = "margin_lending"
    COLLATERAL_SWAP = "collateral_swap"


__all__ = ["ProductType"]
