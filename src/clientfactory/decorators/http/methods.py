# ~/clientfactory/src/clientfactory/decorators/http/methods.py
"""
HTTP Method Decorators
---------------------
Enhanced decorators for defining API methods with comprehensive configuration support.
"""
from __future__ import annotations
import typing as t, functools as fn

from clientfactory.core.models import HTTPMethod, MethodConfig, Payload

def _generatedocstring(config: MethodConfig, func: t.Callable) -> str:
    """Generate enhanced docstring for decorated method."""
    def _description() -> str:
        """Get the main description section."""
        if config.description is not None:
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
        #! MethodConfig does not accept `timeout` yet
        #! also missing retries and headers, probably need to implement ...

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
    config: t.Optional[MethodConfig],
    **kwargs: t.Any
) -> MethodConfig:
    """Build MethodConfig from decorator parameters."""
    if config is not None:
        updates = {k:v for k,v in kwargs.items() if v is not None}
        if path is not None:
            updates['path'] = path
        updates['method'] = method
        updates['name'] = func.__name__
        return config.model_copy(update=updates)

    return MethodConfig(
        name=func.__name__,
        method=method,
        path=path,
        description=kwargs.get('description', func.__doc__ or "") or (func.__doc__ or ""),
        **{k:v for k,v in kwargs.items() if k!='description' and v is not None}
    )

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
    #headers: t.Optional[t.Dict[str, str]] = None, #! not yet implemented
    #cookies: t.Optional[t.Dict[str, str]] = None, #! not yet implemented
    #timeout: t.Optional[float] = None, #! not yet implemented
    #retries: t.Optional[int] = None, #! not yet implemented
    preprocess: t.Optional[t.Callable] = None,
    postprocess: t.Optional[t.Callable] = None,
    description: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Callable[[t.Callable], t.Callable]:
    """
    Base HTTP method decorator with comprehensive configuration support.

    Args:
        method: HTTP method type
        path: Endpoint path (can include parameters like {id})
        config: Pre-configured MethodConfig object
        payload: Payload class for request validation
        preprocess: Function to transform request data
        postprocess: Function to transform response data
        description: Method description (overrides docstring)
        **kwargs: Additional configuration options

    Returns:
        Decorated function with _methodconfig attribute

    Raises:
        ValueError: For invalid decorator usage (e.g., GET with payload)
    """
    def decorator(func: t.Callable) -> t.Callable:
        _validatemethodusage(method, payload, func)

        conf = _buildmethodconfig(
            func=func,
            method=method,
            path=path,
            config=config,
            payload=payload,
            preprocess=preprocess,
            postprocess=postprocess,
            description=description,
            **kwargs
        )

        func._methodconfig = conf # type: ignore

        # Update docstring if description provided or payload available
        if description or (payload and not func.__doc__):
            func.__doc__ = _generatedocstring(conf, func)

        return func

    return decorator

# HTTP method decorators

class DOCS:
   GET: str = """
GET request decorator.

Args:
   path: Endpoint path (can include parameters like {id})
   config: Pre-configured MethodConfig object
   preprocess: Function to transform request data (typically for query params)
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Note: GET requests cannot have payloads. Use preprocess to handle query parameters.

Example:
   @get("{id}")
   def get_user(self, id): pass

   @get("search", preprocess=lambda data: {"params": data})
   def search_users(self, query): pass
"""

   POST: str = """
POST request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   payload: Payload class for request validation
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @post("users", payload=UserPayload)
   def create_user(self, **data): pass

   @post("bulk", config=BulkCreateConfig)
   def bulk_create(self, **data): pass
"""

   PUT: str = """
PUT request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   payload: Payload class for request validation
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @put("{id}", payload=UserPayload)
   def update_user(self, id, **data): pass
"""

   PATCH: str = """
PATCH request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   payload: Payload class for request validation
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @patch("{id}", payload=UserUpdatePayload)
   def partial_update_user(self, id, **data): pass
"""

   DELETE: str = """
DELETE request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @delete("{id}")
   def delete_user(self, id): pass

   @delete("batch", preprocess=lambda data: {"json": {"ids": data["ids"]}})
   def batch_delete(self, ids): pass
"""

   HEAD: str = """
HEAD request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Note: HEAD requests cannot have payloads.

Example:
   @head("{id}")
   def check_user_exists(self, id): pass
"""

   OPTIONS: str = """
OPTIONS request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @options("users")
   def get_user_options(self): pass
"""

def _createdecorator(method: HTTPMethod) -> t.Callable:
    def decorator(funcorpath: t.Any = None, **kwargs):
        if callable(funcorpath):
            # no parentheses
            return httpmethod(method, None)(funcorpath)
        return httpmethod(method, funcorpath, **kwargs)
    return decorator

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
