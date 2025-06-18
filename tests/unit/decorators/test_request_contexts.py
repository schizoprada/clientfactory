# ~/clientfactory/tests/unit/decorators/test_request_contexts.py
"""
Unit tests for request context decorators.
"""
import pytest

from clientfactory.decorators.http.contexts import headers, cookies
from clientfactory.core.models import Headers, Cookies


class TestHeadersDecorator:
    """Test @headers decorator."""

    def test_headers_decorator_basic(self):
        """Test basic @headers decorator usage."""
        @headers
        class MyHeaders:
            authorization = "Bearer token123"
            content_type = "application/json"

        assert isinstance(MyHeaders, Headers)
        assert MyHeaders["Authorization"] == "Bearer token123"
        assert MyHeaders["Content-Type"] == "application/json"

    def test_headers_decorator_with_tuples(self):
        """Test @headers decorator with tuple values."""
        @headers
        class MyHeaders:
            auth = ("Authorization", "Bearer token123")
            content = ("Content-Type", "application/json")

        assert MyHeaders["Authorization"] == "Bearer token123"
        assert MyHeaders["Content-Type"] == "application/json"

    def test_headers_decorator_with_dict(self):
        """Test @headers decorator with dict values."""
        @headers
        class MyHeaders:
            basic = "Bearer token"
            custom = {"X-Custom": "value", "X-Another": "another"}

        assert MyHeaders["Basic"] == "Bearer token"
        assert MyHeaders["X-Custom"] == "value"
        assert MyHeaders["X-Another"] == "another"

    def test_headers_decorator_ignores_private_attrs(self):
        """Test @headers decorator ignores private attributes."""
        @headers
        class MyHeaders:
            _private = "should be ignored"
            __dunder = "should be ignored"
            public = "should be included"

        assert "Public" in MyHeaders
        assert "_private" not in MyHeaders
        assert "__dunder" not in MyHeaders

    def test_headers_decorator_result_is_dict_compatible(self):
        """Test that decorated result works as dict."""
        @headers
        class MyHeaders:
            authorization = "Bearer token"

        # Should work in dict operations
        result = {"existing": "header"}
        result.update(MyHeaders)

        assert result["existing"] == "header"
        assert result["Authorization"] == "Bearer token"


class TestCookiesDecorator:
    """Test @cookies decorator."""

    def test_cookies_decorator_basic(self):
        """Test basic @cookies decorator usage."""
        @cookies
        class MyCookies:
            sessionid = "abc123"
            csrf = "token456"

        assert isinstance(MyCookies, Cookies)
        assert MyCookies["sessionid"] == "abc123"
        assert MyCookies["csrf"] == "token456"

    def test_cookies_decorator_with_tuples(self):
        """Test @cookies decorator with tuple values."""
        @cookies
        class MyCookies:
            session = ("session-id", "abc123")
            auth = ("auth-token", "xyz789")

        assert MyCookies["session-id"] == "abc123"
        assert MyCookies["auth-token"] == "xyz789"

    def test_cookies_decorator_with_dict(self):
        """Test @cookies decorator with dict values."""
        @cookies
        class MyCookies:
            basic = "abc123"
            custom = {"custom-cookie": "value", "another-cookie": "another"}

        assert MyCookies["basic"] == "abc123"
        assert MyCookies["custom-cookie"] == "value"
        assert MyCookies["another-cookie"] == "another"

    def test_cookies_decorator_ignores_private_attrs(self):
        """Test @cookies decorator ignores private attributes."""
        @cookies
        class MyCookies:
            _private = "should be ignored"
            __dunder = "should be ignored"
            public = "should be included"

        assert "public" in MyCookies
        assert "_private" not in MyCookies
        assert "__dunder" not in MyCookies

    def test_cookies_decorator_result_is_dict_compatible(self):
        """Test that decorated result works as dict."""
        @cookies
        class MyCookies:
            session = "abc123"

        # Should work in dict operations
        result = {"existing": "cookie"}
        result.update(MyCookies)

        assert result["existing"] == "cookie"
        assert result["session"] == "abc123"
