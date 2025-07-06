# ~/clientfactory/src/clientfactory/core/bases/auth.py
"""
Base Authentication Implementation
---------------------------------
Abstract base class for authentication providers.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import RequestModel, AuthConfig
from clientfactory.core.protos import AuthProtocol
from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.metas.protocoled import ProtocoledAbstractMeta

class BaseAuth(abc.ABC, Declarative): #! add back in AuthProtocol,
    """
    Abstract base class for authentication providers.

    Provides common functionality and enforces protocol interface.
    Concrete implementations handle specific auth strategies.
    """
    __protocols: set = {AuthProtocol}
    __declaredas__: str = 'auth'
    __declcomps__: set = set()
    __declattrs__: set = {'token', 'username', 'password', 'key', 'scheme'}
    __declconfs__: set = {'timeout', 'retries', 'autorefresh'}

    def __init__(
        self,
        config: t.Optional[AuthConfig] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize auth provider."""
        # 1. resolve components
        components = self._resolvecomponents() # none needed

        # 2. resolve config
        self._config: AuthConfig = self._resolveconfig(AuthConfig, config, **kwargs)

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)

        self._authenticated: bool = False
        self._kwargs: dict = kwargs

    def _resolveattributes(self, attributes: dict) -> None:
        self.token: str = attributes.get('token', '')
        self.username: str = attributes.get('username', '')
        self.password: str = attributes.get('password', '')
        self.key: str = attributes.get('key', '')
        self.scheme: str = attributes.get('scheme', '')

    ## abstracts ##
    @abc.abstractmethod
    def _authenticate(self) -> bool:
        """
        Provider-specific authentication logic.

        Concrete auth implementations must implement this method.
        """
        ...

    @abc.abstractmethod
    def _applyauth(self, request: RequestModel) -> RequestModel:
        """
        Provider-specific auth application.

        Concrete auth implementations must implement this method.
        """
        ...

    ## concretes ##
    def isauthenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated

    def shouldrefresh(self) -> bool:
        """Check if auth should be refreshed."""
        # base implementation - no refresh needed
        return False

    def authenticate(self) -> bool:
        """Perform authentication."""
        try:
            self._authenticated = self._authenticate()
            return self._authenticated
        except Exception:
            self._authenticated = False
            raise

    def applyauth(self, request: RequestModel) -> RequestModel:
        """Apply authentication to request."""
        if not self.isauthenticated():
            if not self.authenticate():
                raise RuntimeError("Authentication failed")

        return self._applyauth(request)

    def refresh(self) -> bool:
        """Refresh authentication."""
        # base implementation - re-authenticate
        return self.authenticate()

    def refreshifneeded(self) -> None:
        """Refresh authentication if needed."""
        if self.shouldrefresh():
            self.refresh()

    def clear(self) -> None:
        """Clear authentication state."""
        self._authenticated = False

    @classmethod
    def _compose(cls, other: t.Any) -> t.Any:
        raise NotImplementedError()
