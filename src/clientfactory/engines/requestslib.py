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
        return request

    def _makerequest(self, request: RequestModel) -> ResponseModel:
        """Execute request using requests.Session"""
        kwargs = request.tokwargs()

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
        """Create RequestsSession with config cascade."""
        sessionconfig = (config or SessionConfig())
        sessionconfig = sessionconfig.cascadefromengine(self._config)
        return RequestsSession(config=sessionconfig)


    def _makerequest(self, method: HTTPMethod, url: str, usesession: bool, **kwargs: t.Any) -> ResponseModel:
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
