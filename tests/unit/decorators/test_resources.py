# ~/clientfactory/tests/unit/decorators/test_resources.py
"""
Unit tests for resource decorators.
"""
import pytest
from unittest.mock import Mock

from clientfactory.decorators.resources import resource, searchable, manageable
from clientfactory.core.resource import Resource
from clientfactory.resources.search import SearchResource
from clientfactory.resources.managed import ManagedResource
from clientfactory.core.models import ResourceConfig, SearchResourceConfig, Payload, Param


class TestResourceDecorators:
   """Test resource decorators."""

   def test_resource_decorator_basic(self):
       """Test basic resource decorator usage."""
       @resource
       class Users:
           def get_user(self):
               return "user"

       assert issubclass(Users, Resource)
       assert hasattr(Users, 'get_user')
       assert hasattr(Users, '_resourceconfig')
       assert Users._resourceconfig.name == "users"
       assert Users._resourceconfig.path == "users"

   def test_resource_decorator_with_config(self):
       """Test resource decorator with custom configuration."""
       @resource(name="custom_users", path="v2/users")
       class Users:
           pass

       assert issubclass(Users, Resource)
       config = Users._resourceconfig
       assert config.name == "custom_users"
       assert config.path == "v2/users"

   def test_resource_decorator_with_config_object(self):
       """Test resource decorator with pre-built config object."""
       config = ResourceConfig(name="test_resource", path="test/path")

       @resource(config=config)
       class TestResource:
           pass

       assert issubclass(TestResource, Resource)
       assert TestResource._resourceconfig.name == "test_resource"
       assert TestResource._resourceconfig.path == "test/path"

   def test_searchable_decorator_basic(self):
       """Test basic searchable decorator usage."""
       @searchable
       class UserSearch:
           def custom_method(self):
               return "search"

       assert issubclass(UserSearch, SearchResource)
       assert hasattr(UserSearch, 'custom_method')
       assert hasattr(UserSearch, '_resourceconfig')
       assert isinstance(UserSearch._resourceconfig, SearchResourceConfig)
       assert UserSearch._resourceconfig.name == "usersearch"
       assert UserSearch._resourceconfig.searchmethod == "search"
       assert UserSearch._resourceconfig.oncall is False

   def test_searchable_decorator_with_config(self):
       """Test searchable decorator with configuration."""
       class SearchPayload(Payload):
           query = Param(required=True)
           limit = Param(default=10)

       @searchable(
           name="advanced_search",
           path="search/advanced",
           payload=SearchPayload,
           searchmethod="find",
           oncall=True
       )
       class AdvancedSearch:
           pass

       assert issubclass(AdvancedSearch, SearchResource)
       config = AdvancedSearch._resourceconfig
       assert config.name == "advanced_search"
       assert config.path == "search/advanced"
       assert config.payload == SearchPayload
       assert config.searchmethod == "find"
       assert config.oncall is True

   def test_manageable_decorator_basic(self):
       """Test basic manageable decorator usage."""
       @manageable
       class Posts:
           def custom_method(self):
               return "posts"

       assert issubclass(Posts, ManagedResource)
       assert hasattr(Posts, 'custom_method')
       assert hasattr(Posts, '_resourceconfig')
       assert Posts._resourceconfig.name == "posts"

   def test_manageable_decorator_with_crud(self):
       """Test manageable decorator with CRUD operations."""
       @manageable(crud={'create', 'read', 'update', 'delete'})
       class Users:
           pass

       assert issubclass(Users, ManagedResource)
       assert hasattr(Users, '__crud__')
       assert Users.__crud__ == {'create', 'read', 'update', 'delete'}

   def test_manageable_decorator_with_config(self):
       """Test manageable decorator with custom configuration."""
       @manageable(
           name="managed_posts",
           path="posts/managed",
           crud={'create', 'read', 'list'}
       )
       class ManagedPosts:
           pass

       assert issubclass(ManagedPosts, ManagedResource)
       config = ManagedPosts._resourceconfig
       assert config.name == "managed_posts"
       assert config.path == "posts/managed"
       assert ManagedPosts.__crud__ == {'create', 'read', 'list'}

   def test_decorator_without_parentheses(self):
       """Test decorators used without parentheses."""
       @resource
       class BasicResource:
           pass

       @searchable
       class SearchResourceClass:
           pass

       @manageable
       class ManagedResourceClass:
           pass

       assert issubclass(BasicResource, Resource)
       assert issubclass(SearchResourceClass, SearchResource)
       assert issubclass(ManagedResourceClass, ManagedResource)

   def test_preserves_original_attributes(self):
       """Test that decorators preserve original class attributes."""
       @resource(name="test_resource")
       class TestResource:
           custom_attr = "test"

           def custom_method(self):
               return "custom"

       # Test that original attributes are preserved
       assert TestResource.custom_attr == "test"
       assert hasattr(TestResource, 'custom_method')

       # Test instantiation works
       instance = TestResource(client=Mock(), config=TestResource._resourceconfig)
       assert instance.custom_method() == "custom"

   def test_preserves_module_and_qualname(self):
       """Test that decorators preserve module and qualname."""
       @resource
       class TestResource:
           pass

       assert TestResource.__module__ == __name__
       assert TestResource.__qualname__ == "TestResourceDecorators.test_preserves_module_and_qualname.<locals>.TestResource"

   def test_inheritance_works_correctly(self):
       """Test that the transformed class inherits correctly."""
       @resource
       class CustomResource:
           def custom_get(self):
               return "custom get"

       # Should inherit from Resource
       instance = CustomResource(client=Mock(), config=CustomResource._resourceconfig)
       assert isinstance(instance, Resource)

       # Should have custom method
       assert instance.custom_get() == "custom get"

       # Should have Resource methods
       assert hasattr(instance, 'getconfig')
       assert hasattr(instance, 'getclient')

   def test_searchable_with_config_object(self):
       """Test searchable decorator with SearchResourceConfig object."""
       config = SearchResourceConfig(
           name="configured_search",
           path="search/configured",
           searchmethod="find_items",
           oncall=True
       )

       @searchable(config=config)
       class ConfiguredSearch:
           pass

       assert issubclass(ConfiguredSearch, SearchResource)
       assert ConfiguredSearch._resourceconfig.name == "configured_search"
       assert ConfiguredSearch._resourceconfig.searchmethod == "find_items"
       assert ConfiguredSearch._resourceconfig.oncall is True

   def test_multiple_decorators_different_classes(self):
       """Test multiple resource decorators on different classes."""
       @resource(path="basic/users")
       class BasicUsers:
           basic_attr = "basic"

       @searchable(searchmethod="find_users")
       class SearchableUsers:
           search_attr = "searchable"

       @manageable(crud={'create', 'delete'})
       class ManagedUsers:
           managed_attr = "managed"

       assert issubclass(BasicUsers, Resource)
       assert issubclass(SearchableUsers, SearchResource)
       assert issubclass(ManagedUsers, ManagedResource)

       assert BasicUsers._resourceconfig.path == "basic/users"
       assert BasicUsers.basic_attr == "basic"

       assert SearchableUsers._resourceconfig.searchmethod == "find_users"
       assert SearchableUsers.search_attr == "searchable"

       assert ManagedUsers.__crud__ == {'create', 'delete'}
       assert ManagedUsers.managed_attr == "managed"
