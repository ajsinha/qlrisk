"""
QLRisk - Calculator Factory
==========================================

Factory for creating and managing calculators.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

import inspect
from typing import Union, Dict, Any, Type, Optional, List
from threading import Lock

from ..core.logger import get_logger

from .base import (
    BaseCalculator,
    CalculatorType,
    ImplementationType,
    DataCalculatorLike
)

logger = get_logger(__name__)


class CalculatorFactory:
    """
    Factory for creating calculator instances.
    
    Supports both Python and QuantLib implementations with
    lazy loading and caching capabilities.
    """
    
    _instance: Optional['CalculatorFactory'] = None
    _lock = Lock()
    
    # Registry mapping (calculator_type, implementation_type) -> calculator_class
    _registry: Dict[tuple, Type[BaseCalculator]] = {}
    
    # Cache for calculator instances
    _cache: Dict[str, BaseCalculator] = {}
    
    def __new__(cls) -> 'CalculatorFactory':
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the factory."""
        if self._initialized:
            return
        self._initialized = True
        self._default_implementation = ImplementationType.PYTHON
        self._register_calculators()
    
    def _register_calculators(self) -> None:
        """Register all available calculators."""
        # Import Python calculators
        from .python.pd_calculator import PDCalculator as PyPDCalculator
        from .python.lgd_calculator import LGDCalculator as PyLGDCalculator
        from .python.ead_calculator import EADCalculator as PyEADCalculator
        from .python.el_calculator import ExpectedLossCalculator as PyELCalculator
        from .python.ce_calculator import CurrentExposureCalculator as PyCECalculator
        from .python.pfe_calculator import PFECalculator as PyPFECalculator
        from .python.ee_calculator import ExpectedExposureCalculator as PyEECalculator
        from .python.cva_calculator import CVACalculator as PyCVACalculator
        from .python.ec_calculator import EconomicCapitalCalculator as PyECCalculator
        from .python.raroc_calculator import RAROCCalculator as PyRAROCCalculator
        from .python.im_calculator import InitialMarginCalculator as PyIMCalculator
        from .python.stress_calculators import (
            StressedExposureCalculator as PyStressedExposureCalculator,
            PeakExposureCalculator as PyPeakExposureCalculator
        )
        from .python.xva_calculators import (
            DVACalculator as PyDVACalculator, FVACalculator as PyFVACalculator,
            KVACalculator as PyKVACalculator, MVACalculator as PyMVACalculator,
        )
        from .python.var_calculators import (
            VaRCalculator as PyVaRCalculator,
            ExpectedShortfallCalculator as PyESCalculator,
        )
        
        # Register Python implementations
        python_calculators = {
            CalculatorType.PD: PyPDCalculator,
            CalculatorType.LGD: PyLGDCalculator,
            CalculatorType.EAD: PyEADCalculator,
            CalculatorType.EL: PyELCalculator,
            CalculatorType.CE: PyCECalculator,
            CalculatorType.PFE: PyPFECalculator,
            CalculatorType.EE: PyEECalculator,
            CalculatorType.PEAK_EXPOSURE: PyPeakExposureCalculator,
            CalculatorType.STRESSED_EXPOSURE: PyStressedExposureCalculator,
            CalculatorType.CVA: PyCVACalculator,
            CalculatorType.EC: PyECCalculator,
            CalculatorType.RAROC: PyRAROCCalculator,
            CalculatorType.IM: PyIMCalculator,
            CalculatorType.DVA: PyDVACalculator,
            CalculatorType.FVA: PyFVACalculator,
            CalculatorType.KVA: PyKVACalculator,
            CalculatorType.MVA: PyMVACalculator,
            CalculatorType.VAR: PyVaRCalculator,
            CalculatorType.EXPECTED_SHORTFALL: PyESCalculator,
        }
        
        for calc_type, calc_class in python_calculators.items():
            self.register(calc_type, ImplementationType.PYTHON, calc_class)
        
        # Try to import QuantLib calculators
        try:
            from .qlib.pd_calculator import QLPDCalculator
            from .qlib.lgd_calculator import QLLGDCalculator
            from .qlib.ead_calculator import QuantLibEADCalculator as QLEADCalculator
            from .qlib.el_calculator import QuantLibELCalculator as QLELCalculator
            from .qlib.ce_calculator import QuantLibCECalculator as QLCECalculator
            from .qlib.pfe_calculator import QuantLibPFECalculator as QLPFECalculator
            from .qlib.ee_calculator import (
                QuantLibEECalculator as QLEECalculator,
                QuantLibEffectiveEECalculator as QLEffectiveExpectedExposureCalculator,
            )
            from .qlib.cva_calculator import QuantLibCVACalculator as QLCVACalculator
            from .qlib.ec_calculator import QuantLibECCalculator as QLECCalculator
            from .qlib.raroc_calculator import QuantLibRAROCCalculator as QLRAROCCalculator
            from .qlib.im_calculator import QuantLibIMCalculator as QLIMCalculator
            from .qlib.stress_calculators import (
                QLStressedExposureCalculator,
                QLPeakExposureCalculator
            )
            
            # Register QuantLib implementations
            qlib_calculators = {
                CalculatorType.PD: QLPDCalculator,
                CalculatorType.LGD: QLLGDCalculator,
                CalculatorType.EAD: QLEADCalculator,
                CalculatorType.EL: QLELCalculator,
                CalculatorType.CE: QLCECalculator,
                CalculatorType.PFE: QLPFECalculator,
                CalculatorType.EE: QLEECalculator,
                CalculatorType.EEE: QLEffectiveExpectedExposureCalculator,
                CalculatorType.PEAK_EXPOSURE: QLPeakExposureCalculator,
                CalculatorType.STRESSED_EXPOSURE: QLStressedExposureCalculator,
                CalculatorType.CVA: QLCVACalculator,
                CalculatorType.EC: QLECCalculator,
                CalculatorType.RAROC: QLRAROCCalculator,
                CalculatorType.IM: QLIMCalculator,
            }
            
            for calc_type, calc_class in qlib_calculators.items():
                # Skip QuantLib calculators that don't yet implement the BaseCalculator interface
                if inspect.isabstract(calc_class):
                    logger.warning(
                        f"QuantLib {calc_type.value} calculator ({calc_class.__name__}) is incomplete; "
                        "falling back to Python implementation"
                    )
                    continue
                self.register(calc_type, ImplementationType.QUANTLIB, calc_class)
                
        except ImportError:
            # QuantLib not available - only Python implementations registered
            pass
    
    def register(
        self,
        calculator_type: CalculatorType,
        implementation: ImplementationType,
        calculator_class: Type[BaseCalculator]
    ) -> None:
        """
        Register a calculator class.
        
        Args:
            calculator_type: Type of calculator
            implementation: Implementation type (Python or QuantLib)
            calculator_class: Calculator class to register
        """
        key = (calculator_type, implementation)
        self._registry[key] = calculator_class
    
    def create(
        self,
        calculator_type: CalculatorType,
        name: str,
        config: Dict[str, Any],
        implementation: Optional[ImplementationType] = None,
        use_cache: bool = True
    ) -> BaseCalculator:
        """
        Create a calculator instance.
        
        Args:
            calculator_type: Type of calculator to create
            name: Unique name for the calculator instance
            config: Configuration dictionary
            implementation: Implementation type (defaults to factory default)
            use_cache: Whether to cache and reuse calculator instances
            
        Returns:
            Calculator instance
            
        Raises:
            ValueError: If calculator type/implementation not found
        """
        impl = implementation or self._default_implementation
        
        # Check cache first
        cache_key = f"{calculator_type.value}:{impl.value}:{name}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        # Look up calculator class
        key = (calculator_type, impl)
        if key not in self._registry:
            # Fall back to Python if QuantLib not available
            if impl == ImplementationType.QUANTLIB:
                key = (calculator_type, ImplementationType.PYTHON)
                if key not in self._registry:
                    raise ValueError(
                        f"Calculator not found: {calculator_type.value} "
                        f"(no implementations available)"
                    )
            else:
                raise ValueError(
                    f"Calculator not found: {calculator_type.value} ({impl.value})"
                )
        
        calculator_class = self._registry[key]
        calculator = calculator_class(name, config)
        
        # Cache the instance
        if use_cache:
            self._cache[cache_key] = calculator
        
        return calculator
    
    def get_pd_calculator(
        self,
        name: str = "pd_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create a Probability of Default calculator."""
        return self.create(
            CalculatorType.PD, name, config or {}, implementation
        )
    
    def get_lgd_calculator(
        self,
        name: str = "lgd_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create a Loss Given Default calculator."""
        return self.create(
            CalculatorType.LGD, name, config or {}, implementation
        )
    
    def get_ead_calculator(
        self,
        name: str = "ead_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create an Exposure at Default calculator."""
        return self.create(
            CalculatorType.EAD, name, config or {}, implementation
        )
    
    def get_el_calculator(
        self,
        name: str = "el_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create an Expected Loss calculator."""
        return self.create(
            CalculatorType.EL, name, config or {}, implementation
        )
    
    def get_ce_calculator(
        self,
        name: str = "ce_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create a Current Exposure calculator."""
        return self.create(
            CalculatorType.CE, name, config or {}, implementation
        )
    
    def get_pfe_calculator(
        self,
        name: str = "pfe_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create a Potential Future Exposure calculator."""
        return self.create(
            CalculatorType.PFE, name, config or {}, implementation
        )
    
    def get_ee_calculator(
        self,
        name: str = "ee_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create an Expected Exposure calculator."""
        return self.create(
            CalculatorType.EE, name, config or {}, implementation
        )
    
    def get_eee_calculator(
        self,
        name: str = "eee_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create an Effective Expected Exposure calculator."""
        return self.create(
            CalculatorType.EEE, name, config or {}, implementation
        )
    
    def get_cva_calculator(
        self,
        name: str = "cva_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create a Credit Valuation Adjustment calculator."""
        return self.create(
            CalculatorType.CVA, name, config or {}, implementation
        )
    
    def get_ec_calculator(
        self,
        name: str = "ec_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create an Economic Capital calculator."""
        return self.create(
            CalculatorType.EC, name, config or {}, implementation
        )
    
    def get_im_calculator(
        self,
        name: str = "im_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create an Initial Margin calculator."""
        return self.create(
            CalculatorType.IM, name, config or {}, implementation
        )
    
    def get_mtm_calculator(
        self,
        name: str = "mtm_calc",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None
    ) -> BaseCalculator:
        """Create a Mark-to-Market calculator."""
        return self.create(
            CalculatorType.MTM, name, config or {}, implementation
        )
    
    def set_default_implementation(self, implementation: ImplementationType) -> None:
        """Set the default implementation type."""
        self._default_implementation = implementation
    
    @classmethod
    def get_instance(cls) -> 'CalculatorFactory':
        """The singleton factory (same as CalculatorFactory() or get_calculator_factory())."""
        return cls()
    
    def get_calculator(
        self,
        calc_type: Union[str, CalculatorType],
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[str] = None
    ) -> BaseCalculator:
        """
        Generic method to get any calculator by type string.
        
        Args:
            calc_type: CalculatorType, or a type string (e.g., 'pd', 'lgd', 'ead', 'el', 'var', ...)
            name: Optional calculator name
            config: Optional configuration
            implementation: 'python', or 'quantlib' / 'qlib' (falls back to Python where incomplete)
            
        Returns:
            Calculator instance
        """
        # Map string to implementation type
        impl = None
        if implementation:
            impl_text = getattr(implementation, "value", implementation)
            impl = ImplementationType.PYTHON if str(impl_text).lower() == "python" else ImplementationType.QUANTLIB
        
        if isinstance(calc_type, CalculatorType):
            return self.create(calc_type, name or f"{calc_type.value}_calc", config or {}, impl)
        
        # Map calc_type string to method
        calc_type_lower = calc_type.lower()
        method_map = {
            "pd": self.get_pd_calculator,
            "lgd": self.get_lgd_calculator,
            "ead": self.get_ead_calculator,
            "el": self.get_el_calculator,
            "ce": self.get_ce_calculator,
            "pfe": self.get_pfe_calculator,
            "ee": self.get_ee_calculator,
            "eee": self.get_eee_calculator,
            "cva": self.get_cva_calculator,
            "ec": self.get_ec_calculator,
            "im": self.get_im_calculator,
            "mtm": self.get_mtm_calculator,
            "raroc": lambda **kw: self.create(CalculatorType.RAROC, kw.get("name") or "raroc_calc", kw.get("config") or {}, kw.get("implementation")),
            "var": lambda **kw: self.create(CalculatorType.VAR, kw.get("name") or "var_calc", kw.get("config") or {}, kw.get("implementation")),
            "es": lambda **kw: self.create(CalculatorType.EXPECTED_SHORTFALL, kw.get("name") or "es_calc", kw.get("config") or {}, kw.get("implementation")),
            "stressed_exposure": lambda **kw: self.create(CalculatorType.STRESSED_EXPOSURE, kw.get("name") or "stressed_exposure_calc", kw.get("config") or {}, kw.get("implementation")),
            "peak_exposure": lambda **kw: self.create(CalculatorType.PEAK_EXPOSURE, kw.get("name") or "peak_exposure_calc", kw.get("config") or {}, kw.get("implementation")),
        }
        
        if calc_type_lower not in method_map:
            raise ValueError(f"Unknown calculator type: {calc_type}")
        
        method = method_map[calc_type_lower]
        
        # Special handling for lambda functions (stress calculators)
        if calc_type_lower in ["stressed_exposure", "peak_exposure", "raroc", "var", "es"]:
            return method(name=name or f"{calc_type_lower}_calc", config=config, implementation=impl)
        
        return method(name=name or f"{calc_type_lower}_calc", config=config, implementation=impl)
    
    def get_available_calculators(self) -> List[Dict[str, str]]:
        """Get list of available calculators."""
        return [
            {
                "type": calc_type.value,
                "implementation": impl.value
            }
            for calc_type, impl in self._registry.keys()
        ]
    
    def clear_cache(self) -> None:
        """Clear the calculator cache."""
        self._cache.clear()
    
    def is_quantlib_available(self) -> bool:
        """Check if QuantLib implementations are available."""
        try:
            import QuantLib
            return True
        except ImportError:
            return False


# Convenience function
def get_calculator_factory() -> CalculatorFactory:
    """Get the singleton calculator factory instance."""
    return CalculatorFactory()
