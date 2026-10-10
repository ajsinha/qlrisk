"""
QLRisk - New Products Examples v2.3.1
=====================================================

Examples for SFT products, Commodity Futures, Equity TRS, and Bond TRS.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from datetime import date, timedelta
from typing import Dict, Any

# Import products
from qlrisk.products.python import (
    # Commodity Futures
    CommodityFuture, CommodityFutureTerms, CommodityType, CommoditySubClass,
    # Equity TRS
    EquityTRS, EquityTRSType, EquityTRSTerms, TRSReturnType,
    # Bond TRS
    BondTRS, BondTRSTerms, BondTRSUnderlyingType, BondTRSReturnType,
    # SFT Products
    MarginLoan, MarginLoanTerms, MarginLoanType,
    CollateralSwap, CollateralQuality, CollateralLeg,
    TriPartyRepo, TriPartyRepoTerms, TriPartyAgent,
    PrimeBrokerage, PrimeBrokerageTerms, PBServiceType, PBPosition
)
from qlrisk.products.base import Currency, PaymentFrequency
from qlrisk.core import MarketData


def create_sample_market_data() -> MarketData:
    """Create sample market data for pricing."""
    return MarketData(
        valuation_date=date.today(),
        discount_curve={0.25: 0.05, 0.5: 0.05, 1.0: 0.05, 2.0: 0.052, 5.0: 0.055},
        forward_curve={0.25: 0.051, 0.5: 0.052, 1.0: 0.053},
        spot_rate=0.05,
        volatility=0.20
    )


# =============================================================================
# COMMODITY FUTURES EXAMPLES
# =============================================================================

def example_commodity_futures():
    """Examples of commodity futures contracts."""
    print("\n" + "="*60)
    print("COMMODITY FUTURES EXAMPLES")
    print("="*60)
    
    market_data = create_sample_market_data()
    
    # Example 1: Crude Oil WTI Future
    print("\n1. Crude Oil WTI Future (10 contracts)")
    print("-" * 40)
    
    oil_future = CommodityFuture(
        trade_id="COM-OIL-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=90),
        notional=750_000,  # 10 contracts × 1000 barrels × $75
        currency=Currency.USD,
        counterparty_id="NYMEX",
        terms=CommodityFutureTerms(
            commodity_type=CommodityType.CRUDE_OIL_WTI,
            contract_size=1000,  # 1000 barrels per contract
            num_contracts=10,
            futures_price=75.00,
            spot_price=74.50,
            exchange="NYMEX",
            contract_month="H25",  # March 2025
            settlement_type="physical"
        ),
        is_long=True
    )
    
    result = oil_future.price(market_data)
    saccr = oil_future.calculate_saccr(market_data)
    
    print(f"Trade ID: {oil_future.trade_id}")
    print(f"Commodity: {oil_future.terms.commodity_type.value}")
    print(f"Contracts: {oil_future.terms.num_contracts}")
    print(f"Contract Value: ${oil_future.get_contract_value():,.0f}")
    print(f"NPV: ${result.npv:,.2f}")
    print(f"SA-CCR EAD: ${saccr.ead:,.2f}")
    
    # Example 2: Gold Future
    print("\n2. Gold Future (5 contracts)")
    print("-" * 40)
    
    gold_future = CommodityFuture(
        trade_id="COM-GOLD-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=180),
        notional=1_000_000,
        currency=Currency.USD,
        counterparty_id="COMEX",
        terms=CommodityFutureTerms(
            commodity_type=CommodityType.GOLD,
            contract_size=100,  # 100 troy oz per contract
            num_contracts=5,
            futures_price=2050.00,
            spot_price=2040.00,
            exchange="COMEX"
        ),
        is_long=True
    )
    
    result = gold_future.price(market_data)
    print(f"Commodity: {gold_future.terms.commodity_type.value}")
    print(f"Contract Value: ${gold_future.get_contract_value():,.0f}")
    print(f"NPV: ${result.npv:,.2f}")
    
    # Example 3: Natural Gas Future (Short)
    print("\n3. Natural Gas Future - Short Position")
    print("-" * 40)
    
    ng_future = CommodityFuture(
        trade_id="COM-NG-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=60),
        notional=500_000,
        currency=Currency.USD,
        counterparty_id="NYMEX",
        terms=CommodityFutureTerms(
            commodity_type=CommodityType.NATURAL_GAS,
            contract_size=10000,  # 10,000 MMBtu
            num_contracts=20,
            futures_price=2.50,
            exchange="NYMEX"
        ),
        is_long=False  # Short position
    )
    
    result = ng_future.price(market_data)
    print(f"Position: SHORT")
    print(f"Contracts: {ng_future.terms.num_contracts}")
    print(f"NPV: ${result.npv:,.2f}")
    
    # Example 4: Agricultural - Corn Future
    print("\n4. Corn Future")
    print("-" * 40)
    
    corn_future = CommodityFuture(
        trade_id="COM-CORN-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=120),
        notional=200_000,
        currency=Currency.USD,
        counterparty_id="CBOT",
        terms=CommodityFutureTerms(
            commodity_type=CommodityType.CORN,
            contract_size=5000,  # 5000 bushels
            num_contracts=10,
            futures_price=4.50,  # Per bushel
            exchange="CBOT"
        ),
        is_long=True
    )
    
    result = corn_future.price(market_data)
    saccr = corn_future.calculate_saccr(market_data)
    print(f"Commodity: {corn_future.terms.commodity_type.value}")
    print(f"Contract Value: ${corn_future.get_contract_value():,.0f}")
    print(f"SA-CCR SF: {saccr.details['supervisory_factor']:.0%}")
    
    return oil_future, gold_future


# =============================================================================
# EQUITY TRS EXAMPLES
# =============================================================================

def example_equity_trs():
    """Examples of Equity Total Return Swaps."""
    print("\n" + "="*60)
    print("EQUITY TRS EXAMPLES")
    print("="*60)
    
    market_data = create_sample_market_data()
    
    # Example 1: Single Stock TRS
    print("\n1. Single Stock TRS - AAPL")
    print("-" * 40)
    
    aapl_trs = EquityTRS(
        trade_id="EQ-TRS-AAPL-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=365),
        notional=10_000_000,
        currency=Currency.USD,
        counterparty_id="PRIME-BROKER-001",
        terms=EquityTRSTerms(
            underlying_type=EquityTRSType.SINGLE_STOCK,
            underlying_ticker="AAPL",
            underlying_name="Apple Inc.",
            initial_price=180.00,
            current_price=185.00,  # 2.78% gain
            dividend_yield=0.005,  # 0.5% dividend yield
            return_type=TRSReturnType.TOTAL_RETURN,
            financing_spread=50,  # 50 bps over SOFR
            is_funded=True
        ),
        is_receiver=True,  # Receive total return
        payment_frequency=PaymentFrequency.QUARTERLY
    )
    
    result = aapl_trs.price(market_data)
    saccr = aapl_trs.calculate_saccr(market_data)
    
    print(f"Trade ID: {aapl_trs.trade_id}")
    print(f"Underlying: {aapl_trs.terms.underlying_ticker}")
    print(f"Notional: ${aapl_trs.notional:,.0f}")
    print(f"Direction: {'Receive' if aapl_trs.is_receiver else 'Pay'} Total Return")
    print(f"Total Return: {aapl_trs.get_underlying_return(market_data):.2%}")
    print(f"NPV: ${result.npv:,.2f}")
    print(f"SA-CCR EAD: ${saccr.ead:,.2f}")
    print(f"SA-CCR SF: {saccr.details['supervisory_factor']:.0%}")
    
    # Example 2: Index TRS
    print("\n2. Index TRS - S&P 500")
    print("-" * 40)
    
    spx_trs = EquityTRS(
        trade_id="EQ-TRS-SPX-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=365),
        notional=50_000_000,
        currency=Currency.USD,
        counterparty_id="DEALER-001",
        terms=EquityTRSTerms(
            underlying_type=EquityTRSType.EQUITY_INDEX,
            underlying_ticker="SPX",
            underlying_name="S&P 500 Index",
            initial_price=4800.00,
            current_price=4850.00,
            dividend_yield=0.015,
            financing_spread=25  # Tighter spread for index
        ),
        is_receiver=True
    )
    
    result = spx_trs.price(market_data)
    saccr = spx_trs.calculate_saccr(market_data)
    
    print(f"Underlying: {spx_trs.terms.underlying_name}")
    print(f"Notional: ${spx_trs.notional:,.0f}")
    print(f"NPV: ${result.npv:,.2f}")
    print(f"SA-CCR SF: {saccr.details['supervisory_factor']:.0%} (index)")
    
    # Example 3: ETF TRS
    print("\n3. ETF TRS - QQQ")
    print("-" * 40)
    
    qqq_trs = EquityTRS(
        trade_id="EQ-TRS-QQQ-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=180),
        notional=25_000_000,
        currency=Currency.USD,
        counterparty_id="PRIME-BROKER-002",
        terms=EquityTRSTerms(
            underlying_type=EquityTRSType.ETF,
            underlying_ticker="QQQ",
            initial_price=400.00,
            current_price=395.00,  # Down 1.25%
            financing_spread=35
        ),
        is_receiver=False  # Pay total return (short exposure)
    )
    
    result = qqq_trs.price(market_data)
    print(f"Position: {'Receive' if qqq_trs.is_receiver else 'Pay'} Total Return (Short)")
    print(f"NPV: ${result.npv:,.2f}")
    
    return aapl_trs, spx_trs


# =============================================================================
# BOND TRS EXAMPLES
# =============================================================================

def example_bond_trs():
    """Examples of Bond Total Return Swaps."""
    print("\n" + "="*60)
    print("BOND TRS EXAMPLES")
    print("="*60)
    
    market_data = create_sample_market_data()
    
    # Example 1: Investment Grade Corporate Bond TRS
    print("\n1. Corporate Bond TRS - BBB Rated")
    print("-" * 40)
    
    corp_trs = BondTRS(
        trade_id="BOND-TRS-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=365),
        notional=50_000_000,
        currency=Currency.USD,
        counterparty_id="DEALER-001",
        terms=BondTRSTerms(
            underlying_type=BondTRSUnderlyingType.CORPORATE_BOND,
            underlying_identifier="US123456789",
            issuer="ABC Corporation",
            initial_price=98.50,
            current_price=99.25,
            coupon_rate=0.05,  # 5% coupon
            credit_rating="BBB",
            modified_duration=5.2,
            financing_spread=75,  # 75 bps
            return_type=BondTRSReturnType.TOTAL_RETURN
        ),
        is_receiver=True
    )
    
    result = corp_trs.price(market_data)
    saccr = corp_trs.calculate_saccr(market_data)
    ccr = corp_trs.calculate_ccr_exposure(market_data)
    
    print(f"Trade ID: {corp_trs.trade_id}")
    print(f"Issuer: {corp_trs.terms.issuer}")
    print(f"Rating: {corp_trs.terms.credit_rating}")
    print(f"Notional: ${corp_trs.notional:,.0f}")
    print(f"Duration: {corp_trs.terms.modified_duration:.1f}")
    print(f"Total Return: {corp_trs.get_underlying_return(market_data):.2%}")
    print(f"NPV: ${result.npv:,.2f}")
    print(f"SA-CCR EAD: ${saccr.ead:,.2f}")
    print(f"SA-CCR SF: {saccr.details['supervisory_factor']:.2%}")
    print(f"CVA: ${ccr.cva:,.2f}")
    
    # Example 2: High Yield Bond TRS
    print("\n2. High Yield Bond TRS - BB Rated")
    print("-" * 40)
    
    hy_trs = BondTRS(
        trade_id="BOND-TRS-HY-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=365),
        notional=25_000_000,
        currency=Currency.USD,
        counterparty_id="DEALER-002",
        terms=BondTRSTerms(
            underlying_type=BondTRSUnderlyingType.HIGH_YIELD_BOND,
            issuer="XYZ Holdings",
            initial_price=95.00,
            current_price=92.00,  # Price decline
            coupon_rate=0.075,  # 7.5% coupon
            credit_rating="BB",
            modified_duration=4.0,
            financing_spread=150,  # Higher spread for HY
            recovery_rate=0.35
        ),
        is_receiver=True
    )
    
    result = hy_trs.price(market_data)
    saccr = hy_trs.calculate_saccr(market_data)
    
    print(f"Rating: {hy_trs.terms.credit_rating}")
    print(f"Coupon: {hy_trs.terms.coupon_rate:.1%}")
    print(f"Price Change: {(hy_trs.terms.current_price/hy_trs.terms.initial_price - 1):.1%}")
    print(f"NPV: ${result.npv:,.2f}")
    print(f"SA-CCR SF: {saccr.details['supervisory_factor']:.2%} (higher for HY)")
    
    # Example 3: Government Bond TRS
    print("\n3. Government Bond TRS - Treasury")
    print("-" * 40)
    
    govt_trs = BondTRS(
        trade_id="BOND-TRS-GOVT-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=365),
        notional=100_000_000,
        currency=Currency.USD,
        counterparty_id="DEALER-003",
        terms=BondTRSTerms(
            underlying_type=BondTRSUnderlyingType.GOVERNMENT_BOND,
            underlying_identifier="912810TM0",
            issuer="US Treasury",
            initial_price=99.00,
            current_price=98.50,
            coupon_rate=0.04,
            credit_rating="AAA",
            modified_duration=8.5,
            financing_spread=15  # Very tight for Treasuries
        ),
        is_receiver=True
    )
    
    result = govt_trs.price(market_data)
    saccr = govt_trs.calculate_saccr(market_data)
    
    print(f"Underlying: {govt_trs.terms.issuer}")
    print(f"Duration: {govt_trs.terms.modified_duration:.1f}")
    print(f"NPV: ${result.npv:,.2f}")
    print(f"Asset Class: {saccr.asset_class.value} (Interest Rate for govt)")
    print(f"SA-CCR SF: {saccr.details['supervisory_factor']:.2%}")
    
    return corp_trs, hy_trs


# =============================================================================
# SFT PRODUCTS EXAMPLES
# =============================================================================

def example_sft_products():
    """Examples of Securities Financing Transactions."""
    print("\n" + "="*60)
    print("SFT (SECURITIES FINANCING) EXAMPLES")
    print("="*60)
    
    market_data = create_sample_market_data()
    
    # Example 1: Margin Loan
    print("\n1. Margin Loan - Securities-Based Lending")
    print("-" * 40)
    
    margin_loan = MarginLoan(
        trade_id="ML-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=365),
        notional=5_000_000,  # Loan amount
        currency=Currency.USD,
        counterparty_id="HNW-CLIENT-001",
        terms=MarginLoanTerms(
            loan_type=MarginLoanType.PURPOSE,
            loan_to_value=0.50,  # 50% LTV
            interest_spread=150,  # 150 bps over benchmark
            maintenance_margin=0.35
        )
    )
    
    result = margin_loan.price(market_data)
    saccr = margin_loan.calculate_saccr(market_data)
    
    print(f"Trade ID: {margin_loan.trade_id}")
    print(f"Loan Amount: ${margin_loan.notional:,.0f}")
    print(f"LTV: {margin_loan.terms.loan_to_value:.0%}")
    print(f"NPV: ${result.npv:,.2f}")
    print(f"SA-CCR EAD: ${saccr.ead:,.2f}")
    
    # Example 2: Tri-Party Repo
    print("\n2. Tri-Party Repo")
    print("-" * 40)
    
    tri_party = TriPartyRepo(
        trade_id="TPR-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=30),
        notional=100_000_000,
        currency=Currency.USD,
        counterparty_id="MONEY-FUND-001",
        terms=TriPartyRepoTerms(
            agent=TriPartyAgent.BNY_MELLON,
            repo_rate=0.052,  # 5.2%
            haircut=0.02  # 2% haircut
        ),
        is_lender=True
    )
    
    result = tri_party.price(market_data)
    
    print(f"Principal: ${tri_party.notional:,.0f}")
    print(f"Agent: {tri_party.terms.agent.value}")
    print(f"Repo Rate: {tri_party.terms.repo_rate:.2%}")
    print(f"Haircut: {tri_party.terms.haircut:.1%}")
    print(f"NPV: ${result.npv:,.2f}")
    
    # Example 3: Collateral Swap
    print("\n3. Collateral Swap (Upgrade Trade)")
    print("-" * 40)
    
    coll_swap = CollateralSwap(
        trade_id="CS-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=180),
        notional=75_000_000,
        currency=Currency.USD,
        counterparty_id="BANK-002",
        give_leg=CollateralLeg(
            collateral_type="Corporate Bond",
            quality=CollateralQuality.HQLA_LEVEL_2B,
            market_value=75_000_000,
            haircut=0.25
        ),
        receive_leg=CollateralLeg(
            collateral_type="Treasury Bond",
            quality=CollateralQuality.HQLA_LEVEL_1,
            market_value=75_000_000,
            haircut=0.02
        )
    )
    
    result = coll_swap.price(market_data)
    
    print(f"Give: {coll_swap.give_leg.collateral_type} ({coll_swap.give_leg.quality.value})")
    print(f"Receive: {coll_swap.receive_leg.collateral_type} ({coll_swap.receive_leg.quality.value})")
    print(f"NPV: ${result.npv:,.2f}")
    
    # Example 4: Prime Brokerage
    print("\n4. Prime Brokerage Agreement")
    print("-" * 40)
    
    prime_brokerage = PrimeBrokerage(
        trade_id="PB-001",
        trade_date=date.today(),
        effective_date=date.today(),
        maturity_date=date.today() + timedelta(days=365),
        notional=500_000_000,  # Credit line
        currency=Currency.USD,
        counterparty_id="HEDGE-FUND-001",
        terms=PrimeBrokerageTerms(
            service_types=[PBServiceType.FULL_SERVICE],
            financing_rate_spread=40,  # 40 bps
            initial_margin_requirement=0.50,
            rehypothecation_allowed=True
        )
    )
    
    # Add some positions
    prime_brokerage.add_position(PBPosition(
        security_id="AAPL",
        security_type="equity",
        quantity=50000,
        market_value=9_000_000,
        is_long=True
    ))
    prime_brokerage.add_position(PBPosition(
        security_id="MSFT",
        security_type="equity",
        quantity=-20000,
        market_value=8_000_000,
        is_long=False  # Short
    ))
    
    result = prime_brokerage.price(market_data)
    
    print(f"Credit Line: ${prime_brokerage.notional:,.0f}")
    print(f"Long Market Value: ${prime_brokerage.get_long_market_value():,.0f}")
    print(f"Short Market Value: ${prime_brokerage.get_short_market_value():,.0f}")
    print(f"Net Market Value: ${prime_brokerage.get_net_market_value():,.0f}")
    print(f"Margin Required: ${prime_brokerage.get_margin_requirement():,.0f}")
    print(f"NPV: ${result.npv:,.2f}")
    
    return margin_loan, prime_brokerage


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("CCR ANALYTICS ENGINE - NEW PRODUCTS EXAMPLES v2.3.1")
    print("="*70)
    
    # Run examples
    example_commodity_futures()
    example_equity_trs()
    example_bond_trs()
    example_sft_products()
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("="*70)


if __name__ == "__main__":
    main()
