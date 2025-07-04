# ~/clientfactory/src/clientfactory/mixins/preparation/mixin.py
"""
Preparation Mixin
----------------
Mixin to add request preparation capabilities to bound methods.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models import ExecutableRequest, MethodConfig, RequestModel
from clientfactory.mixins.core import BaseMixin, MixinMetadata
from clientfactory.mixins.core.comps import PREPARE
from clientfactory.mixins.preparation.comps import PrepConfig


if t.TYPE_CHECKING:
    from clientfactory.core.bases import BaseEngine, BaseClient, BaseBackend, BaseResource

class PrepMixin(BaseMixin):
    """Mixin to add request preparation capabilities to bound methods."""
    __mixmeta__ = MixinMetadata(
        mode=PREPARE,
        terminal=True,
        priority=10
    )
    __chainedas__: str = 'prep'

    def _exec_(self, conf: t.Dict[str, t.Any], **kwargs) -> ExecutableRequest:
        """Execute preparation with merged config"""
        params = {**conf, **kwargs}
        mconf = self._getmethodconfig()
        engine = self._getengine()
        request = self._preparerequest(mconf, **params)

        return ExecutableRequest(
            **request.model_dump(),
            engine=engine
        )

    def _configure_(self, **kwargs) -> t.Dict[str, t.Any]:
        """Prepare and validate configuration for preparation"""
        # just return kwargs for now, could add validation later or whatever
        return kwargs



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
        #methodconfig = self._getmethodconfig()
        engine = self._getengine()
        request = self._func(*args, noexec=True, **kwargs)


        return ExecutableRequest(**request.model_dump(), engine=engine)
