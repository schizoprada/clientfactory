# ~/clientfactory/tests/unit/core/test_resource.py
# tests/unit/core/test_resource.py
"""
Unit tests for concrete Resource implementation.
"""
import pytest
from unittest.mock import Mock

from clientfactory.core.resource import Resource
from clientfactory.core.models import HTTPMethod, RequestModel, ResponseModel, ResourceConfig, MethodConfig


class TestResource:
    """Test concrete Resource functionality."""

    def setup_method(self):
        """Set up test resource with mock client."""
        self.mock_client = Mock()
        self.mock_client.baseurl = "https://api.example.com"
        self.mock_client._engine = Mock()

        self.mock_session = Mock()
        self.mock_backend = Mock()

    def test_resource_creation(self):
        """Test basic resource creation."""
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        assert isinstance(resource, Resource)
        assert resource._client is self.mock_client
        assert resource._session is self.mock_session
        assert resource.path == "users"
        assert resource.name == "test"

    def test_resource_with_backend(self):
        """Test resource creation with backend."""
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session,
            backend=self.mock_backend
        )

        assert resource._backend is self.mock_backend

    def test_register_method(self):
        """Test registering a method."""
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        mock_method = Mock()
        mock_method.__name__ = "test_method"

        resource._registermethod(mock_method, "custom_name")

        assert "custom_name" in resource._methods
        assert resource._methods["custom_name"] is mock_method
        assert hasattr(resource, "custom_name")

    def test_register_child(self):
        """Test registering a child resource."""
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        child_config = ResourceConfig(name="child", path="posts")
        child_resource = Resource(
            client=self.mock_client,
            config=child_config,
            session=self.mock_session
        )

        resource._registerchild(child_resource, "posts")

        assert "posts" in resource._children
        assert resource._children["posts"] is child_resource
        assert hasattr(resource, "posts")

    def test_build_request_basic(self):
        """Test building a basic request."""
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        request = resource._buildrequest(
            method=HTTPMethod.GET,
            path="me"
        )

        assert request.method == HTTPMethod.GET
        assert request.url == "https://api.example.com/users/me"

    def test_build_request_no_resource_path(self):
        """Test building request with no resource path."""
        config = ResourceConfig(name="test", path="")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )
        resource.path = ""

        request = resource._buildrequest(
            method=HTTPMethod.POST,
            path="login"
        )

        assert request.url == "https://api.example.com/login"

    def test_build_request_no_method_path(self):
        """Test building request with no method path."""
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        request = resource._buildrequest(method=HTTPMethod.GET)

        assert request.url == "https://api.example.com/users"

    def test_build_request_with_kwargs(self):
        """Test building request with additional kwargs."""
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        request = resource._buildrequest(
            method=HTTPMethod.POST,
            headers={"Content-Type": "application/json"},
            json={"name": "John"}
        )

        assert request.headers == {"Content-Type": "application/json"}
        assert request.json == {"name": "John"}

    def test_create_bound_method_basic(self):
        """Test creating a bound method."""
        # ensure client has no backend for this test
        self.mock_client._backend = None
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        # Create a mock method with config
        def mock_method(self): pass
        mock_method._methodconfig = MethodConfig(
            name="get_user",
            method=HTTPMethod.GET,
            path="{id}"
        )

        # Mock session.send to return a response
        mock_response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"id": 1, "name": "John"}',
            url="https://api.example.com/users/1"
        )
        resource._session.send.return_value = mock_response

        bound_method = resource._createboundmethod(mock_method)

        # Test the bound method
        result = bound_method()

        assert result is mock_response
        resource._session.send.assert_called_once()

    def test_create_bound_method_with_backend(self):
        """Test creating bound method with backend processing."""
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session,
            backend=self.mock_backend
        )

        # Create a mock method with config
        def mock_method(self): pass
        mock_method._methodconfig = MethodConfig(
            name="get_user",
            method=HTTPMethod.GET,
            path="{id}"
        )

        # Mock responses
        mock_response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"id": 1, "name": "John"}',
            url="https://api.example.com/users/1"
        )
        processed_data = {"id": 1, "name": "John"}

        resource._session.send.return_value = mock_response
        self.mock_backend.formatrequest.return_value = Mock()
        self.mock_backend.processresponse.return_value = processed_data

        bound_method = resource._createboundmethod(mock_method)

        # Test the bound method
        result = bound_method()

        assert result == processed_data
        self.mock_backend.formatrequest.assert_called_once()
        self.mock_backend.processresponse.assert_called_once_with(mock_response)

    def test_create_bound_method_with_postprocess(self):
        """Test creating bound method with postprocessing."""
        # ensure client has no backend for this test
        self.mock_client._backend = None
        config = ResourceConfig(name="test", path="users")
        resource = Resource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        # Create postprocessor
        def postprocessor(response):
            return {"processed": True, "original": response}

        # Create a mock method with config
        def mock_method(self): pass
        mock_method._methodconfig = MethodConfig(
            name="get_user",
            method=HTTPMethod.GET,
            path="{id}",
            postprocess=postprocessor
        )

        # Mock session.send to return a response
        mock_response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"id": 1, "name": "John"}',
            url="https://api.example.com/users/1"
        )
        resource._session.send.return_value = mock_response

        bound_method = resource._createboundmethod(mock_method)

        # Test the bound method
        result = bound_method()

        assert result["processed"] is True
        assert result["original"] is mock_response

    def test_init_methods_discovery(self):
        """Test that _initmethods discovers methods with _methodconfig."""
        # Create a resource class with decorated methods
        class TestResource(Resource):
            def regular_method(self):
                pass

            def decorated_method(self):
                pass

        # Add method config to decorated method
        TestResource.decorated_method._methodconfig = MethodConfig(
            name="decorated_method",
            method=HTTPMethod.GET,
            path="test"
        )

        config = ResourceConfig(name="test", path="users")
        resource = TestResource(
            client=self.mock_client,
            config=config,
            session=self.mock_session
        )

        # Mock session.send to avoid actual requests
        resource._session.send.return_value = Mock()

        # Should have discovered the decorated method
        assert "decorated_method" in resource._methods
        assert "regular_method" not in resource._methods

    @pytest.mark.skip("Known limitation: nested resource discovery during client discovery")
    def test_init_children_discovery(self):
        """Test that _initchildren discovers nested Resource classes."""
        # Create a resource class with nested resources
        clean_mock_client = Mock()
        clean_mock_client.baseurl = "https://api.example.com"
        clean_mock_client._engine = Mock()
        clean_mock_client._backend = None

        class TestResource(Resource):
            class NestedResource(Resource):
                pass

            class NotAResource:
                pass

        config = ResourceConfig(name="test", path="users")
        resource = TestResource(
            client=clean_mock_client,
            config=config,
            session=self.mock_session
        )

        # Should have discovered the nested resource
        assert "nestedresource" in resource._children
        assert hasattr(resource, "nestedresource")
        assert isinstance(resource.nestedresource, Resource)
