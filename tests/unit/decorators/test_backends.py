# ~/clientfactory/tests/unit/decorators/test_backends.py
"""
Unit tests for backend decorators.
"""
import pytest
from unittest.mock import Mock

from clientfactory.decorators.backends import basebackend, algolia, graphql
from clientfactory.core.bases import BaseBackend
from clientfactory.backends.algolia import AlgoliaBackend
from clientfactory.backends.graphql import GQLBackend


class TestBackendDecorators:
   """Test backend decorators."""

   def test_basebackend_decorator_basic(self):
       """Test basic basebackend decorator usage."""
       @basebackend
       class CustomBackend:
           endpoint = "/api/v2"

           def format_request(self, request, data):
               return request

       assert issubclass(CustomBackend, BaseBackend)
       assert CustomBackend.endpoint == "/api/v2"
       assert hasattr(CustomBackend, 'format_request')

   def test_basebackend_decorator_with_kwargs(self):
       """Test basebackend decorator with kwargs."""
       @basebackend(timeout=120.0, retries=5)
       class CustomBackend:
           pass

       assert issubclass(CustomBackend, BaseBackend)
       assert CustomBackend.timeout == 120.0
       assert CustomBackend.retries == 5

   def test_algolia_decorator_basic(self):
       """Test basic Algolia decorator usage."""
       @algolia
       class SearchBackend:
           custom_attr = "search"

       assert issubclass(SearchBackend, AlgoliaBackend)
       assert SearchBackend.custom_attr == "search"

   def test_algolia_decorator_with_config(self):
       """Test Algolia decorator with configuration."""
       @algolia(
           appid="test-app-id",
           apikey="test-api-key",
           index="test-index",
           indices=["index1", "index2"]
       )
       class SearchBackend:
           pass

       assert issubclass(SearchBackend, AlgoliaBackend)
       assert SearchBackend.appid == "test-app-id"
       assert SearchBackend.apikey == "test-api-key"
       assert SearchBackend.index == "test-index"
       assert SearchBackend.indices == ["index1", "index2"]

   def test_graphql_decorator_basic(self):
       """Test basic GraphQL decorator usage."""
       @graphql
       class GQLBackend:
           custom_resolver = "resolver"

       assert issubclass(GQLBackend, GQLBackend)
       assert GQLBackend.custom_resolver == "resolver"
       assert GQLBackend.endpoint == "/graphql"  # Default
       assert GQLBackend.introspection is True  # Default
       assert GQLBackend.maxdepth == 10  # Default

   def test_graphql_decorator_with_config(self):
       """Test GraphQL decorator with configuration."""
       @graphql(
           endpoint="/api/graphql",
           introspection=False,
           maxdepth=15
       )
       class CustomGQLBackend:
           pass

       assert issubclass(CustomGQLBackend, GQLBackend)
       assert CustomGQLBackend.endpoint == "/api/graphql"
       assert CustomGQLBackend.introspection is False
       assert CustomGQLBackend.maxdepth == 15

   def test_decorator_without_parentheses(self):
       """Test decorators used without parentheses."""
       @basebackend
       class CustomBackend:
           pass

       @algolia
       class AlgoliaBackendClass:
           pass

       @graphql
       class GraphQLBackendClass:
           pass

       assert issubclass(CustomBackend, BaseBackend)
       assert issubclass(AlgoliaBackendClass, AlgoliaBackend)
       assert issubclass(GraphQLBackendClass, GQLBackend)

   def test_preserves_original_attributes(self):
       """Test that decorators preserve original class attributes."""
       @algolia(appid="test-app")
       class SearchBackend:
           custom_method_called = False

           def custom_format(self, data):
               self.custom_method_called = True
               return {"formatted": data}

       # Test that original attributes are preserved
       backend = SearchBackend()
       assert hasattr(backend, 'custom_format')
       result = backend.custom_format({"test": "data"})
       assert result == {"formatted": {"test": "data"}}
       assert backend.custom_method_called is True
       assert backend.appid == "test-app"

   def test_preserves_module_and_qualname(self):
       """Test that decorators preserve module and qualname."""
       @graphql
       class TestBackend:
           pass

       assert TestBackend.__module__ == __name__
       assert TestBackend.__qualname__ == "TestBackendDecorators.test_preserves_module_and_qualname.<locals>.TestBackend"

   def test_inheritance_works_correctly(self):
       """Test that the transformed class inherits correctly."""
       @basebackend
       class CustomBackend:
            def custom_process(self, response):
                return "custom processed"

            def _formatrequest(self, request, data): return request
            def _processresponse(self, response): return response

       # Should inherit from BaseBackend
       backend = CustomBackend()
       assert isinstance(backend, BaseBackend)

       # Should have custom method
       assert backend.custom_process(None) == "custom processed"

       # Should have BaseBackend methods
       assert hasattr(backend, 'validatedata')
       assert hasattr(backend, 'handleerror')

   def test_algolia_partial_config(self):
       """Test Algolia decorator with partial configuration."""
       @algolia(appid="test-app", apikey="test-key")
       class PartialConfig:
           pass

       assert issubclass(PartialConfig, AlgoliaBackend)
       assert PartialConfig.appid == "test-app"
       assert PartialConfig.apikey == "test-key"
       # index and indices should not be set
       assert not hasattr(PartialConfig, 'index')
       assert not hasattr(PartialConfig, 'indices')

   def test_multiple_decorators_different_classes(self):
       """Test multiple backend decorators on different classes."""
       @algolia(appid="algolia-app")
       class AlgoliaBackendClass:
           algolia_specific = "algolia"

       @graphql(endpoint="/custom/graphql")
       class GraphQLBackendClass:
           graphql_specific = "graphql"

       assert issubclass(AlgoliaBackendClass, AlgoliaBackend)
       assert issubclass(GraphQLBackendClass, GQLBackend)
       assert AlgoliaBackendClass.appid == "algolia-app"
       assert AlgoliaBackendClass.algolia_specific == "algolia"
       assert GraphQLBackendClass.endpoint == "/custom/graphql"
       assert GraphQLBackendClass.graphql_specific == "graphql"
