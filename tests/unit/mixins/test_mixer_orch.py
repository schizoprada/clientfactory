# ~/clientfactory/tests/unit/mixins/test_mixer_orch.py
import pytest
from unittest.mock import Mock

from clientfactory.core.models.methods import BoundMethod
from clientfactory.core.models import ExecutableRequest, MethodConfig, HTTPMethod
from clientfactory.mixins import IterMixin, PrepMixin
from clientfactory.mixins.core.comps import MixinMetadata, ExecMode, MergeStrategy
from clientfactory.mixins.core.base import BaseMixin
from clientfactory.core.bases.engine import BaseEngine
from clientfactory.core.bases.session import BaseSession
from clientfactory.core.bases.client import BaseClient


class MockEngine(BaseEngine):
   def _setupsession(self, config=None) -> BaseSession:
       return Mock()

   def _makerequest(self, method, url, usesession=True, **kwargs):
       return Mock()


class ConflictingMixin(BaseMixin):
   """Test mixin that conflicts with PrepMixin"""
   __chainedas__ = "conflict"
   __mixmeta__ = MixinMetadata(
       conflicts=["prep"],
       priority=8
   )

   def _exec_(self, conf, **kwargs):
       return f"conflicting result: {conf}"

   def _configure_(self, **kwargs):
       return kwargs


class TransformMixin(BaseMixin):
   """Test mixin that transforms kwargs"""
   __chainedas__ = "transform"
   __mixmeta__ = MixinMetadata(
       mode=ExecMode.TRANSFORM,
       priority=3,
       autoreset=False
   )

   def _exec_(self, conf, **kwargs):
       # Transform kwargs by adding a prefix
       transformed = {f"transformed_{k}": v for k, v in kwargs.items()}
       return {**kwargs, **transformed}

   def _configure_(self, **kwargs):
       return kwargs


class TestMixerOrchestration:
   """Test advanced mixer orchestration behaviors"""

   def setup_method(self):
       """Set up test fixtures"""
       self.mock_func = Mock()
       self.mock_func.__name__ = "test_method"

       # Create BoundMethod that inherits from multiple mixins
       class TestBoundMethod(BoundMethod, ConflictingMixin, TransformMixin):
           pass

       self.bound_method = TestBoundMethod(self.mock_func)

       # Resolve the BoundMethod to fix UNSET parent
       mock_parent = Mock(spec=BaseClient)
       mock_config = MethodConfig(
           name="test_method",
           method=HTTPMethod.GET,
           path="/test"
       )
       self.bound_method._resolvebinding(mock_parent, mock_config)

       # Mock required methods
       mock_request = Mock()
       mock_request.model_dump.return_value = {
           "method": HTTPMethod.GET,
           "url": "https://api.example.com/test",
           "headers": {},
           "cookies": {}
       }

       self.bound_method._getmethodconfig = Mock(return_value=mock_config)
       self.bound_method._getengine = Mock(return_value=MockEngine())
       self.bound_method._preparerequest = Mock(return_value=mock_request)
       self.bound_method.iterate = Mock(return_value=iter([1, 2, 3]))

   def test_conflict_detection(self):
       """Test that mixer detects and prevents conflicting mixins"""
       mixer = self.bound_method.chain

       # First configure prep
       mixer.prep(timeout=30)


       # Should raise error when trying to add conflicting mixin
       with pytest.raises(ValueError):
           mixer.conflict(some_param="value")

   def test_priority_ordering(self):
       """Test that mixins execute in priority order"""
       mixer = self.bound_method.chain

       # Add mixins in random order
       mixer.prep(timeout=30).iter(param="page").transform(prefix="test")

       ordered = mixer._getorder()
       priorities = [mixin.__mixmeta__.priority for mixin in ordered]

       # Should be sorted: transform(3), iter(5), prep(10)
       assert priorities == sorted(priorities)
       assert priorities == [3, 5, 10]

   def test_terminal_mode_execution(self):
       """Test that terminal modes stop execution chain"""
       mixer = self.bound_method.chain

       # Chain transform -> iter -> prep (prep is terminal)
       result = mixer.transform(prefix="test").iter(param="page").prep(timeout=30).execute()

       # Should return ExecutableRequest from prep (terminal)
       assert isinstance(result, ExecutableRequest)

       # Transform should have executed (lower priority)
       # But iter should not have been called since prep is terminal

   def test_deferred_mode_accumulation(self):
       """Test that deferred modes accumulate until final execution"""
       mixer = self.bound_method.chain

       # Chain only deferred mixins
       mixer.iter(param="page").transform(prefix="test")

       # Mock the bound method call
       self.bound_method._func = Mock(return_value="final result")

       result = mixer.execute()

       # Should eventually call the bound method with transformed kwargs
       assert result == "final result"

   def test_transform_mode_modifies_kwargs(self):
       """Test that transform mode modifies kwargs for subsequent mixins"""
       mixer = self.bound_method.chain

       # Create a custom mock to capture the transformed kwargs
       original_call = self.bound_method.__call__
       captured_kwargs = {}

       def capture_call(**kwargs):
           captured_kwargs.update(kwargs)
           return "result"

       self.bound_method._func = capture_call

       # Chain transform then execute
       mixer.transform(key="value").execute(original="param")

       # Should have both original and transformed kwargs
       assert "original" in captured_kwargs
       assert "transformed_original" in captured_kwargs

   def test_auto_reset_behavior(self):
       """Test that mixer resets state after execution when configured"""
       mixer = self.bound_method.chain

       # Configure some mixins
       mixer.prep(timeout=30).iter(param="page")

       # Should have configs
       assert len(mixer._confs) > 0
       assert len(mixer._links) > 0

       # Execute (prep has autoreset=True by default)
       mixer.execute()

       # Should be reset
       assert len(mixer._confs) == 0
       assert len(mixer._links) == 0

   def test_no_auto_reset_when_disabled(self):
       """Test that mixer preserves state when autoreset=False"""
       mixer = self.bound_method.chain

       # Configure transform mixin (has autoreset=False)
       mixer.transform(key="value")

       # Mock the bound method
       self.bound_method._func = Mock(return_value="result")

       # Execute
       mixer.execute()

       # Should still have configs (transform has autoreset=False)
       assert "transform" in mixer._confs

   def test_merge_strategy_application(self):
       """Test that merge strategies work correctly"""
       mixer = self.bound_method.chain

       # Configure same mixin twice with different values
       mixer.iter(param="page", limit=1)
       mixer.iter(param="offset", limit=5)  # Should merge/overwrite based on strategy

       # Check final config
       iter_config = mixer._confs["iter"]

       # Default UPDATE strategy should have last values win
       assert iter_config["limit"] == 5
       assert iter_config["param"] == "offset"

   def test_empty_chain_execution(self):
       """Test execution with no configured mixins"""
       mixer = self.bound_method.chain

       # Mock bound method
       self.bound_method._func = Mock(return_value="direct result")

       # Execute with no mixins configured
       result = mixer.execute(test="param")

       # Should call bound method directly
       assert result == "direct result"
       self.bound_method._func.assert_called_once_with(test="param")

   def test_mixin_discovery(self):
       """Test that mixer discovers all available mixins"""
       mixer = self.bound_method.chain
       discovered = mixer._discovermixins()

       # Should find all mixins in inheritance chain
       mixin_names = {mixin.__name__ for mixin in discovered}
       expected = {"IterMixin", "PrepMixin", "ConflictingMixin", "TransformMixin"}

       assert expected.issubset(mixin_names)

   def test_call_shorthand(self):
       """Test that __call__ is shorthand for execute"""
       mixer = self.bound_method.chain

       # Mock execute method
       mixer.execute = Mock(return_value="execute result")

       # Call mixer directly
       result = mixer(test="param")

       assert result == "execute result"
       mixer.execute.assert_called_once_with(test="param")
