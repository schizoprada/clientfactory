# ~/clientfactory/src/clientfactory/core/metas/declarative.py
"""
...
"""
from __future__ import annotations
import inspect, typing as t

from clientfactory.core.models import DeclarativeType, DECLARATIVE

class DeclarativeMeta(type):
    """
    Metaclass for declarative components.

    Handles automatic discovery of nested classes, methods, and attributes
    during class creation. Populates metadata dictionaries for runtime access.
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        # create class
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # initialize metadata storage
        setattr(cls, '_declmetadata', {})
        setattr(cls, '_declcomponents', {})
        setattr(cls, '_declmethods', {})

        # process class attributes and discover elements
        mcs._discovercomponents(cls, namespace)
        mcs._discovermethods(cls, namespace)
        mcs._inherit(cls, bases)

        return cls

    @classmethod
    def _discovercomponents(mcs, cls: type, namespace: dict) -> None:
        """Discover nested classes that should be treated as components."""
        for name, value in namespace.items():
            if inspect.isclass(value) and hasattr(value, '_decltype'):
                cls._declcomponents[name.lower()] = value
                value._parent = cls

    @classmethod
    def _discovermethods(mcs, cls: type, namespace: dict) -> None:
        """Discover methods marked with declarative metadata."""
        for name, value in namespace.items():
            if callable(value) and (not name.startswith("_")):
                methodinfo = {
                    'method': value,
                    'config': getattr(value, '_methodconfig', None)
                }
                cls._declmethods[name] = methodinfo

    @classmethod
    def _inherit(mcs, cls: type, bases: tuple) -> None:
        """Process metadata inheritance from parent classes."""
        for base in bases:
            if hasattr(base, '_declmetadata'):
                for k,v in base._declmetadata.items():
                    if k not in cls._declmetadata:
                        cls._declmetadata[k] = v
