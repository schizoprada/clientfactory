# ~/clientfactory/tests/unit/backends/test_gql_basic.py
"""
Basic unit tests for GraphQL backend implementation.
"""
import pytest
from unittest.mock import Mock

from clientfactory.backends.graphql import GQLBackend, GQLConfig
from clientfactory.core.models import RequestModel, ResponseModel, HTTPMethod


class TestGQLBackend:
    """Test basic GraphQL backend functionality."""

    def test_gql_backend_creation(self):
        """Test basic GQL backend creation."""
        backend = GQLBackend(
            endpoint="/graphql",
            introspection=True
        )

        assert isinstance(backend, GQLBackend)
        assert backend.endpoint == "/graphql"
        assert backend.introspection is True

    def test_gql_config_defaults(self):
        """Test GQLConfig default values."""
        config = GQLConfig()

        assert config.endpoint == "/graphql"
        assert config.introspection is True
        assert config.maxdepth == 10

    def test_format_request_basic(self):
        """Test basic GraphQL request formatting."""
        backend = GQLBackend()

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com"
        )

        data = {
            "query": "query GetUser($id: ID!) { user(id: $id) { name email } }",
            "variables": {"id": "123"},
            "operationName": "GetUser"
        }

        formatted = backend._formatrequest(request, data)

        assert formatted.method == HTTPMethod.POST
        assert formatted.headers["Content-Type"] == "application/json"

        # Check GraphQL request structure
        assert formatted.json["query"] == data["query"]
        assert formatted.json["variables"] == {"id": "123"}
        assert formatted.json["operationName"] == "GetUser"

    def test_format_request_no_operation_name(self):
        """Test GraphQL request formatting without operation name."""
        backend = GQLBackend()

        request = RequestModel(
            method=HTTPMethod.POST,
            url="https://api.example.com"
        )

        data = {
            "query": "{ user { name } }",
            "variables": {}
        }

        formatted = backend._formatrequest(request, data)

        assert "operationName" not in formatted.json
        assert formatted.json["query"] == "{ user { name } }"
        assert formatted.json["variables"] == {}

    def test_process_response_success(self):
        """Test successful GraphQL response processing."""
        backend = GQLBackend()

        response_data = {
            "data": {
                "user": {"name": "John Doe", "email": "john@example.com"}
            }
        }

        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{}',
            url="https://api.example.com/graphql",
            jsondata=response_data
        )

        result = backend._processresponse(response)

        assert result["data"]["user"]["name"] == "John Doe"
        assert result["errors"] == []

    def test_process_response_with_errors(self):
        """Test GraphQL response processing with errors."""
        backend = GQLBackend(raiseonerror=True)

        response_data = {
            "data": None,
            "errors": [
                {"message": "User not found", "path": ["user"]},
                {"message": "Invalid ID format"}
            ]
        }

        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"data": null, "errors": [...]}',  # Add actual content
            url="https://api.example.com/graphql",
            jsondata=response_data
        )

        with pytest.raises(RuntimeError):
            backend._processresponse(response)

    def test_process_response_errors_no_raise(self):
        """Test GraphQL response with errors when raiseonerror is False."""
        backend = GQLBackend(raiseonerror=False)

        response_data = {
            "data": None,
            "errors": [{"message": "User not found"}]
        }

        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{}',
            url="https://api.example.com/graphql",
            jsondata=response_data
        )

        result = backend._processresponse(response)

        assert result["data"] is None
        assert len(result["errors"]) == 1
        assert result["errors"][0]["message"] == "User not found"

    def test_format_request_empty_data(self):
        """Test GraphQL request formatting with empty data."""
        backend = GQLBackend()

        request = RequestModel(
            method=HTTPMethod.POST,
            url="https://api.example.com"
        )

        formatted = backend._formatrequest(request, {})

        assert formatted is request
        assert formatted.json is None

    def test_process_response_http_error(self):
        """Test GraphQL response processing with HTTP error."""
        backend = GQLBackend()

        response = ResponseModel(
            statuscode=500,
            headers={},
            content=b'Internal Server Error',
            url="https://api.example.com/graphql"
        )

        result = backend._processresponse(response)

        # Should return the response object for HTTP errors
        assert result is response
