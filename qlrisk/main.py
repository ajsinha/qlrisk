#!/usr/bin/env python3
"""
QLRisk - Main Execution Script
=============================================

This script demonstrates QLRisk capabilities including:
- Data generation for testing
- Calculator demonstrations (Python and QuantLib)
- Performance benchmarking between implementations
- Stress testing scenarios
- Full CCR metrics calculation

Usage:
    python main.py                    # Run full demonstration
    python main.py --benchmark        # Run performance benchmarks only
    python main.py --stress           # Run stress testing only
    python main.py --quick            # Quick demonstration

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.
"""

import argparse
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# ============================================================================
# FIX FOR RUNNING AS SCRIPT OR MODULE
# ============================================================================
# When running directly (python main.py), we need to set up the package context
# so that relative imports work correctly.

if __name__ == "__main__" and __package__ is None:
    # Running as script - add parent directory to path and set package
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _parent_dir = os.path.dirname(_script_dir)
    if _parent_dir not in sys.path:
        sys.path.insert(0, _parent_dir)
    __package__ = "qlrisk"

# Now imports will work whether run as script or module
from qlrisk.core import PropertiesConfigurator, get_logger, Timer
from qlrisk.engine import CCREngine, EngineStatus
from qlrisk.calculator import CalculatorFactory, CalculatorType, ImplementationType
from qlrisk.data import DataGenerator, create_test_dataset, ProductType
from qlrisk.mathlib import MathFactory, ProcessType
from qlrisk.config import get_default_config_file


# Initialize logger
logger = get_logger(__name__)


def print_header(title: str, char: str = "=", width: int = 80) -> None:
    """Print a formatted header."""
    print("\n" + char * width)
    print(f" {title}")
    print(char * width)


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n--- {title} ---")


def format_currency(value: float) -> str:
    """Format a value as currency."""
    if value is None:
        return "N/A"
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format a value as percentage."""
    if value is None:
        return "N/A"
    return f"{value:.4%}"


def format_bps(value: float) -> str:
    """Format a value as basis points."""
    if value is None:
        return "N/A"
    return f"{value * 10000:.2f} bps"


class QLRiskDemo:
    """
    Demonstration class for QLRisk.
    
    Provides methods to demonstrate various capabilities of the engine
    including data generation, calculations, benchmarking, and stress testing.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the demo with optional configuration."""
        self.config_path = config_path or str(get_default_config_file())
        
        # Try to load configuration
        try:
            if Path(self.config_path).exists():
                self.config = PropertiesConfigurator(self.config_path)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self.config = PropertiesConfigurator()
        except Exception as e:
            logger.warning(f"Could not load configuration: {e}")
            self.config = None
        
        # Initialize components
        self.data_generator = DataGenerator()
        self.calc_factory = CalculatorFactory()
        self.math_factory = MathFactory()
        
        # Check QuantLib availability
        self._check_quantlib()
    
    def _check_quantlib(self) -> None:
        """Check if QuantLib is available."""
        try:
            import QuantLib
            self.quantlib_available = True
            logger.info(f"QuantLib version {QuantLib.__version__} available")
        except ImportError:
            self.quantlib_available = False
            logger.warning("QuantLib not available - using Python implementations only")
    
    def run_full_demo(self) -> None:
        """Run the full demonstration."""
        print_header("QLRisk - Full Demonstration")
        print(f"\nStart Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"QuantLib Available: {self.quantlib_available}")
        
        with Timer("Full Demonstration"):
            self.demo_data_generation()
            self.demo_individual_calculators()
            self.demo_engine_calculations()
            self.demo_path_generation()
            if self.quantlib_available:
                self.demo_benchmarks()
            self.demo_stress_testing()
        
        print_header("Demonstration Complete", "=", 80)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def demo_data_generation(self) -> None:
        """Demonstrate data generation capabilities."""
        print_header("1. Data Generation", "-", 60)
        
        # Generate counterparty
        print_section("Counterparty Generation")
        counterparty = self.data_generator.generate_counterparty()
        print(f"  ID: {counterparty.counterparty_id}")
        print(f"  Name: {counterparty.name}")
        print(f"  Rating: {counterparty.rating.name}")
        print(f"  PD: {format_percentage(counterparty.pd)}")
        print(f"  LGD: {format_percentage(counterparty.lgd)}")
        print(f"  Sector: {counterparty.sector}")
        print(f"  Country: {counterparty.country}")
        
        # Generate trades
        print_section("Trade Generation")
        for product_type in [ProductType.IRS, ProductType.FX_FORWARD, ProductType.CDS]:
            trade = self.data_generator.generate_trade(counterparty.counterparty_id, product_type)
            print(f"  {product_type.value}:")
            print(f"    Trade ID: {trade.trade_id}")
            print(f"    Notional: {format_currency(trade.notional)}")
            print(f"    Currency: {trade.currency}")
            print(f"    MTM: {format_currency(trade.mtm)}")
        
        # Generate market data
        print_section("Market Data Generation")
        market_data = self.data_generator.generate_market_data()
        print(f"  Valuation Date: {market_data.valuation_date}")
        print(f"  Discount Rate: {format_percentage(market_data.discount_rate)}")
        print(f"  FX Rates: {dict(list(market_data.fx_rates.items())[:3])}...")
        print(f"  Volatilities: {dict(list(market_data.volatilities.items())[:3])}...")
        
        # Generate full portfolio
        print_section("Portfolio Generation")
        with Timer("Portfolio Generation"):
            counterparties, trades = self.data_generator.generate_portfolio(
                num_counterparties=5,
                trades_per_counterparty=(3, 5)
            )
        print(f"  Counterparties: {len(counterparties)}")
        print(f"  Trades: {len(trades)}")
        print(f"  Total Notional: {format_currency(sum(t.notional for t in trades))}")
        print(f"  Total MTM: {format_currency(sum(t.mtm for t in trades))}")
    
    def demo_individual_calculators(self) -> None:
        """Demonstrate individual calculator usage."""
        print_header("2. Individual Calculators", "-", 60)
        
        # Proper input data for each calculator type
        # PD Input - using rating-based model
        pd_data = {
            "credit_rating": "BBB",
            "rating_pd": 0.002,  # 0.2% PD for BBB
            "time_horizon": 1.0,
        }
        
        # LGD Input
        lgd_data = {
            "seniority": "senior_secured",
            "collateral_type": "real_estate",
            "collateral_value": 5_000_000,
            "exposure_value": 10_000_000,
        }
        
        # EAD Input
        ead_data = {
            "current_exposure": 250_000,  # Current MTM
            "notional": 10_000_000,
            "credit_conversion_factor": 1.0,
            "collateral_value": 0,
        }
        
        # EL Input (requires PD, LGD, EAD)
        el_data = {
            "pd": 0.02,  # 2%
            "lgd": 0.45,  # 45%
            "ead": 10_000_000,
            "time_horizon": 1.0,
        }
        
        # CE Input
        ce_data = {
            "mark_to_market": 250_000,
            "collateral_held": 0,
            "collateral_posted": 0,
        }
        
        # PFE Input
        pfe_data = {
            "current_mtm": 250_000,
            "notional": 10_000_000,
            "remaining_maturity": 5.0,
            "volatility": 0.20,
            "product_type": "irs",
        }
        
        # EE Input
        ee_data = {
            "current_mtm": 250_000,
            "notional": 10_000_000,
            "remaining_maturity": 5.0,
            "volatility": 0.20,
            "product_type": "irs",
        }
        
        # CVA Input (requires EE profile)
        time_grid = [0.25, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0]
        ee_profile = [250_000 * (1 + 0.1 * t) for t in time_grid]  # Simple EE growth
        cva_data = {
            "ee_profile": ee_profile,
            "time_grid": time_grid,
            "credit_spread": 0.01,  # 100 bps
            "recovery_rate": 0.40,
            "risk_free_rate": 0.05,
        }
        
        # EC Input (requires portfolio data)
        ec_data = {
            "exposures": [10_000_000, 5_000_000, 8_000_000],
            "pds": [0.02, 0.01, 0.03],
            "lgds": [0.45, 0.40, 0.50],
            "asset_correlation": 0.20,
        }
        
        # RAROC uses same as EC
        raroc_data = ec_data.copy()
        
        # IM Input
        im_data = {
            "notional": 10_000_000,
            "product_type": "irs",
            "remaining_maturity": 5.0,
            "volatility": 0.20,
        }
        
        # Map calculator types to their proper data
        calculator_data = {
            "pd": (pd_data, "Probability of Default", {"model": "transition_matrix"}),
            "lgd": (lgd_data, "Loss Given Default", {}),
            "ead": (ead_data, "Exposure at Default", {}),
            "el": (el_data, "Expected Loss", {}),
            "ce": (ce_data, "Current Exposure", {}),
            "pfe": (pfe_data, "Potential Future Exposure", {}),
            "ee": (ee_data, "Expected Exposure", {}),
            "cva": (cva_data, "Credit Valuation Adjustment", {}),
            "ec": (ec_data, "Economic Capital", {}),
            "raroc": (raroc_data, "Risk-Adjusted Return on Capital", {}),
            "im": (im_data, "Initial Margin", {}),
        }
        
        print_section("Python Implementations")
        for calc_type, (data, calc_name, config) in calculator_data.items():
            try:
                calc = self.calc_factory.get_calculator(calc_type, config=config, implementation="python")
                result = calc.calculate(data)
                
                if isinstance(result.value, dict):
                    primary_value = result.value.get("value", result.value.get(calc_type, "N/A"))
                else:
                    primary_value = result.value
                
                if isinstance(primary_value, (int, float)):
                    if calc_type in ["pd", "lgd", "raroc"]:
                        formatted = format_percentage(primary_value)
                    else:
                        formatted = format_currency(primary_value)
                else:
                    formatted = str(primary_value)
                
                print(f"  {calc_name}: {formatted}")
            except Exception as e:
                print(f"  {calc_name}: Error - {e}")
        
        if self.quantlib_available:
            print_section("QuantLib Implementations")
            for calc_type, (data, calc_name, config) in calculator_data.items():
                try:
                    calc = self.calc_factory.get_calculator(calc_type, config=config, implementation="quantlib")
                    result = calc.calculate(data)
                    
                    if isinstance(result.value, dict):
                        primary_value = result.value.get("value", result.value.get(calc_type, "N/A"))
                    else:
                        primary_value = result.value
                    
                    if isinstance(primary_value, (int, float)):
                        if calc_type in ["pd", "lgd", "raroc"]:
                            formatted = format_percentage(primary_value)
                        else:
                            formatted = format_currency(primary_value)
                    else:
                        formatted = str(primary_value)
                    
                    print(f"  {calc_name}: {formatted}")
                except Exception as e:
                    print(f"  {calc_name}: Error - {e}")
    
    def demo_engine_calculations(self) -> None:
        """Demonstrate the CCR Engine calculations."""
        print_header("3. CCR Engine Calculations", "-", 60)
        
        trade_data = {
            "trade_id": "ENGINE-001",
            "notional": 25_000_000,
            "mtm": 500_000,
            "maturity": 7.0,
            "volatility": 0.25,
            "counterparty_pd": 0.015,
            "counterparty_lgd": 0.50,
            "rating": "A",
            "discount_rate": 0.045,
            "recovery_rate": 0.45,
            "confidence_level": 0.99,
            "time_horizon": 1.0,
            "spread": 0.012,
        }
        
        print_section("Engine Status")
        with CCREngine() as engine:
            print(f"  Status: {engine.status.value}")
            print(f"  Max Workers: {engine._max_workers}")
            print(f"  Default Implementation: {engine._default_implementation}")
            
            print_section("Full CCR Metrics Calculation")
            with Timer("CCR Metrics"):
                results = engine.calculate_ccr_metrics(trade_data)
            
            print(f"\n  Trade: {trade_data['trade_id']}")
            print(f"  Notional: {format_currency(trade_data['notional'])}")
            print(f"  Current MTM: {format_currency(trade_data['mtm'])}")
            print(f"\n  Calculated Metrics:")
            print(f"    PD: {format_percentage(results.get('pd', 0))}")
            print(f"    LGD: {format_percentage(results.get('lgd', 0))}")
            print(f"    EAD: {format_currency(results.get('ead', 0))}")
            print(f"    Expected Loss: {format_currency(results.get('el', 0))}")
            print(f"    Current Exposure: {format_currency(results.get('ce', 0))}")
            print(f"    Expected Exposure: {format_currency(results.get('ee', 0))}")
            print(f"    PFE (99%): {format_currency(results.get('pfe', 0))}")
            print(f"    CVA: {format_currency(results.get('cva', 0))}")
            print(f"    Economic Capital: {format_currency(results.get('ec', 0))}")
            print(f"    Initial Margin: {format_currency(results.get('im', 0))}")
            
            # Portfolio calculation
            print_section("Portfolio Calculation")
            counterparties, trades = self.data_generator.generate_portfolio(
                num_counterparties=3,
                trades_per_counterparty=(2, 3)
            )
            
            total_el = 0
            total_cva = 0
            total_pfe = 0
            
            for trade in trades:
                counterparty = next(
                    (c for c in counterparties if c.counterparty_id == trade.counterparty_id),
                    None
                )
                
                if counterparty:
                    trade_input = {
                        "trade_id": trade.trade_id,
                        "notional": trade.notional,
                        "mtm": trade.mtm,
                        "maturity": (trade.maturity_date - trade.start_date).days / 365.0,
                        "volatility": 0.20,
                        "counterparty_pd": counterparty.pd,
                        "counterparty_lgd": counterparty.lgd,
                        "rating": counterparty.rating.name,
                        "discount_rate": 0.05,
                        "recovery_rate": 1 - counterparty.lgd,
                        "confidence_level": 0.99,
                        "time_horizon": 1.0,
                    }
                    
                    metrics = engine.calculate_ccr_metrics(trade_input)
                    total_el += metrics.get("el", 0) or 0
                    total_cva += metrics.get("cva", 0) or 0
                    total_pfe += metrics.get("pfe", 0) or 0
            
            print(f"  Portfolio Total Expected Loss: {format_currency(total_el)}")
            print(f"  Portfolio Total CVA: {format_currency(total_cva)}")
            print(f"  Portfolio Total PFE: {format_currency(total_pfe)}")
            
            # Engine statistics
            print_section("Engine Statistics")
            stats = engine.statistics if hasattr(engine, "statistics") else {}
            print(f"  Total Calculations: {stats.get('total_calculations', 0)}")
            print(f"  Successful: {stats.get('successful_calculations', 0)}")
            print(f"  Failed: {stats.get('failed_calculations', 0)}")
            if stats.get('avg_execution_time'):
                print(f"  Avg Execution Time: {stats['avg_execution_time']:.4f}s")
    
    def demo_path_generation(self) -> None:
        """Demonstrate path generation capabilities."""
        print_header("4. Path Generation", "-", 60)
        
        from qlrisk.mathlib import PathGenerationParams, PathResult
        
        # Path generation parameters
        params = PathGenerationParams(
            initial_value=100.0,
            drift=0.05,
            volatility=0.20,
            maturity=1.0,
            num_steps=252,
            num_paths=1000,
        )
        
        processes = [
            (ProcessType.GBM, "Geometric Brownian Motion"),
            (ProcessType.OU, "Ornstein-Uhlenbeck"),
            (ProcessType.CIR, "Cox-Ingersoll-Ross"),
            (ProcessType.VASICEK, "Vasicek"),
        ]
        
        print_section("Python Path Generator")
        python_gen = self.math_factory.create_path_generator(implementation="python")
        
        for process_type, process_name in processes:
            params.process_type = process_type
            if process_type in [ProcessType.OU, ProcessType.CIR, ProcessType.VASICEK]:
                params.mean_reversion_speed = 0.5
                params.long_term_mean = 100.0
            
            with Timer(process_name) as timer:
                result = python_gen.generate_paths(params)
            
            final_values = result.paths[:, -1]
            print(f"  {process_name}:")
            print(f"    Mean: {final_values.mean():.4f}")
            print(f"    Std: {final_values.std():.4f}")
            print(f"    Min: {final_values.min():.4f}")
            print(f"    Max: {final_values.max():.4f}")
            print(f"    Time: {timer.elapsed:.4f}s")
        
        if self.quantlib_available:
            print_section("QuantLib Path Generator")
            try:
                ql_gen = self.math_factory.create_path_generator(implementation="quantlib")
                
                for process_type, process_name in processes:
                    params.process_type = process_type
                    if process_type in [ProcessType.OU, ProcessType.CIR, ProcessType.VASICEK]:
                        params.mean_reversion_speed = 0.5
                        params.long_term_mean = 100.0
                    
                    with Timer(process_name) as timer:
                        result = ql_gen.generate_paths(params)
                    
                    final_values = result.paths[:, -1]
                    print(f"  {process_name}:")
                    print(f"    Mean: {final_values.mean():.4f}")
                    print(f"    Std: {final_values.std():.4f}")
                    print(f"    Time: {timer.elapsed:.4f}s")
            except Exception as e:
                print(f"  QuantLib path generation error: {e}")
    
    def demo_benchmarks(self) -> None:
        """Run performance benchmarks between Python and QuantLib."""
        print_header("5. Performance Benchmarks", "-", 60)
        
        if not self.quantlib_available:
            print("  QuantLib not available - skipping benchmarks")
            return
        
        # Proper input data for each calculator type
        benchmark_inputs = {
            CalculatorType.PD: {
                "credit_rating": "BBB",
                "rating_pd": 0.002,
                "time_horizon": 1.0,
            },
            CalculatorType.LGD: {
                "seniority": "senior_unsecured",
                "collateral_value": 0,
                "exposure_value": 10_000_000,
            },
            CalculatorType.EAD: {
                "current_exposure": 250_000,
                "notional": 10_000_000,
                "credit_conversion_factor": 1.0,
            },
            CalculatorType.EL: {
                "pd": 0.02,
                "lgd": 0.45,
                "ead": 10_000_000,
                "time_horizon": 1.0,
            },
            CalculatorType.CE: {
                "mark_to_market": 250_000,
                "collateral_held": 0,
                "collateral_posted": 0,
            },
            CalculatorType.PFE: {
                "current_mtm": 250_000,
                "notional": 10_000_000,
                "remaining_maturity": 5.0,
                "volatility": 0.20,
                "product_type": "irs",
            },
            CalculatorType.EE: {
                "current_mtm": 250_000,
                "notional": 10_000_000,
                "remaining_maturity": 5.0,
                "volatility": 0.20,
                "product_type": "irs",
            },
            CalculatorType.CVA: {
                "ee_profile": [250_000 * (1 + 0.1 * t) for t in [0.25, 0.5, 1.0, 2.0, 3.0, 5.0]],
                "time_grid": [0.25, 0.5, 1.0, 2.0, 3.0, 5.0],
                "credit_spread": 0.01,
                "recovery_rate": 0.40,
                "risk_free_rate": 0.05,
            },
            CalculatorType.EC: {
                "exposures": [10_000_000, 5_000_000, 8_000_000],
                "pds": [0.02, 0.01, 0.03],
                "lgds": [0.45, 0.40, 0.50],
                "asset_correlation": 0.20,
            },
        }
        
        calculators_to_benchmark = [
            (CalculatorType.PD, "Probability of Default"),
            (CalculatorType.LGD, "Loss Given Default"),
            (CalculatorType.EAD, "Exposure at Default"),
            (CalculatorType.EL, "Expected Loss"),
            (CalculatorType.CE, "Current Exposure"),
            (CalculatorType.PFE, "Potential Future Exposure"),
            (CalculatorType.EE, "Expected Exposure"),
            (CalculatorType.CVA, "Credit Valuation Adjustment"),
            (CalculatorType.EC, "Economic Capital"),
        ]
        
        iterations = 50
        
        print(f"\n  Running {iterations} iterations per calculator...")
        print(f"\n  {'Calculator':<35} {'Python':>12} {'QuantLib':>12} {'Speedup':>10}")
        print("  " + "-" * 70)
        
        with CCREngine() as engine:
            for calc_type, calc_name in calculators_to_benchmark:
                try:
                    benchmark_data = benchmark_inputs.get(calc_type, {})
                    result = engine.benchmark(
                        calculator_type=calc_type,
                        input_data=benchmark_data,
                        iterations=iterations
                    )
                    
                    python_time = result.get("python_avg_time", 0) * 1000  # ms
                    ql_time = result.get("quantlib_avg_time", 0) * 1000  # ms
                    speedup = result.get("speedup", 1.0)
                    
                    print(f"  {calc_name:<35} {python_time:>10.3f}ms {ql_time:>10.3f}ms {speedup:>9.2f}x")
                except Exception as e:
                    print(f"  {calc_name:<35} Error: {e}")
        
        # Path generation benchmark
        print_section("Path Generation Benchmark")
        from qlrisk.mathlib import PathGenerationParams
        
        params = PathGenerationParams(
            initial_value=100.0,
            drift=0.05,
            volatility=0.20,
            maturity=1.0,
            num_steps=252,
            num_paths=10000,
        )
        
        # Python
        python_gen = self.math_factory.create_path_generator(implementation="python")
        start = time.time()
        for _ in range(10):
            python_gen.generate_paths(params)
        python_time = (time.time() - start) / 10
        
        # QuantLib
        try:
            ql_gen = self.math_factory.create_path_generator(implementation="quantlib")
            start = time.time()
            for _ in range(10):
                ql_gen.generate_paths(params)
            ql_time = (time.time() - start) / 10
            
            speedup = python_time / ql_time if ql_time > 0 else 1.0
            
            print(f"  10,000 paths x 252 steps (GBM):")
            print(f"    Python: {python_time*1000:.2f}ms")
            print(f"    QuantLib: {ql_time*1000:.2f}ms")
            print(f"    Speedup: {speedup:.2f}x")
        except Exception as e:
            print(f"  QuantLib benchmark error: {e}")
    
    def demo_stress_testing(self) -> None:
        """Demonstrate stress testing capabilities."""
        print_header("6. Stress Testing", "-", 60)
        
        # Historical stress scenarios
        print_section("Historical Stress Scenarios")
        
        scenarios = ["2008_crisis", "covid_2020", "eu_debt_2011", "rate_shock_up"]
        
        try:
            stress_calc = self.calc_factory.get_calculator("stressed_exposure", implementation="python")
            
            # Sample trade for stress testing
            base_mtm = 500_000
            print(f"  Base Trade MTM: {format_currency(base_mtm)}")
            print()
            
            for scenario in scenarios:
                stress_data = {
                    "current_mtm": base_mtm,
                    "notional": 10_000_000,
                    "remaining_maturity": 5.0,
                    "volatility": 0.20,
                    "product_type": "irs",
                    "stress_type": "historical",
                    "stress_scenario": scenario,
                }
                
                try:
                    result = stress_calc.calculate(stress_data)
                    
                    if hasattr(result.value, 'stressed_exposure'):
                        stressed_exp = result.value.stressed_exposure
                        stress_mult = result.value.stress_multiplier
                    elif isinstance(result.value, dict):
                        stressed_exp = result.value.get("stressed_exposure", base_mtm)
                        stress_mult = result.value.get("stress_multiplier", 1.0)
                    else:
                        stressed_exp = result.value
                        stress_mult = stressed_exp / base_mtm if base_mtm > 0 else 1.0
                    
                    impact = (stressed_exp - base_mtm) / base_mtm if base_mtm > 0 else 0
                    
                    print(f"  {scenario.replace('_', ' ').title()}:")
                    print(f"    Stressed Exposure: {format_currency(stressed_exp)}")
                    print(f"    Stress Multiplier: {stress_mult:.2f}x")
                    print(f"    Impact: {format_percentage(impact)}")
                except Exception as e:
                    print(f"  {scenario}: Error - {e}")
        except Exception as e:
            print(f"  Stress calculation error: {e}")
        
        # Sensitivity analysis
        print_section("Sensitivity Analysis")
        try:
            # Hypothetical stress for sensitivity
            stress_calc = self.calc_factory.get_calculator("stressed_exposure", implementation="python")
            
            sensitivity_data = {
                "current_mtm": 500_000,
                "notional": 10_000_000,
                "remaining_maturity": 5.0,
                "volatility": 0.20,
                "product_type": "irs",
                "stress_type": "hypothetical",
                "rate_shock": 100,  # 100 bps rate shock
            }
            
            result = stress_calc.calculate(sensitivity_data)
            
            if hasattr(result.value, 'stressed_exposure'):
                stressed_exp = result.value.stressed_exposure
            elif isinstance(result.value, dict):
                stressed_exp = result.value.get("stressed_exposure", 500_000)
            else:
                stressed_exp = result.value
            
            print("  Portfolio Sensitivities (100bp rate shock):")
            print(f"    DV01 Impact: {format_currency(stressed_exp - 500_000)}")
            
            # Additional sensitivity tests
            fx_shock_data = {
                "current_mtm": 500_000,
                "notional": 10_000_000,
                "remaining_maturity": 5.0,
                "volatility": 0.20,
                "product_type": "fx_forward",
                "stress_type": "hypothetical",
                "fx_shock": 0.10,  # 10% FX shock
            }
            
            result = stress_calc.calculate(fx_shock_data)
            if hasattr(result.value, 'stressed_exposure'):
                fx_stressed = result.value.stressed_exposure
            elif isinstance(result.value, dict):
                fx_stressed = result.value.get("stressed_exposure", 500_000)
            else:
                fx_stressed = result.value
            
            print(f"    FX Delta (10% shock): {format_currency(fx_stressed - 500_000)}")
            
        except Exception as e:
            print(f"  Sensitivity analysis error: {e}")
        
        # Peak exposure
        print_section("Peak Exposure Analysis")
        try:
            peak_calc = self.calc_factory.get_calculator("peak_exposure", implementation="python")
            
            peak_data = {
                "current_mtm": 250_000,
                "notional": 10_000_000,
                "remaining_maturity": 5.0,
                "volatility": 0.20,
                "product_type": "irs",
                "num_simulations": 5000,
                "confidence_level": 0.95,
            }
            
            result = peak_calc.calculate(peak_data)
            
            if hasattr(result.value, 'peak_exposure'):
                peak_exp = result.value.peak_exposure
                peak_time = result.value.peak_time
                avg_exp = result.value.average_exposure
            elif isinstance(result.value, dict):
                peak_exp = result.value.get("peak_exposure", 0)
                peak_time = result.value.get("peak_time", 0)
                avg_exp = result.value.get("average_exposure", 0)
            else:
                peak_exp = result.value
                peak_time = 0
                avg_exp = 0
            
            print(f"  Peak Exposure (95%): {format_currency(peak_exp)}")
            print(f"  Peak Time: {peak_time:.2f} years")
            print(f"  Average Exposure: {format_currency(avg_exp)}")
        except Exception as e:
            print(f"  Peak exposure error: {e}")


def run_quick_demo() -> None:
    """Run a quick demonstration."""
    print_header("QLRisk - Quick Demo")
    
    demo = QLRiskDemo()
    
    print_section("System Components")
    print("  ✓ Core Module: PropertiesConfigurator, Logger, Timer, ThreadPool")
    print("  ✓ Calculator Module: 11 calculators (Python + QuantLib implementations)")
    print("  ✓ Models Module: Trade, Curve, MarketData, Products")
    print("  ✓ Math Module: Path generators (GBM, OU, CIR, Heston, etc.)")
    print("  ✓ Engine Module: Multi-threaded CCR calculation engine")
    print("  ✓ Data Module: Test data generator")
    
    print_section("Calculator Factory")
    factory = CalculatorFactory()
    available = factory.get_available_calculators()
    print(f"  Registered calculators: {len(available)}")
    
    # Group by type
    python_count = sum(1 for c in available if c.get('implementation') == ImplementationType.PYTHON.value)
    ql_count = sum(1 for c in available if c.get('implementation') == ImplementationType.QUANTLIB.value)
    print(f"    Python implementations: {python_count}")
    print(f"    QuantLib implementations: {ql_count}")
    
    print_section("Data Generator")
    data_gen = DataGenerator()
    
    # Generate sample counterparty
    cp = data_gen.generate_counterparty()
    print(f"  Sample Counterparty:")
    print(f"    ID: {cp.counterparty_id}")
    print(f"    Name: {cp.name}")
    print(f"    Rating: {cp.rating.name}")
    print(f"    PD: {format_percentage(cp.pd)}")
    print(f"    LGD: {format_percentage(cp.lgd)}")
    
    # Generate sample trade
    trade = data_gen.generate_trade(cp.counterparty_id, ProductType.IRS)
    print(f"\n  Sample Trade:")
    print(f"    ID: {trade.trade_id}")
    print(f"    Product: {trade.product_type.value}")
    print(f"    Notional: {format_currency(trade.notional)}")
    print(f"    MTM: {format_currency(trade.mtm)}")
    
    # Generate market data
    market = data_gen.generate_market_data()
    print(f"\n  Sample Market Data:")
    print(f"    Valuation Date: {market.valuation_date}")
    print(f"    Discount Rate: {format_percentage(market.discount_rate)}")
    print(f"    FX Rates: {len(market.fx_rates)} currencies")
    
    print_section("Path Generator")
    from qlrisk.mathlib import PathGenerationParams, ImplementationType as MathImplementationType
    
    path_gen = demo.math_factory.create_path_generator(implementation=MathImplementationType.PYTHON)
    params = PathGenerationParams(
        initial_value=100.0,
        drift=0.05,
        volatility=0.20,
        maturity=1.0,
        num_steps=252,
        num_paths=1000,
    )
    
    with Timer("Path Generation") as timer:
        result = path_gen.generate_paths(params)
    
    final_values = result.paths[:, -1]
    print(f"  GBM Simulation (1000 paths, 252 steps):")
    print(f"    Initial: 100.00")
    print(f"    Final Mean: {final_values.mean():.2f}")
    print(f"    Final Std: {final_values.std():.2f}")
    print(f"    Time: {timer.elapsed*1000:.2f}ms")
    
    print_section("CCR Engine")
    with CCREngine() as engine:
        print(f"  Status: {engine.status.value}")
        print(f"  Max Workers: {engine._max_workers}")
        print(f"  Implementation: {engine._default_implementation}")
        stats = engine.statistics if hasattr(engine, "statistics") else {}
        print(f"  Total Calculations: {stats.get('total_calculations', 0)}")
    
    print("\n  ✓ Quick demo complete!")


def run_benchmark_only() -> None:
    """Run benchmarks only."""
    demo = QLRiskDemo()
    demo.demo_benchmarks()


def run_stress_only() -> None:
    """Run stress testing only."""
    demo = QLRiskDemo()
    demo.demo_stress_testing()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="QLRisk - Demonstration and Benchmarking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    Run full demonstration
  python main.py --benchmark        Run performance benchmarks only
  python main.py --stress           Run stress testing only
  python main.py --quick            Quick demonstration

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
        """
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmarks only"
    )
    parser.add_argument(
        "--stress",
        action="store_true",
        help="Run stress testing only"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick demonstration"
    )
    parser.add_argument(
        "--market-risk",
        action="store_true",
        help="Run the market risk demo (VaR, ES, SVaR, stress, backtest, limits)"
    )
    parser.add_argument(
        "--frtb",
        action="store_true",
        help="Run the FRTB standardised approach demo"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         QLRisk v2.0.1                          ║
║                                                                               ║
║  Copyright © 2025-2030, All Rights Reserved                                  ║
║  Ashutosh Sinha | Email: ajsinha@gmail.com                                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        if args.quick:
            run_quick_demo()
        elif args.benchmark:
            run_benchmark_only()
        elif args.stress:
            run_stress_only()
        elif args.market_risk:
            from qlrisk.demos import run_market_risk_demo
            run_market_risk_demo()
        elif args.frtb:
            from qlrisk.demos import run_frtb_demo
            run_frtb_demo()
        else:
            demo = QLRiskDemo(config_path=args.config)
            demo.run_full_demo()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\nError: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
