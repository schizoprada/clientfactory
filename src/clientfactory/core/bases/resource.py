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
    HTTPMethod
)
from clientfactory.core.protos import (
    SessionProtocol, BackendProtocol, PayloadProtocol
)
from clientfactory.core.bases.session import BaseSession

if t.TYPE_CHECKING:
    from clientfactory.core.bases.client import BaseClient

class BaseResource(abc.ABC):
    """
    Abstract base class for API resources.

    Handles method discovery, URL construction, and request building.
    Resources represent logical groupings of related API endpoints.
    """

    def __init__(
        self,
        client: 'BaseClient',
        config: t.Optional[ResourceConfig] = None,
        session: t.Optional[BaseSession] = None,
        backend: t.Optional[BackendProtocol] = None,
        **kwargs: t.Any,
    ) -> None:
        """Initialize resource with client and configuration."""
        self._client: 'BaseClient' = client
        self._config: ResourceConfig = (config or ResourceConfig(**kwargs)) #! lets implement a helper method at somepoint to filter kwargs based on class trying to be instantiated
        self._session: BaseSession = (session or client._engine._session)
        self._backend: t.Optional[BackendProtocol] = (backend or client._backend)
        self._methods: t.Dict[str, t.Callable] = {}
        self._children: t.Dict[str, 'BaseResource'] = {}

        # initialize resources
        self._initmethods()
        self._initchildren()

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

    @abc.abstractmethod
    def _buildrequest(
        self,
        method: t.Union[str, HTTPMethod],
        path: t.Optional[str] = None,
        **kwargs: t.Any
    ) -> RequestModel:
        """
        Build request for resource method.

        Concrete resources implement request building logic.
        """
        ...

    ## concretes ##
    def addmethod(self, method: t.Callable, name: t.Optional[str] = None) -> None:
        """Add method to resource."""
        self._registermethod(method, name)

    def removemethod(self, name: str) -> None:
        """Remove method from resource."""
        if name in self._methods:
            del self._methods[name]
            if hasattr(self, name):
                delattr(self, name)

    def getmethod(self, name: str) -> t.Optional[t.Callable]:
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
    #! implement later
