# ~/clientfactory/src/clientfactory/engines/requestslib.py
"""
Requests Engine Implementation
-----------------------------
HTTP engine implementation using the requests library.
"""
from __future__ import annotations
import typing as t

import requests as rq
from requests.adapters import HTTPAdapter
from urllib3.util.connection import create_connection
from urllib3.poolmanager import PoolManager

from clientfactory.core.bases import BaseEngine, BaseSession
from clientfactory.core.models import (
    HTTPMethod, RequestModel, ResponseModel,
    EngineConfig, SessionConfig
)

from clientfactory.logs import log

class HTTP11Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = None # force http/1.1
        return super().init_poolmanager(*args, **kwargs)


class RequestsSession(BaseSession):
    """Session implementation using requests.Session"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def _cleanup(self) -> None:
        if self._obj is not None:
            self._obj.close()

    def _setup(self) -> rq.Session:
        """Create and configure requests.Session object."""
        session = rq.Session()

        log.info(f"""
            RequestsSession._setup
            ----------------------
            self._headers = {self._headers}

            self._config.defaultheaders = {self._config.defaultheaders}
            """)



        # Apply session config to requests.Session
        if self._config.defaultheaders:
            session.headers.update(self._config.defaultheaders)

        if self._config.defaultcookies:
            session.cookies.update(self._config.defaultcookies)

        if self._initializer:
            session = self._initializer.initialize(session)

        # Configure adapters for retries if needed
        if self._config.maxretries > 0:
            adapter = HTTPAdapter(max_retries=self._config.maxretries)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

        log.info(f"""
            RequestsSession._setup
            ----------------------
            (final) session.headers = {session.headers}
            """)
        return session

    def _preparerequest(self, request: RequestModel, noexec: bool = False) -> RequestModel:
        """Apply session-level defaults to request."""
        log.info(f"""
            RequestsSession._preparerequest
            -------------------------------
            self._obj.headers: {dict(self._obj.headers)}

            (before) request.headers: {request.headers}
            """)

        headers = dict(self._obj.headers).copy()
        headers.update(request.headers)
        updated = request.withheaders(headers)

        log.info(f"""
            RequestsSession._preparerequest
            -------------------------------
            (merged) headers: {headers}

            (after) request.headers: {updated.headers}
            """)

        return updated

    def _makerequest(self, request: RequestModel, noexec: bool = False) -> t.Union[RequestModel, ResponseModel]:
        """Execute request using requests.Session"""
        if noexec:
            return request
        log.info(f"RequestsSession._makerequest: BEFORE tokwargs - request.json = {request.json}")
        kwargs = request.tokwargs()
        log.info(f"RequestsSession._makerequest: AFTER tokwargs - kwargs = {kwargs}")

        try:
            response = self._obj.request(
                method=request.method.value,
                url=request.url,
                **kwargs
            )
            return ResponseModel.FromRequests(response)
        except rq.RequestException as e:
            raise RuntimeError(f"Request failed: {e}") from e

    def _processresponse(self, response: ResponseModel) -> ResponseModel:
        """Standard response processing."""
        return response

    @classmethod
    def FromGeneric(cls, session: BaseSession) -> 'RequestsSession':
        """Create RequestsSession from generic session, preserving all attributes."""
        headers = getattr(session, '_headers', {})
        cookies = getattr(session, '_cookies', {})
        auth = getattr(session, '_auth', None)
        persistence = getattr(session, '_persistence', None)

        config = session._config.updateheaders(headers).updatecookies(cookies)

        rqsession = cls(
            config=config,
            headers=headers,
            cookies=cookies,
            auth=auth,
            persistence=persistence
        )

        return rqsession

class RequestsEngine(BaseEngine):
    """
    HTTP engine implementation using requests library.

    Default engine for ClientFactory with full feature support.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


    def _setupsession(self, config: t.Optional[SessionConfig] = None) -> RequestsSession:
        """Create RequestsSession with config cascade, upgrading provided sessions if needed."""

        sessionprovided = lambda: hasattr(self, '_session') and self._session
        needsupgrade = lambda: sessionprovided() and not isinstance(self._session, RequestsSession)
        goodtogo = lambda: sessionprovided() and isinstance(self._session, RequestsSession)

        extantsession = None
        extantheaders = {}
        extantcookies = {}
        extantauth = None
        extantpersist = None
        extantconfig = None

        if sessionprovided():
            extantsession = self._session
            extantheaders = getattr(extantsession, '_headers', {})
            extantcookies = getattr(extantsession, '_cookies', {})
            extantauth = getattr(extantsession, '_auth', None)
            extantpersist = getattr(extantsession, '_persistence', None)
            extantconfig = getattr(extantsession, '_config', None)

        if goodtogo():
            log.info(f"RequestsEngine._setupsession :: session good to go -- returning")
            return self._session # type: ignore


        log.info(f"""
            RequestsEngine._setupsession
            ----------------------------
            extant:
                session: {extantsession}

                headers: {extantheaders}

                cookies: {extantcookies}

                auth: {extantauth}

                persist: {extantpersist}

                config: {extantconfig}
            """)

        sessionconfig = (config or (extantconfig or SessionConfig()))
        sessionconfig = sessionconfig.cascadefromengine(self._config) # type: ignore
        sessionconfig = sessionconfig.updateheaders(extantheaders).updatecookies(extantcookies)

        log.info(f"""
            RequestsEngine._setupsession
            ----------------------------
            sessionconfig: {sessionconfig}
            """)

        rqsession = RequestsSession(
            config=sessionconfig,
            headers=extantheaders,
            cookies=extantcookies,
            auth=extantauth,
            persistence=extantpersist
        )

        return rqsession

    def _upgradesession(self, session: BaseSession) -> RequestsSession:
        """
        Upgrade a generic session to RequestsSession for compatibility.

        If the session is already a RequestsSession, returns it unchanged.
        Otherwise, creates a new RequestsSession preserving all attributes
        from the original session (headers, cookies, auth, persistence).

        Args:
            session: The session to upgrade

        Returns:
            RequestsSession instance ready for making HTTP requests
        """
        if isinstance(session, RequestsSession):
            return session
        return RequestsSession.FromGeneric(session)


    def _makerequest(self, method: HTTPMethod, url: str, usesession: t.Union[bool, BaseSession], noexec: bool = False, **kwargs: t.Any) -> t.Union[RequestModel, ResponseModel]:
        """Make HTTP request using requests library."""
        log.info(f"""
            RequestsEngine._makerequest
            ---------------------------
            (kwargs) headers = {kwargs.get('headers')}

            """)

        try:
            request = RequestModel(method=method, url=url, **kwargs)
            if usesession:
                if isinstance(usesession, BaseSession):
                    useable = self._upgradesession(usesession)
                    return useable.send(request, noexec=noexec) # use provided session directly
                return self._session.send(request, noexec=noexec)
            else:
                if noexec:
                    return request
                # direct call without session
                response = rq.request(
                    method=method.value,
                    url=url,
                    **kwargs
                )
                return ResponseModel.FromRequests(response)
        except rq.RequestException as e:
            raise RuntimeError(f"Request Failed: {e}") from e
