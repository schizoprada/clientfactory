# ~/clientfactory/src/clientfactory/backends/graphql.py
"""
"""
from __future__ import annotations
import typing as t

#! TO BE IMPLEMENTED
#import gql
#from gql.dsl import DSLSchema
#from graphql.language.ast import DocumentNode

from schematix import Field, Schema

from clientfactory.core.bases import BaseBackend
from clientfactory.core.models import BackendConfig, RequestModel, ResponseModel

class GQLConfig(BackendConfig):
    """Configuration for GraphQL Backend"""
    endpoint: str = "/graphql"
    introspection: bool = True
    maxdepth: int = 10

class GQLResponse(Schema):
    """Process GraphQL Response Structure"""
    data = Field(source="data", target="data", default={})
    errors = Field(source="errors", target="errors", default=[])
    extensions = Field(source="extensions", target="extensions", default={})


class GQLBackend(BaseBackend):
    """
    GraphQL backend implementation.

    Handles GraphQL query/mutation formatting and response processing.
    """
    __declaredas__: str = 'graphql'
    __declattrs__: set[str] = BaseBackend.__declattrs__ | {'endpoint', 'introspection', 'maxdepth'}
    __declconfs__: set[str] = BaseBackend.__declconfs__ | {'endpoint', 'introspection', 'maxdepth'}

    def __init__(
        self,
        config: t.Optional[GQLConfig] = None,
        **kwargs: t.Any
    ) -> None:
        # 1. resolve components
        components = self._resolvecomponents()

        # 2. resolve config
        self._config: GQLConfig = self._resolveconfig(GQLConfig, config, **kwargs) # type: ignore

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)

        self._responseschema: Schema = GQLResponse()

    def _resolveattributes(self, attributes: dict) -> None:
        super()._resolveattributes(attributes)
        self.endpoint: str = attributes.get('endpoint', '/graphql') or self._config.endpoint
        self.introspection: bool = attributes.get('introspection', True) or self._config.introspection
        self.maxdepth: int = attributes.get('maxdepth', 10) or self._config.maxdepth

    def _formatrequest(self, request: RequestModel, data: t.Dict[str, t.Any]) -> RequestModel:
        """Format request for GraphQL API."""
        print(f"DEBUG GQL format: data = {data}")
        if not data:
            return request

        body = {
            k: data.get(k, default)
            for k, default in {
                "query": "",
                "variables": {},
                "operationName": None
            }.items()
        }
        print(f"DEBUG GQL format: body = {body}")

        # ensure operationName is not None
        if body['operationName'] is None:
            del body['operationName']

        update = {
            'method': 'POST',
            'json': body,
            'headers': {
                **request.headers,
                'Content-Type': 'application/json'
            }
        }

        return request.model_copy(update=update)


    def _processresponse(self, response: ResponseModel) -> t.Any:
        """Process GraphQL response."""
        if not response.ok:
            return response

        try:
            processed = self._responseschema.transform(response.json())
            print(f"DEBUG GQL: processed = {processed}")
            print(f"DEBUG GQL: raiseonerror = {self._config.raiseonerror}")

            # check for errors
            if (errors:=processed.get('errors')):
                print(f"DEBUG GQL: Found errors = {errors}, should raise = {self._config.raiseonerror}")
                if self._config.raiseonerror:
                    messages = [err.get('message', 'Unknown Error') for err in errors]
                    raise RuntimeError(f"GraphQL Errors: {'; '.join(messages)}")

            return processed
        except ValueError as e:
            import warnings
            warnings.warn(f"Exception parsing JSON response, returning as text: {e}")
            return response.text
