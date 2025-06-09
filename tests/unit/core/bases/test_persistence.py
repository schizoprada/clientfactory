# tests/unit/core/bases/test_persistence.py
"""
Tests for BasePersistence implementation
"""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from clientfactory.core.bases.persistence import BasePersistence
from clientfactory.core.models.config import PersistenceConfig
from clientfactory.core.protos.persistence import PersistenceProtocol

class ConcretePersistence(BasePersistence):
    """Concrete implementation for testing"""

    def __init__(self, config=None, **kwargs):
        self._save_calls = []
        self._load_calls = []
        self._clear_calls = []
        self._exists_calls = []
        self._storage = {}
        super().__init__(config, **kwargs)

    def _save(self, data):
        self._save_calls.append(data)
        self._storage = data.copy()

    def _load(self):
        self._load_calls.append(True)
        return self._storage.copy()

    def _clear(self):
        self._clear_calls.append(True)
        self._storage = {}

    def _exists(self):
        self._exists_calls.append(True)
        return bool(self._storage)

class TestBasePersistence:
    """Test BasePersistence abstract base class"""

    def test_implements_protocol(self):
        """Test that BasePersistence implements PersistenceProtocol"""
        persistence = ConcretePersistence()
        assert isinstance(persistence, PersistenceProtocol)

    def test_init_with_config(self):
        """Test initialization with PersistenceConfig"""
        config = PersistenceConfig(
            cookies=True,
            headers=False,
            autoload=False,
            autosave=False
        )
        persistence = ConcretePersistence(config=config)

        assert persistence._config is config
        assert persistence._config.cookies == True
        assert persistence._config.headers == False
        assert persistence._config.autoload == False
        assert persistence._config.autosave == False

    def test_init_with_kwargs(self):
        """Test initialization with keyword arguments"""
        persistence = ConcretePersistence(
            cookies=False,
            headers=True,
            autoload=True
        )

        assert persistence._config.cookies == False
        assert persistence._config.headers == True
        assert persistence._config.autoload == True

    def test_autoload_disabled(self):
        """Test that autoload=False doesn't call load on init"""
        persistence = ConcretePersistence(autoload=False)

        assert len(persistence._load_calls) == 0
        assert persistence._loaded == False

    def test_autoload_enabled(self):
        """Test that autoload=True calls load on init"""
        persistence = ConcretePersistence(autoload=True)

        assert len(persistence._load_calls) == 1
        assert persistence._loaded == True

    def test_filter_data_cookies_only(self):
        """Test data filtering with cookies enabled only"""
        config = PersistenceConfig(cookies=True, headers=False, tokens=False)
        persistence = ConcretePersistence(config=config)

        data = {
            'cookies': {'session': '123'},
            'headers': {'User-Agent': 'test'},
            'tokens': {'access': 'abc'},
            'other': 'ignored'
        }

        filtered = persistence._filterdata(data)

        assert filtered == {'cookies': {'session': '123'}}

    def test_filter_data_headers_only(self):
        """Test data filtering with headers enabled only"""
        config = PersistenceConfig(cookies=False, headers=True, tokens=False)
        persistence = ConcretePersistence(config=config)

        data = {
            'cookies': {'session': '123'},
            'headers': {'User-Agent': 'test'},
            'tokens': {'access': 'abc'}
        }

        filtered = persistence._filterdata(data)

        assert filtered == {'headers': {'User-Agent': 'test'}}

    def test_filter_data_all_enabled(self):
        """Test data filtering with all options enabled"""
        config = PersistenceConfig(cookies=True, headers=True, tokens=True)
        persistence = ConcretePersistence(config=config)

        data = {
            'cookies': {'session': '123'},
            'headers': {'User-Agent': 'test'},
            'tokens': {'access': 'abc'},
            'other': 'ignored'
        }

        filtered = persistence._filterdata(data)

        expected = {
            'cookies': {'session': '123'},
            'headers': {'User-Agent': 'test'},
            'tokens': {'access': 'abc'}
        }
        assert filtered == expected

    def test_save_calls_filter(self):
        """Test that save() filters data before calling _save()"""
        config = PersistenceConfig(cookies=True, headers=False)
        persistence = ConcretePersistence(config=config, autoload=False)

        data = {
            'cookies': {'session': '123'},
            'headers': {'User-Agent': 'test'}
        }

        persistence.save(data)

        assert len(persistence._save_calls) == 1
        assert persistence._save_calls[0] == {'cookies': {'session': '123'}}

    def test_load_returns_data(self):
        """Test that load() returns data from _load()"""
        persistence = ConcretePersistence(autoload=False)
        persistence._storage = {'test': 'data'}

        result = persistence.load()

        assert result == {'test': 'data'}
        assert persistence._loaded == True

    def test_load_handles_exception(self):
        """Test that load() handles exceptions gracefully"""
        persistence = ConcretePersistence(autoload=False)

        def failing_load():
            raise Exception("Load failed")

        persistence._load = failing_load

        result = persistence.load()

        assert result == {}
        assert persistence._loaded == True

    def test_clear_calls_implementation(self):
        """Test that clear() calls _clear()"""
        persistence = ConcretePersistence(autoload=False)
        persistence._state = {'some': 'data'}

        persistence.clear()

        assert len(persistence._clear_calls) == 1
        assert persistence._state == {}

    def test_exists_calls_implementation(self):
        """Test that exists() calls _exists()"""
        persistence = ConcretePersistence(autoload=False)

        result = persistence.exists()

        assert len(persistence._exists_calls) == 1
        assert isinstance(result, bool)

    def test_exists_handles_exception(self):
        """Test that exists() handles exceptions gracefully"""
        persistence = ConcretePersistence(autoload=False)

        def failing_exists():
            raise Exception("Exists check failed")

        persistence._exists = failing_exists

        result = persistence.exists()

        assert result == False

    def test_update_with_autosave(self):
        """Test update() with autosave enabled"""
        persistence = ConcretePersistence(autosave=True, autoload=False)
        persistence._state = {'existing': 'data'}
        persistence._loaded = True

        persistence.update({'new': 'value'})

        assert persistence._state == {'existing': 'data', 'new': 'value'}
        assert len(persistence._save_calls) == 1

    def test_update_without_autosave(self):
        """Test update() with autosave disabled"""
        persistence = ConcretePersistence(autosave=False, autoload=False)
        persistence._state = {'existing': 'data'}
        persistence._loaded = True

        persistence.update({'new': 'value'})

        assert persistence._state == {'existing': 'data', 'new': 'value'}
        assert len(persistence._save_calls) == 0

    def test_get_loads_if_needed(self):
        """Test that get() loads state if not loaded"""
        persistence = ConcretePersistence(autoload=False)
        persistence._storage = {'test': 'value'}

        result = persistence.get('test')

        assert result == 'value'
        assert len(persistence._load_calls) == 1

    def test_get_returns_default(self):
        """Test that get() returns default for missing keys"""
        persistence = ConcretePersistence(autoload=False)
        persistence._state = {}
        persistence._loaded = True

        result = persistence.get('missing', 'default')

        assert result == 'default'

    def test_set_with_autosave(self):
        """Test set() with autosave enabled"""
        persistence = ConcretePersistence(autosave=True, autoload=False)
        persistence._state = {}
        persistence._loaded = True

        persistence.set('key', 'value')

        assert persistence._state['key'] == 'value'
        assert len(persistence._save_calls) == 1

    def test_set_loads_if_needed(self):
        """Test that set() loads state if not loaded"""
        persistence = ConcretePersistence(autosave=False, autoload=False)

        persistence.set('key', 'value')

        assert len(persistence._load_calls) == 1
        assert persistence._state['key'] == 'value'

    def test_getall_returns_copy(self):
        """Test that getall() returns a copy of state"""
        persistence = ConcretePersistence(autoload=False)
        persistence._state = {'test': 'data'}
        persistence._loaded = True

        result = persistence.getall()

        assert result == {'test': 'data'}
        assert result is not persistence._state  # Should be a copy

    def test_save_exception_handling(self):
        """Test save() exception handling"""
        persistence = ConcretePersistence(autoload=False)

        def failing_save(data):
            raise Exception("Save failed")

        persistence._save = failing_save

        with pytest.raises(RuntimeError, match="Failed to save state"):
            persistence.save({'test': 'data'})

    def test_clear_exception_handling(self):
        """Test clear() exception handling"""
        persistence = ConcretePersistence(autoload=False)

        def failing_clear():
            raise Exception("Clear failed")

        persistence._clear = failing_clear

        with pytest.raises(RuntimeError, match="Failed to clear state"):
            persistence.clear()

class TestPersistenceConfig:
    """Test PersistenceConfig integration"""

    def test_default_config_values(self):
        """Test default configuration values"""
        persistence = ConcretePersistence()

        config = persistence._config
        assert config.cookies == True
        assert config.headers == True
        assert config.tokens == False
        assert config.autoload == True
        assert config.autosave == True

    def test_custom_config_override(self):
        """Test custom configuration override"""
        config = PersistenceConfig(
            cookies=False,
            headers=False,
            tokens=True,
            autoload=False,
            autosave=False
        )
        persistence = ConcretePersistence(config=config)

        assert persistence._config.cookies == False
        assert persistence._config.headers == False
        assert persistence._config.tokens == True
        assert persistence._config.autoload == False
        assert persistence._config.autosave == False
