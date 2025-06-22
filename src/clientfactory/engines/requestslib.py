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

        log.info(f"RequestsSession._setup: self._headers = {self._headers}")
        log.info(f"RequestsSession._setup: type(self._headers) = {type(self._headers)}")


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

        return session

    def _preparerequest(self, request: RequestModel, noexec: bool = False) -> RequestModel:
        """Apply session-level defaults to request."""
        headers = dict(self._obj.headers).copy()
        headers.update(request.headers)
        return request.withheaders(headers)

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


        if needsupgrade():
            # Upgrade existing session to RequestsSession
            extantsession = self._session
            extantconfig = extantsession._config
            extantauth = getattr(extantsession, '_auth', None)
            extantpersist = getattr(extantsession, '_persistence', None)
            extantheaders = getattr(extantsession, '_headers', {})
            extantcookies = getattr(extantsession, '_cookies', {})

            sessionconfig = config or extantconfig
            sessionconfig = sessionconfig.cascadefromengine(self._config)
            sessionconfig = sessionconfig.updateheaders(extantheaders).updatecookies(extantcookies)

            log.info(f"RequestsEngine._setupsession: sessionconfig (after cascade) = {sessionconfig}")

            rqsession = RequestsSession(config=sessionconfig)

            if extantauth:
                rqsession._auth = extantauth
            if extantpersist:
                rqsession._persistence = extantpersist

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


    def _makerequest(self, method: HTTPMethod, url: str, usesession: bool, noexec: bool = False, **kwargs: t.Any) -> t.Union[RequestModel, ResponseModel]:
        """Make HTTP request using requests library."""
        try:
            request = RequestModel(method=method, url=url, **kwargs)
            if usesession:
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
