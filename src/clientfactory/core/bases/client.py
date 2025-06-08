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
    RequestEngineProtocol, AuthProtocol, SessionProtocol
)
from clientfactory.engines.requests import RequestsEngine
from clientfactory.sessions.standard import StandardSession

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
        engine: t.Optional[RequestEngineProtocol] = None,
        auth: t.Optional[AuthProtocol] = None,
        session: t.Optional[SessionProtocol] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize client with configuration and components."""
        self._config: ClientConfig = (config or ClientConfig(**kwargs))
        self._engine: RequestEngineProtocol = (engine or RequestsEngine()) #! shouldnt we force a default here?
        self._auth: t.Optional[AuthProtocol] = auth
        self._session: SessionProtocol = (session or StandardSession()) #! shouldnt we force a default here?
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
        if self._session:
            self._session.close()
        elif self._engine:
            self._engine.close()
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
    def getconfig(self) -> ClientConfig:
        """Get client configuration."""
        return self._config

    def getengine(self) -> RequestEngineProtocol:
        """Get HTTP Engine"""
        return self._engine

    def getauth(self) -> t.Optional[AuthProtocol]:
        """Get authentication provider."""
        return self._auth

    def getsession(self) -> SessionProtocol:
        """Get session manager."""
        return self._session

    ## context management ##
    def __enter__(self) -> BaseClient:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
        """Exit context manager."""
        self.close()

    ## operator overloads ##
    #! implement later
