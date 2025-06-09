# tests/unit/core/bases/test_backend.py
"""
Tests for BaseBackend implementation
"""
import pytest
from unittest.mock import Mock

from clientfactory.core.bases.backend import BaseBackend
from clientfactory.core.models.config import BackendConfig
from clientfactory.core.models.request import RequestModel, ResponseModel
from clientfactory.core.models.enums import HTTPMethod
from clientfactory.core.protos.backend import BackendProtocol

class ConcreteBackend(BaseBackend):
    """Concrete implementation for testing"""

    def __init__(self, config=None, **kwargs):
        self._format_calls = []
        self._process_calls = []
        super().__init__(config, **kwargs)

    def _formatrequest(self, request, data):
        self._format_calls.append((request, data))
        # Simple test implementation - just add data to request params
        return request.withparams(data)

    def _processresponse(self, response):
        self._process_calls.append(response)
        # Simple test implementation - just return response data
        return response.json() if response.ok else {'error': 'failed'}

class FailingBackend(BaseBackend):
    """Backend that fails for testing error handling"""

    def _formatrequest(self, request, data):
        raise ValueError("Format failed")

    def _processresponse(self, response):
        raise ValueError("Process failed")

class TestBaseBackend:
    """Test BaseBackend abstract base class"""

    def test_implements_protocol(self):
        """Test that BaseBackend implements BackendProtocol"""
        backend = ConcreteBackend()
        assert isinstance(backend, BackendProtocol)

    def test_init_with_config(self):
        """Test initialization with BackendConfig"""
        config = BackendConfig(
            raiseonerror=False,
            autoparse=False,
            retryattempts=5
        )
        backend = ConcreteBackend(config=config)

        assert backend._config is config
        assert backend._config.raiseonerror == False
        assert backend._config.autoparse == False
        assert backend._config.retryattempts == 5

    def test_init_with_kwargs(self):
        """Test initialization with keyword arguments"""
        backend = ConcreteBackend(
            raiseonerror=False,
            autoparse=True,
            retryattempts=3
        )

        assert backend._config.raiseonerror == False
        assert backend._config.autoparse == True
        assert backend._config.retryattempts == 3

    def test_default_config(self):
        """Test initialization with default config"""
        backend = ConcreteBackend()

        assert isinstance(backend._config, BackendConfig)
        assert backend._config.raiseonerror == True
        assert backend._config.autoparse == True

    def test_validate_data_default(self):
        """Test default validatedata() implementation"""
        backend = ConcreteBackend()
        data = {'key': 'value'}

        result = backend.validatedata(data)

        assert result is data  # Should return same dict

    def test_handle_error_success(self):
        """Test handleerror() with successful response"""
        backend = ConcreteBackend()
        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"test": "data"}',
            url="http://test.com"
        )

        # Should not raise exception
        backend.handleerror(response)

    def test_handle_error_failure(self):
        """Test handleerror() with failed response"""
        backend = ConcreteBackend()
        response = ResponseModel(
            statuscode=404,
            headers={},
            content=b'{"error": "not found"}',
            url="http://test.com"
        )

        with pytest.raises(Exception):  # Should raise when raiseforstatus() is called
            backend.handleerror(response)

    def test_format_request_success(self):
        """Test formatrequest() calls _formatrequest()"""
        backend = ConcreteBackend()
        request = RequestModel(method=HTTPMethod.GET, url="http://test.com")
        data = {'param': 'value'}

        result = backend.formatrequest(request, data)

        assert len(backend._format_calls) == 1
        assert backend._format_calls[0] == (request, data)
        assert isinstance(result, RequestModel)
        assert result.params == {'param': 'value'}

    def test_format_request_failure(self):
        """Test formatrequest() exception handling"""
        backend = FailingBackend()
        request = RequestModel(method=HTTPMethod.GET, url="http://test.com")
        data = {'param': 'value'}

        with pytest.raises(RuntimeError, match="Request formatting failed"):
            backend.formatrequest(request, data)

    def test_process_response_success(self):
        """Test processresponse() calls _processresponse()"""
        backend = ConcreteBackend()
        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"test": "data"}',
            url="http://test.com",
            jsondata={"test": "data"}
        )

        result = backend.processresponse(response)

        assert len(backend._process_calls) == 1
        assert backend._process_calls[0] is response
        assert result == {"test": "data"}

    def test_process_response_with_error_handling(self):
        """Test processresponse() calls handleerror() first"""
        backend = ConcreteBackend()
        response = ResponseModel(
            statuscode=500,
            headers={},
            content=b'{"error": "server error"}',
            url="http://test.com"
        )

        # Should raise exception from handleerror() before _processresponse()
        with pytest.raises(Exception):
            backend.processresponse(response)

        # _processresponse should not be called
        assert len(backend._process_calls) == 0

    def test_process_response_failure(self):
        """Test processresponse() exception handling"""
        backend = FailingBackend()
        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"test": "data"}',
            url="http://test.com"
        )

        with pytest.raises(RuntimeError, match="Response processing failed"):
            backend.processresponse(response)

    def test_process_response_reraises_runtime_error(self):
        """Test processresponse() re-raises RuntimeError without wrapping"""
        backend = ConcreteBackend()

        def failing_process(response):
            raise RuntimeError("Already a runtime error")

        backend._processresponse = failing_process

        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"test": "data"}',
            url="http://test.com"
        )

        with pytest.raises(RuntimeError, match="Already a runtime error"):
            backend.processresponse(response)

class TestBackendIntegration:
    """Integration tests for backend functionality"""

    def test_full_request_flow(self):
        """Test complete request formatting and response processing flow"""
        backend = ConcreteBackend()

        # Create request
        request = RequestModel(
            method=HTTPMethod.POST,
            url="http://api.test.com/endpoint"
        )

        # Format request with data
        data = {'search': 'test query', 'limit': 10}
        formatted_request = backend.formatrequest(request, data)

        # Verify request was formatted
        assert formatted_request.params == data
        assert formatted_request.url == request.url
        assert formatted_request.method == request.method

        # Create mock response
        response = ResponseModel(
            statuscode=200,
            headers={"Content-Type": "application/json"},
            content=b'{"results": [{"id": 1, "name": "test"}]}',
            url="http://api.test.com/endpoint",
            jsondata={"results": [{"id": 1, "name": "test"}]}
        )

        # Process response
        result = backend.processresponse(response)

        # Verify response was processed
        assert result == {"results": [{"id": 1, "name": "test"}]}

    def test_custom_validation(self):
        """Test custom data validation"""
        class ValidatingBackend(ConcreteBackend):
            def validatedata(self, data):
                if 'required_field' not in data:
                    raise ValueError("Missing required field")
                return data

        backend = ValidatingBackend()

        # Valid data should pass
        valid_data = {'required_field': 'value', 'other': 'data'}
        result = backend.validatedata(valid_data)
        assert result == valid_data

        # Invalid data should raise
        invalid_data = {'other': 'data'}
        with pytest.raises(ValueError, match="Missing required field"):
            backend.validatedata(invalid_data)

    def test_custom_error_handling(self):
        """Test custom error handling"""
        class CustomErrorBackend(ConcreteBackend):
            def handleerror(self, response):
                if response.statuscode == 429:
                    raise RuntimeError("Rate limited")
                super().handleerror(response)

        backend = CustomErrorBackend()

        # Custom error should be raised
        response = ResponseModel(
            statuscode=429,
            headers={},
            content=b'{"error": "rate limited"}',
            url="http://test.com"
        )

        with pytest.raises(RuntimeError, match="Rate limited"):
            backend.handleerror(response)

class TestBackendConfig:
    """Test BackendConfig integration"""

    def test_config_affects_behavior(self):
        """Test that config settings affect backend behavior"""
        config = BackendConfig(raiseonerror=False)
        backend = ConcreteBackend(config=config)

        assert backend._config.raiseonerror == False

    def test_config_tolerance_settings(self):
        """Test tolerance configuration"""
        from clientfactory.core.models.enums import ToleranceType

        config = BackendConfig(errortolerance=ToleranceType.LAX)
        backend = ConcreteBackend(config=config)

        assert backend._config.errortolerance == ToleranceType.LAX

    def test_config_retry_settings(self):
        """Test retry configuration"""
        config = BackendConfig(
            retryattempts=5,
            retrybackoff=2.0
        )
        backend = ConcreteBackend(config=config)

        assert backend._config.retryattempts == 5
        assert backend._config.retrybackoff == 2.0
