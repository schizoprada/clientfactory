# ~/clientfactory/src/clientfactory/core/bases/resource.py
"""
Base Resource Implementation
---------------------------
Abstract base class for API resources.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import (
    ResourceConfig, RequestModel, ResponseModel,
    HTTPMethod
)
from clientfactory.core.protos import (
    SessionProtocol, BackendProtocol, PayloadProtocol
)
from clientfactory.core.bases.session import BaseSession
from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.metas.protocoled import ProtocoledAbstractMeta

if t.TYPE_CHECKING:
    from clientfactory.core.bases.client import BaseClient

class BaseResource(abc.ABC, Declarative):
    """
    Abstract base class for API resources.

    Handles method discovery, URL construction, and request building.
    Resources represent logical groupings of related API endpoints.
    """
    __declaredas__: str = 'resource'
    __declcomps__: set = {'auth', 'backend', 'persistence', 'session'}
    __declattrs__: set = {'path', 'name', 'description', 'tags', 'standalone', 'baseurl'}
    __declconfs__: set = {'timeout', 'retries'}

    def __init__(
        self,
        client: 'BaseClient',
        config: t.Optional[ResourceConfig] = None,
        session: t.Optional[BaseSession] = None,
        backend: t.Optional[BackendProtocol] = None,
        **kwargs: t.Any,
    ) -> None:
        """Initialize resource with client and configuration."""
        # 1. resolve components
        components = self._resolvecomponents(session=session, backend=backend)
        self._session: BaseSession = (components['session'] or client._engine._session)
        self._backend: t.Optional[BackendProtocol] = (components['backend'] or client._backend)

        # 2. resolve config
        self._config: ResourceConfig = self._resolveconfig(ResourceConfig, config, **kwargs)

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)

        self._client: 'BaseClient' = client
        self._methods: t.Dict[str, t.Callable] = {}
        self._children: t.Dict[str, 'BaseResource'] = {}

        # initialize resources
        self._initmethods()
        self._initchildren()

    def _resolveattributes(self, attributes: dict) -> None:
        self.path: str = attributes.get('path', '')
        self.name: str = attributes.get('name', '')
        self.description: str = attributes.get('description', '')
        self.baseurl: t.Optional[str] = attributes.get('baseurl')
        self.standalone: bool = attributes.get('standalone', False)

    ## abstracts ##
    @abc.abstractmethod
    def _registermethod(self, method: t.Callable, name: t.Optional[str] = None) -> None:
        """
        Register a single method with the resource.

        Called by addmethod and _initmethods for each discovered method.
        Concrete resources implement method registration logic.

        Args:
            method: Callable method to register
            name: Optional name override (defaults to method.__name__)
        """
        ...

    @abc.abstractmethod
    def _registerchild(self, child: 'BaseResource', name: t.Optional[str] = None) -> None:
        """
        Register a single child resource.

        Called by addchild and _initchildren for each discovered child.
        Concrete resources implement child registration logic.

        Args:
            child: Child resource to register
            name: Optional name override (defaults to child.__class__.__name__.lower())
        """
        ...

    @abc.abstractmethod
    def _initmethods(self) -> None:
        """
        Initialize resource methods.

        Concrete resources implement method discovery logic.
        """
        ...

    @abc.abstractmethod
    def _initchildren(self) -> None:
        """
        Initialize child resources.

        Concrete resources implement child resource logic.
        """
        ...

    @abc.abstractmethod
    def _buildrequest(
        self,
        method: t.Union[str, HTTPMethod],
        path: t.Optional[str] = None,
        **kwargs: t.Any
    ) -> RequestModel:
        """
        Build request for resource method.

        Concrete resources implement request building logic.
        """
        ...

    ## concretes ##
    def _separatekwargs(self, method: HTTPMethod, **kwargs) -> tuple[dict, dict]:
        """Separate kwargs into request fields and body data based on HTTP method."""
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

    def _substitutepath(self, path: t.Optional[str] = None, **kwargs) -> tuple[t.Optional[str], t.List[str]]:
        """Substitute path parameters using string formatting."""
        if not path:
            return path, []

        import string
        formatter = string.Formatter()

        try:
            consumed = [fname for _, fname, _, _ in formatter.parse(path) if fname]
            return path.format(**kwargs), consumed
        except KeyError as e:
            raise ValueError(f"Missing path parameter: {e}")

    def _resolvepathargs(self, path: t.Optional[str] = None, *args, **kwargs) -> dict:
        """Extract positional args into kwargs based on path parameter names."""
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

    def _createboundmethod(self, method: t.Callable) -> t.Callable:
        methodconfig = getattr(method, '_methodconfig')

        def bound(*args, noexec: bool = False, **kwargs):
            # preprocess request data if configured
            if methodconfig.preprocess:
                kwargs = methodconfig.preprocess(kwargs)

            # extract args into kwargs based on path parameter order
            kwargs = self._resolvepathargs(methodconfig.path, *args, **kwargs)

            # substitute path params
            path, consumed = self._substitutepath(methodconfig.path, **(kwargs or {}))

            # remove consumed parameters
            for kwarg in consumed:
                kwargs.pop(kwarg, None)

            # build request
            request = self._buildrequest(
               method=methodconfig.method,
               path=path,
               **(kwargs or {})
            )

            if self._backend:
                request = self._backend.formatrequest(request, kwargs)


            response = self._client._engine.send(request, noexec=noexec)

            if isinstance(response, RequestModel):
                return response

            if self._backend:
                processed = self._backend.processresponse(response)
            else:
                processed = response

            if methodconfig.postprocess:
                processed = methodconfig.postprocess(processed)

            return processed

        bound.__name__ = method.__name__
        bound.__doc__ = method.__doc__
        setattr(bound, '_methodconfig', methodconfig)

        return bound

    def addmethod(self, method: t.Callable, name: t.Optional[str] = None) -> None:
        """Add method to resource."""
        self._registermethod(method, name)

    def removemethod(self, name: str) -> None:
        """Remove method from resource."""
        if name in self._methods:
            del self._methods[name]
            if hasattr(self, name):
                delattr(self, name)

    def getmethod(self, name: str) -> t.Optional[t.Callable]: # type: ignore
        """Get method by name."""
        return self._methods.get(name)

    def listmethods(self) -> t.List[str]:
        """List all registered method names."""
        return list(self._methods.keys())

    def addchild(self, child: 'BaseResource', name: t.Optional[str] = None) -> None:
        """Add child resource."""
        self._registerchild(child, name)

    def removechild(self, name: str) -> None:
        """Remove child resource."""
        if name in self._children:
            del self._children[name]
            if hasattr(self, name):
                delattr(self, name)

    def getchild(self, name: str) -> t.Optional['BaseResource']:
        """Get child resource by name."""
        return self._children.get(name)

    def listchildren(self) -> t.List[str]:
        """List all child resource names."""
        return list(self._children.keys())

   ## component access ##
    def getclient(self) -> 'BaseClient':
        """Get parent client."""
        return self._client

    def getconfig(self) -> ResourceConfig:
        """Get resource configuration."""
        return self._config

    def getsession(self) -> SessionProtocol:
        """Get session manager."""
        return self._session

    # no properties, Resources should be declarative

    ## operator overloads ##
    #! implement later
