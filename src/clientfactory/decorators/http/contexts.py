# ~/clientfactory/src/clientfactory/decorators/http/contexts.py
"""
HTTP Contexts Decorators
------------------------
Decorators for defining the request contexts for API methods e.g. Headers & Cookies
"""
from __future__ import annotations
import typing as t, functools as fn

from clientfactory.core.models import Headers, Cookies

from clientfactory.logs import log

def headers(cls: t.Type) -> Headers:
    """
    Decorator to transform a class into a Headers instance.

    Extracts class attributes and creates a Headers object with proper normalization.

    Example:
        @headers
        class MyHeaders:
            authorization = "Bearer token123"
            content_type = ("Content-Type", "application/json")
            custom = {"X-Custom": "value"}

    Returns:
        Headers instance containing all non-private class attributes
    """
    obj = Headers(cls)
    log.info(f"@headers | collected: {obj}")
    return obj


def cookies(cls: t.Type) -> Cookies:
    """
    Decorator to transform a class into a Cookies instance.

    Extracts class attributes and creates a Cookies object.

    Example:
        @cookies
        class MyCookies:
            sessionid = "abc123"
            auth_token = ("auth-token", "xyz789")
            custom = {"custom-cookie": "value"}

    Returns:
        Cookies instance containing all non-private class attributes
    """
    return Cookies(cls)
