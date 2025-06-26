# ~/clientfactory/src/clientfactory/core/utils/request/building.py
"""
Request Building Utilities
-------------------------
Utilities for constructing and configuring HTTP requests.
"""
from __future__ import annotations
import typing as t

if t.TYPE_CHECKING:
    from clientfactory.core.models import HTTPMethod, RequestModel, MethodConfig


def separatekwargs(method: 'HTTPMethod', **kwargs) -> tuple[dict, dict]:
    """
    Separate kwargs into request fields and body data based on HTTP method.

    Args:
        method: HTTP method type
        **kwargs: Mixed request parameters

    Returns:
        Tuple of (request_fields, body_data)

    Note:
        For GET/HEAD/OPTIONS: non-field kwargs become query params
        For POST/PUT/PATCH: non-field kwargs become request body
    """
    fields = {}
    body = {}

    fieldnames = {
        'headers', 'params', 'cookies', 'timeout',
        'allowredirects', 'verifyssl', 'data', 'files'
    }
    bodymethods = {'POST', 'PUT', 'PATCH'}

    if method.value in bodymethods:
        for k,v in kwargs.items():
            if k in fieldnames:
                fields[k] = v
            else:
                body[k] = v
    else:
        # for GET/HEAD/OPTIONS, put non-field kwargs into params
        extparams = kwargs.get('params', {})
        newparams = {}
        for k, v in kwargs.items():
            if k in fieldnames:
                if k == 'params':
                    continue
                fields[k] = v
            else:
                newparams[k] = v

        # merge all params
        if (newparams or extparams):
            params = {**extparams, **newparams}
            fields['params'] = params

    return (fields, body)

def buildrequest(
    method: t.Union[str, 'HTTPMethod'],
    baseurl: str,
    path: t.Optional[str] = None,
    resourcepath: t.Optional[str] = None,
    **kwargs: t.Any
) -> 'RequestModel':
    """
    Build a RequestModel from components.

    Args:
        method: HTTP method
        baseurl: Base URL for the request
        path: Method-specific path segment
        resourcepath: Resource-specific path segment (for resources)
        **kwargs: Request parameters (headers, data, etc.)

    Returns:
        Configured RequestModel instance

    URL Construction:
        Client: baseurl/path
        Resource: baseurl/resourcepath/path
    """
    from clientfactory.core.models import HTTPMethod, RequestModel

    if isinstance(method, str):
        method = HTTPMethod(method.upper())

    ## url construction ##
    base = baseurl.rstrip('/')
    parts = [base]

    if resourcepath: parts.append(resourcepath.strip('/'))
    if path: parts.append(path.strip('/'))

    url = '/'.join(parts)

    ## separate fields and body ##
    fields, body = separatekwargs(method, **kwargs)

    if body:
        return RequestModel(
            method=method,
            url=url,
            json=body,
            **fields
        )

    return RequestModel(
        method=method,
        url=url,
        **fields
    )

def applymethodconfig(request: 'RequestModel', config: 'MethodConfig') -> 'RequestModel':
    """
    Apply method-specific configuration to a request.

    Args:
        request: Base request model
        config: Method configuration with headers, cookies, timeout, etc.

    Returns:
        Updated request model with method config applied

    Note:
        Respects merge modes for headers and cookies (MERGE vs OVERWRITE)
    """
    from clientfactory.core.models import RequestModel, MergeMode
    constructs = {
        'headers': request.headers.copy(),
        'cookies': request.cookies.copy(),
        'timeout': request.timeout,
        #'retries': request.retries // currently, retries are not in the RequestModel
    }
    if config.headers:
        if config.headermode == MergeMode.MERGE:
            constructs['headers'].update(config.headers)
        elif config.headermode == MergeMode.OVERWRITE:
            constructs['headers'] = config.headers

    if config.cookies:
        if config.cookiemode == MergeMode.MERGE:
            constructs['cookies'].update(config.cookies)
        elif config.cookiemode == MergeMode.OVERWRITE:
            constructs['cookies'] = config.cookies

    if config.timeout is not None:
        constructs['timeout'] = config.timeout

    return request.model_copy(update=constructs)
