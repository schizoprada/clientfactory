# ~/clientfactory/src/clientfactory/core/metas/declarative.py
"""
...
"""
from __future__ import annotations
import abc, inspect, typing as t

from clientfactory.core.models import DeclarativeType, DECLARATIVE

class DeclarativeMeta(abc.ABCMeta):
    """
    Metaclass for declarative components.

    Handles automatic discovery of nested classes, methods, and attributes
    during class creation. Populates metadata dictionaries for runtime access.

    Inherits from ABCMeta to avoid metaclass conflicts with abstract base classes.
    """

    def __new__(mcs, name: str, bases: tuple, namespace: dict, **kwargs):
        # create class
        cls = super().__new__(mcs, name, bases, namespace) # remoed kwargs [type]super() doesnt accept

        # initialize metadata storage
        setattr(cls, '_declmetadata', {})
        setattr(cls, '_declcomponents', {})
        setattr(cls, '_declmethods', {})
        setattr(cls, '_declconfigs', {})
        setattr(cls, '_declattrs', {})

        # process class attributes and discover elements
        mcs._discovercomponents(cls, namespace)
        mcs._discoverconfigs(cls, namespace)
        mcs._discoverattrs(cls, namespace)
        mcs._discovermethods(cls, namespace)
        mcs._inherit(cls, bases)
        mcs._injectparent(cls)
        return cls

    @classmethod
    def _injectparent(mcs, cls: type) -> None:
        """Wrap __init__ to automatically inject parent references via stack inspection."""
        #print(f"DEBUG: _injectparent called for {cls.__name__}")
        oginit = getattr(cls, '__init__', None)
        if not oginit:
            #print(f"DEBUG: No __init__ found for {cls.__name__}, skipping")
            return

        def wrappedinit(self, *args, **kwargs):
            #print(f"DEBUG: wrappedinit called for {self.__class__.__name__}")
            import inspect
            currentframe = inspect.currentframe()
            if currentframe:
                frame = currentframe.f_back
                framecount = 0
                while frame and framecount < 10:  # Prevent infinite loops
                    framecount += 1
                    #print(f"DEBUG: Checking frame {framecount}: {frame.f_code.co_name}")
                    if ('self' in frame.f_locals):
                        potentialparent = frame.f_locals['self']
                        #print(f"DEBUG: Found potential parent: {potentialparent.__class__.__name__}")
                        if (
                            hasattr(potentialparent, '_declcomponents') and
                            potentialparent is not self
                        ):
                            #print(f"DEBUG: Setting parent {potentialparent.__class__.__name__} for {self.__class__.__name__}")
                            self._parent = potentialparent
                            break
                    frame = frame.f_back

                if not hasattr(self, '_parent'):
                    pass #print(f"DEBUG: No parent found for {self.__class__.__name__}")

            oginit(self, *args, **kwargs)

        setattr(cls, '__init__', wrappedinit)
        #print(f"DEBUG: Wrapped __init__ for {cls.__name__}")

    @classmethod
    def _discoverconfigs(mcs, cls: type, namespace: dict) -> None:
        """Discover config attributes based on class's __declconfs__ set."""
        declconfs = getattr(cls, '__declconfs__', set())

        for name, value in namespace.items():
            if (name in declconfs) and (not callable(value)): #! revise this
                cls._declconfigs[name] = value

    @classmethod
    def _discoverattrs(mcs, cls: type, namespace: dict) -> None:
        """Discover general attributes based on class's __declattrs__ set."""

        declattrs = getattr(cls, '__declattrs__', set())

        for name, value in namespace.items():
            if (name in declattrs) and (not callable(value)): #! revise this
                cls._declattrs[name] = value

    @classmethod
    def _discoverdunders(mcs, cls: type, namespace: dict) -> None:
        """Discover components via __component__ pattern."""
        declcomps = getattr(cls, '__declcomps__', set()) # get valid declcomps
        #print(f"DEBUG _discoverdunders: cls={cls.__name__}, declcomps={declcomps}")

        isdunder = lambda x: x.startswith('__') and x.endswith('__')
        stripdunder = lambda x: x.lstrip('__').rstrip('__')

        for name, value in namespace.items():
            #print(f"DEBUG _discoverdunders: checking {name}={value}")
            if isdunder(name):
                compname = stripdunder(name)
                #print(f"DEBUG _discoverdunders: found dunder {name} -> {compname}")
                if compname in declcomps:
                    #print(f"DEBUG _discoverdunders: {compname} is declarable, storing")
                    if inspect.isclass(value):
                        # store class for lazy instantiation
                        cls._declcomponents[compname] = {'type': 'class', 'value': value}
                    else:
                        # store instance directly
                        cls._declcomponents[compname] = {'type': 'instance', 'value': value}


    @classmethod
    def _discovernested(mcs, cls: type, namespace: dict) -> None:
        """Discover nested classes that should be treated as components"""
        declcomps = getattr(cls, '__declcomps__', set())

        for name, value in namespace.items():
            if inspect.isclass(value):

                # check if nested class has a __declaredas attribute in its MRO
                for base in value.__mro__:
                    declaredas = getattr(base, '__declaredas__', None)
                    if declaredas:
                        if declaredas in declcomps:
                            cls._declcomponents[declaredas] = {'type': 'class', 'value': value}
                            break

                # fallback
                if hasattr(value, '_decltype'):
                    cls._declcomponents[name.lower()] = value
                    value._parent = cls



    @classmethod
    def _discovercomponents(mcs, cls: type, namespace: dict) -> None:
        """Discover all components (dunder & nested)"""
        # start with dunder declarations
        mcs._discoverdunders(cls, namespace)
        mcs._discovernested(cls, namespace)

    @classmethod
    def _discovermethods(mcs, cls: type, namespace: dict) -> None:
        """Discover methods marked with declarative metadata."""
        for name, value in namespace.items():
            if callable(value) and (not name.startswith("_")):
                methodinfo = {
                    'method': value,
                    'config': getattr(value, '_methodconfig', None)
                }
                cls._declmethods[name] = methodinfo

    @classmethod
    def _inherit(mcs, cls: type, bases: tuple) -> None:
        """Process attribute inheritance from parent classes."""
        def _metadata(base: t.Any) -> None:
            """Inherit metadata from parent classes."""
            if hasattr(base, '_declmetadata'):
                for k,v in base._declmetadata.items():
                    if k not in cls._declmetadata:
                        cls._declmetadata[k] = v
        def _components(base: t.Any) -> None:
            """Inherit components from parent classes."""
            if hasattr(base, '_declcomponents'):
                for k,v in base._declcomponents.items():
                    if k not in cls._declcomponents:
                        cls._declcomponents[k] = v

        def _methods(base: t.Any) -> None:
            """Inherit methods from parent classes."""
            if hasattr(base, '_declmethods'):
                for k,v in base._declmethods.items():
                    if k not in cls._declmethods:
                        cls._declmethods[k] = v

        for base in bases:
            _metadata(base) # inherit metadata
            _components(base) # inherit components
            _methods(base) # inherit methods
