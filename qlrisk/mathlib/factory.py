"""
QLRisk - Math Factory
====================================

Factory for creating mathematical utilities and path generators.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary
and confidential. Unauthorized copying, distribution, modification, or use is
strictly prohibited without explicit written permission from the copyright holder.
"""

from typing import Dict, Any, Optional, Type
from threading import Lock

from .base import (
    BasePathGenerator,
    BaseMonteCarloEngine,
    ImplementationType
)


class MathFactory:
    """
    Factory for creating mathematical utilities.
    
    Supports both Python and QuantLib implementations with
    automatic fallback and caching.
    """
    
    _instance: Optional['MathFactory'] = None
    _lock = Lock()
    _registry: Dict[tuple, Type] = {}
    _cache: Dict[str, Any] = {}
    
    def __new__(cls) -> 'MathFactory':
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'MathFactory':
        """The singleton factory (same as MathFactory())."""
        return cls()
    
    def __init__(self):
        """Initialize the factory."""
        if self._initialized:
            return
        self._initialized = True
        self._default_implementation = ImplementationType.PYTHON
        self._register_components()
    
    def _register_components(self) -> None:
        """Register all available components."""
        # Register Python implementations
        from .python.path_generator import PythonPathGenerator
        self._registry[("path_generator", ImplementationType.PYTHON)] = PythonPathGenerator
        
        # Try to register QuantLib implementations
        try:
            from .qlib.path_generator import QuantLibPathGenerator
            self._registry[("path_generator", ImplementationType.QUANTLIB)] = QuantLibPathGenerator
        except ImportError:
            pass
    
    def create_path_generator(
        self,
        name: str = "path_gen",
        config: Optional[Dict[str, Any]] = None,
        implementation: Optional[ImplementationType] = None,
        use_cache: bool = True
    ) -> BasePathGenerator:
        """
        Create a path generator.
        
        Args:
            name: Generator name
            config: Configuration dictionary
            implementation: Implementation type (ImplementationType or string)
            use_cache: Whether to cache instance
            
        Returns:
            Path generator instance
        """
        # Convert string to ImplementationType if needed
        if isinstance(implementation, str):
            impl = ImplementationType.PYTHON if implementation.lower() == "python" else ImplementationType.QUANTLIB
        else:
            impl = implementation or self._default_implementation
        config = config or {}
        
        cache_key = f"path_generator:{impl.value}:{name}"
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        key = ("path_generator", impl)
        if key not in self._registry:
            # Fall back to Python
            key = ("path_generator", ImplementationType.PYTHON)
            if key not in self._registry:
                raise ValueError("No path generator implementation available")
        
        generator_class = self._registry[key]
        generator = generator_class(name, config)
        
        if use_cache:
            self._cache[cache_key] = generator
        
        return generator
    
    def set_default_implementation(self, implementation: ImplementationType) -> None:
        """Set default implementation type."""
        self._default_implementation = implementation
    
    def is_quantlib_available(self) -> bool:
        """Check if QuantLib is available."""
        try:
            import QuantLib
            return True
        except ImportError:
            return False
    
    def clear_cache(self) -> None:
        """Clear the component cache."""
        self._cache.clear()
    
    def get_available_components(self) -> Dict[str, list]:
        """Get list of available components by type."""
        components = {}
        for (comp_type, impl), _ in self._registry.items():
            if comp_type not in components:
                components[comp_type] = []
            components[comp_type].append(impl.value)
        return components


def get_math_factory() -> MathFactory:
    """Get the singleton math factory instance."""
    return MathFactory()
