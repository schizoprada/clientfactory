# ~/clientfactory/src/clientfactory/core/models/config.py
"""
Configuration Models
--------------------
Immutable configuration objects for clients, resources, and methods.
"""
from __future__ import annotations
import typing as t
from pathlib import Path


from pydantic import (
   BaseModel as PydModel,
   Field,
   field_validator as fieldvalidator,
   computed_field as computedfield
)

from clientfactory.core.models.enums import (
    HTTPMethod, AuthType, BackendType,
    PayloadType, SessionType, EngineType,
    ToleranceType
)

if t.TYPE_CHECKING:
    from clientfactory.core.protos import (
        AuthProtocol, BackendProtocol, PayloadProtocol,
        RequestEngineProtocol, SessionProtocol
    )
    from clientfactory.core.bases.resource import BaseResource

#! TODO:
## consolidate validators

class PayloadConfig(PydModel):
    """..."""
    ...

class MethodConfig(PydModel):
    """Configuration for a resource method"""
    name: str
    method: HTTPMethod
    path: t.Optional[str] = None

    ## processing hooks ##
    preprocess: t.Optional[t.Callable] = None
    postprocess: t.Optional[t.Callable] = None

    ## data handling ##
    payload: t.Optional['PayloadProtocol'] = None

    ## metadata ##
    description: str = ""
    tags: t.List[str] = Field(default_factory=list)

    ## pydantic configs ##
    model_config= {"frozen": True}

    def model_post_init(self, __context: t.Any, /) -> None:
        if (self.method == HTTPMethod.GET) and self.payload:
            raise ValueError("GET methods should not have payloads")

    ## field validators ##
    @fieldvalidator('name')
    @classmethod
    def _vlaidatename(cls, v: str) -> str:
        if not v:
            raise ValueError("Method name is required")
        return v

class ResourceConfig(PydModel):
   """Configuration for a resource."""
   name: str
   path: str = ""

   ## method registry ##
   methods: t.Dict[str, MethodConfig] = Field(default_factory=dict)

   ## child resources ##
   children: t.Dict[str, ResourceConfig] = Field(default_factory=dict)

   ## processing ##
   backend: t.Optional['BackendProtocol'] = None
   payload: t.Optional['PayloadProtocol'] = None

   ## hierarchy ##
   parent: t.Optional[ResourceConfig] = None

   ## metadata ##
   description: str = ""
   tags: t.List[str] = Field(default_factory=list)

   ## pydantic model config ##
   model_config = {"frozen": True}

   def model_post_init(self, __context: t.Any) -> None:
       """Set parent reference on children."""
       for child in self.children.values():
           if child.parent is None:
               object.__setattr__(child, 'parent', self)

   ## model methods ##
   def getmethod(self, name: str) -> t.Optional[MethodConfig]:
       """Get method configuration by name."""
       return self.methods.get(name)

   def getchild(self, name: str) -> t.Optional[ResourceConfig]:
       """Get child resource configuration by name."""
       return self.children.get(name)

   ## computed fields ##
   @computedfield
   @property
   def fullpath(self) -> str:
       """Get full path including parent paths."""
       paths = []
       current = self

       while current:
           if current.path:
               paths.append(current.path.strip('/'))
           current = current.parent

       paths.reverse()
       return '/' + '/'.join(paths) if paths else '/'

   ## field validators ##
   @fieldvalidator('name')
   @classmethod
   def _validatename(cls, v: str) -> str:
       if not v:
           raise ValueError("Resource name is required")
       return v

class ClientConfig(PydModel):
    """Configuration for a client."""
    baseurl: str = ""

    ## component configuration ##
    engine: t.Optional['RequestEngineProtocol'] = None
    auth: t.Optional['AuthProtocol'] = None
    backend: t.Optional['BackendProtocol'] = None
    sessiontype: SessionType = SessionType.STANDARD

    ## default request settings ##
    timeout: float = 30.0
    verifyssl: bool = True
    allowredirects: bool = True

    ## default headers and cookies ##
    headers: t.Dict[str, str] = Field(default_factory=dict)
    cookies: t.Dict[str, str] = Field(default_factory=dict)

    ## resource registry ##
    resources: t.Dict[str, 'BaseResource'] = Field(default_factory=dict)

    ## metadata ##
    name: str = ""
    version: str = "1.0.0" #! implement semver string type for later
    description: str = ""

    ## configuration inheritance behavior ##
    cascade: bool = True

    ## pydantic configs ##
    model_config = {"frozen": True}

    ## model methods ##
    def getresource(self, name: str) -> t.Optional['BaseResource']:
        """Get resource instance by name"""
        return self.resources.get(name)

    def withbaseurl(self, baseurl: str) -> ClientConfig:
        """Return new config with different base URL."""
        return self.model_copy(update={"baseurl": baseurl})

    def withauth(self, auth: 'AuthProtocol') -> ClientConfig:
        """Return new config with different auth."""
        return self.model_copy(update={"auth": auth})

    def withheaders(self, headers: t.Dict[str, str]) -> ClientConfig:
        """Return new config with additional headers."""
        new = self.headers.copy()
        new.update(headers)
        return self.model_copy(update={"headers": new})

    ## field validators ##
    @fieldvalidator('timeout')
    @classmethod
    def _validatetimeout(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @fieldvalidator('baseurl')
    @classmethod
    def _validatebaseurl(cls, v: str) -> str:
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError("Base URL must start with http:// or https://")
        return v

class DeclarableConfig(PydModel):
    """..."""
    @classmethod
    def FromDeclarations(cls, declared: dict, **overrides: t.Any) -> t.Self:
        """Create config from declarative values with optional overrides."""
        merged = declared.copy()
        merged.update(overrides)
        return cls(**merged)

class SessionConfig(DeclarableConfig):
    """Configuration for session behavior."""
    ## connection settings ##
    timeout: float = 30.0
    verifyssl: bool = True
    allowredirects: bool = True
    maxredirects: int = 10

    ## retry settings ##
    maxretries: int = 3
    retrybackoff: float = 1.0

    ## connection pooling ##
    poolconnections: int = 10
    poolmaxsize: int = 10

    ## state management ##
    persistcookies: bool = False
    cookiefile: t.Optional[str] = None

    ## headers and cookies ##
    defaultheaders: t.Dict[str, str] = Field(default_factory=dict)
    defaultcookies: t.Dict[str, str] = Field(default_factory=dict)

    ## pydantic model config ##
    model_config = {"frozen": True}

    ## field validators ##
    @fieldvalidator('timeout')
    @classmethod
    def _validatetimeout(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @fieldvalidator('maxretries')
    @classmethod
    def _validatemaxretries(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Max retries cannot be negative")
        return v

    @fieldvalidator('maxredirects')
    @classmethod
    def _validatemaxredirects(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Max redirects cannot be negative")
        return v

    def cascadefromengine(self, engineconfig: 'EngineConfig') -> 'SessionConfig':
        if not engineconfig.cascade:
            return self

        # Only apply overrides where current value matches default

        overrides = engineconfig.sessionoverrides()
        updates = {}
        defaults = SessionConfig()

        for k,v in overrides.items():
            if hasattr(self, k) and hasattr(defaults, k):
                current = getattr(self, k)
                default = getattr(defaults, k)

                if current == default:
                    updates[k] = v

        if not updates:
            return self

        return self.model_copy(update=updates)

class EngineConfig(DeclarableConfig):
    """Configuration for request engines."""
    verify: bool = True
    timeout: t.Optional[float] = None
    # add more later

    cascade: bool = True # whether to cascade values to dependant component configurations

    ## pydantic model config ##
    model_config = {"frozen": True}

    ## field validators ##
    @fieldvalidator('timeout')
    @classmethod
    def _validatetimeout(cls, v: t.Optional[float]) -> t.Optional[float]:
        if (v is not None) and (v <= 0):
            raise ValueError("Timeout must be positive")
        return v

    ## convenience methods ##
    def requestoverrides(self, nonulls: bool = True, **updates) -> dict:
        """
        Return configuration values that can override a RequestModels settings.
        Toggle `nonulls` flag to `False` to include `None` values
        """
        overrides = {
            'verify': self.verify,
            'timeout': self.timeout
        }
        overrides.update(updates)
        if nonulls:
            return {k:v for k,v in overrides.items() if v is not None}
        return overrides

    def sessionoverrides(self, nonulls: bool = True, **updates) -> dict:
        """
        Return configuration values that can override a BaseSession settings.
        Toggle `nonulls` flag to `False` to include `None` values
        """
        overrides = {
            'verifyssl': self.verify,
            'timeout': self.timeout
        }
        overrides.update(updates)
        if nonulls:
            return {k:v for k,v in overrides.items() if v is not None}
        return overrides

class AuthConfig(DeclarableConfig):
    """Configuration for authentication providers."""
    autorefresh: bool = True
    retryattempts: int = 3
    timeout: t.Optional[float] = None
    ## auth specific settings that concretes can extend

    ## pydantic model config ##
    model_config = {"frozen": True}

    ## field validators ##
    @fieldvalidator('retryattempts')
    @classmethod
    def _validateretryattempts(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Retry attempts cannot be negative")
        return v

    @fieldvalidator('timeout')
    @classmethod
    def _validatetimeout(cls, v: t.Optional[float]) -> t.Optional[float]:
        if (v is not None) and (v <= 0):
            raise ValueError("Timeout must be positive")
        return v

class BackendConfig(DeclarableConfig):
    """Configuration for response processing backends."""
    ## exception handling ##
    raiseonerror: bool = True
    errortolerance: ToleranceType = ToleranceType.STRICT

    ## response processing ##
    autoparse: bool = True
    timeout: t.Optional[float] = None

    ## retry settings ##
    retryattempts: int = 0
    retrybackoff: float = 1.0

    ## pydantic configs ##
    model_config = {"frozen": True}

    ## field validators ##
    @fieldvalidator('retryattempts')
    @classmethod
    def _validateretryattempts(cls, v: int) -> int:
        if (v < 0): #! shouldnt we just be using the pydantic Field.ge?
            raise ValueError("Retry attempts cannot be negative")
        return v

class PersistenceConfig(DeclarableConfig):
    """Configuration for persistence behavior"""
    cookies: bool = True
    headers: bool = True
    tokens: bool = False  # For auth tokens
    file: t.Optional[Path] = None
    format: str = "json"  # json, pickle, etc.
    autoload: bool = True
    autosave: bool = True

    ## field validators ##
    @fieldvalidator('file')
    @classmethod
    def _validatefile(cls, v: t.Any) -> t.Optional[Path]:
        if v is None:
            return None
        try:
            return Path(v)
        except Exception as e:
            raise ValueError(f"Invalid file path: {e}")

    @fieldvalidator('format')
    @classmethod
    def _validateformat(cls, v: str) -> str:
        if v not in ('json', 'pickle'):
            raise ValueError("Format must be 'json' or 'pickle'")
        return v
