# ~/clientfactory/tests/unit/misc/test_path_payload_conflict.py
"""
Unit tests for path vs payload parameter conflict resolution using args/kwargs.
"""
import pytest
from unittest.mock import Mock

from clientfactory.core import Client, Resource
from clientfactory.decorators.http import get, post
from clientfactory.core.models import HTTPMethod, ResourceConfig, Payload, Param


class TestPathPayloadConflicts:
    """Test args vs kwargs for path vs payload parameters."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_session = Mock()
        self.mock_engine._session = self.mock_session

    def test_client_args_override_kwargs_for_path(self):
        """Test that positional args override kwargs for path parameters."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("users/{id}")
            def update_user(self, id, /, **kwargs): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        # Args should take precedence for path, kwargs for payload
        client.update_user(123, id=456, name="John")

        request = self.mock_session.send.call_args[0][0]
        # Path should use arg value (123)
        assert request.url == "https://api.example.com/users/123"
        # Payload should only have remaining kwargs (no id since it was consumed for path)
        assert request.json == {"name": "John"}

    def test_resource_args_override_kwargs_for_path(self):
        """Test args vs kwargs for resource methods."""
        class TestResource(Resource):
            @post("{category}/{id}")
            def update_item(self, category, id, **kwargs): pass

        mock_client = Mock()
        mock_client.baseurl = "https://api.example.com"
        mock_client._engine = self.mock_engine
        mock_client._backend = None

        resource = TestResource(
            client=mock_client,
            config=ResourceConfig(name="items", path="items")
        )
        resource._session.send.return_value = Mock()

        # Multiple path params via args
        resource.update_item("books", 456, id=789, title="Python Guide")

        request = resource._session.send.call_args[0][0]
        # Path should use args (books, 456)
        assert request.url == "https://api.example.com/items/books/456"
        # Payload should only have remaining kwargs
        assert request.json == {"title": "Python Guide"}

    def test_client_with_payload_class(self):
        """Test args vs kwargs with actual Payload class."""
        class UserPayload(Payload):
            id = Param(source="user_id")  # Different target name
            name = Param(required=True)
            email = Param()

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("groups/{id}/members", payload=UserPayload)
            def add_member(self, id, **kwargs): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        # Path id vs payload id (with different semantics)
        client.add_member(999, id=123, name="John", email="john@example.com")

        request = self.mock_session.send.call_args[0][0]
        # Path should use arg (group id = 999)
        assert request.url == "https://api.example.com/groups/999/members"
        # Payload should have user data (user id = 123)
        assert request.json == {"name": "John", "email": "john@example.com"}

    def test_fallback_to_kwargs_when_no_args(self):
        """Test fallback to kwargs when no positional args provided."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get("users/{id}")
            def get_user(self, id): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        # No args provided, should fallback to kwargs
        client.get_user(id=456)

        request = self.mock_session.send.call_args[0][0]
        assert request.url == "https://api.example.com/users/456"

    def test_partial_args_with_kwargs_fallback(self):
        """Test partial args with kwargs fallback for remaining path params."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("teams/{team_id}/projects/{project_id}")
            def update_project(self, team_id, project_id, **kwargs): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        # Provide first path param as arg, second as kwarg
        client.update_project("dev", project_id=789, name="New Project")

        request = self.mock_session.send.call_args[0][0]
        assert request.url == "https://api.example.com/teams/dev/projects/789"
        assert request.json == {"name": "New Project"}

    def test_too_many_args_ignored(self):
        """Test that extra args beyond path parameters are ignored."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("users/{id}")
            def update_user(self, id, **kwargs): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        # Extra args should be ignored
        client.update_user(123, "extra", "args", name="John")

        request = self.mock_session.send.call_args[0][0]
        assert request.url == "https://api.example.com/users/123"
        assert request.json == {"name": "John"}

    def test_no_path_parameters_all_kwargs_go_to_payload(self):
        """Test that when there are no path params, all kwargs go to payload."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("users")
            def create_user(self, **kwargs): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.create_user("ignored_arg", name="John", email="john@example.com")

        request = self.mock_session.send.call_args[0][0]
        assert request.url == "https://api.example.com/users"
        assert request.json == {"name": "John", "email": "john@example.com"}

    def test_preprocess_works_with_args_extraction(self):
        """Test that preprocess still works after args extraction."""
        def add_timestamp(data):
            return {**data, "timestamp": "2025-01-01"}

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("users/{id}", preprocess=add_timestamp)
            def update_user(self, id, **kwargs): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.update_user(123, name="John")

        request = self.mock_session.send.call_args[0][0]
        assert request.url == "https://api.example.com/users/123"
        # Should have preprocessed data
        assert request.json == {"name": "John", "timestamp": "2025-01-01"}
