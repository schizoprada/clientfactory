# ~/clientfactory/tests/unit/decorators/test_persistences.py
"""
Unit tests for persistence decorators.
"""
import pytest
import tempfile
from pathlib import Path

from clientfactory.decorators.persistences import persistence
from clientfactory.core.persistence import Persistence
from clientfactory.core.bases.persistence import BasePersistence


class TestPersistenceDecorators:
   """Test persistence decorators."""

   def test_persistence_decorator_basic(self):
       """Test basic @persistence decorator."""
       @persistence
       class MyPersistence:
           path = "/tmp/test.json"
           format = "json"
           cookies = True
           headers = False


       print(f"""
           DEBUG:
            path: {MyPersistence.path}
            format: {MyPersistence.format}
            cookies: {MyPersistence._config.cookies}
            headers: {MyPersistence._config.headers}
           """)
       assert isinstance(MyPersistence, BasePersistence)
       assert isinstance(MyPersistence, Persistence)  # Should be concrete JSON implementation
       assert MyPersistence.path == "/tmp/test.json"
       assert MyPersistence.format == "json"
       assert MyPersistence._config.cookies is True
       assert MyPersistence._config.headers is False

   def test_persistence_json_decorator(self):
       """Test @persistence.json decorator."""
       @persistence.json
       class JsonPersistence:
           path = "/tmp/json_test.json"
           cookies = True
           headers = True

       assert isinstance(JsonPersistence, Persistence)
       assert JsonPersistence.path == "/tmp/json_test.json"
       assert JsonPersistence.format == "json"
       assert JsonPersistence._config.cookies is True
       assert JsonPersistence._config.headers is True

   def test_persistence_pkl_decorator_not_implemented(self):
       """Test @persistence.pkl decorator raises NotImplementedError."""
       with pytest.raises(NotImplementedError, match="Pickle persistence not yet implemented"):
           @persistence.pkl
           class PicklePersistence:
               path = "/tmp/pickle_test.pkl"

   def test_persistence_decorator_ignores_private_attrs(self):
       """Test that decorator ignores private attributes."""
       @persistence
       class MyPersistence:
           path = "/tmp/test.json"
           _private = "ignored"
           __dunder = "ignored"

       assert MyPersistence.path == "/tmp/test.json"
       assert not hasattr(MyPersistence, '_private')
       assert not hasattr(MyPersistence, '__dunder')

   def test_persistence_decorator_functional(self):
       """Test that decorated persistence actually works."""
       with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
           temp_path = f.name

       try:
           @persistence
           class MyPersistence:
               path = temp_path
               cookies = True
               headers = False
               autoload = False
               autosave = False

           # Test save/load functionality
           test_data = {'cookies': {'session': 'abc123'}}
           MyPersistence.save(test_data)

           loaded_data = MyPersistence.load()
           # Should only have cookies due to filtering
           assert loaded_data == {'cookies': {'session': 'abc123'}}

       finally:
           Path(temp_path).unlink(missing_ok=True)

   def test_persistence_decorator_with_config_attrs(self):
       """Test persistence decorator with various config attributes."""
       @persistence
       class MyPersistence:
           path = "/tmp/test.json"
           autoload = True
           autosave = False
           cookies = True
           headers = False
           tokens = True

       assert MyPersistence._config.autoload is True
       assert MyPersistence._config.autosave is False
       assert MyPersistence._config.cookies is True
       assert MyPersistence._config.headers is False
       assert MyPersistence._config.tokens is True
