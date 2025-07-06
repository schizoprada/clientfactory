# ~/clientfactory/tests/unit/resources/test_resource_composition.py
"""
Unit tests for resource composition using & operator.
"""
import pytest
from unittest.mock import Mock

from clientfactory.resources.search import SearchResource
from clientfactory.resources.view import ViewResource
from clientfactory.core.models import ResourceConfig, SearchResourceConfig, HTTPMethod, HTTP
from clientfactory.core.bases import BaseClient, BaseSession


class TestResourceComposition:
   """Test resource composition functionality."""

   def setup_method(self):
       """Set up test fixtures."""
       # Mock session
       self.mock_session = Mock(spec=BaseSession)
       self.mock_session.send = Mock()

       # Mock backend
       self.mock_backend = Mock()
       self.mock_backend.processresponse = Mock()

       # Mock engine
       self.mock_engine = Mock()
       self.mock_engine._session = self.mock_session
       self.mock_engine.send = Mock()

       # Mock client
       self.mock_client = Mock(spec=BaseClient)
       self.mock_client.baseurl = "https://api.example.com"
       self.mock_client._engine = self.mock_engine
       self.mock_client._backend = self.mock_backend
       self.mock_client._registerresource = Mock()

   def test_basic_composition(self):
       """Test basic & operator composition."""
       # Create composed class
       ComposedResource = SearchResource & ViewResource

       # Verify it's a new class
       assert ComposedResource is not SearchResource
       assert ComposedResource is not ViewResource
       assert issubclass(ComposedResource, SearchResource)
       assert issubclass(ComposedResource, ViewResource)

   def test_composed_class_name(self):
       """Test composed class naming."""
       ComposedResource = SearchResource & ViewResource

       expected_name = "(SearchResource)&(ViewResource)"
       assert ComposedResource.__name__ == expected_name

   def test_reverse_composition(self):
       """Test reverse composition with __rand__."""
       ComposedResource1 = SearchResource & ViewResource
       ComposedResource2 = ViewResource & SearchResource

       # Should be different classes due to MRO
       assert ComposedResource1 is not ComposedResource2
       assert ComposedResource1.__name__ == "(SearchResource)&(ViewResource)"
       assert ComposedResource2.__name__ == "(ViewResource)&(SearchResource)"

   def test_composed_resource_instantiation(self):
       """Test that composed resource can be instantiated."""
       ComposedResource = SearchResource & ViewResource

       config = ResourceConfig(name="test", path="items")
       resource = ComposedResource(client=self.mock_client, config=config)

       # Should be instance of both parent classes
       assert isinstance(resource, SearchResource)
       assert isinstance(resource, ViewResource)
       assert isinstance(resource, ComposedResource)

   def test_composed_resource_has_both_methods(self):
       """Test that composed resource has methods from both parents."""
       ComposedResource = SearchResource & ViewResource

       config = ResourceConfig(name="test", path="items")
       resource = ComposedResource(client=self.mock_client, config=config)

       # Should have both search and view methods
       assert hasattr(resource, "search")
       assert hasattr(resource, "view")
       assert callable(resource.search)
       assert callable(resource.view)
       assert "search" in resource._methods
       assert "view" in resource._methods

   def test_composed_resource_method_execution(self):
       """Test that both methods work in composed resource."""
       from clientfactory.core.models.request import ResponseModel

       ComposedResource = SearchResource & ViewResource

       # Setup mock responses
       search_response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"items": [{"id": 1}]}',
           url="https://api.example.com/items"
       )
       view_response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"id": 123, "name": "test"}',
           url="https://api.example.com/items/123"
       )

       self.mock_engine.send.side_effect = [search_response, view_response]
       self.mock_backend.processresponse.side_effect = [
           {"items": [{"id": 1}]},
           {"id": 123, "name": "test"}
       ]

       config = ResourceConfig(name="test", path="items")
       resource = ComposedResource(client=self.mock_client, config=config)

       # Test search method
       search_result = resource.search(q="test")
       assert search_result == {"items": [{"id": 1}]}

       # Test view method
       view_result = resource.view(123)
       assert view_result == {"id": 123, "name": "test"}

       # Verify both methods were called
       assert self.mock_engine.send.call_count == 2

   def test_mro_order(self):
       """Test method resolution order."""
       ComposedResource1 = SearchResource & ViewResource
       ComposedResource2 = ViewResource & SearchResource

       # MRO should be different based on composition order
       mro1 = ComposedResource1.__mro__
       mro2 = ComposedResource2.__mro__

       assert mro1 != mro2
       assert SearchResource in mro1
       assert ViewResource in mro1
       assert SearchResource in mro2
       assert ViewResource in mro2

   def test_chained_composition(self):
       """Test chaining multiple compositions."""
       # This would test A & B & C pattern if we had a third resource type
       # For now, test that the composition returns a composable class
       ComposedResource = SearchResource & ViewResource

       # Should still be composable (though we don't have a third type to test with)
       assert hasattr(ComposedResource, '__and__')
       assert hasattr(ComposedResource, '__rand__')

   def test_composition_preserves_attributes(self):
       """Test that composition preserves class attributes."""
       class CustomSearchResource(SearchResource):
           searchmethod = "find"
           custom_attr = "search_value"

       class CustomViewResource(ViewResource):
           viewmethod = "get"
           custom_attr = "view_value"

       ComposedResource = CustomSearchResource & CustomViewResource

       config = ResourceConfig(name="test", path="items")
       resource = ComposedResource(client=self.mock_client, config=config)

       # Should have custom search method name
       assert hasattr(resource, "find")
       assert hasattr(resource, "get")

       # MRO should determine which custom_attr wins
       # (First class in composition should win)
       assert resource.custom_attr == "search_value"
