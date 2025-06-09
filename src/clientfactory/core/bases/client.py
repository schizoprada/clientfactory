# ~/clientfactory/src/clientfactory/core/bases/client.py
"""
Base Client Implementation
-------------------------
Abstract base class for API clients.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import (
    ClientConfig, RequestModel, ResponseModel
)

from clientfactory.core.protos import (
    RequestEngineProtocol, SessionProtocol, BackendProtocol
)
from clientfactory.core.bases.engine import BaseEngine
from clientfactory.core.bases.auth import BaseAuth

if t.TYPE_CHECKING:
    from clientfactory.core.bases.resource import BaseResource


class BaseClient(abc.ABC):
    """
    Abstract base class for API clients.

    Handles resource discovery, configuration management, and provides
    the main interface for interacting with APIs.
    """
    def __init__(
        self,
        config: t.Optional[ClientConfig] = None,
        engine: t.Optional[BaseEngine] = None,
        backend: t.Optional[BackendProtocol] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize client with configuration and components."""
        from clientfactory.engines.requestslib import RequestsEngine
        self._config: ClientConfig = (config or ClientConfig(**kwargs))
        self._engine: BaseEngine = (engine or RequestsEngine()) #! handle config passing
        self._backend: t.Optional[BackendProtocol] = backend
        self._resources: t.Dict[str, 'BaseResource'] = {}
        self._closed: bool = False

        # initialize components
        self._initcomps()

        # discover resources
        self._discoverresources()


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
