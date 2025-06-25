# ~/clientfactory/src/clientfactory/core/models/request.py
"""
Request and Response Models
---------------------------
Core data structures for HTTP requests and responses using Pydantic.
"""
from __future__ import annotations
import inspect, typing as t
from urllib.parse import urljoin, urlparse, urlunparse

from pydantic import (
    BaseModel as PydModel,
    Field,
    field_validator as fieldvalidator,
    computed_field as computedfield
)

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

_UNSET: t.Any = object() # Sentinel for Param defaults

class Param(sex.Field):
    """
    ClientFactory parameter built on schematix Field.

    Extends schematix field capabilities with clientfactory-specific
    functionality for API parameter handling.
    """
    __defaults__ = {**sex.Field.__defaults__, 'allownone': True}

    def __init__(
        self,
        name: t.Optional[str] = _UNSET,
        source: t.Optional[str] = _UNSET,
        target: t.Optional[str] = _UNSET,
        required: bool = _UNSET,
        default: t.Any = _UNSET,
        transform: t.Optional[t.Callable] = _UNSET,
        type: t.Optional[t.Type] = _UNSET,
        choices: t.Optional[t.List[t.Any]] = _UNSET,
        mapping: t.Optional[t.Dict] = _UNSET,
        mapper: t.Optional[t.Callable] = _UNSET,
        keysaschoices: bool = _UNSET,
        valuesaschoices: bool = _UNSET,
        transient: bool = _UNSET,
        conditional: bool = _UNSET,
        dependencies: t.Optional[t.List[str]] = _UNSET,
        conditions: t.Optional[t.Dict[str, t.Callable]] = _UNSET,
        allownone: bool = _UNSET,
        **kwargs: t.Any
    ) -> None:
        """Initialize parameter with clientfactory extensions."""
        # apply real defaults for unset values
        explicit = set()
        locs = locals().copy()
        for pname, dvalue in self.__defaults__.items():
            if (pname in locs) and (locs[pname] is _UNSET):
                locs[pname] = dvalue
            else:
                explicit.add(pname)
        explicit.update(kwargs.keys())

        # resolve class attrs before calling super
        shouldresolve = lambda key: (key not in ('self', 'kwargs', 'shouldresolve')) and (not key.startswith('_'))
        resolvable = {k:v for k, v in locs.items() if (v is not _UNSET) and shouldresolve(k)}
        resolved = self._resolveclassattrs(**resolvable)
        super().__init__(
            **resolved
        )
        self.allownone: bool = locs['allownone']
        self._explicit: set = explicit # store explicit params for use in __rshift__/__lshift__
        self._initializedwith['allownone'] = allownone

    def _resolveclassattrs(self, **resolve) -> t.Dict[str, t.Any]:
        """
        Resolve class-level attributes into instance initialization.

        Precedence order:
        1. User-provided explicit kwargs (different from defaults) - highest
        2. Class attributes - middle
        3. Parameter defaults - lowest

        Returns:
            Updated kwargs dictionary with resolved class attributes.
        """
        filtered = {k:v for k,v in resolve.items() if k not in ('self', 'kwargs') or not k.startswith('_')}
        defaults = {
            n: p.default
            for n, p in inspect.signature(self.__init__).parameters.items()
            if p.default is not inspect.Parameter.empty
        }

        explicit = {key for key in resolve.keys()}.union({name for name, value in filtered.items() if (name in defaults) and (value != defaults[name])})
        resolvable = {
            k: v
            for k,v in filtered.items()
            if (
                v is not None and
                (
                    k not in defaults or
                    v != defaults[k]
                )
            )
        }
        if hasattr(self.__class__, '_classattrs'):
            # Start with class attributes, then update with explicit kwargs
            resolved = self.__class__._classattrs.copy()
            resolved.update(resolvable)
            return resolved
        return filtered

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Capture class-level field attributes during class definition.

        Scans the class for attributes that match field construct names and stores
        them for later resolution during instance initialization. Excludes private
        attributes and handles callable attributes appropriately.
        """
        super().__init_subclass__(**kwargs)
        verify = lambda name: (not name.startswith('_')) and (name in cls.__constructs__)
        validate = lambda name, value: (value is not None) and (not callable(value) or name in ['transform', 'mapper'])
        cls._classattrs = {
            name: getattr(cls, name, None)
            for name in dir(cls)
            if verify(name) and validate(name, getattr(cls, name, None))
        }

    def __set_name__(self, owner, name):
        """Called when Param is assigned to a class attribute."""
        # This is called by the metaclass with the actual attribute name
        if self.name is None:
            self.name = name

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

    def _getoriginalvalue(self, attr: str) -> t.Any:
        """Get the original value before BaseField mangled it."""
        if attr in self._explicit:
            return self._initializedwith[attr]
        return self.__defaults__[attr]

    def __rshift__(self, other: 'Param') -> 'Param': # pyright: ignore[reportIncompatibleMethodOverride]
        """
        Override with other's explicit values only.

        Usage: base >> override
        Result: base values, but override with other's explicitly set values
        """
        # Start with ALL of self's values
        new = {
            attr: self._getoriginalvalue(attr) for attr in self.__defaults__.keys()
        }

        print(f"""
            DEBUG
            Param.__rshift__
            -----------------
               new:
                   {new}

               other._explicit:
                    {other._explicit}
            """)

        updates = {
            attr: other._getoriginalvalue(attr) for attr in other._explicit
        }

        print(f"""
            DEBUG
            Param.__rshift__
            -----------------
               updates:
                   {updates}
            """)

        # Override with other's explicit values only
        new.update(updates)

        print(f"""
            DEBUG
            Param.__rshift__
            -----------------
               new(final):
                   {new}
            """)

        return Param(**new)

    def __lshift__(self, other: 'Param') -> 'Param':
        """
        Fill in missing values from other.

        Usage: sparse << defaults
        Result: sparse values, but fill gaps with other's values
        """
        # Get all non-None values from other
        new = {
            attr: other._getoriginalvalue(attr)
            for attr in other.__defaults__.keys()
        }
        print(f"""
            DEBUG
            Param.__lshift__
            -----------------
               new:
                   {new}

               other._explicit:
                    {other._explicit}
            """)

        updates = {
            attr: self._getoriginalvalue(attr)
            for attr in self._explicit
        }
        print(f"""
            DEBUG
            Param.__lshift__
            -----------------
               updates:
                   {updates}
            """)

        # Override with ALL of selfs values
        new.update(updates)
        print(f"""
            DEBUG
            Param.__lshift__
            -----------------
               new(final):
                   {new}
            """)
        final = {k:v for k,v in new.items() if v is not None}
        return Param(**new)

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
