"""
QLRisk - Math Module v2.3.0
==========================================

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is 
strictly prohibited without explicit written permission from the copyright holder.

---

Mathematical utilities for market risk and CCR analytics including:
- Stochastic path generation
- Monte Carlo simulation engines
- Statistical utilities
- Numerical methods

Stochastic Processes (8):
- GBM: Geometric Brownian Motion
- OU: Ornstein-Uhlenbeck (mean-reverting)
- CIR: Cox-Ingersoll-Ross (interest rates)
- VASICEK: Vasicek interest rate model
- HULL_WHITE: Hull-White one-factor model
- BLACK_KARASINSKI: Black-Karasinski model
- HESTON: Heston stochastic volatility
- MERTON_JUMP: Merton jump diffusion

Implementations:
- Pure Python: Cross-platform, NumPy-based
- QuantLib: High-performance C++ backend

Usage:
    from qlrisk.mathlib import MathFactory, PathGenerationParams, ProcessType
    
    factory = MathFactory.get_instance()
    generator = factory.create_path_generator(implementation='python')
    
    params = PathGenerationParams(
        initial_value=100.0,
        drift=0.05,
        volatility=0.2,
        maturity=1.0,
        num_paths=10000,
        num_steps=252
    )
    
    result = generator.generate_paths(params, ProcessType.GBM)
"""

__version__ = "2.3.0"

from .base import (
    ProcessType,
    ImplementationType,
    PathGenerationParams,
    PathResult,
    MonteCarloConfig,
    BasePathGenerator,
    BaseMonteCarloEngine,
    PathGeneratorLike,
    MonteCarloEngineLike,
    StatisticalUtilsLike
)

from .factory import MathFactory, get_math_factory

__all__ = [
    "__version__",
    # Enums
    'ProcessType',
    'ImplementationType',
    
    # Data classes
    'PathGenerationParams',
    'PathResult',
    'MonteCarloConfig',
    
    # Base classes
    'BasePathGenerator',
    'BaseMonteCarloEngine',
    
    # Protocols
    'PathGeneratorLike',
    'MonteCarloEngineLike',
    'StatisticalUtilsLike',
    
    # Factory
    'MathFactory',
    'get_math_factory'
]
