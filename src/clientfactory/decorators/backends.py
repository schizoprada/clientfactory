# ~/clientfactory/src/clientfactory/decorators/backends.py
"""
Backend Decorators
-----------------
Decorators for transforming classes into backend components.
"""
from __future__ import annotations
import typing as t, functools as fn

from clientfactory.core.bases import BaseBackend
from clientfactory.backends.algolia import AlgoliaBackend
from clientfactory.backends.graphql import GQLBackend
from clientfactory.decorators._utils import annotate, buildclassdict

BT = t.TypeVar('BT', bound=BaseBackend)


def _transformtobackend(
    target: t.Type,
    variant: t.Type[BT],
    **kwargs: t.Any
) -> t.Type[BT]:
    """Transform a target class into the specified backend type."""
    comps = {f'__{comp}__' for comp in (variant.__declcomps__ | getattr(target, '__declcomps__', set()))}
    classdict = buildclassdict(target, dunders=comps)
    classdict.update(kwargs)

    new = type(
        target.__name__,
        (variant,),
        classdict
    )
    new.__module__ = target.__module__
    new.__qualname__ = target.__qualname__
    annotate(new, variant)
    return new # type: ignore


## overloads ##
@t.overload
def basebackend(cls: t.Type, /) -> t.Type[BaseBackend]: ...

@t.overload
def basebackend(
    cls: None = None,
    **kwargs: t.Any
) -> t.Callable[[t.Type], t.Type[BaseBackend]]:...

def basebackend(
    cls: t.Optional[t.Type] = None,
    **kwargs: t.Any
) -> t.Union[t.Type[BaseBackend], t.Callable[[t.Type], t.Type[BaseBackend]]]:
    """Transform class into BaseBackend component."""
    def decorator(target: t.Type) -> t.Type[BaseBackend]:
        return _transformtobackend(target, BaseBackend, **kwargs)
    if cls is not None:
        return decorator(cls)
    return decorator



## overloads ##
@t.overload
def algolia(cls: t.Type, /) -> t.Type[AlgoliaBackend]: ...

@t.overload
def algolia(
    *,
    appid: t.Optional[str] = None,
    apikey: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Callable[[t.Type], t.Type[AlgoliaBackend]]: ...

def algolia(
    cls: t.Optional[t.Type] = None,
    *,
    appid: t.Optional[str] = None,
    apikey: t.Optional[str] = None,
    index: t.Optional[str] = None,
    indices: t.Optional[t.List[str]] = None,
    **kwargs: t.Any
) -> t.Union[t.Type[AlgoliaBackend], t.Callable[[t.Type], t.Type[AlgoliaBackend]]]:
    """Transform class into AlgoliaBackend component."""
    def decorator(target: t.Type) -> t.Type[AlgoliaBackend]:
        bkwargs = kwargs
        for k,v in {'appid': appid, 'apikey': apikey, 'index': index, 'indices': indices}.items():
            if v is not None:
                bkwargs[k] = v
        return _transformtobackend(target, AlgoliaBackend, **bkwargs)
    if cls is not None:
        return decorator(cls)
    return decorator


## overloads ##
@t.overload
def graphql(cls: t.Type, /) -> t.Type[GQLBackend]: ...

@t.overload
def graphql(
    *,
    endpoint: str = "/graphql",
    introspection: bool = True,
    **kwargs: t.Any
) -> t.Callable[[t.Type], t.Type[GQLBackend]]: ...

def graphql(
    cls: t.Optional[t.Type] = None,
    *,
    endpoint: str = "/graphql",
    introspection: bool = True,
    maxdepth: int = 10,
    **kwargs
) -> t.Union[t.Type[GQLBackend], t.Callable[[t.Type], t.Type[GQLBackend]]]:
    """Transform class into GQLBackend component."""
    def decorator(target: t.Type) -> t.Type[GQLBackend]:
        bkwargs = {
            'endpoint': endpoint,
            'introspection': introspection,
            'maxdepth': maxdepth,
            **kwargs
        }
        return _transformtobackend(target, GQLBackend, **bkwargs)
    if cls is not None:
        return decorator(cls)
    return decorator
