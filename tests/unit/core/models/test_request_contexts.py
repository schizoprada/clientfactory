# ~/clientfactory/tests/unit/core/models/test_request_contexts.py
"""
Unit tests for Headers and Cookies context models.
"""
import pytest

from clientfactory.core.models import Headers, Cookies


class TestHeaders:
    """Test Headers functionality."""

    def test_headers_creation_from_kwargs(self):
        """Test creating headers from kwargs."""
        headers = Headers(content_type="application/json", x_api_key="123")

        assert headers["Content-Type"] == "application/json"
        assert headers["X-Api-Key"] == "123"

    def test_headers_creation_from_dict(self):
        """Test creating headers from dict."""
        headers = Headers({"Authorization": "Bearer token", "Accept": "application/json"})

        assert headers["Authorization"] == "Bearer token"
        assert headers["Accept"] == "application/json"

    def test_headers_creation_from_class(self):
        """Test creating headers from class instance."""
        class MyHeaders:
            authorization = "Bearer token"
            content_type = ("Content-Type", "application/json")
            custom = {"X-Custom": "value"}

        headers = Headers(MyHeaders)

        assert headers["Authorization"] == "Bearer token"
        assert headers["Content-Type"] == "application/json"
        assert headers["X-Custom"] == "value"

    def test_headers_inheritance(self):
        """Test headers through inheritance."""
        class MyHeaders(Headers):
            authorization = "Bearer token"
            content_type = ("Content-Type", "application/json")

        headers = MyHeaders()

        assert headers["Authorization"] == "Bearer token"
        assert headers["Content-Type"] == "application/json"

    def test_headers_normalization(self):
        """Test underscore to hyphen normalization."""
        headers = Headers(user_agent="Test Client", x_custom_header="value")

        assert headers["User-Agent"] == "Test Client"
        assert headers["X-Custom-Header"] == "value"

    def test_headers_no_normalization(self):
        """Test disabling normalization."""
        headers = Headers(user_agent="Test Client", normalize=False)

        assert headers["user_agent"] == "Test Client"

    def test_headers_custom_normalizer(self):
        """Test custom normalizer function."""
        def uppercase_normalizer(key):
            return key.upper()

        headers = Headers(content_type="json", normalizer=uppercase_normalizer)

        assert headers["CONTENT_TYPE"] == "json"

    def test_headers_setitem(self):
        """Test setting items after creation."""
        headers = Headers()
        headers["user_agent"] = "Test Client"

        assert headers["User-Agent"] == "Test Client"

    def test_headers_rshift_operator(self):
        """Test >> operator for updating other headers/dict."""
        headers1 = Headers(authorization="Bearer token")
        headers2 = Headers(content_type="application/json")

        result = headers1 >> headers2

        assert result["Authorization"] == "Bearer token"
        assert result["Content-Type"] == "application/json"
        assert isinstance(result, Headers)

    def test_headers_lshift_operator(self):
        """Test << operator for updating self."""
        headers1 = Headers(authorization="Bearer token")
        headers2 = Headers(content_type="application/json")

        result = headers1 << headers2

        assert result is headers1
        assert headers1["Authorization"] == "Bearer token"
        assert headers1["Content-Type"] == "application/json"

    def test_headers_dict_compatibility(self):
        """Test that Headers work as regular dicts."""
        headers = Headers(content_type="application/json")

        # Test dict methods
        assert "Content-Type" in headers
        assert headers.get("Content-Type") == "application/json"
        assert list(headers.keys()) == ["Content-Type"]
        assert len(headers) == 1


    def test_headers_integration_with_requestmodel(self):
        """Test Headers integration with RequestModel."""
        from clientfactory.core.models import RequestModel, HTTPMethod

        headers = Headers(authorization="Bearer token", content_type="application/json")

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            headers=headers
        )

        assert request.headers["Authorization"] == "Bearer token"
        assert request.headers["Content-Type"] == "application/json"

        # Test withheaders method
        additional_headers = Headers(x_api_key="123456")
        new_request = request.withheaders(additional_headers)

        assert new_request.headers["Authorization"] == "Bearer token"
        assert new_request.headers["Content-Type"] == "application/json"
        assert new_request.headers["X-Api-Key"] == "123456"

    def test_headers_integration_with_session(self):
        """Test Headers integration with Session."""
        from clientfactory.core.session import Session
        from clientfactory.core.models import RequestModel, HTTPMethod

        headers = Headers(user_agent="Test Client", x_custom="value")
        session = Session(headers=headers)

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )

        prepared = session.preparerequest(request)

        assert prepared.headers["User-Agent"] == "Test Client"
        assert prepared.headers["X-Custom"] == "value"

class TestCookies:
    """Test Cookies functionality."""

    def test_cookies_creation_from_kwargs(self):
        """Test creating cookies from kwargs."""
        cookies = Cookies(sessionid="abc123", csrf="token456")

        assert cookies["sessionid"] == "abc123"
        assert cookies["csrf"] == "token456"

    def test_cookies_creation_from_dict(self):
        """Test creating cookies from dict."""
        cookies = Cookies({"session": "abc123", "auth": "xyz789"})

        assert cookies["session"] == "abc123"
        assert cookies["auth"] == "xyz789"

    def test_cookies_creation_from_class(self):
        """Test creating cookies from class instance."""
        class MyCookies:
            sessionid = "abc123"
            auth_token = ("auth-token", "xyz789")
            custom = {"custom-cookie": "value"}

        cookies = Cookies(MyCookies)

        assert cookies["sessionid"] == "abc123"
        assert cookies["auth-token"] == "xyz789"
        assert cookies["custom-cookie"] == "value"

    def test_cookies_inheritance(self):
        """Test cookies through inheritance."""
        class MyCookies(Cookies):
            sessionid = "abc123"
            auth_token = ("auth-token", "xyz789")

        cookies = MyCookies()

        assert cookies["sessionid"] == "abc123"
        assert cookies["auth-token"] == "xyz789"

    def test_cookies_no_normalization_by_default(self):
        """Test that cookies don't normalize by default."""
        cookies = Cookies(session_id="abc123")

        assert cookies["session_id"] == "abc123"

    def test_cookies_with_normalization(self):
        """Test cookies with normalization enabled."""
        def hyphen_normalizer(key):
            return key.replace('_', '-')

        cookies = Cookies(session_id="abc123", normalize=True, normalizer=hyphen_normalizer)

        assert cookies["session-id"] == "abc123"

    def test_cookies_setitem(self):
        """Test setting items after creation."""
        cookies = Cookies()
        cookies["session_id"] = "abc123"

        assert cookies["session_id"] == "abc123"

    def test_cookies_rshift_operator(self):
        """Test >> operator for updating other cookies/dict."""
        cookies1 = Cookies(session="abc123")
        cookies2 = Cookies(csrf="token456")

        result = cookies1 >> cookies2

        assert result["session"] == "abc123"
        assert result["csrf"] == "token456"
        assert isinstance(result, Cookies)

    def test_cookies_lshift_operator(self):
        """Test << operator for updating self."""
        cookies1 = Cookies(session="abc123")
        cookies2 = Cookies(csrf="token456")

        result = cookies1 << cookies2

        assert result is cookies1
        assert cookies1["session"] == "abc123"
        assert cookies1["csrf"] == "token456"

    def test_cookies_dict_compatibility(self):
        """Test that Cookies work as regular dicts."""
        cookies = Cookies(session="abc123")

        # Test dict methods
        assert "session" in cookies
        assert cookies.get("session") == "abc123"
        assert list(cookies.keys()) == ["session"]
        assert len(cookies) == 1


    def test_cookies_integration_with_requestmodel(self):
        """Test Cookies integration with RequestModel."""
        from clientfactory.core.models import RequestModel, HTTPMethod

        cookies = Cookies(sessionid="abc123", csrf="token456")

        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            cookies=cookies
        )

        assert request.cookies["sessionid"] == "abc123"
        assert request.cookies["csrf"] == "token456"

        # Test withcookies method
        additional_cookies = Cookies(auth="xyz789")
        new_request = request.withcookies(additional_cookies)

        assert new_request.cookies["sessionid"] == "abc123"
        assert new_request.cookies["csrf"] == "token456"
        assert new_request.cookies["auth"] == "xyz789"
