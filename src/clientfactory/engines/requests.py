# ~/clientfactory/src/clientfactory/engines/requests.py
"""
Requests Engine Implementation
-----------------------------
HTTP engine implementation using the requests library.
"""
from __future__ import annotations
import typing as t

import requests as rq # 'Import "requests" could not be resolved from source (Pyright reportMissingModuleSource)' ? name conflict?

from clientfactory.core.bases import BaseEngine
from clientfactory.core.models import HTTPMethod, ResponseModel


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
        self._session: rq.Session = rq.Session()
        self._configrqsession(**kwargs)

    def _configrqsession(self, **kwargs: t.Any) -> None:
        if 'verify' in kwargs:
            self._session.verify = kwargs['verify']
        if 'timeout' in kwargs:
            pass # requests.Session doesnt seem to have `timeout`

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
