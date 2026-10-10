"""
QLRisk - Loss Given Default Calculator (Python)
==============================================================

Pure Python implementation of LGD calculation.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import math
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from ..base import (
    filter_dict_for_dataclass,
    CreditRiskCalculator,
    CalculatorType,
    ImplementationType
)


class LGDModel(Enum):
    """LGD calculation models."""
    FIXED = "fixed"  # Fixed LGD assumption
    COLLATERAL = "collateral"  # Collateral-based
    WORKOUT = "workout"  # Workout-based (historical)
    MARKET = "market"  # Market-based (bond prices)
    STOCHASTIC = "stochastic"  # Stochastic LGD


class CollateralType(Enum):
    """Types of collateral."""
    CASH = "cash"
    GOVERNMENT_BONDS = "government_bonds"
    CORPORATE_BONDS = "corporate_bonds"
    EQUITIES = "equities"
    REAL_ESTATE = "real_estate"
    RECEIVABLES = "receivables"
    OTHER = "other"


@dataclass
class CollateralInfo:
    """Collateral information."""
    collateral_type: CollateralType
    value: float
    haircut: float = 0.0
    currency: str = "USD"
    
    @property
    def effective_value(self) -> float:
        """Get collateral value after haircut."""
        return self.value * (1.0 - self.haircut)


@dataclass
class LGDInput:
    """Input data for LGD calculation."""
    # Common
    exposure: float = 0.0
    recovery_rate: Optional[float] = None
    
    # For collateral model
    collateral: List[CollateralInfo] = field(default_factory=list)
    
    # For workout model
    recovery_history: Optional[List[float]] = None
    
    # For market model
    bond_price: Optional[float] = None  # As percentage of par
    
    # For stochastic model
    lgd_mean: Optional[float] = None
    lgd_std: Optional[float] = None
    
    # Seniority
    is_senior: bool = True
    is_secured: bool = False


class LGDCalculator(CreditRiskCalculator):
    """
    Loss Given Default Calculator.
    
    Calculates the expected loss severity in the event of default.
    LGD = 1 - Recovery Rate
    
    Supports multiple calculation methods:
    - Fixed LGD
    - Collateral-based LGD
    - Workout-based (historical recovery)
    - Market-based (bond prices)
    - Stochastic LGD
    """
    
    # Basel II/III standardized haircuts
    STANDARD_HAIRCUTS = {
        CollateralType.CASH: 0.0,
        CollateralType.GOVERNMENT_BONDS: 0.02,
        CollateralType.CORPORATE_BONDS: 0.10,
        CollateralType.EQUITIES: 0.25,
        CollateralType.REAL_ESTATE: 0.35,
        CollateralType.RECEIVABLES: 0.40,
        CollateralType.OTHER: 0.50
    }
    
    # Base LGD by seniority (Basel estimates)
    BASE_LGD = {
        ("senior", "secured"): 0.25,
        ("senior", "unsecured"): 0.45,
        ("subordinated", "secured"): 0.50,
        ("subordinated", "unsecured"): 0.75
    }
    
    def __init__(self, name: str = "", config: Optional[Dict[str, Any]] = None):
        """
        Initialize LGD calculator.
        
        Args:
            name: Calculator name
            config: Configuration with optional keys:
                - model: LGDModel type
                - default_lgd: Default LGD if not calculated
                - floor: Minimum LGD
                - cap: Maximum LGD
        """
        config = config or {}
        name = name or self.__class__.__name__
        super().__init__(name, config)
        self._implementation_type = ImplementationType.PYTHON
        self._model = LGDModel(config.get("model", LGDModel.COLLATERAL.value))
        self._default_lgd = config.get("default_lgd", 0.45)
        self._floor = config.get("floor", 0.0)
        self._cap = config.get("cap", 1.0)
    
    @property
    def calculator_type(self) -> CalculatorType:
        return CalculatorType.LGD
    
    def _calculate_impl(self, data: Any) -> float:
        """
        Calculate loss given default.
        
        Args:
            data: LGDInput or dict with required fields
            
        Returns:
            Loss given default (0 to 1)
        """
        if isinstance(data, dict):
            filtered_data = filter_dict_for_dataclass(data, LGDInput)
            lgd_input = LGDInput(**filtered_data)
        else:
            lgd_input = data
        
        if self._model == LGDModel.FIXED:
            lgd = self._fixed_lgd(lgd_input)
        elif self._model == LGDModel.COLLATERAL:
            lgd = self._collateral_lgd(lgd_input)
        elif self._model == LGDModel.WORKOUT:
            lgd = self._workout_lgd(lgd_input)
        elif self._model == LGDModel.MARKET:
            lgd = self._market_lgd(lgd_input)
        elif self._model == LGDModel.STOCHASTIC:
            lgd = self._stochastic_lgd(lgd_input)
        else:
            raise ValueError(f"Unknown LGD model: {self._model}")
        
        # Apply floor and cap
        return max(self._floor, min(self._cap, lgd))
    
    def _fixed_lgd(self, data: LGDInput) -> float:
        """
        Fixed LGD based on recovery rate or seniority.
        
        Args:
            data: LGDInput
            
        Returns:
            Loss given default
        """
        if data.recovery_rate is not None:
            return 1.0 - data.recovery_rate
        
        # Use seniority-based default
        seniority = "senior" if data.is_senior else "subordinated"
        security = "secured" if data.is_secured else "unsecured"
        
        return self.BASE_LGD.get((seniority, security), self._default_lgd)
    
    def _collateral_lgd(self, data: LGDInput) -> float:
        """
        Collateral-based LGD.
        
        LGD = max(0, EAD - Effective Collateral) / EAD
        
        Args:
            data: LGDInput with collateral information
            
        Returns:
            Loss given default
        """
        if data.exposure <= 0:
            return 0.0
        
        # Calculate total effective collateral
        total_collateral = sum(c.effective_value for c in data.collateral)
        
        # Calculate loss after collateral
        loss = max(0.0, data.exposure - total_collateral)
        
        lgd = loss / data.exposure
        
        return lgd
    
    def _workout_lgd(self, data: LGDInput) -> float:
        """
        Workout-based LGD from historical recovery data.
        
        Uses average historical recovery rate.
        
        Args:
            data: LGDInput with recovery_history
            
        Returns:
            Loss given default
        """
        if data.recovery_history is None or len(data.recovery_history) == 0:
            return self._default_lgd
        
        avg_recovery = sum(data.recovery_history) / len(data.recovery_history)
        
        return 1.0 - avg_recovery
    
    def _market_lgd(self, data: LGDInput) -> float:
        """
        Market-based LGD from bond prices.
        
        LGD = 1 - (Bond Price / 100)
        
        Args:
            data: LGDInput with bond_price
            
        Returns:
            Loss given default
        """
        if data.bond_price is None:
            return self._default_lgd
        
        # Bond price is typically quoted as percentage of par
        recovery_rate = data.bond_price / 100.0
        
        return 1.0 - recovery_rate
    
    def _stochastic_lgd(self, data: LGDInput) -> float:
        """
        Stochastic LGD using beta distribution.
        
        Returns the expected LGD from a beta distribution.
        
        Args:
            data: LGDInput with lgd_mean and lgd_std
            
        Returns:
            Expected loss given default
        """
        mean = data.lgd_mean if data.lgd_mean is not None else self._default_lgd
        std = data.lgd_std if data.lgd_std is not None else 0.1
        
        # For expected value, just return mean
        # In simulation, would draw from beta distribution
        return mean
    
    def calculate_recovery_rate(self, data: LGDInput) -> float:
        """
        Calculate recovery rate (1 - LGD).
        
        Args:
            data: LGDInput
            
        Returns:
            Recovery rate (0 to 1)
        """
        lgd = self._calculate_impl(data)
        return 1.0 - lgd
    
    def get_standard_haircut(self, collateral_type: CollateralType) -> float:
        """
        Get standard haircut for collateral type.
        
        Args:
            collateral_type: Type of collateral
            
        Returns:
            Standard haircut
        """
        return self.STANDARD_HAIRCUTS.get(collateral_type, 0.50)
    
    def calculate_effective_collateral(
        self,
        collateral_list: List[CollateralInfo]
    ) -> float:
        """
        Calculate total effective collateral after haircuts.
        
        Args:
            collateral_list: List of collateral items
            
        Returns:
            Total effective collateral value
        """
        return sum(c.effective_value for c in collateral_list)
    
    def details(self) -> Dict[str, Any]:
        """Get calculator details."""
        base_details = super().details()
        base_details.update({
            "model": self._model.value,
            "default_lgd": self._default_lgd,
            "floor": self._floor,
            "cap": self._cap,
            "available_models": [m.value for m in LGDModel]
        })
        return base_details
