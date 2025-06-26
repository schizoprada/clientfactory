# ~/clientfactory/tests/unit/misc/test_method_config_request_applied.py

import pytest
from unittest.mock import Mock, patch

from clientfactory.core.models import MethodConfig, RequestModel, HTTPMethod, MergeMode
from clientfactory.core.bases import BaseClient, BaseResource
from clientfactory.decorators.http.methods import get, post
from clientfactory.core.resource import Resource
from clientfactory.core.client import Client


class TestMethodConfigApplication:
    """Test that method configs are properly applied to requests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_engine.send.return_value = Mock(statuscode=200)

    def test_method_headers_applied_to_request(self):
        """Test that method-specific headers are applied to requests."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get(headers={"X-Method": "test", "Authorization": "Bearer method-token"})
            def test_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)

        # Call the method
        client.test_endpoint()

        # Verify engine.send was called with headers
        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        assert isinstance(request, RequestModel)
        assert request.headers["X-Method"] == "test"
        assert request.headers["Authorization"] == "Bearer method-token"

    def test_method_cookies_applied_to_request(self):
        """Test that method-specific cookies are applied to requests."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get(cookies={"method_cookie": "value123", "session_id": "abc"})
            def test_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)
        client.test_endpoint()

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        assert request.cookies["method_cookie"] == "value123"
        assert request.cookies["session_id"] == "abc"

    def test_method_timeout_applied_to_request(self):
        """Test that method-specific timeout is applied to requests."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get(timeout=45.0)
            def test_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)
        client.test_endpoint()

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        assert request.timeout == 45.0

    def test_header_merge_mode_merge(self):
        """Test header merge mode MERGE behavior."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get(headers={"X-Method": "test"}, headermode=MergeMode.MERGE)
            def test_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)

        # Call with additional headers
        client.test_endpoint(headers={"X-Extra": "extra"})

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        # Both headers should be present
        assert request.headers["X-Method"] == "test"
        assert request.headers["X-Extra"] == "extra"

    def test_header_merge_mode_overwrite(self):
        """Test header merge mode OVERWRITE behavior."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get(headers={"X-Method": "test"}, headermode=MergeMode.OVERWRITE)
            def test_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)

        # Call with additional headers
        client.test_endpoint(headers={"X-Extra": "extra"})

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        # Only method headers should be present
        assert request.headers["X-Method"] == "test"
        assert "X-Extra" not in request.headers

    def test_cookie_merge_mode_merge(self):
        """Test cookie merge mode MERGE behavior."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get(cookies={"method_cookie": "value"}, cookiemode=MergeMode.MERGE)
            def test_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)

        # Call with additional cookies
        client.test_endpoint(cookies={"extra_cookie": "extra"})

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        # Both cookies should be present
        assert request.cookies["method_cookie"] == "value"
        assert request.cookies["extra_cookie"] == "extra"

    def test_cookie_merge_mode_overwrite(self):
        """Test cookie merge mode OVERWRITE behavior."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get(cookies={"method_cookie": "value"}, cookiemode=MergeMode.OVERWRITE)
            def test_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)

        # Call with additional cookies
        client.test_endpoint(cookies={"extra_cookie": "extra"})

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        # Only method cookies should be present
        assert request.cookies["method_cookie"] == "value"
        assert "extra_cookie" not in request.cookies

    def test_resource_method_configs_applied(self):
        """Test that method configs work on resource methods."""

        from clientfactory.core.models import ResourceConfig

        class TestResource(Resource):

            @post(headers={"X-Resource": "test"}, timeout=30.0)
            def create_item(self): pass

        mock_client = Mock()
        mock_client.baseurl = "https://api.example.com"
        mock_client._engine = self.mock_engine
        mock_client._backend = None  # Disable backend processing

        resource = TestResource(client=mock_client, config=ResourceConfig(name="test", path="test"))
        resource.create_item()

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        print(f"Request type: {type(request)}")
        print(f"Request headers type: {type(request.headers)}")
        print(f"Request headers: {request.headers}")
        print(f"Request timeout: {request.timeout}")

        assert request.headers["X-Resource"] == "test"
        assert request.timeout == 30.0

    def test_multiple_configs_applied_together(self):
        """Test that multiple method config options work together."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post(
                headers={"X-Method": "complex"},
                cookies={"method_session": "abc123"},
                timeout=60.0,
                headermode=MergeMode.MERGE,
                cookiemode=MergeMode.OVERWRITE
            )
            def complex_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)
        client.complex_endpoint()

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        assert request.headers["X-Method"] == "complex"
        assert request.cookies["method_session"] == "abc123"
        assert request.timeout == 60.0

    def test_method_config_overrides_request_defaults(self):
        """Test that method config overrides request defaults."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get(timeout=45.0)
            def test_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)

        # Call with different timeout - method config should win
        client.test_endpoint(timeout=30.0)

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        # Method config timeout should override call-time timeout
        assert request.timeout == 45.0

    def test_no_method_config_preserves_defaults(self):
        """Test that methods without configs still work normally."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get
            def simple_endpoint(self): pass

        client = TestClient(engine=self.mock_engine)
        client.simple_endpoint(headers={"X-Call": "test"}, timeout=20.0)

        call_args = self.mock_engine.send.call_args[0]
        request = call_args[0]

        assert request.headers["X-Call"] == "test"
        assert request.timeout == 20.0
