# ~/clientfactory/src/clientfactory/mixins/core/comps.py
"""
...
"""
from __future__ import annotations
import enum, typing as t

from pydantic import (
    BaseModel as PydModel,
    Field,
    computed_field as computedfield,
    field_validator as fieldvalidator
)

class MergeStrategy(str, enum.Enum):
    UPDATE = "update" # dict.update -- last wins
    REPLACE = "replace" # complete overwrite
    DEEP = "deep" # deep merge
    APPEND = "append" # for list-type configs

    def _deepmerge(self, d1: dict, d2: dict) -> dict:
        result = d1.copy()
        shouldrecurse = lambda key, value: (key in result) and isinstance(result[key], dict) and isinstance(value, dict)
        for k,v in d2.items():
            if shouldrecurse(k,v):
                result[k] = self._deepmerge(result[k], v)
            else:
                result[k] = v
        return result

    def _appendmerge(self, d1: dict, d2: dict) -> dict:
        result = d1.copy()
        shouldappend = lambda key, value: (key in result) and isinstance(result[key], list) and isinstance(value, list)
        for k,v in d2.items():
            if shouldappend(k, v):
                result[k] = (result[k] + v)
            else:
                result[k] = v
        return result

    def merge(self, extant: dict, new: dict) -> dict:
        match self.value:
            case "replace":
                return new.copy()
            case "update":
                result = extant.copy()
                result.update(new)
                return result
            case "append":
                return self._appendmerge(extant, new)
            case "deep":
                return self._deepmerge(extant, new)
            case _:
                raise ValueError() # shouldnt be reachable

    def __call__(self, extant: dict, new: dict) -> dict:
        """..."""
        return self.merge(extant, new)

class ExecMode(str, enum.Enum):
    IMMEDIATE = "immediate" # right away
    DEFERRED  = "deferred" # defer return value, keep chain
    TRANSFORM  = "transform" # modify request/response flow
    PREPARE = "prepare" # return executable object

    @property
    def terminates(self) -> bool:
        return self.value in ["immediate", "prepare"]

    @property
    def defers(self) -> bool:
        return self.value == "deferred"

    @property
    def transforms(self) -> bool:
        return self.value == "transform"

class Scoping(str, enum.Enum):
    GLOBAL  = "global" # persists all methods
    SESSION = "session" # persists across calls
    METHOD = "method" # single method call

class MixinMetadata(PydModel):
    """..."""
    ## capabilities ##
    chainable: bool = True # can this mixin can be chained with others
    terminal: bool = False # can this mixin end a chain

    ## exec control ##
    priority: int = Field(default=0, ge=0)
    mode: ExecMode = ExecMode.DEFERRED
    scope: Scoping = Scoping.METHOD

    ## compatibilities ##
    conflicts: t.List[str] = Field(default_factory=list) # mixin names that conflict
    requires: t.List[str] = Field(default_factory=list) # mixin names that must come before
    enhances: t.List[str] = Field(default_factory=list) # mixin names that works well with

    ## behaviors ##
    merging: MergeStrategy = MergeStrategy.UPDATE
    autoreset: bool = True # clear after execution

    ## parameter handling ##
    confkeys: t.Set[str] = Field(default_factory=set)
    passkeys: t.Set[str] = Field(default_factory=set)

    @fieldvalidator('conflicts', 'requires', 'enhances')
    @classmethod
    def _validatecompats(cls, v: t.List[str]) -> t.List[str]: #! this is kinda asscheeks
        for name in v:
            if not name.isidentifier():
                raise ValueError(f"Invalid Mixin: {name}")
        return v


    @computedfield
    def terminator(self) -> bool:
        """Whether this mixin typically ends a chain"""
        return self.terminal or self.mode.terminates


## shorthands ##
### strategy ###
UPDATE = MergeStrategy.UPDATE
REPLACE = MergeStrategy.REPLACE
DEEP = MergeStrategy.DEEP
APPEND = MergeStrategy.APPEND

### mode ###
IMMEDIATE = ExecMode.IMMEDIATE
DEFERRED = ExecMode.DEFERRED
TRANSFORM = ExecMode.TRANSFORM
PREPARE = ExecMode.PREPARE
