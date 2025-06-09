# ~/clientfactory/src/clientfactory/core/protos/auth.py
"""
Authentication Protocol
-----------------------
Protocol for authentication strategies.
"""
from __future__ import annotations
import typing as t

if t.TYPE_CHECKING:
    from clientfactory.core.models.request import RequestModel

@t.runtime_checkable
class AuthProtocol(t.Protocol):
    """
    Authentication strategy protocol.

    Defines interface for credential management and request authentication.
    """

    def applyauth(self, request: 'RequestModel') -> 'RequestModel':
        """
        Apply authentication to a request.

        Args:
            request: Request to authenticate

        Returns:
            New request with authentication applied
        """
        ...

    def isauthenticated(self) -> bool:
        """
        Check if currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        ...

    def shouldrefresh(self) -> bool:
        """"""
        ...

    def refresh(self) -> bool:
        """"""
        ...

    def refreshifneeded(self) -> None:
        """
        Refresh authentication if needed.

        Should check expiration and refresh credentials if necessary.
        """
        ...

    def authenticate(self) -> bool:
        """
        Perform initial authentication.

        Returns:
            True if authentication successful, False otherwise
        """
        ...

    def clear(self) -> None:
        """
        Clear authentication state.

        Removes stored credentials and resets authentication status.
        """
        ...
