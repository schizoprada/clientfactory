# ~/clientfactory/tests/unit/resources/test_search_resource.py 
# tests/unit/resources/test_search_resource.py
"""
Unit tests for SearchResource implementation.
"""
import pytest
from unittest.mock import Mock

from clientfactory.resources.search import SearchResource
from clientfactory.core.models import SearchResourceConfig, HTTPMethod, Payload, Param
from clientfactory.core.models.request import ResponseModel


class TestSearchResource:
    """Test SearchResource functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client.baseurl = "https://api.example.com"
        self.mock_client._engine = Mock()
        self.mock_client._engine._session = Mock()
        self.mock_client._backend = None

    def test_search_resource_creation(self):
        """Test basic SearchResource creation."""
        config = SearchResourceConfig(name="test", path="search")
        resource = SearchResource(client=self.mock_client, config=config)

        assert isinstance(resource, SearchResource)
        assert resource.name == "test"
        assert resource.path == "search"
        assert resource.method == HTTPMethod.GET
        assert resource.searchmethod == "search"
        assert resource.oncall is False

    def test_search_resource_with_custom_attributes(self):
        """Test SearchResource with custom declarative attributes."""
        class TestSearchResource(SearchResource):
            method = HTTPMethod.POST
            searchmethod = "find"
            oncall = True

        resource = TestSearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )

        assert resource.method == HTTPMethod.POST
        assert resource.searchmethod == "find"
        assert resource.oncall is True

    def test_auto_generates_search_method(self):
        """Test that search method is auto-generated."""
        resource = SearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )

        assert "search" in resource._methods
        assert hasattr(resource, "search")
        assert callable(resource.search)

    def test_custom_searchmethod_name(self):
        """Test custom search method name."""
        class TestSearchResource(SearchResource):
            searchmethod = "find"

        resource = TestSearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )

        assert "find" in resource._methods
        assert hasattr(resource, "find")
        assert "search" not in resource._methods

    def test_oncall_makes_instance_callable(self):
        """Test that oncall=True makes instance callable."""
        class TestSearchResource(SearchResource):
            oncall = True

        resource = TestSearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )

        assert hasattr(resource, "__call__")
        # try direct call
        call_works = False
        try:
            resource()
            call_works = True
        except Exception as e:
            print(f"Calling resource() failed: {e}")

        assert call_works

    def test_search_method_without_payload(self):
        """Test search method execution without payload."""
        resource = SearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )

        # Mock session response
        mock_response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"results": []}',
            url="https://api.example.com"
        )
        resource._session.send.return_value = mock_response

        result = resource.search(q="test", limit=10)

        assert result is mock_response
        resource._session.send.assert_called_once()

    def test_search_method_with_payload(self):
        """Test search method with payload validation."""
        class SearchPayload(Payload):
            query = Param(source="q", required=True)
            limit = Param(source="size", default=10)

        class TestSearchResource(SearchResource):
            payload = SearchPayload

        resource = TestSearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )

        # Mock session response
        mock_response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"results": []}',
            url="https://api.example.com"
        )
        resource._session.send.return_value = mock_response

        result = resource.search(q="test")

        assert result is mock_response

    def test_search_method_get_vs_post(self):
        """Test search method data preparation for GET vs POST."""
        # Test GET
        get_resource = SearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )
        get_data = get_resource._preparerequestdata({"q": "test"})
        assert get_data == {"params": {"q": "test"}}

        # Test POST
        class PostSearchResource(SearchResource):
            method = HTTPMethod.POST

        post_resource = PostSearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )
        post_data = post_resource._preparerequestdata({"q": "test"})
        assert post_data == {"json": {"q": "test"}}

    def test_search_method_with_backend(self):
        """Test search method with backend processing."""
        mock_backend = Mock()
        mock_backend.processresponse.return_value = {"processed": True}

        resource = SearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path=""),
            backend=mock_backend
        )

        mock_response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"results": []}',
            url="https://api.example.com"
        )
        resource._session.send.return_value = mock_response

        result = resource.search(q="test")

        assert result == {"processed": True}
        mock_backend.processresponse.assert_called_once_with(mock_response)

    def test_preparerequestdata_already_formatted(self):
        """Test _preparerequestdata with already formatted data."""
        resource = SearchResource(
            client=self.mock_client,
            config=SearchResourceConfig(name="test", path="")
        )

        # Already formatted data should pass through
        formatted_data = {"params": {"q": "test"}}
        result = resource._preparerequestdata(formatted_data)
        assert result == formatted_data

        # Multiple keys should be reformatted
        mixed_data = {"q": "test", "params": {"other": "data"}}
        result = resource._preparerequestdata(mixed_data)
        assert result == {"params": mixed_data}
