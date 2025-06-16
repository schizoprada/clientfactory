# ~/clientfactory/tests/unit/backends/test_algolia.py
"""
Unit tests for Algolia backend implementation.
"""
import pytest
from unittest.mock import Mock

from clientfactory.backends.algolia import AlgoliaBackend, AlgoliaConfig
from clientfactory.core.models import RequestModel, ResponseModel, HTTPMethod


class TestAlgoliaBackend:
    """Test Algolia backend functionality."""

    def test_algolia_backend_creation(self):
        """Test basic Algolia backend creation."""
        backend = AlgoliaBackend(
            appid="test-app-id",
            apikey="test-api-key",
            index="test-index"
        )

        assert isinstance(backend, AlgoliaBackend)
        assert backend.appid == "test-app-id"
        assert backend.apikey == "test-api-key"
        assert backend.index == "test-index"

    def test_algolia_config_baseurl(self):
        """Test AlgoliaConfig base URL formatting."""
        config = AlgoliaConfig(
            appid="test123",
            apikey="key123",
            urlbase="https://{appid}-dsn.algolia.net"
        )

        assert config.baseurl == "https://test123-dsn.algolia.net"

    def test_convert_params(self):
        """Test parameter conversion to Algolia format."""
        backend = AlgoliaBackend(
            appid="test",
            apikey="key",
            index="index"
        )

        data = {
            "q": "search query",
            "limit": 20,
            "offset": 40
        }

        params = backend._convertparams(data)

        assert params["query"] == "search query"
        assert params["hitsPerPage"] == 20
        assert params["page"] == 2  # offset/limit = 40/20 = 2

    def test_format_request_single_index(self):
        """Test request formatting for single index."""
        backend = AlgoliaBackend(
            appid="test123",
            apikey="key123",
            index="products"
        )

        request = RequestModel(
            method=HTTPMethod.POST,
            url="https://api.example.com"
        )

        data = {"q": "laptop", "limit": 10}

        formatted = backend._formatrequest(request, data)

        assert "test123-dsn.algolia.net/1/indexes/*/queries" in formatted.url
        assert "x-algolia-agent=ClientFactory" in formatted.url
        assert formatted.headers["X-Algolia-Application-Id"] == "test123"
        assert formatted.headers["X-Algolia-API-Key"] == "key123"

        # Check request structure
        assert "requests" in formatted.json
        assert len(formatted.json["requests"]) == 1
        assert formatted.json["requests"][0]["indexName"] == "products"

    def test_format_request_multi_index(self):
        """Test request formatting for multiple indices."""
        backend = AlgoliaBackend(
            appid="test123",
            apikey="key123",
            indices=["products", "categories"]
        )

        request = RequestModel(
            method=HTTPMethod.POST,
            url="https://api.example.com"
        )

        data = {"q": "laptop"}

        formatted = backend._formatrequest(request, data)

        assert len(formatted.json["requests"]) == 2
        assert formatted.json["requests"][0]["indexName"] == "products"
        assert formatted.json["requests"][1]["indexName"] == "categories"

    def test_process_response_success(self):
        """Test successful response processing."""
        backend = AlgoliaBackend(
            appid="test",
            apikey="key",
            index="index"
        )

        response_data = {
            "results": [{
                "hits": [{"objectID": "1", "name": "Product 1"}],
                "nbHits": 1,
                "page": 0,
                "nbPages": 1,
                "hitsPerPage": 20,
                "processingTimeMS": 2,
                "query": "laptop"
            }]
        }

        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{}',
            url="https://test.algolia.net",
            jsondata=response_data
        )

        result = backend._processresponse(response)

        assert result["hits"] == [{"objectID": "1", "name": "Product 1"}]
        assert result["total"] == 1
        assert result["query"] == "laptop"

    def test_process_response_error(self):
        """Test error response processing."""
        backend = AlgoliaBackend(
            appid="test",
            apikey="key",
            index="index",
            raiseonerror=True
        )

        response_data = {
            "message": "Invalid API key",
            "status": 403
        }

        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"message": "Invalid API key", "status": 403}',
            url="https://test.algolia.net",
            jsondata=response_data
        )

        with pytest.raises(RuntimeError):
            backend._processresponse(response)

    def test_merge_results(self):
        """Test merging multiple index results."""
        backend = AlgoliaBackend(
            appid="test",
            apikey="key",
            mergeresults=True
        )

        results = [
            {
                "hits": [{"objectID": "1", "name": "Product 1"}],
                "nbHits": 1,
                "processingTimeMS": 2
            },
            {
                "hits": [{"objectID": "2", "name": "Product 2"}],
                "nbHits": 1,
                "processingTimeMS": 3
            }
        ]

        indices = ["products", "categories"]
        merged = backend._mergeresults(results, indices)

        assert len(merged["hits"]) == 2
        assert merged["total"] == 2
        assert merged["processingTime"] == 5
        assert merged["hits"][0]["_index"] == "products"
        assert merged["hits"][1]["_index"] == "categories"

    def test_no_index_error(self):
        """Test error when no index is provided."""
        backend = AlgoliaBackend(
            appid="test",
            apikey="key"
        )

        request = RequestModel(method=HTTPMethod.POST, url="https://api.example.com")
        data = {"q": "search"}

        with pytest.raises(ValueError, match="At least one index is required"):
            backend._formatrequest(request, data)
