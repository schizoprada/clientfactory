# ~/clientfactory/src/clientfactory/core/metas/protocoled.py
"""
Protocol-Enforced Metaclass
---------------------------
Extends DeclarativeMeta with runtime protocol conformance checking.

Allows base classes to declare required protocols that concrete implementations
must conform to, providing both declarative discovery and interface enforcement.

Usage:
    class BaseAuth(abc.ABC, Declarative, metaclass=ProtocoledAbstractMeta):
        __protocols = {AuthProtocol}  # Framework-internal protocol enforcement
        __declcomps = set()           # Inherited declarative discovery

        @abc.abstractmethod
        def applyauth(self, request): ...

This ensures concrete auth implementations structurally conform to AuthProtocol
while maintaining all declarative component discovery capabilities.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.metas.declarative import DeclarativeMeta

class ProtocoledAbstractMeta(DeclarativeMeta):
    """Metaclass that adds protocol conformance checking to declarative classes."""

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace) # no kwargs

        protocols = getattr(cls, '__protocols', set())

        isabstract = lambda c: hasattr(c, '__abstractmethods__') and c.__abstractmethods__

        for protocol in protocols:
            if not isabstract(cls):
                # only check concrete classes
                if not isinstance(cls(), protocol):
                    raise TypeError(f"({name}) does not conform to protocol: {protocol.__name__}")

        return cls
