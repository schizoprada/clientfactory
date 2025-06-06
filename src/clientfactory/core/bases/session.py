# ~/clientfactory/src/clientfactory/core/bases/session.py
"""
Base Session Implementation
--------------------------
Abstract base class for session lifecycle management.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import RequestModel, ResponseModel, SessionConfig
from clientfactory.core.protos import (
    SessionProtocol, AuthProtocol, RequestEngineProtocol
)

class BaseSession(SessionProtocol, abc.ABC):
    """
    Abstract base class for session lifecycle management.

    Handles request preparation, authentication, and response processing.
    Concrete implementations define specific session behaviors.
    """
    def __init__(
        self,
        engine: t.Optional[RequestEngineProtocol] = None,
        auth: t.Optional[AuthProtocol] = None,
        config: t.Optional[SessionConfig] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize session with engine and auth."""
        self._engine: t.Optional[RequestEngineProtocol] = engine
        self._auth: t.Optional[AuthProtocol] = auth
        self._config: SessionConfig = (config or SessionConfig(**kwargs))
        self._closed: bool = False

    ## abstracts ##
    @abc.abstractmethod
    def _preparerequest(self, request: RequestModel) -> RequestModel:
        """
        Session-specific request preparation.

        Concrete sessions implement custom preparation logic.
        """
        ...

    @abc.abstractmethod
    def _processresponse(self, response: ResponseModel) -> ResponseModel:
        """
        Session-specific response processing.

        Concrete sessions implement custom processing logic.
        """
        ...


    ## helper methods ##
    def _checknotclosed(self) -> None:
        """Check if session is still open"""
        if self._closed:
            raise RuntimeError("Session is closed")

    def _checkengineavailable(self) -> None:
        """Check if a request engine has been configured"""
        if (not self._engine) or (self._engine is None):
            raise RuntimeError(f"No engine configured")

    ## core methods ##
    def preparerequest(self, request: RequestModel) -> RequestModel:
        """
        Prepare request for sending.

        Apply authentication, default headers, etc.
        """
        prepared = request

        # apply auth if available
        if (self._auth and self._auth.isauthenticated()):
            prepared = self._auth.applyauth(prepared)
        elif self._auth:
            # try to authenticate
            if self._auth.authenticate():
                prepared = self._auth.applyauth(prepared)

        # instance-specific preparation
        prepared = self._preparerequest(prepared)

        return prepared

    def processresponse(self, response: ResponseModel) -> ResponseModel:
        """
        Process response after receiving.

        Handle session-level response processing.
        """
        processed = self._processresponse(response)

        # refresh auth if needed
        if (self._auth and self._auth.shouldrefresh()):
            self._auth.refreshifneeded()

        return processed


    def send(self, request: RequestModel) -> ResponseModel:
        """
        Send a request and return response.

        Main request lifecycle orchestration.
        """
        self._checknotclosed()
        self._checkengineavailable()

        # prepare the request
        prepared = self.preparerequest(request)

        # send via engine
        response = self._engine.send(prepared) # type: ignore // we already checked

        # process response
        return self.processresponse(response)


    ## lifecycle management ##
    def close(self) -> None:
        """Close session and cleanup resources"""
        if self._engine:
            self._engine.close()
        self._closed = True

    ## component management ##
    def setauth(self, auth: AuthProtocol) -> None:
        """Set authentication for session"""
        self._auth = auth

    def setengine(self, engine: RequestEngineProtocol) -> None:
        """Set HTTP Engine for session"""
        self._engine = engine

    ## context management ##
    def __enter__(self) -> SessionProtocol:
        """Enter context manager"""
        return self

    def __exit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
        """Exit context manager"""
        self.close()
