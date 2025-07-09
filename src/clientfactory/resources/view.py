# ~/clientfactory/src/clientfactory/resources/view.py
"""
...
"""
from __future__ import annotations
import typing as t

from clientfactory.core.models import (
    HTTPMethod, HTTP, RequestModel, ResponseModel,
    ResourceConfig, MergeMode, Payload, Param,
    BoundMethod, MethodConfig
)
from clientfactory.core.protos import BackendProtocol
from clientfactory.core.bases import BaseResource, BaseSession
from clientfactory.core.resource import Resource
if t.TYPE_CHECKING:
    from clientfactory.core.bases import BaseClient

class ViewResource(Resource):
    """
    Resource specialized for view operations.

    Provides automatic view method generation for retrieving single items.
    """
    __declaredas__: str = "viewresource"
    __declattrs__: set[str] = BaseResource.__declattrs__ | {
        'payload', 'viewmethod', 'viewpath', 'method',
        'headers', 'cookies', 'headermode', 'cookiemode',
        'timeout', 'retries', 'preprocess', 'postprocess'
    }
    __declconfs__: set[str] = BaseResource.__declconfs__ | {
        'method', 'headermode', 'cookiemode', 'timeout', 'retries'
    }

    def __init__(
        self,
        client: 'BaseClient',
        config: t.Optional[ResourceConfig] = None,
        session: t.Optional[BaseSession] = None,
        backend: t.Optional[BackendProtocol] = None,
        **kwargs: t.Any
    ) -> None:
        """..."""
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
        super()._resolveattributes(attributes)
        self.method: HTTPMethod = attributes.get('method', HTTP.GET) or HTTP.GET
        self.headers = attributes.get('headers')
        self.cookies = attributes.get('cookies')
        self.headermode = attributes.get('headermode', MergeMode.MERGE) or MergeMode.MERGE
        self.cookiemode = attributes.get('cookiemode', MergeMode.MERGE) or MergeMode.MERGE
        self.timeout = attributes.get('timeout')
        self.retries = attributes.get('retries')
        self.preprocess = attributes.get('preprocess')
        self.postprocess = attributes.get('postprocess')
        self.payload = attributes.get('payload')
        self.viewmethod = attributes.get('viewmethod', 'view') or 'view'
        self.viewpath = attributes.get('viewpath', '{id}') or '{id}'

    def _getpayloadinstance(self) -> t.Optional[Payload]:
        """Get the payload instance"""
        if self.payload is None:
            return None
        if isinstance(self.payload, type):
            return self.payload()
        return self.payload

    def _generateviewdocs(self) -> str:
        """Generate docstring for view method based on viewpath and payload"""
        if not self.payload:
            return f"View method for {self.name} resource"

        lines = [f"View {self.name} with validated parameters.", ""]

        pinstance = self._getpayloadinstance()

        if (pinstance is not None) and (hasattr(pinstance, '_fields')):
            lines.append(f"Parameters:")
            for name, field in pinstance._fields.items():
                required = " [required]" if field.required else ""
                default = f" (default: {field.default})" if (field.default is not None) else ""
                lines.append(f"    {name}{required}{default}")


        lines.extend(["", "Returns:", "    Processed response data or Response object"])
        return "\n".join(lines)

    def _generateviewmethod(self) -> None:
        """Generate the view method."""
        from clientfactory.core.utils.discover import createboundmethod

        methodconfig = MethodConfig(
            name=self.viewmethod,
            method=self.method,
            path=self.viewpath,
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

        def viewmethod(): pass # dummy
        viewmethod._methodconfig = methodconfig
        viewmethod.__name__ = self.viewmethod
        viewmethod.__doc__ = self._generateviewdocs()

        def validatepayload(kwargs):
            if self.payload is not None:
                pinstance = self._getpayloadinstance()
                if pinstance is not None:
                    result = pinstance.validate(kwargs)
                    return result
            return kwargs

        getengine = lambda p: p._client._engine
        getbackend = lambda p: p._backend
        baseurl = self.baseurl if self.baseurl is not None else self._client.baseurl

        bound = createboundmethod(
            method=viewmethod,
            parent=self,
            getengine=getengine,
            getbackend=getbackend,
            baseurl=baseurl,
            usesession=self._session,
            resourcepath=self.path,
            validationstep=validatepayload,
            pathoverride=self.viewpath
        )

        self._registermethod(bound, self.viewmethod)

    def _initmethods(self) -> None:
        super()._initmethods()

        if (self.viewmethod not in self._methods):
            self._generateviewmethod()
