# tests/unit/core/bases/test_declarative.py
"""
Unit tests for declarative base functionality.
"""
import pytest
from unittest.mock import Mock

from clientfactory.core.bases.declarative import Declarative
from clientfactory.core.models import DeclarativeType, DECLARATIVE


class TestDeclarative:
    """Test declarative base class functionality."""

    def test_metaclass_initialization(self):
        """Test that DeclarativeMeta properly initializes metadata storage."""

        class TestComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

        # Check that metadata storage is initialized
        assert hasattr(TestComponent, '_declmetadata')
        assert hasattr(TestComponent, '_declcomponents')
        assert hasattr(TestComponent, '_declmethods')
        assert isinstance(TestComponent._declmetadata, dict)
        assert isinstance(TestComponent._declcomponents, dict)
        assert isinstance(TestComponent._declmethods, dict)

    def test_metadata_management(self):
        """Test metadata getting and setting."""

        class TestComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

        # Test setting metadata
        TestComponent.setmetadata('test_key', 'test_value')
        assert TestComponent.getmetadata('test_key') == 'test_value'

        # Test getting nonexistent metadata with default
        assert TestComponent.getmetadata('nonexistent') is None
        assert TestComponent.getmetadata('nonexistent', 'default') == 'default'

    def test_component_discovery(self):
        """Test nested component discovery."""

        class ParentComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

            class ChildComponent(Declarative):
                _decltype = DECLARATIVE.COMPONENT

        # Check that child component is discovered
        components = ParentComponent.getcomponents()
        assert 'childcomponent' in components
        assert components['childcomponent'] == ParentComponent.ChildComponent

        # Test getting specific component
        child = ParentComponent.getcomponent('childcomponent')
        assert child == ParentComponent.ChildComponent

        # Test getting nonexistent component
        assert ParentComponent.getcomponent('nonexistent') is None

    def test_method_discovery(self):
        """Test declarative method discovery."""

        # Create a method with config before class definition
        def special_method_with_config(self):
            """Method with special config."""
            pass
        special_method_with_config._methodconfig = {'type': 'special'}

        class TestComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

            def regular_method(self):
                """Regular method without special attributes."""
                pass

            # Assign the pre-configured method
            special_method = special_method_with_config

        # Check that methods are discovered
        methods = TestComponent.getmethods()
        assert 'regular_method' in methods
        assert 'special_method' in methods

        # Check method info structure
        regular_info = methods['regular_method']
        assert 'method' in regular_info
        assert 'config' in regular_info
        assert regular_info['method'] == TestComponent.regular_method
        assert regular_info['config'] is None

        special_info = methods['special_method']
        assert special_info['config'] == {'type': 'special'}

        # Test getting specific method
        method_info = TestComponent.getmethod('special_method')
        assert method_info == special_info

        # Test getting nonexistent method
        assert TestComponent.getmethod('nonexistent') is None

    def test_inheritance(self):
        """Test metadata inheritance from parent classes."""

        class BaseComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

        # Set metadata on base class
        BaseComponent.setmetadata('inherited_key', 'inherited_value')

        class DerivedComponent(BaseComponent):
            pass

        # Check that derived class inherits metadata
        assert DerivedComponent.getmetadata('inherited_key') == 'inherited_value'

        # Check that setting on derived doesn't affect base
        DerivedComponent.setmetadata('derived_key', 'derived_value')
        assert BaseComponent.getmetadata('derived_key') is None
        assert DerivedComponent.getmetadata('derived_key') == 'derived_value'

    def test_component_case_insensitive_access(self):
        """Test that component access is case-insensitive."""

        class ParentComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

            class MyChildComponent(Declarative):
                _decltype = DECLARATIVE.COMPONENT

        # Test various case combinations
        assert ParentComponent.getcomponent('mychildcomponent') == ParentComponent.MyChildComponent
        assert ParentComponent.getcomponent('MYCHILDCOMPONENT') == ParentComponent.MyChildComponent
        assert ParentComponent.getcomponent('MyChildComponent') == ParentComponent.MyChildComponent

    def test_private_methods_ignored(self):
        """Test that private methods are not discovered."""

        class TestComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

            def _private_method(self):
                pass

            def __dunder_method__(self):
                pass

            def public_method(self):
                pass

        methods = TestComponent.getmethods()
        assert 'public_method' in methods
        assert '_private_method' not in methods
        assert '__dunder_method__' not in methods

    def test_nested_component_parent_reference(self):
        """Test that nested components get parent reference."""

        class ParentComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

            class ChildComponent(Declarative):
                _decltype = DECLARATIVE.COMPONENT

        # Check that child has parent reference
        assert hasattr(ParentComponent.ChildComponent, '_parent')
        assert ParentComponent.ChildComponent._parent == ParentComponent

    def test_multiple_inheritance(self):
        """Test declarative behavior with multiple inheritance."""

        class MixinA(Declarative):
            _decltype = DECLARATIVE.COMPONENT

        class MixinB(Declarative):
            _decltype = DECLARATIVE.COMPONENT

        MixinA.setmetadata('from_a', 'value_a')
        MixinB.setmetadata('from_b', 'value_b')

        class CombinedComponent(MixinA, MixinB):
            pass

        # Should inherit from both parents
        assert CombinedComponent.getmetadata('from_a') == 'value_a'
        assert CombinedComponent.getmetadata('from_b') == 'value_b'

    def test_component_without_decltype(self):
        """Test that components without _decltype are not discovered."""

        class ParentComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

            class RegularClass:
                """Regular class without _decltype."""
                pass

            class ComponentClass(Declarative):
                _decltype = DECLARATIVE.COMPONENT

        components = ParentComponent.getcomponents()
        assert 'componentclass' in components
        assert 'regularclass' not in components

    def test_empty_component_collections(self):
        """Test behavior with no components or methods."""

        class EmptyComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

        assert EmptyComponent.getcomponents() == {}
        assert EmptyComponent.getmethods() == {}
        assert EmptyComponent.getcomponent('anything') is None
        assert EmptyComponent.getmethod('anything') is None

    def test_method_config_after_creation(self):
        """Test that we can set method config after class creation."""

        class TestComponent(Declarative):
            _decltype = DECLARATIVE.COMPONENT

            def test_method(self):
                pass

        # This should work for dynamically added configs
        TestComponent.test_method._methodconfig = {'dynamic': True}

        # The metaclass discovery happens at class creation time,
        # so we need to manually update the methods dict for this case
        TestComponent._declmethods['test_method'] = {
            'method': TestComponent.test_method,
            'config': {'dynamic': True}
        }

        method_info = TestComponent.getmethod('test_method')
        assert method_info['config'] == {'dynamic': True}
