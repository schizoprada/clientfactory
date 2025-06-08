# ~/clientfactory/tests/unit/core/bases/test_auth.py
"""
Unit tests for BaseAuth abstract base class.
"""
import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from clientfactory.core.bases.auth import BaseAuth
from clientfactory.core.models import RequestModel, ResponseModel, AuthConfig, HTTPMethod


class ConcreteAuth(BaseAuth):
   """Concrete implementation for testing."""

   def __init__(self, should_fail=False, **kwargs):
       super().__init__(**kwargs)
       self.should_fail = should_fail
       self.auth_call_count = 0
       self.prepare_call_count = 0

   def _authenticate(self) -> bool:
       self.auth_call_count += 1
       if self.should_fail:
           return False
       self._authenticated = True
       return True

   def _applyauth(self, request: RequestModel) -> RequestModel:
       self.prepare_call_count += 1
       return request.withheaders({"Authorization": "Bearer test-token"})


class TestBaseAuth:
   """Test BaseAuth functionality."""

   def test_auth_creation_with_config(self):
       """Test auth creation with AuthConfig."""
       config = AuthConfig(autorefresh=False, retryattempts=5)
       auth = ConcreteAuth(config=config)

       assert auth._config == config
       assert auth._config.autorefresh is False
       assert auth._config.retryattempts == 5
       assert auth._authenticated is False

   def test_auth_creation_with_kwargs(self):
       """Test auth creation with kwargs."""
       auth = ConcreteAuth(autorefresh=True, retryattempts=2)

       assert isinstance(auth._config, AuthConfig)
       assert auth._config.autorefresh is True
       assert auth._config.retryattempts == 2

   def test_auth_creation_without_config(self):
       """Test auth creation without config creates default."""
       auth = ConcreteAuth()

       assert isinstance(auth._config, AuthConfig)
       assert auth._config.autorefresh is True  # Default
       assert auth._config.retryattempts == 3  # Default

   def test_is_authenticated_initial_state(self):
       """Test initial authentication state."""
       auth = ConcreteAuth()

       assert auth.isauthenticated() is False
       assert auth._authenticated is False

   def test_should_refresh_default(self):
       """Test default shouldrefresh behavior."""
       auth = ConcreteAuth()

       # Base implementation should return False
       assert auth.shouldrefresh() is False

   def test_authenticate_success(self):
       """Test successful authentication."""
       auth = ConcreteAuth()

       result = auth.authenticate()

       assert result is True
       assert auth.isauthenticated() is True
       assert auth._authenticated is True
       assert auth.auth_call_count == 1

   def test_authenticate_failure(self):
       """Test failed authentication."""
       auth = ConcreteAuth(should_fail=True)

       result = auth.authenticate()

       assert result is False
       assert auth.isauthenticated() is False
       assert auth._authenticated is False

   def test_authenticate_exception_handling(self):
       """Test authentication handles exceptions."""
       class FailingAuth(BaseAuth):
           def _authenticate(self):
               raise RuntimeError("Auth service down")

           def _applyauth(self, request):
               return request

       auth = FailingAuth()

       with pytest.raises(RuntimeError):
           auth.authenticate()

       # Should not be marked as authenticated on exception
       assert auth.isauthenticated() is False

   def test_apply_auth_when_authenticated(self):
       """Test applyauth when already authenticated."""
       auth = ConcreteAuth()
       auth.authenticate()  # Ensure authenticated

       request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

       result = auth.applyauth(request)

       assert result.headers == {"Authorization": "Bearer test-token"}
       assert auth.prepare_call_count == 1

   def test_apply_auth_when_not_authenticated(self):
       """Test applyauth authenticates if not already authenticated."""
       auth = ConcreteAuth()

       request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

       result = auth.applyauth(request)

       # Should have authenticated automatically
       assert auth.auth_call_count == 1
       assert auth.isauthenticated() is True
       assert result.headers == {"Authorization": "Bearer test-token"}

   def test_apply_auth_fails_when_auth_fails(self):
       """Test applyauth raises when authentication fails."""
       auth = ConcreteAuth(should_fail=True)

       request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

       with pytest.raises(RuntimeError, match="Authentication failed"):
           auth.applyauth(request)

   def test_refresh_default_implementation(self):
       """Test default refresh implementation."""
       auth = ConcreteAuth()

       # Default refresh should re-authenticate
       result = auth.refresh()

       assert result is True
       assert auth.auth_call_count == 1
       assert auth.isauthenticated() is True

   def test_refresh_if_needed_when_should_refresh_false(self):
       """Test refreshifneeded when shouldrefresh returns False."""
       auth = ConcreteAuth()
       auth.authenticate()  # Initial auth

       auth.refreshifneeded()

       # Should not refresh since shouldrefresh returns False
       assert auth.auth_call_count == 1  # Only initial auth

   def test_refresh_if_needed_when_should_refresh_true(self):
       """Test refreshifneeded when shouldrefresh returns True."""
       class RefreshingAuth(ConcreteAuth):
           def shouldrefresh(self):
               return True

       auth = RefreshingAuth()
       auth.authenticate()  # Initial auth

       auth.refreshifneeded()

       # Should refresh since shouldrefresh returns True
       assert auth.auth_call_count == 2  # Initial + refresh

   def test_clear_resets_state(self):
       """Test clear resets authentication state."""
       auth = ConcreteAuth()
       auth.authenticate()

       assert auth.isauthenticated() is True

       auth.clear()

       assert auth.isauthenticated() is False
       assert auth._authenticated is False


class TestBaseAuthAbstract:
   """Test BaseAuth abstract behavior."""

   def test_cannot_instantiate_base_auth(self):
       """Test BaseAuth cannot be instantiated directly."""
       with pytest.raises(TypeError):
           BaseAuth()

   def test_concrete_must_implement_authenticate(self):
       """Test concrete classes must implement _authenticate."""
       class IncompleteAuth(BaseAuth):
           def _applyauth(self, request):
               return request

       with pytest.raises(TypeError):
           IncompleteAuth()

   def test_concrete_must_implement_applyauth(self):
       """Test concrete classes must implement _applyauth."""
       class IncompleteAuth(BaseAuth):
           def _authenticate(self):
               return True

       with pytest.raises(TypeError):
           IncompleteAuth()


class TestAuthConfigHandling:
   """Test authentication configuration handling."""

   def test_config_timeout_applied(self):
       """Test config timeout is accessible."""
       config = AuthConfig(timeout=60.0, retryattempts=5)
       auth = ConcreteAuth(config=config)

       assert auth._config.timeout == 60.0
       assert auth._config.retryattempts == 5

   def test_config_retry_attempts_validation(self):
       """Test config validates retry attempts."""
       # Should not raise for valid values
       AuthConfig(retryattempts=0)
       AuthConfig(retryattempts=10)

       # Should raise for negative values
       with pytest.raises(ValueError):
           AuthConfig(retryattempts=-1)

   def test_config_timeout_validation(self):
       """Test config validates timeout."""
       # Should not raise for valid values
       AuthConfig(timeout=30.0)
       AuthConfig(timeout=None)

       # Should raise for negative values
       with pytest.raises(ValueError):
           AuthConfig(timeout=-1.0)


class TestAuthStateManagement:
   """Test authentication state management."""

   def test_multiple_authentications(self):
       """Test multiple authentication calls."""
       auth = ConcreteAuth()

       # First authentication
       assert auth.authenticate() is True
       assert auth.auth_call_count == 1

       # Second authentication (should work again)
       assert auth.authenticate() is True
       assert auth.auth_call_count == 2

   def test_authentication_state_persistence(self):
       """Test authentication state persists across method calls."""
       auth = ConcreteAuth()
       auth.authenticate()

       request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

       # Multiple applyauth calls should not re-authenticate
       auth.applyauth(request)
       auth.applyauth(request)

       assert auth.auth_call_count == 1  # Only initial auth
       assert auth.prepare_call_count == 2  # Both apply calls

   def test_clear_requires_reauthentication(self):
       """Test clear requires re-authentication for applyauth."""
       auth = ConcreteAuth()
       auth.authenticate()

       auth.clear()

       request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")
       auth.applyauth(request)

       # Should have re-authenticated
       assert auth.auth_call_count == 2  # Initial + after clear


class TestAuthIntegration:
   """Test auth integration scenarios."""

   def test_request_modification_preserves_original(self):
       """Test auth doesn't modify original request."""
       auth = ConcreteAuth()
       auth.authenticate()

       original = RequestModel(
           method=HTTPMethod.GET,
           url="https://api.example.com",
           headers={"Accept": "application/json"}
       )

       modified = auth.applyauth(original)

       # Original should be unchanged
       assert original.headers == {"Accept": "application/json"}

       # Modified should have auth header
       assert modified.headers == {
           "Accept": "application/json",
           "Authorization": "Bearer test-token"
       }

   def test_auth_with_existing_headers(self):
       """Test auth preserves existing headers."""
       auth = ConcreteAuth()
       auth.authenticate()

       request = RequestModel(
           method=HTTPMethod.POST,
           url="https://api.example.com",
           headers={
               "Content-Type": "application/json",
               "X-Custom": "value"
           }
       )

       result = auth.applyauth(request)

       expected = {
           "Content-Type": "application/json",
           "X-Custom": "value",
           "Authorization": "Bearer test-token"
       }

       assert result.headers == expected
