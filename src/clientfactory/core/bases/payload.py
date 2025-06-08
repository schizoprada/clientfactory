# ~/clientfactory/src/clientfactory/core/bases/payload.py
"""
Base Payload Implementation
--------------------------
Abstract base class for request payload validation and transformation.
"""
from __future__ import annotations
import abc, typing as t

from clientfactory.core.models import Param, PayloadConfig
from clientfactory.core.protos import PayloadProtocol

class BasePayload(PayloadProtocol, abc.ABC):
    """
    Abstract base class for request payload handling.

    Provides framework for parameter validation, transformation,
    and request data preparation using schematix-powered Param objects.
    """

    def __init__(
        self,
        config: t.Optional[PayloadConfig] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize payload with configuration."""
        self._config: PayloadConfig = (config or PayloadConfig(**kwargs))
        self._params: t.Dict[str, Param] = {}
        self._static: t.Dict[str, t.Any] = {}

        # discover parameters
        self._discoverparams()

    ## abstracts ##
    @abc.abstractmethod
    def _regiserparam(self, param: Param, name: t.Optional[str] = None) -> None: ...

    @abc.abstractmethod
    def _discoverparams(self) -> None:...

    @abc.abstractmethod
    def _transformdata(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]: ...

    ## concretes ##
    def addparam(self, param: Param, name: t.Optional[str] = None) -> None:
        self._regiserparam(param, name)

    def removeparam(self, name: str) -> None:
        """Remove parameter from payload."""
        if name in self._params:
            del self._params[name]

    def getparam(self, name: str) -> t.Optional[Param]:
        """Get parameter by name."""
        return self._params.get(name)

    def listparams(self) -> t.List[str]:
        """List all parameter names."""
        return list(self._params.keys())

    def validate(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Validate data against all parameters."""
        validated = {}
        errors = []

        for name, param in self._params.items():
            try:
                if name in data:
                    validated[name] = param.validate(data[name])
                elif param.required:
                    if param.default is not None:
                        validated[name] = param.default
                    else:
                        errors.append(f"Required parameter '{name}' missing")
                elif param.default is not None:
                    validated[name] = param.default
            except Exception as e:
                errors.append(f"Parameter '{name}' validation failed: {e}")

        if errors:
            raise ValueError(f"Payload validation failed: {'; '.join(errors)}")

        return validated

    def serialize(self, data: t.Dict[str, t.Any]) -> t.Union[str, bytes, t.Dict[str, t.Any]]:
            """Serialize validated data."""
            # validate first
            validated = self.validate(data)

            # apply transformations
            transformed = self._transformdata(validated)

            # merge with static data
            result = self._static.copy()
            result.update(transformed)

            return result

    def setstatic(self, **kwargs: t.Any) -> None:
        """Set static values to include in all payloads."""
        self._static.update(kwargs)

    def getconfig(self) -> PayloadConfig:
        """Get payload configuration."""
        return self._config
