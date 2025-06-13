# ~/clientfactory/tests/unit/core/test_client.py
# tests/unit/core/test_client.py
"""
Unit tests for concrete Client implementation.
"""
import pytest
from unittest.mock import Mock, patch

from clientfactory.core.client import Client
from clientfactory.core.resource import Resource
from clientfactory.core.models import ClientConfig, ResourceConfig, MethodConfig, HTTPMethod


class TestClient:
    """Test concrete Client functionality."""

    def test_client_creation_basic(self):
        """Test basic client creation."""
        client = Client()

        assert isinstance(client, Client)
        assert client.baseurl == ''
        assert client._closed is False
        assert isinstance(client._resources, dict)

    def test_client_creation_with_config(self):
        """Test client creation with config."""
        config = ClientConfig(
            baseurl="https://api.example.com",
            timeout=60.0,
            verifyssl=False
        )
        client = Client(config=config)

        assert client._config.baseurl == "https://api.example.com"
        assert client._config.timeout == 60.0
        assert client._config.verifyssl is False

    def test_client_creation_with_kwargs(self):
        """Test client creation with kwargs."""
        client = Client(
            baseurl="https://api.test.com",
            timeout=45.0
        )

        assert client.baseurl == "https://api.test.com"
        assert client._config.timeout == 45.0

    def test_client_has_engine(self):
        """Test that client has an engine by default."""
        client = Client()

        assert client._engine is not None
        # Should have RequestsEngine by default
        from clientfactory.engines.requestslib import RequestsEngine
        assert isinstance(client._engine, RequestsEngine)

    def test_register_resource(self):
        """Test registering a resource."""
        client = Client()

        # Create mock resource
        mock_resource = Mock()
        mock_resource.__class__.__name__ = "TestResource"

        client._registerresource(mock_resource, "custom_name")

        assert "custom_name" in client._resources
        assert client._resources["custom_name"] is mock_resource
        assert hasattr(client, "custom_name")

    def test_register_resource_default_name(self):
        """Test registering resource with default name."""
        client = Client()

        # Create mock resource
        mock_resource = Mock()
        mock_resource.__class__.__name__ = "TestResource"

        client._registerresource(mock_resource)

        assert "testresource" in client._resources
        assert hasattr(client, "testresource")

    def test_get_resource(self):
        """Test getting a resource by name."""
        client = Client()
        mock_resource = Mock()

        client._registerresource(mock_resource, "test")

        result = client.getresource("test")
        assert result is mock_resource

        # Non-existent resource should return None
        assert client.getresource("nonexistent") is None

    def test_add_resource(self):
        """Test adding a resource."""
        client = Client()
        mock_resource = Mock()
        mock_resource.__class__.__name__ = "TestResource"

        client.addresource(mock_resource, "added")

        assert "added" in client._resources
        assert client.getresource("added") is mock_resource

    def test_remove_resource(self):
        """Test removing a resource."""
        client = Client()
        mock_resource = Mock()

        client._registerresource(mock_resource, "test")
        assert "test" in client._resources
        assert hasattr(client, "test")

        client.removeresource("test")

        assert "test" not in client._resources
        assert not hasattr(client, "test")

    def test_list_resources(self):
        """Test listing all resource names."""
        client = Client()

        mock_resource1 = Mock()
        mock_resource2 = Mock()

        client._registerresource(mock_resource1, "resource1")
        client._registerresource(mock_resource2, "resource2")

        resources = client.listresources()

        assert "resource1" in resources
        assert "resource2" in resources
        assert len(resources) == 2

    def test_discover_resources(self):
        """Test resource discovery from nested classes."""
        # Create a client class with nested resources
        class TestClient(Client):
            class Users(Resource):
                pass

            class Posts(Resource):
                pass

            class NotAResource:
                pass

        client = TestClient()

        # Should have discovered the Resource classes
        assert "users" in client._resources
        assert "posts" in client._resources
        assert isinstance(client._resources["users"], Resource)
        assert isinstance(client._resources["posts"], Resource)

        # Should not have discovered the non-Resource class
        assert "notaresource" not in client._resources

    def test_discover_resources_with_config(self):
        """Test resource discovery with resource configs."""
        # Create a resource class with config
        class TestResourceClass(Resource):
            pass

        # Add config to the class
        TestResourceClass._resourceconfig = ResourceConfig(
            name="test_resource",
            path="test"
        )

        class TestClient(Client):
            TestResource = TestResourceClass

        client = TestClient()

        assert "testresource" in client._resources
        discovered_resource = client._resources["testresource"]
        assert discovered_resource._config.name == "test_resource"
        assert discovered_resource._config.path == "test"

    def test_client_with_engine_override(self):
        """Test client with custom engine."""
        mock_engine = Mock()

        client = Client(engine=mock_engine)

        assert client._engine is mock_engine

    def test_client_with_backend_override(self):
        """Test client with custom backend."""
        mock_backend = Mock()

        client = Client(backend=mock_backend)

        assert client._backend is mock_backend

    def test_client_close(self):
        """Test client close functionality."""
        client = Client()

        assert client._closed is False

        client.close()

        assert client._closed is True

    def test_client_context_manager(self):
        """Test client context manager."""
        client = Client()

        with client as ctx_client:
            assert ctx_client is client
            assert client._closed is False

        assert client._closed is True

    def test_integration_with_real_resource(self):
        """Test integration with actual Resource instances."""
        class TestClient(Client):
            class Users(Resource):
                def get_user(self):
                    pass

        # Add method config to the method
        TestClient.Users.get_user._methodconfig = MethodConfig(
            name="get_user",
            method=HTTPMethod.GET,
            path="{id}"
        )

        client = TestClient(baseurl="https://api.example.com")

        # Check that resource was discovered and configured
        assert "users" in client._resources
        users_resource = client._resources["users"]

        assert isinstance(users_resource, Resource)
        assert users_resource._client is client
        assert hasattr(client, "users")
        assert client.users is users_resource

    def test_client_component_resolution(self):
        """Test that client resolves components correctly."""
        # Test with declarative components
        class TestAuth:
            pass

        class TestClient(Client):
            __auth__ = TestAuth

        #print(f"DEBUG test: TestClient.__declcomps__ = {getattr(TestClient, '__declcomps__', 'NOT_FOUND')}")
        #print(f"DEBUG test: TestClient._declcomponents = {getattr(TestClient, '_declcomponents', 'NOT_FOUND')}")


        client = TestClient()

        #print(f"DEBUG test: client.auth = {client.auth}")

        # Should have resolved auth component
        assert client.auth is not None
        assert isinstance(client.auth, TestAuth)

    def test_client_attribute_resolution(self):
        """Test that client resolves attributes correctly."""
        class TestClient(Client):
            baseurl = "https://declarative.example.com"
            version = "2.0.0"
            description = "Test client"

        client = TestClient()

        assert client.baseurl == "https://declarative.example.com"
        assert client._version == "2.0.0"

    def test_client_config_resolution(self):
        """Test that client resolves config correctly."""
        class TestClient(Client):
            timeout = 120.0
            verifyssl = False

        client = TestClient()

        assert client._config.timeout == 120.0
        assert client._config.verifyssl is False
