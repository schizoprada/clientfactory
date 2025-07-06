# ~/clientfactory/src/clientfactory/core/bases/backend.py
"""
Base Backend Implementation
---------------------------
Abstract base class for response processing backends.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.protos import BackendProtocol
from clientfactory.core.models import (
    BackendConfig, RequestModel, ResponseModel
)
from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.metas.protocoled import ProtocoledAbstractMeta

class BaseBackend(abc.ABC, Declarative): #! add back in BackendProtocol,
    """
    Abstract base class for response processing backends.

    Provides common functionality for API-specific request formatting
    and response processing. Concrete implementations handle specific
    API protocols (REST, GraphQL, Algolia, etc.).
    """
    __protocols: set = {BackendProtocol}
    __declaredas__: str = 'backend'
    __declcomps__: set = set()
    __declattrs__: set = {'endpoint', 'apiversion', 'format'}
    __declconfs__: set = {'timeout', 'retries', 'raiseonerror', 'autoparse'}

    def __init__(
        self,
        config: t.Optional[BackendConfig] = None,
        **kwargs: t.Any
    ) -> None:
        # 1. resolve components
        components = self._resolvecomponents() # not needed

        # 2. resolve config
        self._config: BackendConfig = self._resolveconfig(BackendConfig, config, **kwargs)

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        #print(f"DEBUG Backend.__init__: collected attrs = {attrs}")
        self._resolveattributes(attrs)


    def _resolveattributes(self, attributes: dict) -> None:
        #print(f"DEBUG Backend._resolveattributes: attributes = {attributes}")
        #print(f"DEBUG Backend._resolveattributes: self._config = {self._config}")
        #print(f"DEBUG Backend._resolveattributes: self._config.model_dump() = {self._config.model_dump()}")

        self.endpoint: str = attributes.get('endpoint', '')
        self.apiversion: str = attributes.get('apiversion', 'v1')
        self.format: str = attributes.get('format', 'json')
        #print(f"DEBUG Backend._resolveattributes: final self.endpoint = {self.endpoint}")
        #print(f"DEBUG Backend._resolveattributes: final self.apiversion = {self.apiversion}")
        #print(f"DEBUG Backend._resolveattributes: final self.format = {self.format}")


    @abc.abstractmethod
    def _formatrequest(self, request: RequestModel, data: t.Dict[str, t.Any]) -> RequestModel:
        """
        Backend-specific request formatting.

        Concrete backends implement protocol-specific formatting logic.

        Args:
            request: Base request to format
            data: Request data to include

        Returns:
            Formatted request ready for backend
        """
        ...

    @abc.abstractmethod
    def _processresponse(self, response: ResponseModel) -> t.Any:
        """
        Backend-specific response processing.

        Concrete backends implement protocol-specific processing logic.

        Args:
            response: Raw response from backend

        Returns:
            Processed response data
        """
        ...

    def validatedata(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """
        Validate data before sending to backend.

        Base implementation does no validation.
        Concrete backends can override for specific validation.
        """
        return data

    def handleerror(self, response: ResponseModel) -> None:
        """
        Handle backend-specific errors.

        Base implementation checks HTTP status codes.
        Concrete backends can override for protocol-specific errors.
        """
        if not self._config.raiseonerror:
            return
        if not response.ok:
            response.raiseforstatus()

    def formatrequest(self, request: RequestModel, data: t.Dict[str, t.Any]) -> RequestModel:
        """Format request for specific backend."""
        try:
            return self._formatrequest(request, data)
        except Exception as e:
            raise RuntimeError(f"Request formatting failed: {e}") from e

    def processresponse(self, response: ResponseModel) -> t.Any:
        """Process response from backend."""
        try:
            # check for errors first
            self.handleerror(response)
            return self._processresponse(response)
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Response processing failed: {e}") from e

    @classmethod
    def _compose(cls, other: t.Any) -> t.Any:
        raise NotImplementedError()
