# ~/clientfactory/tests/integration/test_schematix_integration.py
"""
Integration tests for schematix library integration.
"""
import pytest
import schematix as sex
from clientfactory.core.models import Param
from clientfactory.core.models.request import Payload


class TestParamSchematixIntegration:
   """Test Param class integration with schematix Field."""

   def test_param_inherits_from_schematix_field(self):
       """Test that Param properly inherits from schematix Field."""
       param = Param(name="test", source="test_field")
       assert isinstance(param, sex.Field)
       assert hasattr(param, 'extract')
       assert hasattr(param, 'assign')

   def test_param_basic_extraction(self, sample_payload_data):
       """Test basic field extraction works."""
       param = Param(name="query", source="q")
       result = param.extract(sample_payload_data)
       assert result == "search term"

   def test_param_with_default(self):
       """Test param with default value."""
       param = Param(name="limit", source="missing_field", default=10)
       result = param.extract({})
       assert result == 10

   def test_param_with_transform(self, sample_payload_data):
       """Test param with transform function."""
       param = Param(
           name="query",
           source="q",
           transform=lambda x: x.upper()
       )
       result = param.extract(sample_payload_data)
       assert result == "SEARCH TERM"

   def test_param_required_missing_raises(self):
       """Test required param raises when missing."""
       param = Param(name="required_field", source="missing", required=True)
       with pytest.raises(ValueError):
           param.extract({})

   def test_param_nested_extraction(self, sample_payload_data):
       """Test nested path extraction."""
       param = Param(name="user_name", source="user.name")
       result = param.extract(sample_payload_data)
       assert result == "john"


class TestParamOperators:
   """Test schematix operator integration with Param."""

   def test_fallback_operator(self, sample_payload_data):
       """Test | operator creates FallbackField."""
       primary = Param(source="missing_field")
       fallback = Param(source="q")

       combined = primary | fallback
       assert isinstance(combined, sex.FallbackField)

       result = combined.extract(sample_payload_data)
       assert result == "search term"

   def test_combine_operator(self, sample_payload_data):
       """Test & operator creates CombinedField."""
       param1 = Param(name="query", source="q")
       param2 = Param(name="size", source="size")

       combined = param1 & param2
       assert isinstance(combined, sex.CombinedField)

       result = combined.extract(sample_payload_data)
       assert isinstance(result, dict)
       assert "query" in result
       assert "size" in result

   def test_nested_operator(self, sample_payload_data):
       """Test @ operator creates NestedField."""
       param = Param(source="name")
       nested = param @ "user"

       assert isinstance(nested, sex.NestedField)
       result = nested.extract(sample_payload_data)
       assert result == "john"

   def test_accumulate_operator(self, sample_payload_data):
       """Test + operator creates AccumulatedField."""
       param1 = Param(source="q")
       param2 = Param(source="user.name")

       accumulated = param1 + param2
       assert isinstance(accumulated, sex.AccumulatedField)

       result = accumulated.extract(sample_payload_data)
       assert result == "search term john"  # Default separator is space


class TestPayloadSchematixIntegration:
   """Test Payload class integration with schematix Schema."""

   def test_payload_inherits_from_schematix_schema(self):
       """Test that Payload properly inherits from schematix Schema."""
       payload = Payload()
       assert isinstance(payload, sex.Schema)
       assert hasattr(payload, 'transform')
       assert hasattr(payload, '_fields')

   def test_payload_field_discovery(self):
       """Test that schematix metaclass discovers Param fields."""
       class TestPayload(Payload):
           query = Param(source="q", target="search_query")
           limit = Param(source="size", target="limit", default=10)

       payload = TestPayload()

       # Check fields were discovered
       assert "query" in payload._fields
       assert "limit" in payload._fields
       assert isinstance(payload._fields["query"], Param)
       assert isinstance(payload._fields["limit"], Param)

   def test_payload_transform(self, sample_payload_data):
       """Test payload transformation using schematix."""
       class TestPayload(Payload):
           search_term = Param(source="q", target="query")
           page_size = Param(source="size", target="limit")

       payload = TestPayload()
       result = payload.transform(sample_payload_data)

       assert isinstance(result, dict)
       assert result["query"] == "search term"
       assert result["limit"] == 20

   def test_payload_with_complex_fields(self, sample_payload_data):
       """Test payload with composed schematix fields."""
       class ComplexPayload(Payload):
           # Fallback field
           search = (
               Param(source="q") |
               Param(source="query") |
               Param(default="*")
           )

           # Nested field
           user_id = Param(source="id") @ "user"

           # Combined field
           user_info = (
               Param(name="user_name", source="name") &
               Param(name="user_id", source="id")
           ) @ "user"

       payload = ComplexPayload()
       result = payload.transform(sample_payload_data)

       assert "search" in result
       assert "user_id" in result
       assert "user_info" in result
       assert result["search"] == "search term"
       assert result["user_id"] == 123

   def test_payload_validation_error(self):
       """Test payload validation raises on missing required fields."""
       class StrictPayload(Payload):
           required_field = Param(source="missing", required=True)

       payload = StrictPayload()
       with pytest.raises(ValueError):
           payload.validate({})

   def test_payload_serialize(self, sample_payload_data):
       """Test payload serialization."""
       class TestPayload(Payload):
           query = Param(source="q")
           limit = Param(source="size", default=10)

       payload = TestPayload()
       result = payload.serialize(sample_payload_data)

       assert isinstance(result, dict)
       assert "query" in result
       assert "limit" in result


class TestSchematixAdvancedFeatures:
   """Test advanced schematix features with ClientFactory integration."""

   def test_bound_schema(self, sample_payload_data):
       """Test schematix bound schema functionality."""
       class TestPayload(Payload):
           query = Param(target="search_query")
           limit = Param(target="page_size")

       payload = TestPayload()

       # Bind to specific source mappings
       bound = payload.bind({
           "query": "q",
           "limit": ("size", lambda x: min(x, 100))  # Transform + limit
       })

       result = bound.serialize(sample_payload_data)
       assert result["search_query"] == "search term"
       assert result["page_size"] == 20

   def test_payload_schema_info(self):
       """Test payload schema introspection."""
       class TestPayload(Payload):
           query = Param(source="q", required=True)
           limit = Param(source="size", default=10)

       payload = TestPayload()
       schema = payload.getschema()

       assert isinstance(schema, dict)
       assert "query" in schema
       assert "limit" in schema
       assert schema["query"]["required"] is True
       assert schema["limit"]["default"] == 10
