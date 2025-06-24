# ~/clientfactory/src/clientfactory/mixins/iteration/comps.py
"""
"""
from __future__ import annotations
import enum, typing as t
from collections.abc import Iterator, Iterable

from pydantic import BaseModel as PydModel, field_validator as fieldvalidator

from clientfactory.core.models import Param, Payload, MethodConfig



class ErrorHandles(str, enum.Enum):
    CONTINUE = "continue"
    STOP = "stop"
    RETRY = "retry"
    CALLBACK = "callback"

class CycleModes(str, enum.Enum):
    SEQUENTIAL = "sequential"
    NESTED = "nested" # cartesian product
    PARALLEL = "parallel" # future: concurrent
    # define more...

ErrorCallback = t.Callable[[Exception, 'IterCycle'], bool]

class IterCycle(PydModel):
    """A reusable iteration cycle configuration."""
    param: Param
    start: t.Optional[t.Any] = None
    end: t.Optional[t.Any] = None
    step: t.Optional[t.Any] = None
    stepfilter: t.Optional[t.Callable[[t.Any], bool]] = None
    values: t.Optional[t.Iterable] = None
    onerror: ErrorHandles = ErrorHandles.CONTINUE
    maxretries: int = 3
    retrydelay: float = 1.0
    errorcallback: t.Optional[ErrorCallback] = None

    ## pydantic model configs ##
    model_config = {
        "arbitrary_types_allowed": True
    }

    @fieldvalidator('onerror')
    @classmethod
    def _validateonerror(cls, v: t.Any) -> ErrorHandles:
        try:
            return ErrorHandles(v)
        except:
            import warnings
            warnings.warn(f"")
            return ErrorHandles.CONTINUE

    @fieldvalidator('stepfilter')
    @classmethod
    def _validatestepfilter(cls, v: t.Any) -> t.Optional[t.Callable]:
        if v is None:
            return v

        if not callable(v):
            raise ValueError("stepfilter must be callable")

        try:
            result = v("test")
            if not isinstance(result, bool):
                raise ValueError(f"stepfilter function must return bool, got {type(result)}")
        except TypeError:
            # Function might require specific types, can't validate at model creation
            import warnings
            warnings.warn("Could not validate stepfilter signature - will validate at runtime")
        except Exception as e:
            raise ValueError(f"stepfilter validation failed: {e}")

        return v

    @property
    def parameter(self) -> str:
        """Get the name of the parameter being cycled."""
        return self.param.name

    def _infervalues(self) -> t.Optional[t.Iterable]:
        """Infer iteration values from Param metadata."""
        if self.param.mapping:
            if self.param.valuesaschoices:
                return self.param.mapping.values()
            elif self.param.keysaschoices:
                return self.param.mapping.keys()
            else:
                return self.param.mapping.values()

        if self.param.choices:
            return self.param.choices

        return None

    def _generatenumeric(self) -> Iterator[t.Any]:
        """..."""
        start = self.start
        end = self.end
        step = (self.step or 1)


        # both start and end provided
        if (start is not None) and (end is not None):
            current = start
            while (current <= end):
                yield current
                current += step
            return

        # only start provided - infinite iterator (until break condition)
        if (start is not None):
            current = start
            while True:
                yield current
                current += step
            return

        # only end provided - start from 0
        if (end is not None):
            current = 0
            while (current <= end):
                yield current
                current += step
            return

        raise ValueError(f"Numeric generation requires at least a 'start' or 'end'")


    def _ensurereusable(self) -> None:
        """Convert self.values to list to ensure re-usability"""
        if (
            self.values is not None and
            hasattr(self.values, '__iter__') and
            not isinstance(self.values, (list, tuple, str))
        ):
            self.values = list(self.values)

    def _generatefromvalues(self) -> Iterator[t.Any]:
        """Generate from explicit values as iterable."""
        if self.values is  None:
            raise ValueError(f"Cannot generate from values: NoneType")

        self._ensurereusable()

        def applyfilter(value: t.Any) -> bool:
            if self.stepfilter:
                result = self.stepfilter(value)
                if not isinstance(result, bool):
                    raise TypeError(f"stepfilter must return bool, got {type(result)} for value {value}")
                return result
            return True

        filtered = (v for v in self.values if applyfilter(v))

        if isinstance(self.step, int) and (self.step > 1):
            for i, value in enumerate(filtered):
                if (i % self.step == 0):
                    yield value
        else:
            yield from filtered



    def generate(self) -> Iterator[t.Any]:
        """Generate iteration values for this cycle."""
        if self.values is not None:

            yield from self._generatefromvalues()
            return

        inferred = self._infervalues()
        if inferred is not None:
            self.values = inferred
            yield from self._generatefromvalues()
            return

        if (self.start is not None) and (self.end is not None):
            yield from self._generatenumeric()
            return

        raise ValueError(f"Cycle({self.parameter}) requires either 'values' or 'start/end'")


IterateCyclesType = t.Union[IterCycle, t.Tuple[IterCycle, ...], t.List[IterCycle]] # should expand probably

PAGEPARAMS: set[str]  = {'page', 'pagenum', 'pagenumber', 'pageno', 'pagination', 'p'} # expand potentially
OFFSETPARAMS: set[str] = {'offset', 'start', 'skip'} # expand potentially
LIMITPARAMS: set[str] = {'limit', 'count', 'size', 'take'} # expand potentially
ITERCONFIGS: set[str] = {
    'start', 'end', 'step', 'stepfilter','values', 'onerror', 'maxretries',
    'retrydelay', 'errorcallback', 'cycles', 'cyclemode'
}
