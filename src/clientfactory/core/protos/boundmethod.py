# ~/clientfactory/src/clientfactory/core/protos/boundmethod.py
"""
...
"""
from __future__ import annotations
import typing as t


class BoundMethodProtocol(t.Protocol):
    """..."""

    def __call__(self, *args, **kwargs) -> t.Any: ...

    def cycle(self, *args, **kwargs) -> t.Any: ...

    def iterate(self, *args, **kwargs) -> t.Any: ...

    def prepare(self, *args, **kwargs) -> t.Any: ...
