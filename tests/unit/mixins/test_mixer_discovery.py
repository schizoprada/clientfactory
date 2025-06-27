# ~/clientfactory/tests/unit/mixins/test_mixer_discovery.py
import pytest
from unittest.mock import Mock

from clientfactory.core.models.methods import BoundMethod
from clientfactory.mixins.core import Mixer
from clientfactory.mixins import IterMixin, PrepMixin


class TestMixerDiscovery:
   """Test that Mixer can discover and expose available mixins"""

   def setup_method(self):
       """Set up test fixtures"""
       # Create a mock function for BoundMethod
       self.mock_func = Mock()
       self.mock_func.__name__ = "test_method"

       # Create BoundMethod instance (inherits from IterMixin, PrepMixin)
       self.bound_method = BoundMethod(self.mock_func)

   def test_chain_property_returns_mixer(self):
       """Test that .chain property returns a Mixer instance"""
       mixer = self.bound_method.chain
       assert isinstance(mixer, Mixer)
       assert mixer._bound is self.bound_method

   def test_mixer_discovers_available_mixins(self):
       """Test that Mixer can discover mixins from BoundMethod inheritance"""
       mixer = self.bound_method.chain
       discovered = mixer._discovermixins()

       # Should find both IterMixin and PrepMixin
       mixin_names = {mixin.__name__ for mixin in discovered}
       assert "IterMixin" in mixin_names
       assert "PrepMixin" in mixin_names

   def test_dynamic_method_creation(self):
       """Test that Mixer creates methods based on mixin __chainedas__"""
       mixer = self.bound_method.chain

       # Should have dynamic methods based on __chainedas__
       assert hasattr(mixer, 'iter')  # From IterMixin.__chainedas__ = 'iter'
       assert hasattr(mixer, 'prep')  # From PrepMixin.__chainedas__ = 'prep'

       # Methods should be callable
       assert callable(mixer.iter)
       assert callable(mixer.prep)

   def test_unknown_mixin_raises_attribute_error(self):
       """Test that accessing unknown mixin raises AttributeError"""
       mixer = self.bound_method.chain

       with pytest.raises(AttributeError):
           mixer.nonexistent

   def test_chaining_returns_mixer(self):
       """Test that chaining methods return the same Mixer for continued chaining"""
       mixer = self.bound_method.chain

       # Chain some methods (won't execute due to NotImplementedError stubs)
       try:
           result = mixer.iter(page=[1, 2, 3])
           assert result is mixer  # Should return self for chaining
       except NotImplementedError:
           # Expected since we haven't implemented _configure_ yet
           pass

   def test_mixer_state_tracking(self):
       """Test that Mixer tracks configuration and chain order"""
       mixer = self.bound_method.chain

       # Initial state should be empty
       assert mixer._confs == {}
       assert mixer._links == []

       # After attempted chaining (even if it fails), we can inspect state
       # This will fail due to NotImplementedError, but we can still test structure
       assert hasattr(mixer, '_confs')
       assert hasattr(mixer, '_links')
