# ~/clientfactory/tests/unit/core/models/test_executable_request.py
import pytest
from unittest.mock import Mock

from clientfactory.core.models import ExecutableRequest, ResponseModel, HTTPMethod
from clientfactory.core.bases.engine import BaseEngine


class TestEngine(BaseEngine):
    """Simple test engine for ExecutableRequest tests."""

    def _setupsession(self, config = None):
        pass
    def _makerequest(self, method, url, usesession=True, **kwargs):
        # Return a mock response for testing
        return ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"test": "response"}',
            url=url
        )


class TestExecutableRequest:
    """Test ExecutableRequest functionality."""

    def setup_method(self):
        """Set up test engine."""
        self.test_engine = TestEngine()

    def test_executable_request_creation(self):
        """Test creating an ExecutableRequest."""
        executable = ExecutableRequest(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            headers={"Authorization": "Bearer token"},
            engine=self.test_engine
        )

        assert executable.method == HTTPMethod.GET
        assert executable.url == "https://api.example.com/test"
        assert executable.headers["Authorization"] == "Bearer token"
        assert executable.engine is self.test_engine

    def test_executable_request_call_executes(self):
        """Test that calling ExecutableRequest executes the request."""
        executable = ExecutableRequest(
            method=HTTPMethod.POST,
            url="https://api.example.com/create",
            json={"name": "test"},
            engine=self.test_engine
        )

        result = executable()

        assert isinstance(result, ResponseModel)
        assert result.statuscode == 200
        assert result.url == "https://api.example.com/create"

    def test_executable_request_preserves_all_fields(self):
        """Test that ExecutableRequest preserves all RequestModel fields."""
        executable = ExecutableRequest(
            method=HTTPMethod.PUT,
            url="https://api.example.com/update",
            headers={"Content-Type": "application/json"},
            cookies={"session": "abc123"},
            params={"force": True},
            json={"data": "value"},
            timeout=30.0,
            engine=self.test_engine
        )

        assert executable.headers["Content-Type"] == "application/json"
        assert executable.cookies["session"] == "abc123"
        assert executable.params["force"] is True
        assert executable.json == {"data": "value"}
        assert executable.timeout == 30.0
        assert executable.engine is self.test_engine

    def test_executable_request_inherits_from_request_model(self):
        """Test that ExecutableRequest properly inherits from RequestModel."""
        executable = ExecutableRequest(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            engine=self.test_engine
        )

        # Should have RequestModel methods
        assert hasattr(executable, 'withheaders')
        assert hasattr(executable, 'withcookies')
        assert hasattr(executable, 'tokwargs')

        # Test one of the inherited methods
        new_executable = executable.withheaders({"X-Test": "value"})
        assert new_executable.headers["X-Test"] == "value"

    def test_executable_request_validates_engine_type(self):
        """Test that engine validation works properly."""
        with pytest.raises(ValueError, match="'engine' must be a BaseEngine type"):
            ExecutableRequest(
                method=HTTPMethod.GET,
                url="https://api.example.com/test",
                engine="not an engine"
            )
