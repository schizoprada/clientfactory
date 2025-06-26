# ~/clientfactory/src/clientfactory/core/models/methods.py
"""
...
"""
from __future__ import annotations
import typing as t


from clientfactory.core.models.config import MethodConfig
from clientfactory.core.protos import BoundMethodProtocol
from clientfactory.mixins import IterMixin, PrepMixin

if t.TYPE_CHECKING:
    from clientfactory.core.bases.client import BaseClient
    from clientfactory.core.bases.resource import BaseResource


BoundParentType = t.Union[
    'BaseClient',
    'BaseResource',
    t.Type['BaseClient'],
    t.Type['BaseResource']
]


class BoundMethod(IterMixin, PrepMixin):
    """A bound method that can accept mixins for enhanced functionality"""

    def __init__(
        self,
        func: t.Callable,
        parent: BoundParentType,
        config: MethodConfig,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._func: t.Callable = func
        self._parent: BoundParentType = parent
        self._config: MethodConfig = config
        self._cloneattributes()

    @property
    def _methodconfig(self) -> MethodConfig:
        """Backwards compatibility"""
        return self._config

    def _cloneattributes(self) -> None:
        """Copy appropriate attributes from original function to this bound method."""
        self.__name__ = self._func.__name__
        self.__doc__ = self._func.__doc__

    def __call__(self, *args, **kwargs) -> t.Any:
        """Call the function this method is bound to."""
        return self._func(*args, **kwargs)

    def __repr__(self) -> str:
        """String representation of bound method."""
        return f"<BoundMethod({self.__name__})::{self._parent.__class__.__name__}>"
