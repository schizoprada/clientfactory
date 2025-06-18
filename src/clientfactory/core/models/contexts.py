# ~/clientfactory/src/clientfactory/core/models/contexts.py
"""
Request Context Models
----------------------
Dict-compatible classes for headers, cookies, and other request contexts.
"""
from __future__ import annotations
import typing as t


class Headers(dict):
    """
    Headers that auto-normalize names and behave like a dict.

    Can be initialized from:
    - Regular dict: Headers({"Content-Type": "application/json"})
    - Kwargs: Headers(content_type="application/json", x_api_key="123")
    - Class instance: Headers(MyHeadersClass)
    - Inheritance: class MyHeaders(Headers): ...
    """

    def __init__(
        self,
        *args,
        normalize: bool = True,
        normalizer: t.Optional[t.Callable[[str], str]] = None,
        **kwargs
    ) -> None:
        self.normalize: bool = normalize
        self.normalizer: t.Callable[[str], str] = (normalizer or self._normalize)
        super().__init__()
        self._initialize(*args, **kwargs)


    def _normalize(self, key: str) -> str:
        """Convert underscores to hyphens for HTTP headers."""
        if not self.normalize:
            return key
        return key.replace('_', '-').title()


    def _processitem(self, key: str, value: t.Any) -> None:
        """Process key:value pair and add to headers."""
        if isinstance(value, tuple) and len(value) == 2:
            # Tuple format: (header_name, header_value)
            k,v = value
        elif isinstance(value, dict):
            # Dict format: merge into headers
            for dk, dv in value.items():
                self._processitem(dk, dv)
            return
        else:
            # Regular format: use key as header name
            k = self.normalizer(key)
            v = value

        super().__setitem__(k, str(v))

    def _processclassattrs(self) -> None:
        """Process class attributes for inheritance pattern"""
        for name, value in self.__class__.__dict__.items():
            if (not name.startswith('_')) and (not callable(value)):
                self._processitem(name, value)


    def _initialize(self, *args, **kwargs) -> None:
        """Initialize Headers dict with args and kwargs"""
        if self.__class__ is not Headers:
            self._processclassattrs()

        if (
            args and
            hasattr(args[0], '__dict__') and
            not isinstance(args[0], dict)
        ):
            for name, value in args[0].__dict__.items():
                if not name.startswith('_'):
                    self._processitem(name, value)

        elif args:
            temp = dict(*args)
            for k,v in temp.items():
                self._processitem(k, v)

        for k,v in kwargs.items():
            self._processitem(k, v)


    def __setitem__(self, key: str, value: t.Any) -> None:
        """Override setitem to process values."""
        self._processitem(key, value)

    def __rshift__(self, other: t.Any) -> 'Headers':
        """Update another Headers or Dict with this Headers values"""
        if not isinstance(other, (dict, Headers)):
            raise ValueError(f"Cannot merge headers with: {type(other)}")

        other.update(self)

        if isinstance(other, Headers):
            return other
        return Headers(other)

    def __lshift__(self, other: t.Any) -> 'Headers':
        """Update this Headers with other Headers or Dict values"""
        if not isinstance(other, (dict, Headers)):
            raise ValueError(f"Cannot merge headers with: {type(other)}")

        self.update(other)

        return self


class Cookies(dict):
    """
    Cookies that behave like a dict.

    Can be initialized from:
    - Regular dict: Cookies({"session": "abc123"})
    - Kwargs: Cookies(session="abc123", csrf="token456")
    - Class instance: Cookies(MyCookiesClass)
    - Inheritance: class MyCookies(Cookies): ...
    """

    def __init__(
        self,
        *args,
        normalize: bool = False,
        normalizer: t.Optional[t.Callable[[str], str]] = None,
        **kwargs
    ) -> None:
        self.normalize: bool = normalize
        self.normalizer: t.Callable[[str], str] = (normalizer or self._normalize)
        super().__init__()
        self._initialize(*args, **kwargs)


    def _normalize(self, key: str) -> str:
        """Default normalizer (no-op for cookies)."""
        if not self.normalize:
            return key
        return key


    def _processitem(self, key: str, value: t.Any) -> None:
        """Process key:value pair and add to cookies."""
        if isinstance(value, tuple) and len(value) == 2:
            # Tuple format: (cookie_name, cookie_value)
            k,v = value
        elif isinstance(value, dict):
            # Dict format: merge into cookies
            for dk, dv in value.items():
                self._processitem(dk, dv)
            return
        else:
            # Regular format: use key as cookie name
            k = self.normalizer(key)
            v = value

        super().__setitem__(k, str(v))

    def _processclassattrs(self) -> None:
        """Process class attributes for inheritance pattern"""
        for name, value in self.__class__.__dict__.items():
            if (not name.startswith('_')) and (not callable(value)):
                self._processitem(name, value)

    def _initialize(self, *args, **kwargs) -> None:
        """Initialize Cookies dict with args and kwargs"""
        if self.__class__ is not Cookies:
            self._processclassattrs()

        if (
            args and
            hasattr(args[0], '__dict__') and
            not isinstance(args[0], dict)
        ):
            for name, value in args[0].__dict__.items():
                if not name.startswith('_'):
                    self._processitem(name, value)

        elif args:
            temp = dict(*args)
            for k,v in temp.items():
                self._processitem(k, v)

        for k,v in kwargs.items():
            self._processitem(k, v)


    def __setitem__(self, key: str, value: t.Any) -> None:
        """Override setitem to process values."""
        self._processitem(key, value)

    def __rshift__(self, other: t.Any) -> 'Cookies':
        """Update another Cookies or Dict with this Cookies values"""
        if not isinstance(other, (dict, Cookies)):
            raise ValueError(f"Cannot merge cookies with: {type(other)}")

        other.update(self)

        if isinstance(other, Cookies):
            return other
        return Cookies(other)

    def __lshift__(self, other: t.Any) -> 'Cookies':
        """Update this Cookies with other Cookies or Dict values"""
        if not isinstance(other, (dict, Cookies)):
            raise ValueError(f"Cannot merge cookies with: {type(other)}")

        self.update(other)

        return self
