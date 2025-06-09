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

class BaseEngine(RequestEngineProtocol, abc.ABC):
    """
    Abstract base class for HTTP request engines.

    Provides common functionality and enforces protocol interface.
    Concrete implementations handle library-specific details.
    """
    def __init__(
        self,
        config: t.Optional[EngineConfig] = None,
        session: t.Optional[BaseSession] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize engine with configuration.""" #! update to reflect new signature
        self._closed: bool = False
        self._config: EngineConfig = (config or EngineConfig(**kwargs))
        self._session: BaseSession = (session or self._setupsession(kwargs.get('sessionconfig')))
        self._kwargs: dict = kwargs

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
        usesession: bool,
        **kwargs: t.Any
    ) -> ResponseModel:
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
        usesession: bool = True,
        **kwargs: t.Any
    ) -> ResponseModel:
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

        return self._makerequest(method, url, usesession, **kwargs)

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
        configoverride: bool = False,
        usesession: bool = True, # should execute request with session
    ) -> ResponseModel:
        """Send a prepared request object."""
        self._checknotclosed()
        kwargs = request.tokwargs()
        kwargs = self._applyconfigfallbacks(kwargs) # apply fallbacks from config
        if configoverride:
            kwargs.update(self._config.requestoverrides())
        return self._makerequest(request.method, request.url, usesession, **kwargs)

    ## convenience methods ##
    def get(self, url: str, **kwargs: t.Any) -> ResponseModel:
        """Make a GET request."""
        return self.request(HTTPMethod.GET, url, **kwargs)

    def post(self, url: str, **kwargs: t.Any) -> ResponseModel:
        """Make a POST request."""
        return self.request(HTTPMethod.POST, url, **kwargs)

    def put(self, url: str, **kwargs: t.Any) -> ResponseModel:
        """Make a PUT request."""
        return self.request(HTTPMethod.PUT, url, **kwargs)

    def patch(self, url: str, **kwargs: t.Any) -> ResponseModel:
        """Make a PATCH request."""
        return self.request(HTTPMethod.PATCH, url, **kwargs)

    def delete(self, url: str, **kwargs: t.Any) -> ResponseModel:
        """Make a DELETE request."""
        return self.request(HTTPMethod.DELETE, url, **kwargs)

    def head(self, url: str, **kwargs: t.Any) -> ResponseModel:
        """Make a HEAD request."""
        return self.request(HTTPMethod.HEAD, url, **kwargs)

    def options(self, url: str, **kwargs: t.Any) -> ResponseModel:
        """Make an OPTIONS request."""
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
