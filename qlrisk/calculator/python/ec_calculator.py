"""
QLRisk - Economic Capital (EC) Calculator
========================================================

Python implementation of Economic Capital calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import math
import random

from ..base import (
    filter_dict_for_dataclass,
    BaseCalculator, CalculatorType, ImplementationType
)


@dataclass
class ECInput:
    """Input data for Economic Capital calculation."""
    # Portfolio exposures
    exposures: List[float]  # EAD for each counterparty
    pds: List[float]  # Probability of default for each
    lgds: List[float]  # LGD for each
    
    # Correlation parameters
    asset_correlation: float = 0.20  # Average asset correlation
    correlation_matrix: Optional[List[List[float]]] = None  # Full correlation matrix
    
    # For single obligor
    ead: Optional[float] = None
    pd: Optional[float] = None
    lgd: Optional[float] = None
    
    # Confidence level
    confidence_level: float = 0.999  # 99.9% for Basel
    
    # Time horizon
    time_horizon: float = 1.0  # years


@dataclass
class ECResult:
    """Result of Economic Capital calculation."""
    economic_capital: float
    expected_loss: float
    unexpected_loss: float
    var: float  # Value at Risk
    es: float  # Expected Shortfall
    capital_ratio: float  # EC / Total EAD
    components: Dict[str, Any]


class EconomicCapitalCalculator(BaseCalculator[ECResult]):
    """
    Economic Capital (EC) Calculator.
    
    Economic Capital is the amount of capital needed to cover
    unexpected losses at a specified confidence level.
    
    EC = UL = VaR(α) - EL
    
    Methods supported:
    - Vasicek (single factor model)
    - Monte Carlo simulation
    - Gordy asymptotic formula
    
    The Vasicek formula (Basel II IRB):
    EC = LGD × N[(1/√(1-ρ)) × N^(-1)(PD) + √(ρ/(1-ρ)) × N^(-1)(α)] - EL
    """
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        """
        Initialize Economic Capital calculator.
        
        Args:
            name: Calculator name
            config: Configuration including:
                - method: 'vasicek', 'monte_carlo', or 'gordy'
                - confidence_level: VaR confidence level (default 0.999)
                - num_simulations: For MC method
        """
        config = config or {}
        name = name or self.__class__.__name__
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._method = config.get("method", "vasicek")
        self._confidence_level = config.get("confidence_level", 0.999)
        self._num_simulations = config.get("num_simulations", 100000)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.EC
    
    def _calculate_impl(self, data: Any) -> ECResult:
        """
        Calculate Economic Capital.
        
        Args:
            data: ECInput or dictionary
            
        Returns:
            ECResult with EC and components
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, ECInput)
            data = ECInput(**filtered_data)
        
        if self._method == "vasicek":
            return self._calculate_vasicek(data)
        elif self._method == "monte_carlo":
            return self._calculate_monte_carlo(data)
        elif self._method == "gordy":
            return self._calculate_gordy(data)
        else:
            raise ValueError(f"Unknown EC method: {self._method}")
    
    def _calculate_vasicek(self, data: ECInput) -> ECResult:
        """
        Vasicek single-factor model (Basel II IRB formula).
        
        Capital = K × EAD
        K = LGD × N[(1/√(1-ρ))×N^(-1)(PD) + √(ρ/(1-ρ))×N^(-1)(α)] - PD×LGD
        """
        # Handle single obligor or portfolio
        if data.ead is not None:
            # Single obligor
            exposures = [data.ead]
            pds = [data.pd]
            lgds = [data.lgd]
        else:
            exposures = data.exposures
            pds = data.pds
            lgds = data.lgds
        
        total_ead = sum(exposures)
        total_el = 0.0
        total_ec = 0.0
        
        rho = data.asset_correlation
        alpha = data.confidence_level
        
        for ead, pd, lgd in zip(exposures, pds, lgds):
            # Expected Loss
            el = pd * lgd * ead
            total_el += el
            
            # Vasicek conditional default probability
            # N[(N^(-1)(PD) + √ρ × N^(-1)(α)) / √(1-ρ)]
            norm_inv_pd = self._norm_inv(pd)
            norm_inv_alpha = self._norm_inv(alpha)
            
            conditional_pd = self._norm_cdf(
                (norm_inv_pd + math.sqrt(rho) * norm_inv_alpha) / math.sqrt(1 - rho)
            )
            
            # Unexpected Loss = Conditional Loss - Expected Loss
            conditional_loss = lgd * conditional_pd * ead
            ec = conditional_loss - el
            total_ec += ec
        
        # VaR is total loss at confidence level
        var = total_el + total_ec
        
        # Expected Shortfall (approximation)
        es = self._calculate_expected_shortfall_vasicek(
            pds, lgds, exposures, rho, alpha
        )
        
        capital_ratio = total_ec / total_ead if total_ead > 0 else 0
        
        return ECResult(
            economic_capital=total_ec,
            expected_loss=total_el,
            unexpected_loss=total_ec,
            var=var,
            es=es,
            capital_ratio=capital_ratio,
            components={
                "method": "vasicek",
                "asset_correlation": rho,
                "confidence_level": alpha,
                "total_ead": total_ead,
                "num_obligors": len(exposures)
            }
        )
    
    def _calculate_monte_carlo(self, data: ECInput) -> ECResult:
        """
        Monte Carlo simulation for EC.
        
        Simulates correlated defaults using Gaussian copula.
        """
        if data.ead is not None:
            exposures = [data.ead]
            pds = [data.pd]
            lgds = [data.lgd]
        else:
            exposures = data.exposures
            pds = data.pds
            lgds = data.lgds
        
        n_obligors = len(exposures)
        n_sims = self._num_simulations
        rho = data.asset_correlation
        
        total_ead = sum(exposures)
        
        # Precompute default thresholds
        thresholds = [self._norm_inv(pd) for pd in pds]
        
        # Simulate losses
        losses = []
        
        for _ in range(n_sims):
            # Systematic factor
            z = random.gauss(0, 1)
            
            portfolio_loss = 0.0
            for i in range(n_obligors):
                # Idiosyncratic factor
                epsilon = random.gauss(0, 1)
                
                # Asset return (single factor model)
                asset_return = math.sqrt(rho) * z + math.sqrt(1 - rho) * epsilon
                
                # Default if asset return below threshold
                if asset_return < thresholds[i]:
                    portfolio_loss += lgds[i] * exposures[i]
            
            losses.append(portfolio_loss)
        
        # Sort losses
        losses.sort()
        
        # Expected Loss
        expected_loss = sum(losses) / n_sims
        
        # VaR at confidence level
        var_idx = int(self._confidence_level * n_sims)
        var = losses[min(var_idx, n_sims - 1)]
        
        # Expected Shortfall
        tail_losses = losses[var_idx:]
        es = sum(tail_losses) / len(tail_losses) if tail_losses else var
        
        # Economic Capital
        ec = var - expected_loss
        
        capital_ratio = ec / total_ead if total_ead > 0 else 0
        
        return ECResult(
            economic_capital=ec,
            expected_loss=expected_loss,
            unexpected_loss=ec,
            var=var,
            es=es,
            capital_ratio=capital_ratio,
            components={
                "method": "monte_carlo",
                "num_simulations": n_sims,
                "asset_correlation": rho,
                "confidence_level": self._confidence_level
            }
        )
    
    def _calculate_gordy(self, data: ECInput) -> ECResult:
        """
        Gordy asymptotic formula for granular portfolios.
        
        For infinitely granular portfolios:
        EC = E[L|Z=z_α] - EL
        
        Where z_α = N^(-1)(α)
        """
        if data.ead is not None:
            exposures = [data.ead]
            pds = [data.pd]
            lgds = [data.lgd]
        else:
            exposures = data.exposures
            pds = data.pds
            lgds = data.lgds
        
        total_ead = sum(exposures)
        rho = data.asset_correlation
        alpha = data.confidence_level
        z_alpha = self._norm_inv(alpha)
        
        total_el = 0.0
        conditional_loss = 0.0
        
        for ead, pd, lgd in zip(exposures, pds, lgds):
            el = pd * lgd * ead
            total_el += el
            
            # Conditional default probability given systematic factor
            norm_inv_pd = self._norm_inv(pd)
            cond_pd = self._norm_cdf(
                (norm_inv_pd + math.sqrt(rho) * z_alpha) / math.sqrt(1 - rho)
            )
            
            conditional_loss += lgd * cond_pd * ead
        
        ec = conditional_loss - total_el
        var = conditional_loss
        
        # Granularity adjustment (simplified)
        hhi = sum((e / total_ead) ** 2 for e in exposures)
        granularity_adj = hhi * ec * 0.5  # Simplified adjustment
        ec_adjusted = ec + granularity_adj
        
        capital_ratio = ec_adjusted / total_ead if total_ead > 0 else 0
        
        return ECResult(
            economic_capital=ec_adjusted,
            expected_loss=total_el,
            unexpected_loss=ec_adjusted,
            var=var + granularity_adj,
            es=var * 1.1,  # Approximation
            capital_ratio=capital_ratio,
            components={
                "method": "gordy",
                "unadjusted_ec": ec,
                "granularity_adjustment": granularity_adj,
                "hhi": hhi,
                "asset_correlation": rho
            }
        )
    
    def _calculate_expected_shortfall_vasicek(self, pds: List[float],
                                               lgds: List[float],
                                               exposures: List[float],
                                               rho: float, alpha: float) -> float:
        """Calculate Expected Shortfall using Vasicek model."""
        # Numerical integration for ES
        n_points = 100
        total_es = 0.0
        
        z_alpha = self._norm_inv(alpha)
        
        for i in range(n_points):
            # Points in the tail
            p = alpha + (1 - alpha) * (i + 0.5) / n_points
            z = self._norm_inv(p)
            
            # Conditional loss at this point
            cond_loss = 0.0
            for ead, pd, lgd in zip(exposures, pds, lgds):
                norm_inv_pd = self._norm_inv(pd)
                cond_pd = self._norm_cdf(
                    (norm_inv_pd + math.sqrt(rho) * z) / math.sqrt(1 - rho)
                )
                cond_loss += lgd * cond_pd * ead
            
            total_es += cond_loss
        
        return total_es / n_points
    
    def _norm_cdf(self, x: float) -> float:
        """Standard normal CDF."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def _norm_inv(self, p: float) -> float:
        """Inverse standard normal CDF."""
        if p <= 0:
            return -10.0
        if p >= 1:
            return 10.0
        
        # Rational approximation
        a = [
            -3.969683028665376e+01, 2.209460984245205e+02,
            -2.759285104469687e+02, 1.383577518672690e+02,
            -3.066479806614716e+01, 2.506628277459239e+00
        ]
        b = [
            -5.447609879822406e+01, 1.615858368580409e+02,
            -1.556989798598866e+02, 6.680131188771972e+01,
            -1.328068155288572e+01
        ]
        c = [
            -7.784894002430293e-03, -3.223964580411365e-01,
            -2.400758277161838e+00, -2.549732539343734e+00,
            4.374664141464968e+00, 2.938163982698783e+00
        ]
        d = [
            7.784695709041462e-03, 3.224671290700398e-01,
            2.445134137142996e+00, 3.754408661907416e+00
        ]
        
        p_low = 0.02425
        p_high = 1 - p_low
        
        if p < p_low:
            q = math.sqrt(-2 * math.log(p))
            return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                   ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
        elif p <= p_high:
            q = p - 0.5
            r = q * q
            return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / \
                   (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)
        else:
            q = math.sqrt(-2 * math.log(1 - p))
            return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / \
                    ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "method": self._method,
            "confidence_level": self._confidence_level,
            "num_simulations": self._num_simulations
        })
        return base_details
