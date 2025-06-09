"""
Unit tests for session configuration models.
"""
import pytest
from pydantic import ValidationError

from clientfactory.core.models import SessionConfig


class TestSessionConfig:
    """Test session configuration model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SessionConfig()

        assert config.timeout == 30.0
        assert config.verifyssl is True
        assert config.allowredirects is True
        assert config.maxredirects == 10
        assert config.maxretries == 3
        assert config.retrybackoff == 1.0
        assert config.poolconnections == 10
        assert config.poolmaxsize == 10
        assert config.persistcookies is False
        assert config.cookiefile is None
        assert config.defaultheaders == {}
        assert config.defaultcookies == {}

    def test_custom_values(self):
        """Test setting custom configuration values."""
        headers = {"User-Agent": "TestClient/1.0"}
        cookies = {"session": "abc123"}

        config = SessionConfig(
            timeout=60.0,
            verifyssl=False,
            allowredirects=False,
            maxredirects=5,
            maxretries=1,
            retrybackoff=2.0,
            poolconnections=20,
            poolmaxsize=20,
            persistcookies=True,
            cookiefile="/tmp/cookies.txt",
            defaultheaders=headers,
            defaultcookies=cookies
        )

        assert config.timeout == 60.0
        assert config.verifyssl is False
        assert config.allowredirects is False
        assert config.maxredirects == 5
        assert config.maxretries == 1
        assert config.retrybackoff == 2.0
        assert config.poolconnections == 20
        assert config.poolmaxsize == 20
        assert config.persistcookies is True
        assert config.cookiefile == "/tmp/cookies.txt"
        assert config.defaultheaders == headers
        assert config.defaultcookies == cookies

    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid positive timeout
        config = SessionConfig(timeout=30.0)
        assert config.timeout == 30.0

        # Invalid zero timeout
        with pytest.raises(ValidationError) as exc:
            SessionConfig(timeout=0.0)
        assert "Timeout must be positive" in str(exc.value)

        # Invalid negative timeout
        with pytest.raises(ValidationError) as exc:
            SessionConfig(timeout=-1.0)
        assert "Timeout must be positive" in str(exc.value)

    def test_maxretries_validation(self):
        """Test max retries validation."""
        # Valid zero retries
        config = SessionConfig(maxretries=0)
        assert config.maxretries == 0

        # Valid positive retries
        config = SessionConfig(maxretries=5)
        assert config.maxretries == 5

        # Invalid negative retries
        with pytest.raises(ValidationError) as exc:
            SessionConfig(maxretries=-1)
        assert "Max retries cannot be negative" in str(exc.value)

    def test_maxredirects_validation(self):
        """Test max redirects validation."""
        # Valid zero redirects
        config = SessionConfig(maxredirects=0)
        assert config.maxredirects == 0

        # Valid positive redirects
        config = SessionConfig(maxredirects=10)
        assert config.maxredirects == 10

        # Invalid negative redirects
        with pytest.raises(ValidationError) as exc:
            SessionConfig(maxredirects=-1)
        assert "Max redirects cannot be negative" in str(exc.value)

    def test_immutability(self):
        """Test that config is immutable (frozen)."""
        config = SessionConfig(timeout=30.0)

        # Should not be able to modify after creation
        with pytest.raises(ValidationError):
            config.timeout = 60.0

    def test_dict_updates(self):
        """Test that dict fields are properly copied."""
        original_headers = {"User-Agent": "Test"}
        config = SessionConfig(defaultheaders=original_headers)

        # Original dict should not be modified
        config.defaultheaders["Accept"] = "application/json"
        assert "Accept" not in original_headers

    def test_pooling_config(self):
        """Test connection pooling configuration."""
        config = SessionConfig(
            poolconnections=50,
            poolmaxsize=100
        )

        assert config.poolconnections == 50
        assert config.poolmaxsize == 100

    def test_retry_config(self):
        """Test retry configuration."""
        config = SessionConfig(
            maxretries=5,
            retrybackoff=1.5
        )

        assert config.maxretries == 5
        assert config.retrybackoff == 1.5

    def test_ssl_and_redirects(self):
        """Test SSL verification and redirect settings."""
        config = SessionConfig(
            verifyssl=False,
            allowredirects=False,
            maxredirects=0
        )

        assert config.verifyssl is False
        assert config.allowredirects is False
        assert config.maxredirects == 0

    def test_cookie_persistence(self):
        """Test cookie persistence settings."""
        config = SessionConfig(
            persistcookies=True,
            cookiefile="/path/to/cookies.jar"
        )

        assert config.persistcookies is True
        assert config.cookiefile == "/path/to/cookies.jar"
