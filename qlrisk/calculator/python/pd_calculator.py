"""
QLRisk - Probability of Default Calculator (Python)
==================================================================

Pure Python implementation of PD calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from ..base import (
    CreditRiskCalculator,
    CalculatorType,
    ImplementationType,
    CalculationResult,
    filter_dict_for_dataclass
)


class PDModel(Enum):
    """PD calculation models."""
    STRUCTURAL = "structural"  # Merton model
    REDUCED_FORM = "reduced_form"  # Hazard rate model
    TRANSITION_MATRIX = "transition_matrix"  # Rating transition
    LOGISTIC = "logistic"  # Logistic regression
    HISTORICAL = "historical"  # Historical default rates


@dataclass
class PDInput:
    """Input data for PD calculation."""
    # For Merton model
    asset_value: Optional[float] = None
    debt_value: Optional[float] = None
    asset_volatility: Optional[float] = None
    risk_free_rate: Optional[float] = None
    time_horizon: float = 1.0  # years
    
    # For hazard rate model
    hazard_rate: Optional[float] = None
    
    # For rating-based
    credit_rating: Optional[str] = None
    rating_pd: Optional[float] = None
    
    # For logistic model
    financial_ratios: Optional[Dict[str, float]] = None
    model_coefficients: Optional[Dict[str, float]] = None


class PDCalculator(CreditRiskCalculator):
    """
    Probability of Default Calculator.
    
    Supports multiple PD estimation methods:
    - Structural (Merton) model
    - Reduced-form (hazard rate) model
    - Transition matrix approach
    - Logistic regression
    - Historical default rates
    """
    
    # Default rating PDs (1-year, Basel estimates)
    RATING_PDS = {
        "AAA": 0.0001, "AA+": 0.0002, "AA": 0.0003, "AA-": 0.0005,
        "A+": 0.0008, "A": 0.0010, "A-": 0.0015,
        "BBB+": 0.0025, "BBB": 0.0040, "BBB-": 0.0070,
        "BB+": 0.0100, "BB": 0.0150, "BB-": 0.0250,
        "B+": 0.0400, "B": 0.0600, "B-": 0.1000,
        "CCC+": 0.1500, "CCC": 0.2500, "CCC-": 0.3500,
        "CC": 0.5000, "C": 0.7000, "D": 1.0000
    }
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize PD calculator.
        
        Args:
            name: Calculator name
            config: Configuration with optional keys:
                - model: PDModel type (default: STRUCTURAL)
                - time_horizon: Time horizon in years (default: 1.0)
        """
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._model = PDModel(config.get("model", PDModel.STRUCTURAL.value))
        self._time_horizon = config.get("time_horizon", 1.0)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.PD
    
    def _calculate_impl(self, data: Any) -> float:
        """
        Calculate probability of default.
        
        Args:
            data: PDInput or dict with required fields
            
        Returns:
            Probability of default (0 to 1)
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, PDInput)
            pd_input = PDInput(**filtered_data)
        else:
            pd_input = data
        
        if self._model == PDModel.STRUCTURAL:
            return self._merton_pd(pd_input)
        elif self._model == PDModel.REDUCED_FORM:
            return self._hazard_rate_pd(pd_input)
        elif self._model == PDModel.TRANSITION_MATRIX:
            return self._transition_matrix_pd(pd_input)
        elif self._model == PDModel.LOGISTIC:
            return self._logistic_pd(pd_input)
        elif self._model == PDModel.HISTORICAL:
            return self._historical_pd(pd_input)
        else:
            raise ValueError(f"Unknown PD model: {self._model}")
    
    def _merton_pd(self, data: PDInput) -> float:
        """
        Merton structural model for PD.
        
        PD = N(-d2) where:
        d2 = [ln(V/D) + (r - σ²/2)T] / (σ√T)
        
        Args:
            data: PDInput with asset_value, debt_value, asset_volatility, risk_free_rate
            
        Returns:
            Probability of default
        """
        V = data.asset_value
        D = data.debt_value
        sigma = data.asset_volatility
        r = data.risk_free_rate or 0.0
        T = data.time_horizon
        
        if V is None or D is None or sigma is None:
            raise ValueError("Merton model requires asset_value, debt_value, asset_volatility")
        
        if V <= 0 or D <= 0 or sigma <= 0 or T <= 0:
            raise ValueError("Values must be positive")
        
        # Calculate d2
        d2 = (math.log(V / D) + (r - 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        
        # PD = N(-d2)
        pd = self._norm_cdf(-d2)
        
        return max(0.0, min(1.0, pd))
    
    def _hazard_rate_pd(self, data: PDInput) -> float:
        """
        Reduced-form model using constant hazard rate.
        
        PD = 1 - exp(-λT)
        
        Args:
            data: PDInput with hazard_rate
            
        Returns:
            Probability of default
        """
        hazard_rate = data.hazard_rate
        T = data.time_horizon
        
        if hazard_rate is None:
            raise ValueError("Hazard rate model requires hazard_rate")
        
        if hazard_rate < 0:
            raise ValueError("Hazard rate must be non-negative")
        
        # PD = 1 - survival probability
        pd = 1.0 - math.exp(-hazard_rate * T)
        
        return max(0.0, min(1.0, pd))
    
    def _transition_matrix_pd(self, data: PDInput) -> float:
        """
        Rating transition-based PD.
        
        Uses historical rating transition matrices to estimate PD.
        
        Args:
            data: PDInput with credit_rating
            
        Returns:
            Probability of default
        """
        rating = data.credit_rating
        
        if rating is None:
            raise ValueError("Transition matrix model requires credit_rating")
        
        rating = rating.upper()
        
        if rating not in self.RATING_PDS:
            raise ValueError(f"Unknown rating: {rating}")
        
        base_pd = self.RATING_PDS[rating]
        T = data.time_horizon
        
        # Scale PD for time horizon (simplified)
        # For multi-year, use cumulative PD approximation
        if T <= 1.0:
            pd = base_pd * T
        else:
            # Cumulative PD using marginal PD approximation
            pd = 1.0 - (1.0 - base_pd) ** T
        
        return max(0.0, min(1.0, pd))
    
    def _logistic_pd(self, data: PDInput) -> float:
        """
        Logistic regression PD model.
        
        PD = 1 / (1 + exp(-z))
        where z = β₀ + β₁x₁ + β₂x₂ + ...
        
        Args:
            data: PDInput with financial_ratios and model_coefficients
            
        Returns:
            Probability of default
        """
        ratios = data.financial_ratios
        coefficients = data.model_coefficients
        
        if ratios is None or coefficients is None:
            raise ValueError("Logistic model requires financial_ratios and model_coefficients")
        
        # Calculate z-score
        z = coefficients.get("intercept", 0.0)
        
        for var_name, coef in coefficients.items():
            if var_name != "intercept" and var_name in ratios:
                z += coef * ratios[var_name]
        
        # Logistic function
        pd = 1.0 / (1.0 + math.exp(-z))
        
        return max(0.0, min(1.0, pd))
    
    def _historical_pd(self, data: PDInput) -> float:
        """
        Historical default rate based PD.
        
        Uses provided rating PD directly.
        
        Args:
            data: PDInput with rating_pd
            
        Returns:
            Probability of default
        """
        if data.rating_pd is not None:
            return max(0.0, min(1.0, data.rating_pd))
        
        if data.credit_rating is not None:
            rating = data.credit_rating.upper()
            if rating in self.RATING_PDS:
                return self.RATING_PDS[rating]
        
        raise ValueError("Historical model requires rating_pd or credit_rating")
    
    def _norm_cdf(self, x: float) -> float:
        """
        Standard normal cumulative distribution function.
        
        Uses the error function approximation.
        """
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    
    def calculate_term_structure(
        self,
        data: PDInput,
        time_points: List[float]
    ) -> Dict[float, float]:
        """
        Calculate PD term structure.
        
        Args:
            data: PDInput
            time_points: List of time horizons in years
            
        Returns:
            Dictionary mapping time points to PD values
        """
        results = {}
        original_horizon = data.time_horizon
        
        for t in time_points:
            data.time_horizon = t
            results[t] = self._calculate_impl(data)
        
        data.time_horizon = original_horizon
        return results
    
    @staticmethod
    def get_rating_pd(rating: str) -> float:
        """
        Get default PD for a credit rating.
        
        Args:
            rating: Credit rating (e.g., 'AAA', 'BBB+')
            
        Returns:
            1-year PD
        """
        return PDCalculator.RATING_PDS.get(rating.upper(), 0.05)
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "model": self._model.value,
            "time_horizon": self._time_horizon,
            "available_models": [m.value for m in PDModel]
        })
        return base_details
