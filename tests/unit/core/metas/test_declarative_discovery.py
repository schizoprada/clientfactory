# tests/unit/core/metas/test_declarative_discovery.py

import pytest
from unittest.mock import Mock

from clientfactory.core.metas.declarative import DeclarativeMeta
from clientfactory.core.bases import Declarative


class MockAuth:
    """Mock auth class for testing."""
    pass


class MockBackend:
    """Mock backend class for testing."""
    pass


class TestDeclarativeDiscovery:
    """Test declarative component discovery in DeclarativeMeta."""

    def test_discover_dunder_components_class(self):
        """Test discovery of dunder component declarations (class)."""

        class TestClass(Declarative):
            __declcomps__ = {'auth', 'backend'}
            __auth__ = MockAuth
            __backend__ = MockBackend

        # Check components were discovered
        assert 'auth' in TestClass._declcomponents
        assert 'backend' in TestClass._declcomponents

        # Check class storage
        assert TestClass._declcomponents['auth']['type'] == 'class'
        assert TestClass._declcomponents['auth']['value'] == MockAuth
        assert TestClass._declcomponents['backend']['type'] == 'class'
        assert TestClass._declcomponents['backend']['value'] == MockBackend

    def test_discover_dunder_components_instance(self):
        """Test discovery of dunder component declarations (instance)."""

        auth_instance = MockAuth()
        backend_instance = MockBackend()

        class TestClass(Declarative):
            __declcomps__ = {'auth', 'backend'}
            __auth__ = auth_instance
            __backend__ = backend_instance

        # Check instance storage
        assert TestClass._declcomponents['auth']['type'] == 'instance'
        assert TestClass._declcomponents['auth']['value'] is auth_instance
        assert TestClass._declcomponents['backend']['type'] == 'instance'
        assert TestClass._declcomponents['backend']['value'] is backend_instance

    def test_discover_configs(self):
        """Test discovery of config declarations."""

        class TestClass(Declarative):
            __declconfs__ = {'timeout', 'retries'}
            timeout = 30.0
            retries = 3
            ignored_attr = "not in declconfs"

        # Check configs were discovered
        assert TestClass._declconfigs['timeout'] == 30.0
        assert TestClass._declconfigs['retries'] == 3
        assert 'ignored_attr' not in TestClass._declconfigs

    def test_discover_attrs(self):
        """Test discovery of attribute declarations."""

        class TestClass(Declarative):
            __declattrs__ = {'headers', 'cookies'}
            headers = {'User-Agent': 'Test'}
            cookies = {'session': 'abc123'}
            ignored_attr = "not in declattrs"

        # Check attrs were discovered
        assert TestClass._declattrs['headers'] == {'User-Agent': 'Test'}
        assert TestClass._declattrs['cookies'] == {'session': 'abc123'}
        assert 'ignored_attr' not in TestClass._declattrs

    def test_inheritance_of_declarations(self):
        """Test that declarations are inherited from parent classes."""

        class ParentClass(Declarative):
            __declcomps__ = {'auth'}
            __auth__ = MockAuth

        class ChildClass(ParentClass):
            __declcomps__ = {'backend'}
            __backend__ = MockBackend

        # Child should have both parent and own components
        assert 'auth' in ChildClass._declcomponents
        assert 'backend' in ChildClass._declcomponents
        assert ChildClass._declcomponents['auth']['value'] == MockAuth
        assert ChildClass._declcomponents['backend']['value'] == MockBackend

    def test_ignore_undeclared_dunders(self):
        """Test that undeclared dunder attributes are ignored."""

        class TestClass(Declarative):
            __declcomps__ = {'auth'}  # Only auth is declarable
            __auth__ = MockAuth
            __backend__ = MockBackend  # This should be ignored

        # Only auth should be discovered
        assert 'auth' in TestClass._declcomponents
        assert 'backend' not in TestClass._declcomponents

    def test_ignore_callable_attributes(self):
        """Test that callable attributes are not discovered as configs/attrs."""

        def some_method():
            pass

        class TestClass(Declarative):
            __declconfs__ = {'timeout'}
            __declattrs__ = {'headers'}
            timeout = 30.0
            headers = {}
            method_name = some_method  # Should be ignored

        assert TestClass._declconfigs['timeout'] == 30.0
        assert TestClass._declattrs['headers'] == {}
        assert 'method_name' not in TestClass._declconfigs
        assert 'method_name' not in TestClass._declattrs
