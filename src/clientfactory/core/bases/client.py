# ~/clientfactory/src/clientfactory/core/bases/client.py
"""
Base Client Implementation
-------------------------
Abstract base class for API clients.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import (
    ClientConfig, RequestModel, ResponseModel,
    HTTPMethod, MethodConfig, MergeMode
)

from clientfactory.core.protos import (
    RequestEngineProtocol, SessionProtocol, BackendProtocol
)
from clientfactory.core.bases.engine import BaseEngine
from clientfactory.core.bases.auth import BaseAuth
from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.metas.protocoled import ProtocoledAbstractMeta

if t.TYPE_CHECKING:
    from clientfactory.core.bases.resource import BaseResource
    from clientfactory.core.models.methods import BoundMethod

class BaseClient(abc.ABC, Declarative):
    """
    Abstract base class for API clients.

    Handles resource discovery, configuration management, and provides
    the main interface for interacting with APIs.
    """
    __declcomps__: set = {'auth', 'persistence', 'session', 'engine', 'backend'}
    __declattrs__: set = {'baseurl', 'version', 'name', 'description'}
    __declconfs__: set = {'timeout', 'verifyssl', 'allowredirects', 'cascade'}

    def __init__(
        self,
        config: t.Optional[ClientConfig] = None,
        engine: t.Optional[BaseEngine] = None,
        backend: t.Optional[BackendProtocol] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize client with configuration and components."""
        from clientfactory.engines.requestslib import RequestsEngine

        # 1. resolve components
        components = self._resolvecomponents(engine=engine, backend=backend)
        self._engine: BaseEngine = (components['engine'] or RequestsEngine())
        self._backend: t.Optional[BackendProtocol] = components['backend']

        # 2. resolve config
        self._config: ClientConfig = self._resolveconfig(ClientConfig, config, **kwargs)

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)

        self._resources: t.Dict[str, 'BaseResource'] = {}
        self._closed: bool = False

        # initialize components
        self._initcomps()

        # initialize methods
        self._initmethods()

        # discover resources
        self._discoverresources()


    def _resolveattributes(self, attributes: dict) -> None:
        self.baseurl: str = attributes.get('baseurl', '')
        self._version: str = attributes.get('version', '1.0.0')
        self._name = attributes.get('name', self.__class__.__name__.lower())


    ## abstracts ##
    @abc.abstractmethod
    def _initcomps(self) -> None:
        """
        Initialize client components.

        Concrete clients implement component setup logic.
        """
        ...

    @abc.abstractmethod
    def _registerresource(self, resource: 'BaseResource', name: t.Optional[str] = None) -> None:
        """
        Register a single resource.

        Called by _discoverresources for each found resource.
        """
        ...

    @abc.abstractmethod
    def _discoverresources(self) -> None:
        """
        Discover and register resources.

        Concrete clients implement resource discovery logic.
        """
        ...

    ## lifecycle ##
    def _checknotclosed(self) -> None:
        """Check if client is still open."""
        if self._closed:
            raise RuntimeError("Client is closed")

    def close(self) -> None:
        """Close client and cleanup resources."""
        #!
        self._closed = True

    ## concretes ##

    def _createboundmethod(self, method: t.Callable) -> 'BoundMethod':
        from clientfactory.core.utils.discover import createboundmethod
        getengine = lambda p: p._engine
        getbackend = lambda p: p._backend
        return createboundmethod(
            method=method,
            parent=self,
            getengine=getengine,
            getbackend=getbackend, # type: ignore
            baseurl=self.baseurl,
            resourcepath=None
        )

    def _initmethods(self) -> None:
        """Initialize client-level HTTP methods."""
        from clientfactory.core.models.methods import BoundMethod
        for attrname in dir(self.__class__):
            if attrname.startswith('_'):
                continue

            attr = getattr(self.__class__, attrname)

            # handle pre-bound methods from decorators
            if isinstance(attr, BoundMethod):
                if not attr._resolved:
                    attr._resolvebinding(self)
                setattr(self, attrname, attr)
                continue

            # Legacy: undecorated methods with _methodconfig
            if (attr and callable(attr) and hasattr(attr, '_methodconfig')):
                bound = self._createboundmethod(attr)
                setattr(self, attrname, bound)

    def getresource(self, name: str) -> t.Optional['BaseResource']:
        """Get resource by name."""
        return self._resources.get(name)

    def addresource(self, resource: 'BaseResource', name: t.Optional[str] = None) -> None:
        """Add resource to client."""
        self._registerresource(resource, name)

    def removeresource(self, name: str) -> None:
        """Remove resource from client."""
        if name in self._resources:
            del self._resources[name]
            if hasattr(self, name):
                delattr(self, name)

    def listresources(self) -> t.List[str]:
        """List all registered resource names."""
        return list(self._resources.keys())

    ## component access ##
    #! to be reimplemented

    ## context management ##
    def __enter__(self) -> BaseClient:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
        """Exit context manager."""
        self.close()



    ## operator overloads ##
    #! implement later

    @classmethod
    def _compose(cls, other: t.Any) -> t.Any:
        raise NotImplementedError()
