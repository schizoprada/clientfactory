# ~/clientfactory/tests/unit/decorators/test_auths.py
"""
Unit tests for auth decorators.
"""
import pytest
from unittest.mock import Mock

from clientfactory.decorators.auths import baseauth, jwt, dpop
from clientfactory.core.bases import BaseAuth
from clientfactory.auths.jwt import JWTAuth
from clientfactory.auths.dpop import DPOPAuth


class TestAuthDecorators:
   """Test authentication decorators."""

   def test_baseauth_decorator_basic(self):
       """Test basic baseauth decorator usage."""
       @baseauth
       class CustomAuth:
           token = "test-token"

           def authenticate(self):
               return True

       assert issubclass(CustomAuth, BaseAuth)
       assert CustomAuth.token == "test-token"
       assert hasattr(CustomAuth, 'authenticate')

   def test_baseauth_decorator_with_kwargs(self):
       """Test baseauth decorator with kwargs."""
       @baseauth(timeout=60.0, retries=3)
       class CustomAuth:
           pass

       assert issubclass(CustomAuth, BaseAuth)
       assert CustomAuth.timeout == 60.0
       assert CustomAuth.retries == 3

   def test_jwt_decorator_basic(self):
       """Test basic JWT decorator usage."""
       @jwt
       class APIAuth:
           scheme = "Bearer"

       assert issubclass(APIAuth, JWTAuth)
       assert APIAuth.scheme == "Bearer"

   def test_jwt_decorator_with_token(self):
       """Test JWT decorator with token parameter."""
       @jwt(token="test-jwt-token")
       class APIAuth:
           pass

       assert issubclass(APIAuth, JWTAuth)
       assert APIAuth.token == "test-jwt-token"

   def test_jwt_decorator_with_kwargs(self):
       """Test JWT decorator with additional kwargs."""
       @jwt(token="test-token", username="testuser")
       class APIAuth:
           custom_attr = "custom"

       assert issubclass(APIAuth, JWTAuth)
       assert APIAuth.token == "test-token"
       assert APIAuth.username == "testuser"
       assert APIAuth.custom_attr == "custom"

   def test_dpop_decorator_basic(self):
       """Test basic DPoP decorator usage."""
       @dpop
       class DPoPAuth:
           pass

       assert issubclass(DPoPAuth, DPOPAuth)
       assert DPoPAuth.algorithm == "ES256"
       assert DPoPAuth.headerkey == "DPoP"

   def test_dpop_decorator_with_config(self):
       """Test DPoP decorator with configuration."""
       test_jwk = {
           "kty": "EC",
           "crv": "P-256",
           "x": "test-x",
           "y": "test-y",
           "d": "test-d"
       }

       @dpop(jwk=test_jwk, algorithm="ES384", headerkey="CustomDPoP")
       class DPoPAuth:
           pass

       assert issubclass(DPoPAuth, DPOPAuth)
       assert DPoPAuth.jwk == test_jwk
       assert DPoPAuth.algorithm == "ES384"
       assert DPoPAuth.headerkey == "CustomDPoP"

   def test_decorator_without_parentheses(self):
       """Test decorators used without parentheses."""
       @baseauth
       class CustomAuth:
           pass

       @jwt
       class JWTAuthClass:
           pass

       @dpop
       class DPoPAuthClass:
           pass

       assert issubclass(CustomAuth, BaseAuth)
       assert issubclass(JWTAuthClass, JWTAuth)
       assert issubclass(DPoPAuthClass, DPOPAuth)

   def test_preserves_original_attributes(self):
       """Test that decorators preserve original class attributes."""
       @jwt(token="test-token")
       class APIAuth:
           custom_method_called = False

           def custom_method(self):
               self.custom_method_called = True
               return "custom"

       # Test that original attributes are preserved
       auth = APIAuth()
       assert hasattr(auth, 'custom_method')
       assert auth.custom_method() == "custom"
       assert auth.custom_method_called is True
       assert auth.token == "test-token"

   def test_preserves_module_and_qualname(self):
       """Test that decorators preserve module and qualname."""
       @jwt
       class TestAuth:
           pass

       assert TestAuth.__module__ == __name__
       assert TestAuth.__qualname__ == "TestAuthDecorators.test_preserves_module_and_qualname.<locals>.TestAuth"

   def test_inheritance_works_correctly(self):
       """Test that the transformed class inherits correctly."""
       @baseauth
       class CustomAuth:
            def custom_authenticate(self):
                return "custom auth"

            def _authenticate(self):
                return True

            def _applyauth(self, request):
                return request

       # Should inherit from BaseAuth
       auth = CustomAuth()
       assert isinstance(auth, BaseAuth)

       # Should have custom method
       assert auth.custom_authenticate() == "custom auth"

       # Should have BaseAuth methods (checking abstract ones would require implementation)
       assert hasattr(auth, 'isauthenticated')
       assert hasattr(auth, 'clear')

   def test_multiple_decorators_different_classes(self):
       """Test multiple auth decorators on different classes."""
       @jwt(token="jwt-token")
       class JWTAuthClass:
           jwt_specific = "jwt"

       @dpop(algorithm="ES384")
       class DPoPAuthClass:
           dpop_specific = "dpop"

       assert issubclass(JWTAuthClass, JWTAuth)
       assert issubclass(DPoPAuthClass, DPOPAuth)
       assert JWTAuthClass.token == "jwt-token"
       assert JWTAuthClass.jwt_specific == "jwt"
       assert DPoPAuthClass.algorithm == "ES384"
       assert DPoPAuthClass.dpop_specific == "dpop"
