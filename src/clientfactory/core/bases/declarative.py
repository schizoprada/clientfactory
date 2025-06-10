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
    # no __declarable__
    _decltype: DeclarativeType
    _declmetadata: t.Dict[str, t.Any]
    _declcomponents: t.Dict[str, type]
    _declmethods: t.Dict[str, t.Dict[str, t.Any]]
    _declconfigs: t.Dict[str, t.Any]
    _declattrs: t.Dict[str, t.Any]

    def _resolveconfigs(self, conf: t.Any = None, **provided: t.Any) -> t.Any:
        """Resolve config from declarations and merge with provided config."""
        # Implementation depends on mapping flow we decide later
        pass

    def _resolveattributes(self, **provided: t.Any) -> dict:
        """Resolve attributes from declarations and provided values."""
        declarable: set = getattr(self.__class__, '__declattrs__', set())
        declared: dict = getattr(self.__class__, '_declattrs', {})
        resolved: dict = {}

        for name in declarable:
            if (name in provided):
                resolved[name] = provided[name]
            elif name in declared:
                resolved[name] = declared[name]
            else:
                resolved[name] = None

        return resolved

    def _resolvecomponents(self, **provided: t.Any) -> dict:
        """Resolve components from declarations and constructor params."""
        declarable: set = getattr(self.__class__, '__declcomps__', set())
        declared: dict = getattr(self.__class__, '_declcomponents', {})
        resolved: dict = {}

        for name in declarable:
            # constructor param beats declaration
            if (name in provided):
                resolved[name] = provided[name]
            elif (name in declared):
                declaration = declared[name]
                if (declaration['type'] == 'class'):
                    resolved[name] = declaration['value']() # lazy instantiation
                else:
                    resolved[name] = declaration['value']
            else:
                resolved[name] = None

        return resolved

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
