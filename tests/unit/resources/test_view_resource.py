# ~/clientfactory/tests/unit/resources/test_view_resource.py
"""
Unit tests for ViewResource implementation.
"""
import pytest
from unittest.mock import Mock, MagicMock

from clientfactory.resources.view import ViewResource
from clientfactory.core.models import ResourceConfig, HTTPMethod, Payload, Param, HTTP
from clientfactory.core.models.request import ResponseModel
from clientfactory.core.bases import BaseClient, BaseSession
from clientfactory.core.protos import BackendProtocol


class TestViewResource:
   """Test ViewResource functionality."""

   def setup_method(self):
       """Set up test fixtures with proper mocks."""
       # Mock session
       self.mock_session = Mock(spec=BaseSession)
       self.mock_session.send = Mock()

       # Mock backend - DON'T spec it to a protocol, mock the actual methods
       self.mock_backend = Mock()
       self.mock_backend.process = Mock()
       self.mock_backend.processresponse = Mock()  # This is probably what's being called

       # Mock engine
       self.mock_engine = Mock()
       self.mock_engine._session = self.mock_session
       self.mock_engine.send = Mock()

       # Mock client
       self.mock_client = Mock(spec=BaseClient)
       self.mock_client.baseurl = "https://api.example.com"
       self.mock_client._engine = self.mock_engine
       self.mock_client._backend = self.mock_backend

       # Mock resource registration methods
       self.mock_client._registerresource = Mock()

   def test_view_resource_creation(self):
       """Test basic ViewResource creation."""
       config = ResourceConfig(name="test", path="items")
       resource = ViewResource(client=self.mock_client, config=config)

       assert isinstance(resource, ViewResource)
       assert resource.name == "test"
       assert resource.path == "items"
       assert resource.method == HTTP.GET
       assert resource.viewmethod == "view"
       assert resource.viewpath == "{id}"

   def test_view_resource_with_custom_attributes(self):
       """Test ViewResource with custom declarative attributes."""
       class TestViewResource(ViewResource):
           method = HTTP.POST
           viewmethod = "get"
           viewpath = "{category}/{id}"

       resource = TestViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       assert resource.method == HTTP.POST
       assert resource.viewmethod == "get"
       assert resource.viewpath == "{category}/{id}"

   def test_auto_generates_view_method(self):
       """Test that view method is auto-generated."""
       resource = ViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       assert "view" in resource._methods
       assert hasattr(resource, "view")
       assert callable(resource.view)

   def test_custom_viewmethod_name(self):
       """Test custom view method name."""
       class TestViewResource(ViewResource):
           viewmethod = "get"

       resource = TestViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       assert "get" in resource._methods
       assert hasattr(resource, "get")
       assert "view" not in resource._methods

   def test_view_method_execution(self):
       """Test view method execution."""
       # Setup mock response and processed result
       mock_response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"id": 123, "name": "test item"}',
           url="https://api.example.com/items/123"
       )
       processed_data = {"id": 123, "name": "test item"}

       # Configure mocks properly
       self.mock_engine.send.return_value = mock_response
       self.mock_backend.processresponse.return_value = processed_data

       # Create resource
       resource = ViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       # Execute view method
       result = resource.view(123)

       # Verify calls
       self.mock_engine.send.assert_called_once()
       self.mock_backend.processresponse.assert_called_once_with(mock_response)
       assert result == processed_data

   def test_view_method_with_payload(self):
       """Test view method with payload validation."""
       class ViewPayload(Payload):
           expand = Param(source="expand", default="details")

       class TestViewResource(ViewResource):
           payload = ViewPayload

       resource = TestViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       # Setup mock response
       mock_response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"id": 123}',
           url="https://api.example.com/items/123"
       )
       # Mock engine.send instead of session.send
       self.mock_engine.send = Mock(return_value=mock_response)

       result = resource.view(123, expand="full")

       self.mock_engine.send.assert_called_once()

   def test_docstring_generation(self):
       """Test docstring generation for view method."""
       resource = ViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       docstring = resource._generateviewdocs()
       assert "View method for test resource" in docstring

   def test_docstring_generation_with_payload(self):
       """Test docstring generation with payload parameters."""
       class ViewPayload(Payload):
           expand = Param(source="expand", required=False, default="basic")

       class TestViewResource(ViewResource):
           payload = ViewPayload

       resource = TestViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       docstring = resource._generateviewdocs()
       assert "View test with validated parameters" in docstring
       assert "Parameters:" in docstring
       assert "expand" in docstring

   def test_payload_instance_creation(self):
       """Test payload instance creation."""
       class ViewPayload(Payload):
           expand = Param(source="expand")

       class TestViewResource(ViewResource):
           payload = ViewPayload

       resource = TestViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       payload_instance = resource._getpayloadinstance()
       assert payload_instance is not None
       assert isinstance(payload_instance, ViewPayload)

   def test_no_payload_instance(self):
       """Test behavior when no payload is configured."""
       resource = ViewResource(
           client=self.mock_client,
           config=ResourceConfig(name="test", path="items")
       )

       payload_instance = resource._getpayloadinstance()
       assert payload_instance is None
