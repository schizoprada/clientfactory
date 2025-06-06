# ~/clientfactory/src/clientfactory/core/models/request.py
"""
Request and Response Models
---------------------------
Core data structures for HTTP requests and responses using Pydantic.
"""
from __future__ import annotations
import typing as t
from urllib.parse import urljoin, urlparse, urlunparse

from pydantic import (
    BaseModel as PydModel,
    Field,
    field_validator as fieldvalidator,
    computed_field as computedfield
)

from clientfactory.core.models.enums import HTTPMethod

if t.TYPE_CHECKING:
    import requests as rq



class RequestModel(PydModel):
    """
    HTTP Request representation.

    Immutable request object that contains all data needed to make an HTTP request.
    """
    method: HTTPMethod
    url: str
    headers: t.Dict[str, str] = Field(default_factory=dict)
    params: t.Dict[str, t.Any] = Field(default_factory=dict)
    json: t.Optional[t.Dict[str, t.Any]] = None # type: ignore[override]
    data: t.Optional[t.Union[str, bytes, t.Dict[str, t.Any]]] = None
    files: t.Optional[t.Dict[str, t.Any]] = None
    cookies: t.Dict[str, str] = Field(default_factory=dict)
    timeout: t.Optional[float] = None
    allowredirects: bool = True
    verifyssl: bool = True

    # metadata for debugging & processing
    context: t.Dict[str, t.Any] = Field(default_factory=dict)

    # pydantic model config
    model_config = {"frozen": True}

    def model_post_init(self, __context: t.Any) -> None:
        """Validate request after creation."""
        if (self.json is not None) and (self.data is not None):
            raise ValueError(f"Cannot specify both 'json' and 'data'")

        if (self.method == HTTPMethod.GET) and (self.json or self.data):
            raise ValueError(f"GET requests cannot have body")
    ## pydantic tweaks ##
    def modeljson(self) -> str:
        """Serialize model to JSON string (reroutes original BaseModel.json)."""
        return super().model_dump_json()

    ## model methods ##
    def withparams(self, params: t.Dict[str, t.Any]) -> RequestModel:
        """Return new request with additional query parameters."""
        new = self.params.copy()
        new.update(params)
        return self.model_copy(update={"params": new})

    def withheaders(self, headers: t.Dict[str, str]) -> RequestModel:
        """Return new request with additional headers."""
        new = self.headers.copy()
        new.update(headers)
        return self.model_copy(update={"headers": new})

    def withauth(self, header: str, value: str) -> RequestModel:
        """Return new request with authentication header added."""
        return self.withheaders({header: value})

    def withcookies(self, cookies: t.Dict[str, str]) -> RequestModel:
        """Return a new request with additional cookies"""
        new = self.cookies.copy()
        new.update(cookies)
        return self.model_copy(update={"cookies": new})

    def tokwargs(self, **kwargs) -> t.Dict:
        """Convert to kwargs for BaseEngine"""
        updates = {
            'headers': self.headers,
            'params': self.params,
            'cookies': self.cookies,
            'timeout': self.timeout,
            'allow_redirects': self.allowredirects,
            'verify': self.verifyssl
        }
        kwargs.update(updates)
        if self.json is not None:
            kwargs['json'] = self.json
        elif self.data is not None:
            kwargs['data'] = self.data

        if self.files is not None:
            kwargs['files'] = self.files

        return kwargs

    ## computed fields ##
    @computedfield
    @property
    def hasbody(self) -> bool:
        """Check if request has a body."""
        return any((self.json, self.data, self.files))

    @computedfield
    @property
    def contenttype(self) -> t.Optional[str]:
        """Get Content-Type header value."""
        key = 'Content-Type'
        return self.headers.get(key, self.headers.get(key.lower()))

    ## field validators ##
    @fieldvalidator('url')
    @classmethod
    def _validateurl(cls, v: str) -> str:
        if not v:
            raise ValueError("URL is required")
        return v

    @fieldvalidator('timeout')
    @classmethod
    def _validatetimeout(cls, v: t.Optional[float]) -> t.Optional[float]:
        if (v is not None) and (v <= 0):
            raise ValueError("Timeout must be positive")
        return v


class ResponseModel(PydModel):
    """
    HTTP Response representation.

    Contains response data and provides methods for data extraction.
    """
    statuscode: int
    headers: t.Dict[str, str]
    content: bytes
    url: str

    ## optional parsed content ##
    jsondata: t.Optional[t.Any] = None
    textdata: t.Optional[str] = None

    ## original request ##
    request: t.Optional[RequestModel] = None

    ## response metadata ##
    elapsedtime: t.Optional[float] = None
    cookies: t.Dict[str, str] = Field(default_factory=dict)

    ## pydantic tweaks ##
    def modeljson(self) -> str:
        """Serialize model to JSON string (reroutes original BaseModel.json)."""
        return super().model_dump_json()

    ## computed fields ##
    @computedfield
    @property
    def ok(self) -> bool:
        """Check if response indicates success (2xx status)."""
        return (200 <= self.statuscode < 300)

    @computedfield
    @property
    def text(self) -> str:
        """Get response content as text."""
        if self.textdata is None:
            self.textdata = self.content.decode('utf-8')
        return self.textdata

    ## model methods ##
    def json(self) -> t.Any: # type: ignore[override]
        """Parse response content as JSON."""
        if self.jsondata is None:
            import json as _json
            try:
                object.__setattr__(self, 'jsondata', _json.loads(self.text))
            except _json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in response: {e}")
        return self.jsondata

    def raiseforstatus(self) -> None:
        """Raise exception if response indicates error."""
        if not self.ok:
            raise Exception(f"HTTP {self.statuscode} Error for {self.url}")

    def extract(self, path: str, default: t.Any = None) -> t.Any:
        """
        Extract value from response using dot notation.

        Examples:
            response.extract("data.items[0].name")  # JSON path
            response.extract("headers.content-type")  # Header value
        """
        try:
            if path.startswith("headers."):
                header = path[8:]
                return self.headers.get(header, default)

            # assume JSON path for everything else
            data = self.json()
            parts = path.split('.')

            for part in parts:
                if ('[' in part) and (']' in part):
                    # handle array access
                    key, idxstr = part.split('[', 1)
                    idx = int(idxstr.rstrip(']'))
                    if key:
                        data = data[key]
                    data = data[idx]
                else:
                    data = data[part]

            return data
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            import warnings
            warnings.warn(f"") # add warning
            return default

    ## class methods ##
    @classmethod
    def FromRequests(cls, response: 'rq.Response') -> ResponseModel:
        """Create a ResponseModel from requests.Response"""
        return cls(
            statuscode=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=response.url,
            cookies=dict(response.cookies),
            elapsedtime=response.elapsed.total_seconds()
        )
