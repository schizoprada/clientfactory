# ~/clientfactory/tests/unit/mixins/test_mixer_impls.py
import pytest
from unittest.mock import Mock

from clientfactory.core.models.methods import BoundMethod
from clientfactory.core.models import ExecutableRequest, MethodConfig, HTTPMethod
from clientfactory.mixins import IterMixin, PrepMixin
from clientfactory.core.bases.engine import BaseEngine
from clientfactory.core.bases.session import BaseSession

class MockEngine(BaseEngine):
   def _setupsession(self, config=None) -> BaseSession:
       return Mock()

   def _makerequest(self, method, url, usesession=True, **kwargs):
       return Mock()

class TestMixinImplementations:
   """Test that mixin abstract method implementations work correctly"""

   def setup_method(self):
       """Set up test fixtures"""
       # Create a mock function for BoundMethod
       self.mock_func = Mock()
       self.mock_func.__name__ = "test_method"

       # Create BoundMethod instance
       self.bound_method = BoundMethod(self.mock_func)

       # Mock the required methods for PrepMixin
       self.bound_method._getmethodconfig = Mock(return_value=MethodConfig(
           name="test_method",
           method=HTTPMethod.GET,
           path="/test"
       ))
       self.bound_method._getengine = Mock(return_value=MockEngine())

       # Mock _preparerequest to return proper request data
       mock_request = Mock()
       mock_request.model_dump.return_value = {
           "method": HTTPMethod.GET,
           "url": "https://api.example.com/test",
           "headers": {},
           "cookies": {}
       }
       self.bound_method._preparerequest = Mock(return_value=mock_request)

   def test_prep_mixin_configure(self):
       """Test PrepMixin._configure_ implementation"""
       prep_mixin = PrepMixin()

       config = prep_mixin._configure_(timeout=30, format="json", extra="value")

       assert config == {"timeout": 30, "format": "json", "extra": "value"}

   def test_prep_mixin_exec(self):
       """Test PrepMixin._exec_ implementation"""
       config = {"timeout": 30}
       kwargs = {"format": "json"}

       result = PrepMixin._exec_(self.bound_method, config, **kwargs)

       # Should return ExecutableRequest
       assert isinstance(result, ExecutableRequest)

       # Should have called the preparation methods
       self.bound_method._getmethodconfig.assert_called_once()
       self.bound_method._getengine.assert_called_once()
       self.bound_method._preparerequest.assert_called_once()

   def test_iter_mixin_configure(self):
       """Test IterMixin._configure_ implementation"""
       iter_mixin = IterMixin()

       # Mix of valid and invalid keys
       config = iter_mixin._configure_(
           param="page",
           cycles=None,
           mode="seq",
           invalid_key="should_be_filtered",
           start=1,
           end=10
       )

       # Should only include keys in ITERKEYS
       expected_keys = {"param", "cycles", "mode", "start", "end"}
       assert set(config.keys()) == expected_keys
       assert "invalid_key" not in config

   def test_iter_mixin_exec(self):
       """Test IterMixin._exec_ implementation"""
       # Mock the iterate method
       self.bound_method.iterate = Mock(return_value=iter([1, 2, 3]))

       config = {"param": "page", "start": 1, "end": 3}
       kwargs = {"extra": "value"}

       result = IterMixin._exec_(self.bound_method, config, **kwargs)

       # Should have called iterate with proper parameters
       self.bound_method.iterate.assert_called_once()
       call_args = self.bound_method.iterate.call_args

       # Check that EXECDEFAULTS were applied
       assert call_args.kwargs['param'] == "page"
       assert call_args.kwargs['mode'] is not None  # Should have default
       assert call_args.kwargs['extra'] == "value"  # Extra kwargs passed through

   def test_end_to_end_chaining(self):
       """Test full chain: configure -> execute with both mixins"""
       mixer = self.bound_method.chain

       # Mock iterate method for IterMixin
       self.bound_method.iterate = Mock(return_value=iter([1, 2, 3]))

       # Chain iter then prep
       chained = mixer.iter(param="page", start=1, end=3).prep(timeout=30)

       # Should have both configs stored
       assert "iter" in mixer._confs
       assert "prep" in mixer._confs

       # Execute - should call prep since it's terminal
       result = chained.execute()

       # Should return ExecutableRequest from prep
       assert isinstance(result, ExecutableRequest)

   def test_mixer_respects_priority_order(self):
       """Test that mixins execute in priority order"""
       mixer = self.bound_method.chain

       # Get execution order
       ordered = mixer._getorder()

       if len(ordered) >= 2:
           # Should be sorted by priority (iter=5, prep=10)
           priorities = [mixin.__mixmeta__.priority for mixin in ordered]
           assert priorities == sorted(priorities)
