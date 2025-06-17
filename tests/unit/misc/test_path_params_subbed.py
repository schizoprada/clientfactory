# ~/clientfactory/tests/unit/misc/test_path_params_subbed.py
"""
Unit tests for path parameter substitution in HTTP decorators.
"""
import pytest
from unittest.mock import Mock

from clientfactory.core import Client, Resource
from clientfactory.decorators.http import get, post
from clientfactory.core.models import HTTPMethod, ResourceConfig


class TestPathParameterSubstitution:
    """Test path parameter substitution for both clients and resources."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_session = Mock()
        self.mock_engine._session = self.mock_session

    def test_resource_single_path_param(self):
        """Test single path parameter substitution in resources."""
        class TestResource(Resource):
            @get("{id}")
            def get_item(self, id): pass

        mock_client = Mock()
        mock_client.baseurl = "https://api.example.com"
        mock_client._engine = self.mock_engine
        mock_client._backend = None

        resource = TestResource(
            client=mock_client,
            config=ResourceConfig(name="items", path="items")
        )

        # Mock the session response
        resource._session.send.return_value = Mock()

        # Call the method
        resource.get_item(id=123)

        # Verify the request was built with substituted path
        call_args = resource._session.send.call_args[0][0]  # First arg (request)
        assert call_args.url == "https://api.example.com/items/123"
        assert call_args.method == HTTPMethod.GET

    def test_resource_multiple_path_params(self):
        """Test multiple path parameters in resources."""
        class TestResource(Resource):
            @get("{category}/{id}")
            def get_item(self, category, id): pass

        mock_client = Mock()
        mock_client.baseurl = "https://api.example.com"
        mock_client._engine = self.mock_engine
        mock_client._backend = None

        resource = TestResource(
            client=mock_client,
            config=ResourceConfig(name="items", path="items")
        )

        resource._session.send.return_value = Mock()

        resource.get_item(category="books", id=456)

        call_args = resource._session.send.call_args[0][0]
        assert call_args.url == "https://api.example.com/items/books/456"

    def test_client_single_path_param(self):
        """Test single path parameter substitution in clients."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get("users/{id}")
            def get_user(self, id): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.get_user(id=789)

        call_args = client._engine._session.send.call_args[0][0]
        assert call_args.url == "https://api.example.com/users/789"
        assert call_args.method == HTTPMethod.GET

    def test_client_multiple_path_params(self):
        """Test multiple path parameters in clients."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("teams/{team_id}/members/{user_id}")
            def add_member(self, team_id, user_id): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.add_member(team_id="dev", user_id=123)

        call_args = client._engine._session.send.call_args[0][0]
        assert call_args.url == "https://api.example.com/teams/dev/members/123"
        assert call_args.method == HTTPMethod.POST

    def test_missing_path_parameter_raises_error(self):
        """Test that missing path parameters raise ValueError."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get("users/{id}")
            def get_user(self, id): pass

        client = TestClient(engine=self.mock_engine)

        with pytest.raises(ValueError, match="Missing path parameter"):
            client.get_user()  # Missing id parameter

    def test_path_substitution_with_extra_kwargs(self):
        """Test path substitution works with extra kwargs."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("users/{id}")
            def update_user(self, id, **kwargs): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.update_user(id=123, name="John", email="john@example.com")

        call_args = client._engine._session.send.call_args[0][0]
        assert call_args.url == "https://api.example.com/users/123"
        # Extra kwargs should still be in the request
        assert call_args.json == {"name": "John", "email": "john@example.com"}
