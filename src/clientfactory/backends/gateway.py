# ~/clientfactory/src/clientfactory/backends/gateway.py
"""
Gateway Backend Implementation
-----------------------------
Backend for APIs accessed through proxy/gateway endpoints.
"""
from __future__ import annotations
import typing as t
from urllib.parse import urlencode, quote

from clientfactory.core.bases import BaseBackend
from clientfactory.core.models import RequestModel, ResponseModel

class GatewayBackend(BaseBackend):
    """
    Backend for gateway/proxy request patterns.

    Wraps target URLs as parameters to gateway endpoints.
    Works with existing client/resource baseurl and paths.
    """
    __declaredas__: str = 'gateway'
    __declattrs__: set[str] = BaseBackend.__declattrs__ | {'gatewayurl', 'urlparam'}

    def __init__(
        self,
        gatewayurl: t.Optional[str] = None,
        urlparam: t.Optional[str] = None,
        **kwargs
    ) -> None:
        self._gatewayurl = gatewayurl or ''
        self._urlparam = urlparam or ''
        super().__init__(**kwargs)

    def _resolveattributes(self, attributes: dict) -> None:
        super()._resolveattributes(attributes)
        self._gatewayurl: str = self._gatewayurl or attributes.get('gatewayurl', '')
        self._urlparam: str = self._urlparam or attributes.get('urlparam', 'url')
        if (not self._gatewayurl) or (not self._urlparam):
            raise ValueError(f"GatewayBackend requires 'gatewayurl' and 'urlparam'")


    def _formatrequest(self, request: RequestModel, data: t.Dict[str, t.Any]) -> RequestModel:
        target = self._gatewayurl
        if data:
            qstring = urlencode(data)
            sep = '&' if '?' in target else '?'
            target += sep + qstring

        params = {self._urlparam: target}

        return RequestModel(
            method=request.method,
            url=request.url,
            params=params
        )

    def _processresponse(self, response: ResponseModel) -> t.Any:
        if response.ok:
            try:
                return response.json()
            except:
                return response.text
        return response
