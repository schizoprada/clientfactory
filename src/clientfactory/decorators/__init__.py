# ~/clientfactory/src/clientfactory/decorators/__init__.py

from .http import (
    httpmethod, get, post,
    put, patch, delete,
    head, options
)

from .resources import (
    resource,
    searchable,
    manageable
)
