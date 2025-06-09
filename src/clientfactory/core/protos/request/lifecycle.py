# ~/clientfactory/src/clientfactory/core/protos/request/lifecycle.py
"""
Session Lifecycle Protocol
--------------------------
Protocol for request/response lifecycle management.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.protos.auth import AuthProtocol
from clientfactory.core.protos.request.engine import RequestEngineProtocol

if t.TYPE_CHECKING:
    from clientfactory.core.models.request import RequestModel, ResponseModel


@t.runtime_checkable
class SessionProtocol(t.Protocol):
    """
    Request/response lifecycle management protocol.

    Handles request preparation, authentication, and response processing.
    """

    def send(self, request: 'RequestModel') -> 'ResponseModel':
        """
        Send a request and return response.

        Args:
            request: Request to send

        Returns:
            Response from server
        """
        ...

    def preparerequest(self, request: 'RequestModel') -> 'RequestModel':
        """
        Prepare request for sending.

        Args:
            request: Raw request to prepare

        Returns:
            Prepared request with auth, headers, etc.
        """
        ...

    def processresponse(self, response: 'ResponseModel') -> 'ResponseModel':
        """
        Process response after receiving.

        Args:
            response: Raw response

        Returns:
            Processed response
        """
        ...

    def setauth(self, auth: AuthProtocol) -> None:
        """
        Set authentication for session.

        Args:
            auth: Authentication provider
        """
        ...


    def close(self) -> None:
        """Close session and clean up resources."""
        ...

    def __enter__(self) -> SessionProtocol:
        """Enter context manager."""
        ...

    def __exit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
        """Exit context manager."""
        ...
