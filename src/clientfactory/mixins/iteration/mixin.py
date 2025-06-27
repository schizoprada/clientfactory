# ~/clientfactory/src/clientfactory/mixins/iteration/mixin.py
"""
Iteration Mixin
--------------
Mixin to add parameter iteration capabilities to bound methods.
"""
from __future__ import annotations
import time, typing as t, itertools as it
from collections.abc import Iterator, Iterable


from clientfactory.core.models import Param, Payload, MethodConfig
from clientfactory.mixins.core import BaseMixin, MixinMetadata
from clientfactory.mixins.core.comps import DEFERRED
from clientfactory.mixins.iteration.comps import (
    ErrorHandles, CycleModes, ErrorCallback,
    IterCycle, IterateCyclesType, IterContext,
    CycleBreak, PAGEPARAMS, OFFSETPARAMS,
    LIMITPARAMS, ITERCONFIGS,
    ITERKEYS, EXECDEFAULTS
)

from clientfactory.logs import log


class IterMixin(BaseMixin):
    """Mixin to add parameter iteration capabilities to bound methods."""
    __mixmeta__ = MixinMetadata(
        mode = DEFERRED,
        priority = 5,
        confkeys = ITERCONFIGS
    )
    __chainedas__: str = 'iter'

    def _exec_(self, conf: t.Dict[str, t.Any], **kwargs) -> t.Any:
        """..."""
        final = {**conf, **kwargs}
        param, cycles, mode, static, store, breaks = [
            final.pop(key, default) for key, default in EXECDEFAULTS.items()
        ]
        return self.iterate(
            param=param,
            cycles=cycles,
            mode=mode,
            static=static,
            store=store,
            breaks=breaks,
            **final
        )

    def _configure_(self, **kwargs) -> t.Dict[str, t.Any]:
        """Testing Testing"""
        return {k:v for k,v in kwargs.items() if k in ITERKEYS}


    def __init__(self, *args, **kwargs) -> None:
        """..."""
        super().__init__(*args, **kwargs)
        self._staticparams: dict = {}
        self._iterconfig: dict = {}
        self._iterctx: IterContext = IterContext()

    ## Private Methods ##
    ### Data Handling ###
    def _extractiterconf(self, static: t.Optional[t.Dict[str, t.Any]], **kwargs) -> tuple[dict, dict]:
        """
        Separate iteration configuration from static method parameters.

        Uses multiple detection methods to resolve naming conflicts:
        1. Explicit `static` dict - parameters passed directly to each method call
        2. Underscore prefix (`_key`) - removes prefix only if `key` conflicts with iteration config
        3. Known iteration config keys - reserved for iteration configuration
        4. Everything else - defaults to static method parameters

        Args:
            static: Optional dict of explicit static parameters
            **kwargs: Mixed iteration config and static method parameters

        Returns:
            tuple: (iteration_config_dict, static_method_params_dict)

        Examples:
            # Underscore removes prefix for conflicts, keeps it otherwise
            _extractiterconf(start=1, _start=100, _custom=True)
            # Returns: ({'start': 1}, {'start': 100, '_custom': True})

            # Static dict combined with other methods
            _extractiterconf(static={'brand': 'nike'}, end=10, category='shoes')
            # Returns: ({'end': 10}, {'brand': 'nike', 'category': 'shoes'})
        """
        config = self._iterconfig.copy()
        static = static.copy() if static else {}

        for k, v in kwargs.items():
            if k.startswith('_'):
                key = k[1:]
                if key in ITERCONFIGS:
                    static[key] = v
                else:
                    static[k] = v # not namespace conflicted, dont remove leading underscore
            elif k in ITERCONFIGS:
                config[k] = v
            else:
                static[k] = v

        self._iterconfig.clear() # Clear instance iter config since we're using it
        return config, static

    def _extractpayloadparams(self, source: t.Union[Payload, t.Type[Payload]]) -> set[str]:
        """Extract parameter names from payload class/instance"""
        payload = source() if isinstance(source, type) else source
        if not isinstance(payload, Payload):
            raise TypeError(f"")

        return set(payload.paramnames())

    def _collectiterables(self) -> set[str]:
        """Collect all available parameters that could be iterated."""

        params = set()

        if hasattr(self, '_methodconfig'):
            methodconfig: t.Optional[MethodConfig] = getattr(self, '_methodconfig', None)
            if methodconfig is not None:

                #extract from path template
                if methodconfig.path:
                    pathparams = methodconfig.pathparams()
                    params.update(pathparams)

                # extract from payload if available
                if methodconfig.payload:
                    payloadparams = self._extractpayloadparams(methodconfig.payload)
                    params.update(payloadparams)

        return params

    def _discoverparam(self) -> str: # Return string since this is pre-normalization
        """Discover default iteration parameter following priority rules."""
        candidates = self._collectiterables()

        find = lambda REF: next((param for param in list(REF) if param in candidates), None)

        # first priority: page/pagination
        if (page:=find(PAGEPARAMS)):
            return page

        if (offset:=find(OFFSETPARAMS)):
            return offset

        #! TODO:
        # handle single-param paths for automatic discovery for convenience
        # e.g.
        """
        @get("{id}")
        def method: pass

        method.iterate(range(1, 11)) -- this should work, if theres no payload and the path only has one param
        """

        raise ValueError(f"No suitable iteration parameter found in candidates: {candidates} -- Explicitly declare param to iter.")

    def _findlimitvalue(self, offsetparam: str) -> t.Optional[int]:
        """Find corresponding limit parameter value for offset iteration"""
        candidates = self._collectiterables()
        find = lambda opts: next((param for param in list(LIMITPARAMS) if param in opts), None)

        if (static:=find(self._staticparams)):
            return self._staticparams[static]

        if (candid:=(find(candidates))):
            limitparam = self._resolveparam(candid)
            if limitparam and limitparam.default is not None:
                return limitparam.default

        return None

    def _findstepvalue(self, param: Param, step: t.Optional[t.Any]) -> t.Optional[t.Any]:
        """Auto-detect step value for offset/limit patterns."""
        if step is not None:
            return step

        if (param.name in OFFSETPARAMS):
            return self._findlimitvalue(param.name)

        return step

    def _resolveparam(self, name: str) -> t.Optional[Param]:
        """Resolve string parameter name to actual param object"""

        methodconfig: t.Optional[MethodConfig] = getattr(self, '_methodconfig', None)
        if not methodconfig:
            return None


        def frompath(n: str):
            """Resolve parameter from path template."""
            if methodconfig.path:
                pathparams = methodconfig.pathparams()
                if n in pathparams:
                    return Param(name=n, source=n, target=n)
            return None

        def frompayload(n: str):
            """Resolve parameter from payload."""
            if methodconfig.payload:
                payload = methodconfig.payload() if isinstance(methodconfig.payload, type) else methodconfig.payload
                if n in payload._fields:
                    result = payload._fields[n]
                    return result
            return None

        def getresolver():
            if ('.' in name):
                qualifier, paramname = name.split('.', 1)
                if qualifier == 'payload':
                    return lambda: frompayload(paramname)
                elif qualifier == 'path':
                    return lambda: frompath(paramname)
                else:
                    raise ValueError(f"Invalid qualifier '{qualifier}'. Use 'path' or 'payload' to specify iteration target.")
            return lambda: frompayload(name) if methodconfig.payload is not None else frompath(name)

        if (resolver:=getresolver()):
            result = resolver()
            return result

        return None

    def _normalizeparam(self, param: t.Union[str, Param]) -> Param:
        """Normalize parameter to Param object."""
        if isinstance(param, Param):
            return param

        if isinstance(param, str):
            if (obj:=self._resolveparam(param)):
                return obj

            # No fallback - if it cant be resolved, its invalid.
            raise ValueError(f"Parameter '{param}' not found in method payload or path template")

        raise TypeError(f"")

    def _resolvemapping(self, value: str, param: Param) -> t.Any:
        """Resolve string value via param mapping."""
        if not param.mapping:
            return None


        # strategy 1: direct key lookup
        if value in param.mapping:
            if param.keysaschoices:
                return value
            return param.mapping[value]


        # strategy 2: check if values can be choices
        if param.valuesaschoices and value in list(param.mapping.values()):
            return value

        # strategy 3: check if we have a mapper function
        if param.mapper:
            return param.mapper(value)

        # default None
        return None

    def _resolvecallable(self, call: t.Callable, param: Param) -> t.Any:
        """Resolve callable by evaluating against available values"""
        #! we're making certain assumptions about the nature of this callable that we'll have to check back in on
        matches = [v for v in param._availablevalues() if call(v)]

        if not matches:
            raise ValueError(f"Callable filter found no matching values for parameter '{param.name}'")

        # return first match for now, can sophisticate this later
        return matches[0]

    def _resolvevalue(self, value: t.Any, param: Param, target: str) -> t.Any:
        """Main value resolution dispatcher."""
        def valuestarget():
            available = param._availablevalues()
            listable = lambda v: isinstance(v, (range, set, frozenset)) or (hasattr(v, '__iter__') and hasattr(v, '__next__'))
            # case 1: literal 'all'
            if isinstance(value, str) and value.lower() == 'all':
                    return available

            # case 2: slice - subset of available
            if isinstance(value, slice):
                return available[value]

            # case 3: listable - convert to list
            if listable(value):
                return list(value)

            # case 4: dict - generator for truthy vals
            if isinstance(value, dict):
                return [k for k, v in value.items() if v]

            # case 5:
            if isinstance(value, (list, tuple)):
                return [self._resolvevalue(v, param, 'element') for v in value]

            return None # fallback to main resolution

        # if already a standard type, return as-is
        if value is None or isinstance(value, (int, float)):
            return value

        # check if target is 'values' and handle if so
        if target.lower() == 'values':
            resolved = valuestarget()
            if resolved is not None:
                return resolved

        # strategy 1: mapping resolution
        if isinstance(value, str):
            resolved = self._resolvemapping(value, param)
            if resolved is not None:
                return resolved

        # strategy 2: callable evaluation
        if callable(value):
            return self._resolvecallable(value, param)

        # strategy 3: recursive resolution
        if isinstance(value, (list, tuple)):
            return [self._resolvevalue(v, param, target) for v in value]

        # default to value as-is if we cant resolve and let IterCycle handle
        return value

    ### Control Flow ###
    def _errorhandle(self, origin: IterCycle, exc: Exception) -> t.Union[bool, t.Callable]:
        """
        Handle error during iteration.

        Returns:
            True: Continue to next iteration
            False: Retry current iteration
            Callable: Error Callback Function
            Raises: For STOP mode
        """
        match origin.onerror:
            case ErrorHandles.STOP:
                raise exc
            case ErrorHandles.CONTINUE:
                return True # continue to next
            case ErrorHandles.RETRY:
                return False # retry current iteration
            case ErrorHandles.CALLBACK:
                if origin.errorcallback:
                    return origin.errorcallback
                raise ValueError(f"") # raise an error if theres no callback to refer to
            case _:
               raise NotImplementedError()


    def _shouldbreak(self, breaks: t.List[CycleBreak], result: t.Any = None) -> bool:
        """Check if any break condition is met."""

        if not breaks:

            return False

        context = self._iterctx.todict()

        for i, condition in enumerate(breaks):
            should = condition.evaluate(context, result)

            if should:

                return True

        return False

    #### Executors ####
    def _executewithretry(self, call: t.Callable, cycle: IterCycle) -> t.Any:
        """Execute a call with retry logic."""
        tries = 0

        while (tries <= cycle.maxretries):
            try:
                result = call()

                self._iterctx.addresult(result)

                return result
            except Exception as e:

                self._iterctx.adderror(e)

                handle = self._errorhandle(cycle, e)
                if handle is True:
                    raise e
                elif (handle is False) and (tries < cycle.maxretries):
                    tries += 1
                    time.sleep(cycle.retrydelay)
                    continue
                elif callable(handle): # CALLBACK
                    shouldretry = handle(e, cycle)
                    if shouldretry and (tries < cycle.maxretries):
                        tries += 1
                        time.sleep(cycle.retrydelay)
                        continue
                    else:
                        raise e
                else:
                    raise e

    def _executewithbreaks(self, call: t.Callable, cycle: IterCycle, breaks: t.List[CycleBreak]) -> t.Tuple[t.Any, bool]:
        """
        Execute call with break condition checking.

        Returns:
            tuple: (result, should)
        """
        print(f"EXEC: Checking breaks BEFORE call")
        # check breaks BEFORE call for context-based conditions
        if self._shouldbreak(breaks, None):
            print(f"EXEC: BREAKING BEFORE CALL")
            return None, True

        try:
            print(f"EXEC: Making call...")
            result = self._executewithretry(call, cycle)
            print(f"EXEC: Call succeeded, result={result}")
            # check immediately after success
            print(f"EXEC: Checking breaks AFTER call with result={result}")
            if (should:=self._shouldbreak(breaks, result)):
                print(f"EXEC: Should={should}, result={result}")
                return result, True
            print(f"EXEC: Should={should}, result={result}")
            return result, False

        except Exception as e:
            # check breaks FIRST
            if self._shouldbreak(breaks, e):
                return None, True

            # do error handling
            handle = self._errorhandle(cycle, e)
            if handle is True:
                return None, False # continue
            else:
                raise # re-raise

    def _executecycles(self, primary: IterCycle, value: t.Any, cycles: IterateCyclesType, staticparams: dict, breaks: t.List[CycleBreak]) -> Iterator[t.Any]:
        """Execute all cycles for a single primary parameter value."""
        if not callable(self):
            raise TypeError(f"Object {type(self)} is not callable - cannot execute iteration")

        cyclelist = [cycles] if isinstance(cycles, IterCycle) else list(cycles)

        for cycle in cyclelist:
            for cvalue in cycle.generate():
                def call():
                    callkwargs = {
                        **staticparams,
                        primary.parameter: value,
                        cycle.parameter: cvalue
                    }
                    return self(**callkwargs)
                result, breakout = self._executewithbreaks(call, cycle, breaks)
                print(f"EXEC(Cycles): result={result}, breakout={breakout}")
                if result is not None:
                    print(f"EXEC(Cycles): yielding={result}")
                    yield result
                if breakout:
                    return

    #### Iteration Modes ####
    def _iterseq(self, primary: IterCycle, cycles: t.Optional[IterateCyclesType], breaks: t.List[CycleBreak], **staticparams) -> Iterator[t.Any]:
        """Execute SEQ iteration."""
        if not callable(self):
            raise TypeError(f"Object {type(self)} is not callable - cannot execute iteration")

        # single parameter iteration
        for value in primary.generate():
            if cycles is None:
                if self._shouldbreak(breaks):
                    return
                def call():
                    callkwargs = {**staticparams, primary.parameter: value}
                    return self(**callkwargs)
                result, breakout = self._executewithbreaks(call, primary, breaks)
                print(f"ITER(Seq): result={result}, breakout={breakout}")
                if result is not None:
                    print(f"ITER(Seq): yielding={result}")
                    yield result
                if breakout:
                    return
            else:
                try:
                    yield from self._executecycles(primary, value, cycles, staticparams, breaks)
                except Exception as e:
                    raise

    def _iterprod(self, primary: IterCycle, cycles: t.Optional[IterateCyclesType], breaks: t.List[CycleBreak], **staticparams) -> Iterator[t.Any]:
        """Execute PROD (cartesian product) iteration."""
        if not callable(self):
            raise TypeError(f"Object {type(self)} is not callable - cannot execute iteration")

        if cycles is None: # no cycles = no product, just iterate the primary as usual
            return self._iterseq(primary, cycles, breaks, **staticparams)

        # get list of cycles
        cyclelist = [cycles] if isinstance(cycles, IterCycle) else list(cycles)

        # generate all values
        primaryvals = list(primary.generate())
        cyclicvals = [list(cycle.generate()) for cycle in cyclelist]

        # cartesian product
        combos = it.product(primaryvals, *cyclicvals)
        for combo in combos:
            if self._shouldbreak(breaks):
                return
            pval = combo[0]
            cvals = combo[1:]

            def call():
                callkwargs = {**staticparams, primary.parameter: pval}
                for i, cycle in enumerate(cyclelist):
                    callkwargs[cycle.parameter] = cvals[i]
                return self(**callkwargs)

            result, breakout = self._executewithbreaks(call, primary, breaks)
            print(f"ITER(Prod): result={result}, breakout={breakout}")
            if result is not None:
                print(f"ITER(Prod): yielding={result}")
                yield result
            if breakout:
                return

    def _iterate(self, primary: IterCycle, cycles: t.Optional[IterateCyclesType], mode: CycleModes, breaks: t.Optional[t.List[CycleBreak]] = None, **staticparams) -> Iterator[t.Any]:
        """Execute the iteration with cycles."""
        if not callable(self):
            raise TypeError(f"Object {type(self)} is not callable - cannot execute iteration")

        breaks = (breaks or [])
        match mode:
            case CycleModes.SEQ:
                return self._iterseq(primary, cycles, breaks, **staticparams)
            case CycleModes.PROD:
                return self._iterprod(primary, cycles, breaks, **staticparams)
            case CycleModes.PARA:
                raise NotImplementedError()
            case _:
                raise ValueError(f"Invalid iteration mode '{mode.value if isinstance(mode, CycleModes) else mode}', options: {[m.value for m in CycleModes]}")

    ## Public Methods ##
    ### Core Methods ###
    def cycle(
        self,
        param: t.Union[str, Param],
        start: t.Optional[t.Any] = None,
        end: t.Optional[t.Any] = None,
        step: t.Optional[t.Any] = None,
        stepfilter: t.Optional[t.Callable[[t.Any], bool]] = None,
        values: t.Optional[t.Iterable] = None,
        onerror: ErrorHandles = ErrorHandles.CONTINUE,
        maxretries: int = 0,
        retrydelay: float = 1.0,
        errorcallback: t.Optional[ErrorCallback] = None,
        **kwargs
    ) -> IterCycle:
        """Create a reusable iteration cycle."""
        param = self._normalizeparam(param)
        return IterCycle(
            param=param,
            start=self._resolvevalue(start, param, 'start'),
            end=self._resolvevalue(end, param, 'end'),
            step=self._findstepvalue(param, step),
            stepfilter=stepfilter,
            values=self._resolvevalue(values, param, 'values'),
            onerror=onerror,
            maxretries=maxretries,
            retrydelay=retrydelay,
            errorcallback=errorcallback,
            **kwargs
        )



    def iterate(
        self,
        param: t.Optional[t.Union[str, Param]] = None,
        cycles: t.Optional[IterateCyclesType] = None,
        mode: CycleModes = CycleModes.SEQ,
        static: t.Optional[t.Dict[str, t.Any]] = None,
        store: bool = False,
        breaks: t.Optional[t.Iterable[CycleBreak]] = None,
        **kwargs
    ) -> Iterator[t.Any]:
        """Main iteration with optional cycles."""
        # reset context for each call
        self._iterctx.reset(storeresults=store)
        if param is None:
            param = self._discoverparam()

        param = self._normalizeparam(param)

        # Separate iteration config from static method parameters
        iterconfig, staticparams = self._extractiterconf(static, **kwargs)

        # Merge instance static params with call-specific static params
        # Call-specific params take precedence over instance params
        staticparams = {**self._staticparams, **staticparams}

        primary = self.cycle(param, **iterconfig)

        breaks = list(breaks) if breaks else []
        return self._iterate(primary, cycles, mode, breaks, **staticparams)

    ### Convenience Methods ###
    def foreach(self, param: t.Union[str, Param], cycles: t.Optional[IterateCyclesType] = None, **kwargs) -> Iterator[t.Any]:
        """Alias for iterate for chaining readability."""
        return self.iterate(param, cycles=cycles, **kwargs)

    ### Builder Methods ###
    def withparams(self, **params) -> 'IterMixin':
        """
        Add static parameters to this bound method.

        Args:
            **params: Static parameters to include in all future calls

        Returns:
            Self for method chaining

        Examples:
            method.withparams(category='shoes').iterate('page', start=1, end=10)
            method.withparams(format='json').withparams(include_meta=True)
        """
        self._staticparams.update(params)
        return self

    def range(self, start: t.Any, end: t.Any, step: t.Optional[t.Any] = None) -> 'IterMixin':
        self._iterconfig.update({'start': start, 'end': end, 'step': step})
        return self

    def values(self, values: t.Iterable) -> 'IterMixin':
        self._iterconfig['values'] = values
        return self

    def mode(self, cyclemode: CycleModes) -> 'IterMixin':
        self._iterconfig['cyclemode'] = cyclemode
        return self


    def __iter__(self, *args, **kwargs) -> Iterator[t.Any]:
        """Default iteration with optional parameters."""
        return self.iterate(*args, **kwargs)
