# ~/clientfactory/tests/unit/mixins/tiered/test_t1.py
"""
Tier 1 Testing: Offset/Limit Detection + Advanced Param Inference
"""
import pytest
from unittest.mock import Mock

from clientfactory.mixins.iteration.mixin import IterMixin
from clientfactory.mixins.iteration.comps import IterCycle, ErrorHandles, CycleModes
from clientfactory.core.models import MethodConfig, Payload, Param
from clientfactory.core.models.enums import HTTPMethod


class MockBoundMethodT1(IterMixin):
   """Mock bound method for Tier 1 testing."""

   def __init__(self, payload_class=None, path=None):
       super().__init__()
       self._methodconfig = MethodConfig(
           name="test_method",
           method=HTTPMethod.GET,
           path=path or "test/{id}",
           payload=payload_class
       )
       self.call_history = []

   def __call__(self, **kwargs):
       self.call_history.append(kwargs)
       return f"result_for_{kwargs}"


class TestOffsetLimitDetection:
   """Test offset/limit parameter detection and auto-step."""

   def test_discovers_offset_param(self):
       """Test that _discoverparam finds offset parameters."""
       class TestPayload(Payload):
           offset = Param()
           limit = Param(default=20)


       method = MockBoundMethodT1(TestPayload)
       discovered = method._discoverparam()
       assert discovered == 'offset'

   def test_finds_limit_value_from_static(self):
       """Test finding limit value from static params."""
       class TestPayload(Payload):
           offset = Param()
           limit = Param()

       method = MockBoundMethodT1(TestPayload)
       method.withparams(limit=25)

       limit_value = method._findlimitvalue('offset')
       assert limit_value == 25

   def test_finds_limit_value_from_payload_default(self):
       """Test finding limit value from payload default."""
       class TestPayload(Payload):
           offset = Param()
           limit = Param(default=50)

       method = MockBoundMethodT1(TestPayload)
       limit_value = method._findlimitvalue('offset')
       assert limit_value == 50

   def test_auto_step_detection(self):
       """Test automatic step detection for offset/limit."""
       class TestPayload(Payload):
           offset = Param()
           limit = Param(default=20)

       method = MockBoundMethodT1(TestPayload)
       offset_param = method._normalizeparam('offset')

       step = method._findstepvalue(offset_param, None)
       assert step == 20


class TestParameterNormalization:
   """Test parameter normalization and qualified names."""

   def test_normalizes_string_to_param(self):
       """Test string parameter gets normalized to Param object."""
       class TestPayload(Payload):
           brand = Param(mapping={'nike': 'NIKE_ID'})

       method = MockBoundMethodT1(TestPayload)
       normalized = method._normalizeparam('brand')

       assert isinstance(normalized, Param)
       assert normalized.name == 'brand'

   def test_qualified_payload_param(self):
       """Test payload.param qualified name resolution."""
       class TestPayload(Payload):
           brand = Param(mapping={'nike': 'NIKE_ID'})

       method = MockBoundMethodT1(TestPayload, path="items/{brand}")
       normalized = method._normalizeparam('payload.brand')

       assert isinstance(normalized, Param)
       assert hasattr(normalized, 'mapping')
       assert normalized.mapping['nike'] == 'NIKE_ID'

   def test_qualified_path_param(self):
       """Test path.param qualified name resolution."""
       class TestPayload(Payload):
           brand = Param(mapping={'nike': 'NIKE_ID'})

       method = MockBoundMethodT1(TestPayload, path="items/{brand}")
       normalized = method._normalizeparam('path.brand')

       assert isinstance(normalized, Param)
       assert normalized.name == 'brand'
       assert normalized.source == 'brand'

   def test_invalid_qualifier_raises_error(self):
       """Test invalid qualifier raises appropriate error."""
       method = MockBoundMethodT1()

       with pytest.raises(ValueError, match="Invalid qualifier 'invalid'"):
           method._normalizeparam('invalid.param')

   def test_unresolvable_param_raises_error(self):
       """Test unresolvable parameter raises error."""
       method = MockBoundMethodT1()

       with pytest.raises(ValueError, match="Parameter 'nonexistent' not found"):
           method._normalizeparam('nonexistent')


class TestAdvancedParamInference:
   """Test advanced parameter inference and resolution."""

   def test_mapping_resolution(self):
       """Test string values get resolved via mapping."""
       class BrandParam(Param):
           mapping = {'nike': 'NIKE_ID', 'adidas': 'ADIDAS_ID'}
           keysaschoices = False

       method = MockBoundMethodT1()
       resolved = method._resolvemapping('nike', BrandParam())
       assert resolved == 'NIKE_ID'

   def test_keys_as_choices_resolution(self):
       """Test keysaschoices parameter resolution."""
       class BrandParam(Param):
           mapping = {'nike': 'NIKE_ID', 'adidas': 'ADIDAS_ID'}
           keysaschoices = True

       method = MockBoundMethodT1()
       resolved = method._resolvemapping('nike', BrandParam())
       assert resolved == 'nike'  # Returns key, not mapped value

   def test_callable_resolution(self):
       """Test callable value resolution."""
       class BrandParam(Param):
           mapping = {'nike': 'NIKE_ID', 'adidas': 'ADIDAS_ID', 'puma': 'PUMA_ID'}

       method = MockBoundMethodT1()
       resolved = method._resolvecallable(lambda x: x.startswith('a'), BrandParam())
       assert resolved == 'adidas'

   def test_values_all_resolution(self):
       """Test values='all' resolution."""
       class BrandParam(Param):
           mapping = {'nike': 'NIKE_ID', 'adidas': 'ADIDAS_ID'}

           def _availablevalues(self):
               return list(self.mapping.keys())

       method = MockBoundMethodT1()
       resolved = method._resolvevalue('all', BrandParam(), 'values')
       assert resolved == ['nike', 'adidas']

   def test_values_slice_resolution(self):
       """Test values=slice() resolution."""
       class BrandParam(Param):
           mapping = {'nike': 'NIKE_ID', 'adidas': 'ADIDAS_ID', 'puma': 'PUMA_ID'}

           def _availablevalues(self):
               return list(self.mapping.keys())

       method = MockBoundMethodT1()
       resolved = method._resolvevalue(slice(0, 2), BrandParam(), 'values')
       assert len(resolved) == 2
       assert 'nike' in resolved
       assert 'adidas' in resolved

   def test_values_dict_resolution(self):
       """Test values=dict resolution (truthy values)."""
       method = MockBoundMethodT1()
       test_dict = {'nike': True, 'adidas': False, 'puma': True}

       resolved = method._resolvevalue(test_dict, Param(), 'values')
       assert resolved == ['nike', 'puma']

   def test_values_recursive_resolution(self):
       """Test recursive resolution in values list."""
       class BrandParam(Param):
           mapping = {'nike': 'NIKE_ID', 'adidas': 'ADIDAS_ID'}
           keysaschoices = False

       method = MockBoundMethodT1()
       test_values = ['nike', 'adidas']

       resolved = method._resolvevalue(test_values, BrandParam(), 'values')
       assert resolved == ['NIKE_ID', 'ADIDAS_ID']


class TestIntegration:
   """Test full integration of Tier 1 features."""

   def test_full_cycle_creation_with_resolution(self):
       """Test creating cycle with all resolution features."""
       class TestPayload(Payload):
           brand = Param(mapping={'nike': 'NIKE_ID', 'adidas': 'ADIDAS_ID'}, keysaschoices=False)
           offset = Param()
           limit = Param(default=20)


       method = MockBoundMethodT1(TestPayload)

       cycle = method.cycle(
           'brand',
           start='nike',
           end='adidas',
           values=['nike', 'adidas']
       )
       print(f"DEBUG: cycle.values = {cycle.values}, type = {type(cycle.values)}")

       assert cycle.param.name == 'brand'
       assert cycle.start == 'NIKE_ID'
       assert cycle.end == 'ADIDAS_ID'
       assert cycle.values == ['NIKE_ID', 'ADIDAS_ID']

   def test_offset_iteration_with_auto_step(self):
       """Test offset iteration with automatic step detection."""
       class TestPayload(Payload):
           offset = Param()
           limit = Param(default=25)

       method = MockBoundMethodT1(TestPayload)

       cycle = method.cycle('offset', start=0, end=100)
       assert cycle.step == 25  # Auto-detected from limit
