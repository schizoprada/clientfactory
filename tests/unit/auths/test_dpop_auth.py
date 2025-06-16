# ~/clientfactory/tests/unit/auths/test_dpop_auth.py
"""
Unit tests for DPoP authentication.
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from clientfactory.auths.dpop import DPOPAuth
from clientfactory.core.models import RequestModel, HTTPMethod, AuthConfig

# Test JWK for EC P-256 curve
TEST_JWK = {
    "kty": "EC",
    "crv": "P-256",
    "x": "MKBCTNIcKUSDii11ySs3526iDZ8AiTo7Tu6KPAqv7D4",
    "y": "4Etl6SRW2YiLUrN5vfvVHuhp7x8PxltmWWlbbM4IFyM",
    "d": "870MB6gfuTJ4HtUnUvYMyJpr5eUZNP4Bk43bVdj3eAE"
}

# Invalid JWKs for testing
INVALID_JWK_NO_KTY = {
    "x": "test",
    "y": "test"
}

INVALID_JWK_MISSING_EC_FIELDS = {
    "kty": "EC",
    "x": "test"
    # Missing y, d, crv
}

INVALID_JWK_UNSUPPORTED_TYPE = {
    "kty": "UNSUPPORTED"
}


class TestDPOPAuth:
    """Test DPoP authentication."""

    def test_dpop_auth_creation_with_jwk(self):
        """Test DPoP auth creation with valid JWK."""
        auth = DPOPAuth(jwk=TEST_JWK)
        auth._validatejwk()

        assert isinstance(auth, DPOPAuth)
        assert auth.jwk == TEST_JWK
        assert auth.algorithm == "ES256"
        assert auth.headerkey == "DPoP"

    def test_dpop_auth_creation_empty(self):
        """Test DPoP auth creation without JWK."""
        auth = DPOPAuth(jwk={})

        assert auth.algorithm == "ES256"
        assert auth.headerkey == "DPoP"

    def test_dpop_auth_with_config(self):
        """Test DPoP auth with AuthConfig."""
        config = AuthConfig(timeout=45.0)
        auth = DPOPAuth(config=config)

        assert auth._config.timeout == 45.0

    def test_dpop_declarative_attributes(self):
        """Test DPoP auth with declarative attributes."""
        class CustomDPOPAuth(DPOPAuth):
            algorithm = "ES384"
            headerkey = "CustomDPoP"
            jwk = TEST_JWK

        auth = CustomDPOPAuth()

        assert auth.algorithm == "ES384"
        assert auth.headerkey == "CustomDPoP"
        assert auth.jwk == TEST_JWK

    def test_dpop_jwk_validation_success(self):
        """Test valid JWK validation passes."""
        auth = DPOPAuth()
        auth.jwk = TEST_JWK

        # Should not raise
        auth._validatejwk()
        assert auth._authenticated is True

    def test_dpop_jwk_validation_no_kty(self):
        """Test JWK validation fails with missing kty."""
        auth = DPOPAuth()
        auth.jwk = INVALID_JWK_NO_KTY

        with pytest.raises(ValueError, match="JWK missing 'kty' field"):
            auth._validatejwk()

    def test_dpop_jwk_validation_missing_ec_fields(self):
        """Test JWK validation fails with missing EC fields."""
        auth = DPOPAuth()
        auth.jwk = INVALID_JWK_MISSING_EC_FIELDS

        with pytest.raises(ValueError, match="EC JWK missing fields"):
            auth._validatejwk()

    def test_dpop_jwk_validation_unsupported_type(self):
        """Test JWK validation fails with unsupported key type."""
        auth = DPOPAuth()
        auth.jwk = INVALID_JWK_UNSUPPORTED_TYPE

        with pytest.raises(ValueError, match="Unsupported JWK type"):
            auth._validatejwk()

    def test_dpop_authenticate_with_jwk(self):
        """Test authentication succeeds with valid JWK."""
        auth = DPOPAuth()
        auth.jwk = TEST_JWK
        auth._validatejwk()

        result = auth.authenticate()

        assert result is True
        assert auth.isauthenticated() is True

    def test_dpop_authenticate_without_jwk(self):
        """Test authentication fails without JWK."""
        auth = DPOPAuth()

        result = auth.authenticate()

        assert result is False
        assert auth.isauthenticated() is False

    def test_dpop_get_private_key_ec(self):
        """Test extracting EC private key from JWK."""
        auth = DPOPAuth()
        auth.jwk = TEST_JWK

        private_key = auth._getprivatekey()

        # Should return an EC private key
        from cryptography.hazmat.primitives.asymmetric import ec
        assert isinstance(private_key, ec.EllipticCurvePrivateKey)

    def test_dpop_get_private_key_unsupported(self):
        """Test private key extraction with unsupported key type."""
        auth = DPOPAuth()
        auth.jwk = {"kty": "RSA", "n": "test", "e": "test", "d": "test"}

        with pytest.raises(NotImplementedError, match="Private key extraction not yet implemented"):
            auth._getprivatekey()

    def test_dpop_get_public_jwk(self):
        """Test extracting public JWK portion."""
        auth = DPOPAuth()
        auth.jwk = TEST_JWK

        public_jwk = auth._getpublicjwk()

        expected = {
            "kty": "EC",
            "crv": "P-256",
            "x": "MKBCTNIcKUSDii11ySs3526iDZ8AiTo7Tu6KPAqv7D4",
            "y": "4Etl6SRW2YiLUrN5vfvVHuhp7x8PxltmWWlbbM4IFyM"
        }

        assert public_jwk == expected
        assert "d" not in public_jwk  # Private key should not be included

    @patch('jwt.encode')
    def test_dpop_generate_token(self, mock_jwt_encode):
        """Test DPoP token generation."""
        mock_jwt_encode.return_value = "test-dpop-token"

        auth = DPOPAuth()
        auth.jwk = TEST_JWK
        auth._validatejwk()

        request = RequestModel(
            method=HTTPMethod.POST,
            url="https://api.example.com/test"
        )

        token = auth._generatetoken(request)

        assert token == "test-dpop-token"

        # Verify jwt.encode was called with correct parameters
        call_args = mock_jwt_encode.call_args
        payload = call_args[0][0]

        assert payload['htm'] == 'POST'
        assert payload['htu'] == 'https://api.example.com/test'
        assert 'jti' in payload
        assert 'iat' in payload

    def test_dpop_generate_token_no_jwk(self):
        """Test token generation fails without JWK."""
        auth = DPOPAuth()

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )

        with pytest.raises(RuntimeError, match="No JWK configured"):
            auth._generatetoken(request)

    @patch('jwt.encode')
    def test_dpop_apply_auth(self, mock_jwt_encode):
        """Test applying DPoP auth to request."""
        mock_jwt_encode.return_value = "test-dpop-token"

        auth = DPOPAuth(jwk=TEST_JWK)
        auth._validatejwk()

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )

        authenticated_request = auth.applyauth(request)

        assert authenticated_request.headers["DPoP"] == "test-dpop-token"

    @patch('jwt.encode')
    def test_dpop_apply_auth_custom_header(self, mock_jwt_encode):
        """Test DPoP auth with custom header key."""
        mock_jwt_encode.return_value = "test-dpop-token"

        class CustomDPOPAuth(DPOPAuth):
            headerkey = "CustomDPoP"

        auth = CustomDPOPAuth(jwk=TEST_JWK)
        auth._validatejwk()

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )

        authenticated_request = auth.applyauth(request)

        assert authenticated_request.headers["CustomDPoP"] == "test-dpop-token"

    @patch('jwt.encode')
    def test_dpop_apply_auth_preserves_headers(self, mock_jwt_encode):
        """Test DPoP auth preserves existing headers."""
        mock_jwt_encode.return_value = "test-dpop-token"

        auth = DPOPAuth()
        auth.jwk = TEST_JWK
        auth._validatejwk()

        request = RequestModel(
            method=HTTPMethod.POST,
            url="https://api.example.com/test",
            headers={"Content-Type": "application/json", "X-Custom": "value"}
        )

        authenticated_request = auth.applyauth(request)

        expected_headers = {
            "Content-Type": "application/json",
            "X-Custom": "value",
            "DPoP": "test-dpop-token"
        }

        assert authenticated_request.headers == expected_headers

    def test_dpop_set_jwk(self):
        """Test setting JWK after creation."""
        auth = DPOPAuth()

        assert auth.isauthenticated() is False

        auth.setjwk(TEST_JWK)

        assert auth.jwk == TEST_JWK
        assert auth.isauthenticated() is True

    def test_dpop_set_jwk_validates(self):
        """Test setting invalid JWK raises error."""
        auth = DPOPAuth()

        with pytest.raises(ValueError):
            auth.setjwk(INVALID_JWK_NO_KTY)
