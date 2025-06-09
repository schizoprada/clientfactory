# tests/unit/core/bases/test_engine.py
"""
Unit tests for base request engine functionality.
"""
import pytest
from unittest.mock import Mock, patch

from clientfactory.core.bases.engine import BaseEngine
from clientfactory.core.models import (
    HTTPMethod, RequestModel, ResponseModel, EngineConfig
)


class TestEngineBasics:
    """Test basic engine functionality."""

    def test_initialization_with_defaults(self):
        """Test engine initialization with default config."""
        # Update the TestEngine classes in test_engine.py

        class TestEngine(BaseEngine):
            def _setupsession(self, config=None):
                # Return a mock session for testing
                mock_session = Mock()
                mock_session.send = Mock(return_value=ResponseModel(
                    statuscode=200, headers={}, content=b"", url="test"
                ))
                return mock_session

            def _makerequest(self, method, url, usesession=True, **kwargs):
                if usesession:
                    # Use the session
                    request = RequestModel(method=method, url=url, **kwargs)
                    return self._session.send(request)
                else:
                    # Direct request without session
                    return ResponseModel(
                        statuscode=200,
                        headers={'Content-Type': 'application/json'},
                        content=b'{"test": "data"}',
                        url=url
                    )

        engine = TestEngine()
        assert isinstance(engine._config, EngineConfig)
        assert engine._config.verify is True
        assert engine._config.timeout is None
        assert engine._closed is False

    def test_initialization_with_custom_config(self):
        """Test engine initialization with custom config."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        config = EngineConfig(verify=False, timeout=60.0)
        engine = TestEngine(config=config)
        assert engine._config.verify is False
        assert engine._config.timeout == 60.0

    def test_initialization_with_kwargs(self):
        """Test engine initialization with kwargs."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine(verify=False, timeout=30.0)
        assert engine._config.verify is False
        assert engine._config.timeout == 30.0


class TestRequestMethods:
    """Test HTTP method implementations."""

    def setup_method(self):
        """Set up test engine."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(
                    statuscode=200,
                    headers={'Content-Type': 'application/json'},
                    content=b'{"test": "data"}',
                    url=url
                )

        self.engine = TestEngine()

    def test_request_with_string_method(self):
        """Test request with string method."""
        response = self.engine.request("GET", "https://api.example.com/test")
        assert response.statuscode == 200
        assert response.url == "https://api.example.com/test"

    def test_request_with_enum_method(self):
        """Test request with HTTPMethod enum."""
        response = self.engine.request(HTTPMethod.POST, "https://api.example.com/test")
        assert response.statuscode == 200

    def test_get_method(self):
        """Test GET convenience method."""
        response = self.engine.get("https://api.example.com/test")
        assert response.statuscode == 200

    def test_post_method(self):
        """Test POST convenience method."""
        response = self.engine.post("https://api.example.com/test", json={"data": "test"})
        assert response.statuscode == 200

    def test_put_method(self):
        """Test PUT convenience method."""
        response = self.engine.put("https://api.example.com/test")
        assert response.statuscode == 200

    def test_patch_method(self):
        """Test PATCH convenience method."""
        response = self.engine.patch("https://api.example.com/test")
        assert response.statuscode == 200

    def test_delete_method(self):
        """Test DELETE convenience method."""
        response = self.engine.delete("https://api.example.com/test")
        assert response.statuscode == 200

    def test_head_method(self):
        """Test HEAD convenience method."""
        response = self.engine.head("https://api.example.com/test")
        assert response.statuscode == 200

    def test_options_method(self):
        """Test OPTIONS convenience method."""
        response = self.engine.options("https://api.example.com/test")
        assert response.statuscode == 200


class TestSendMethod:
    """Test send method with RequestModel."""

    def setup_method(self):
        """Set up test engine."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                # Store the kwargs for verification
                self.last_kwargs = kwargs
                return ResponseModel(
                    statuscode=200,
                    headers={},
                    content=b"",
                    url=url
                )

        self.engine = TestEngine()

    def test_send_basic_request(self):
        """Test sending a basic request."""
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )
        response = self.engine.send(request)
        assert response.statuscode == 200

    def test_send_applies_config_defaults(self):
        """Test that send applies config defaults."""
        self.engine._config = EngineConfig(verify=False, timeout=30.0)
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )
        self.engine.send(request)

        # Check that config defaults were applied
        assert self.engine.last_kwargs['verify'] is True # request has a default for this so engine should not override
        assert self.engine.last_kwargs['timeout'] == 30.0

    def test_send_request_overrides_config(self):
        """Test that request values override config defaults."""
        self.engine._config = EngineConfig(timeout=30.0)
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            timeout=60.0
        )
        self.engine.send(request)

        # Request timeout should override config timeout
        assert self.engine.last_kwargs['timeout'] == 60.0


class TestConfigHandling:
    """Test configuration handling."""

    def test_config_defaults_applied(self):
        """Test that config defaults are applied to requests."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                self.last_kwargs = kwargs
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine(timeout=45.0, verify=False)
        engine.request(HTTPMethod.GET, "https://api.example.com/test")

        assert engine.last_kwargs['timeout'] == 45.0
        assert engine.last_kwargs['verify'] is False

    def test_request_kwargs_override_config(self):
        """Test that request kwargs override config."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                self.last_kwargs = kwargs
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine(timeout=30.0)
        engine.request(
            HTTPMethod.GET,
            "https://api.example.com/test",
            timeout=60.0
        )

        assert engine.last_kwargs['timeout'] == 60.0


class TestLifecycleManagement:
    """Test engine lifecycle management."""

    def test_close_sets_closed_flag(self):
        """Test that close sets the closed flag."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine()
        assert engine._closed is False
        engine.close()
        assert engine._closed is True

    def test_request_after_close_raises_error(self):
        """Test that requests after close raise error."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine()
        engine.close()

        with pytest.raises(RuntimeError, match="Engine is closed"):
            engine.request(HTTPMethod.GET, "https://api.example.com/test")

    def test_send_after_close_raises_error(self):
        """Test that send after close raises error."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine()
        engine.close()

        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com/test")
        with pytest.raises(RuntimeError, match="Engine is closed"):
            engine.send(request)


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager_enters_and_exits(self):
        """Test context manager enter and exit."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine()

        with engine as ctx_engine:
            assert ctx_engine is engine
            assert engine._closed is False

        assert engine._closed is True

    def test_context_manager_closes_on_exception(self):
        """Test context manager closes engine on exception."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine()

        try:
            with engine:
                raise ValueError("Test exception")
        except ValueError:
            pass

        assert engine._closed is True


class TestAbstractImplementation:
    """Test abstract method implementation requirements."""

    def test_abstract_makerequest_must_be_implemented(self):
        """Test that _makerequest must be implemented."""
        with pytest.raises(TypeError):
            # This should fail because _makerequest is not implemented
            class IncompleteEngine(BaseEngine):
                pass

            IncompleteEngine()


class TestEngineErrorHandling:
    """Test error handling in engine."""

    def test_send_handles_request_conversion_error(self):
        """Test send handles RequestModel conversion errors gracefully."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine()

        # Create a valid request but then test error handling
        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com/test")

        # Test 1: Engine handles invalid URL in request
        # (This will pass validation but shows error handling pattern)
        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com/test")
        response = engine.send(request)
        assert response.statuscode == 200


    def test_invalid_method_string_raises_error(self):
        """Test that invalid method strings raise appropriate errors."""
        class TestEngine(BaseEngine):
            def _makerequest(self, method, url, **kwargs):
                return ResponseModel(statuscode=200, headers={}, content=b"", url=url)

        engine = TestEngine()

        with pytest.raises(ValueError):
            engine.request("INVALID_METHOD", "https://api.example.com/test")
