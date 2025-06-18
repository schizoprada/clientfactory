# ~/clientfactory/tests/unit/decorators/test_http_data.py
"""
Unit tests for HTTP data decorators.
"""
import pytest

from clientfactory.decorators.http.data import param, payload
from clientfactory.core.models import Param, Payload


class TestParamDecorator:
   """Test @param decorator."""

   def test_param_decorator_basic(self):
       """Test basic @param decorator usage."""
       @param
       class UserID:
           source = "user_id"
           required = True
           default = None

       assert isinstance(UserID, Param)
       assert UserID.source == "user_id"
       assert UserID.required is True
       assert UserID.default is None

   def test_param_decorator_with_transform(self):
       """Test @param decorator with transform function."""
       @param
       class AgeParam:
           source = "age"
           required = False
           default = 0
           transform = int

       assert AgeParam.source == "age"
       assert AgeParam.required is False
       assert AgeParam.default == 0
       assert AgeParam.transform == int

   def test_param_decorator_ignores_private_attrs(self):
       """Test that decorator ignores private attributes."""
       @param
       class MyParam:
           source = "test"
           _private = "ignored"
           __dunder = "ignored"

       assert MyParam.source == "test"
       assert not hasattr(MyParam, '_private')
       assert not hasattr(MyParam, '__dunder')

   def test_param_decorator_empty_class(self):
       """Test param decorator with empty class uses defaults."""
       @param
       class EmptyParam:
           pass

       assert isinstance(EmptyParam, Param)
       # Should have default Param values
       assert EmptyParam.required is False
       assert EmptyParam.default is None

   def test_param_decorator_with_all_options(self):
       """Test param decorator with all possible options."""
       @param
       class CompleteParam:
           name = "test_param"
           source = "test_source"
           target = "test_target"
           required = True
           default = "default_value"
           transform = str.upper

       assert CompleteParam.name == "test_param"
       assert CompleteParam.source == "test_source"
       assert CompleteParam.target == "test_target"
       assert CompleteParam.required is True
       assert CompleteParam.default == "default_value"
       assert CompleteParam.transform == str.upper


class TestPayloadDecorator:
   """Test @payload decorator."""

   def test_payload_decorator_basic(self):
       """Test basic @payload decorator usage."""
       @payload
       class UserPayload:
           user_id = Param(source="id", required=True)
           email = Param(source="email_addr", required=True)

       assert issubclass(UserPayload, Payload)
       assert hasattr(UserPayload, '_fields')
       assert 'user_id' in UserPayload._fields
       assert 'email' in UserPayload._fields

       # Check that fields are Param instances
       assert isinstance(UserPayload._fields['user_id'], Param)
       assert isinstance(UserPayload._fields['email'], Param)

   def test_payload_decorator_with_dict_values(self):
       """Test @payload decorator with dict field definitions."""
       @payload
       class TestPayload:
           name = {"source": "full_name", "required": True}
           age = {"source": "user_age", "default": 18}

       assert issubclass(TestPayload, Payload)
       assert 'name' in TestPayload._fields
       assert 'age' in TestPayload._fields

       # Should be converted to Param instances
       assert isinstance(TestPayload._fields['name'], Param)
       assert isinstance(TestPayload._fields['age'], Param)

   def test_payload_decorator_with_tuple_values(self):
       """Test @payload decorator with tuple field definitions."""
       @payload
       class TestPayload:
           username = ("user_name", True)  # (source, required)
           score = (100,)  # (default,)

       assert 'username' in TestPayload._fields
       assert 'score' in TestPayload._fields
       assert isinstance(TestPayload._fields['username'], Param)
       assert isinstance(TestPayload._fields['score'], Param)

   def test_payload_decorator_with_simple_values(self):
       """Test @payload decorator with simple default values."""
       @payload
       class TestPayload:
           status = "active"
           count = 0
           enabled = True

       assert 'status' in TestPayload._fields
       assert 'count' in TestPayload._fields
       assert 'enabled' in TestPayload._fields

       # Should create Param instances with defaults
       assert TestPayload._fields['status'].default == "active"
       assert TestPayload._fields['count'].default == 0
       assert TestPayload._fields['enabled'].default is True

   def test_payload_decorator_class_name_handling(self):
       """Test payload decorator handles class names correctly."""
       @payload
       class UserPayload:
           name = Param(source="username")

       # Should keep original name since it contains "Payload"
       assert UserPayload.__name__ == "UserPayload"

       @payload
       class User:
           name = Param(source="username")

       # Should add "Payload" suffix
       assert User.__name__ == "UserPayload"

   def test_payload_decorator_preserves_metadata(self):
       """Test that decorator preserves class metadata."""
       @payload
       class TestPayload:
           """Test payload docstring."""
           field1 = Param(source="test")

       assert TestPayload.__doc__ == "Test payload docstring."
       assert hasattr(TestPayload, '__module__')

   def test_payload_decorator_ignores_private_attrs(self):
       """Test that decorator ignores private attributes and methods."""
       @payload
       class TestPayload:
           field1 = Param(source="test")
           _private = "ignored"
           __dunder = "ignored"

           def method(self):
               pass

       assert 'field1' in TestPayload._fields
       assert '_private' not in TestPayload._fields
       assert '__dunder' not in TestPayload._fields
       assert 'method' not in TestPayload._fields

   def test_payload_decorator_functional(self):
       """Test that decorated payload actually works."""
       @payload
       class TestPayload:
           name = Param(source="full_name", required=True)
           age = Param(source="user_age", default=25)

       # Test instantiation
       instance = TestPayload()
       assert isinstance(instance, Payload)

       # Test basic functionality
       test_data = {"full_name": "John Doe", "user_age": 30}
       result = instance.transform(test_data)

       assert "name" in result
       assert "age" in result
       assert result["name"] == "John Doe"
       assert result["age"] == 30

   def test_payload_decorator_mixed_field_types(self):
       """Test payload decorator with mixed field definition types."""
       @payload
       class MixedPayload:
           # Existing Param instance
           id = Param(source="user_id", required=True)
           # Dict definition
           name = {"source": "full_name", "required": True}
           # Tuple definition
           age = ("user_age", False, 18)  # (source, required, default)
           # Simple value
           status = "active"

       assert len(MixedPayload._fields) == 4
       for field_name in ['id', 'name', 'age', 'status']:
           assert field_name in MixedPayload._fields
           assert isinstance(MixedPayload._fields[field_name], Param)
