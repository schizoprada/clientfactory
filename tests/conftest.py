# ~/clientfactory/tests/conftest.py
"""
Test configuration and shared fixtures.
"""
import pytest
import typing as t
from unittest.mock import Mock

# Test data fixtures
@pytest.fixture
def sample_request_data():
   """Sample data for request testing."""
   return {
       "method": "GET",
       "url": "https://api.example.com/users",
       "headers": {"Authorization": "Bearer token123"},
       "params": {"limit": 10, "offset": 0}
   }

@pytest.fixture
def sample_response_data():
   """Sample data for response testing."""
   return {
       "statuscode": 200,
       "headers": {"Content-Type": "application/json"},
       "content": b'{"users": [{"id": 1, "name": "John"}]}',
       "url": "https://api.example.com/users"
   }

@pytest.fixture
def sample_payload_data():
   """Sample data for payload testing."""
   return {
       "q": "search term",
       "size": 20,
       "user": {"name": "john", "id": 123},
       "tags": ["python", "api"]
   }

# Mock fixtures
@pytest.fixture
def mock_engine():
   """Mock request engine."""
   engine = Mock()
   engine.request.return_value = Mock()
   engine.send.return_value = Mock()
   return engine

@pytest.fixture
def mock_auth():
   """Mock auth provider."""
   auth = Mock()
   auth.isauthenticated.return_value = True
   auth.shouldrefresh.return_value = False
   auth.applyauth.return_value = Mock()
   return auth

@pytest.fixture
def mock_session():
   """Mock session."""
   session = Mock()
   session.send.return_value = Mock()
   session.preparerequest.return_value = Mock()
   return session

# Config fixtures
@pytest.fixture
def engine_config():
   """Engine configuration for testing."""
   from clientfactory.core.models import EngineConfig
   return EngineConfig(verify=True, timeout=30.0)

@pytest.fixture
def session_config():
   """Session configuration for testing."""
   from clientfactory.core.models import SessionConfig
   return SessionConfig(timeout=30.0, verifyssl=True)
