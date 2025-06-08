# ~/clientfactory/src/clientfactory/core/bases/declarative.py
"""
Declarative Base Class
---------------------
Core infrastructure for declarative component discovery and metadata management.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import DeclarativeType, DECLARATIVE
from clientfactory.core.metas import DeclarativeMeta

class Declarative(metaclass=DeclarativeMeta):
    """
    Base class for declarative components.

    Provides core functionality for:
    - Automatic discovery of nested components
    - Metadata management and inheritance
    - Runtime access to discovered elements
    """
    _decltype: DeclarativeType
    _declmetadata: t.Dict[str, t.Any]
    _declcomponents: t.Dict[str, type]
    _declmethods: t.Dict[str, t.Dict[str, t.Any]]

    @classmethod
    def getmetadata(cls, k: str, default: t.Any = None) -> t.Any:
        """Get metadata value by key."""
        return cls._declmetadata.get(k, default)

    @classmethod
    def setmetadata(cls, k: str, v: t.Any) -> None:
        """Set metadata value."""
        cls._declmetadata[k] = v

    @classmethod
    def getcomponents(cls) -> t.Dict[str, type]:
        """Get all discovered components."""
        return cls._declcomponents.copy()

    @classmethod
    def getcomponent(cls, name: str) -> t.Optional[type]:
        """Get component by name."""
        return cls._declcomponents.get(name.lower())

    @classmethod
    def getmethods(cls) -> t.Dict[str, t.Dict[str, t.Any]]:
        """Get all discovered methods."""
        return cls._declmethods.copy()

    @classmethod
    def getmethod(cls, name: str) -> t.Optional[t.Dict[str, t.Any]]:
        """Get method info by name."""
        return cls._declmethods.get(name)
