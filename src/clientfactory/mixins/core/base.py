# ~/clientfactory/src/clientfactory/mixins/core/base.py
"""
...
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.mixins.core.comps import (
    MergeStrategy, ExecMode, Scoping, MixinMetadata,
    UPDATE, REPLACE, DEEP, APPEND,
    IMMEDIATE, DEFERRED, TRANSFORM, PREPARE
)

if t.TYPE_CHECKING:
    from clientfactory.core.models.request import ExecutableRequest
    from clientfactory.core.models.config import MethodConfig
    from clientfactory.core.bases import BaseClient, BaseResource, BaseEngine

class BaseMixin(abc.ABC):
    """..."""
    __mixmeta__: MixinMetadata
    __chainedas__: str

    def __init_subclass__(cls, **kwargs):
        """..."""
        super().__init_subclass__(**kwargs)
        for attr in ('__mixmeta__', '__chainedas__'):
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define {attr}")

    @abc.abstractmethod
    def _exec_(self, conf: t.Dict[str, t.Any], **kwargs) -> t.Any:
        """..."""
        ...

    @abc.abstractmethod
    def _configure_(self, **kwargs) -> t.Dict[str, t.Any]:
        """..."""
        ...


    @classmethod
    def getchain(cls) -> str:
        """..."""
        return cls.__chainedas__

    @classmethod
    def getmeta(cls) -> MixinMetadata:
        """..."""
        return cls.__mixmeta__

    def _getmethodconfig(self) -> 'MethodConfig':
        """Get method config from bound method."""
        if not hasattr(self, '_methodconfig'):
            raise AttributeError("prepare() can only be called on bound methods with method config")

        methodconfig: t.Optional['MethodConfig'] = getattr(self, '_methodconfig', None)
        if methodconfig is None:
            raise ValueError("Method config is None")

        return methodconfig

    def _getengine(self) -> 'BaseEngine':
        """Get engine for request execution."""

        # Check parent (could be client or resource)
        parent: t.Optional[t.Union['BaseClient', 'BaseResource']] = getattr(self, '_parent', None)

        if parent is not None:
            # If parent is a client, get its engine
            if hasattr(parent, '_engine'):
                client: 'BaseClient' = parent  # type: ignore
                engine = getattr(client, '_engine', None)
                if engine is not None:
                    return engine

            # If parent is a resource, get its client's engine
            if hasattr(parent, '_client'):
                resource: 'BaseResource' = parent  # type: ignore
                resourceparent: t.Optional['BaseClient'] = getattr(resource, '_client', None)
                if resourceparent is not None and hasattr(resourceparent, '_engine'):
                    engine = getattr(resourceparent, '_engine', None)
                    if engine is not None:
                        return engine

        # Fallback to original logic
        client: t.Optional['BaseClient'] = getattr(self, '_client', None)
        if client is not None:
            engine = getattr(client, '_engine', None)
            if engine is not None:
                return engine

        engine: t.Optional['BaseEngine'] = getattr(self, '_engine', None)
        if engine is not None:
            return engine

        raise AttributeError("No engine available for request preparation")
