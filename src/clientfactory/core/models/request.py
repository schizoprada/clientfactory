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

from pydantic.types import constr
import schematix as sex

from clientfactory.core.protos import PayloadProtocol
from clientfactory.core.models.enums import HTTPMethod
from clientfactory.core.models.config import PayloadConfig
from clientfactory.logs import log

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
        log.info(f"RequestModel.withheaders: current = {self.headers}")
        log.info(f"RequestModel.withheaders: new = {headers}")
        new = self.headers.copy()
        new.update(headers)
        log.info(f"RequestModel.withheaders: after updating = {new}")
        return self.model_copy(update={"headers": new})

    def withauth(self, header: str, value: str) -> RequestModel:
        """Return new request with authentication header added."""
        return self.withheaders({header: value})

    def withcookies(self, cookies: t.Dict[str, str]) -> RequestModel:
        """Return a new request with additional cookies"""
        new = self.cookies.copy()
        new.update(cookies)
        return self.model_copy(update={"cookies": new})

    def tokwargs(self, **updates) -> t.Dict:
        """Convert to kwargs for BaseEngine"""
        kwargs = {
            'headers': self.headers,
            'params': self.params,
            'cookies': self.cookies,
            'timeout': self.timeout,
            'allow_redirects': self.allowredirects,
            'verify': self.verifyssl
        }
        #print(f"DEBUG | initial kwargs: {kwargs}")
        #print(f"DEBUG | received updates: {updates}")
        if self.json is not None:
            kwargs['json'] = self.json
        elif self.data is not None:
            kwargs['data'] = self.data

        if self.files is not None:
            kwargs['files'] = self.files

        kwargs.update(updates)
        #print(f"DEBUG | final kwargs: {kwargs}")
        return kwargs

    def toexecutable(self, engine: t.Any) -> 'ExecutableRequest':
        """Convert this request to an executable request."""
        if engine is None: raise ValueError()
        constructs = self.model_dump()
        constructs['engine'] = engine
        return ExecutableRequest(**constructs)

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

    @fieldvalidator('method', mode='before')
    @classmethod
    def _validatemethod(cls, v: t.Union[str, HTTPMethod]) -> HTTPMethod:
        if isinstance(v, HTTPMethod):
            return v
        try:
            return HTTPMethod(v.upper())
        except Exception as e:
            raise ValueError(f"Invalid HTTP Method '{v}'")

    ## dunders ##
    def __hash__(self) -> int:
        """Generate hash based on request signature"""
        headers = tuple(sorted(self.headers.items()))
        cookies = tuple(sorted(self.cookies.items()))
        params = tuple(sorted(self.params.items()))
        _json = str(self.json) if self.json else None
        data = str(self.data) if self.data else None,
        return hash((
            self.method,
            self.url,
            headers,
            cookies,
            params,
            _json,
            data,
            self.timeout
        ))

    def __eq__(self, other: t.Any) -> bool:
        """Check equality based on request signature"""
        if not isinstance(other, RequestModel):
            return False
        return all((
            self.method == other.method,
            self.url == other.url,
            self.headers == other.headers,
            self.params == other.params,
            self.json == other.json,
            self.data == other.data,
            self.cookies == other.cookies,
            self.timeout == other.timeout
        ))

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
    def FromRequests(cls, response: 'rq.Response', request: t.Optional[RequestModel] = None) -> ResponseModel:
        """Create a ResponseModel from requests.Response"""
        return cls(
            statuscode=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=response.url,
            cookies=dict(response.cookies),
            elapsedtime=response.elapsed.total_seconds(),
            request=request
        )

class ExecutableRequest(RequestModel):
    """..."""
    engine: t.Any

    @fieldvalidator('engine')
    @classmethod
    def _validateengine(cls, v: t.Any) -> t.Any:
        from clientfactory.core.bases.engine import BaseEngine
        if not isinstance(v, BaseEngine):
            raise ValueError(f"'engine' must be a BaseEngine type.")
        return v

    def __call__(self) -> ResponseModel:
        """Execute this request with the provided engine."""
        return self.engine.send(self, noexec=False)


from clientfactory.core.utils.typed import UNSET

class Param(sex.Field):
    """
    ClientFactory parameter built on schematix Field.

    Extends schematix field capabilities with clientfactory-specific
    functionality for API parameter handling.
    """
    __constructs__ = sex.BaseField.__constructs__ | {'allownone'}

    def __init__(
        self,
        name: t.Optional[str] = None,
        required: bool = UNSET[False],
        default: t.Any = None,
        transform: t.Optional[t.Callable] = None,
        source: t.Optional[str] = None,
        target: t.Optional[str] = None,
        type: t.Optional[t.Type] = None,
        choices: t.Optional[t.List[t.Any]] = None,
        mapping: t.Optional[t.Dict] = None,
        mapper: t.Optional[t.Callable] = None,
        keysaschoices: bool = UNSET[True],
        valuesaschoices: bool = UNSET[False],
        transient: bool = UNSET[False],
        conditional: bool = UNSET[False],
        dependencies: t.Optional[t.List[str]] = None,
        conditions: t.Optional[t.Dict[str, t.Callable]] = None,
        validator: t.Optional[t.Callable] = None,
        selfdependent: bool = False,
        allownone: bool = True,
        **kwargs: t.Any
    ) -> None:
        """Initialize parameter with clientfactory extensions."""
        self._explicit: set[str] = set()

        constructing = {
            'name': name,
            'required': required,
            'default': default,
            'transform': transform,
            'source': source,
            'target': target,
            'type': type,
            'choices': choices,
            'mapping': mapping,
            'mapper': mapper,
            'keysaschoices': keysaschoices,
            'valuesaschoices': valuesaschoices,
            'transient': transient,
            'conditional': conditional,
            'dependencies': dependencies,
            'conditions': conditions,
            'validator': validator,
            'selfdependent': selfdependent,
            'allownone': allownone
        }

        # track explicit attrs before resolution
        for attr, value in constructing.items():
            if (value is not UNSET) and (value is not None):
                self._explicit.add(attr)

        # resolve class attributes or remove if unset
        for attr in sex.BaseField.__constructs__:
            if (constructing[attr] is None) or (constructing[attr] is UNSET):
                if hasattr(self.__class__, attr):
                    cval = getattr(self.__class__, attr)
                    if cval is not None:
                        constructing[attr] = cval
                        self._explicit.add(attr) # class attrs count as explicit
                    else:
                        del constructing[attr]
                else:
                    del constructing[attr]

        super().__init__(
            **constructing,
            **kwargs
        )
        self.allownone: bool = allownone

    def __set_name__(self, owner, name):
        """Called when Param is assigned to a class attribute."""
        # This is called by the metaclass with the actual attribute name
        if self.name is None:
            self.name = name

        if self.source is None:
            self.source = self.name

        # Now set target default if not specified
        if self.target is None:
            self.target = self.name

        # Call parent if it exists
        if hasattr(super(), '__set_name__'):
            super().__set_name__(owner, name) # type: ignore

    def _availablevalues(self) -> list:
        """Get available values for this parameter from its metadata."""
        if self.mapping:
            return list(self.mapping.keys())
        if self.choices:
            return list(self.choices)
        return []

    def __rshift__(self, other: 'Param') -> 'Param': # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Merge with another Param, prioritizing self's attributes.

        Returns a new Param with attributes from both, where self's
        non-None values take precedence in conflicts.

        Example:
            p1 >> p2  # p1's values win where both are defined
        """
        def pick(a: str) -> t.Any:
            if a in self._explicit:
                return getattr(self, a, None)
            elif a in getattr(other, '_explicit', set()):
                return getattr(other, a, None)
            return None

        merged = {
            attr: pick(attr)
            for attr in self.__constructs__
            if pick(attr) is not None
        }

        return Param(**merged)

    def __lshift__(self, other: 'Param') -> 'Param':
        """
        Merge with another Param, prioritizing other's attributes.

        Returns a new Param with attributes from both, where other's
        non-None values take precedence in conflicts.

        Example:
            p1 << p2  # p2's values win where both are defined
        """
        def pick(a: str) -> t.Any:
            if a in getattr(other, '_explicit', set()):
                return getattr(other, a, None)
            elif a in self._explicit:
                return getattr(self, a, None)
            return None

        merged = {
            attr: pick(attr)
            for attr in self.__constructs__
            if pick(attr) is not None
        }

        return Param(**merged)

class BoundPayload:
    """Payload bound to specific source mappings."""
    def __init__(
        self,
        boundto: sex.core.schema.BoundSchema,
        config: PayloadConfig
    ) -> None:
        self.boundto = boundto
        self._config = config

    def serialize(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Serialize using bound schema with ClientFactory target-key behavior."""
        result = {}
        isbound = lambda field: hasattr(field, 'extractonly') and hasattr(field, 'targetfield')
        # Use the bound fields, but apply ClientFactory target-key logic
        for fieldname, field in self.boundto._boundfields.items():
            try:
                if isbound(field):
                    value = field.extractonly(data) # type: ignore
                    field.targetfield.assign(result, value) # type: ignore
                else:
                    value = field.extract(data)
                    field.assign(result, value)
            except Exception as e:
                raise ValueError(f"Bound transform failed on field '{fieldname}': {e}")

        return result

    def paramnames(self) -> t.List[str]:
        """List all paramater names registered in this payload."""
        return list(self.boundto._boundfields.keys())


class Payload(sex.Schema): #! PayloadProtocol removed
    """
    Abstract base class for request payload handling.

    Extends schematix Schema with ClientFactory-specific functionality.
    Gets automatic field discovery via SchemaMeta metaclass.
    """

    def __init__(
        self,
        config: t.Optional[PayloadConfig] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize payload with configuration."""
        super().__init__(**kwargs)
        self._config: PayloadConfig = (config or PayloadConfig(**kwargs))
        self._assigntargets()

    def _assigntargets(self) -> None:
        """Fix field targets after SchemaMeta has set names but before target defaulting"""
        isbound = lambda field: hasattr(field, 'extractonly') and hasattr(field, 'targetfield')
        for fieldname, field in self._fields.items():
            if isbound(field):
                continue
            if hasattr(field, 'target') and field.target is None:
                field.target = field.name

    ## inheritance overrides ##
    def transform(self, data: t.Any, typetarget: t.Optional[t.Type] = None) -> t.Any:
        """Transform data using schematix with PayloadProtocol compatibility."""
        from schematix.core.deps import DependencyResolver

        # use schematix built-in transform to handle conditional fields
        resolver = DependencyResolver(self._fields)
        execorder = resolver.resolveorder()

        computed = {}
        result = {}
        isbound = lambda field: hasattr(field, 'extractonly') and hasattr(field, 'targetfield')
        allowsnone = lambda field: hasattr(field, 'allownone') and getattr(field, 'allownone', True)
        # process fields in dependency order
        for fieldname in execorder:
            field = self._fields[fieldname]
            try:
                if isbound(field):
                    value = field.extractonly(data) # type: ignore
                    computed[fieldname] = value
                    if not field.transient:
                        if (value is None) and (not allowsnone(field)): # skip fields with none values if they dont allow it
                            continue
                        field.targetfield.assign(result, value) # type: ignore
                else:
                    value = field.extract(data, computed)
                    computed[fieldname] = value
                    if not field.transient:
                        if (value is None) and (not allowsnone(field)):
                            continue
                        field.assign(result, value)
            except Exception as e:
                raise ValueError(f"Transform failed on field '{fieldname}': {e}")

        if typetarget is not None:
            return self._typeconvert(result, typetarget)
        return result

    def bind(self, mapping: t.Dict[str, t.Any]) -> BoundPayload: # type: ignore
        boundschema = super().bind(mapping)

        # perserve original targets in bound fields
        for fieldname, boundfield in boundschema._boundfields.items():
            if fieldname in self._fields:
                original = self._fields[fieldname]
                if hasattr(original, 'target') and original.target:
                    boundfield.target = original.target

        return BoundPayload(boundto=boundschema, config=self._config)

    def validate(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        return self.transform(data)

    def serialize(self, data: t.Dict[str, t.Any]) -> t.Union[str, bytes, t.Dict[str, t.Any]]:
        """Serialize validated data using schematix transform."""
        return self.transform(data)

    def getschema(self) -> t.Dict[str, t.Any]:
        """Get payload schema definition."""
        schema = {}
        for name, field in self._fields.items():
            schema[name] = {
                'name': field.name,
                'required': field.required,
                'default': field.default,
                'source': field.source,
                'target': field.target
            }
        return schema

    def getconfig(self) -> PayloadConfig:
        """Get payload configuration."""
        return self._config

    def paramnames(self) -> t.List[str]:
        """List all paramater names registered in this payload."""
        return list(self._fields.keys())
