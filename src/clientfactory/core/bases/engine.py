# ~/clientfactory/src/clientfactory/core/bases/engine.py
"""
Base Request Engine
------------------
Abstract base class for HTTP request engines.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.protos import RequestEngineProtocol
from clientfactory.core.models import HTTPMethod, RequestModel, ResponseModel


class BaseEngine(RequestEngineProtocol, abc.ABC):
    """
    Abstract base class for HTTP request engines.

    Provides common functionality and enforces protocol interface.
    Concrete implementations handle library-specific details.
    """
    def __init__(
        self,
        **kwargs: t.Any
    ) -> None:
        """Initialize engine with configuration."""
        self._closed: bool = False
        self._config: dict = kwargs

    ## abstracts ##
    @abc.abstractmethod
    def _makerequest(
        self,
        method: HTTPMethod,
        url: str,
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
        **kwargs: t.Any
    ) -> ResponseModel:
        """Make an HTTP request"""
        self._checknotclosed()

        # normalize method to HTTPMethod
        if isinstance(method, str):
            method = HTTPMethod(method.upper())

        return self._makerequest(method, url, **kwargs)

    def send(
        self,
        request: RequestModel
    ) -> ResponseModel:
        """Send a prepared request object."""
        self._checknotclosed()
        return self._makerequest(request.method, request.url, **request.tokwargs())

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
