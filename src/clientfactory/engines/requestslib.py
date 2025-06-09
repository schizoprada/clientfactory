# ~/clientfactory/src/clientfactory/engines/requestslib.py
"""
Requests Engine Implementation
-----------------------------
HTTP engine implementation using the requests library.
"""
from __future__ import annotations
import typing as t

import requests as rq

from clientfactory.core.protos import AuthProtocol
from clientfactory.core.bases import BaseEngine, BaseSession
from clientfactory.core.models import HTTPMethod, ResponseModel, SessionConfig, EngineConfig

class RequestsSession(BaseSession):
    """..."""
    def __init__(self, engineconfig: t.Optional[EngineConfig] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._obj = self._setup(engineconfig)

    def _setup(self, engineconfig: t.Optional[EngineConfig] = None) -> rq.Session:


class RequestsEngine(BaseEngine):
    """
    HTTP engine implementation using requests library.

    Default engine for ClientFactory with full feature support.
    """
    def __init__(
        self,
        **kwargs: t.Any
    ) -> None:
        """Initialize requests engine"""
        super().__init__(**kwargs)

    def _setupsession(self) -> RequestsSession:
        """"""



    def _makerequest(self, method: HTTPMethod, url: str, **kwargs: t.Any) -> ResponseModel:
        """Make HTTP request using requests library."""
        try:
            response = self._session.request(
                method=method.value,
                url=url,
                **kwargs
            )
            return ResponseModel.FromRequests(response)
        except rq.RequestException as e:
            raise RuntimeError(f"Request failed: {e}") from e

    def close(self) -> None:
        if hasattr(self, '_session'):
            self._session.close()
        super().close()
