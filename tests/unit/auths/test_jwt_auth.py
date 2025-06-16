# ~/clientfactory/tests/unit/auths/test_jwt_auth.py
"""
Unit tests for JWT authentication.
"""
import pytest
from unittest.mock import Mock

from clientfactory.auths.jwt import JWTAuth
from clientfactory.core.models import RequestModel, HTTPMethod, AuthConfig


class TestJWTAuth:
   """Test JWT Bearer authentication."""

   def test_jwt_auth_creation(self):
       """Test basic JWT auth creation."""
       auth = JWTAuth(token="test-token")

       assert isinstance(auth, JWTAuth)
       assert auth._token == "test-token"

   def test_jwt_auth_creation_without_token(self):
       """Test JWT auth creation without token."""
       auth = JWTAuth()

       assert auth._token is None

   def test_jwt_auth_with_config(self):
       """Test JWT auth with AuthConfig."""
       config = AuthConfig(timeout=60.0, autorefresh=False)
       auth = JWTAuth(token="test-token", config=config)

       assert auth._config.timeout == 60.0
       assert auth._config.autorefresh is False

   def test_jwt_authenticate_with_token(self):
       """Test authentication succeeds with token."""
       auth = JWTAuth(token="test-token")

       result = auth.authenticate()

       assert result is True
       assert auth.isauthenticated() is True

   def test_jwt_authenticate_without_token(self):
       """Test authentication fails without token."""
       auth = JWTAuth()

       result = auth.authenticate()

       assert result is False
       assert auth.isauthenticated() is False

   def test_jwt_apply_auth_success(self):
       """Test applying JWT auth to request."""
       auth = JWTAuth(token="test-jwt-token")
       auth.authenticate()

       request = RequestModel(
           method=HTTPMethod.GET,
           url="https://api.example.com/test"
       )

       authenticated_request = auth.applyauth(request)

       assert authenticated_request.headers["Authorization"] == "Bearer test-jwt-token"

   def test_jwt_apply_auth_preserves_headers(self):
       """Test JWT auth preserves existing headers."""
       auth = JWTAuth(token="test-token")
       auth.authenticate()

       request = RequestModel(
           method=HTTPMethod.POST,
           url="https://api.example.com/test",
           headers={"Content-Type": "application/json", "X-Custom": "value"}
       )

       authenticated_request = auth.applyauth(request)

       expected_headers = {
           "Content-Type": "application/json",
           "X-Custom": "value",
           "Authorization": "Bearer test-token"
       }

       assert authenticated_request.headers == expected_headers

   def test_jwt_apply_auth_no_token_raises(self):
       """Test applying auth without token raises error."""
       auth = JWTAuth()

       request = RequestModel(
           method=HTTPMethod.GET,
           url="https://api.example.com/test"
       )

       with pytest.raises(RuntimeError, match="Authentication failed"):
           auth.applyauth(request)

   def test_jwt_set_token(self):
       """Test setting JWT token."""
       auth = JWTAuth()

       assert auth.isauthenticated() is False

       auth.settoken("new-jwt-token")

       assert auth._token == "new-jwt-token"
       assert auth.isauthenticated() is True

   def test_jwt_set_token_overwrites(self):
       """Test setting token overwrites existing token."""
       auth = JWTAuth(token="old-token")

       auth.settoken("new-token")

       assert auth._token == "new-token"

   def test_jwt_declarative_attributes(self):
       """Test JWT auth with declarative attributes."""
       class CustomJWTAuth(JWTAuth):
           scheme = "Custom"
           audience = "test-audience"

       auth = CustomJWTAuth(token="test-token")

       assert auth.scheme == "Custom"
       assert auth.audience == "test-audience"
