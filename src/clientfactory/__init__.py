# ~/clientfactory/src/clientfactory/__init__.py
"""
ClientFactory
-------------
A declarative framework for building API clients with minimal boilerplate.
"""

__version__ = "0.9.36"
__author__ = "Joel Yisrael"
__email__ = "schizoprada@gmail.com"
__license__ = "MIT"
__url__ = "https://github.com/schizoprada/schematix"

# Version info tuple for programmatic access
VERSION = tuple(map(int, __version__.split('.')))

from .core import (
    Backend, Client, Resource, Session, Persistence
)
from .resources import (
    ManagedResource, SearchResource
)
from .engines import (
    RequestsEngine, RequestsSession
)
from .decorators import (
    httpmethod, get, post,
    put, patch, delete,
    head, options, resource,
   searchable, manageable,
   headers, cookies,
   param, payload,
   baseauth, jwt, dpop,
   basebackend, algolia, graphql,
   configs, engine, persistence,
   basesession, session
)
from .backends import (
    AlgoliaConfig, AlgoliaParams,
    AlgoliaResponse, AlgoliaBackend,
    GQLConfig, GQLResponse,
    GQLBackend
)
from .auths import (
    JWTAuth, DPOPAuth
)

from .logs import log
