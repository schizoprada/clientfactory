# ~/clientfactory/src/clientfactory/utils/crud.py
"""
Convenience methods for generating CRUD MethodConfigs
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models import (
    Payload, RequestModel, SearchResourceConfig,
    HTTPMethod, MethodConfig
)

class crud:
    @staticmethod
    def method(
        name: str,
        method: HTTPMethod,
        path: str = "",
        payload: t.Optional[Payload] = None,
        **kwargs
    ) -> MethodConfig:
        return MethodConfig(name=name, method=method, path=path, payload=payload, **kwargs)

    @classmethod
    def create(cls, name: str = "create", path: str = "", payload: t.Optional[Payload] = None, **kwargs) -> MethodConfig:
        return cls.method(name, HTTPMethod.POST, path, payload, **kwargs)

    @classmethod
    def read(cls, name: str = "read", path: str = "{id}", payload: t.Optional[Payload] = None, **kwargs) -> MethodConfig:
        return cls.method(name, HTTPMethod.GET, path, payload, **kwargs)

    @classmethod
    def update(cls, name: str = "update", path: str = "{id}", payload: t.Optional[Payload] = None, **kwargs) -> MethodConfig:
        return cls.method(name, HTTPMethod.PUT, path, payload, **kwargs)

    @classmethod
    def delete(cls, name: str = "delete", path: str = "{id}", payload: t.Optional[Payload] = None, **kwargs) -> MethodConfig:
        return cls.method(name, HTTPMethod.DELETE, path, payload, **kwargs)

    @classmethod
    def list(cls, name: str = "list", path: str = "", payload: t.Optional[Payload] = None, **kwargs) -> MethodConfig:
        return cls.method(name, HTTPMethod.GET, path, payload, **kwargs)
