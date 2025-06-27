# ~/clientfactory/src/clientfactory/mixins/iteration/comps.py
"""
"""
from __future__ import annotations
import enum, typing as t
from collections.abc import Iterator, Iterable

from pydantic import (
    BaseModel as PydModel,
    field_validator as fieldvalidator,
    computed_field as computedfield,
    Field)

from clientfactory.core.models import Param, Payload, MethodConfig
from clientfactory.core.bases.condition import ContextualCondition


## type hints ##
ErrorCallback = t.Callable[[Exception, 'IterCycle'], bool]

IterateCyclesType = t.Union['IterCycle', t.Tuple['IterCycle', ...], t.List['IterCycle']] # should expand probably

## enums ##

class ErrorHandles(str, enum.Enum):
    CONTINUE = "continue"
    STOP = "stop"
    RETRY = "retry"
    CALLBACK = "callback"

class CycleModes(str, enum.Enum):
    SEQ = "sequential"
    PROD = "nested" # cartesian product
    PARA = "parallel" # future: concurrent
    # define more...

## core ##

class CycleBreak(ContextualCondition):
    """"""
    def __init__(
        self,
        evalfunc: t.Callable[[dict, t.Any], bool],
        name: t.Optional[str] = None,
        description: str = "",
        **kwargs
    ) -> None:
        """"""
        self.evalfunc = evalfunc
        self.name = (name or self.__class__.__name__)
        self.description = description
        self._kwargs = kwargs

    def __repr__(self) -> str:
        return f"CycleBreak[{self.name}]({self.description or 'custom condition'})"

    def evaluate(self, context: dict, result: t.Any = None, *args, **kwargs) -> bool:
        should = self.evalfunc(context, result)
        return should

    @classmethod
    def ConsecutiveErrors(cls, max: int) -> 'CycleBreak':
        """
        Create break condition for consecutive error limit.

        Args:
            max: Maximum number of consecutive errors before breaking

        Returns:
            CycleBreak: Condition that breaks after consecutive error threshold
        """
        def check(context: dict, result: t.Any) -> bool:
            return context.get('errors', {}).get('consecutive', 0) >= max #! revise

        return cls(check, 'ConsecutiveErrors', f"Break after {max} consecutive errors")

    @classmethod
    def When(cls, predicate: t.Callable[[t.Any], bool], description: str = "") -> 'CycleBreak':
        """
        Create break condition based on result predicate.

        Args:
            predicate: Function that takes result and returns bool
            description: Optional description of the condition

        Returns:
            CycleBreak: Condition that breaks when predicate returns True
        """
        def check(context: dict, result: t.Any) -> bool:
            return predicate(result) if result is not None else False #! revise

        desc = (description or "Break when predicate satisfied")
        return cls(check, 'When', desc)

    @classmethod
    def Callback(cls, call: t.Callable[[dict, t.Any], bool], description: str = "") -> 'CycleBreak':
        """
        Create break condition with custom callback logic.

        Args:
            call: Custom function taking (context, result) returning bool
            description: Optional description of the condition

        Returns:
            CycleBreak: Condition using custom callback logic
        """
        desc = (description or "Break with custom callback")
        return cls(call, 'Callback', desc)

    @classmethod
    def StatusCode(cls, predicate: t.Callable[[int], bool], description: str = "") -> 'CycleBreak':
        def check(context: dict, result: t.Any) -> bool:
            code = getattr(result, 'statuscode', getattr(result, 'status_code', None)) # safety check 'status_code' just in case
            if code is not None:
                return predicate(code)
            return False
        desc = (description or "Break on status code condition")
        return cls(check, desc)

    @classmethod
    def BadRequest(cls) -> 'CycleBreak':
        notok = lambda status: status < 200 or status >= 300
        description = ""
        return cls.StatusCode(notok, description)

    # should make one for consecutive bad requests

class ErrorContext(PydModel):
    history: list = Field(default_factory=list)
    consecutive: int = 0

    def adderror(self, error: t.Union[str, Exception], increment: bool = False) -> None:
        self.history.append(error)
        if increment:
            self.consecutive += 1

    def increment(self, n: int = 1) -> None:
        if n < 1:
            return
        self.consecutive += n

    def clearcount(self) -> None:
        self.consecutive = 0

    @computedfield
    def total(self) -> int:
        return len(self.history)

    def todict(self) -> dict:
        return self.model_dump()

    def reset(self) -> None:
        """Reset all values"""
        self.history.clear()
        self.clearcount()

class IterContext(PydModel):
    errors: ErrorContext = Field(default_factory=ErrorContext)
    results: t.List = Field(default_factory=list)
    iterations: int = 0
    storeresults: bool = False # opt in

    def addresult(self, result: t.Optional[t.Any] = None) -> None:
        """Add successful result and clear consecutive errors."""
        if self.storeresults and result:
            self.results.append(result)
        else:
            self.results.append(True) # placeholder
        self.iterations += 1
        self.errors.clearcount() # success means break in consecutive

    def adderror(self, error: t.Union[str, Exception]) -> None:
        """Add error and increment counts."""
        self.errors.adderror(error, increment=True)

    def todict(self) -> dict:
        return self.model_dump()

    def reset(self, storeresults: bool = False) -> None:
        """Reset all values"""
        self.errors.reset()
        self.results.clear()
        self.iterations = 0
        self.storeresults = storeresults


class IterCycle(PydModel):
    """A reusable iteration cycle configuration."""
    param: Param
    start: t.Optional[t.Any] = None
    end: t.Optional[t.Any] = None
    step: t.Optional[t.Any] = None
    stepfilter: t.Optional[t.Callable[[t.Any], bool]] = None
    values: t.Optional[t.Union[t.List[t.Any], t.Tuple[t.Any, ...]]] = None
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

    def _infervalues(self) -> t.Optional[t.List]:
        """Infer iteration values from Param metadata."""
        if self.param.mapping:
            if self.param.valuesaschoices:
                return list(self.param.mapping.values())
            elif self.param.keysaschoices:
                return list(self.param.mapping.keys())
            else:
                return list(self.param.mapping.values())

        if self.param.choices:
            return list(self.param.choices)

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


## consts ##

PAGEPARAMS: set[str]  = {'page', 'pagenum', 'pagenumber', 'pageno', 'pagination', 'p'} # expand potentially
OFFSETPARAMS: set[str] = {'offset', 'start', 'skip'} # expand potentially
LIMITPARAMS: set[str] = {'limit', 'count', 'size', 'take'} # expand potentially
ITERCONFIGS: set[str] = {
    'start', 'end', 'step', 'stepfilter','values', 'onerror', 'maxretries',
    'retrydelay', 'errorcallback', 'cycles', 'cyclemode'
}


ITERKEYS: set[str] = PAGEPARAMS | OFFSETPARAMS | LIMITPARAMS | ITERCONFIGS | {'breaks', 'param', 'cycles', 'mode', 'static', 'store'}


EXECDEFAULTS: dict[str, t.Any] = {
    'param': None,
    'cycles': None,
    'mode': CycleModes.SEQ,
    'static': None,
    'store': False,
    'breaks': None
}
