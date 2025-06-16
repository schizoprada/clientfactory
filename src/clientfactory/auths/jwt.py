# ~/clientfactory/src/clientfactory/auths/jwt.py
"""
JWT Authentication
-----------------
JWT Bearer token authentication for ClientFactory.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.bases import BaseAuth
from clientfactory.core.models import RequestModel


class JWTAuth(BaseAuth):
    """
    JWT Bearer token authentication.

    Applies JWT tokens as Bearer authorization headers.
    """
    __declaredas__: str = 'jwt'

    def __init__(
        self,
        token: t.Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._token = token

    def _authenticate(self) -> bool:
        """JWT auth is authenticated if a token is present."""
        return (self._token is not None)

    def _applyauth(self, request: RequestModel) -> RequestModel:
        """Apply JWT Bearer token to Authorization header."""
        if not self._token:
            raise RuntimeError(f"No JWT token available")
        return request.withauth("Authorization", f"Bearer {self._token}")

    def settoken(self, token: str) -> None:
        """Set the JWT token."""
        self._token = token
        self._authenticated = True
