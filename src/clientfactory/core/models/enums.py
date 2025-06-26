# ~/clientfactory/src/clientfactory/core/models/enums.py
"""
Core Enumerations
-----------------
Defines standard enums used throughout ClientFactory.
"""
from __future__ import annotations
import enum

class HTTPMethod(str, enum.Enum):
    """HTTP request methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"

class AuthType(str, enum.Enum):
    """Authentication strategy types"""
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    TOKEN = "token"
    APIKEY = "apikey"
    OAUTH = "oauth"
    JWT = "jwt"
    CUSTOM = "custom"

class BackendType(str, enum.Enum):
    """Response processing backend types"""
    REST = "rest"
    GRAPHQL = "graphql"
    ALGOLIA = "algolia"
    ELASTICSEARCH = "elasticsearch"
    CUSTOM = "custom"

class PayloadType(str, enum.Enum):
    """Request payload serialization types"""
    JSON = "json"
    FORM = "form"
    MULTIPART = "multipart"
    XML = "xml"
    TEXT = "text"
    BINARY = "binary"

class SessionType(str, enum.Enum):
    """Session management types"""
    STANDARD = "standard"
    PERSISTENT = "persistent"
    ASYNC = "async"
    CUSTOM = "custom"

class EngineType(str, enum.Enum):
    """HTTP engine types"""
    REQUESTS = "requests"
    HTTPX = "httpx"
    AIOHTTP = "aiohttp"
    CUSTOM = "custom"

class ToleranceType(str, enum.Enum):
    """Handling strictness level types"""
    IGNORE = "ignore"
    LAX = "lax"
    STRICT = "strict"
    #! define more as eneded

class DeclarativeType(str, enum.Enum):
    """..."""
    COMPONENT = "component"


class MergeMode(str, enum.Enum):
    """How to handle merging extracted data with existing session data."""
    MERGE = "merge"
    OVERWRITE = "overwrite"
    IGNORE = "ignore"

## Shorthand Aliases ##
HTTP = HTTPMethod
AUTH = AuthType
BACKEND = BackendType
PAYLOAD = PayloadType
SESSION = SessionType
ENGINE = EngineType
TOLERANCE = ToleranceType
DECLARATIVE = DeclarativeType
