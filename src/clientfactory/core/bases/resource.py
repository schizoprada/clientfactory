# ~/clientfactory/src/clientfactory/core/bases/resource.py
"""
Base Resource Implementation
---------------------------
Abstract base class for API resources.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import (
    ResourceConfig, RequestModel, ResponseModel,
    HTTPMethod, MethodConfig, MergeMode
)
from clientfactory.core.protos import (
    SessionProtocol, BackendProtocol, PayloadProtocol
)
from clientfactory.core.bases.session import BaseSession
from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.metas.protocoled import ProtocoledAbstractMeta


if t.TYPE_CHECKING:
    from clientfactory.core.bases.client import BaseClient
    from clientfactory.core.models.methods import BoundMethod

class BaseResource(abc.ABC, Declarative):
    """
    Abstract base class for API resources.

    Handles method discovery, URL construction, and request building.
    Resources represent logical groupings of related API endpoints.
    """
    __declaredas__: str = 'resource'
    __declcomps__: set = {'auth', 'backend', 'persistence', 'session'}
    __declattrs__: set = {'path', 'name', 'description', 'tags', 'standalone', 'baseurl'}
    __declconfs__: set = {'timeout', 'retries'}

    def __init__(
        self,
        client: 'BaseClient',
        config: t.Optional[ResourceConfig] = None,
        session: t.Optional[BaseSession] = None,
        backend: t.Optional[BackendProtocol] = None,
        **kwargs: t.Any,
    ) -> None:
        """Initialize resource with client and configuration."""
        # 1. resolve components
        components = self._resolvecomponents(session=session, backend=backend)
        self._session: BaseSession = (components['session'] or client._engine._session)
        self._backend: t.Optional[BackendProtocol] = (components['backend'] or client._backend)

        # 2. resolve config
        self._config: ResourceConfig = self._resolveconfig(ResourceConfig, config, **kwargs)

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)

        self._client: 'BaseClient' = client
        self._methods: t.Dict[str, t.Callable] = {}
        self._children: t.Dict[str, 'BaseResource'] = {}

        # initialize resources
        self._initmethods()
        self._initchildren()

    def _resolveattributes(self, attributes: dict) -> None:
        self.path: str = attributes.get('path', '')
        self.name: str = attributes.get('name', '')
        self.description: str = attributes.get('description', '')
        self.baseurl: t.Optional[str] = attributes.get('baseurl')
        self.standalone: bool = attributes.get('standalone', False)

    ## abstracts ##
    @abc.abstractmethod
    def _registermethod(self, method: t.Callable, name: t.Optional[str] = None) -> None:
        """
        Register a single method with the resource.

        Called by addmethod and _initmethods for each discovered method.
        Concrete resources implement method registration logic.

        Args:
            method: Callable method to register
            name: Optional name override (defaults to method.__name__)
        """
        ...

    @abc.abstractmethod
    def _registerchild(self, child: 'BaseResource', name: t.Optional[str] = None) -> None:
        """
        Register a single child resource.

        Called by addchild and _initchildren for each discovered child.
        Concrete resources implement child registration logic.

        Args:
            child: Child resource to register
            name: Optional name override (defaults to child.__class__.__name__.lower())
        """
        ...

    @abc.abstractmethod
    def _initmethods(self) -> None:
        """
        Initialize resource methods.

        Concrete resources implement method discovery logic.
        """
        ...

    @abc.abstractmethod
    def _initchildren(self) -> None:
        """
        Initialize child resources.

        Concrete resources implement child resource logic.
        """
        ...


    ## concretes ##

    def _createboundmethod(self, method: t.Callable) -> 'BoundMethod':
        from clientfactory.core.utils.discover import createboundmethod
        getengine = lambda p: p._client._engine
        getbackend = lambda p: p._backend
        baseurl = self.baseurl if self.baseurl is not None else self._client.baseurl
        return createboundmethod(
            method=method,
            parent=self,
            getengine=getengine,
            getbackend=getbackend,
            baseurl=baseurl,
            resourcepath=self.path
        )

    def addmethod(self, method: t.Callable, name: t.Optional[str] = None) -> None:
        """Add method to resource."""
        self._registermethod(method, name)

    def removemethod(self, name: str) -> None:
        """Remove method from resource."""
        if name in self._methods:
            del self._methods[name]
            if hasattr(self, name):
                delattr(self, name)

    def getmethod(self, name: str) -> t.Optional[t.Callable]: # type: ignore
        """Get method by name."""
        return self._methods.get(name)

    def listmethods(self) -> t.List[str]:
        """List all registered method names."""
        return list(self._methods.keys())

    def addchild(self, child: 'BaseResource', name: t.Optional[str] = None) -> None:
        """Add child resource."""
        self._registerchild(child, name)

    def removechild(self, name: str) -> None:
        """Remove child resource."""
        if name in self._children:
            del self._children[name]
            if hasattr(self, name):
                delattr(self, name)

    def getchild(self, name: str) -> t.Optional['BaseResource']:
        """Get child resource by name."""
        return self._children.get(name)

    def listchildren(self) -> t.List[str]:
        """List all child resource names."""
        return list(self._children.keys())

   ## component access ##
    def getclient(self) -> 'BaseClient':
        """Get parent client."""
        return self._client

    def getconfig(self) -> ResourceConfig:
        """Get resource configuration."""
        return self._config

    def getsession(self) -> SessionProtocol:
        """Get session manager."""
        return self._session

    # no properties, Resources should be declarative

    ## operator overloads ##
    @classmethod
    def _compose(cls, other: t.Union['BaseResource', t.Type['BaseResource']]) -> t.Type['BaseResource']:
        """Create a new composed resource class."""
        othercls = other if isinstance(other, type) else type(other)

        name = f"({cls.__name__})&({othercls.__name__})"
        # Use the metaclass instead of type() to preserve metaclass behavior
        metaclass = type(cls)

        composed = metaclass(name, (cls, othercls), {
            "__module__": cls.__module__,
            "__qualname__": f"({cls.__qualname__})&({othercls.__qualname__})"
        })
        return composed
