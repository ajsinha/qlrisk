"""
QLRisk - Math Module Base
========================================

Base classes and protocols for mathematical utilities.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np


class ProcessType(Enum):
    """Stochastic process types."""
    GBM = "gbm"  # Geometric Brownian Motion
    OU = "ou"  # Ornstein-Uhlenbeck
    CIR = "cir"  # Cox-Ingersoll-Ross
    HESTON = "heston"  # Heston stochastic volatility
    VASICEK = "vasicek"  # Vasicek interest rate model
    HULL_WHITE = "hull_white"  # Hull-White model
    BLACK_KARASINSKI = "black_karasinski"  # Black-Karasinski model
    MERTON_JUMP = "merton_jump"  # Merton jump diffusion


class ImplementationType(Enum):
    """Implementation type."""
    PYTHON = "python"
    QUANTLIB = "quantlib"


@dataclass
class PathGenerationParams:
    """Parameters for path generation."""
    initial_value: float
    drift: float = 0.0
    volatility: float = 0.2
    maturity: float = 1.0
    num_steps: int = 252
    num_paths: int = 10000
    
    # Mean reversion parameters (for OU, CIR, Vasicek)
    mean_reversion_speed: float = 0.1
    long_term_mean: float = 0.0
    
    # Heston parameters
    vol_of_vol: float = 0.1
    correlation: float = -0.7
    initial_variance: float = 0.04
    
    # Jump parameters (Merton)
    jump_intensity: float = 0.0
    jump_mean: float = 0.0
    jump_std: float = 0.0
    
    # Random seed
    seed: Optional[int] = None


@dataclass
class PathResult:
    """Result of path generation."""
    paths: np.ndarray  # Shape: (num_paths, num_steps + 1)
    time_grid: np.ndarray  # Shape: (num_steps + 1,)
    dt: float
    process_type: ProcessType
    metadata: Dict[str, Any]


class PathGeneratorLike(Protocol):
    """Protocol for path generators."""
    
    def generate_paths(
        self,
        params: PathGenerationParams,
        process_type: ProcessType = ProcessType.GBM
    ) -> PathResult:
        """Generate sample paths."""
        ...
    
    def generate_correlated_paths(
        self,
        params_list: List[PathGenerationParams],
        correlation_matrix: np.ndarray,
        process_type: ProcessType = ProcessType.GBM
    ) -> List[PathResult]:
        """Generate correlated paths for multiple assets."""
        ...


class BasePathGenerator(ABC):
    """Abstract base class for path generators."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize path generator.
        
        Args:
            name: Generator name
            config: Configuration dictionary
        """
        self._name = name
        self._config = config
        self._implementation_type: ImplementationType = ImplementationType.PYTHON
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def implementation_type(self) -> ImplementationType:
        return self._implementation_type
    
    @abstractmethod
    def generate_paths(
        self,
        params: PathGenerationParams,
        process_type: ProcessType = ProcessType.GBM
    ) -> PathResult:
        """Generate sample paths."""
        pass
    
    @abstractmethod
    def generate_correlated_paths(
        self,
        params_list: List[PathGenerationParams],
        correlation_matrix: np.ndarray,
        process_type: ProcessType = ProcessType.GBM
    ) -> List[PathResult]:
        """Generate correlated paths for multiple assets."""
        pass
    
    def _validate_correlation_matrix(
        self,
        correlation_matrix: np.ndarray,
        n_assets: int
    ) -> None:
        """Validate correlation matrix."""
        if correlation_matrix.shape != (n_assets, n_assets):
            raise ValueError(
                f"Correlation matrix must be {n_assets}x{n_assets}, "
                f"got {correlation_matrix.shape}"
            )
        
        # Check symmetry
        if not np.allclose(correlation_matrix, correlation_matrix.T):
            raise ValueError("Correlation matrix must be symmetric")
        
        # Check diagonal is 1
        if not np.allclose(np.diag(correlation_matrix), 1.0):
            raise ValueError("Diagonal elements must be 1")
        
        # Check positive semi-definite
        eigenvalues = np.linalg.eigvalsh(correlation_matrix)
        if np.any(eigenvalues < -1e-10):
            raise ValueError("Correlation matrix must be positive semi-definite")
    
    def _cholesky_decomposition(
        self,
        correlation_matrix: np.ndarray
    ) -> np.ndarray:
        """Perform Cholesky decomposition for correlation."""
        try:
            return np.linalg.cholesky(correlation_matrix)
        except np.linalg.LinAlgError:
            # Fall back to eigenvalue decomposition for near-PSD matrices
            eigenvalues, eigenvectors = np.linalg.eigh(correlation_matrix)
            eigenvalues = np.maximum(eigenvalues, 0)
            return eigenvectors @ np.diag(np.sqrt(eigenvalues))
    
    def details(self) -> Dict[str, Any]:
        """Get generator details."""
        return {
            "name": self._name,
            "implementation": self._implementation_type.value,
            "supported_processes": [p.value for p in ProcessType]
        }


@dataclass
class MonteCarloConfig:
    """Configuration for Monte Carlo simulation."""
    num_simulations: int = 10000
    num_time_steps: int = 252
    antithetic: bool = True
    moment_matching: bool = False
    quasi_random: bool = False
    seed: Optional[int] = None


class MonteCarloEngineLike(Protocol):
    """Protocol for Monte Carlo engines."""
    
    def simulate(
        self,
        params: PathGenerationParams,
        config: MonteCarloConfig
    ) -> PathResult:
        """Run Monte Carlo simulation."""
        ...
    
    def price_option(
        self,
        params: PathGenerationParams,
        payoff_func: callable,
        config: MonteCarloConfig
    ) -> Tuple[float, float]:
        """Price option using Monte Carlo (returns price and std error)."""
        ...


class BaseMonteCarloEngine(ABC):
    """Abstract base class for Monte Carlo engines."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Monte Carlo engine.
        
        Args:
            name: Engine name
            config: Configuration dictionary
        """
        self._name = name
        self._config = config
        self._path_generator: Optional[BasePathGenerator] = None
        self._implementation_type: ImplementationType = ImplementationType.PYTHON
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def implementation_type(self) -> ImplementationType:
        return self._implementation_type
    
    def set_path_generator(self, generator: BasePathGenerator) -> None:
        """Set the path generator to use."""
        self._path_generator = generator
    
    @abstractmethod
    def simulate(
        self,
        params: PathGenerationParams,
        config: MonteCarloConfig
    ) -> PathResult:
        """Run Monte Carlo simulation."""
        pass
    
    @abstractmethod
    def price_option(
        self,
        params: PathGenerationParams,
        payoff_func: callable,
        config: MonteCarloConfig
    ) -> Tuple[float, float]:
        """Price option using Monte Carlo."""
        pass
    
    def _apply_antithetic(
        self,
        random_numbers: np.ndarray
    ) -> np.ndarray:
        """Apply antithetic variates for variance reduction."""
        n_paths = random_numbers.shape[0]
        half = n_paths // 2
        random_numbers[half:] = -random_numbers[:half]
        return random_numbers
    
    def _apply_moment_matching(
        self,
        random_numbers: np.ndarray
    ) -> np.ndarray:
        """Apply moment matching for variance reduction."""
        # Standardize to mean 0, variance 1
        mean = np.mean(random_numbers, axis=0)
        std = np.std(random_numbers, axis=0)
        return (random_numbers - mean) / np.where(std > 0, std, 1.0)
    
    def details(self) -> Dict[str, Any]:
        """Get engine details."""
        return {
            "name": self._name,
            "implementation": self._implementation_type.value,
            "path_generator": self._path_generator.name if self._path_generator else None
        }


# Statistical utilities protocol
class StatisticalUtilsLike(Protocol):
    """Protocol for statistical utilities."""
    
    def normal_cdf(self, x: float) -> float:
        """Cumulative distribution function of standard normal."""
        ...
    
    def normal_pdf(self, x: float) -> float:
        """Probability density function of standard normal."""
        ...
    
    def inverse_normal_cdf(self, p: float) -> float:
        """Inverse CDF (quantile function) of standard normal."""
        ...
    
    def black_scholes_call(
        self,
        S: float,
        K: float,
        r: float,
        sigma: float,
        T: float
    ) -> float:
        """Black-Scholes call option price."""
        ...
    
    def black_scholes_put(
        self,
        S: float,
        K: float,
        r: float,
        sigma: float,
        T: float
    ) -> float:
        """Black-Scholes put option price."""
        ...
