# ~/clientfactory/tests/unit/core/test_backend.py
# tests/unit/core/test_backend.py
"""
Unit tests for concrete Backend implementation.
"""
import pytest
from unittest.mock import Mock

from clientfactory.core.backend import Backend
from clientfactory.core.models import HTTPMethod, RequestModel, ResponseModel, BackendConfig


class TestBackend:
    """Test concrete Backend functionality."""

    def test_backend_creation(self):
        """Test basic backend creation."""
        backend = Backend()
        assert isinstance(backend, Backend)
        assert backend.endpoint == ''
        assert backend.apiversion == 'v1'
        assert backend.format == 'json'

    def test_backend_with_config(self):
        """Test backend creation with config."""
        config = BackendConfig(
            raiseonerror=False,
            autoparse=True,
            retryattempts=5
        )
        backend = Backend(config=config)
        assert backend._config.raiseonerror is False
        assert backend._config.autoparse is True
        assert backend._config.retryattempts == 5

    def test_format_request_get_with_data(self):
        """Test formatting GET request with data."""
        backend = Backend()
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/users"
        )
        data = {"limit": 10, "offset": 0}

        formatted = backend.formatrequest(request, data)

        assert formatted.params == {"limit": 10, "offset": 0}
        assert formatted.json is None
        assert formatted.url == request.url
        assert formatted.method == request.method

    def test_format_request_post_with_data(self):
        """Test formatting POST request with data."""
        backend = Backend()
        request = RequestModel(
            method=HTTPMethod.POST,
            url="https://api.example.com/users"
        )
        data = {"name": "John", "email": "john@example.com"}

        formatted = backend.formatrequest(request, data)

        assert formatted.json == {"name": "John", "email": "john@example.com"}
        assert formatted.params == {}
        assert formatted.url == request.url
        assert formatted.method == request.method

    def test_format_request_put_with_data(self):
        """Test formatting PUT request with data."""
        backend = Backend()
        request = RequestModel(
            method=HTTPMethod.PUT,
            url="https://api.example.com/users/1"
        )
        data = {"name": "Jane"}

        formatted = backend.formatrequest(request, data)

        assert formatted.json == {"name": "Jane"}
        assert formatted.params == {}

    def test_format_request_patch_with_data(self):
        """Test formatting PATCH request with data."""
        backend = Backend()
        request = RequestModel(
            method=HTTPMethod.PATCH,
            url="https://api.example.com/users/1"
        )
        data = {"email": "jane@example.com"}

        formatted = backend.formatrequest(request, data)

        assert formatted.json == {"email": "jane@example.com"}
        assert formatted.params == {}

    def test_format_request_delete_no_data(self):
        """Test formatting DELETE request without data."""
        backend = Backend()
        request = RequestModel(
            method=HTTPMethod.DELETE,
            url="https://api.example.com/users/1"
        )
        data = {}

        formatted = backend.formatrequest(request, data)

        assert formatted.json is None
        assert formatted.params == {}
        assert formatted is request  # Should return same object when no data

    def test_format_request_no_data(self):
        """Test formatting request with no data."""
        backend = Backend()
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/users"
        )
        data = {}

        formatted = backend.formatrequest(request, data)

        assert formatted is request  # Should return same object

    def test_process_response_success_json(self):
        """Test processing successful JSON response."""
        backend = Backend()
        response = ResponseModel(
            statuscode=200,
            headers={"Content-Type": "application/json"},
            content=b'{"users": [{"id": 1, "name": "John"}]}',
            url="https://api.example.com/users",
            jsondata={"users": [{"id": 1, "name": "John"}]}
        )

        result = backend.processresponse(response)

        assert result == {"users": [{"id": 1, "name": "John"}]}

    def test_process_response_success_text(self):
        """Test processing successful text response."""
        backend = Backend()
        response = ResponseModel(
            statuscode=200,
            headers={"Content-Type": "text/plain"},
            content=b'Hello World',
            url="https://api.example.com/test"
        )

        result = backend.processresponse(response)

        assert result == "Hello World"

    def test_process_response_error(self):
        """Test processing error response."""
        backend = Backend(raiseonerror=False)
        response = ResponseModel(
            statuscode=404,
            headers={},
            content=b'{"error": "Not found"}',
            url="https://api.example.com/users/999"
        )

        result = backend.processresponse(response)

        assert result is response  # Should return original response for errors

    def test_validate_data_default(self):
        """Test default data validation."""
        backend = Backend()
        data = {"key": "value"}

        result = backend.validatedata(data)

        assert result is data  # Should return same dict

    def test_handle_error_success(self):
        """Test error handling with successful response."""
        backend = Backend()
        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"success": true}',
            url="https://api.example.com/test"
        )

        # Should not raise
        backend.handleerror(response)

    def test_handle_error_failure(self):
        """Test error handling with failed response."""
        backend = Backend()
        response = ResponseModel(
            statuscode=404,
            headers={},
            content=b'{"error": "Not found"}',
            url="https://api.example.com/missing"
        )

        with pytest.raises(Exception):
            backend.handleerror(response)

    def test_format_request_error_handling(self):
        """Test format request error handling."""
        class FailingBackend(Backend):
            def _formatrequest(self, request, data):
                raise ValueError("Format failed")

        backend = FailingBackend()
        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

        with pytest.raises(RuntimeError, match="Request formatting failed"):
            backend.formatrequest(request, {})

    def test_process_response_error_handling(self):
        """Test process response error handling."""
        class FailingBackend(Backend):
            def _processresponse(self, response):
                raise ValueError("Process failed")

        backend = FailingBackend()
        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"test": "data"}',
            url="https://api.example.com"
        )

        with pytest.raises(RuntimeError, match="Response processing failed"):
            backend.processresponse(response)
