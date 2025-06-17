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
    HTTPMethod
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
    def _substitutepath(self, path: t.Optional[str] = None, **kwargs) -> tuple[t.Optional[str], t.List[str]]:
        """Substitute path parameters using string formatting."""
        if not path:
            return path, []

        import string
        formatter = string.Formatter()

        try:
            consumed = [fname for _, fname, _, _ in formatter.parse(path) if fname]
            return path.format(**kwargs), consumed
        except KeyError as e:
            raise ValueError(f"Missing path parameter: {e}")

    def _separatekwargs(self, method: HTTPMethod, **kwargs) -> tuple[dict, dict]:
        """Separate kwargs into request fields and body data based on HTTP method."""
        fields = {}
        body = {}

        fieldnames = {
            'headers', 'params', 'cookies', 'timeout',
            'allowredirects', 'verifyssl', 'data', 'files'
        }
        bodymethods = {'POST', 'PUT', 'PATCH'}

        if method.value in bodymethods:
            for k,v in kwargs.items():
                if k in fieldnames:
                    fields[k] = v
                else:
                    body[k] = v
        else:
            fields = kwargs

        return (fields, body)

    def _buildrequest(
        self,
        method: t.Union[str, HTTPMethod],
        path: t.Optional[str] = None,
        **kwargs: t.Any
    ) -> RequestModel:
        """Build request for client-level method"""
        if isinstance(method, str):
            method = HTTPMethod(method.upper())

        baseurl = self.baseurl.rstrip('/')

        if path:
            url = f"{baseurl}/{path.lstrip('/')}"
        else:
            url = baseurl

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

    def _createboundmethod(self, method: t.Callable) -> t.Callable:
        methodconfig = getattr(method, '_methodconfig')

        def bound(*args, **kwargs):
            # preprocess request data if configured
            if methodconfig.preprocess:
                kwargs = methodconfig.preprocess(kwargs)

            # substitute path params
            path, consumed = self._substitutepath(methodconfig.path, **(kwargs or {}))

            # remove consumed parameters
            for kwarg in consumed:
                kwargs.pop(kwarg, None)

            # build request
            request = self._buildrequest(
               method=methodconfig.method,
               path=path,
               **(kwargs or {})
            )

            if self._backend:
                request = self._backend.formatrequest(request, kwargs)

            response = self._engine._session.send(request)

            if self._backend:
                processed = self._backend.processresponse(response)
            else:
                processed = response

            if methodconfig.postprocess:
                processed = methodconfig.postprocess(processed)

            return processed

        bound.__name__ = method.__name__
        bound.__doc__ = method.__doc__
        setattr(bound, '_methodconfig', methodconfig)
        return bound

    def _initmethods(self) -> None:
        """Initialize client-level HTTP methods."""
        for attrname in dir(self.__class__):
            if attrname.startswith('_'):
                continue

            attr = getattr(self.__class__, attrname)
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
