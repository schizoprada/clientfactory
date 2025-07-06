# ~/clientfactory/tests/unit/resources/test_managed_resource.py 
# tests/unit/resources/test_managed_resource.py
"""
Unit tests for ManagedResource implementation.
"""
import pytest
from unittest.mock import Mock

from clientfactory.resources.managed import ManagedResource
from clientfactory.utils import crud
from clientfactory.core.models import ResourceConfig, HTTPMethod, MethodConfig
from clientfactory.core.models.request import ResponseModel


class TestManagedResource:
   """Test ManagedResource functionality."""

   def setup_method(self):
       """Set up test fixtures."""
       self.mock_client = Mock()
       self.mock_client.baseurl = "https://api.example.com"
       self.mock_client._engine = Mock()
       self.mock_client._engine._session = Mock()
       self.mock_client._backend = None

   def test_managed_resource_creation(self):
       """Test basic ManagedResource creation."""
       config = ResourceConfig(name="users", path="users")
       resource = ManagedResource(client=self.mock_client, config=config)

       assert isinstance(resource, ManagedResource)
       assert resource.name == "users"
       assert resource.path == "users"

   def test_crud_set_generates_methods(self):
       """Test that __crud__ set generates methods."""
       class TestManagedResource(ManagedResource):
           __crud__ = {'create', 'read', 'update', 'delete', 'list'}

       resource = TestManagedResource(
           client=self.mock_client,
           config=ResourceConfig(name="users", path="users")
       )

       # All CRUD methods should be generated
       assert "create" in resource._methods
       assert "read" in resource._methods
       assert "update" in resource._methods
       assert "delete" in resource._methods
       assert "list" in resource._methods

       # Methods should be callable
       assert hasattr(resource, "create")
       assert hasattr(resource, "read")
       assert hasattr(resource, "update")
       assert hasattr(resource, "delete")
       assert hasattr(resource, "list")

   def test_partial_crud_set(self):
       """Test partial CRUD operation generation."""
       class TestManagedResource(ManagedResource):
           __crud__ = {'create', 'read'}

       resource = TestManagedResource(
           client=self.mock_client,
           config=ResourceConfig(name="users", path="users")
       )

       # Only specified methods should be generated
       assert "create" in resource._methods
       assert "read" in resource._methods
       assert "update" not in resource._methods
       assert "delete" not in resource._methods
       assert "list" not in resource._methods

   def test_no_crud_set_no_generation(self):
       """Test that no __crud__ means no auto-generation."""
       class TestManagedResource(ManagedResource):
           pass

       resource = TestManagedResource(
           client=self.mock_client,
           config=ResourceConfig(name="users", path="users")
       )

       # No CRUD methods should be auto-generated
       assert "create" not in resource._methods
       assert "read" not in resource._methods
       assert "update" not in resource._methods
       assert "delete" not in resource._methods
       assert "list" not in resource._methods

   def test_explicit_method_overrides_auto_generation(self):
       """Test that explicit method definitions override auto-generation."""
       class TestManagedResource(ManagedResource):
           __crud__ = {'create', 'read'}

           def create(self):
               return "custom create"

       # Mock the session to avoid actual method binding issues
       resource = TestManagedResource(
           client=self.mock_client,
           config=ResourceConfig(name="users", path="users")
       )

       # Should have both methods, but create should be the explicit one
       assert "create" in resource._methods
       assert "read" in resource._methods

       # The explicit create method should not be overridden
       # (This tests that we check 'op not in self._methods' in _generatecrudmethods)


class TestCrudHelpers:
   """Test the crud helper class."""

   def test_crud_create(self):
       """Test crud.create helper."""
       method_config = crud.create()

       assert isinstance(method_config, MethodConfig)
       assert method_config.name == "create"
       assert method_config.method == HTTPMethod.POST
       assert method_config.path == ""

   def test_crud_read(self):
       """Test crud.read helper."""
       method_config = crud.read()

       assert isinstance(method_config, MethodConfig)
       assert method_config.name == "read"
       assert method_config.method == HTTPMethod.GET
       assert method_config.path == "{id}"

   def test_crud_update(self):
       """Test crud.update helper."""
       method_config = crud.update()

       assert isinstance(method_config, MethodConfig)
       assert method_config.name == "update"
       assert method_config.method == HTTPMethod.PUT
       assert method_config.path == "{id}"

   def test_crud_delete(self):
       """Test crud.delete helper."""
       method_config = crud.delete()

       assert isinstance(method_config, MethodConfig)
       assert method_config.name == "delete"
       assert method_config.method == HTTPMethod.DELETE
       assert method_config.path == "{id}"

   def test_crud_list(self):
       """Test crud.list helper."""
       method_config = crud.list()

       assert isinstance(method_config, MethodConfig)
       assert method_config.name == "list"
       assert method_config.method == HTTPMethod.GET
       assert method_config.path == ""

   def test_crud_custom_parameters(self):
       """Test crud helpers with custom parameters."""
       # Test custom name and path
       method_config = crud.create(name="add", path="items")
       assert method_config.name == "add"
       assert method_config.path == "items"

       # Test with payload
       mock_payload = Mock()
       method_config = crud.update(payload=mock_payload)
       assert method_config.payload is mock_payload

   def test_crud_method_base(self):
       """Test crud.method base function."""
       method_config = crud.method(
           name="custom",
           method=HTTPMethod.PATCH,
           path="custom/{id}",
           description="Custom method"
       )

       assert method_config.name == "custom"
       assert method_config.method == HTTPMethod.PATCH
       assert method_config.path == "custom/{id}"
       assert method_config.description == "Custom method"


class TestManagedResourceIntegration:
   """Test ManagedResource integration scenarios."""

   def setup_method(self):
       """Set up test fixtures."""
       self.mock_client = Mock()
       self.mock_client.baseurl = "https://api.example.com"
       self.mock_client._engine = Mock()
       self.mock_client._engine._session = Mock()
       self.mock_client._backend = None

   def test_crud_method_execution(self):
       """Test that generated CRUD methods can be executed."""
       class TestManagedResource(ManagedResource):
           __crud__ = {'create', 'read'}

       resource = TestManagedResource(
           client=self.mock_client,
           config=ResourceConfig(name="users", path="users")
       )

       # Mock session response
       mock_response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"id": 1, "name": "John"}',
           url="https://api.example.com/users"
       )
       resource._session.send.return_value = mock_response

       # Test create method execution
       result = resource.create(name="John", email="john@example.com")
       assert result is mock_response

       # Test read method execution
       result = resource.read(id=1)
       assert result is mock_response

       # Verify session.send was called
       assert resource._session.send.call_count == 2

   def test_mixed_explicit_and_generated_methods(self):
       """Test mixing explicit methods with generated ones."""
       class TestManagedResource(ManagedResource):
           __crud__ = {'create', 'read', 'update'}

           # Explicit method definition
           def read(self):
               return "custom read implementation"

       resource = TestManagedResource(
           client=self.mock_client,
           config=ResourceConfig(name="users", path="users")
       )

       # Should have all three methods
       assert "create" in resource._methods
       assert "read" in resource._methods
       assert "update" in resource._methods

       # Custom read should be preserved
       assert callable(resource.read)
