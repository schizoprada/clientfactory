# ~/clientfactory/src/clientfactory/mixins/bulk/comps.py
"""
...
"""
from __future__ import annotations
import enum, typing as t

if t.TYPE_CHECKING:
    from clientfactory.core.models import ResponseModel, RequestModel, ExecutableRequest


RequestType = t.Union['RequestModel', 'ExecutableRequest']
ErrorChecker = t.Callable[['ResponseModel'], bool]
EnumMember = t.TypeVar('EnumMember', bound=enum.Enum)

ErrorHandler = t.Union[
    'ErrorHandlers',
    t.Callable[[Exception, RequestType], bool]
]

RollbackHook = t.Callable[[t.List[ResponseModel], Exception], bool]

CONFKEYS: set[str] = {
    # execution behavior
    'onerror', 'mode', 'bulkmode', 'aggregate', 'aggregation', 'aggrmode',

    # response handling
    'errorcheck', 'collectall',

    # performance
    'delay', 'execdelay', 'maxpool',

    # transaction
    'rollback', 'shouldrollback', 'rollhook', 'rollbackhooks',

    # request building
    'requests', 'dependson', 'dependencies'
}

class BulkMode(str, enum.Enum):
    SEQ = "sequential"
    PARA = "parallel"

SEQ = BulkMode.SEQ
PARA = BulkMode.PARA

class AggregationMode(str, enum.Enum):
    ALL = "all"
    LAST = "last"
    FIRST = "first"
    SUCCESS = "success"
    FAILURE = "failure"
    COUNT = "count"

    def aggregate(self, responses: t.List['ResponseModel'], errorcheck: t.Optional[ErrorChecker] = None) -> t.Any:
        """..."""
        responses = (responses or [])
        checkerror = lambda r: not r.ok
        errorcheck = (errorcheck or checkerror)
        match self.value:
            case "all":
                return responses
            case "last":
                return responses[-1]
            case "first":
                return responses[0]
            case "success":
                return [r for r in responses if not errorcheck(r)]
            case "failure":
                return [r for r in responses if errorcheck(r)]
            case "count":
                return len(responses)
            case _:
                raise ValueError() # should not be reachable

ALL = AggregationMode.ALL
LAST = AggregationMode.LAST
FIRST = AggregationMode.FIRST
SUCCESS = AggregationMode.SUCCESS
FAILURE = AggregationMode.FAILURE
COUNT = AggregationMode.COUNT


class ErrorHandlers(str, enum.Enum):
    RAISE = "raise"
    BREAK = "break"
    CONTINUE = "continue"

    def shouldraise(self) -> bool:
        return self.value == "raise"

    def shouldbreak(self) -> bool:
        return self.value == "break"

    def shouldcontinue(self) -> bool:
        return self.value == "continue"

RAISE = ErrorHandlers.RAISE
BREAK = ErrorHandlers.BREAK
CONTINUE = ErrorHandlers.CONTINUE
