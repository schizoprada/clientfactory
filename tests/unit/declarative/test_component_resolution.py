# ~/clientfactory/tests/unit/declarative/test_component_resolution.py
import pytest
from unittest.mock import Mock

from clientfactory.core.bases.declarative import Declarative


class MockAuth:
    """Mock auth component for testing."""
    def __init__(self, token="default-token"):
        self.token = token


class MockPersistence:
    """Mock persistence component for testing."""
    def __init__(self, path="default.json"):
        self.path = path


class TestComponentResolution:
    """Test _resolvecomponents method functionality."""

    def test_resolve_with_constructor_params(self):
        """Test that constructor params override class declarations."""

        auth_instance = MockAuth("constructor-token")

        class TestClass(Declarative):
            __declcomps__ = {'auth', 'persistence'}
            __auth__ = MockAuth  # Class declaration

            def _resolveattributes(self, attributes: dict) -> None:
                pass

        instance = TestClass()
        resolved = instance._resolvecomponents(auth=auth_instance)

        # Constructor param should win
        assert resolved['auth'] is auth_instance
        assert resolved['auth'].token == "constructor-token"

    def test_resolve_with_class_declarations(self):
        """Test resolution using class declarations when no params provided."""

        class TestClass(Declarative):
            __declcomps__ = {'auth', 'persistence'}
            __auth__ = MockAuth
            __persistence__ = MockPersistence
            def _resolveattributes(self, attributes: dict) -> None:
                pass

        instance = TestClass()
        resolved = instance._resolvecomponents()

        # Should use class declarations
        assert isinstance(resolved['auth'], MockAuth)
        assert isinstance(resolved['persistence'], MockPersistence)
        assert resolved['auth'].token == "default-token"
        assert resolved['persistence'].path == "default.json"

    def test_lazy_instantiation_of_classes(self):
        """Test that class declarations are instantiated lazily."""

        instantiation_count = 0

        class CountingAuth(MockAuth):
            def __init__(self):
                nonlocal instantiation_count
                instantiation_count += 1
                super().__init__()

        class TestClass(Declarative):
            __declcomps__ = {'auth'}
            __auth__ = CountingAuth  # Class reference
            def _resolveattributes(self, attributes: dict) -> None:
                pass

        # Class creation shouldn't instantiate
        assert instantiation_count == 0

        instance = TestClass()
        assert instantiation_count == 0

        # Resolution should instantiate
        resolved = instance._resolvecomponents()
        assert instantiation_count == 1
        assert isinstance(resolved['auth'], CountingAuth)

    def test_instance_declarations_used_directly(self):
        """Test that instance declarations are used without instantiation."""

        auth_instance = MockAuth("instance-token")

        class TestClass(Declarative):
            __declcomps__ = {'auth'}
            __auth__ = auth_instance  # Instance
            def _resolveattributes(self, attributes: dict) -> None:
                pass

        instance = TestClass()
        resolved = instance._resolvecomponents()

        # Should be the exact same instance
        assert resolved['auth'] is auth_instance
        assert resolved['auth'].token == "instance-token"

    def test_none_for_undeclared_components(self):
        """Test that undeclared components resolve to None."""

        class TestClass(Declarative):
            __declcomps__ = {'auth', 'persistence', 'backend'}
            __auth__ = MockAuth
            def _resolveattributes(self, attributes: dict) -> None:
                pass
            # persistence and backend not declared

        instance = TestClass()
        resolved = instance._resolvecomponents()

        assert isinstance(resolved['auth'], MockAuth)
        assert resolved['persistence'] is None
        assert resolved['backend'] is None

    def test_constructor_none_doesnt_override_declaration(self):
        """Test that explicit None in constructor doesn't override declarations."""

        class TestClass(Declarative):
            __declcomps__ = {'auth'}
            __auth__ = MockAuth
            def _resolveattributes(self, attributes: dict) -> None:
                pass

        instance = TestClass()
        resolved = instance._resolvecomponents(auth=None)

        # None shouldn't win over declaration
        assert resolved['auth'] is not None

    def test_mixed_constructor_and_declarations(self):
        """Test mixed resolution with some constructor params and some declarations."""

        constructor_auth = MockAuth("constructor")

        class TestClass(Declarative):
            __declcomps__ = {'auth', 'persistence'}
            __auth__ = MockAuth  # Will be overridden
            __persistence__ = MockPersistence  # Will be used
            def _resolveattributes(self, attributes: dict) -> None:
                pass

        instance = TestClass()
        resolved = instance._resolvecomponents(auth=constructor_auth)

        # Constructor param overrides declaration
        assert resolved['auth'] is constructor_auth
        # Declaration used when no constructor param
        assert isinstance(resolved['persistence'], MockPersistence)

    def test_no_declarable_components(self):
        """Test resolution with empty __declcomps__."""

        class TestClass(Declarative):
            __declcomps__ = set()  # No declarable components
            __auth__ = MockAuth  # Should be ignored
            def _resolveattributes(self, attributes: dict) -> None:
                pass

        instance = TestClass()
        resolved = instance._resolvecomponents(auth=MockAuth())

        # Should return empty dict since nothing is declarable
        assert resolved == {}
