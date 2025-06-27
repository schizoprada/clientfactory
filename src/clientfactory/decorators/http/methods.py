# ~/clientfactory/src/clientfactory/decorators/http/methods.py
"""
HTTP Method Decorators
---------------------
Enhanced decorators for defining API methods with comprehensive configuration support.
"""
from __future__ import annotations
import typing as t, functools as fn

from clientfactory.core.models import HTTPMethod, MethodConfig, Payload, MergeMode
from clientfactory.decorators.http.docs import DOCS

if t.TYPE_CHECKING:
    from clientfactory.core.models.methods import BoundMethod

def _generatedocstring(config: MethodConfig, func: t.Callable) -> str:
    """Generate enhanced docstring for decorated method."""
    def _description() -> str:
        """Get the main description section."""
        if config.description:
            return config.description
        elif func.__doc__ is not None:
           return func.__doc__.strip()
        else:
           return f"{config.method.value} {config.path or ''}"

    def _payload() -> list[str]:
        """Generate payload parameters section."""
        lines = []
        if config.payload:
            instance = _getpayloadinstance(config.payload)
            if instance and hasattr(instance, '_fields'):
                lines.append('Parameters:')
                for name, field in instance._fields.items():
                    required = " [required]" if field.required else ""
                    default = f" (default: {field.default})" if field.default is not None else ""
                    source = f" from '{field.source}'" if field.source != name else ""
                    lines.append(f"    {name}{required}{default}{source}")
        return lines

    def _config() -> list[str]:
        """Generate configuration info section."""
        lines = []

        if config.timeout is not None:
            lines.append(f"timeout={config.timeout}s")
        if config.retries is not None:
            lines.append(f"retries={config.retries}")
        if config.headers:
            lines.append(f"headers={len(config.headers)} custom")
        if config.cookies:
            lines.append(f"cookies={len(config.cookies)} custom")
        if config.headermode != MergeMode.MERGE:
            lines.append(f"headermode={config.headermode.value}")
        if config.cookiemode != MergeMode.MERGE:
            lines.append(f"cookiemode={config.cookiemode.value}")

        if lines:
            return [f"Configuration: {', '.join(lines)}"]
        return lines

    def _returns() -> list[str]:
        """Generate returns section."""
        return [
            "Returns:",
            "    Response data or Response object"
        ]

    lines = [_description(), ""]

    if (payload:=_payload()):
        lines.extend(payload)
        lines.append("")

    if (confs:=_config()):
        lines.extend(confs)
        lines.append("")

    lines.extend(_returns())
    return "\n".join(lines)

def _getpayloadinstance(payload: t.Union[Payload, t.Type[Payload]]) -> t.Optional[Payload]:
    """Get payload instance for introspection."""
    try:
        if isinstance(payload, type):
            return payload()
        return payload
    except Exception:
        return None

def _buildmethodconfig(
    func: t.Callable,
    method: HTTPMethod,
    path: t.Optional[str],
    headers: t.Optional[t.Dict[str, str]] = None,
    cookies: t.Optional[t.Dict[str, str]] = None,
    headermode: t.Optional[MergeMode] = None,
    cookiemode: t.Optional[MergeMode] = None,
    timeout: t.Optional[float] = None,
    retries: t.Optional[int] = None,
    payload: t.Optional[t.Union[Payload, t.Type[Payload]]] = None,
    preprocess: t.Optional[t.Callable] = None,
    postprocess: t.Optional[t.Callable] = None,
    description: t.Optional[str] = None,
    config: t.Optional[MethodConfig] = None,
    **kwargs: t.Any
) -> MethodConfig:
    """Build MethodConfig from decorator parameters."""
    data = {
        'name': func.__name__,
        'method': method,
        'path': path,
        'headers': headers,
        'cookies': cookies,
        'headermode': headermode,
        'cookiemode': cookiemode,
        'timeout': timeout,
        'retries': retries,
        'payload': payload,
        'preprocess': preprocess,
        'postprocess': postprocess,
        'description': (description or func.__doc__ or ""),
        **kwargs
    }
    constructs = {k:v for k,v in data.items() if v is not None}
    if config is not None:
        return config.model_copy(update=constructs)
    return MethodConfig(**constructs)

def _validatemethodusage(
    method: HTTPMethod,
    payload: t.Optional[t.Union[Payload, t.Type[Payload]]],
    func: t.Callable
) -> None:
    # all method allowed
    pass

def httpmethod(
    method: HTTPMethod,
    path: t.Optional[str] = None,
    *,
    config: t.Optional[MethodConfig] = None,
    payload: t.Optional[t.Union[Payload, t.Type[Payload]]] = None,
    headers: t.Optional[t.Dict[str, str]] = None,
    cookies: t.Optional[t.Dict[str, str]] = None,
    headermode: t.Optional[MergeMode] = None,
    cookiemode: t.Optional[MergeMode] = None,
    timeout: t.Optional[float] = None,
    retries: t.Optional[int] = None,
    preprocess: t.Optional[t.Callable] = None,
    postprocess: t.Optional[t.Callable] = None,
    description: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Callable[[t.Callable], 'BoundMethod']:
    """
    Base HTTP method decorator with comprehensive configuration support.

    Args:
        method: HTTP method type
        path: Endpoint path (can include parameters like {id})
        config: Pre-configured MethodConfig object
        payload: Payload class for request validation
        headers: Method-specific headers
        cookies: Method-specific cookies
        headermode: How to merge method headers with session headers
        cookiemode: How to merge method cookies with session cookies
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        preprocess: Function to transform request data
        postprocess: Function to transform response data
        description: Method description (overrides docstring)
        **kwargs: Additional configuration options

    Returns:
        Decorated function with _methodconfig attribute

    Raises:
        ValueError: For invalid decorator usage (e.g., GET with payload)
    """
    def decorator(func: t.Callable) -> 'BoundMethod':
        from clientfactory.core.utils.typed import UNSET
        from clientfactory.core.models.methods import BoundMethod

        _validatemethodusage(method, payload, func)

        conf = _buildmethodconfig(
            func=func,
            method=method,
            path=path,
            headers=headers,
            cookies=cookies,
            headermode=headermode,
            cookiemode=cookiemode,
            timeout=timeout,
            retries=retries,
            payload=payload,
            preprocess=preprocess,
            postprocess=postprocess,
            description=description,
            config=config,
            **kwargs
        )

        func._methodconfig = conf # type: ignore

        # Update docstring if description provided or payload available
        if description or (payload and not func.__doc__):
            func.__doc__ = _generatedocstring(conf, func)

        bound = BoundMethod(func, UNSET, conf)

        return t.cast('BoundMethod', bound)

    return decorator

# HTTP method decorators
def _createdecorator(method: HTTPMethod) -> t.Callable[..., t.Union['BoundMethod', t.Callable[[t.Callable], 'BoundMethod']]]:
    def decorator(funcorpath: t.Any = None, **kwargs):
        if callable(funcorpath):
            # no parentheses
            return httpmethod(method, None)(funcorpath)
        return httpmethod(method, funcorpath, **kwargs)
    decorator.__annotations__ = {'return': 'BoundMethod'}
    return t.cast(t.Callable[..., 'BoundMethod'], decorator)

get = _createdecorator(HTTPMethod.GET)
post = _createdecorator(HTTPMethod.POST)
put = _createdecorator(HTTPMethod.PUT)
patch = _createdecorator(HTTPMethod.PATCH)
delete = _createdecorator(HTTPMethod.DELETE)
head = _createdecorator(HTTPMethod.HEAD)
options = _createdecorator(HTTPMethod.OPTIONS)

get.__doc__ = DOCS.GET
post.__doc__ = DOCS.POST
put.__doc__ = DOCS.PUT
patch.__doc__ = DOCS.PATCH
delete.__doc__ = DOCS.DELETE
head.__doc__ = DOCS.HEAD
options.__doc__ = DOCS.OPTIONS
