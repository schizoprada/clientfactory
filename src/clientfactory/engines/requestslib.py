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


from clientfactory.core.bases import BaseEngine, BaseSession
from clientfactory.core.models import (
    HTTPMethod, RequestModel, ResponseModel,
    EngineConfig, SessionConfig
)

from clientfactory.logs import log

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

        # Apply session config to requests.Session
        if self._config.defaultheaders:
            session.headers.update(self._config.defaultheaders)

        if self._config.defaultcookies:
            session.cookies.update(self._config.defaultcookies)

        # Configure adapters for retries if needed
        if self._config.maxretries > 0:
            adapter = HTTPAdapter(max_retries=self._config.maxretries)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

        return session

    def _preparerequest(self, request: RequestModel) -> RequestModel:
        """Apply session-level defaults to request."""
        # Session headers/cookies should already be on self._obj
        log.info(f"RequestsSession._preparerequest: request.headers = {request.headers}")
        log.info(f"RequestsSession._preparerequest: self._obj.headers = {self._obj.headers}")
        return request

    def _makerequest(self, request: RequestModel) -> ResponseModel:
        """Execute request using requests.Session"""
        log.info(f"RequestsSession._makerequest: request.headers (before tokwargs) = {request.headers}")
        kwargs = request.tokwargs()
        log.info(f"RequestsSession._makerequest: kwargs headers = {kwargs.get('HEADERS', 'NOTSET')}")

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

class RequestsEngine(BaseEngine):
    """
    HTTP engine implementation using requests library.

    Default engine for ClientFactory with full feature support.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


    def _setupsession(self, config: t.Optional[SessionConfig] = None) -> RequestsSession:
        """Create RequestsSession with config cascade, upgrading provided sessions if needed."""
        log.debug(f"RequestsEngine._setupsession: called with config={config}")
        log.debug(f"RequestsEngine._setupsession: self._session exists = {hasattr(self, '_session')}")
        if hasattr(self, '_session'):
            log.debug(f"RequestsEngine._setupsession: self._session = {self._session} (type: {type(self._session)})")

        sessionprovided = lambda: hasattr(self, '_session') and self._session
        needsupgrade = lambda: sessionprovided() and not isinstance(self._session, RequestsSession)
        goodtogo = lambda: sessionprovided() and isinstance(self._session, RequestsSession)

        log.debug(f"RequestsEngine._setupsession: sessionprovided = {sessionprovided()}")
        log.debug(f"RequestsEngine._setupsession: needsupgrade = {needsupgrade()}")
        log.debug(f"RequestsEngine._setupsession: goodtogo = {goodtogo()}")

        if needsupgrade():
            log.debug(f"RequestsEngine._setupsession: upgrading session")
            # Upgrade existing session to RequestsSession
            extantsession = self._session
            log.debug(f"RequestsEngine._setupsession: extantsession = {extantsession}")
            extantconfig = extantsession._config
            log.debug(f"RequestsEngine._setupsession: extantconfig = {extantconfig}")
            extantauth = getattr(extantsession, '_auth', None)
            log.debug(f"RequestsEngine._setupsession: extantauth = {extantauth}")
            extantpersist = getattr(extantsession, '_persistence', None)
            log.debug(f"RequestsEngine._setupsession: extantpersist = {extantpersist}")

            sessionconfig = config or extantconfig
            sessionconfig = sessionconfig.cascadefromengine(self._config)
            log.debug(f"RequestsEngine._setupsession: final sessionconfig = {sessionconfig}")

            rqsession = RequestsSession(config=sessionconfig)
            log.debug(f"RequestsEngine._setupsession: created new RequestsSession = {rqsession}")

            if extantauth:
                rqsession._auth = extantauth
                log.debug(f"RequestsEngine._setupsession: transferred auth to new session")
            if extantpersist:
                rqsession._persistence = extantpersist
                log.debug(f"RequestsEngine._setupsession: transferred persistence to new session")

            log.debug(f"RequestsEngine._setupsession: returning upgraded session = {rqsession}")
            return rqsession

        elif goodtogo():
            log.debug(f"RequestsEngine._setupsession: session already good, returning existing")
            # Already is RequestsSession
            return self._session # type: ignore

        else:
            log.debug(f"RequestsEngine._setupsession: creating new RequestsSession")
            # No session provided, create new
            sessionconfig = (config or SessionConfig())
            sessionconfig = sessionconfig.cascadefromengine(self._config)
            log.debug(f"RequestsEngine._setupsession: new sessionconfig = {sessionconfig}")
            new_session = RequestsSession(config=sessionconfig)
            log.debug(f"RequestsEngine._setupsession: created new session = {new_session}")
            return new_session


    def _makerequest(self, method: HTTPMethod, url: str, usesession: bool, noexec: bool = False, **kwargs: t.Any) -> ResponseModel:
        """Make HTTP request using requests library."""
        try:
            if usesession:
                request = RequestModel(method=method, url=url, **kwargs)
                return self._session.send(request)
            else:
                # direct call without session
                response = rq.request(
                    method=method.value,
                    url=url,
                    **kwargs
                )
                return ResponseModel.FromRequests(response)
        except rq.RequestException as e:
            raise RuntimeError(f"Request Failed: {e}") from e
