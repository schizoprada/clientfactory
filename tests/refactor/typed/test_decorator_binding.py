# ~/clientfactory/tests/refactor/typed/test_decorator_binding.py
# tests/refactor/typed/test_decorator_binding.py
"""Test that decorators now return properly typed BoundMethod objects."""
import pytest
from unittest.mock import Mock

from clientfactory.core.models import HTTPMethod, MethodConfig
from clientfactory.core.models.methods import BoundMethod
from clientfactory.decorators.http import get, post
from clientfactory.core.bases.client import BaseClient
from clientfactory.core.bases.resource import BaseResource
from clientfactory.core.utils.typed import UNSET


class TestDecoratorBinding:
    """Test that HTTP decorators return BoundMethod objects."""

    def test_decorator_returns_boundmethod(self):
        """Test that @get returns a BoundMethod instance."""
        @get("test")
        def test_method(): pass

        assert isinstance(test_method, BoundMethod)
        assert test_method._parent is UNSET
        assert test_method._resolved is False

    def test_decorator_without_parentheses(self):
        """Test @get without parentheses returns BoundMethod."""
        @get
        def test_method(): pass

        assert isinstance(test_method, BoundMethod)
        assert test_method._parent is UNSET

    def test_client_initialization_resolves_binding(self):
        """Test that client initialization resolves decorated methods."""
        class TestClient(BaseClient):
            baseurl = "https://api.example.com"

            @get("users")
            def get_users(self): pass

            # Mock required abstract methods
            def _initcomps(self): pass
            def _registerresource(self, resource, name=None): pass
            def _discoverresources(self): pass

        # Before init - method should be unresolved BoundMethod
        unresolved = TestClient.get_users
        assert isinstance(unresolved, BoundMethod)
        assert unresolved._parent is UNSET
        assert not unresolved._resolved

        # Mock dependencies
        client = Mock(spec=TestClient)
        client.baseurl = "https://api.example.com"
        client._engine = Mock()
        client._backend = None

        # Test _initmethods resolves the binding
        TestClient._initmethods(client)

        # Should have resolved the method
        resolved_method = getattr(client, 'get_users')
        assert isinstance(resolved_method, BoundMethod)
        assert resolved_method._resolved

    def test_boundmethod_has_mixin_methods(self):
        """Test that BoundMethod has prepare, iterate, cycle methods."""
        @post("test")
        def test_method(): pass

        # Should have mixin methods (even if not resolved)
        assert hasattr(test_method, 'prepare')
        assert hasattr(test_method, 'iterate')
        assert hasattr(test_method, 'cycle')

    def test_calling_unresolved_method_raises(self):
        """Test that calling unresolved BoundMethod raises error."""
        @get("test")
        def test_method(): pass

        with pytest.raises(RuntimeError, match="not resolved"):
            test_method()
