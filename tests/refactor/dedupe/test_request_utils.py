# tests/refactor/dedupe/test_request_utils.py
"""Test extracted request utilities work correctly."""
import pytest
from clientfactory.core.models import HTTPMethod, RequestModel
from clientfactory.core.utils.request import resolveargs, substitute, separatekwargs, buildrequest


class TestPathUtils:
    """Test path utilities."""

    def test_resolveargs_basic(self):
        """Test basic path args resolution."""
        result = resolveargs("/users/{id}/posts/{post_id}", 123, 456, name="John")
        expected = {"id": 123, "post_id": 456, "name": "John"}
        assert result == expected

    def test_substitute_basic(self):
        """Test basic path substitution."""
        path, consumed = substitute("/users/{id}", id=123, name="John")
        assert path == "/users/123"
        assert consumed == ["id"]


class TestBuildingUtils:
    """Test request building utilities."""

    def test_separatekwargs_get(self):
        """Test kwargs separation for GET."""
        fields, body = separatekwargs(HTTPMethod.GET, headers={"X-Test": "1"}, query="test")
        assert "headers" in fields
        assert "params" in fields
        assert fields["params"]["query"] == "test"
        assert body == {}

    def test_separatekwargs_post(self):
        """Test kwargs separation for POST."""
        fields, body = separatekwargs(HTTPMethod.POST, headers={"X-Test": "1"}, name="John", email="test@test.com")
        assert "headers" in fields
        assert body["name"] == "John"
        assert body["email"] == "test@test.com"

    def test_buildrequest_client(self):
        """Test request building for client context."""
        request = buildrequest(
            method=HTTPMethod.GET,
            baseurl="https://api.example.com",
            path="users",
            headers={"X-Test": "1"}
        )
        assert request.method == HTTPMethod.GET
        assert request.url == "https://api.example.com/users"
        assert request.headers["X-Test"] == "1"

    def test_buildrequest_resource(self):
        """Test request building for resource context."""
        request = buildrequest(
            method=HTTPMethod.GET,
            baseurl="https://api.example.com",
            path="123",
            resourcepath="users",
            headers={"X-Test": "1"}
        )
        assert request.method == HTTPMethod.GET
        assert request.url == "https://api.example.com/users/123"
