# tests/unit/core/metas/test_declarative.py
"""
Unit tests for DeclarativeMeta metaclass functionality.
"""
import pytest
from unittest.mock import Mock

from clientfactory.core.metas.declarative import DeclarativeMeta
from clientfactory.core.models import DeclarativeType, DECLARATIVE


class TestDeclarativeMeta:
    """Test DeclarativeMeta metaclass functionality."""

    def test_metaclass_creates_metadata_storage(self):
        """Test that DeclarativeMeta initializes metadata storage attributes."""

        class TestClass(metaclass=DeclarativeMeta):
            pass

        # Check that all metadata storage attributes are created
        assert hasattr(TestClass, '_declmetadata')
        assert hasattr(TestClass, '_declcomponents')
        assert hasattr(TestClass, '_declmethods')

        # Check that they are the right types
        assert isinstance(TestClass._declmetadata, dict)
        assert isinstance(TestClass._declcomponents, dict)
        assert isinstance(TestClass._declmethods, dict)

        # Check that they start empty
        assert TestClass._declmetadata == {}
        assert TestClass._declcomponents == {}
        assert TestClass._declmethods == {}

    def test_component_discovery(self):
        """Test discovery of nested classes with _decltype."""

        class ParentClass(metaclass=DeclarativeMeta):

            class ComponentChild(metaclass=DeclarativeMeta):
                _decltype = DECLARATIVE.COMPONENT

            class RegularChild:
                """Regular class without _decltype should be ignored."""
                pass

            class AnotherComponent(metaclass=DeclarativeMeta):
                _decltype = DECLARATIVE.COMPONENT

        # Check that only classes with _decltype are discovered
        assert 'componentchild' in ParentClass._declcomponents
        assert 'anothercomponent' in ParentClass._declcomponents
        assert 'regularchild' not in ParentClass._declcomponents

        # Check that discovered components are the actual classes
        assert ParentClass._declcomponents['componentchild'] == ParentClass.ComponentChild
        assert ParentClass._declcomponents['anothercomponent'] == ParentClass.AnotherComponent

        # Check that components get parent reference
        assert ParentClass.ComponentChild._parent == ParentClass
        assert ParentClass.AnotherComponent._parent == ParentClass

    def test_method_discovery(self):
        """Test discovery of methods with and without _methodconfig."""

        def method_with_config(self):
            pass
        method_with_config._methodconfig = {'type': 'special'}

        class TestClass(metaclass=DeclarativeMeta):

            def regular_method(self):
                """Regular method without config."""
                pass

            # Assign pre-configured method
            special_method = method_with_config

            def _private_method(self):
                """Private method should be discovered but marked as private."""
                pass

        # Check that all public methods are discovered
        assert 'regular_method' in TestClass._declmethods
        assert 'special_method' in TestClass._declmethods
        assert '_private_method' not in TestClass._declmethods  # Private methods ignored

        # Check method info structure
        regular_info = TestClass._declmethods['regular_method']
        assert 'method' in regular_info
        assert 'config' in regular_info
        assert regular_info['method'] == TestClass.regular_method
        assert regular_info['config'] is None

        special_info = TestClass._declmethods['special_method']
        assert special_info['method'] == TestClass.special_method
        assert special_info['config'] == {'type': 'special'}

    def test_inheritance_metadata_propagation(self):
        """Test that metadata is inherited from parent classes."""

        class BaseClass(metaclass=DeclarativeMeta):
            pass

        # Set metadata on base class
        BaseClass._declmetadata['inherited_key'] = 'inherited_value'
        BaseClass._declmetadata['base_only'] = 'base_value'

        class DerivedClass(BaseClass):
            pass

        # Set some metadata on derived class too
        DerivedClass._declmetadata['derived_key'] = 'derived_value'

        class GrandchildClass(DerivedClass):
            pass

        # Check inheritance chain
        assert DerivedClass._declmetadata['inherited_key'] == 'inherited_value'
        assert DerivedClass._declmetadata['base_only'] == 'base_value'
        assert DerivedClass._declmetadata['derived_key'] == 'derived_value'

        assert GrandchildClass._declmetadata['inherited_key'] == 'inherited_value'
        assert GrandchildClass._declmetadata['base_only'] == 'base_value'
        assert GrandchildClass._declmetadata['derived_key'] == 'derived_value'

        # Check that changes to derived don't affect base
        DerivedClass._declmetadata['new_derived'] = 'new_value'
        assert 'new_derived' not in BaseClass._declmetadata

    def test_multiple_inheritance(self):
        """Test metadata inheritance with multiple base classes."""

        class MixinA(metaclass=DeclarativeMeta):
            pass

        class MixinB(metaclass=DeclarativeMeta):
            pass

        MixinA._declmetadata['from_a'] = 'value_a'
        MixinA._declmetadata['common'] = 'a_value'
        MixinB._declmetadata['from_b'] = 'value_b'
        MixinB._declmetadata['common'] = 'b_value'  # Should not override A

        class Combined(MixinA, MixinB):
            pass

        # Should inherit from both
        assert Combined._declmetadata['from_a'] == 'value_a'
        assert Combined._declmetadata['from_b'] == 'value_b'

        # MRO should determine which value wins for conflicts
        # (MixinA comes first in bases, so it should win)
        assert Combined._declmetadata['common'] == 'a_value'

    def test_component_discovery_with_inheritance(self):
        """Test that component discovery works with inheritance."""

        class BaseClass(metaclass=DeclarativeMeta):

            class BaseComponent(metaclass=DeclarativeMeta):
                _decltype = DECLARATIVE.COMPONENT

        class DerivedClass(BaseClass):

            class DerivedComponent(metaclass=DeclarativeMeta):
                _decltype = DECLARATIVE.COMPONENT

        # Derived class should have both components
        assert 'basecomponent' in DerivedClass._declcomponents
        assert 'derivedcomponent' in DerivedClass._declcomponents

        # Base class should only have its own
        assert 'basecomponent' in BaseClass._declcomponents
        assert 'derivedcomponent' not in BaseClass._declcomponents

    def test_method_discovery_with_inheritance(self):
        """Test that method discovery works with inheritance."""

        def base_special_method(self):
            pass
        base_special_method._methodconfig = {'type': 'base'}

        def derived_special_method(self):
            pass
        derived_special_method._methodconfig = {'type': 'derived'}

        class BaseClass(metaclass=DeclarativeMeta):
            def base_method(self):
                pass

            base_special = base_special_method

        class DerivedClass(BaseClass):
            def derived_method(self):
                pass

            derived_special = derived_special_method

        # Check that derived has both sets of methods
        assert 'base_method' in DerivedClass._declmethods
        assert 'derived_method' in DerivedClass._declmethods
        assert 'base_special' in DerivedClass._declmethods
        assert 'derived_special' in DerivedClass._declmethods

        # Check configs are preserved
        assert DerivedClass._declmethods['base_special']['config']['type'] == 'base'
        assert DerivedClass._declmethods['derived_special']['config']['type'] == 'derived'

    def test_namespace_processing(self):
        """Test that namespace items are processed correctly."""

        class TestClass(metaclass=DeclarativeMeta):
            # Class attributes
            class_attr = "test_value"
            _private_attr = "private_value"

            # Nested component
            class Component(metaclass=DeclarativeMeta):
                _decltype = DECLARATIVE.COMPONENT

            # Regular method
            def method(self):
                pass

            # Property (should be ignored)
            @property
            def prop(self):
                return "property_value"

        # Check that class attributes are preserved
        assert TestClass.class_attr == "test_value"
        assert TestClass._private_attr == "private_value"

        # Check that component was discovered
        assert 'component' in TestClass._declcomponents

        # Check that method was discovered
        assert 'method' in TestClass._declmethods

        # Property should still work normally
        instance = TestClass()
        assert instance.prop == "property_value"

    def test_component_case_handling(self):
        """Test that component names are properly lowercased."""

        class TestClass(metaclass=DeclarativeMeta):

            class MyComplexComponentName(metaclass=DeclarativeMeta):
                _decltype = DECLARATIVE.COMPONENT

            class UPPERCASE_COMPONENT(metaclass=DeclarativeMeta):
                _decltype = DECLARATIVE.COMPONENT

        # Check that names are lowercased
        assert 'mycomplexcomponentname' in TestClass._declcomponents
        assert 'uppercase_component' in TestClass._declcomponents

        # Original class names should still work
        assert TestClass.MyComplexComponentName._decltype == DECLARATIVE.COMPONENT
        assert TestClass.UPPERCASE_COMPONENT._decltype == DECLARATIVE.COMPONENT

    def test_empty_class_processing(self):
        """Test metaclass behavior with empty classes."""

        class EmptyClass(metaclass=DeclarativeMeta):
            pass

        # Should still have metadata storage
        assert hasattr(EmptyClass, '_declmetadata')
        assert hasattr(EmptyClass, '_declcomponents')
        assert hasattr(EmptyClass, '_declmethods')

        # Should all be empty
        assert EmptyClass._declmetadata == {}
        assert EmptyClass._declcomponents == {}
        assert EmptyClass._declmethods == {}

    def test_kwargs_handling(self):
        """Test that metaclass handles **kwargs properly."""

        class TestClass(metaclass=DeclarativeMeta, extra_arg="test"):
            pass

        # Class should be created successfully
        assert TestClass.__name__ == "TestClass"

        # Metadata storage should still be initialized
        assert hasattr(TestClass, '_declmetadata')
        assert hasattr(TestClass, '_declcomponents')
        assert hasattr(TestClass, '_declmethods')
