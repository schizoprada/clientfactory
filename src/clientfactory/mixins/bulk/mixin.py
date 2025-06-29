# ~/clientfactory/src/clientfactory/mixins/bulk/mixin.py
"""
...
"""
from __future__ import annotations
import time, typing as t, threading as th
from concurrent.futures import ThreadPoolExecutor, as_completed as ascompleted


from clientfactory.core.models import (
    MethodConfig, RequestModel, ResponseModel, ExecutableRequest
)
from clientfactory.mixins.core.base import BaseMixin
from clientfactory.mixins.core.comps import MixinMetadata, ExecMode, IMMEDIATE
from clientfactory.mixins.bulk.comps import (
AggregationMode, RequestType, ErrorChecker,
BulkMode, EnumMember, ErrorHandler, RollbackHook,
ErrorHandlers,
CONFKEYS, ALL, SEQ, CONTINUE
)


class BulkMixin(BaseMixin):
    """..."""
    __mixmeta__ = MixinMetadata(
        mode=IMMEDIATE,
        priority=9,
        autoreset=True,
        confkeys=CONFKEYS
    )
    __chainedas__: str = 'batch' # bulk will be the direct method

    def __init__(
        self
    ) -> None:
        """..."""
        super().__init__()
        self._requests: t.List[RequestType] = []
        self._responses: t.Dict[str, ResponseModel] = {} # request identification: response
        self._errors: t.Dict[str, Exception] = {}

        ## configurations ##
        ### execution behavior ###
        self._onerror: ErrorHandler = CONTINUE
        self._bulkmode: BulkMode = SEQ
        self._aggrmode: AggregationMode = ALL

        ### response handling ###
        self._errorcheck: t.Optional[ErrorChecker] = None
        self._collectall: bool = True # collect both responses and errors

        ### performance ###
        self._execdelay: float = 0.0
        self._maxpool: int = 10 # parallel

        ### transaction ###
        self._shouldrollback: bool = False # on error
        self._rollbackhooks: t.List[RollbackHook] = []

        self._dependencies: t.Dict[str, t.List[str]] = {} # reqid -> [depid1, depid2, ...]
        self._completed: set[str] = set()

    def _getreqid(self, request: RequestType) -> str:
        """Generate consistent ID for request using hash"""
        return str(hash(request))

    def _collectresponses(self, request: RequestType, response: t.Optional[ResponseModel] = None, error: t.Optional[Exception] = None) -> None:
        """Collect response or error for a request"""
        reqid = self._getreqid(request)

        if response is not None:
            self._responses[reqid] = response

        if error is not None:
            self._errors[reqid] = error

    def _aggregateresponses(self, mode: AggregationMode = ALL, errorcheck: t.Optional[ErrorChecker] = None) -> t.Any:
        """Aggregate collected responses using specific mode"""
        responses = list(self._responses.values())
        return mode.aggregate(responses, errorcheck)

    def _clearcollected(self) -> None:
        """Clear collected responses and errors"""
        self._responses.clear()
        self._errors.clear()
        self._completed.clear()

    def _reset(self) -> None:
        """..."""
        self._clearcollected()
        self._requests.clear()
        self._dependencies.clear()

    def _errorhandle(self, request: RequestType, error: Exception) -> bool:
        """..."""
        if self._collectall:
            self._collectresponses(request=request, error=error)

        if callable(self._onerror):
            return self._onerror(error, request)
        elif isinstance(self._onerror, ErrorHandlers):
            if self._onerror.shouldraise():
                raise error
            elif self._onerror.shouldbreak():
                return False
            else:
                return True

        return True # default: continue

    def _rollback(self, trigger: Exception) -> None:
        """..."""
        if (not self._shouldrollback) or (not self._rollbackhooks):
            return

        successful = [r for r in self._responses.values() if r is not None]

        for hook in self._rollbackhooks:
            try:
                hook(successful, trigger)
            except Exception as rollerror:
                raise RuntimeError(f"Rollback Failed: {rollerror}") from rollerror


    def _canexec(self, request: RequestType) -> bool:
        """..."""
        reqid = self._getreqid(request)
        if (reqid not in self._dependencies):
            return True

        deps = self._dependencies[reqid]
        return all(dep in self._completed for dep in deps)

    def _execone(self, request: RequestType) -> tuple[t.Optional[ResponseModel], bool]:
        """Execute a single request and handle errors."""
        try:
            if isinstance(request, ExecutableRequest):
                response = request()
            else:
                engine = self._getengine()
                executable = request.toexecutable(engine=engine)
                response = executable()
            self._collectresponses(request, response=response)
            return response, True # continue
        except Exception as e:
            should = self._errorhandle(request, e)
            return None, should

    def _execseq(self) -> t.List[t.Optional[ResponseModel]]:
        """..."""
        responses: t.List[t.Optional[ResponseModel]] = ([None] * len(self._requests))
        remaining = list(enumerate(self._requests)) # (index, request)
        lasterror = None

        while remaining:
            anyexecuted = False

            for i, (index, request) in enumerate(remaining):
                if self._canexec(request):
                    if self._completed and self._execdelay > 0:
                        time.sleep(self._execdelay)

                    response, proceed = self._execone(request)
                    responses[index] = response

                    reqid = self._getreqid(request)
                    self._completed.add(reqid)

                    if response is None:
                        lasterror = self._errors.get(reqid)

                    remaining.pop(i)
                    anyexecuted = True

                    if not proceed:
                        if lasterror:
                            self._rollback(lasterror)
                        return responses
                    break # restart loop since we modified remaining

            if not anyexecuted:
                raise RuntimeError()

        if self._errors and lasterror:
            self._rollback(lasterror)

        return responses

    def _execpara(self) -> t.List[t.Optional[ResponseModel]]:
        """..."""
        #! dependencies not supported currently for parallel
        if self._dependencies:
            raise RuntimeError()
        if self._shouldrollback:
            raise RuntimeError()

        responses: t.List[t.Optional[ResponseModel]] = ([None] * len(self._requests))
        shouldbreak = th.Event()

        def indexexec(idxrq) -> tuple[int, t.Optional[ResponseModel], bool]:
            index, request = idxrq
            if shouldbreak.is_set():
                return index, None, False

            response, proceed = self._execone(request)
            if not proceed:
                shouldbreak.set()

            return index, response, proceed

        with ThreadPoolExecutor(max_workers=self._maxpool) as x:
            futures = [
                x.submit(indexexec, (i, req))
                for i, req in enumerate(self._requests)
            ]

            for future in ascompleted(futures):
                index, response, proceed = future.result()
                responses[index] = response

                if not proceed:
                    for f in futures:
                        f.cancel()
                    break


        return responses

    def _execall(self) -> t.List[t.Optional[ResponseModel]]:
        """Execute all requests sequentially"""
        match self._bulkmode:
            case BulkMode.SEQ:
                return self._execseq()
            case BulkMode.PARA:
                return self._execpara()
            case _:
                raise ValueError()

    def _convertenum(self, value: t.Union[str, EnumMember], enumeration: t.Type[EnumMember]) -> EnumMember:
        """Convert a value to a corresponding enumeration value"""
        if isinstance(value, enumeration):
            return value
        try:
            return enumeration(value.lower())
        except (ValueError, TypeError):
            try:
                return enumeration[value.upper()]
            except KeyError:
                raise ValueError(f"{value!r} is not a valid member of {enumeration.__name__}")

    def _configure_(self, **kwargs) -> t.Dict[str, t.Any]:
        """..."""
        return {k:v for k,v in kwargs.items() if k in CONFKEYS}

    def _exec_(self, conf: t.Dict[str, t.Any], **kwargs) -> t.Any:
        def withoptions(**options):
            #! need to implement logic to handle configs and such
            responses = self._execall()
            result = self._aggregateresponses(self._aggrmode, self._errorcheck) # should probably update to not need param pass

            if self.__mixmeta__.autoreset:
                self._clearcollected() # shouldnt we call _reset?

            return result

        options = {**conf, **kwargs}
        return withoptions(**options)



    ## configuration methods ##
    def onerror(self, handler: t.Union[str, ErrorHandler]) -> 'BulkMixin':
        if isinstance(handler, str):
            handler = self._convertenum(handler, ErrorHandlers)
        self._onerror = handler
        return self

    def mode(self, m: t.Union[str, BulkMode]) -> 'BulkMixin':
        """..."""
        if isinstance(m, str):
            m = self._convertenum(m, BulkMode)
        self._bulkmode = m
        return self

    def aggregate(self, mode: t.Union[str, AggregationMode]) -> 'BulkMixin':
        """..."""
        if isinstance(mode, str):
            mode = self._convertenum(mode, AggregationMode)
        self._aggrmode = mode
        return self

    def delay(self, seconds: float) -> 'BulkMixin':
        """..."""
        self._execdelay = seconds
        return self

    def errorcheck(self, checker: ErrorChecker) -> 'BulkMixin':
        """..."""
        self._errorcheck = checker
        return self

    def collectall(self, v: bool) -> 'BulkMixin':
        """..."""
        self._collectall = v
        return self

    def maxpool(self, v: int) -> 'BulkMixin':
        """..."""
        self._maxpool = v
        return self

    def rollback(self, should: t.Optional[bool] = None, *hooks: RollbackHook) -> 'BulkMixin':
        """..."""
        if should is None:
            if not hooks:
                should = False
            else:
                should = True

        self._shouldrollback = should
        self._rollbackhooks.extend(hooks)
        return self

    ## building ##
    def add(self, *requests: RequestType, dependson: t.Optional[t.List[RequestType]] = None) -> 'BulkMixin':
        """..."""
        dependson = (dependson or [])
        depids = [self._getreqid(dep) for dep in dependson]

        for request in requests:
            reqid = self._getreqid(request)
            self._requests.append(request)

            if depids:
                self._dependencies[reqid] = depids

        return self
