# ~/clientfactory/src/clientfactory/core/session.py
"""
Concrete Session Implementation
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models import RequestModel, ResponseModel
from clientfactory.core.bases import BaseSession

class Session(BaseSession):
    """Standard concrete session implementation."""

    def _setup(self) -> t.Any:
        obj = {
            'headers': self._headers.copy(),
            'cookies': self._cookies.copy()
        }
        self._loadpersistentstate()

        if self._initializer:
            obj = self._initializer.initialize(obj)

        return obj

    def _cleanup(self) -> None:
        self._savepersistentstate()

    def _preparerequest(self, request: RequestModel, noexec: bool = False) -> RequestModel:

        if self._obj['headers']:
            request = request.withheaders(self._obj['headers'])

        if self._obj['cookies']:
            request = request.withcookies(self._obj['cookies'])

        return request

    def _makerequest(self, request: RequestModel, noexec: bool = False) -> ResponseModel:
        raise NotImplementedError(f"Session should not make requests directly - use engine")

    def _processresponse(self, response: ResponseModel) -> ResponseModel:
        if response.cookies:
            self._obj['cookies'].update(response.cookies)
        return response
