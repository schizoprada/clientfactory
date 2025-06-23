# ~/clientfactory/src/clientfactory/mixins/iteration/mixin.py
"""
Iteration Mixin
--------------
Mixin to add parameter iteration capabilities to bound methods.
"""
from __future__ import annotations
import enum, typing as t
from collections.abc import Iterator, Iterable

from pydantic import BaseModel as PydModel, field_validator as fieldvalidator

from clientfactory.core.models import Param, Payload, MethodConfig
from clientfactory.mixins.iteration.comps import (
    ErrorHandles, CycleModes, IterCycle, IterateCyclesType,
    PAGEPARAMS, OFFSETPARAMS, LIMITPARAMS, ITERCONFIGS
)


class IterMixin:
    """Mixin to add parameter iteration capabilities to bound methods."""

    def __init__(self, *args, **kwargs) -> None:
        """..."""
        super().__init__(*args, **kwargs)
        self._staticparams: dict = {}
        self._iterconfig: dict = {}

    def cycle(
        self,
        param: t.Union[str, Param],
        start: t.Optional[t.Any] = None,
        end: t.Optional[t.Any] = None,
        step: t.Optional[t.Any] = None,
        stepfilter: t.Optional[t.Callable[[t.Any], bool]] = None,
        values: t.Optional[t.Iterable] = None,
        onerror: ErrorHandles = ErrorHandles.CONTINUE,
        maxretries: int = 3,
        retrydelay: float = 1.0,
        errorcallback: t.Optional[t.Callable] = None,
        **kwargs
    ) -> IterCycle:
        """Create a reusable iteration cycle."""
        return IterCycle(
            param=param,
            start=start,
            end=end,
            step=step,
            stepfilter=stepfilter,
            values=values,
            onerror=onerror,
            maxretries=maxretries,
            retrydelay=retrydelay,
            errorcallback=errorcallback,
            **kwargs
        )

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
                    # TODO: extract param names from payload class
                    pass

        return params

    def _discoverparam(self) -> t.Union[str, Param]:
        """Discover default iteration parameter following priority rules."""
        candidates = self._collectiterables()

        # first priority: page/pagination
        for param in list(PAGEPARAMS):
            if param in candidates:
               return param # we're only returning a string right now too


        # second priority: offset/limit
        ## this one is tricky because we need to have both present to know for a fact its the "pagination" method for this API
        ### TBD.
        raise NotImplementedError()

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

    def _executecycles(self, primary: IterCycle, value: t.Any, cycles: IterateCyclesType, staticparams: dict) -> Iterator[t.Any]:
        """Execute all cycles for a single primary parameter value."""
        if not callable(self):
            raise TypeError(f"Object {type(self)} is not callable - cannot execute iteration")


        cyclelist = [cycles] if isinstance(cycles, IterCycle) else list(cycles)

        # sequential execution: complete each cycle before proceesing
        for cycle in cyclelist:
            for cvalue in cycle.generate():
                try:
                    callkwargs = {
                        **staticparams,
                        primary.parameter: value,
                        cycle.parameter: cvalue
                    }
                    result = self(**callkwargs)
                    yield result
                except Exception as e:
                    handle = self._errorhandle(cycle, e)
                    if handle is True:
                        continue
                    elif handle is False:
                        pass # retry logic to be implemented
                    elif callable(handle):
                        pass # callback logic to be implemented
                    # handle other handles

    def _iterate(self, primary: IterCycle, cycles: t.Optional[IterateCyclesType], cyclemode: CycleModes, **staticparams) -> Iterator[t.Any]:
        """Execute the iteration with cycles."""



        if cyclemode != CycleModes.SEQUENTIAL:
            raise NotImplementedError()

        if not callable(self):
            raise TypeError(f"Object {type(self)} is not callable - cannot execute iteration")

        # single parameter iteration
        for value in primary.generate():
            if cycles is None:
                try:
                    callkwargs = {**staticparams, primary.parameter: value}
                    result = self(**callkwargs)
                    yield result
                except Exception as e:
                    # handle based on error strategy
                    handle = self._errorhandle(primary, e)
                    if handle is True:
                        continue
                    elif handle is False:
                        pass # retry logic to be implemented
                    elif callable(handle):
                        pass # callback logic to be implemented
                    # ...
            else:
                yield from self._executecycles(primary, value, cycles, staticparams)

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

        # Separate iteration config from static method parameters
        iterconfig, staticparams = self._separatekwargs(static, **kwargs)

        # Merge instance static params with call-specific static params
        # Call-specific params take precedence over instance params
        staticparams = {**self._staticparams, **staticparams}

        primary = self.cycle(param, **iterconfig)

        return self._iterate(primary, cycles, cyclemode, **staticparams)


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


    def foreach(self, param: t.Union[str, Param], cycles: t.Optional[IterateCyclesType] = None, **kwargs) -> Iterator[t.Any]:
        """Alias for iterate for chaining readability."""
        return self.iterate(param, cycles=cycles, **kwargs)

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
