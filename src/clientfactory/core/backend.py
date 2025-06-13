# ~/clientfactory/src/clientfactory/core/backend.py
"""
Concrete Backend Implementation
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models import RequestModel, ResponseModel
from clientfactory.core.bases import BaseBackend

class Backend(BaseBackend):
    """Standard concrete backend implementation for REST APIs."""

    def _formatrequest(self, request: RequestModel, data: t.Dict[str, t.Any]) -> RequestModel:
        if not data:
            return request

        if request.method.value == 'GET':
            return request.withparams(data)

        elif request.method.value in ('POST', 'PUT', 'PATCH'):
            return request.model_copy(update={'json': data})

        return request

    def _processresponse(self, response: ResponseModel) -> t.Any:
        if response.ok:
            try:
                return response.json()
            except:
                return response.text
        return response
