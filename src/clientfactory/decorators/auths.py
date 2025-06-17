# ~/clientfactory/src/clientfactory/decorators/auths.py
"""
Authentication Decorators
------------------------
Decorators for transforming classes into authentication components.
"""
from __future__ import annotations
import typing as t, functools as fn

from clientfactory.core.bases import BaseAuth
from clientfactory.auths.jwt import JWTAuth
from clientfactory.auths.dpop import DPOPAuth

AT = t.TypeVar('AT', bound=BaseAuth)

def _transformtoauth(
    target: t.Type,
    variant: t.Type[AT],
    **kwargs: t.Any
) -> t.Type[AT]:
    """Transform a target class into the specified auth type."""
    classdict = {}
    for attrname in dir(target):
        if not attrname.startswith('__'):
            classdict[attrname] = getattr(target, attrname)

    classdict.update(kwargs)

    new = type(
        target.__name__,
        (variant,),
        classdict
    )
    new.__module__ = target.__module__
    new.__qualname__ = target.__qualname__
    return new

def baseauth(
    cls: t.Optional[t.Type] = None,
    **kwargs: t.Any
) -> t.Union[t.Type[BaseAuth], t.Callable[[t.Type], t.Type[BaseAuth]]]:
    """Transform a class into a BaseAuth component."""
    def decorator(target: t.Type) -> t.Type[BaseAuth]:
        return _transformtoauth(target, BaseAuth, **kwargs)
    if cls is not None:
        return decorator(cls)
    return decorator


def jwt(
    cls: t.Optional[t.Type] = None,
    *,
    token: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Union[t.Type[JWTAuth], t.Callable[[t.Type], t.Type[JWTAuth]]]:
    """Transform a class into a JWTAuth component."""
    def decorator(target: t.Type) -> t.Type[JWTAuth]:
        authkwargs = kwargs
        if token is not None:
            authkwargs['token'] = token
        return _transformtoauth(target, JWTAuth, **authkwargs)

    if cls is not None:
        return decorator(cls)
    return decorator


def dpop(
    cls: t.Optional[t.Type] = None,
    *,
    jwk: t.Optional[t.Dict[str, t.Any]] = None,
    algorithm: str  = "ES256",
    headerkey: str = "DPoP",
    **kwargs: t.Any
) -> t.Union[t.Type[DPOPAuth], t.Callable[[t.Type], t.Type[DPOPAuth]]]:
    """Transform a class into a DPOPAuth component."""
    def decorator(target: t.Type) -> t.Type[DPOPAuth]:
        authkwargs = {
            'algorithm': algorithm,
            'headerkey': headerkey,
            **kwargs
        }
        if jwk is not None:
            authkwargs['jwk'] = jwk
        return _transformtoauth(target, DPOPAuth, **authkwargs)

    if cls is not None:
        return decorator(cls)
    return decorator

# TODO:
# add @auth for BasicAuth when implemented
