# ~/clientfactory/src/clientfactory/core/models/methods.py
"""
...
"""
from __future__ import annotations
import typing as t

from clientfactory.core.utils.typed import UNSET
from clientfactory.core.models.config import MethodConfig
from clientfactory.core.protos import BoundMethodProtocol
from clientfactory.mixins import IterMixin, PrepMixin
from clientfactory.mixins.core import Mixer

if t.TYPE_CHECKING:
    from clientfactory.core.bases.client import BaseClient
    from clientfactory.core.bases.resource import BaseResource


BoundParentType = t.Union[
    'BaseClient',
    'BaseResource',
    t.Type['BaseClient'],
    t.Type['BaseResource']
]

T = t.TypeVar('T')

class BoundMethod(IterMixin, PrepMixin):
    """A bound method that can accept mixins for enhanced functionality"""

    def __init__(
        self,
        func: t.Callable,
        parent: BoundParentType = UNSET,
        config: MethodConfig = UNSET,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._func: t.Callable = func
        self._parent: BoundParentType = parent
        self._config: MethodConfig = config
        self._resolved: bool = (parent is not UNSET) and (config is not UNSET)

        self._cloneattributes()

    @t.overload
    def __get__(self, obj: None, objtype: t.Type[T]) -> t.Self: ...

    @t.overload
    def __get__(self, obj: T, objtype: t.Type[T]) -> t.Self: ...

    def __get__(self, obj: t.Optional[T], objtype: t.Optional[t.Type[T]] = None) -> t.Self:
        """Descriptor protocol - return self when accessed as attribute."""
        return self


    def _cloneattributes(self) -> None:
        """Copy appropriate attributes from original function to this bound method."""
        self.__name__ = self._func.__name__
        self.__doc__ = self._func.__doc__

    def _resolvebinding(self, parent: BoundParentType, config: t.Optional[MethodConfig] = None) -> None:
        """Resolve UNSET parent and config during class initialization."""
        if not self._resolved:
            self._parent = parent
            if config is not None:
                self._config = config
            self._resolved = True
            self._cloneattributes()

    @staticmethod
    def _requireresolution(func: t.Callable) -> t.Callable:
        """Decorator ensuring method is resolved before execution."""
        def decorator(self, *args, **kwargs):
            if (not getattr(self, '_resolved', False)) or (self._parent is UNSET):
                raise RuntimeError(f"BoundMethod '{self.__name__}' not resolved - parent is UNSET")
            return func(self, *args, **kwargs)
        return decorator

    @_requireresolution
    def __call__(self, *args, **kwargs) -> t.Any:
        """Call the function this method is bound to."""
        return self._func(*args, **kwargs)

    @_requireresolution
    def __repr__(self) -> str:
        """String representation of bound method."""
        return f"<BoundMethod({self.__name__})::{self._parent.__class__.__name__}>"


    @property
    def _methodconfig(self) -> MethodConfig:
        """Backwards compatibility"""
        return self._config

    @property
    def chain(self) -> Mixer:
        """..."""
        return Mixer(self)
