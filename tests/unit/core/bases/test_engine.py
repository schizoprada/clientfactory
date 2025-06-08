# ~/clientfactory/tests/unit/core/bases/test_engine.py
"""
Unit tests for BaseEngine abstract base class.
"""
import pytest
from unittest.mock import Mock, patch
from clientfactory.core.bases.engine import BaseEngine
from clientfactory.core.models import HTTPMethod, RequestModel, ResponseModel, EngineConfig


class ConcreteEngine(BaseEngine):
    """Concrete implementation for testing."""

    def _makerequest(self, method: HTTPMethod, url: str, **kwargs):
        # Mock implementation that returns a ResponseModel
        return ResponseModel(
            statuscode=200,
            headers={"Content-Type": "application/json"},
            content=b'{"test": "response"}',
            url=url
        )


class TestBaseEngine:
    """Test BaseEngine functionality."""

    def test_engine_creation_with_config(self):
        """Test engine creation with EngineConfig."""
        config = EngineConfig(verify=False, timeout=60.0)
        engine = ConcreteEngine(config=config)

        assert engine._config == config
        assert engine._config.verify is False
        assert engine._config.timeout == 60.0
        assert engine._closed is False

    def test_engine_creation_with_kwargs(self):
        """Test engine creation with kwargs."""
        engine = ConcreteEngine(verify=True, timeout=30.0)

        assert isinstance(engine._config, EngineConfig)
        assert engine._config.verify is True
        assert engine._config.timeout == 30.0

    def test_engine_creation_without_config(self):
        """Test engine creation without config creates default."""
        engine = ConcreteEngine()

        assert isinstance(engine._config, EngineConfig)
        assert engine._config.verify is True  # Default
        assert engine._config.timeout is None  # Default

    def test_request_method_with_http_method(self):
        """Test request method with HTTPMethod enum."""
        engine = ConcreteEngine()

        response = engine.request(HTTPMethod.GET, "https://api.example.com")

        assert isinstance(response, ResponseModel)
        assert response.statuscode == 200
        assert response.url == "https://api.example.com"

    def test_request_method_with_string(self):
        """Test request method with string method."""
        engine = ConcreteEngine()

        response = engine.request("POST", "https://api.example.com")

        assert isinstance(response, ResponseModel)
        assert response.statuscode == 200

    def test_request_method_applies_config_defaults(self):
        """Test request method applies config defaults."""
        engine = ConcreteEngine(timeout=45.0, verify=False)

        with patch.object(engine, '_makerequest') as mock_make:
            mock_make.return_value = ResponseModel(
                statuscode=200, headers={}, content=b"", url=""
            )

            engine.request(HTTPMethod.GET, "https://api.example.com")

            # Should apply config defaults
            mock_make.assert_called_once_with(
                HTTPMethod.GET,
                "https://api.example.com",
                timeout=45.0,
                verify=False
            )

    def test_request_method_kwargs_override_config(self):
        """Test request kwargs override config defaults."""
        engine = ConcreteEngine(timeout=30.0, verify=True)

        with patch.object(engine, '_makerequest') as mock_make:
            mock_make.return_value = ResponseModel(
                statuscode=200, headers={}, content=b"", url=""
            )

            engine.request(HTTPMethod.GET, "https://api.example.com", timeout=60.0)

            # Explicit timeout should override config
            mock_make.assert_called_once_with(
                HTTPMethod.GET,
                "https://api.example.com",
                timeout=60.0,
                verify=True
            )

    def test_send_method(self):
        """Test send method with RequestModel."""
        engine = ConcreteEngine()

        request = RequestModel(
            method=HTTPMethod.POST,
            url="https://api.example.com/users",
            headers={"Authorization": "Bearer token"},
            json={"name": "John"}
        )

        with patch.object(engine, '_makerequest') as mock_make:
            mock_make.return_value = ResponseModel(
                statuscode=201, headers={}, content=b"", url=""
            )

            response = engine.send(request)

            # Should extract request data into kwargs
            expected_kwargs = request.tokwargs(timeout=None, verify=True)
            mock_make.assert_called_once_with(
                HTTPMethod.POST,
                "https://api.example.com/users",
                **expected_kwargs
            )

    def test_convenience_methods(self):
        """Test HTTP method convenience methods."""
        engine = ConcreteEngine()
        url = "https://api.example.com"

        with patch.object(engine, 'request') as mock_request:
            mock_request.return_value = ResponseModel(
                statuscode=200, headers={}, content=b"", url=""
            )

            # Test all convenience methods
            engine.get(url, param="value")
            mock_request.assert_called_with(HTTPMethod.GET, url, param="value")

            engine.post(url, data="test")
            mock_request.assert_called_with(HTTPMethod.POST, url, data="test")

            engine.put(url, json={"key": "value"})
            mock_request.assert_called_with(HTTPMethod.PUT, url, json={"key": "value"})

            engine.patch(url, headers={"X-Test": "true"})
            mock_request.assert_called_with(HTTPMethod.PATCH, url, headers={"X-Test": "true"})

            engine.delete(url)
            mock_request.assert_called_with(HTTPMethod.DELETE, url)

            engine.head(url)
            mock_request.assert_called_with(HTTPMethod.HEAD, url)

            engine.options(url)
            mock_request.assert_called_with(HTTPMethod.OPTIONS, url)

    def test_check_not_closed_raises_when_closed(self):
        """Test _checknotclosed raises when engine is closed."""
        engine = ConcreteEngine()
        engine.close()

        with pytest.raises(RuntimeError, match="Engine is closed"):
            engine.request(HTTPMethod.GET, "https://api.example.com")

    def test_close_method(self):
        """Test close method sets closed flag."""
        engine = ConcreteEngine()

        assert engine._closed is False

        engine.close()

        assert engine._closed is True

    def test_context_manager(self):
        """Test engine as context manager."""
        with ConcreteEngine() as engine:
            assert engine._closed is False
            response = engine.get("https://api.example.com")
            assert isinstance(response, ResponseModel)

        # Should be closed after context
        assert engine._closed is True

    def test_context_manager_with_exception(self):
        """Test context manager closes even with exception."""
        engine = None
        try:
            with ConcreteEngine() as engine:
                assert engine._closed is False
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should still be closed
        assert engine._closed is True


class TestBaseEngineAbstract:
    """Test BaseEngine abstract behavior."""

    def test_cannot_instantiate_base_engine(self):
        """Test BaseEngine cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseEngine()

    def test_concrete_must_implement_makerequest(self):
        """Test concrete classes must implement _makerequest."""
        class IncompleteEngine(BaseEngine):
            pass

        with pytest.raises(TypeError):
            IncompleteEngine()


class TestEngineErrorHandling:
    """Test engine error handling."""

    def test_engine_handles_makerequest_exception(self):
        """Test engine handles exceptions from _makerequest."""
        class FailingEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                raise ConnectionError("Network failure")

        engine = FailingEngine()

        with pytest.raises(ConnectionError):
            engine.request(HTTPMethod.GET, "https://api.example.com")

    def test_send_handles_request_conversion_error(self):
        """Test send handles RequestModel conversion errors."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine()

        # Create invalid request that might cause conversion issues
        request = RequestModel(method=HTTPMethod.GET, url="")

        with pytest.raises(ValueError):  # From URL validation
            engine.send(request)


class TestEngineConfiguration:
    """Test engine configuration handling."""

    def test_config_inheritance(self):
        """Test config values are properly inherited."""
        config = EngineConfig(verify=False, timeout=120.0)

        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                # Verify config values are passed through
                assert kwargs.get('verify') is False
                assert kwargs.get('timeout') == 120.0
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine(config=config)
        engine.request(HTTPMethod.GET, "https://api.example.com")

    def test_config_defaults_only_applied_when_missing(self):
        """Test config defaults only applied when not in kwargs."""
        config = EngineConfig(verify=False, timeout=30.0)

        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                # Explicit values should override config
                assert kwargs.get('verify') is True  # Overridden
                assert kwargs.get('timeout') == 30.0  # From config
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine(config=config)
        engine.request(HTTPMethod.GET, "https://api.example.com", verify=True)
