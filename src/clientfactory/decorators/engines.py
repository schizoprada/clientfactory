# ~/clientfactory/src/clientfactory/decorators/engines.py
"""
Engine Decorators
-----------------
Decorators for creating declarative engine objects.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.bases import BaseEngine
from clientfactory.engines import EnginesMap, RequestsEngine

def _createengine(cls: t.Type, variant: t.Optional[str] = None) -> BaseEngine:
    """Helper to create engine objects from class attributes."""
    attrs = {
        k:v for k,v in cls.__dict__.items()
        if not k.startswith('_')
        and not callable(v)
    }

    if variant is None:
        return RequestsEngine(**attrs)

    if (engineclass:=EnginesMap.get(variant)):
        return engineclass(**attrs)

    raise NotImplementedError(f"{variant} engine not yet implemented")


class engine:
    """Engine decorator with library variants."""

    def __new__(cls, target: t.Type) -> BaseEngine:
        """Base engine decorator. Defaults to requests."""
        return _createengine(target)

    @staticmethod
    def requests(cls: t.Type) -> RequestsEngine: # type: ignore
        """Requests engine decorator."""
        return t.cast(RequestsEngine, _createengine(cls, 'requests'))
