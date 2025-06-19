# ~/clientfactory/src/clientfactory/decorators/__init__.py

from .auths import (
    baseauth, jwt, dpop
)

from .backends import (
    basebackend, algolia, graphql
)

from .configs import (
    configs
)

from .engines import (
    engine
)


from .http import (
    httpmethod, get, post,
    put, patch, delete,
    head, options, headers,
    cookies, param, payload
)

from .persistences import (
    persistence
)

from .resources import (
    resource,
    searchable,
    manageable
)

from .sessions import (
    basesession, session
)
