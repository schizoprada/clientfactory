# ~/clientfactory/src/clientfactory/core/utils/discover/binding.py
"""
Bound Method Creation Utilities
------------------------------
Universal bound method creation logic shared across clients and resources.
"""
from __future__ import annotations
import typing as t

from clientfactory.logs import log

if t.TYPE_CHECKING:
    from clientfactory.core.models.config import MethodConfig
    from clientfactory.core.models.methods import BoundMethod
    from clientfactory.core.bases import BaseEngine, BaseBackend, BaseResource, BaseClient, BaseSession

ParentType = t.Union['BaseClient', 'BaseResource']
EngineGetter = t.Callable[[ParentType], 'BaseEngine']
BackendGetter = t.Callable[[ParentType], t.Optional['BaseBackend']]


def createboundmethod(
    method: t.Callable,
    parent: ParentType,
    getengine: EngineGetter,
    getbackend: BackendGetter,
    baseurl: str,
    usesession: t.Union[bool, 'BaseSession'] = True,
    resourcepath: t.Optional[str] = None,
    validationstep: t.Optional[t.Callable] = None,
    pathoverride: t.Optional[str] = None,
    sessionmeta: t.Optional[dict] = None
) -> 'BoundMethod':
    """
    Create a bound method with unified request processing logic.

    Args:
        method: Original method with _methodconfig attribute
        parent: Parent client or resource instance
        getengine: Function to get engine from parent
        getbackend: Function to get backend from parent
        baseurl: Base URL for requests
        resourcepath: Resource path segment (None for clients)
        validationstep: Optional validation function (SearchResource)
        pathoverride: Path override (SearchResource uses "")

    Returns:
        BoundMethod instance with request processing capabilities

    Note:
        Consolidates the request pipeline: preprocess → path resolution →
        validation → substitution → building → config → backend → engine
    """
    from clientfactory.core.models import BoundMethod, RequestModel, ResponseModel
    from clientfactory.core.utils.request import (
        resolveargs, substitute, separatekwargs,
        buildrequest, applymethodconfig
    )

    methodconfig: 'MethodConfig' = getattr(method, '_methodconfig')

    def bound(*args, noexec: bool = False, **kwargs):
        if methodconfig.preprocess:
            kwargs = methodconfig.preprocess(kwargs)
        kwargs = resolveargs(methodconfig.path, *args, **kwargs)
        if validationstep:
            kwargs = validationstep(kwargs)
        targetpath = pathoverride if pathoverride is not None else methodconfig.path
        path, consumed = substitute(targetpath, **kwargs)

        for kwarg in consumed:
            kwargs.pop(kwarg, None)

        request = buildrequest(
            method=methodconfig.method,
            baseurl=baseurl,
            path=path,
            resourcepath=resourcepath,
            **kwargs
        )

        request = applymethodconfig(request, methodconfig)

        backend = getbackend(parent)
        if backend:
            request = backend.formatrequest(request, kwargs)

        engine = getengine(parent)
        session = engine._session # get session directly

        # extract and set session metadata
        if sessionmeta is not None:
            xsessionmeta = sessionmeta
            log.critical(f"(createboundmethod)@[{method.__name__}] using provided sessionmeta: {xsessionmeta}")
        else:
            from clientfactory.core.utils.session.meta import getsessionmeta
            xsessionmeta = getsessionmeta(method)
            log.critical(f"(createboundmethod)@[{method.__name__}] extracted sessionmeta: {xsessionmeta}")

        try:
            session._focusedmeta = xsessionmeta
            response = engine.send(request, noexec=noexec, usesession=usesession)
        finally:
            session._focusedmeta = None

        if isinstance(response, RequestModel):
            return response

        processed = response
        if backend:
            processed = backend.processresponse(response)

        if methodconfig.postprocess:
            processed = methodconfig.postprocess(processed)

        return processed

    bound.__name__ = method.__name__
    bound.__doc__ = method.__doc__
    setattr(bound, '_methodconfig', methodconfig)

    return BoundMethod(bound, parent, methodconfig)
