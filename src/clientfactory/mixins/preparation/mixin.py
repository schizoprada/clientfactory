# ~/clientfactory/src/clientfactory/mixins/preparation/mixin.py
"""
Preparation Mixin
----------------
Mixin to add request preparation capabilities to bound methods.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models import ExecutableRequest, MethodConfig, RequestModel
from clientfactory.mixins.preparation.comps import PrepConfig

if t.TYPE_CHECKING:
    from clientfactory.core.bases import BaseEngine, BaseClient, BaseBackend, BaseResource

class PrepMixin:
    """Mixin to add request preparation capabilities to bound methods."""

    def _getmethodconfig(self) -> MethodConfig:
        """Get method config from bound method."""
        if not hasattr(self, '_methodconfig'):
            raise AttributeError("prepare() can only be called on bound methods with method config")

        methodconfig: t.Optional[MethodConfig] = getattr(self, '_methodconfig', None)
        if methodconfig is None:
            raise ValueError("Method config is None")

        return methodconfig

    def _getengine(self) -> 'BaseEngine':
        """Get engine for request execution."""
        print(f"DEBUG: self type = {type(self)}")
        print(f"DEBUG: self attributes = {dir(self)}")

        # Check parent (could be client or resource)
        parent: t.Optional[t.Union['BaseClient', 'BaseResource']] = getattr(self, '_parent', None)
        print(f"DEBUG: _parent = {parent}")
        print(f"DEBUG: _parent type = {type(parent) if parent else None}")

        if parent is not None:
            # If parent is a client, get its engine
            if hasattr(parent, '_engine'):
                client: 'BaseClient' = parent  # type: ignore
                engine = getattr(client, '_engine', None)
                print(f"DEBUG: parent is client, engine = {engine}")
                if engine is not None:
                    return engine

            # If parent is a resource, get its client's engine
            if hasattr(parent, '_client'):
                resource: 'BaseResource' = parent  # type: ignore
                client_from_resource: t.Optional['BaseClient'] = getattr(resource, '_client', None)
                print(f"DEBUG: parent is resource, _client = {client_from_resource}")
                if client_from_resource is not None and hasattr(client_from_resource, '_engine'):
                    engine = getattr(client_from_resource, '_engine', None)
                    print(f"DEBUG: resource._client._engine = {engine}")
                    if engine is not None:
                        return engine

        # Fallback to original logic
        client: t.Optional['BaseClient'] = getattr(self, '_client', None)
        print(f"DEBUG: fallback _client = {client}")
        if client is not None:
            engine = getattr(client, '_engine', None)
            print(f"DEBUG: fallback client._engine = {engine}")
            if engine is not None:
                return engine

        engine: t.Optional['BaseEngine'] = getattr(self, '_engine', None)
        print(f"DEBUG: fallback direct _engine = {engine}")
        if engine is not None:
            return engine

        print(f"DEBUG: No engine found!")
        raise AttributeError("No engine available for request preparation")

    def _geturlparts(self, parent: t.Union['BaseClient', 'BaseResource']) -> tuple[str, t.Optional[str]]:
        if hasattr(parent, '_client'):
            baseurl = getattr(parent, 'baseurl', None) or parent._client.baseurl
            resourcepath = getattr(parent, 'path', None)
        else:
            baseurl = parent.baseurl
            resourcepath = None
        return baseurl, resourcepath # type: ignore

    def _preparerequest(self, methodconfig: MethodConfig, *args, **kwargs) -> RequestModel:
        """Build request for preparation (mirrors bound method logic)."""
        from clientfactory.core.utils.request import (
            resolveargs, substitute, buildrequest, applymethodconfig
        )

        parent: t.Optional[t.Union['BaseClient', 'BaseResource']] = getattr(self, '_parent', None)
        if parent is None: raise AttributeError("No parent available for request building")

        if methodconfig.preprocess: kwargs = methodconfig.preprocess(kwargs)

        kwargs = resolveargs(methodconfig.path, *args, **kwargs)
        path, consumed = substitute(methodconfig.path, **(kwargs or {}))

        for kwarg in consumed: kwargs.pop(kwarg, None)

        baseurl, resourcepath = self._geturlparts(parent)

        request = buildrequest(
            method=methodconfig.method,
            baseurl=baseurl,
            path=path,
            resourcepath=resourcepath,
            **(kwargs or {})
        )

        request =  applymethodconfig(request, methodconfig)

        backend: t.Optional['BaseBackend'] = getattr(parent, '_backend', None)
        if backend: request = backend.formatrequest(request, kwargs)

        return request


    def prepare(self, *args, **kwargs) -> ExecutableRequest:
        """
        Prepare request for later execution instead of executing immediately.

        Args:
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            ExecutableRequest: Request object that can be called later to execute
        """
        methodconfig = self._getmethodconfig()
        engine = self._getengine()
        request = self._preparerequest(methodconfig, *args, **kwargs)

        return ExecutableRequest(**request.model_dump(), engine=engine)
