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

from clientfactory.logs import log

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

    def _collectattributes(self, attrmap: t.Optional[dict] = None, **provided: t.Any) -> dict:
        """Collect attributes from declarations and provided values."""
        declarable: set = getattr(self.__class__, '__declattrs__', set())
        declared: dict = getattr(self.__class__, '_declattrs', {})
        collected: dict = {}
        mappedattrs: dict = (attrmap or {})
        #print(f"DEBUG _collectattributes: declarable = {declarable}")
        #print(f"DEBUG _collectattributes: declared = {declared}")
        #print(f"DEBUG _collectattributes: provided = {provided}")


        # get config defaults if available
        defaults = {}
        if hasattr(self, '_config'):
            defaults = self._config.model_dump()


        # helper lambda
        ismapped = lambda name, mapping: (name in mappedattrs) and (mappedattrs[name] in mapping)

        for name in declarable:
            if (name in provided):
                collected[name] = provided[name]
            elif name in declared:
                collected[name] = declared[name]
            elif hasattr(self.__class__, name):
                collected[name] = getattr(self.__class__, name)
            elif name in defaults:
                collected[name] = defaults[name]
            else:
                collected[name] = None

        return collected
        #! TODO: implement `attrmap` kwarg for name-value check mapping

    def _resolvecomponents(self, **provided: t.Any) -> dict:
        """Resolve components from declarations and constructor params."""
        from clientfactory.logs import log

        declarable: set = getattr(self.__class__, '__declcomps__', set())
        log.debug(f"Declarative._resolvecomponents: declarable={declarable}")
        log.debug(f"Declarative._resolvecomponents: provided={provided}")
        log.debug(f"Declarative._resolvecomponents: class={self.__class__.__name__}")

        declcomps = getattr(self.__class__, '_declcomponents', {})
        log.debug(f"Declarative._resolvecomponents: _declcomponents={declcomps}")

        # collect declarations from component hierarchy
        declared: dict = {}
        current = self
        traversed = []
        while current:
            traversed.append(current.__class__.__name__)
            currentdeclared = getattr(current.__class__, '_declcomponents', {})
            log.debug(f"Declarative._resolvecomponents: {current.__class__.__name__} _declcomponents={currentdeclared}")
            for name, decl in currentdeclared.items():
                if name not in declared:
                    declared[name] = decl
                    log.debug(f"Declarative._resolvecomponents: added {name} = {decl}")

            # move up hierarchy
            old = current
            current = getattr(current, '_parent', None) or getattr(current, '_client', None)
            log.debug(f"Declarative._resolvecomponents: moved from {old.__class__.__name__} to {current.__class__.__name__ if current else None}")

            if current is old:
                break

        log.debug(f"Declarative._resolvecomponents: traversed={traversed}")
        log.debug(f"Declarative._resolvecomponents: final declared={declared}")

        resolved: dict = {}
        for name in declarable:
            log.debug(f"Declarative._resolvecomponents: resolving {name}")
            if (name in provided) and (provided[name] is not None):
                resolved[name] = provided[name]
                log.debug(f"Declarative._resolvecomponents: {name} from provided = {resolved[name]}")
            elif (name in declared):
                declaration = declared[name]
                log.debug(f"Declarative._resolvecomponents: {name} from declared = {declaration}")
                if (declaration['type'] == 'class'):
                    resolved[name] = declaration['value']() # needs insantiation
                    log.debug(f"Declarative._resolvecomponents: instantiated {name} = {resolved[name]}")
                else:
                    resolved[name] = declaration['value'] # already instantiated
                    log.debug(f"Declarative._resolvecomponents: used instance {name} = {resolved[name]}")
            else:
                resolved[name] = None
                log.debug(f"Declarative._resolvecomponents: {name} = None (not found)")

        log.debug(f"Declarative._resolvecomponents: final resolved={resolved}")
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

    def _findcomponent(self, name: str) -> t.Any:
        """Traverse component hierarchy to find component."""
        #print(f"DEBUG: Looking for _{name} in {self.__class__.__name__}")
        #print(f"DEBUG: self.__dict__ keys: {list(self.__dict__.keys())}")
        abstraction = f'_{name}'
        # direct
        if abstraction in self.__dict__:
            #print(f"DEBUG: Found {abstraction} directly")
            return self.__dict__[abstraction]

        # check child components
        declcomps = getattr(self.__class__, '__declcomps__', set())
        #print(f"DEBUG: Checking children in declared components: {declcomps}")
        for comp in declcomps:
            childattr = f'_{comp}'
            if childattr in self.__dict__:
                child = self.__dict__[childattr]
                #print(f"DEBUG: found child ({childattr}): {child}")
                if child and hasattr(child, abstraction):
                    #print(f"DEBUG: Child ({childattr}) has {abstraction}")
                    result =  getattr(child, abstraction)
                    #print(f"DEBUG: getattr returned: {result}")
                    return result
                elif child and hasattr(child, '_findcomponent'):
                    #print(f"DEBUG: Recursing into {childattr}")
                    found = child._findcomponent(name)
                    if found:
                        return found
        #print(f"DEBUG: Could not find: {abstraction}")
        return None

    def __getattr__(self, name: str) -> t.Any:
        """Handle dynamic property access for components."""

        declcomps = getattr(self.__class__, '__declcomps__', set())

        # check if this is attribute has a declarable counterpart
        if name.lower() in declcomps:
            component = self._findcomponent(name.lower())
            if component is not None:
                if name.islower():
                    return component
                elif name.isupper():
                    if hasattr(component, '_obj'):
                        return component._obj
                    return component
            raise AttributeError(f"({self.__class__.__name__}:{name}) component not initialized ")

        # standard attribute error for non-component attributes
        raise AttributeError(f"({self.__class__.__name__}) has no attribute: {name}")



    @classmethod
    @abc.abstractmethod
    def _compose(cls, other: t.Any) -> t.Any:
        """Create a new composed class. Must be implemented by subclasses."""

    @classmethod
    def _checkcomposable(cls, other: t.Any) -> None:
        if not hasattr(other, '_compose'):
            raise ValueError()

    @classmethod
    def __and__(cls, other: t.Any) -> t.Any:
        cls._checkcomposable(other)
        return cls._compose(other)

    @classmethod
    def __rand__(cls, other: t.Any) -> t.Any:
        cls._checkcomposable(other)
        return other._compose(cls)
