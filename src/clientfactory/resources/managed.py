# ~/clientfactory/src/clientfactory/resources/managed.py
"""
Managed Resource Implementation
------------------------------
Specialized resource for CRUD operations with standardized methods.
"""
from __future__ import annotations
import typing as t


from clientfactory.utils import crud
from clientfactory.core.bases import BaseResource
from clientfactory.core.resource import Resource
from clientfactory.core.models import (
    Payload, RequestModel,
    HTTPMethod, MethodConfig
)
from clientfactory.core.models.methods import BoundMethod

class ManagedResource(Resource):
    """
    Resource specialized for CRUD operations.

    Provides automatic generation of standard CRUD methods based on
    declarative configuration.
    """
    __declaredas__: str = "managedresource"
    __declattrs__: set[str] = BaseResource.__declattrs__ | {'crud'}

    # declarative CRUD
    __crud__: t.Optional[set[str]] = None

    def _resolveattributes(self, attributes: dict) -> None:
        """Resolve managed resource attributes."""
        super()._resolveattributes(attributes)
        self.crud = attributes.get('crud', set())


    def _initmethods(self) -> None:
        """Initialize methods, including auto-generated CRUD methods."""
        super()._initmethods()

        # auto-generate if __crud__ defined
        crudset = getattr(self.__class__, '__crud__', None)
        if crudset:
            self._generatecrudmethods(crudset)

    def _generatecrudmethods(self, operations: set[str]) -> None:
        """Generate standard CRUD methods."""
        #! TODO:
        ## Figure out how to properly allow CRUD method MethodConfig configuration

        generators: dict[str, t.Callable] = {
            'create': crud.create,
            'read': crud.read,
            'update': crud.update,
            'delete': crud.delete,
            'list': crud.list
        }

        for op in operations:
            if (op in generators) and (op not in self._methods):
                methodconfig = generators[op]()

                # dummy method to bind config to
                def _(): pass
                _._methodconfig = methodconfig

                boundmethod = self._createboundmethod(_)
                self._registermethod(boundmethod, op)
