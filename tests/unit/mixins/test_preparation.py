# ~/clientfactory/tests/unit/mixins/test_preparation.py
import pytest
from unittest.mock import Mock

from clientfactory.core.models import ExecutableRequest, RequestModel, HTTPMethod, ResourceConfig, ResponseModel, SessionConfig
from clientfactory.decorators.http.methods import get, post
from clientfactory.core.client import Client
from clientfactory.core.resource import Resource
from clientfactory.core.bases.engine import BaseEngine
from clientfactory.core.bases.session import BaseSession


class TestEngine(BaseEngine):
    """Simple test engine for preparation tests."""

    def _setupsession(self, config = None) -> BaseSession:
        """Setup session - return mock for tests."""
        return Mock()

    def _makerequest(self, method, url, usesession=True, **kwargs):
        # Return a mock response for testing
        return ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"test": "response"}',
            url=url
        )


class TestPrepMixin:
    """Test PrepMixin functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_engine = TestEngine()

    def test_client_method_prepare(self):
        """Test preparing a client method."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get("{id}", headers={"X-Method": "test"})
            def get_item(self, id): pass

        client = TestClient(engine=self.test_engine)

        # Prepare the request instead of executing
        executable = client.get_item.prepare(123)

        # Should get an ExecutableRequest
        assert isinstance(executable, ExecutableRequest)
        assert executable.method == HTTPMethod.GET
        assert executable.url == "https://api.example.com/123"
        assert executable.headers["X-Method"] == "test"
        assert executable.engine is self.test_engine

    def test_resource_method_prepare(self):
        """Test preparing a resource method."""

        class TestResource(Resource):
            @post(headers={"X-Resource": "test"})
            def create_item(self): pass

        mock_client = Mock()
        mock_client.baseurl = "https://api.example.com"
        mock_client._engine = self.test_engine
        mock_client._backend = None

        resource = TestResource(client=mock_client, config=ResourceConfig(name="test", path="items"))

        # Prepare the request
        executable = resource.create_item.prepare()

        assert isinstance(executable, ExecutableRequest)
        assert executable.method == HTTPMethod.POST
        assert executable.url == "https://api.example.com/items"
        assert executable.headers["X-Resource"] == "test"
        assert executable.engine is self.test_engine

    def test_prepared_request_execution(self):
        """Test that prepared requests can be executed later."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get
            def simple_method(self): pass

        client = TestClient(engine=self.test_engine)

        # Prepare the request
        executable = client.simple_method.prepare()

        # Execute it later
        result = executable()

        # Should return a response
        assert isinstance(result, ResponseModel)
        assert result.statuscode == 200

    def test_prepare_with_arguments(self):
        """Test preparing requests with arguments."""

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("{category}/items")
            def create_item(self, category, name): pass

        client = TestClient(engine=self.test_engine)

        executable = client.create_item.prepare("electronics", name="laptop")

        assert executable.url == "https://api.example.com/electronics/items"
        assert executable.json["name"] == "laptop"

    def test_prepare_without_methodconfig_raises_error(self):
        """Test that prepare fails on objects without method config."""

        class BadObject:
            pass

        obj = BadObject()

        # Manually add PrepMixin methods (this is a contrived test)
        from clientfactory.mixins.preparation import PrepMixin
        obj.__class__ = type('BadObjectWithPrep', (BadObject, PrepMixin), {})

        with pytest.raises(AttributeError, match="prepare\\(\\) can only be called on bound methods"):
            obj.prepare()
