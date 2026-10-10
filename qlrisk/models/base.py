"""
Base Model - Abstract base class for all domain models

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com

Legal Notice: This module and the associated software architecture are proprietary 
and confidential. Unauthorized copying, distribution, modification, or use is strictly 
prohibited without explicit written permission from the copyright holder.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import uuid
import json


@dataclass
class ModelBase(ABC):
    """
    Abstract base class for all domain models.
    Provides common functionality for serialization and validation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization validation."""
        self.validate()

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate the model.

        Returns:
            True if valid

        Raises:
            ValidationError: If validation fails
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.

        Returns:
            Dictionary representation
        """
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, ModelBase):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    item.to_dict() if isinstance(item, ModelBase) else item
                    for item in value
                ]
            elif isinstance(value, dict):
                result[key] = {
                    k: v.to_dict() if isinstance(v, ModelBase) else v
                    for k, v in value.items()
                }
            else:
                result[key] = value
        return result

    def to_json(self, indent: int = 2) -> str:
        """
        Convert model to JSON string.

        Args:
            indent: JSON indentation

        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelBase':
        """
        Create model from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Model instance
        """
        # Convert datetime strings back to datetime objects
        for key in ['created_at', 'updated_at']:
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'ModelBase':
        """
        Create model from JSON string.

        Args:
            json_str: JSON string

        Returns:
            Model instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def update(self, **kwargs) -> 'ModelBase':
        """
        Update model attributes.

        Args:
            **kwargs: Attributes to update

        Returns:
            Self for chaining
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()
        self.validate()
        return self

    def clone(self) -> 'ModelBase':
        """
        Create a deep copy with new ID.

        Returns:
            Cloned model
        """
        data = self.to_dict()
        data['id'] = str(uuid.uuid4())
        data['created_at'] = datetime.now()
        data['updated_at'] = datetime.now()
        return self.__class__.from_dict(data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
