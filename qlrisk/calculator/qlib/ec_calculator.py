# Copyright © 2025-2030, All Rights Reserved
# Ashutosh Sinha | Email: ajsinha@gmail.com
#
# Legal Notice: This module and the associated software architecture are proprietary
# and confidential. Unauthorized copying, distribution, modification, or use is
# strictly prohibited without explicit written permission from the copyright holder.

"""
QuantLib-based Economic Capital (EC) Calculator.

Calculates Economic Capital using various methodologies including
Vasicek single-factor model, Monte Carlo simulation with Gaussian copula,
and Gordy's asymptotic approximation.

EC = UL = VaR(α) - EL
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import math

try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

from ..base import BaseCalculator, CalculationResult, CalculatorType


class ECMethod(Enum):
    """Economic Capital calculation methodology."""
    VASICEK = "vasicek"
    MONTE_CARLO = "monte_carlo"
    GORDY = "gordy_asymptotic"


@dataclass
class QLECInput:
    """Input parameters for QuantLib Economic Capital calculation."""
    exposures: List[float]  # EAD for each exposure
    pds: List[float]  # PD for each exposure
    lgds: List[float]  # LGD for each exposure
    asset_correlation: float = 0.15  # Single factor correlation
    confidence_level: float = 0.999  # VaR confidence (99.9%)
    time_horizon: float = 1.0  # Years
    correlation_matrix: Optional[List[List[float]]] = None
    num_simulations: int = 100000
    method: ECMethod = ECMethod.VASICEK


@dataclass
class QLECResult:
    """Result of QuantLib Economic Capital calculation."""
    economic_capital: float
    expected_loss: float
    unexpected_loss: float
    var: float  # Value at Risk
    es: float  # Expected Shortfall
    capital_ratio: float  # EC / Total Exposure
    method: str = ""
    granularity_adjustment: float = 0.0
    concentration_risk: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)


class QuantLibECCalculator(BaseCalculator):
    """
    QuantLib-based Economic Capital Calculator.
    
    Uses QuantLib for:
    - Random number generation (Mersenne Twister, Sobol)
    - Statistical functions
    - Copula simulations
    """
    
    def __init__(self, name: str = "QuantLibECCalculator",
                 config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config or {})
        self._calculator_type = CalculatorType.ECONOMIC_CAPITAL
        self._validate_quantlib()
    
    def _validate_quantlib(self) -> None:
        """Verify QuantLib is available."""
        if not QUANTLIB_AVAILABLE:
            raise ImportError(
                "QuantLib is required for QuantLibECCalculator. "
                "Install with: pip install QuantLib"
            )
    
    def calculate(self, data: QLECInput) -> CalculationResult:
        """
        Calculate Economic Capital using QuantLib.
        
        Args:
            data: QLECInput containing portfolio parameters
            
        Returns:
            CalculationResult containing QLECResult
        """
        self._validate_input(data)
        
        if data.method == ECMethod.VASICEK:
            result = self._calculate_vasicek(data)
        elif data.method == ECMethod.MONTE_CARLO:
            result = self._calculate_monte_carlo(data)
        elif data.method == ECMethod.GORDY:
            result = self._calculate_gordy(data)
        else:
            raise ValueError(f"Unknown EC method: {data.method}")
        
        return CalculationResult(
            calculator_name=self.name,
            calculator_type=self._calculator_type,
            result=result,
            metadata={
                "method": data.method.value,
                "confidence_level": data.confidence_level,
                "quantlib_version": ql.QuantLib.version() if QUANTLIB_AVAILABLE else "N/A",
            }
        )
    
    def _validate_input(self, data: QLECInput) -> None:
        """Validate input parameters."""
        n = len(data.exposures)
        if n == 0:
            raise ValueError("Portfolio cannot be empty")
        if len(data.pds) != n or len(data.lgds) != n:
            raise ValueError("Exposures, PDs, and LGDs must have same length")
        if not all(0 <= pd <= 1 for pd in data.pds):
            raise ValueError("All PDs must be between 0 and 1")
        if not all(0 <= lgd <= 1 for lgd in data.lgds):
            raise ValueError("All LGDs must be between 0 and 1")
        if not 0 < data.confidence_level < 1:
            raise ValueError("Confidence level must be between 0 and 1")
    
    def _calculate_vasicek(self, data: QLECInput) -> QLECResult:
        """
        Calculate EC using Vasicek single-factor model (Basel II IRB).
        
        K = LGD × N[(N⁻¹(PD) + √ρ × N⁻¹(α)) / √(1-ρ)] - PD × LGD
        
        where ρ is asset correlation and α is confidence level.
        """
        # QuantLib normal distribution functions
        norm = ql.CumulativeNormalDistribution()
        inv_norm = ql.InverseCumulativeNormal()
        
        total_ead = sum(data.exposures)
        expected_loss = 0.0
        capital_requirement = 0.0
        
        # Confidence level quantile
        alpha = data.confidence_level
        z_alpha = inv_norm(alpha)
        
        rho = data.asset_correlation
        sqrt_rho = math.sqrt(rho)
        sqrt_1_minus_rho = math.sqrt(1 - rho)
        
        for i, (ead, pd, lgd) in enumerate(zip(data.exposures, data.pds, data.lgds)):
            # Expected Loss for this exposure
            el_i = pd * lgd * ead
            expected_loss += el_i
            
            # Vasicek formula for capital requirement
            if pd > 0 and pd < 1:
                z_pd = inv_norm(pd)
                
                # Conditional PD at stress
                conditional_pd = norm((z_pd + sqrt_rho * z_alpha) / sqrt_1_minus_rho)
                
                # Capital requirement
                k_i = lgd * (conditional_pd - pd) * ead
            else:
                k_i = 0.0
            
            capital_requirement += k_i
        
        # VaR
        var = expected_loss + capital_requirement
        
        # Expected Shortfall (approximate)
        es = var * 1.1  # Simple approximation
        
        # Capital ratio
        capital_ratio = capital_requirement / total_ead if total_ead > 0 else 0
        
        return QLECResult(
            economic_capital=capital_requirement,
            expected_loss=expected_loss,
            unexpected_loss=capital_requirement,
            var=var,
            es=es,
            capital_ratio=capital_ratio,
            method=ECMethod.VASICEK.value,
            components={
                "asset_correlation": rho,
                "z_alpha": z_alpha,
                "total_ead": total_ead,
            }
        )
    
    def _calculate_monte_carlo(self, data: QLECInput) -> QLECResult:
        """
        Calculate EC using Monte Carlo with Gaussian copula.
        """
        n_exposures = len(data.exposures)
        n_sims = data.num_simulations
        
        # Set up QuantLib RNG
        rng = ql.MersenneTwisterUniformRng(42)
        gaussian_rng = ql.MersenneTwisterGaussianRng(rng)
        inv_norm = ql.InverseCumulativeNormal()
        norm = ql.CumulativeNormalDistribution()
        
        # Default thresholds
        thresholds = [inv_norm(pd) if 0 < pd < 1 else (-10 if pd <= 0 else 10) 
                     for pd in data.pds]
        
        rho = data.asset_correlation
        sqrt_rho = math.sqrt(rho)
        sqrt_1_minus_rho = math.sqrt(1 - rho)
        
        losses = []
        
        for _ in range(n_sims):
            # Systematic factor
            z_sys = gaussian_rng.next().value()
            
            # Portfolio loss for this scenario
            portfolio_loss = 0.0
            
            for i in range(n_exposures):
                # Idiosyncratic factor
                z_idio = gaussian_rng.next().value()
                
                # Latent variable (single-factor model)
                latent = sqrt_rho * z_sys + sqrt_1_minus_rho * z_idio
                
                # Default occurs if latent < threshold
                if latent < thresholds[i]:
                    loss = data.lgds[i] * data.exposures[i]
                    portfolio_loss += loss
            
            losses.append(portfolio_loss)
        
        # Sort losses for percentile calculation
        losses.sort()
        
        # Expected Loss
        expected_loss = sum(losses) / n_sims
        
        # VaR at confidence level
        var_idx = int(data.confidence_level * n_sims)
        var_idx = min(var_idx, n_sims - 1)
        var = losses[var_idx]
        
        # Expected Shortfall (tail average)
        es_losses = losses[var_idx:]
        es = sum(es_losses) / len(es_losses) if es_losses else var
        
        # Economic Capital = UL = VaR - EL
        economic_capital = max(0, var - expected_loss)
        
        # Capital ratio
        total_ead = sum(data.exposures)
        capital_ratio = economic_capital / total_ead if total_ead > 0 else 0
        
        return QLECResult(
            economic_capital=economic_capital,
            expected_loss=expected_loss,
            unexpected_loss=economic_capital,
            var=var,
            es=es,
            capital_ratio=capital_ratio,
            method=ECMethod.MONTE_CARLO.value,
            components={
                "num_simulations": n_sims,
                "asset_correlation": rho,
                "total_ead": total_ead,
            }
        )
    
    def _calculate_gordy(self, data: QLECInput) -> QLECResult:
        """
        Calculate EC using Gordy's asymptotic approximation.
        
        Includes granularity adjustment for concentration risk.
        """
        # First calculate Vasicek base
        vasicek_result = self._calculate_vasicek(data)
        
        # Granularity adjustment
        granularity_adj = self._calculate_granularity_adjustment(data)
        
        # Adjusted EC
        ec_adjusted = vasicek_result.economic_capital + granularity_adj
        
        # Concentration risk (Herfindahl index)
        total_ead = sum(data.exposures)
        hhi = sum((e / total_ead) ** 2 for e in data.exposures) if total_ead > 0 else 0
        effective_n = 1 / hhi if hhi > 0 else len(data.exposures)
        
        concentration_risk = (len(data.exposures) - effective_n) / len(data.exposures) if len(data.exposures) > 0 else 0
        
        return QLECResult(
            economic_capital=ec_adjusted,
            expected_loss=vasicek_result.expected_loss,
            unexpected_loss=ec_adjusted,
            var=vasicek_result.var + granularity_adj,
            es=vasicek_result.es + granularity_adj,
            capital_ratio=ec_adjusted / total_ead if total_ead > 0 else 0,
            method=ECMethod.GORDY.value,
            granularity_adjustment=granularity_adj,
            concentration_risk=concentration_risk,
            components={
                "vasicek_ec": vasicek_result.economic_capital,
                "hhi": hhi,
                "effective_n": effective_n,
            }
        )
    
    def _calculate_granularity_adjustment(self, data: QLECInput) -> float:
        """
        Calculate granularity adjustment for portfolio concentration.
        
        GA = (1/2) × Σ wᵢ² × LGDᵢ² × (1 - ρ) × σᵢ²
        
        where wᵢ is exposure weight and σᵢ² is variance contribution.
        """
        total_ead = sum(data.exposures)
        if total_ead == 0:
            return 0.0
        
        rho = data.asset_correlation
        
        ga = 0.0
        for ead, pd, lgd in zip(data.exposures, data.pds, data.lgds):
            w = ead / total_ead
            
            # Variance contribution
            var_i = pd * (1 - pd)
            
            ga += 0.5 * (w ** 2) * (lgd ** 2) * (1 - rho) * var_i * total_ead
        
        return ga
    
    def calculate_marginal_ec(self, 
                               portfolio: QLECInput,
                               new_exposure: Tuple[float, float, float]) -> Dict[str, Any]:
        """
        Calculate marginal EC contribution of a new exposure.
        
        Args:
            portfolio: Existing portfolio
            new_exposure: (EAD, PD, LGD) for new exposure
            
        Returns:
            Marginal EC analysis
        """
        # Calculate existing EC
        existing_result = self.calculate(portfolio)
        existing_ec = existing_result.result.economic_capital
        
        # Create new portfolio
        new_ead, new_pd, new_lgd = new_exposure
        
        new_portfolio = QLECInput(
            exposures=portfolio.exposures + [new_ead],
            pds=portfolio.pds + [new_pd],
            lgds=portfolio.lgds + [new_lgd],
            asset_correlation=portfolio.asset_correlation,
            confidence_level=portfolio.confidence_level,
            method=portfolio.method,
        )
        
        # Calculate new EC
        new_result = self.calculate(new_portfolio)
        new_ec = new_result.result.economic_capital
        
        # Marginal EC
        marginal_ec = new_ec - existing_ec
        
        # Standalone EC
        standalone_portfolio = QLECInput(
            exposures=[new_ead],
            pds=[new_pd],
            lgds=[new_lgd],
            asset_correlation=portfolio.asset_correlation,
            confidence_level=portfolio.confidence_level,
            method=portfolio.method,
        )
        standalone_result = self.calculate(standalone_portfolio)
        standalone_ec = standalone_result.result.economic_capital
        
        return {
            "marginal_ec": marginal_ec,
            "standalone_ec": standalone_ec,
            "diversification_benefit": standalone_ec - marginal_ec,
            "existing_ec": existing_ec,
            "new_portfolio_ec": new_ec,
            "marginal_raroc": 0.0,  # Would need revenue info
        }
    
    def calculate_stress_ec(self, 
                            portfolio: QLECInput,
                            pd_stress_factor: float = 2.0,
                            correlation_stress: float = 0.0) -> Dict[str, Any]:
        """
        Calculate Economic Capital under stress scenarios.
        
        Args:
            portfolio: Portfolio to stress
            pd_stress_factor: Multiplier for PDs
            correlation_stress: Additive stress to correlation
            
        Returns:
            Stressed EC results
        """
        # Base case
        base_result = self.calculate(portfolio)
        
        # Stressed PDs
        stressed_pds = [min(1.0, pd * pd_stress_factor) for pd in portfolio.pds]
        
        # Stressed correlation
        stressed_corr = min(0.99, portfolio.asset_correlation + correlation_stress)
        
        stressed_portfolio = QLECInput(
            exposures=portfolio.exposures,
            pds=stressed_pds,
            lgds=portfolio.lgds,
            asset_correlation=stressed_corr,
            confidence_level=portfolio.confidence_level,
            method=portfolio.method,
        )
        
        stressed_result = self.calculate(stressed_portfolio)
        
        return {
            "base_ec": base_result.result.economic_capital,
            "stressed_ec": stressed_result.result.economic_capital,
            "ec_increase": stressed_result.result.economic_capital - base_result.result.economic_capital,
            "ec_increase_pct": (stressed_result.result.economic_capital / base_result.result.economic_capital - 1) * 100 if base_result.result.economic_capital > 0 else 0,
            "stressed_el": stressed_result.result.expected_loss,
            "pd_stress_factor": pd_stress_factor,
            "correlation_stress": correlation_stress,
        }
    
    def details(self) -> Dict[str, Any]:
        """Return calculator details."""
        return {
            "name": self.name,
            "type": self._calculator_type.value,
            "implementation": "quantlib",
            "version": "1.0.0",
            "methods": [m.value for m in ECMethod],
            "default_confidence": 0.999,
            "supports_stress_testing": True,
            "quantlib_available": QUANTLIB_AVAILABLE,
        }
