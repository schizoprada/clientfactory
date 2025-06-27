# ~/clientfactory/src/clientfactory/core/resource.py
"""
Concrete Resource Implementation
"""
from __future__ import annotations
import typing as t
from urllib.parse import urljoin

from clientfactory.core.bases import BaseResource
from clientfactory.core.models import (
    HTTPMethod, RequestModel, ResponseModel, Payload
)
from clientfactory.logs import log

if t.TYPE_CHECKING:
    from clientfactory.core.bases import BaseClient


class Resource(BaseResource):
    """Standard concrete resource implementation"""

    def _getpayloadinstance(self) -> t.Optional[Payload]:
        """Get payload instance if any."""
        payload = getattr(self, 'payload', None)
        if payload is None:
            return None
        if isinstance(payload, type):
            return payload()
        return payload

    def _registermethod(self, method: t.Callable, name: t.Optional[str] = None) -> None:
        mname = (name or method.__name__)
        self._methods[mname] = method
        setattr(self, mname, method)

    def _registerchild(self, child: 'BaseResource', name: t.Optional[str] = None) -> None:
        cname = (name or child.__class__.__name__.lower())
        self._children[cname] = child
        setattr(self, cname, child)

    def _initmethods(self) -> None:
        from clientfactory.core.models.methods import BoundMethod
        for attrname in dir(self.__class__):
            if attrname.startswith('_'):
                continue

            attr = getattr(self.__class__, attrname)

            if isinstance(attr, BoundMethod):
                if not attr._resolved:
                    attr._resolvebinding(self)
                setattr(self, attrname, attr)
                continue

            if callable(attr) and hasattr(attr, '_methodconfig'):
                bound = self._createboundmethod(attr)
                self._registermethod(bound, attrname)


    def _initchildren(self) -> None:
        # only discover children if this resource is directly defined in the client class
        # prevents infinite recursion when nested resources try to discover themselves

        if hasattr(self._client, '_discoveringresources'):
            return # skip, we're already in the resource discovery

        for attrname in dir(self.__class__):
            if attrname.startswith('_'):
                continue

            attr = getattr(self.__class__, attrname)


            if (
                isinstance(attr, type) and
                issubclass(attr, Resource) and
                attr is not Resource
            ):
                child = attr(
                    client=self._client,
                    config=getattr(attr, '_resourceconfig', None)
                )
                self._registerchild(child, attrname.lower())
