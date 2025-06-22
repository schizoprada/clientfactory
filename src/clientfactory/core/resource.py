# ~/clientfactory/src/clientfactory/core/resource.py
"""
Concrete Resource Implementation
"""
from __future__ import annotations
import typing as t
from urllib.parse import urljoin

from clientfactory.core.bases import BaseResource
from clientfactory.core.models import (
    HTTPMethod, RequestModel, ResponseModel
)
from clientfactory.logs import log

if t.TYPE_CHECKING:
    from clientfactory.core.bases import BaseClient


class Resource(BaseResource):
    """Standard concrete resource implementation"""

    def _registermethod(self, method: t.Callable, name: t.Optional[str] = None) -> None:
        mname = (name or method.__name__)
        self._methods[mname] = method
        setattr(self, mname, method)

    def _registerchild(self, child: 'BaseResource', name: t.Optional[str] = None) -> None:
        cname = (name or child.__class__.__name__.lower())
        self._children[cname] = child
        setattr(self, cname, child)

    def _initmethods(self) -> None:
        for attrname in dir(self.__class__):
            if attrname.startswith('_'):
                continue

            attr = getattr(self.__class__, attrname)
            if callable(attr) and hasattr(attr, '_methodconfig'):
                bound = self._createboundmethod(attr)
                self._registermethod(bound, attrname)


    def _initchildren(self) -> None:
        # only discover children if this resource is directly defined in the client class
        # prevents infinite recursion when nested resources try to discover themselves

        if hasattr(self._client, '_discoveringresources'):
            #print("DEBUG _initchildren: Skipping due to _discoveringresources flag")
            return # skip, we're already in the resource discovery

        #print(f"DEBUG _initchildren: Starting discovery for {self.__class__.__name__}")
        #print(f"DEBUG _initchildren: dir(self.__class__) = {dir(self.__class__)}")

        for attrname in dir(self.__class__):
            if attrname.startswith('_'):
                continue

            #print(f"DEBUG _initchildren: Checking attribute '{attrname}'")
            attr = getattr(self.__class__, attrname)
            #print(f"DEBUG _initchildren: attr = {attr}")
            #print(f"DEBUG _initchildren: isinstance(attr, type) = {isinstance(attr, type)}")

            if isinstance(attr, type):
                pass
                #print(f"DEBUG _initchildren: issubclass(attr, Resource) = {issubclass(attr, Resource)}")
                #print(f"DEBUG _initchildren: attr is not Resource = {attr is not Resource}")

            if (
                isinstance(attr, type) and
                issubclass(attr, Resource) and
                attr is not Resource
            ):
                #print(f"DEBUG _initchildren: Found nested resource: {attrname}")
                child = attr(
                    client=self._client,
                    config=getattr(attr, '_resourceconfig', None)
                )
                self._registerchild(child, attrname.lower())
            else:
                #print(f"DEBUG _initchildren: Skipping {attrname} - not a Resource class")
                pass
        #print(f"DEBUG _initchildren: Final children: {self._children}")

    def _buildrequest(self, method: t.Union[str, HTTPMethod], path: t.Optional[str] = None, **kwargs: t.Any) -> RequestModel:
        if isinstance(method, str):
            method = HTTPMethod(method.upper())

        urlbase = self.baseurl if self.baseurl is not None else self._client.baseurl

        baseurl = urlbase.rstrip('/')
        resourcepath = self.path.strip('/') if self.path else ''
        methodpath = path.strip('/') if path else ''

        log.info(f"""
            Resource._buildrequest:
                baseurl = {baseurl}
                resourcepath = {resourcepath}
                methodpath = {methodpath}
            """)

        parts = [baseurl]
        if resourcepath:
            parts.append(resourcepath)
        if methodpath:
            parts.append(methodpath)

        url = '/'.join(parts)

        log.info(f"Resource._buildrequest: url = {url}")

        fields, body = self._separatekwargs(method, **kwargs)

        if body:
            return RequestModel(
                method=method,
                url=url,
                json=body,
                **fields
            )

        return RequestModel(
            method=method,
            url=url,
            **fields
        )
