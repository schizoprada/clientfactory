# ~/clientfactory/tests/unit/declarative/test_inheritance_chain.py
import pytest
import abc

from clientfactory.core.bases import (
    BaseAuth, BaseBackend, BaseClient,
    BaseEngine, BaseResource, BaseSession,
    Declarative
)


class TestInheritanceChain:
    """Test that all base classes properly inherit from Declarative."""

    def test_base_auth_inheritance(self):
        """Test BaseAuth inherits from Declarative and has declarative capabilities."""
        assert issubclass(BaseAuth, Declarative)
        assert issubclass(BaseAuth, abc.ABC)
        assert hasattr(BaseAuth, '__declcomps__')
        assert hasattr(BaseAuth, '__declattrs__')
        assert hasattr(BaseAuth, '__declconfs__')

    def test_base_backend_inheritance(self):
        """Test BaseBackend inherits from Declarative."""
        assert issubclass(BaseBackend, Declarative)
        assert issubclass(BaseBackend, abc.ABC)
        assert hasattr(BaseBackend, '__declcomps__')
        assert hasattr(BaseBackend, '__declattrs__')
        assert hasattr(BaseBackend, '__declconfs__')

    def test_base_client_inheritance(self):
        """Test BaseClient inherits from Declarative."""
        assert issubclass(BaseClient, Declarative)
        assert issubclass(BaseClient, abc.ABC)
        assert hasattr(BaseClient, '__declcomps__')
        assert hasattr(BaseClient, '__declattrs__')
        assert hasattr(BaseClient, '__declconfs__')

    def test_base_engine_inheritance(self):
        """Test BaseEngine inherits from Declarative."""
        assert issubclass(BaseEngine, Declarative)
        assert issubclass(BaseEngine, abc.ABC)
        assert hasattr(BaseEngine, '__declcomps__')
        assert hasattr(BaseEngine, '__declattrs__')
        assert hasattr(BaseEngine, '__declconfs__')

    def test_base_resource_inheritance(self):
        """Test BaseResource inherits from Declarative."""
        assert issubclass(BaseResource, Declarative)
        assert issubclass(BaseResource, abc.ABC)
        assert hasattr(BaseResource, '__declcomps__')
        assert hasattr(BaseResource, '__declattrs__')
        assert hasattr(BaseResource, '__declconfs__')

    def test_base_session_inheritance(self):
        """Test BaseSession inherits from Declarative."""
        assert issubclass(BaseSession, Declarative)
        assert issubclass(BaseSession, abc.ABC)
        assert hasattr(BaseSession, '__declcomps__')
        assert hasattr(BaseSession, '__declattrs__')
        assert hasattr(BaseSession, '__declconfs__')

    def test_all_have_declarative_methods(self):
        """Test all base classes have access to declarative methods."""
        base_classes = [
            BaseAuth, BaseBackend, BaseClient,
            BaseEngine, BaseResource, BaseSession
        ]

        for base_cls in base_classes:
            # Check they have the resolution method
            assert hasattr(base_cls, '_resolvecomponents')

            # Check they have metadata storage attributes (from metaclass)
            assert hasattr(base_cls, '_declcomponents')
            assert hasattr(base_cls, '_declconfigs')
            assert hasattr(base_cls, '_declattrs')

    def test_declarative_component_sets_defined(self):
        """Test that __declcomps__ sets are properly defined."""
        # BaseAuth - leaf component
        assert BaseAuth.__declcomps__ == set()

        # BaseSession - can declare auth + persistence
        assert 'auth' in BaseSession.__declcomps__
        assert 'persistence' in BaseSession.__declcomps__

        # BaseEngine - can declare session + what session can declare
        assert 'session' in BaseEngine.__declcomps__
        assert 'auth' in BaseEngine.__declcomps__
        assert 'persistence' in BaseEngine.__declcomps__

        # BaseClient - can declare everything
        assert 'engine' in BaseClient.__declcomps__
        assert 'backend' in BaseClient.__declcomps__
        assert 'auth' in BaseClient.__declcomps__

    def test_can_create_declarative_subclasses(self):
        """Test that users can create declarative subclasses."""

        class MockAuth:
            pass

        # Let's test with a class that can actually declare things
        class TestSession(BaseSession):
            __auth__ = MockAuth
            headers = {"User-Agent": "Test"}
            timeout = 30.0

        # These should be discovered
        assert 'auth' in TestSession._declcomponents
        assert TestSession._declattrs.get('headers') == {"User-Agent": "Test"}
        assert TestSession._declconfigs.get('timeout') == 30.0

    def test_metaclass_applied_correctly(self):
        """Test that DeclarativeMeta is applied to all base classes."""
        from clientfactory.core.metas.declarative import DeclarativeMeta

        base_classes = [
            BaseAuth, BaseBackend, BaseClient,
            BaseEngine, BaseResource, BaseSession
        ]

        for base_cls in base_classes:
            assert isinstance(base_cls, DeclarativeMeta)
