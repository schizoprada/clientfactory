# ~/clientfactory/src/clientfactory/core/protos/requestengine.py
"""
Request Engine Protocol
"""
from __future__ import annotations
import typing as t



@t.runtime_checkable
class RequestEngineProtocol(t.Protocol):
    """
    Protocol to identify all potential request engines
    Default library used will be `requests`
    """

    def get(self, *args, **kwargs):
        ...

    def post(self, *args, **kwargs):
        ...

    def put(self, *args, **kwargs):
        ...

    def patch(self, *args, **kwargs):
        ...

    def delete(self, *args, **kwargs):
        ...

    def head(self, *args, **kwargs):
        ...

    def options(self, *args, **kwargs):
        ...
