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
