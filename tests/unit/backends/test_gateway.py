# ~/clientfactory/tests/unit/backends/test_gateway.py

import pytest
from unittest.mock import Mock
from urllib.parse import unquote

from clientfactory.backends.gateway import GatewayBackend
from clientfactory.core.models import RequestModel, ResponseModel
from clientfactory.core.models.enums import HTTPMethod

class TestGatewayBackend:

    def test_basic_initialization(self):
        """Test basic GatewayBackend creation."""
        backend = GatewayBackend(
            gatewayurl="https://api.example.com/search",
            urlparam="target"
        )

        assert backend._gatewayurl == "https://api.example.com/search"
        assert backend._urlparam == "target"

    def test_missing_gatewayurl_raises_error(self):
        """Test that missing gatewayurl raises ValueError."""
        with pytest.raises(ValueError, match="GatewayBackend requires 'gatewayurl' and 'urlparam'"):
            GatewayBackend()

    def test_formatrequest_no_data(self):
        """Test formatting request without data."""
        backend = GatewayBackend(
            gatewayurl="https://api.example.com/search",
            urlparam="url"
        )

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://proxy.example.com/gateway"
        )

        result = backend._formatrequest(request, {})

        assert result.method == HTTPMethod.GET
        assert result.url == "https://proxy.example.com/gateway"
        assert result.params == {"url": "https://api.example.com/search"}

    def test_formatrequest_with_data(self):
        """Test formatting request with data."""
        backend = GatewayBackend(
            gatewayurl="https://api.example.com/search",
            urlparam="url"
        )

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://proxy.example.com/gateway"
        )

        data = {"keyword": "Rick Owens", "limit": 10}
        result = backend._formatrequest(request, data)

        assert result.method == HTTPMethod.GET
        assert result.url == "https://proxy.example.com/gateway"

        # Check that target URL contains encoded data
        target_url = result.params["url"]
        assert "api.example.com/search" in target_url
        assert "keyword=Rick+Owens" in target_url or "keyword=Rick%20Owens" in target_url
        assert "limit=10" in target_url

    def test_formatrequest_gateway_url_with_existing_params(self):
        """Test formatting when gateway URL already has parameters."""
        backend = GatewayBackend(
            gatewayurl="https://api.example.com/search?format=json",
            urlparam="url"
        )

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://proxy.example.com/gateway"
        )

        data = {"keyword": "test"}
        result = backend._formatrequest(request, data)

        target_url = result.params["url"]
        assert "format=json" in target_url
        assert "keyword=test" in target_url
        assert target_url.count("?") == 1  # Should only have one ?

    def test_processresponse_json(self):
        """Test processing JSON response."""
        backend = GatewayBackend(gatewayurl="https://api.example.com", urlparam="url")

        response = Mock()
        response.ok = True
        response.json.return_value = {"results": ["item1", "item2"]}

        result = backend._processresponse(response)
        assert result == {"results": ["item1", "item2"]}

    def test_processresponse_text_fallback(self):
        """Test processing response when JSON fails."""
        backend = GatewayBackend(gatewayurl="https://api.example.com", urlparam="url")

        response = Mock()
        response.ok = True
        response.json.side_effect = ValueError("No JSON")
        response.text = "plain text response"

        result = backend._processresponse(response)
        assert result == "plain text response"

    def test_processresponse_error(self):
        """Test processing error response."""
        backend = GatewayBackend(gatewayurl="https://api.example.com", urlparam="url")

        response = Mock()
        response.ok = False

        result = backend._processresponse(response)
        assert result == response

    def test_declarative_attributes(self):
        """Test declarative attribute resolution."""
        class TestGateway(GatewayBackend):
            gatewayurl = "https://test.example.com/api"
            urlparam = "target_url"

        backend = TestGateway()
        assert backend._gatewayurl == "https://test.example.com/api"
        assert backend._urlparam == "target_url"
