# ~/clientfactory/src/clientfactory/backends/elasticsearch.py
"""
...
"""
from __future__ import annotations
import urllib.parse, typing as t, json as _json

import schematix as sex
from pydantic import (
    Field as PField,
    field_validator as fieldvalidator,
    computed_field as computedfield
)

from clientfactory.core.bases import BaseBackend
from clientfactory.core.models import (
    BackendConfig, RequestModel, ResponseModel
)

from clientfactory.logs import log

class ElasticSearchConfig:
    """Configuration for ElasticSearch backend."""
    host: str = "localhost"
    port: int = 9200
    scheme: str = "http"
    username: str = ""
    password: str = ""
    apikey: str = ""
    index: str = ""
    indices: t.List[str] = PField(default_factory=list)
    doctype: str = "_doc"
    timeout: int = 30
    maxretries: int = 3
    verifycerts: bool = True
    usessl: bool = False

    @fieldvalidator('scheme')
    @classmethod
    def _validatescheme(cls, v: str) -> str:
        """Validate scheme is http or https"""
        if v.lower() not in ('http', 'https'):
            raise ValueError()
        return v.lower()

    @computedfield
    def baseurl(self) -> str:
       """Get the formatted Base URL."""
       return f"{self.scheme}://{self.host}:{self.port}"
