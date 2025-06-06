# ~/clientfactory/src/clientfactory/core/models/config.py
"""
Configuration Models
--------------------
Immutable configuration objects for clients, resources, and methods.
"""
from __future__ import annotations
import typing as t

from pydantic import (
   BaseModel as PydModel,
   Field,
   field_validator as fieldvalidator,
   computed_field as computedfield
)

from clientfactory.core.models.enums import (
    HTTPMethod, AuthType, BackendType,
    PayloadType, SessionType, EngineType
)

if t.TYPE_CHECKING:
    from clientfactory.core.protos import (
        AuthProtocol, BackendProtocol, PayloadProtocol,
        RequestEngineProtocol, SessionProtocol
    )
    from clientfactory.core.bases.resource import BaseResource


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

class SessionConfig(PydModel):
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
