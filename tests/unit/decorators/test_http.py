# ~/clientfactory/tests/unit/decorators/test_http.py
"""
Unit tests for HTTP method decorators.
"""
import pytest
from unittest.mock import Mock

from clientfactory.decorators.http import get, post, put, patch, delete, head, options, httpmethod
from clientfactory.core.models import HTTPMethod, MethodConfig, Payload, Param


class TestHTTPMethodDecorators:
   """Test HTTP method decorators."""

   def test_get_decorator_basic(self):
       """Test basic GET decorator usage."""
       @get("{id}")
       def get_user(self, id): pass

       assert hasattr(get_user, '_methodconfig')
       config = get_user._methodconfig
       assert isinstance(config, MethodConfig)
       assert config.method == HTTPMethod.GET
       assert config.path == "{id}"
       assert config.name == "get_user"

   def test_post_decorator_with_payload(self):
       """Test POST decorator with payload."""
       class UserPayload(Payload):
           name = Param(required=True)
           email = Param(required=True)

       @post("users", payload=UserPayload)
       def create_user(self, **data): pass

       config = create_user._methodconfig
       assert config.method == HTTPMethod.POST
       assert config.path == "users"
       assert config.payload == UserPayload

   def test_decorator_with_config_object(self):
       """Test decorator with pre-built MethodConfig."""
       config = MethodConfig(
           name="test",
           method=HTTPMethod.PUT,
           path="test/{id}",
           description="Test method"
       )

       @put(config=config)
       def update_test(self, id): pass

       assert update_test._methodconfig.method == HTTPMethod.PUT
       assert update_test._methodconfig.path == "test/{id}"
       assert update_test._methodconfig.description == "Test method"
       assert update_test._methodconfig.name == "update_test"  # Should override

   def test_decorator_with_processing_hooks(self):
       """Test decorator with pre/post processing."""
       preprocess = lambda data: {"processed": data}
       postprocess = lambda resp: resp.json()

       @patch("{id}", preprocess=preprocess, postprocess=postprocess)
       def update_item(self, id, **data): pass

       config = update_item._methodconfig
       assert config.preprocess == preprocess
       assert config.postprocess == postprocess

   def test_get_with_payload_raises_error(self):
       """Test that GET with payload raises validation error."""
       class TestPayload(Payload):
           query = Param()

       with pytest.raises(ValueError, match="GET method .* cannot have a payload"):
           @get("{id}", payload=TestPayload)
           def invalid_get(self, id): pass

   def test_head_with_payload_raises_error(self):
       """Test that HEAD with payload raises validation error."""
       class TestPayload(Payload):
           data = Param()

       with pytest.raises(ValueError, match="HEAD method .* cannot have a payload"):
           @head("{id}", payload=TestPayload)
           def invalid_head(self, id): pass

   def test_all_http_methods(self):
       """Test all HTTP method decorators."""
       @get("test")
       def test_get(self): pass

       @post("test")
       def test_post(self): pass

       @put("test")
       def test_put(self): pass

       @patch("test")
       def test_patch(self): pass

       @delete("test")
       def test_delete(self): pass

       @head("test")
       def test_head(self): pass

       @options("test")
       def test_options(self): pass

       methods = [test_get, test_post, test_put, test_patch, test_delete, test_head, test_options]
       expected_methods = [HTTPMethod.GET, HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH,
                         HTTPMethod.DELETE, HTTPMethod.HEAD, HTTPMethod.OPTIONS]

       for func, expected_method in zip(methods, expected_methods):
           assert func._methodconfig.method == expected_method
           assert func._methodconfig.path == "test"

   def test_decorator_without_parentheses(self):
       """Test decorator usage without parentheses."""
       @get
       def simple_get(self): pass

       config = simple_get._methodconfig
       assert config.method == HTTPMethod.GET
       assert config.path is None

   def test_docstring_generation_with_payload(self):
       """Test automatic docstring generation with payload."""
       class UserPayload(Payload):
           name = Param(required=True, default="Unknown")
           email = Param(required=True)

       @post("users", payload=UserPayload)
       def create_user(self, **data): pass

       assert "Parameters:" in create_user.__doc__
       assert "name [required]" in create_user.__doc__
       assert "email [required]" in create_user.__doc__

   def test_custom_description_override(self):
       """Test custom description overrides docstring."""
       @get("{id}", description="Custom description for getting user")
       def get_user(self, id):
           """Original docstring"""
           pass

       assert "Custom description for getting user" in get_user.__doc__
       assert "Original docstring" not in get_user.__doc__

   def test_httpmethod_base_function(self):
       """Test the base httpmethod function."""
       @httpmethod(HTTPMethod.PATCH, "custom/{id}")
       def custom_method(self, id): pass

       config = custom_method._methodconfig
       assert config.method == HTTPMethod.PATCH
       assert config.path == "custom/{id}"
       assert config.name == "custom_method"
