# ~/clientfactory/src/clientfactory/mixins/core/mixer.py
"""
...
"""
from __future__ import annotations
import typing as t, collections as co

from clientfactory.mixins.core.base import BaseMixin
from clientfactory.mixins.core.comps import MixinMetadata, ExecMode
from clientfactory.mixins.preparation.mixin import PrepMixin

if t.TYPE_CHECKING:
    from clientfactory.core.models.methods import BoundMethod

class Mixer:
    """..."""

    def __init__(
        self,
        bound: 'BoundMethod'
    ) -> None:
        """..."""
        self._bound = bound
        self._confs: t.Dict[str, t.Dict[str, t.Any]] = {} # {mixin: conf}
        self._links: t.List[str] = [] # track order for execution
        self._proxymethods()

    def _discovermixins(self) -> t.List[t.Type[BaseMixin]]:
        """..."""
        discoverable = lambda c: issubclass(c, BaseMixin) and (c is not BaseMixin)
        mixins = [
            cls for cls in type(self._bound).__mro__
            if discoverable(cls)
        ]
        return mixins

    def _checkconflicts(self, mixin: t.Type[BaseMixin]) -> None:
        """..."""
        for conflict in mixin.__mixmeta__.conflicts:
            if conflict in self._confs:
                raise ValueError()

    def _methodchain(self, mixin: t.Type[BaseMixin]) -> t.Callable[..., 'Mixer']:
        """..."""
        def chainmethod(**kwargs) -> 'Mixer':
            self._checkconflicts(mixin)
            name = mixin.__chainedas__

            # prepare and merge config
            newconf = mixin._configure_(self._bound, **kwargs)
            extconf = self._confs.get(name, {})
            conf = mixin.__mixmeta__.merging(extconf, newconf)

            self._confs[name] = conf
            if (name not in self._links):
                self._links.append(name)

            return self

        return chainmethod

    def _getorder(self) -> t.List[t.Type[BaseMixin]]:
        """..."""
        chainmap = {
            cls.__chainedas__: cls for cls in self._discovermixins()
        }
        configured = [chainmap[name] for name in self._links if name in chainmap]
        sortkey = lambda c: c.__mixmeta__.priority
        return sorted(configured, key=sortkey)

    def _resetorpass(self) -> None:
        """..."""
        should = any(
            m.__mixmeta__.autoreset
            for m in self._discovermixins()
            if m.__chainedas__ in self._confs
        )
        if should:
            self._confs.clear()
            self._links.clear()

    def _proxymethods(self) -> None:
        """Dynamically create proxy methods with proper signatures"""
        def getoriginal(name: str) -> t.Optional[t.Callable]:
            for mixin in self._discovermixins():
                if mixin.__chainedas__ == name:
                    return mixin._configure_
            return None

        def create(name: str) -> t.Callable:
            def proxy(**kwargs) -> 'Mixer': return self.__getattr__(name)(**kwargs)

            if (original:=getoriginal(name)):
                proxy.__doc__ = original.__doc__
                proxy.__annotations__ = original.__annotations__.copy()
                proxy.__name__ = original.__name__

            return proxy

        for mixin in self._discovermixins():
            proxy = create(mixin.__chainedas__)
            setattr(self, mixin.__chainedas__, proxy)

    def execute(self, **kwargs) -> t.Any:
        """..."""
        if not self._confs:
            # no mixins configured, regular execution
            return self._bound(**kwargs)

        ordered = self._getorder()

        result = None
        for mixin in ordered:
            name = mixin.__chainedas__
            conf = self._confs[name]

            if mixin.__mixmeta__.mode.terminates:
                result = mixin._exec_(self._bound, conf, **kwargs)
                break
            elif mixin.__mixmeta__.mode.defers:
                continue
            elif mixin.__mixmeta__.mode.transforms:
                kwargs = mixin._exec_(self._bound, conf, **kwargs)

        if result is None:
            result = self._bound(**kwargs)

        self._resetorpass()

        return result


    def __call__(self, **kwargs) -> t.Any:
        """..."""
        return self.execute(**kwargs)

    def __getattr__(self, name: str) -> t.Callable:
        """..."""
        for mixin in self._discovermixins():
            if mixin.__chainedas__ == name:
                return self._methodchain(mixin)
        raise AttributeError()

    ## Mixin Chainable Method References for IDE##
    def iter(self, **kwargs) -> 'Mixer': return self.__getattr__('iter')(**kwargs)

    def prep(self, **kwargs) -> 'Mixer': return self.__getattr__('prep')(**kwargs)
