# ~/clientfactory/tests/integration/test_declarative_components.py
import pytest
from unittest.mock import Mock

from clientfactory.core.bases import BaseClient, BaseAuth, BaseSession, BaseEngine
from clientfactory.core.models import AuthConfig, SessionConfig, EngineConfig, ClientConfig


class MockAuth(BaseAuth):
    def _authenticate(self) -> bool:
        return True

    def _applyauth(self, request):
        return request


class MockSession(BaseSession):
    def _setup(self):
        return "mock-session-object"

    def _preparerequest(self, request):
        return request

    def _makerequest(self, request):
        pass

    def _processresponse(self, response):
        return response

    def _cleanup(self) -> None:
        pass

class MockEngine(BaseEngine):
    def _setupsession(self, config=None):
        return MockSession()

    def _makerequest(self, method, url, usesession, **kwargs):
        pass


class MockClient(BaseClient):
    def _initcomps(self):
        pass

    def _registerresource(self, resource, name=None):
        pass

    def _discoverresources(self):
        pass


class TestDeclarativeComponents:
    """Test full declarative component integration."""

    def test_full_component_chain(self):
        """Test complete component chain: Client → Engine → Session → Auth"""

        class TestAuth(MockAuth):
            token = "test-token"
            timeout = 30

        class TestSession(MockSession):
            __auth__ = TestAuth
            headers = {"User-Agent": "TestApp"}
            timeout = 60

        class TestEngine(MockEngine):
            __session__ = TestSession
            poolsize = 20

        class TestClient(MockClient):
            __engine__ = TestEngine
            baseurl = "https://api.test.com"
            timeout = 45

        # Test instantiation
        client = TestClient()

        # Verify component chain
        assert isinstance(client._engine, TestEngine)
        assert isinstance(client._engine._session, TestSession)
        assert isinstance(client._engine._session._auth, TestAuth)

        # Verify declarative attributes
        assert client._engine._session._auth.token == "test-token"
        assert client._engine._session._headers["User-Agent"] == "TestApp"
        assert client._engine._poolsize == 20
        assert client.baseurl == "https://api.test.com"

        # Verify declarative configs
        assert client._engine._session._auth._config.timeout == 30
        assert client._engine._session._config.timeout == 60
        assert client._config.timeout == 45

    def test_constructor_override_chain(self):
        """Test constructor params override declarations throughout chain."""

        class TestAuth(MockAuth):
            token = "declared-token"

        class TestSession(MockSession):
            __auth__ = TestAuth

        class TestClient(MockClient):
            __engine__ = MockEngine

        # Override at different levels
        override_auth = MockAuth()
        override_auth.token = "override-token"

        client = TestClient()
        # TODO: Need to implement session override in engine
        # engine = client._engine
        # session = TestSession(auth=override_auth)

        # For now, just test basic override
        session = TestSession(auth=override_auth)
        assert session._auth is override_auth
        assert session._auth.token == "override-token"

    def test_mixed_declaration_styles(self):
        """Test mixing flat and nested declaration styles."""

        class TestAuth(MockAuth):
            token = "auth-token"

        # Flat style
        class FlatClient(MockClient):
            __auth__ = TestAuth  # Direct auth on client
            baseurl = "https://flat.com"

        # Nested style
        class NestedEngine(MockEngine):
            class NestedSession(MockSession):
                __auth__ = TestAuth

        class NestedClient(MockClient):
            __engine__ = NestedEngine
            baseurl = "https://nested.com"

        flat_client = FlatClient()
        nested_client = NestedClient()

        # Both should work (though flat client's auth might not be wired yet)
        assert flat_client.baseurl == "https://flat.com"
        assert nested_client.baseurl == "https://nested.com"
        assert isinstance(nested_client._engine._session._auth, TestAuth)

    def test_component_lazy_instantiation(self):
        """Test that class declarations are lazily instantiated."""

        instantiation_count = 0

        class CountingAuth(MockAuth):
            def __init__(self, **kwargs):
                nonlocal instantiation_count
                instantiation_count += 1
                super().__init__(**kwargs)

        class TestSession(MockSession):
            __auth__ = CountingAuth  # Class reference



        # Class creation shouldn't instantiate
        assert instantiation_count == 0

        # Instance creation should instantiate once
        session = TestSession()
        assert instantiation_count == 1
        assert isinstance(session._auth, CountingAuth)

        # Multiple instances should instantiate multiple times
        session2 = TestSession()
        assert instantiation_count == 2
