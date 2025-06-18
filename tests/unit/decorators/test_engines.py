# ~/clientfactory/tests/unit/decorators/test_engines.py
"""
Unit tests for engine decorators.
"""
import pytest
from unittest.mock import Mock

from clientfactory.decorators.engines import engine
from clientfactory.engines.requestslib import RequestsEngine
from clientfactory.core.bases.engine import BaseEngine
from clientfactory.core.models import EngineConfig


class TestEngineDecorators:
    """Test engine decorators."""

    def test_engine_decorator_basic(self):
        """Test basic @engine decorator."""
        @engine
        class MyEngine:
            timeout = 30.0
            verify = False
            retries = 3

        assert isinstance(MyEngine, BaseEngine)
        assert isinstance(MyEngine, RequestsEngine)  # Should default to requests
        assert MyEngine._config.timeout == 30.0
        assert MyEngine._config.verify is False
        #assert MyEngine._config.retries == 3

    def test_engine_requests_decorator(self):
        """Test @engine.requests decorator."""
        @engine.requests
        class RequestsEngine:
            timeout = 60.0
            verify = True
            retries = 5

        assert isinstance(RequestsEngine, BaseEngine)
        assert RequestsEngine._config.timeout == 60.0
        assert RequestsEngine._config.verify is True
        #assert RequestsEngine._config.retries == 5

    def test_engine_decorator_ignores_private_attrs(self):
        """Test that decorator ignores private attributes."""
        @engine
        class MyEngine:
            timeout = 30.0
            _private = "ignored"
            __dunder = "ignored"

        assert MyEngine._config.timeout == 30.0
        assert not hasattr(MyEngine, '_private')
        assert not hasattr(MyEngine, '__dunder')

    def test_engine_decorator_functional(self):
        """Test that decorated engine actually works."""
        @engine
        class MyEngine:
            timeout = 45.0
            verify = False

        # Test that we can make requests
        # Mock the session to avoid actual HTTP calls
        mock_session = Mock()
        mock_response = Mock()
        mock_response.statuscode = 200
        mock_session.send.return_value = mock_response
        MyEngine._session = mock_session

        # Test convenience method
        response = MyEngine.get("https://api.example.com/test")
        assert response.statuscode == 200

    def test_engine_decorator_default_to_requests(self):
        """Test that base @engine decorator defaults to requests engine."""
        @engine
        class MyEngine:
            timeout = 30.0

        # Should be a RequestsEngine instance
        from clientfactory.engines.requestslib import RequestsEngine as ConcreteRequestsEngine
        assert isinstance(MyEngine, ConcreteRequestsEngine)

    def test_engine_decorator_with_config_attrs(self):
        """Test engine decorator with various config attributes."""
        @engine
        class MyEngine:
            timeout = 120.0
            verify = False
            retries = 10
            poolsize = 20

        assert MyEngine._config.timeout == 120.0
        assert MyEngine._config.verify is False
        #assert MyEngine._config.retries == 10
        assert MyEngine._poolsize == 20  # This should be an attribute, not config

    def test_engine_decorator_empty_class(self):
        """Test engine decorator with empty class uses defaults."""
        @engine
        class EmptyEngine:
            pass

        assert isinstance(EmptyEngine, BaseEngine)
        # Should have default config values
        assert EmptyEngine._config.verify is True  # Default from EngineConfig
        assert EmptyEngine._config.timeout is None  # Default from EngineConfig
