# ~/clientfactory/tests/unit/core/bases/test_property_access.py
import pytest
from unittest.mock import Mock

from clientfactory.core.bases import BaseClient, BaseAuth, BaseSession
from clientfactory.core.bases.declarative import Declarative


class MockAuth(BaseAuth):
    def _authenticate(self) -> bool:
        return True

    def _applyauth(self, request):
        return request



class MockSession(BaseSession):
    def _setup(self):
        return {"mock": "session_obj"}

    def _preparerequest(self, request):
        return request

    def _makerequest(self, request):
        pass

    def _processresponse(self, response):
        return response

    def _cleanup(self) -> None:
        pass

class MockClient(BaseClient):
    def _initcomps(self):
        pass

    def _registerresource(self, resource, name=None):
        pass

    def _discoverresources(self):
        pass


class TestPropertyAccess:
    """Test lowercase/UPPERCASE property access pattern."""

    def test_lowercase_returns_abstraction(self):
        """Test that lowercase names return our abstractions."""

        class TestClient(MockClient):
            __auth__ = MockAuth
            __session__ = MockSession

        client = TestClient()

        # Lowercase should return our abstractions
        auth = client.auth
        session = client.session

        assert isinstance(auth, MockAuth)
        assert isinstance(session, MockSession)

    def test_uppercase_returns_raw_object(self):
        """Test that UPPERCASE names return raw ._obj when available."""

        class TestClient(MockClient):
            __session__ = MockSession  # Has ._obj from _setup()

        client = TestClient()

        # UPPERCASE should return ._obj
        session_obj = client.SESSION
        assert session_obj == {"mock": "session_obj"}

        # Lowercase returns abstraction
        session = client.session
        assert isinstance(session, MockSession)
        assert session._obj == {"mock": "session_obj"}

    def test_uppercase_fallback_when_no_obj(self):
        """Test UPPERCASE falls back to component when no ._obj exists."""

        class TestClient(MockClient):
            __auth__ = MockAuth  # No ._obj in auth

        client = TestClient()

        # UPPERCASE should fallback to component itself
        auth_upper = client.AUTH
        auth_lower = client.auth

        assert auth_upper is auth_lower  # Same object since no ._obj

    def test_normal_attributes_unaffected(self):
        """Test that normal attributes work normally."""

        class TestClient(MockClient):
            baseurl = "https://api.test.com"

        client = TestClient()

        # Normal attributes should work
        assert client.baseurl == "https://api.test.com"
        assert hasattr(client, '_config')
        assert hasattr(client, '_resources')

    def test_nonexistent_attribute_error(self):
        """Test that non-component attributes raise AttributeError."""

        class TestClient(MockClient):
            pass

        client = TestClient()

        with pytest.raises(AttributeError):
            client.nonexistent

        with pytest.raises(AttributeError):
            client.NONEXISTENT

    def test_undeclared_component_error(self):
        """Test accessing undeclared components raises AttributeError."""

        class TestClient(MockClient):
            # backend not in __declcomps__ for BaseClient
            pass

        client = TestClient()

        # These should work (declared components)
        with pytest.raises(AttributeError):
            client.backend  # Not declared, should fail

        with pytest.raises(AttributeError):
            client.BACKEND

    def test_mixed_case_access(self):
        """Test various case combinations."""

        class TestClient(MockClient):
            __auth__ = MockAuth

        client = TestClient()

        # These should work
        assert isinstance(client.auth, MockAuth)
        assert client.AUTH  # Fallback to component

        # These should fail
        with pytest.raises(AttributeError):
            client.Auth  # Mixed case

        with pytest.raises(AttributeError):
            client.aUTH  # Mixed case

    def test_component_without_obj_attribute(self):
        """Test components that don't set ._obj work correctly."""

        class NoObjComponent(Declarative):
            __declcomps__ = set()
            __declattrs__ = set()
            __declconfs__ = set()

            def _resolveattributes(self, attributes):
                pass

        class TestClass(Declarative):
            __declcomps__ = {'comp'}
            __declattrs__ = set()
            __declconfs__ = set()

            def __init__(self):
                components = self._resolvecomponents()
                self._comp = NoObjComponent()

            def _resolveattributes(self, attributes):
                pass

        instance = TestClass()

        # Both should return the same component
        assert instance.comp is instance.COMP
        assert isinstance(instance.comp, NoObjComponent)
