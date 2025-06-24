# ~/clientfactory/src/clientfactory/mixins/iteration/mixin.py
"""
Iteration Mixin
--------------
Mixin to add parameter iteration capabilities to bound methods.
"""
from __future__ import annotations
import time, typing as t
from collections.abc import Iterator, Iterable


from clientfactory.core.models import Param, Payload, MethodConfig
from clientfactory.mixins.iteration.comps import (
    ErrorHandles, CycleModes, ErrorCallback,
    IterCycle, IterateCyclesType,
    PAGEPARAMS, OFFSETPARAMS, LIMITPARAMS, ITERCONFIGS
)

from clientfactory.logs import log

class IterMixin:
    """Mixin to add parameter iteration capabilities to bound methods."""

    def __init__(self, *args, **kwargs) -> None:
        """..."""
        super().__init__(*args, **kwargs)
        self._staticparams: dict = {}
        self._iterconfig: dict = {}

    ## Private Methods ##
    ### Data Handling ###
    def _separatekwargs(self, static: t.Optional[t.Dict[str, t.Any]], **kwargs) -> tuple[dict, dict]:
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
            _separatekwargs(start=1, _start=100, _custom=True)
            # Returns: ({'start': 1}, {'start': 100, '_custom': True})

            # Static dict combined with other methods
            _separatekwargs(static={'brand': 'nike'}, end=10, category='shoes')
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
            return lambda: frompayload(name)

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

    def _executewithretry(self, call: t.Callable, cycle: IterCycle) -> t.Any:
        """Execute a call with retry logic."""
        tries = 0

        while (tries <= cycle.maxretries):
            try:
                result = call()
                return result
            except Exception as e:
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

    def _executecycles(self, primary: IterCycle, value: t.Any, cycles: IterateCyclesType, staticparams: dict) -> Iterator[t.Any]:
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
                try:
                    result = self._executewithretry(call, cycle)
                    yield result
                except Exception as e:
                    handle = self._errorhandle(cycle, e)
                    if handle is True:
                        continue
                    else:
                        raise

    def _iterate(self, primary: IterCycle, cycles: t.Optional[IterateCyclesType], cyclemode: CycleModes, **staticparams) -> Iterator[t.Any]:
        """Execute the iteration with cycles."""
        if cyclemode != CycleModes.SEQUENTIAL:
            raise NotImplementedError()

        if not callable(self):
            raise TypeError(f"Object {type(self)} is not callable - cannot execute iteration")

        # single parameter iteration
        for value in primary.generate():
            if cycles is None:
                def call():
                    callkwargs = {**staticparams, primary.parameter: value}
                    return self(**callkwargs)
                try:
                    result = self._executewithretry(call, primary)
                    yield result
                except Exception as e:
                    # handle based on error strategy
                    handle = self._errorhandle(primary, e)
                    if handle is True:
                        continue
                    else:
                        raise e # Re-raise for STOP, RETRY, CALLBACK (already handled in retry logic)
                    # all other cases handled by retry logic
            else:
                try:
                    yield from self._executecycles(primary, value, cycles, staticparams)
                except Exception as e:
                    raise

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
        cyclemode: CycleModes = CycleModes.SEQUENTIAL,
        static: t.Optional[t.Dict[str, t.Any]] = None,
        **kwargs
    ) -> Iterator[t.Any]:
        """Main iteration with optional cycles."""
        if param is None:
            param = self._discoverparam()

        param = self._normalizeparam(param)

        # Separate iteration config from static method parameters
        iterconfig, staticparams = self._separatekwargs(static, **kwargs)

        # Merge instance static params with call-specific static params
        # Call-specific params take precedence over instance params
        staticparams = {**self._staticparams, **staticparams}

        primary = self.cycle(param, **iterconfig)

        return self._iterate(primary, cycles, cyclemode, **staticparams)

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
