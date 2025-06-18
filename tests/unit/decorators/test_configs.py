# ~/clientfactory/tests/unit/decorators/test_configs.py
"""
Unit tests for configuration decorators.
"""
import pytest

from clientfactory.decorators.configs import configs
from clientfactory.core.models.config import (
    EngineConfig, SessionConfig, AuthConfig, ResourceConfig
)
from clientfactory.core.models.enums import EngineType, AuthType, HTTPMethod


class TestConfigDecorators:
    """Test configuration decorators."""

    def test_engine_config_decorator(self):
        """Test @configs.engine decorator."""
        @configs.engine
        class MyEngineConfig:
            engine_type = EngineType.REQUESTS
            timeout = 30.0
            retries = 3

        assert isinstance(MyEngineConfig, EngineConfig)
        #assert MyEngineConfig.engine_type == EngineType.REQUESTS
        assert MyEngineConfig.timeout == 30.0
        #assert MyEngineConfig.retries == 3

    def test_session_config_decorator(self):
        """Test @configs.session decorator."""
        @configs.session
        class MySessionConfig:
            defaultheaders = {"User-Agent": "MyApp"}
            maxretries = 5
            timeout = 60.0

        assert isinstance(MySessionConfig, SessionConfig)
        assert MySessionConfig.defaultheaders == {"User-Agent": "MyApp"}
        assert MySessionConfig.maxretries == 5
        assert MySessionConfig.timeout == 60.0

    def test_auth_config_decorator(self):
        """Test @configs.auth decorator."""
        @configs.auth
        class MyAuthConfig:
            auth_type = AuthType.BEARER
            token = "my-token"

        assert isinstance(MyAuthConfig, AuthConfig)
        #assert MyAuthConfig.auth_type == AuthType.BEARER
        #assert MyAuthConfig.token == "my-token"

    def test_resource_config_decorator(self):
        """Test @configs.resource decorator."""
        @configs.resource
        class MyResourceConfig:
            name = "users"
            path = "api/users"
            description = "User management"

        assert isinstance(MyResourceConfig, ResourceConfig)
        assert MyResourceConfig.name == "users"
        assert MyResourceConfig.path == "api/users"
        assert MyResourceConfig.description == "User management"

    def test_decorator_ignores_private_attributes(self):
        """Test that decorators ignore private attributes."""
        @configs.engine
        class MyEngineConfig:
            timeout = 30.0
            _private = "ignored"
            __dunder = "ignored"

        assert MyEngineConfig.timeout == 30.0
        assert not hasattr(MyEngineConfig, '_private')
        assert not hasattr(MyEngineConfig, '__dunder')
