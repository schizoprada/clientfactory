# ~/clientfactory/tests/unit/core/models/test_boundmethod.py
"""
Tests for BoundMethod basic functionality
"""
import pytest
from unittest.mock import Mock

from clientfactory.core.models.methods import BoundMethod
from clientfactory.core.models.config import MethodConfig
from clientfactory.core.models.enums import HTTPMethod


class TestBoundMethod:
   """Test basic BoundMethod functionality."""

   def test_boundmethod_creation(self):
       """Test basic BoundMethod creation."""
       def dummy_func():
           return "test_result"

       parent = Mock()
       config = MethodConfig(name="test", method=HTTPMethod.GET)

       bound = BoundMethod(dummy_func, parent, config)

       assert bound._func == dummy_func
       assert bound._parent == parent
       assert bound._config == config

   def test_boundmethod_call(self):
       """Test that BoundMethod calls underlying function."""
       def test_func(x, y=10):
           return x + y

       parent = Mock()
       config = MethodConfig(name="test", method=HTTPMethod.GET)

       bound = BoundMethod(test_func, parent, config)
       result = bound(5, y=20)

       assert result == 25

   def test_boundmethod_attributes_cloned(self):
       """Test that function attributes are cloned."""
       def test_function():
           """Test docstring"""
           pass

       parent = Mock()
       config = MethodConfig(name="test", method=HTTPMethod.GET)

       bound = BoundMethod(test_function, parent, config)

       assert bound.__name__ == "test_function"
       assert bound.__doc__ == "Test docstring"

   def test_methodconfig_property(self):
       """Test _methodconfig backwards compatibility property."""
       def dummy_func(): pass
       parent = Mock()
       config = MethodConfig(name="test", method=HTTPMethod.GET)

       bound = BoundMethod(dummy_func, parent, config)

       assert bound._methodconfig == config

   def test_repr(self):
       """Test string representation."""
       def dummy_func(): pass
       parent = Mock()
       parent.__class__.__name__ = "TestParent"
       config = MethodConfig(name="test", method=HTTPMethod.GET)

       bound = BoundMethod(dummy_func, parent, config)
       bound.__name__ = "test_method"

       assert "BoundMethod(test_method)" in repr(bound)
       assert "TestParent" in repr(bound)


class TestBoundMethodCreation:
   """Test that _createboundmethod returns BoundMethod instances."""

   def test_client_createboundmethod_returns_boundmethod(self):
       """Test BaseClient._createboundmethod returns BoundMethod."""
       from clientfactory.core.bases.client import BaseClient

       # Mock client setup
       client = Mock(spec=BaseClient)
       client._backend = None
       client._engine = Mock()
       client._engine.send.return_value = Mock()

       # Mock method with config
       def test_method(): pass
       test_method._methodconfig = MethodConfig(name="test", method=HTTPMethod.GET)

       # Call actual _createboundmethod
       bound = BaseClient._createboundmethod(client, test_method)

       assert isinstance(bound, BoundMethod)

   def test_resource_createboundmethod_returns_boundmethod(self):
       """Test BaseResource._createboundmethod returns BoundMethod."""
       from clientfactory.core.bases.resource import BaseResource

       # Mock resource setup
       resource = Mock(spec=BaseResource)
       resource._backend = None
       resource._client = Mock()
       resource._client._engine = Mock()
       resource._client._engine.send.return_value = Mock()

       # Mock method with config
       def test_method(): pass
       test_method._methodconfig = MethodConfig(name="test", method=HTTPMethod.GET)

       # Call actual _createboundmethod
       bound = BaseResource._createboundmethod(resource, test_method)

       assert isinstance(bound, BoundMethod)
