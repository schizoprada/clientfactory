# ~/clientfactory/src/clientfactory/decorators/configs.py
"""
Configuration Decorators
------------------------
Decorators for creating declarative configuration objects.
"""
from __future__ import annotations
import typing as t, functools as fn

from clientfactory.core.models.config import (
   AuthConfig, BackendConfig, ClientConfig,
   DeclarableConfig, EngineConfig, PayloadConfig,
   PersistenceConfig, ResourceConfig, SearchResourceConfig,
   SessionConfig
)


def _createconfig(cls: t.Type, conf: t.Type) -> t.Any:
   """Helper method to transform a given class into specified config class."""
   attrs = {
       k:v for k,v in cls.__dict__.items()
       if not k.startswith('_') and
       not callable(v)
   }
   return conf(**attrs)

class configs:
   """Namespace for configuration decorators"""

   @staticmethod
   def auth(cls: t.Type) -> AuthConfig: #type: ignore
       """
       Decorator to transform a class into an AuthConfig instance.

       Example:
           @configs.auth
           class MyAuthConfig:
               auth_type = AuthType.BEARER
               token = "my-token"
               header = "Authorization"
       """
       return _createconfig(cls, AuthConfig)

   @staticmethod
   def backend(cls: t.Type) -> BackendConfig: #type: ignore
       """
       Decorator to transform a class into a BackendConfig instance.

       Example:
           @configs.backend
           class MyBackendConfig:
               backend_type = BackendType.REST
               baseurl = "https://api.example.com"
               timeout = 30.0
       """
       return _createconfig(cls, BackendConfig)

   @staticmethod
   def client(cls: t.Type) -> ClientConfig: #type: ignore
       """
       Decorator to transform a class into a ClientConfig instance.

       Example:
           @configs.client
           class MyClientConfig:
               baseurl = "https://api.example.com"
               timeout = 30.0
               headers = {"User-Agent": "MyApp"}
       """
       return _createconfig(cls, ClientConfig)

   @staticmethod
   def declarable(cls: t.Type) -> DeclarableConfig: #type: ignore
       """
       Decorator to transform a class into a DeclarableConfig instance.

       Example:
           @configs.declarable
           class MyDeclarableConfig:
               tolerance = ToleranceType.STRICT
               validate = True
       """
       return _createconfig(cls, DeclarableConfig)

   @staticmethod
   def engine(cls: t.Type) -> EngineConfig: #type: ignore
       """
       Decorator to transform a class into an EngineConfig instance.

       Example:
           @configs.engine
           class MyEngineConfig:
               engine_type = EngineType.REQUESTS
               timeout = 30.0
               retries = 3
       """
       return _createconfig(cls, EngineConfig)

   @staticmethod
   def payload(cls: t.Type) -> PayloadConfig: #type: ignore
       """
       Decorator to transform a class into a PayloadConfig instance.

       Example:
           @configs.payload
           class MyPayloadConfig:
               payload_type = PayloadType.JSON
               validate = True
               strict = False
       """
       return _createconfig(cls, PayloadConfig)

   @staticmethod
   def persistence(cls: t.Type) -> PersistenceConfig: #type: ignore
       """
       Decorator to transform a class into a PersistenceConfig instance.

       Example:
           @configs.persistence
           class MyPersistenceConfig:
               enabled = True
               format = "json"
               path = "/tmp/session.json"
       """
       return _createconfig(cls, PersistenceConfig)

   @staticmethod
   def resource(cls: t.Type) -> ResourceConfig: #type: ignore
       """
       Decorator to transform a class into a ResourceConfig instance.

       Example:
           @configs.resource
           class MyResourceConfig:
               name = "users"
               path = "api/users"
               description = "User management resource"
       """
       return _createconfig(cls, ResourceConfig)

   @staticmethod
   def searchable(cls: t.Type) -> SearchResourceConfig: #type: ignore
       """
       Decorator to transform a class into a SearchResourceConfig instance.

       Example:
           @configs.searchable
           class MySearchConfig:
               name = "search"
               path = "search"
               method = HTTPMethod.POST
               searchmethod = "search"
       """
       return _createconfig(cls, SearchResourceConfig)

   @staticmethod
   def session(cls: t.Type) -> SessionConfig: #type: ignore
       """
       Decorator to transform a class into a SessionConfig instance.

       Example:
           @configs.session
           class MySessionConfig:
               defaultheaders = {"User-Agent": "MyApp"}
               defaultcookies = {"session": "abc123"}
               maxretries = 5
               timeout = 60.0
       """
       return _createconfig(cls, SessionConfig)
