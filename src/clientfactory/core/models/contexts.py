# ~/clientfactory/src/clientfactory/core/models/contexts.py
"""
Request Context Models
----------------------
Dict-compatible classes for headers, cookies, and other request contexts.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models.enums import MergeMode
from clientfactory.core.models.request import RequestModel, ResponseModel



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



class SessionInitializer:
    """
    Initialize session state from an HTTP request.

    Executes a request and extracts cookies, headers, or other session data
    for bootstrapping session state.
    """

    def __init__(
        self,
        request: 'RequestModel',
        headers: bool = True, # whether to extract headers
        cookies: bool = True, # whether to extract cookies
        headermode: MergeMode = MergeMode.MERGE,
        cookiemode: MergeMode = MergeMode.MERGE,
    ) -> None:
        """..."""
        self.request: 'RequestModel' = request
        self.headers: bool = headers
        self.cookies: bool = cookies
        self.headermode: MergeMode = MergeMode(headermode)
        self.cookiemode: MergeMode = MergeMode(cookiemode)


    def execute(self) -> 'ResponseModel':
        """..."""
        import requests as rq
        method = self.request.method.value.lower()
        if (
            hasattr(rq, method) and
            (caller:=getattr(rq, method)) and
            callable(caller)
        ):
            try:
                kwargs = self.request.tokwargs()
                response: rq.Response = caller(**kwargs) # type: ignore
                response.raise_for_status()
                return ResponseModel.FromRequests(response)
            except Exception as e:
                raise RuntimeError(f"Exception executing initial request: {e}")
        raise ValueError(f"Unsupported request method: {method.upper()}")

    def extract(self, response: 'ResponseModel') -> t.Dict[str, t.Any]:
        """
        Extract session data from response.

        Args:
            response: Response to extract from

        Returns:
            Dict with 'cookies' and/or 'headers' keys
        """
        extracted = {}

        if self.headers and response.headers:
            extracted['headers'] = response.headers

        if self.cookies and response.cookies:
            extracted['cookies'] = response.cookies

        return extracted

    def _setupdict(self, obj: dict, extracted: dict) -> dict:
        """Initialize dict-style session object."""

        if ('headers' in extracted) and self.headers:
            if self.headermode == MergeMode.MERGE:
                if ('headers' not in obj):
                    obj['headers'] = {}
                obj['headers'].update(extracted['headers'])
            elif self.headermode == MergeMode.OVERWRITE:
                obj['headers'] = extracted['headers'].copy()

        if ('cookies' in extracted) and self.cookies:
            if self.cookiemode == MergeMode.MERGE:
                if ('cookies' not in obj):
                    obj['cookies'] = {}
                obj['cookies'].update(extracted['cookies'])
            elif self.cookiemode == MergeMode.OVERWRITE:
                obj['cookies'] = extracted['cookies'].copy()

        return obj

    def _setuptyped(self, obj: t.Any, extracted: dict) -> t.Any:
        """Initialize requests.Session-style object."""
        if ('headers' in extracted) and self.headers:
            if self.headermode == MergeMode.MERGE:
                obj.headers.update(extracted['headers'])
            elif self.headermode == MergeMode.OVERWRITE:
                obj.headers.clear()
                obj.headers.update(extracted['headers'])

        if ('cookies' in extracted) and self.cookies:
            if self.cookiemode == MergeMode.MERGE:
               obj.cookies.update(extracted['cookies'])
            elif self.cookiemode == MergeMode.OVERWRITE:
               obj.cookies.clear()
               obj.cookies.update(extracted['cookies'])

        return obj


    def _setupobject(self, obj: t.Any, extracted: dict) -> t.Any:
        """Initialize generic object with setattr."""
        for x in ('headers', 'cookies'):
            if (x in extracted) and (getattr(self, x, False) is True):
                setattr(obj, x, extracted[x])

        return obj

    def initialize(self, obj: t.Any) -> t.Any:
        """
        Initialize session object with extracted data.

        Args:
            obj: Session object to initialize (dict, requests.Session, etc.)

        Returns:
            Updated session object
        """
        response = self.execute()
        extracted = self.extract(response)

        if isinstance(obj, dict):
            return self._setupdict(obj, extracted)
        elif hasattr(obj, 'headers') and hasattr(obj, 'cookies'):
            return self._setuptyped(obj, extracted)
        else:
            return self._setupobject(obj, extracted)
