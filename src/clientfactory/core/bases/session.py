# ~/clientfactory/src/clientfactory/core/bases/session.py
"""
Base Session Implementation
--------------------------
Abstract base class for session lifecycle management.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import (
    RequestModel, ResponseModel, SessionConfig,
    SessionInitializer, MergeMode, HeaderMetadata,
    SessionMetadata
)
from clientfactory.core.protos import (
    SessionProtocol, AuthProtocol, RequestEngineProtocol,
    PersistenceProtocol
)
from clientfactory.core.utils.session.meta import (
    ensuresessionmeta, metaheaders, metasession
)
from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.metas.protocoled import ProtocoledAbstractMeta

from clientfactory.logs import log

class BaseSession(abc.ABC, Declarative): #! add back in: SessionProtocol,
    """
    Abstract base class for session lifecycle management.

    Handles request preparation, authentication, and response processing.
    Concrete implementations define specific session behaviors.
    """
    __protocols: set = {SessionProtocol}
    __declaredas__: str = 'session'
    __declcomps__: set = {'auth', 'persistence'}
    __declattrs__: set = {'headers', 'cookies', 'useragent'}
    __declconfs__: set = {'timeout', 'retries', 'verifyssl', 'allowredirects', 'maxredirects', 'initializer'}

    def __init__(
        self,
        auth: t.Optional[AuthProtocol] = None,
        persistence: t.Optional[PersistenceProtocol] = None,
        config: t.Optional[SessionConfig] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize session with engine and auth."""
        log.debug(f"BaseSession.__init__: class={self.__class__.__name__}")
        log.debug(f"BaseSession.__init__: auth={auth}, persistence={persistence}")

        # 1. resolve components
        components = self._resolvecomponents(auth=auth, persistence=persistence)
        log.debug(f"BaseSession.__init__: resolved components = {components}")

        self._auth: t.Optional[AuthProtocol] = components['auth']
        self._persistence: t.Optional[PersistenceProtocol] = components['persistence']
        log.debug(f"BaseSession.__init__: self._auth = {self._auth}")
        log.debug(f"BaseSession.__init__: self._persistence = {self._persistence}")

        # 2. resolve config
        self._config: SessionConfig = self._resolveconfig(SessionConfig, config, **kwargs)
        log.debug(f"BaseSession.__init__: self._config = {self._config}")

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        log.debug(f"BaseSession.__init__: attrs = {attrs}")
        self._resolveattributes(attrs)

        # initialize session metadata tracking
        self._focusedmeta: t.Optional[SessionMetadata] = None

        self._closed: bool = False
        self._obj: t.Any = self._setup()
        log.debug(f"BaseSession.__init__: setup complete, _obj = {type(self._obj)}")

    def _resolveattributes(self, attributes: dict) -> None:
        log.info(f"BaseSession._resolveattributes: attributes = {attributes}")
        self._headers: dict = attributes.get('headers', {})
        self._cookies: dict = attributes.get('cookies', {})
        self._initializer: t.Optional[SessionInitializer] = attributes.get('initializer')

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
    def _preparerequest(self, request: RequestModel, noexec: bool = False) -> RequestModel:
        """
        Session-specific request preparation.

        Concrete sessions implement custom preparation logic.
        """
        ...

    @abc.abstractmethod
    def _makerequest(self, request: RequestModel, noexec: bool = False) -> t.Union[RequestModel, ResponseModel]:
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

    def _handleresponseheaders(self, response: ResponseModel) -> None:
        """Handle response headers based on focused method metadata."""
        if not (
            self._focusedmeta and
            'headers' in self._focusedmeta and
            response.headers
        ):
            return
        log.info(f"(BaseSession._handleresponseheaders) processing {len(response.headers)} headers with config: {self._focusedmeta['headers']}")

        options = self._focusedmeta['headers']

        # handle ignore=True first
        ignore = options.get('ignore', [])
        if ignore is True:
            log.info(f"(BaseSession._handleresponseheaders) ignoring all headers")
            return
        ignoreable = ignore if isinstance(ignore, list) else []

        current = metasession.getheaders(self._obj) # current headers

        # apply operations
        if ('add' in options):
            added = metaheaders.applyadd(
                current,
                response.headers,
                options['add'],
                ignoreable
            )
            metasession.setheaders(self._obj, added)
        if ('update' in options):
            updated = metaheaders.applyupdate(
                current,
                response.headers,
                options['update'],
                ignoreable
            )
            metasession.setheaders(self._obj, updated)
        if ('discard' in options):
            preserved = metaheaders.applydiscard(
                current,
                options['discard']
            )
            metasession.setheaders(self._obj, preserved)

    def _handleresponse(self, response: ResponseModel) -> ResponseModel:
        """Handle all response-level processing."""
        # headers first
        self._handleresponseheaders(response)

        return response

    ## core methods ##
    def preparerequest(self, request: RequestModel, noexec: bool = False) -> RequestModel:
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
        prepared = self._preparerequest(prepared, noexec=noexec)

        return prepared

    def processresponse(self, response: ResponseModel) -> ResponseModel:
        """
        Process response after receiving.

        Handle session-level response processing.
        """
        # handle session-level response processing (headers, cookies, etc.)
        self._handleresponse(response)

        processed = self._processresponse(response)

        # refresh auth if needed
        if (self._auth and self._auth.shouldrefresh()):
            self._auth.refreshifneeded()

        return processed

    def send(self, request: RequestModel, noexec: bool = False) -> t.Union[RequestModel, ResponseModel]:
        """
        Send a request and return response.

        Main request lifecycle orchestration.
        """
        self._checknotclosed()

        # prepare the request
        prepared = self.preparerequest(request, noexec=noexec)

        response = self._makerequest(prepared, noexec=noexec) # session literal handles
        if isinstance(response, RequestModel):
            return response
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

    @classmethod
    def _compose(cls, other: t.Any) -> t.Any:
        raise NotImplementedError()

    ## class methods ##
    @classmethod
    def AddHeaders(cls, *headers: str) -> t.Callable:
        """
        Decorator to add response headers to session state.

        Args:
            *headers: Specific header names to add. If empty, adds all response headers.

        Returns:
            Decorator function that marks method for header addition

        Example:
            @MySession.AddHeaders('x-api-key', 'authorization')
            @get('endpoint')
            def get_data(self): pass

            @MySession.AddHeaders()  # Add all headers
            @post('login')
            def login(self): pass
        """
        addable = list(headers) if headers else True
        def decorator(func: t.Callable) -> t.Callable:
            log.critical(f"({cls.__name__}.AddHeaders)@[{func.__name__}] addable: {addable}")
            func = ensuresessionmeta(func)
            func._sessionmeta['headers']['add'] = addable
            return func
        return decorator

    @classmethod
    def UpdateHeaders(cls, *headers: str) -> t.Callable:
        """
        Decorator to update existing session headers with response values.

        Only updates headers that already exist in session state.

        Args:
            *headers: Specific header names to update. If empty, updates all existing headers.

        Returns:
            Decorator function that marks method for header updating

        Example:
            @MySession.UpdateHeaders('authorization', 'x-session-token')
            @get('refresh')
            def refresh_token(self): pass

            @MySession.UpdateHeaders()  # Update all existing headers
            @post('authenticate')
            def authenticate(self): pass
        """
        updateable = list(headers) if headers else True
        def decorator(func: t.Callable) -> t.Callable:
            func = ensuresessionmeta(func)
            func._sessionmeta['headers']['update'] = updateable
            return func
        return decorator

    @classmethod
    def IgnoreHeaders(cls, *headers: str) -> t.Callable:
        """
        Decorator to ignore specific response headers for this method.

        Prevents specified headers from being processed by session.

        Args:
            *headers: Specific header names to ignore. If empty, ignores all response headers.

        Returns:
            Decorator function that marks method to ignore headers

        Example:
            @MySession.IgnoreHeaders('content-type', 'server')
            @get('data')
            def get_static_data(self): pass

            @MySession.IgnoreHeaders()  # Ignore all headers
            @get('download')
            def download_file(self): pass
        """
        ignoreable = list(headers) if headers else True
        def decorator(func: t.Callable) -> t.Callable:
            func = ensuresessionmeta(func)
            func._sessionmeta['headers']['ignore'] = ignoreable
            return func
        return decorator

    @classmethod
    def DiscardHeaders(cls, *headers: str) -> t.Callable:
        """
        Decorator to remove headers from session state after response.

        Removes specified headers from session, useful for cleanup.

        Args:
            *headers: Specific header names to discard. If empty, clears all session headers.

        Returns:
            Decorator function that marks method for header removal

        Example:
            @MySession.DiscardHeaders('temp-token', 'x-request-id')
            @post('logout')
            def logout(self): pass

            @MySession.DiscardHeaders()  # Clear all headers
            @delete('session')
            def clear_session(self): pass
        """
        discardable = list(headers) if headers else True
        def decorator(func: t.Callable) -> t.Callable:
            func = ensuresessionmeta(func)
            func._sessionmeta['headers']['discard'] = discardable
            return func
        return decorator

    @classmethod
    def Headers(
        cls,
        add: t.Optional[t.Union[bool, t.List[str]]] = None,
        update: t.Optional[t.Union[bool, t.List[str]]] = None,
        ignore: t.Optional[t.Union[bool, t.List[str]]] = None,
        discard: t.Optional[t.Union[bool, t.List[str]]] = None
    ) -> t.Callable:
        """
        Decorator for comprehensive header processing configuration.

        Combines multiple header operations in a single decorator.

        Args:
            add: Headers to add (bool for all, list for specific)
            update: Headers to update (bool for all existing, list for specific)
            ignore: Headers to ignore (bool for all, list for specific)
            discard: Headers to discard (bool for all, list for specific)

        Returns:
            Decorator function that applies specified header processing

        Example:
            @MySession.Headers(add=['x-api-key'], ignore=['server', 'date'])
            @get('endpoint')
            def get_data(self): pass

            @MySession.Headers(update=True, discard=['temp-header'])
            @post('submit')
            def submit_data(self): pass
        """
        operable = {'add': add, 'update': update, 'ignore': ignore, 'discard': discard}
        def decorator(func: t.Callable) -> t.Callable:
            log.critical(f"({cls.__name__}.Headers)@[{func.__name__}] operatable: {operable}")
            func = ensuresessionmeta(func)
            for k,v in operable.items():
                if v is not None:
                    func._sessionmeta['headers'][k] = v
            return func
        return decorator
