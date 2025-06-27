# ~/clientfactory/src/clientfactory/core/utils/typed/sentinel.py
"""
Sentinel Value Utilities
-----------------------
Sentinel objects for distinguishing between explicitly passed and omitted values.
"""
from __future__ import annotations
import typing as t

class Sentinel:
    """
    A sentinel object that can stand in for any type in function signatures.

    Provides a way to distinguish between explicitly passed values (including None)
    and parameters that were omitted entirely. Supports subscript and attribute
    access syntax for encoding default values within the sentinel.

    Example:
        def func(value: int = UNSET[42], enabled: bool = UNSET[False]):
            if value is UNSET:
                value = 42  # Or call UNSET[42] to get the encoded default
            if enabled is UNSET:
                enabled = False

        func(0, False)  # Explicitly passed 0 and False
        func()          # Both parameters are UNSET, use defaults
    """
    def __getitem__(self, key) -> 'Sentinel':
        """
        Support subscript syntax for encoding default values.

        Args:
            key: The default value or factory to encode

        Returns:
            Self, allowing chaining and type compatibility

        Example:
            UNSET[list] represents "unset, default to calling list()"
            UNSET[False] represents "unset, default to False"
        """
        return self

    def __getattr__(self, name) -> 'Sentinel':
        """
        Support attribute access for any attribute name.

        Args:
            name: Any attribute name

        Returns:
            Self, maintaining sentinel behavior

        Note:
            This enables UNSET to satisfy any type checker requirements
            while preserving its sentinel nature at runtime.
        """
        return self


UNSET: t.Any = Sentinel()
"""
Universal sentinel value for distinguishing unset parameters.

Type-hinted as Any to satisfy any parameter type in function signatures
while maintaining its sentinel identity for runtime checks.

Usage:
   def method(parent: ParentType = UNSET):
       if parent is UNSET:
           # Handle unset case
       else:
           # Use explicitly passed parent
"""
