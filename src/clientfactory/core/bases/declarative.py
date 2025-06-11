# ~/clientfactory/src/clientfactory/core/bases/declarative.py
"""
Declarative Base Class
---------------------
Core infrastructure for declarative component discovery and metadata management.
"""
from __future__ import annotations
import abc, typing as t

from pydantic import BaseModel as PydModel

from clientfactory.core.metas import DeclarativeMeta
from clientfactory.core.models import (
    DeclarativeType, DECLARATIVE, DeclarableConfig
)

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

    @abc.abstractmethod
    def _resolveattributes(self, attributes: dict) -> None:
        """Apply collected attributes to the component. Subclasses must implement."""
        ...

    def _resolveconfig(self, confclass: t.Type, conf: t.Any = None, **provided: t.Any) -> t.Any:
        """Resolve config from declarations and merge with provided config."""
        declarable: set = getattr(self.__class__, '__declconfs__', set())
        declared: dict = getattr(self.__class__, '_declconfigs', {})

        configvalues = {}
        for name in declarable:
            if name in provided:
                configvalues[name] = provided[name]
            elif name in declared:
                configvalues[name] = declared[name]
            # skip if neither provided not declared (config defaults)

        if conf is not None:
            # update existing config with resolved values
            if isinstance(conf, PydModel):
                return conf.model_copy(update=configvalues)
            # if its not a pydantic model, try updating directly
            else:
                for k,v in configvalues.items():
                    if hasattr(conf, k):
                        setattr(conf, k, v)
                return conf

        if issubclass(confclass, DeclarableConfig):
            return confclass.FromDeclarations(configvalues)
        # fallback for non-declarable
        return confclass(**configvalues)

    def _collectattributes(self, **provided: t.Any) -> dict:
        """Collect attributes from declarations and provided values."""
        declarable: set = getattr(self.__class__, '__declattrs__', set())
        declared: dict = getattr(self.__class__, '_declattrs', {})
        collected: dict = {}

        for name in declarable:
            if (name in provided):
                collected[name] = provided[name]
            elif name in declared:
                collected[name] = declared[name]
            else:
                collected[name] = None

        return collected

    def _resolvecomponents(self, **provided: t.Any) -> dict:
        """Resolve components from declarations and constructor params."""
        declarable: set = getattr(self.__class__, '__declcomps__', set())
        declared: dict = getattr(self.__class__, '_declcomponents', {})
        resolved: dict = {}

        for name in declarable:
            # constructor param beats declaration
            if (name in provided) and (provided[name] is not None):
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

    ## ahhh ##
    def __getattr__(self, name: str) -> t.Any:
        """Handle dynamic property access for components."""

        declcomps = getattr(self.__class__, '__declcomps__', set())

        # check if this is attribute has a declarable counterpart
        if name.lower() in declcomps:
            abstraction = f'_{name.lower()}'
            if hasattr(self, abstraction):
                if name.islower(): # return abstract class
                    return getattr(self, abstraction)
                elif name.isupper(): # return the actual raw object
                    component = getattr(self, abstraction)
                    if hasattr(component, '_obj'):
                        return component._obj
                    return component
            raise AttributeError(f"({self.__class__.__name__}:{name}) component not initialized ")

        # standard attribute error for non-component attributes
        raise AttributeError(f"({self.__class__.__name__}) has no attribute: {name}")
