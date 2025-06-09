# ~/clientfactory/src/clientfactory/core/protos/request/engine.py
"""
Request Engine Protocol
-----------------------
Protocol for HTTP transport engines.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models.enums import HTTPMethod

if t.TYPE_CHECKING:
    from clientfactory.core.models.request import RequestModel, ResponseModel


@t.runtime_checkable
class RequestEngineProtocol(t.Protocol):
   """
   HTTP transport engine protocol.

   Allows swapping between different HTTP libraries (requests, httpx, aiohttp).
   Default implementation uses `requests` library.
   """

   def request(
       self,
       method: HTTPMethod | str,
       url: str,
       **kwargs: t.Any
   ) -> 'ResponseModel':
       """
       Make an HTTP request.

       Args:
           method: HTTP method to use
           url: URL to request
           **kwargs: Additional request parameters

       Returns:
           Response object
       """
       ...

   def send(self, request: 'RequestModel', *args, **kwargs) -> 'ResponseModel':
       """
       Send a prepared request object.

       Args:
           request: Prepared request to send

       Returns:
           Response object
       """
       ...

   def get(self, url: str, **kwargs: t.Any) -> 'ResponseModel':
       """Make a GET request."""
       ...

   def post(self, url: str, **kwargs: t.Any) -> 'ResponseModel':
       """Make a POST request."""
       ...

   def put(self, url: str, **kwargs: t.Any) -> 'ResponseModel':
       """Make a PUT request."""
       ...

   def patch(self, url: str, **kwargs: t.Any) -> 'ResponseModel':
       """Make a PATCH request."""
       ...

   def delete(self, url: str, **kwargs: t.Any) -> 'ResponseModel':
       """Make a DELETE request."""
       ...

   def head(self, url: str, **kwargs: t.Any) -> 'ResponseModel':
       """Make a HEAD request."""
       ...

   def options(self, url: str, **kwargs: t.Any) -> 'ResponseModel':
       """Make an OPTIONS request."""
       ...

   def close(self) -> None:
       """Close the engine and clean up resources."""
       ...

   def __enter__(self) -> RequestEngineProtocol:
       """Enter context manager."""
       ...

   def __exit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
       """Exit context manager."""
       ...
