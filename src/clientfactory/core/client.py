# ~/clientfactory/src/clientfactory/core/client.py
"""
Concrete Client Implementation
"""
from __future__ import annotations
import typing as t

from clientfactory.core.bases.client import BaseClient
from clientfactory.core.bases.resource import BaseResource


class Client(BaseClient):
    """Standard concrete client implementation"""

    def _initcomps(self) -> None:
        pass

    def _registerresource(self, resource: 'BaseResource', name: t.Optional[str] = None) -> None:
        rname = (name or resource.__class__.__name__.lower())
        self._resources[rname] = resource
        setattr(self, rname, resource)

    def _discoverresources(self) -> None:
        from clientfactory.core.resource import Resource

        self._discoveringresources = True # flag to prevent infinite recursion

        try:
            for attrname in dir(self.__class__):
                if attrname.startswith('_'):
                    continue

                attr = getattr(self.__class__, attrname)
                if (
                    isinstance(attr, type) and
                    issubclass(attr, Resource) and
                    attr is not Resource
                ):
                    config = getattr(attr, '_resourceconfig', None)
                    #print(f"DEBUG: Resource {attrname} config = {config}")
                    if config is None:
                        from clientfactory.core.models import ResourceConfig
                        config = ResourceConfig(
                            name=attrname.lower(),
                            path=attrname.lower() #! should provide some sort of flag to override this for an empty string path
                        )
                    instance = attr(
                        client=self,
                        config=config
                    )
                    self._registerresource(instance, attrname.lower())

        finally:
            # clean up flag
            if hasattr(self, '_discoveringresources'):
                delattr(self, '_discoveringresources')
