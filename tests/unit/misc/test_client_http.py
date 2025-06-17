# ~/clientfactory/tests/unit/misc/test_client_http.py
"""
Unit tests for client-level HTTP methods.
"""
import pytest
from unittest.mock import Mock

from clientfactory.core import Client
from clientfactory.decorators.http import get, post, put, delete
from clientfactory.core.models import HTTPMethod


class TestClientHTTPMethods:
    """Test client-level decorated HTTP methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_session = Mock()
        self.mock_engine._session = self.mock_session

    def test_client_get_method(self):
        """Test GET method on client."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get("health")
            def health_check(self): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        # Call the method
        client.health_check()

        # Verify request was sent
        self.mock_session.send.assert_called_once()
        request = self.mock_session.send.call_args[0][0]
        assert request.method == HTTPMethod.GET
        assert request.url == "https://api.example.com/health"

    def test_client_post_method(self):
        """Test POST method on client."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("auth/login")
            def login(self, username, password): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.login(username="user", password="pass")

        request = self.mock_session.send.call_args[0][0]
        assert request.method == HTTPMethod.POST
        assert request.url == "https://api.example.com/auth/login"
        assert request.json == {"username": "user", "password": "pass"}

    def test_client_method_without_path(self):
        """Test client method without path (just baseurl)."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get()
            def root(self): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.root()

        request = self.mock_session.send.call_args[0][0]
        assert request.url == "https://api.example.com"

    def test_client_method_with_backend(self):
        """Test client method with backend processing."""
        mock_backend = Mock()
        mock_backend.formatrequest.return_value = Mock()
        mock_backend.processresponse.return_value = {"processed": True}

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get("data")
            def get_data(self): pass

        client = TestClient(engine=self.mock_engine, backend=mock_backend)
        client._engine._session.send.return_value = Mock()

        result = client.get_data()

        # Backend should be called
        mock_backend.formatrequest.assert_called_once()
        mock_backend.processresponse.assert_called_once()
        assert result == {"processed": True}

    def test_client_multiple_methods(self):
        """Test client with multiple decorated methods."""
        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get("users")
            def get_users(self): pass

            @post("users")
            def create_user(self, **data): pass

            @delete("users/{id}")
            def delete_user(self, id): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        # Test all methods exist and are callable
        assert hasattr(client, 'get_users')
        assert hasattr(client, 'create_user')
        assert hasattr(client, 'delete_user')

        # Test they make requests
        client.get_users()
        client.create_user(name="John")
        client.delete_user(id=123)

        # Should have made 3 requests
        assert self.mock_session.send.call_count == 3

        # Check the URLs
        calls = self.mock_session.send.call_args_list
        assert calls[0][0][0].url == "https://api.example.com/users"
        assert calls[1][0][0].url == "https://api.example.com/users"
        assert calls[2][0][0].url == "https://api.example.com/users/123"

    def test_client_method_discovery_inheritance(self):
        """Test method discovery works with inheritance."""
        class BaseClient(Client):
            baseurl = "https://api.example.com"

            @get("base")
            def base_method(self): pass

        class ExtendedClient(BaseClient):
            @post("extended")
            def extended_method(self): pass

        client = ExtendedClient(engine=self.mock_engine)

        # Should have both methods
        assert hasattr(client, 'base_method')
        assert hasattr(client, 'extended_method')

    def test_client_baseurl_variations(self):
        """Test different baseurl formats."""
        test_cases = [
            "https://api.example.com",      # no trailing slash
            "https://api.example.com/",     # trailing slash
            "https://api.example.com/v1",   # with path
            "https://api.example.com/v1/",  # with path and slash
        ]

        for testurl in test_cases:
            class TestClient(Client):
                baseurl = testurl

                @get("test")
                def test_method(self): pass

            client = TestClient(engine=self.mock_engine)
            client._engine._session.send.return_value = Mock()

            client.test_method()

            request = self.mock_session.send.call_args[0][0]
            # Should always result in clean URL construction
            assert "/test" in request.url
            assert "//" not in request.url.replace("https://", "")
