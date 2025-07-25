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

    def _resolvebinding(
        self,
        parent: BoundParentType,
        config: t.Optional[MethodConfig] = None
    ) -> None:
        """Resolve UNSET parent and config during class initialization."""
        if not self._resolved:
            self._parent = parent
            if config is not None:
                self._config = config
            self._resolved = True
            self._cloneattributes()

    def _autodetectparent(self) -> t.Optional[t.Any]:
        """
        Auto-detect parent resource/client from call stack context.

        Returns the 'self' object if called from within a resource method,
        None otherwise.
        """
        import inspect
        from clientfactory.logs import log

        frame = inspect.currentframe()
        if frame:
            try:
                # look back thru frames to find resource/client context
                current = frame.f_back
                fcount = 0
                while current:
                    fcount += 1
                    callerlocals = current.f_locals
                    callerself = callerlocals.get('self')
                    log.info(f"[BoundMethod._autodetectparent](Frame {fcount}) self: {type(callerself) if callerself else None}")
                    # check if its a resource or client context
                    if callerself and (
                        hasattr(callerself, '_client') or # Resource
                        hasattr(callerself, '_resources') # Client
                    ):
                        log.info(f"[BoundMethod._autodetectparent](Frame {fcount}) found parent: {callerself}({type(callerself)})")
                        return callerself

                    current = current.f_back

            except Exception as e:
                # logging just for testing
                from clientfactory.logs import log
                log.error(f"[BoundMethod] Exception finding parent: {e!r}")
                pass # fail silently
            finally:
                if frame:
                    del frame

        return None

    def _recreate(self, parent: BoundParentType) -> 'BoundMethod':
        """
        Create a properly constructed BoundMethod instance with full request pipeline.

        Used for nested decorators that need complete reconstruction.
        """
        from clientfactory.core.utils.discover import createboundmethod
        from clientfactory.logs import log

        log.info(f"[BoundMethod._recreate] Creating proper instance for {self.__name__}")

        inresource = hasattr(parent, '_client')
        getengine = (lambda p: p._engine) if not inresource else (lambda p: p._client._engine)
        getbackend = (lambda p: p._backend) if not inresource else (lambda p: p._backend or p._client._backend)
        baseurl = parent.baseurl if not inresource else (getattr(parent, 'baseurl', None) or parent._client.baseurl)
        resourcepath = None if not inresource else parent.path

        log.info(f"[BoundMethod._recreate] baseurl: {baseurl}, resourcepath: {resourcepath}")

        # Return completely new, properly constructed BoundMethod
        return createboundmethod(
            method=self._func,
            parent=parent,
            getengine=getengine,
            getbackend=getbackend,
            baseurl=baseurl,
            resourcepath=resourcepath
        )


    def _autoresolve(self) -> bool:
        """Decorator to auto-resolve binding before method execution."""
        from clientfactory.logs import log
        if (not self._resolved) or (self._parent is UNSET):
            log.info(f"[BoundMethod._autoresolve] auto-resolving: {self.__name__}")
            log.info(f"[BoundMethod._autoresolve] self._resolved: {self._resolved}\tself._parent: {self._parent}")
            parent = self._autodetectparent()
            if parent:
                log.info(f"[BoundMethod._autoresolve] parent detected: {parent}\nRecreating proper instance")
                rebound = self._recreate(parent)
                log.info(f"[BoundMethod._autoresolve] self.__dict__ before update: {self.__dict__}")
                self.__dict__.update(rebound.__dict__)
                log.info(f"[BoundMethod._autoresolve] self.__dict__ after update: {self.__dict__}")
                return True
            return False
        return True

    @staticmethod
    def _requireresolution(func: t.Callable) -> t.Callable:
        """Decorator ensuring method is resolved before execution."""
        def decorator(self, *args, **kwargs):
            if not self._autoresolve():#if (not getattr(self, '_resolved', False)) or (self._parent is UNSET):
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

'''
TODO:
    handle mixins for recreated binds
'''
