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
    SessionProtocol, AuthProtocol, RequestEngineProtocol,
    PersistenceProtocol
)
from clientfactory.core.bases.declarative import Declarative

class BaseSession(abc.ABC, Declarative): #! add back in: SessionProtocol,
    """
    Abstract base class for session lifecycle management.

    Handles request preparation, authentication, and response processing.
    Concrete implementations define specific session behaviors.
    """
    __declcomps__: set = {'auth', 'persistence'}
    __declattrs__: set = {'headers', 'cookies', 'useragent'}
    __declconfs__: set = {'timeout', 'retries', 'verifyssl', 'allowredirects', 'maxredirects'}

    def __init__(
        self,
        auth: t.Optional[AuthProtocol] = None,
        persistence: t.Optional[PersistenceProtocol] = None,
        config: t.Optional[SessionConfig] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize session with engine and auth."""
        self._auth: t.Optional[AuthProtocol] = auth
        self._persistence: t.Optional[PersistenceProtocol] = persistence
        self._config: SessionConfig = (config or SessionConfig(**kwargs))
        self._closed: bool = False
        self._obj: t.Any = self._setup()

    ## abstracts ##
    @abc.abstractmethod
    def _setup(self) -> t.Any:
        """
        Create the underlying library-specific session object,
        and apply any configurations.
        """
        ...

    @abc.abstractmethod
    def _cleanup(self) -> None:
        """
        Clean up session resources.
        """

    @abc.abstractmethod
    def _preparerequest(self, request: RequestModel) -> RequestModel:
        """
        Session-specific request preparation.

        Concrete sessions implement custom preparation logic.
        """
        ...

    @abc.abstractmethod
    def _makerequest(self, request: RequestModel) -> ResponseModel:
        """Session-specific request execution"""
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

    def _loadpersistentstate(self) -> None:
        """Load session state from persistence"""
        if not self._persistence:
            return

        state = self._persistence.load()

        if ('cookies' in state) and (hasattr(self._obj, 'cookies')):
            self._obj.cookies.update(state['cookies'])

        if ('headers' in state) and (hasattr(self._obj, 'headers')):
            self._obj.headers.update(state['headers'])


    def _savepersistentstate(self) -> None:
        """Save session state to persistence"""
        if not self._persistence:
            return

        state = {}
        if hasattr(self._obj, 'cookies'):
            state['cookies'] = dict(self._obj.cookies)
        if hasattr(self._obj, 'headers'):
            state['headers'] = dict(self._obj.headers)


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

        # prepare the request
        prepared = self.preparerequest(request)

        response = self._makerequest(prepared) # session literal handles

        # process response
        return self.processresponse(response)


    ## lifecycle management ##
    def close(self) -> None:
        """Close session and cleanup resources"""
        self._cleanup()
        self._closed = True

    ## component management ##
    def setauth(self, auth: AuthProtocol) -> None:
        """Set authentication for session"""
        self._auth = auth

    ## context management ##
    def __enter__(self) -> SessionProtocol:
        """Enter context manager"""
        return self

    def __exit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
        """Exit context manager"""
        self.close()

    ## properties ##
    @property
    def obj(self) -> t.Any:
        """The library-specific session object"""
        return self._obj
