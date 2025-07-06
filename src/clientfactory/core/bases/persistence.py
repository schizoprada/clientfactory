# ~/clientfactory/src/clientfactory/core/bases/persistence.py
"""
Base Persistence Implementation
------------------------------
Abstract base class for session state persistence.
"""
from __future__ import annotations
import abc, typing as t
from pathlib import Path

from clientfactory.core.protos.persistence import PersistenceProtocol
from clientfactory.core.models.config import PersistenceConfig
from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.metas.protocoled import ProtocoledAbstractMeta

class BasePersistence(abc.ABC, Declarative): #! add back in PersistenceProtocol,
    """
    Abstract base class for session state persistence.

    Provides common functionality and enforces protocol interface.
    Concrete implementations handle specific storage mechanisms.
    """
    __protocols: set = {PersistenceProtocol}
    __declaredas__: str = 'persistence'
    __declcomps__: set = set()
    __declattrs__: set = {'path', 'format'} #! revise
    __declconfs__: set = {'autoload', 'autosave', 'timeout', 'file', 'format', 'headers', 'cookies', 'tokens'}

    def __init__(
        self,
        config: t.Optional[PersistenceConfig] = None,
        **kwargs: t.Any
    ) -> None:
        """Initialize persistence manager."""
        # 1. resolve components
        components = self._resolvecomponents() # not needed

        # 2. resolve config
        self._config: PersistenceConfig = self._resolveconfig(PersistenceConfig, config, **kwargs)

        # 3. resolve attributes
        attrs = self._collectattributes(**kwargs)
        self._resolveattributes(attrs)

        self._state: t.Dict[str, t.Any] = {}
        self._loaded: bool = False
        if self._config.autoload:
            self._state = self.load()
            self._loaded = True


    def _resolveattributes(self, attributes: dict) -> None:
        self.path: str = attributes.get('path', '')
        self.format: str = attributes.get('format', 'json')

    @abc.abstractmethod
    def _save(self, data: t.Dict[str, t.Any]) -> None:
        """Implementation-specific save logic."""
        ...

    @abc.abstractmethod
    def _load(self) -> t.Dict[str, t.Any]:
        """Implementation-specific load logic."""
        ...

    @abc.abstractmethod
    def _clear(self) -> None:
        """Implementation-specific clear logic."""
        ...

    @abc.abstractmethod
    def _exists(self) -> bool:
        """Implementation-specific existence check."""
        ...

    def _filterdata(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Filter data based on config settings."""
        filtered = {}

        if self._config.cookies and 'cookies' in data:
            filtered['cookies'] = data['cookies']
        if self._config.headers and 'headers' in data:
            filtered['headers'] = data['headers']
        if self._config.tokens and 'tokens' in data:
            filtered['tokens'] = data['tokens']

        return filtered

    def save(self, data: t.Dict[str, t.Any]) -> None:
        """Save session state data."""
        try:
            filtered = self._filterdata(data)
            self._save(filtered)
        except Exception as e:
            raise RuntimeError(f"Failed to save state: {e}") from e

    def load(self) -> t.Dict[str, t.Any]:
        """Load session state data."""
        try:
            data = self._load()
            self._state = data.copy()
            self._loaded = True
            return data
        except Exception as e:
            self._state = {}
            self._loaded = True
            return {}

    def clear(self) -> None:
        """Clear all persisted session state."""
        try:
            self._clear()
            self._state = {}
        except Exception as e:
            raise RuntimeError(f"Failed to clear state: {e}") from e

    def exists(self) -> bool:
        """Check if persisted state exists."""
        try:
            return self._exists()
        except Exception:
            return False

    def update(self, data: t.Dict[str, t.Any]) -> None:
        """Update specific keys in persisted state."""
        if not self._loaded:
            self._state = self.load()

        self._state.update(data)

        if self._config.autosave:
            self.save(self._state)

    def get(self, key: str, default: t.Any = None) -> t.Any:
        """Get value from state."""
        if not self._loaded:
            self._state = self.load()
        return self._state.get(key, default)

    def set(self, key: str, value: t.Any) -> None:
        """Set value in state."""
        if not self._loaded:
            self._state = self.load()

        self._state[key] = value

        if self._config.autosave:
            self.save(self._state)

    def getall(self) -> t.Dict[str, t.Any]:
        """Get all state data."""
        if not self._loaded:
            self._state = self.load()
        return self._state.copy()

    @classmethod
    def _compose(cls, other: t.Any) -> t.Any:
        raise NotImplementedError()
