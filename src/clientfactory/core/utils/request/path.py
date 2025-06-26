# ~/clientfactory/src/clientfactory/core/utils/request/path.py
"""
Path Parameter Utilities
------------------------
Utilities for handling URL path parameter resolution and substitution.
"""
from __future__ import annotations
import typing as t


def resolveargs(path: t.Optional[str] = None, *args, **kwargs) -> dict:
    """
    Extract positional args into kwargs based on path parameter names.

    Args:
        path: URL path template with {param} placeholders
        *args: Positional arguments to map to path parameters
        **kwargs: Existing keyword arguments

    Returns:
        Updated kwargs dict with positional args mapped to parameter names

    Example:
        resolveargs("/users/{id}/posts/{post_id}", 123, 456, name="John")
        # Returns: {"id": 123, "post_id": 456, "name": "John"}
    """
    if (not path) or (not args):
        return kwargs

    import string
    formatter = string.Formatter()
    pathparams = [pname for _, pname, _, _ in formatter.parse(path) if pname]

    result = kwargs.copy()

    for i, arg in enumerate(args):
        if (i < len(pathparams)):
            result[pathparams[i]] = arg

    return result


def substitute(path: t.Optional[str] = None, **kwargs) -> tuple[t.Optional[str], t.List[str]]:
    """
    Substitute path parameters using string formatting.

    Args:
        path: URL path template with {param} placeholders
        **kwargs: Parameter values for substitution

    Returns:
        Tuple of (formatted_path, consumed_parameter_names)

    Raises:
        ValueError: If required path parameters are missing

    Example:
        substitute("/users/{id}", id=123, name="John")
        # Returns: ("/users/123", ["id"])
    """
    if not path:
        return path, []

    import string
    formatter = string.Formatter()

    try:
        consumed = [fname for _, fname, _, _ in formatter.parse(path) if fname]
        return path.format(**kwargs), consumed
    except KeyError as e:
        raise ValueError(f"Missing path parameter: {e}")
