# ~/clientfactory/tests/unit/core/models/test_payload.py
"""
Unit tests for Payload and BoundPayload classes.
"""
import pytest
from unittest.mock import Mock
import schematix as sex
from clientfactory.core.models import Param, Payload, BoundPayload, PayloadConfig


class TestPayload:
    """Test Payload functionality."""

    def test_payload_inherits_from_schematix_schema(self):
        """Test Payload inherits from schematix Schema."""
        payload = Payload()
        assert isinstance(payload, sex.Schema)
        assert hasattr(payload, '_fields')
        assert hasattr(payload, '_fieldnames')

    def test_payload_creation_with_config(self):
        """Test payload creation with config."""
        config = PayloadConfig()
        payload = Payload(config=config)

        assert payload._config == config
        assert payload.getconfig() == config

    def test_payload_creation_without_config(self):
        """Test payload creation without config creates default."""
        payload = Payload()

        assert isinstance(payload._config, PayloadConfig)

    def test_payload_field_discovery(self):
        """Test schematix metaclass discovers Param fields."""
        class TestPayload(Payload):
            name = Param(source="full_name")
            age = Param(source="years", default=0)
            email = Param(source="email_address", required=True)

        payload = TestPayload()

        # Check fields were discovered
        assert "name" in payload._fields
        assert "age" in payload._fields
        assert "email" in payload._fields

        # Check field types
        assert isinstance(payload._fields["name"], Param)
        assert isinstance(payload._fields["age"], Param)
        assert isinstance(payload._fields["email"], Param)

        # Check field properties
        assert payload._fields["name"].source == "full_name"
        assert payload._fields["age"].default == 0
        assert payload._fields["email"].required is True


    def test_payload_field_names_set_by_metaclass(self):
        """Test field names are set by metaclass via __set_name__."""
        class TestPayload(Payload):
            user_id = Param()
            user_name = Param()

        payload = TestPayload()

        # Names should be set by __set_name__
        assert payload._fields["user_id"].name == "user_id"
        assert payload._fields["user_name"].name == "user_name"

        # Targets should default to names
        assert payload._fields["user_id"].target == "user_id"
        assert payload._fields["user_name"].target == "user_name"

    def test_payload_transform_uses_targets(self):
        """Test transform uses target values as output keys."""
        class TestPayload(Payload):
            search_term = Param(source="q", target="query")
            page_size = Param(source="size", target="limit")

        payload = TestPayload()
        data = {"q": "python", "size": 50}

        result = payload.transform(data)

        # Should use target values as keys
        assert result == {"query": "python", "limit": 50}

    def test_payload_transform_fallback_to_fieldname(self):
        """Test transform falls back to field name when no target."""
        class TestPayload(Payload):
            query = Param(source="q")  # No target specified

        payload = TestPayload()
        data = {"q": "search"}

        result = payload.transform(data)

        # Should use field name as key
        assert result == {"query": "search"}

    def test_payload_transform_with_type_target(self):
        """Test transform with type conversion."""
        class TestPayload(Payload):
            name = Param(source="name")

        payload = TestPayload()
        data = {"name": "John"}

        # Mock the _typeconvert method
        payload._typeconvert = Mock(return_value={"converted": True})

        result = payload.transform(data, typetarget=dict)

        # Should call _typeconvert
        payload._typeconvert.assert_called_once()
        assert result == {"converted": True}

    def test_payload_transform_error_handling(self):
        """Test transform error handling."""
        class TestPayload(Payload):
            required_field = Param(source="missing", required=True)

        payload = TestPayload()
        data = {}

        with pytest.raises(ValueError, match="Transform failed on field 'required_field'"):
            payload.transform(data)

    def test_payload_validate_success(self):
        """Test validate method with valid data."""
        class TestPayload(Payload):
            name = Param(source="name", required=True)
            age = Param(source="age", default=0)

        payload = TestPayload()
        data = {"name": "John", "age": 25}

        result = payload.validate(data)

        # Should return transformed data
        assert result == {"name": "John", "age": 25}

    def test_payload_serialize(self):
        """Test serialize method."""
        class TestPayload(Payload):
            name = Param(source="name")

        payload = TestPayload()
        data = {"name": "John"}

        result = payload.serialize(data)

        # Should return same as transform
        assert result == {"name": "John"}

    def test_payload_get_schema(self):
        """Test getschema method."""
        class TestPayload(Payload):
            name = Param(source="full_name", target="user_name", required=True, default="Unknown")
            age = Param(source="years")

        payload = TestPayload()
        schema = payload.getschema()

        expected = {
            "name": {
                "name": "name",
                "required": True,
                "default": "Unknown",
                "source": "full_name",
                "target": "user_name"
            },
            "age": {
                "name": "age",
                "required": False,
                "default": None,
                "source": "years",
                "target": "age"  # Should default to field name
            }
        }

        assert schema == expected

    def test_payload_bind_creates_bound_payload(self):
        """Test bind method creates BoundPayload."""
        class TestPayload(Payload):
            name = Param(target="user_name")
            age = Param(target="user_age")

        payload = TestPayload()

        bound = payload.bind({
            "name": "full_name",
            "age": ("years", lambda x: max(x, 0))
        })

        assert isinstance(bound, BoundPayload)
        assert bound._config == payload._config

    def test_payload_with_complex_fields(self):
        """Test payload with schematix operator compositions."""
        class ComplexPayload(Payload):
            # Fallback field
            search = (
                Param(source="q") |
                Param(source="query") |
                Param(default="*")
            )

            # Combined field
            user_info = (
                Param(name="user_name", source="name", target="name") &
                Param(name="user_id", source="id", target="id")
            )

        payload = ComplexPayload()
        data = {"q": "python", "name": "John", "id": 123}

        result = payload.transform(data)

        # Should handle complex field compositions
        assert "search" in result
        assert "user_info" in result
        assert result["search"] == "python"
        assert isinstance(result["user_info"], dict)


class TestBoundPayload:
    """Test BoundPayload functionality."""

    def test_bound_payload_creation(self):
        """Test BoundPayload creation."""
        mock_bound_schema = Mock()
        config = PayloadConfig()

        bound = BoundPayload(boundto=mock_bound_schema, config=config)

        assert bound.boundto == mock_bound_schema
        assert bound._config == config

    def test_bound_payload_serialize(self):
        """Test BoundPayload serialize method."""
        # Create a real payload and bind it
        class TestPayload(Payload):
            name = Param(target="user_name")
            age = Param(target="user_age")

        payload = TestPayload()
        bound = payload.bind({
            "name": "full_name",
            "age": "years"
        })

        data = {"full_name": "John Doe", "years": 30}
        result = bound.serialize(data)

        # Should preserve target keys
        assert result == {"user_name": "John Doe", "user_age": 30}

    def test_bound_payload_serialize_with_transform(self):
        """Test BoundPayload with transform functions."""
        class TestPayload(Payload):
            age = Param(target="user_age")

        payload = TestPayload()
        bound = payload.bind({
            "age": ("raw_age", lambda x: max(x, 0))  # Ensure non-negative
        })

        data = {"raw_age": -5}
        result = bound.serialize(data)

        assert result == {"user_age": 0}

    def test_bound_payload_serialize_missing_field(self):
        """Test BoundPayload handles missing fields."""
        class TestPayload(Payload):
            required_field = Param(required=True)

        payload = TestPayload()
        bound = payload.bind({
            "required_field": "missing_source"
        })

        data = {}

        with pytest.raises(ValueError, match="Bound transform failed"):
            bound.serialize(data)

    def test_bound_payload_preserves_original_targets(self):
        """Test that binding preserves original target values."""
        class TestPayload(Payload):
            search_term = Param(target="query")
            page_size = Param(target="limit")

        payload = TestPayload()
        bound = payload.bind({
            "search_term": "q",
            "page_size": "size"
        })

        data = {"q": "python", "size": 25}
        result = bound.serialize(data)

        # Should use original targets, not field names
        assert result == {"query": "python", "limit": 25}


class TestPayloadEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_payload(self):
        """Test payload with no fields."""
        class EmptyPayload(Payload):
            pass

        payload = EmptyPayload()
        result = payload.transform({})

        assert result == {}

    def test_payload_with_none_values(self):
        """Test payload handling None values."""
        class TestPayload(Payload):
            optional = Param(source="opt", default="fallback")
            nullable = Param(source="null")

        payload = TestPayload()
        data = {"null": None}

        result = payload.transform(data)

        assert result == {"optional": "fallback", "nullable": None}

    def test_payload_field_name_conflicts(self):
        """Test payload with field name conflicts."""
        class TestPayload(Payload):
            # Both target the same output key
            field1 = Param(source="src1", target="output")
            field2 = Param(source="src2", target="output")

        payload = TestPayload()
        data = {"src1": "value1", "src2": "value2"}

        result = payload.transform(data)

        # Last field should win
        assert result == {"output": "value2"}

    def test_payload_inheritance(self):
        """Test payload class inheritance."""
        class BasePayload(Payload):
            common = Param(source="common_field")

        class ExtendedPayload(BasePayload):
            specific = Param(source="specific_field")

        payload = ExtendedPayload()

        # Should have fields from both classes
        assert "common" in payload._fields
        assert "specific" in payload._fields

        data = {"common_field": "base", "specific_field": "extended"}
        result = payload.transform(data)

        assert result == {"common": "base", "specific": "extended"}
