# ~/clientfactory/src/clientfactory/decorators/http.py
"""
HTTP Method decorators
"""
from __future__ import annotations
import typing as t, functools as fn

from clientfactory.core.models import HTTP, HTTPMethod, MethodConfig


def httpmethod(type: HTTPMethod, path: t.Optional[str] = None, **kwargs) -> t.Callable:
    def decorator(func: t.Callable):
        func._methodconfig = MethodConfig(
            name=func.__name__,
            method=type,
            path=path,
            preprocess=kwargs.get('preprocess'),
            postprocess=kwargs.get('postprocess'),
            payload=kwargs.get('payload'),
            description=kwargs.get('description', (func.__doc__ or ""))
        )
        return func
    return decorator


get, post, put, patch, delete, head, options = (fn.partial(httpmethod, mtype) for mtype in HTTP)
