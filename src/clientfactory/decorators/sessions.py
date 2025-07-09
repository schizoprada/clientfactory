# ~/clientfactory/src/clientfactory/decorators/sessions.py
"""
Session Decorators
-----------------
Decorators for transforming classes into session components.
"""
from __future__ import annotations
import typing as t, functools as fn

from clientfactory.core.bases import BaseSession
from clientfactory.core.session import Session
from clientfactory.decorators._utils import annotate, buildclassdict

ST = t.TypeVar('ST', bound=BaseSession)

def _transformtosession(
    target: t.Type,
    variant: t.Type[ST],
    **kwargs: t.Any
) -> t.Type[ST]:
    """Transform a target class into the specified session type."""
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
def basesession(cls: t.Type, /) -> t.Type[BaseSession]: ...

@t.overload
def basesession(cls: None = None, **kwargs: t.Any) -> t.Callable[[t.Type], t.Type[BaseSession]]: ...

def basesession(
    cls: t.Optional[t.Type] = None,
    **kwargs: t.Any
) -> t.Union[t.Type[BaseSession], t.Callable[[t.Type], t.Type[BaseSession]]]:
    """Transform a class into a BaseSession component."""
    def decorator(target: t.Type) -> t.Type[BaseSession]:
        return _transformtosession(target, BaseSession, **kwargs)
    if cls is not None:
        return decorator(cls)
    return decorator


## overloads ##
@t.overload
def session(cls: t.Type, /) -> t.Type[Session]: ...

@t.overload
def session(
    cls: None = None,
    *,
    auth: t.Optional[t.Any] = None,
    persistence: t.Optional[t.Any] = None,
    headers: t.Optional[t.Dict[str, str]] = None,
    cookies: t.Optional[t.Dict[str, str]] = None,
    useragent: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Callable[[t.Type], t.Type[Session]]: ...

def session(
    cls: t.Optional[t.Type] = None,
    *,
    auth: t.Optional[t.Any] = None,
    persistence: t.Optional[t.Any] = None,
    headers: t.Optional[t.Dict[str, str]] = None,
    cookies: t.Optional[t.Dict[str, str]] = None,
    useragent: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Union[t.Type[Session], t.Callable[[t.Type], t.Type[Session]]]:
    """Transform a class into a Session component."""
    def decorator(target: t.Type) -> t.Type[Session]:
        skwargs = kwargs
        for k,v in {'__auth__': auth, '__persistence__': persistence, 'headers': headers, 'cookies': cookies, 'useragent': useragent}.items():
            if v is not None:
                skwargs[k] = v
        return _transformtosession(target, Session, **skwargs)
    if cls is not None:
        return decorator(cls)
    return decorator
