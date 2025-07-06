# ~/clientfactory/src/clientfactory/core/bases/engine.py
"""
Base Request Engine
------------------
Abstract base class for HTTP request engines.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.protos import RequestEngineProtocol, SessionProtocol
from clientfactory.core.models import HTTPMethod, RequestModel, ResponseModel, EngineConfig, SessionConfig
from clientfactory.core.bases.session import BaseSession
from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.metas.protocoled import ProtocoledAbstractMeta

class BaseEngine(abc.ABC, Declarative): #! add back in: RequestEngineProtocol,
    """
    Abstract base class for HTTP request engines.

    Provides common functionality and enforces protocol interface.
    Concrete implementations handle library-specific details.
    """
    __protocols: set  = {RequestEngineProtocol}
    __declaredas__: str = 'engine'
    __declcomps__: set = {'auth', 'persistence', 'session'}
    __declattrs__: set = {'poolsize', 'adapter'}
    __declconfs__: set = {'timeout', 'verify', 'retries'}

    def __init__(
        self,
        config: t.Optional[EngineConfig] = None,
        session: t.Optional[BaseSession] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize engine with configuration.""" #! update to reflect new signature
        # 1. resolve components
        components = self._resolvecomponents(session=session)

        # 2. resolve config
        self._config: EngineConfig = self._resolveconfig(EngineConfig, config, **kwargs)

        # 3. resolve session after config (needs _config)
        self._session: BaseSession = components['session']

        # 4. set up session
        self._session = self._setupsession(kwargs.get('sessionconfig'))

        # 5. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)

        self._closed: bool = False
        self._kwargs: dict = kwargs

    def _resolveattributes(self, attributes: dict) -> None:
        self._poolsize: int = attributes.get('poolsize', 10)
        self._adapter: t.Any = attributes.get('adapter', None)

    @abc.abstractmethod
    def _setupsession(self, config: t.Optional[SessionConfig] = None) -> BaseSession:
        """
        Create engine-specific session.
        """
        ...

    @abc.abstractmethod
    def _makerequest(
        self,
        method: HTTPMethod,
        url: str,
        usesession: t.Union[bool, BaseSession],
        noexec: bool = False,
        **kwargs: t.Any
    ) -> t.Union[RequestModel, ResponseModel]:
        """
        Implementation-specific request method.

        Concrete engines must implement this method.
        """
        ...

    ## core ##
    def request(
        self,
        method: t.Union[HTTPMethod, str],
        url: str,
        configoverride: bool = False,
        usesession: t.Union[bool, BaseSession] = True,
        noexec: bool = False,
        **kwargs: t.Any
    ) -> t.Union[RequestModel, ResponseModel]:
        """Make an HTTP request"""
        self._checknotclosed()

        # normalize method to HTTPMethod
        if isinstance(method, str):
            method = HTTPMethod(method.upper())

        # apply config defaults as fallbacks
        kwargs = self._applyconfigfallbacks(kwargs)

        # override with config defaults if flagged
        if configoverride:
            kwargs.update(self._config.requestoverrides())

        return self._makerequest(method, url, usesession, noexec=noexec, **kwargs)

    def _applyconfigfallbacks(self, requestkwargs: dict, noapply: t.Optional[t.List[str]] = None) -> dict:
        """
        Apply config values as fallbacks for None request values.

        Args:
            requestkwargs: Request kwargs from tokwargs()
            noapply: List of keys to exclude from config fallback application

        Returns:
            Updated kwargs with config fallbacks applied
        """
        kwargs = requestkwargs.copy()
        skip = set(noapply or [])

        for k,v in kwargs.items():
            if (
                v is None and # request value is None
                hasattr(self._config, k) and # config has this attribute
                k not in skip # key is not excluded
            ):
                fallback = getattr(self._config, k)
                if fallback is not None:
                    kwargs[k] = fallback

        return kwargs

    def send(
        self,
        request: RequestModel,
        noexec: bool = False,
        configoverride: bool = False,
        usesession: t.Union[bool, BaseSession] = True, # should execute request with session
    ) -> t.Union[RequestModel, ResponseModel]:
        """Send a prepared request object."""
        self._checknotclosed()
        kwargs = request.tokwargs()
        kwargs = self._applyconfigfallbacks(kwargs) # apply fallbacks from config
        if configoverride:
            kwargs.update(self._config.requestoverrides())
        return self._makerequest(request.method, request.url, usesession, noexec=noexec, **kwargs)

    ## convenience methods ##
    def get(self, url: str, noexec: bool = False, **kwargs: t.Any) -> t.Union[ResponseModel, RequestModel]:
        """Make a GET request."""
        if noexec:
            return RequestModel(method=HTTPMethod.GET, url=url, **kwargs)
        return self.request(HTTPMethod.GET, url, **kwargs)

    def post(self, url: str, noexec: bool = False, **kwargs: t.Any) -> t.Union[ResponseModel, RequestModel]:
        """Make a POST request."""
        if noexec:
            return RequestModel(method=HTTPMethod.POST, url=url, **kwargs)
        return self.request(HTTPMethod.POST, url, **kwargs)

    def put(self, url: str, noexec: bool = False, **kwargs: t.Any) -> t.Union[ResponseModel, RequestModel]:
        """Make a PUT request."""
        if noexec:
            return RequestModel(method=HTTPMethod.PUT, url=url, **kwargs)
        return self.request(HTTPMethod.PUT, url, **kwargs)

    def patch(self, url: str, noexec: bool = False, **kwargs: t.Any) -> t.Union[ResponseModel, RequestModel]:
        """Make a PATCH request."""
        if noexec:
            return RequestModel(method=HTTPMethod.PATCH, url=url, **kwargs)
        return self.request(HTTPMethod.PATCH, url, **kwargs)

    def delete(self, url: str, noexec: bool = False, **kwargs: t.Any) -> t.Union[ResponseModel, RequestModel]:
        """Make a DELETE request."""
        if noexec:
            return RequestModel(method=HTTPMethod.DELETE, url=url, **kwargs)
        return self.request(HTTPMethod.DELETE, url, **kwargs)

    def head(self, url: str, noexec: bool = False, **kwargs: t.Any) -> t.Union[ResponseModel, RequestModel]:
        """Make a HEAD request."""
        if noexec:
            return RequestModel(method=HTTPMethod.HEAD, url=url, **kwargs)
        return self.request(HTTPMethod.HEAD, url, **kwargs)

    def options(self, url: str, noexec: bool = False, **kwargs: t.Any) -> t.Union[ResponseModel, RequestModel]:
        """Make an OPTIONS request."""
        if noexec:
            return RequestModel(method=HTTPMethod.OPTIONS, url=url, **kwargs)
        return self.request(HTTPMethod.OPTIONS, url, **kwargs)

    ## lifectyle ##
    def _checknotclosed(self) -> None:
        """Check if engine is still open"""
        if self._closed:
            raise RuntimeError("Engine is closed")


    def close(self) -> None:
        """Close the engine and clean up resources."""
        self._closed = True

    ## context management ##
    def __enter__(self) -> RequestEngineProtocol:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
        """Exit context manager."""
        self.close()

    @classmethod
    def _compose(cls, other: t.Any) -> t.Any:
        raise NotImplementedError()
