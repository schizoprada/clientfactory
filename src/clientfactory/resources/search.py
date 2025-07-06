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
    HTTPMethod, MethodConfig, MergeMode
)
from clientfactory.core.models.methods import BoundMethod

from clientfactory.logs import log

if t.TYPE_CHECKING:
    from clientfactory.core.bases import BaseClient


class SearchResource(Resource):
    """
    Resource specialized for search operations.

    Provides automatic search method generation with parameter validation
    through Payload integration.
    """
    __declaredas__: str = "searchresource"
    __declattrs__: set[str] = BaseResource.__declattrs__ | {
        'payload', 'searchmethod', 'oncall', 'method',
        'headers', 'cookies', 'headermode', 'cookiemode',
        'timeout', 'retries', 'preprocess', 'postprocess'
    }
    __declconfs__: set[str] = BaseResource.__declconfs__ | {
        'method', 'headermode', 'cookiemode', 'timeout', 'retries'
    }


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

        log.info(f"""
            SearchResource.__init__
            -----------------------
            (param) session: {session}

            (components) session: {components['session']}

            (client-engine) session: {client._engine._session}

            (final) session: {self._session}

            (type) session: {type(self._session)}
            """)

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

    def _generatesearchdocs(self) -> str:
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


    def _generatesearchmethod(self) -> None:
        """Generate the search method."""
        from clientfactory.core.utils.discover import createboundmethod

        # create a method config
        methodconfig = MethodConfig(
            name=self.searchmethod,
            method=self.method,
            path=self.path,
            payload=self._getpayloadinstance(),
            headers=self.headers,
            cookies=self.cookies,
            headermode=self.headermode,
            cookiemode=self.cookiemode,
            timeout=self.timeout,
            retries=self.retries,
            preprocess=self.preprocess,
            postprocess=self.postprocess
        )

        def searchmethod(): pass # dummy
        searchmethod._methodconfig = methodconfig # type: ignore
        searchmethod.__name__ = self.searchmethod
        searchmethod.__doc__ = self._generatesearchdocs()

        def validatepayload(kwargs):
            if self.payload is not None:
                pinstance = self._getpayloadinstance()
                if pinstance is not None:
                    result =  pinstance.validate(kwargs)
                    return result
            return kwargs

        getengine = lambda p: p._client._engine
        getbackend = lambda p: p._backend
        baseurl = self.baseurl if self.baseurl is not None else self._client.baseurl

        bound = createboundmethod(
            method=searchmethod,
            parent=self,
            getengine=getengine,
            getbackend=getbackend,
            baseurl=baseurl,
            usesession=self._session,
            resourcepath=self.path,
            validationstep=validatepayload,
            pathoverride=""
        )

        self._registermethod(bound, self.searchmethod)


    def _resolveattributes(self, attributes: dict) -> None:
        super()._resolveattributes(attributes)
        self.payload = attributes.get('payload')
        self.method = attributes.get('method', HTTPMethod.POST)
        self.searchmethod = attributes.get('searchmethod', 'search')
        self.oncall = attributes.get('oncall', False)
        # method config attributes
        self.headers = attributes.get('headers')
        self.cookies = attributes.get('cookies')
        self.headermode = attributes.get('headermode', MergeMode.MERGE) or MergeMode.MERGE
        self.cookiemode = attributes.get('cookiemode', MergeMode.MERGE) or MergeMode.MERGE
        self.timeout = attributes.get('timeout')
        self.retries = attributes.get('retries')
        self.preprocess = attributes.get('preprocess')
        self.postprocess = attributes.get('postprocess')

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
