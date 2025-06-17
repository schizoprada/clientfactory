# ~/clientfactory/src/clientfactory/resources/search.py
"""
Search Resource Implementation
-----------------------------
Specialized resource for search operations with parameter validation.
"""
from __future__ import annotations
import typing as t

from clientfactory.core.resource import Resource
from clientfactory.core.protos import BackendProtocol
from clientfactory.core.bases import BaseResource, BaseSession
from clientfactory.core.models import (
    Payload, RequestModel, SearchResourceConfig,
    HTTPMethod
)

if t.TYPE_CHECKING:
    from clientfactory.core.bases import BaseClient


class SearchResource(Resource):
    """
    Resource specialized for search operations.

    Provides automatic search method generation with parameter validation
    through Payload integration.
    """
    __declaredas__: str = "searchresource"
    __declattrs__: set[str] = BaseResource.__declattrs__ | {'payload', 'searchmethod', 'oncall', 'method'}
    __declconfs__: set[str] = BaseResource.__declconfs__ | {'method'}


    def __init__(
        self,
        client: 'BaseClient',
        config: t.Optional[SearchResourceConfig] = None,
        session: t.Optional[BaseSession] = None,
        backend: t.Optional[BackendProtocol] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize search resource."""
        # 1. resolve components
        components = self._resolvecomponents(session=session, backend=backend)
        self._session: BaseSession = (components['session'] or client._engine._session)
        self._backend: t.Optional[BackendProtocol] = (components['backend'] or client._backend)

        # 2. resolve config
        self._config: SearchResourceConfig = self._resolveconfig(SearchResourceConfig, config, **kwargs) # type: ignore

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)

        self._client: 'BaseClient' = client
        self._methods: t.Dict[str, t.Callable] = {}
        self._children: t.Dict[str, 'BaseResource'] = {}

        # initialize resources
        self._initmethods()
        self._initchildren()

    def _generatedocstring(self) -> str:
        """Generate docstring for search method based on payload"""
        if not self.payload:
            return f"Search method for {self.name} resource"

        lines = [f"Search {self.name} with validated parameters.", ""]

        pinstance = self._getpayloadinstance()
        if (pinstance is not None) and (hasattr(pinstance, '_fields')):
            lines.append("Parameters:")
            for name, field in pinstance._fields.items():
                required = " [required]" if field.required else ""
                default = f" (default: {field.default})" if (field.default is not None) else ""
                lines.append(f"   {name}{required}{default}")

        lines.extend(["", "Returns:", "    Processed response data or Response object"])
        return "\n".join(lines)

    def _getpayloadinstance(self) -> t.Optional[Payload]:
        """Get the payload instance"""
        if self.payload is None:
            return None
        if isinstance(self.payload, type):
            return self.payload()
        return self.payload


    def _preparerequestdata(self, data: dict) -> dict:
        """Prepare validated data for request building"""
        def alreadyprepped(data: dict) -> bool:
            prepped = False
            if ('params' in data) or ('json' in data):
                if len(list(data.keys())) == 1: # top level key
                    prepped = True
            return prepped

        if alreadyprepped(data):
            return data

        if (self.method == HTTPMethod.GET):
            return {"params": data}
        return {"json": data}

    def _generatesearchmethod(self) -> None:
        """Generate the search method."""
        def searchmethod(*args, **kwargs) -> t.Any:
            # validate params thru payload if defined
            if self.payload is not None:
                pinstance = self._getpayloadinstance()
                if pinstance is not None:
                    validated = pinstance.validate(kwargs)
                else:
                    validated = kwargs
            else:
                validated = kwargs

            # substitute path parameters
            path = self._substitutepath(self.path, **kwargs)

            # build request
            reqkwargs = self._preparerequestdata(validated)
            request = self._buildrequest(method=self.method, path=path, **reqkwargs)

            # send thru session
            response = self._session.send(request)

            # process thru backend if available
            if self._backend:
                return self._backend.processresponse(response)
            return response

        # set method name and register
        searchmethod.__name__ = self.searchmethod
        searchmethod.__doc__ = self._generatedocstring()
        self._registermethod(searchmethod, self.searchmethod)
        # removed oncall logic

    def _resolveattributes(self, attributes: dict) -> None:
        super()._resolveattributes(attributes)
        self.payload = attributes.get('payload')
        self.method = attributes.get('method', HTTPMethod.GET)
        self.searchmethod = attributes.get('searchmethod', 'search')
        self.oncall = attributes.get('oncall', False)
        print(f"""
            DEBUG SearchResource._resolveattributes:
                self.payload = {self.payload}
                self.method = {self.method}
                self.searchmethod = {self.searchmethod}
                self.oncall = {self.oncall}
            """)

    def _initmethods(self) -> None:
        super()._initmethods()

        if (self.searchmethod not in self._methods):
            self._generatesearchmethod()


    def __call__(self, *args, **kwargs) -> t.Any:
        """Make instance callable if oncall is enabled."""
        if not self.oncall:
            raise TypeError(f"({self.__class__.__name__}) object is not callable")

        if (search:=getattr(self, self.searchmethod)):
            return search(*args, **kwargs)
        raise AttributeError(f"({self.__class__.__name__}) has no search method defined")
