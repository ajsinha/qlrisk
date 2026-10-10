"""
QLRisk - Calculator Base Module
==============================================

Abstract base classes and protocols for all calculators.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from abc import ABC, abstractmethod
from typing import Protocol, Dict, Any, Optional, List, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class CalculatorType(Enum):
    """Enumeration of calculator types."""
    # Core Credit Risk Metrics
    PD = "probability_of_default"
    LGD = "loss_given_default"
    EAD = "exposure_at_default"
    EL = "expected_loss"
    
    # Exposure Metrics
    CE = "current_exposure"
    PFE = "potential_future_exposure"
    EE = "expected_exposure"
    EEE = "effective_expected_exposure"
    PEAK_EXPOSURE = "peak_exposure"
    STRESSED_EXPOSURE = "stressed_exposure"
    
    # Advanced Metrics
    CVA = "credit_valuation_adjustment"
    EC = "economic_capital"
    RAROC = "risk_adjusted_return_on_capital"
    IM = "initial_margin"
    
    # Other valuation adjustments
    DVA = "debit_valuation_adjustment"
    FVA = "funding_valuation_adjustment"
    KVA = "capital_valuation_adjustment"
    MVA = "margin_valuation_adjustment"
    
    # Market Risk
    VAR = "value_at_risk"
    EXPECTED_SHORTFALL = "expected_shortfall"
    
    # Pricing
    MTM = "mark_to_market"
    NPV = "net_present_value"


class ImplementationType(Enum):
    """Implementation type - Python or QuantLib."""
    PYTHON = "python"
    QUANTLIB = "qlib"


@dataclass
class CalculationResult:
    """Container for calculation results."""
    calculator_name: str
    calculator_type: CalculatorType
    value: Any
    unit: str = ""
    confidence_level: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "calculator_name": self.calculator_name,
            "calculator_type": self.calculator_type.value,
            "value": self.value,
            "unit": self.unit,
            "confidence_level": self.confidence_level,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "details": self.details,
            "warnings": self.warnings
        }


class DataCalculatorLike(Protocol):
    """
    Protocol defining the interface for all calculators.
    
    All calculators must implement this protocol to ensure
    consistent behavior across the system.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the calculator.
        
        Args:
            name: Unique name for this calculator instance
            config: Configuration dictionary
        """
        ...
    
    def calculate(self, data: Any) -> Any:
        """
        Perform the calculation.
        
        Args:
            data: Input data for calculation
            
        Returns:
            Calculation result
        """
        ...
    
    def details(self) -> Dict[str, Any]:
        """
        Get calculator details.
        
        Returns:
            Dictionary containing calculator metadata and configuration
        """
        ...


T = TypeVar('T')


class BaseCalculator(ABC, Generic[T]):
    """
    Abstract base class for all calculators.
    
    Provides common functionality and enforces the DataCalculatorLike protocol.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the calculator.
        
        Args:
            name: Unique name for this calculator instance
            config: Configuration dictionary
        """
        self._name = name
        self._config = config
        self._calculation_count = 0
        self._last_calculation_time: Optional[datetime] = None
        self._implementation_type = ImplementationType.PYTHON
    
    @property
    def name(self) -> str:
        """Get calculator name."""
        return self._name
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get calculator configuration."""
        return self._config
    
    @property
    def calculation_count(self) -> int:
        """Get total calculation count."""
        return self._calculation_count
    
    @property
    def implementation_type(self) -> ImplementationType:
        """Get implementation type."""
        return self._implementation_type
    
    @property
    @abstractmethod
    def calculator_type(self) -> CalculatorType:
        """Get the calculator type."""
        pass
    
    @abstractmethod
    def _calculate_impl(self, data: Any) -> T:
        """
        Implementation-specific calculation logic.
        
        Args:
            data: Input data for calculation
            
        Returns:
            Calculation result
        """
        pass
    
    def calculate(self, data: Any) -> CalculationResult:
        """
        Perform the calculation with result wrapping.
        
        Args:
            data: Input data for calculation
            
        Returns:
            CalculationResult containing the computed value
        """
        self._calculation_count += 1
        self._last_calculation_time = datetime.now()
        
        result_value = self._calculate_impl(data)
        
        return CalculationResult(
            calculator_name=self._name,
            calculator_type=self.calculator_type,
            value=result_value,
            metadata={
                "implementation": self._implementation_type.value,
                "calculation_count": self._calculation_count
            }
        )
    
    def details(self) -> Dict[str, Any]:
        """
        Get calculator details.
        
        Returns:
            Dictionary containing calculator metadata and configuration
        """
        return {
            "name": self._name,
            "type": self.calculator_type.value,
            "implementation": self._implementation_type.value,
            "calculation_count": self._calculation_count,
            "last_calculation": self._last_calculation_time.isoformat() if self._last_calculation_time else None,
            "config": self._config
        }
    
    def validate_config(self, required_keys: List[str]) -> None:
        """
        Validate that required configuration keys are present.
        
        Args:
            required_keys: List of required configuration keys
            
        Raises:
            ValueError: If a required key is missing
        """
        for key in required_keys:
            if key not in self._config:
                raise ValueError(f"Missing required configuration key: {key}")
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value with optional default.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)


class ExposureCalculator(BaseCalculator[float]):
    """Base class for exposure-related calculators."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._confidence_level = config.get("confidence_level", 0.95)
        self._time_horizon = config.get("time_horizon", 1.0)  # in years
    
    @property
    def confidence_level(self) -> float:
        """Get confidence level for calculations."""
        return self._confidence_level
    
    @property
    def time_horizon(self) -> float:
        """Get time horizon in years."""
        return self._time_horizon


class CreditRiskCalculator(BaseCalculator[float]):
    """Base class for credit risk calculators."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._recovery_rate = config.get("recovery_rate", 0.4)
    
    @property
    def recovery_rate(self) -> float:
        """Get recovery rate assumption."""
        return self._recovery_rate


class PricingCalculator(BaseCalculator[float]):
    """Base class for pricing calculators."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._currency = config.get("currency", "USD")
    
    @property
    def currency(self) -> str:
        """Get pricing currency."""
        return self._currency


def filter_dict_for_dataclass(data: Dict[str, Any], dataclass_type: type) -> Dict[str, Any]:
    """
    Filter a dictionary to only include keys that are valid fields for a dataclass.
    
    Args:
        data: Input dictionary
        dataclass_type: The dataclass type to filter for
        
    Returns:
        Filtered dictionary with only valid keys
    """
    import dataclasses
    if not dataclasses.is_dataclass(dataclass_type):
        return data
    
    valid_fields = {f.name for f in dataclasses.fields(dataclass_type)}
    return {k: v for k, v in data.items() if k in valid_fields}
