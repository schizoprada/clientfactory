# ~/clientfactory/src/clientfactory/decorators/persistences.py
"""
Persistence Decorators
----------------------
Decorators for creating declarative persistence objects.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.bases import BasePersistence
from clientfactory.core.persistence import Persistence



def _createpersistence(cls: t.Type, fmt: t.Optional[str] = None) -> Persistence:
    """Helper to create persistence objects from class attributes."""
    attrs = {
        k:v for k,v in cls.__dict__.items()
        if not k.startswith('_')
        and not callable(v)
    }

    if fmt:
        attrs['format'] = fmt

    # For now, always return the JSON Persistence class
    # TODO: Add other persistence classes as they're implemented
    return Persistence(**attrs)

class persistence:
    """Persistence decorator with format variants."""

    def __new__(cls, target: t.Type) -> Persistence:
        """Base persistence decorator."""
        return _createpersistence(target)

    @staticmethod
    def json(cls: t.Type) -> Persistence: #type: ignore
        """JSON persistence decorator."""
        return _createpersistence(cls, 'json')

    @staticmethod
    def pkl(cls: t.Type) -> BasePersistence: #type: ignore
        """Pickle persistence decorator (not implemented yet)."""
        raise NotImplementedError("Pickle persistence not yet implemented")
