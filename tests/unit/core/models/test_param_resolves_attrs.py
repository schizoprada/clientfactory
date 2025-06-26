# ~/clientfactory/tests/unit/core/models/test_param_resolves_attrs.py

import pytest
from clientfactory.core.models.request import Param
from clientfactory.decorators import param


class TestParamClassAttributeResolution:
   """Test class attribute resolution in Param inheritance."""

   def test_inheritance_preserves_choices(self):
       """Test that choices are preserved through inheritance."""
       class StatusParam(Param):
           choices = ['active', 'inactive', 'pending']

       param_instance = StatusParam()
       assert param_instance.choices == ['active', 'inactive', 'pending']

   def test_inheritance_preserves_mapping(self):
       """Test that mapping is preserved through inheritance."""
       class CategoryParam(Param):
           mapping = {'shoes': 'footwear', 'shirts': 'apparel'}

       param_instance = CategoryParam()
       assert param_instance.mapping == {'shoes': 'footwear', 'shirts': 'apparel'}

   def test_inheritance_preserves_multiple_attrs(self):
       """Test that multiple attributes are preserved through inheritance."""
       class ComplexParam(Param):
           choices = ['a', 'b', 'c']
           mapping = {'x': 1, 'y': 2}
           keysaschoices = False
           valuesaschoices = True

       param_instance = ComplexParam()
       assert param_instance.choices == ['a', 'b', 'c']
       assert param_instance.mapping == {'x': 1, 'y': 2}
       assert param_instance.keysaschoices is False
       assert param_instance.valuesaschoices is True

   def test_inheritance_kwargs_override_class_attrs(self):
       """Test that kwargs override class attributes."""
       class DefaultParam(Param):
           choices = ['default1', 'default2']
           required = True

       param_instance = DefaultParam(choices=['override1', 'override2'], required=False)
       assert param_instance.choices == ['override1', 'override2']
       assert param_instance.required is False

   def test_inheritance_none_kwargs_use_class_attrs(self):
       """Test that None kwargs fall back to class attributes."""
       class DefaultParam(Param):
           choices = ['fallback1', 'fallback2']
           default = 'fallback_value'

       param_instance = DefaultParam(choices=None, default=None)
       assert param_instance.choices == ['fallback1', 'fallback2']
       assert param_instance.default == 'fallback_value'

   def test_inheritance_callable_attrs_preserved(self):
       """Test that callable attributes like transform and mapper are preserved."""
       def custom_transform(x):
           return x.upper()

       def custom_mapper(x):
           return f"mapped_{x}"

       class CallableParam(Param):
           transform = custom_transform
           mapper = custom_mapper

       param_instance = CallableParam()
       assert param_instance.transform == custom_transform
       assert param_instance.mapper == custom_mapper


class TestParamDecoratorCompatibility:
   """Test that decorator usage still works."""

   def test_decorator_preserves_choices(self):
       """Test that @param decorator preserves choices."""
       @param
       class KeywordParam:
           choices = ['public', 'private', 'protected']

       # Should be able to access choices on the class
       assert hasattr(KeywordParam, 'choices')
       assert KeywordParam.choices == ['public', 'private', 'protected']

       # And on instances
       #instance = KeywordParam()
       #assert instance.choices == ['public', 'private', 'protected']

   def test_decorator_with_mapping(self):
       """Test that @param decorator works with mapping."""
       @param
       class StatusParam:
           mapping = {'1': 'active', '0': 'inactive'}
           keysaschoices = True

       instance = StatusParam
       assert instance.mapping == {'1': 'active', '0': 'inactive'}
       assert instance.keysaschoices is True


class TestParamDirectInstantiation:
   """Test that direct instantiation still works."""

   def test_direct_instantiation_with_choices(self):
       """Test direct instantiation with choices."""
       param_instance = Param(choices=['option1', 'option2', 'option3'])
       assert param_instance.choices == ['option1', 'option2', 'option3']

   def test_direct_instantiation_with_mapping(self):
       """Test direct instantiation with mapping."""
       param_instance = Param(mapping={'key1': 'value1', 'key2': 'value2'})
       assert param_instance.mapping == {'key1': 'value1', 'key2': 'value2'}

   def test_direct_instantiation_all_params(self):
       """Test direct instantiation with all parameters."""
       param_instance = Param(
           name='test_param',
           source='test_source',
           target='test_target',
           required=True,
           default='test_default',
           choices=['a', 'b'],
           mapping={'x': 1},
           allownone=False
       )

       assert param_instance.name == 'test_param'
       assert param_instance.source == 'test_source'
       assert param_instance.target == 'test_target'
       assert param_instance.required is True
       assert param_instance.default == 'test_default'
       assert param_instance.choices == ['a', 'b']
       assert param_instance.mapping == {'x': 1}
       assert param_instance.allownone is False


class TestParamClassAttributeEdgeCases:
   """Test edge cases for class attribute resolution."""

   def test_non_construct_attributes_ignored(self):
       """Test that attributes not in __constructs__ are ignored."""
       class NonConstructParam(Param):
           choices = ['valid']
           random_attribute = 'should_be_ignored'

       param_instance = NonConstructParam()
       assert param_instance.choices == ['valid']
       # random_attribute should not be passed to BaseField.__init__
