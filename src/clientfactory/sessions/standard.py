# ~/clientfactory/src/clientfactory/sessions/standard.py
"""
Standard Session Implementation
------------------------------
Basic session implementation with minimal processing.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models import RequestModel, ResponseModel
from clientfactory.core.bases.session import BaseSession

class StandardSession(BaseSession):
    """
    Standard session implementation.

    Provides basic request/response handling without additional processing.
    Good for simple use cases and testing.
    """

    def _preparerequest(self, request: RequestModel) -> RequestModel:
        """
        Standard request preparation.

        Applies any default headers or session-level configuration.
        """
        prepared = request

        # apply default headers if configured
        if self._config.defaultheaders:
            newheaders = self._config.defaultheaders.copy()
            newheaders.update(prepared.headers)
            prepared = prepared.withheaders(newheaders)

        # apply default cookies if configured
        if self._config.defaultcookies:
            newcookies = self._config.defaultcookies.copy()
            newcookies.update(prepared.cookies)
            prepared = prepared.withcookies(newcookies)

        return prepared

    def _processresponse(self, response: ResponseModel) -> ResponseModel:
        """
        Standard response processing.

        Basic response handling without modification.
        """
        # return as is for standard session
        # concrete sessions might add logging, caching, etc
        return response
