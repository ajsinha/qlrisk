"""
QLRisk - Python Path Generator
=============================================

Pure Python implementation of stochastic path generation.

Mathematical Models:
-------------------
GBM: dS = μS dt + σS dW
OU:  dX = θ(μ - X) dt + σ dW
CIR: dX = θ(μ - X) dt + σ√X dW
Vasicek: dr = a(b - r) dt + σ dW

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, List, Optional
import numpy as np

from ..base import (
    BasePathGenerator,
    PathGenerationParams,
    PathResult,
    ProcessType,
    ImplementationType
)


class PythonPathGenerator(BasePathGenerator):
    """
    Pure Python implementation of stochastic path generator.
    
    Supports various stochastic processes using Euler-Maruyama
    and exact discretization schemes.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize Python path generator.
        
        Args:
            name: Generator name
            config: Configuration including:
                - seed: Random seed
                - use_antithetic: Use antithetic variates
                - use_moment_matching: Use moment matching
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._seed = config.get("seed")
        self._use_antithetic = config.get("use_antithetic", True)
        self._use_moment_matching = config.get("use_moment_matching", False)
        
        if self._seed is not None:
            np.random.seed(self._seed)
    
    def generate_paths(
        self,
        params: PathGenerationParams,
        process_type: ProcessType = ProcessType.GBM
    ) -> PathResult:
        """
        Generate sample paths for the specified process.
        
        Args:
            params: Path generation parameters
            process_type: Type of stochastic process
            
        Returns:
            PathResult with generated paths
        """
        if params.seed is not None:
            np.random.seed(params.seed)
        
        dt = params.maturity / params.num_steps
        time_grid = np.linspace(0, params.maturity, params.num_steps + 1)
        
        # Generate random numbers
        num_paths = params.num_paths
        if self._use_antithetic:
            num_paths = (params.num_paths + 1) // 2
        
        random_numbers = np.random.standard_normal((num_paths, params.num_steps))
        
        if self._use_antithetic:
            random_numbers = np.vstack([random_numbers, -random_numbers])
            random_numbers = random_numbers[:params.num_paths]
        
        if self._use_moment_matching:
            random_numbers = self._apply_moment_matching(random_numbers)
        
        # Generate paths based on process type
        if process_type == ProcessType.GBM:
            paths = self._generate_gbm_paths(params, random_numbers, dt)
        elif process_type == ProcessType.OU:
            paths = self._generate_ou_paths(params, random_numbers, dt)
        elif process_type == ProcessType.CIR:
            paths = self._generate_cir_paths(params, random_numbers, dt)
        elif process_type == ProcessType.VASICEK:
            paths = self._generate_vasicek_paths(params, random_numbers, dt)
        elif process_type == ProcessType.HULL_WHITE:
            paths = self._generate_hull_white_paths(params, random_numbers, dt)
        elif process_type == ProcessType.HESTON:
            paths = self._generate_heston_paths(params, dt)
        elif process_type == ProcessType.MERTON_JUMP:
            paths = self._generate_merton_jump_paths(params, random_numbers, dt)
        else:
            raise ValueError(f"Unsupported process type: {process_type}")
        
        return PathResult(
            paths=paths,
            time_grid=time_grid,
            dt=dt,
            process_type=process_type,
            metadata={
                "implementation": "python",
                "num_paths": params.num_paths,
                "num_steps": params.num_steps,
                "antithetic": self._use_antithetic,
                "moment_matching": self._use_moment_matching
            }
        )
    
    def generate_correlated_paths(
        self,
        params_list: List[PathGenerationParams],
        correlation_matrix: np.ndarray,
        process_type: ProcessType = ProcessType.GBM
    ) -> List[PathResult]:
        """
        Generate correlated paths for multiple assets.
        
        Uses Cholesky decomposition to correlate independent
        Brownian motions.
        
        Args:
            params_list: List of parameters for each asset
            correlation_matrix: Correlation matrix between assets
            process_type: Type of stochastic process
            
        Returns:
            List of PathResult, one per asset
        """
        n_assets = len(params_list)
        self._validate_correlation_matrix(correlation_matrix, n_assets)
        
        # Use first asset's parameters for common settings
        base_params = params_list[0]
        num_paths = base_params.num_paths
        num_steps = base_params.num_steps
        dt = base_params.maturity / num_steps
        time_grid = np.linspace(0, base_params.maturity, num_steps + 1)
        
        # Generate independent random numbers
        independent_randoms = np.random.standard_normal(
            (n_assets, num_paths, num_steps)
        )
        
        # Apply Cholesky decomposition to correlate
        cholesky = self._cholesky_decomposition(correlation_matrix)
        
        # Correlate the random numbers
        correlated_randoms = np.zeros_like(independent_randoms)
        for t in range(num_steps):
            for p in range(num_paths):
                correlated_randoms[:, p, t] = cholesky @ independent_randoms[:, p, t]
        
        # Generate paths for each asset
        results = []
        for i, params in enumerate(params_list):
            random_numbers = correlated_randoms[i]
            
            if process_type == ProcessType.GBM:
                paths = self._generate_gbm_paths(params, random_numbers, dt)
            elif process_type == ProcessType.OU:
                paths = self._generate_ou_paths(params, random_numbers, dt)
            else:
                paths = self._generate_gbm_paths(params, random_numbers, dt)
            
            results.append(PathResult(
                paths=paths,
                time_grid=time_grid,
                dt=dt,
                process_type=process_type,
                metadata={
                    "implementation": "python",
                    "asset_index": i,
                    "correlated": True
                }
            ))
        
        return results
    
    def _generate_gbm_paths(
        self,
        params: PathGenerationParams,
        random_numbers: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Generate Geometric Brownian Motion paths.
        
        Exact discretization:
        S(t+dt) = S(t) × exp((μ - σ²/2)dt + σ√dt × Z)
        """
        num_paths, num_steps = random_numbers.shape
        paths = np.zeros((num_paths, num_steps + 1))
        paths[:, 0] = params.initial_value
        
        drift_term = (params.drift - 0.5 * params.volatility ** 2) * dt
        diffusion_term = params.volatility * np.sqrt(dt)
        
        for t in range(num_steps):
            paths[:, t + 1] = paths[:, t] * np.exp(
                drift_term + diffusion_term * random_numbers[:, t]
            )
        
        return paths
    
    def _generate_ou_paths(
        self,
        params: PathGenerationParams,
        random_numbers: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Generate Ornstein-Uhlenbeck process paths.
        
        Exact discretization:
        X(t+dt) = X(t)e^(-θdt) + μ(1 - e^(-θdt)) + σ√((1-e^(-2θdt))/2θ) × Z
        """
        num_paths, num_steps = random_numbers.shape
        paths = np.zeros((num_paths, num_steps + 1))
        paths[:, 0] = params.initial_value
        
        theta = params.mean_reversion_speed
        mu = params.long_term_mean
        sigma = params.volatility
        
        exp_theta = np.exp(-theta * dt)
        mean_coef = mu * (1 - exp_theta)
        
        if theta > 0:
            vol_coef = sigma * np.sqrt((1 - np.exp(-2 * theta * dt)) / (2 * theta))
        else:
            vol_coef = sigma * np.sqrt(dt)
        
        for t in range(num_steps):
            paths[:, t + 1] = (
                paths[:, t] * exp_theta +
                mean_coef +
                vol_coef * random_numbers[:, t]
            )
        
        return paths
    
    def _generate_cir_paths(
        self,
        params: PathGenerationParams,
        random_numbers: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Generate CIR (Cox-Ingersoll-Ross) process paths.
        
        Uses full truncation Euler scheme:
        X(t+dt) = X(t) + θ(μ - X⁺(t))dt + σ√(X⁺(t)dt) × Z
        
        Feller condition: 2θμ ≥ σ² ensures positivity
        """
        num_paths, num_steps = random_numbers.shape
        paths = np.zeros((num_paths, num_steps + 1))
        paths[:, 0] = max(params.initial_value, 1e-8)
        
        theta = params.mean_reversion_speed
        mu = params.long_term_mean
        sigma = params.volatility
        
        for t in range(num_steps):
            x_pos = np.maximum(paths[:, t], 0)
            paths[:, t + 1] = (
                x_pos +
                theta * (mu - x_pos) * dt +
                sigma * np.sqrt(x_pos * dt) * random_numbers[:, t]
            )
            paths[:, t + 1] = np.maximum(paths[:, t + 1], 0)
        
        return paths
    
    def _generate_vasicek_paths(
        self,
        params: PathGenerationParams,
        random_numbers: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Generate Vasicek interest rate paths.
        
        Same as OU process:
        dr = a(b - r)dt + σdW
        """
        return self._generate_ou_paths(params, random_numbers, dt)
    
    def _generate_hull_white_paths(
        self,
        params: PathGenerationParams,
        random_numbers: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Generate Hull-White one-factor paths.
        
        dr = (θ(t) - ar)dt + σdW
        
        For constant θ, reduces to Vasicek.
        """
        return self._generate_ou_paths(params, random_numbers, dt)
    
    def _generate_heston_paths(
        self,
        params: PathGenerationParams,
        dt: float
    ) -> np.ndarray:
        """
        Generate Heston stochastic volatility paths.
        
        dS = μS dt + √V S dW₁
        dV = κ(θ - V)dt + σ_v √V dW₂
        
        where dW₁ dW₂ = ρ dt
        """
        num_paths = params.num_paths
        num_steps = params.num_steps
        
        # Generate correlated random numbers
        z1 = np.random.standard_normal((num_paths, num_steps))
        z2 = np.random.standard_normal((num_paths, num_steps))
        
        rho = params.correlation
        w1 = z1
        w2 = rho * z1 + np.sqrt(1 - rho ** 2) * z2
        
        # Initialize paths
        paths = np.zeros((num_paths, num_steps + 1))
        variance = np.zeros((num_paths, num_steps + 1))
        
        paths[:, 0] = params.initial_value
        variance[:, 0] = params.initial_variance
        
        kappa = params.mean_reversion_speed
        theta = params.volatility ** 2  # Long-term variance
        sigma_v = params.vol_of_vol
        mu = params.drift
        
        for t in range(num_steps):
            v_pos = np.maximum(variance[:, t], 0)
            sqrt_v = np.sqrt(v_pos)
            
            # Variance process (CIR)
            variance[:, t + 1] = (
                v_pos +
                kappa * (theta - v_pos) * dt +
                sigma_v * sqrt_v * np.sqrt(dt) * w2[:, t]
            )
            variance[:, t + 1] = np.maximum(variance[:, t + 1], 0)
            
            # Asset price process
            paths[:, t + 1] = paths[:, t] * np.exp(
                (mu - 0.5 * v_pos) * dt +
                sqrt_v * np.sqrt(dt) * w1[:, t]
            )
        
        return paths
    
    def _generate_merton_jump_paths(
        self,
        params: PathGenerationParams,
        random_numbers: np.ndarray,
        dt: float
    ) -> np.ndarray:
        """
        Generate Merton jump-diffusion paths.
        
        dS/S = (μ - λk)dt + σdW + (J-1)dN
        
        where N is Poisson process with intensity λ
        and J is lognormal jump size.
        """
        num_paths, num_steps = random_numbers.shape
        paths = np.zeros((num_paths, num_steps + 1))
        paths[:, 0] = params.initial_value
        
        mu = params.drift
        sigma = params.volatility
        lambda_j = params.jump_intensity
        mu_j = params.jump_mean
        sigma_j = params.jump_std
        
        # Expected jump compensation
        k = np.exp(mu_j + 0.5 * sigma_j ** 2) - 1
        
        for t in range(num_steps):
            # Number of jumps (Poisson)
            n_jumps = np.random.poisson(lambda_j * dt, num_paths)
            
            # Total jump size (compound lognormal)
            total_jump = np.ones(num_paths)
            for i in range(num_paths):
                if n_jumps[i] > 0:
                    jumps = np.exp(
                        mu_j + sigma_j * np.random.standard_normal(n_jumps[i])
                    )
                    total_jump[i] = np.prod(jumps)
            
            # GBM with compensated drift
            drift_term = (mu - lambda_j * k - 0.5 * sigma ** 2) * dt
            diffusion_term = sigma * np.sqrt(dt) * random_numbers[:, t]
            
            paths[:, t + 1] = paths[:, t] * np.exp(
                drift_term + diffusion_term
            ) * total_jump
        
        return paths
    
    def _apply_moment_matching(
        self,
        random_numbers: np.ndarray
    ) -> np.ndarray:
        """Apply moment matching for variance reduction."""
        mean = np.mean(random_numbers, axis=0)
        std = np.std(random_numbers, axis=0)
        std = np.where(std > 0, std, 1.0)
        return (random_numbers - mean) / std
    
    def details(self) -> Dict[str, Any]:
        """Get generator details."""
        base = super().details()
        base.update({
            "seed": self._seed,
            "use_antithetic": self._use_antithetic,
            "use_moment_matching": self._use_moment_matching
        })
        return base
