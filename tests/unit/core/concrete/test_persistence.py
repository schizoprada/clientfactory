# ~/clientfactory/tests/unit/core/test_persistence.py
# tests/unit/core/test_persistence.py
"""
Unit tests for concrete Persistence implementation.
"""
import pytest
import json
import tempfile
from pathlib import Path

from clientfactory.core.persistence import Persistence
from clientfactory.core.models.config import PersistenceConfig


class TestPersistence:
    """Test concrete Persistence functionality."""

    def test_persistence_creation(self):
        """Test basic persistence creation."""
        persistence = Persistence()
        assert isinstance(persistence, Persistence)
        assert persistence.path == Path(".clientfactorysession.json")  # Default from config
        assert persistence.format == 'json'

    def test_persistence_with_config(self):
        """Test persistence creation with config."""
        config = PersistenceConfig(
            cookies=True,
            headers=False,
            autoload=False,
            autosave=False
        )
        persistence = Persistence(config=config)
        assert persistence._config.cookies is True
        assert persistence._config.headers is False
        assert persistence._config.autoload is False

    def test_save_and_load(self):
        """Test save and load functionality."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = Path(f.name)

        try:
            config = PersistenceConfig(file=temp_path)  # Pass file to config
            persistence = Persistence(config=config)
            test_data = {'cookies': {'session': 'abc123'}, 'headers': {'auth': 'token'}}

            # Save data
            persistence.save(test_data)

            # Load data
            loaded_data = persistence.load()
            assert loaded_data == test_data

        finally:
            temp_path.unlink(missing_ok=True)

    def test_save_creates_directories(self):
        """Test that save creates parent directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / 'nested' / 'dir' / 'test.json'

            persistence = Persistence(file=str(nested_path))
            test_data = {'headers': {'header': 'value'}}

            persistence.save(test_data)
            #print(f"DEBUG test: persistence.path = {persistence.path}")
            exists = nested_path.exists()
            #print(f"DEBUG test: nested path exists: {exists}")
            assert exists
            loaded_data = persistence.load()
            #print(f"DEBUG test: loaded data: {loaded_data}")
            assert loaded_data == test_data

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns empty dict."""
        persistence = Persistence(path='/nonexistent/path/file.json')
        result = persistence.load()
        assert result == {}

    def test_exists(self):
        """Test exists functionality."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            persistence = Persistence(path=temp_path)

            # File exists
            assert persistence.exists() is True

            # Clear file
            persistence.clear()
            assert persistence.exists() is False

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_clear(self):
        """Test clear functionality."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            persistence = Persistence(path=temp_path)
            test_data = {'test': 'data'}

            # Save data
            persistence.save(test_data)
            assert persistence.exists() is True

            # Clear
            persistence.clear()
            assert persistence.exists() is False

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_no_path_operations(self):
        """Test operations when no path is set."""
        # Create config with empty file path
        config = PersistenceConfig(file=Path(""))  # Empty path
        persistence = Persistence(config=config)

        # Should not raise errors
        persistence.save({'test': 'data'})
        result = persistence.load()
        assert result == {}

    def test_filter_data_integration(self):
        """Test that data filtering works with save."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            config = PersistenceConfig(cookies=True, headers=False, tokens=False)
            persistence = Persistence(config=config, path=temp_path)

            test_data = {
                'cookies': {'session': 'abc123'},
                'headers': {'auth': 'token'},
                'tokens': {'access': 'xyz'},
                'other': 'ignored'
            }

            persistence.save(test_data)
            loaded_data = persistence.load()

            # Should only have cookies
            assert loaded_data == {'cookies': {'session': 'abc123'}}

        finally:
            Path(temp_path).unlink(missing_ok=True)
