# ~/clientfactory/src/clientfactory/decorators/http/data.py
"""
HTTP Data Decorators
--------------------
Decorators for defining request data components like parameters and payloads.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models import Param, Payload

def _createparam(cls: t.Type) -> Param:
    """Helper to create Param objects from class attributes."""
    attrs = {
        k: v for k, v in cls.__dict__.items()
        if not k.startswith('_') and (
            not callable(v) or
            k in getattr(Param, '__constructs__', set())
        )
    }
    return Param(**attrs) # type: ignore[arg-type]



def _createpayload(cls: t.Type) -> t.Type[Payload]:
    """Helper to create Payload classes from class attributes."""
    fields = {}
    for name, value in cls.__dict__.items():
        if (not name.startswith('_')) and (not callable(value)):
            if isinstance(value, Param):
                fields[name] = value
            else:
                if isinstance(value, dict):
                    fields[name] = Param(**value)
                elif isinstance(value, (tuple, list)):
                    instance = Param(*value)
                    instance.name = name
                    fields[name] = instance
                else:
                    instance = Param(default=value) #! this may need review
                    instance.name = name
                    fields[name] = instance

    pname = f"{cls.__name__}Payload" if ('payload' not in cls.__name__.lower()) else cls.__name__

    pclass = type(
        pname,
        (Payload,),
        fields
    )

    if cls.__doc__:
        pclass.__doc__ = cls.__doc__

    if hasattr(cls, '__module__'):
        pclass.__module__ = cls.__module__

    if hasattr(cls, '__qualname__'):
        pclass.__qualname__ = cls.__qualname__

    return pclass


def param(cls: t.Type) -> Param:
    """
    Decorator to transform a class into a Param instance.

    Example:
        @param
        class UserID:
            source = "user_id"
            required = True
            transform = int
            default = None

    Returns:
        Param instance configured from class attributes
    """
    return _createparam(cls)


def payload(cls: t.Type) -> t.Type[Payload]:
    """
    Decorator to transform a class into a Payload class.

    Example:
        @payload
        class UserPayload:
            user_id = Param(source="id", required=True)
            email = Param(source="email_addr", required=True)
            name = Param(source="full_name", default="Unknown")

    Returns:
        Payload class configured from class attributes
    """
    return _createpayload(cls)
