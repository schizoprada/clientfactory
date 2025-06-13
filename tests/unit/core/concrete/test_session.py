# ~/clientfactory/tests/unit/core/test_session.py
# tests/unit/core/test_session.py
"""
Unit tests for concrete Session implementation.
"""
import pytest
from unittest.mock import Mock, patch

from clientfactory.core.session import Session
from clientfactory.core.models import HTTPMethod, RequestModel, ResponseModel, SessionConfig


class TestSession:
    """Test concrete Session functionality."""

    def test_session_creation(self):
        """Test basic session creation."""
        session = Session()
        assert isinstance(session, Session)
        assert isinstance(session._obj, dict)
        assert 'headers' in session._obj
        assert 'cookies' in session._obj

    def test_session_with_config(self):
        """Test session creation with config."""
        config = SessionConfig(
            timeout=60.0,
            verifyssl=False,
            defaultheaders={"User-Agent": "Test"},
            defaultcookies={"session": "abc123"}
        )
        session = Session(config=config)

        assert session._config.timeout == 60.0
        assert session._config.verifyssl is False

    def test_session_with_headers_and_cookies(self):
        """Test session creation with headers and cookies."""
        session = Session(
            headers={"Authorization": "Bearer token"},
            cookies={"session": "test123"}
        )

        assert session._headers["Authorization"] == "Bearer token"
        assert session._cookies["session"] == "test123"
        assert session._obj['headers']["Authorization"] == "Bearer token"
        assert session._obj['cookies']["session"] == "test123"

    def test_prepare_request_adds_headers(self):
        """Test that prepare request adds session headers."""
        session = Session(headers={"User-Agent": "Test Client"})
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )

        prepared = session.preparerequest(request)

        assert prepared.headers["User-Agent"] == "Test Client"
        assert prepared.url == request.url
        assert prepared.method == request.method

    def test_prepare_request_adds_cookies(self):
        """Test that prepare request adds session cookies."""
        session = Session(cookies={"session": "abc123"})
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )

        prepared = session.preparerequest(request)

        assert prepared.cookies["session"] == "abc123"

    def test_prepare_request_merges_headers(self):
        """Test that prepare request merges headers."""
        session = Session(headers={"User-Agent": "Test Client"})
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            headers={"Authorization": "Bearer token"}
        )

        prepared = session.preparerequest(request)

        assert prepared.headers["User-Agent"] == "Test Client"
        assert prepared.headers["Authorization"] == "Bearer token"

    def test_prepare_request_merges_cookies(self):
        """Test that prepare request merges cookies."""
        session = Session(cookies={"session": "abc123"})
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test",
            cookies={"csrf": "token456"}
        )

        prepared = session.preparerequest(request)

        assert prepared.cookies["session"] == "abc123"
        assert prepared.cookies["csrf"] == "token456"

    def test_process_response_updates_cookies(self):
        """Test that process response updates session cookies."""
        session = Session()
        response = ResponseModel(
            statuscode=200,
            headers={},
            content=b'{"success": true}',
            url="https://api.example.com/test",
            cookies={"new_session": "xyz789"}
        )

        processed = session.processresponse(response)

        assert session._obj['cookies']["new_session"] == "xyz789"
        assert processed is response

    def test_make_request_raises_not_implemented(self):
        """Test that _makerequest raises NotImplementedError."""
        session = Session()
        request = RequestModel(
            method=HTTPMethod.GET,
            url="https://api.example.com/test"
        )

        with pytest.raises(NotImplementedError, match="Session should not make requests directly"):
            session._makerequest(request)

    def test_send_with_auth(self):
        """Test send method with authentication."""
        mock_auth = Mock()
        mock_auth.isauthenticated.return_value = True
        mock_auth.applyauth.return_value = Mock()
        mock_auth.shouldrefresh.return_value = False

        session = Session(auth=mock_auth)

        # Mock the _makerequest to avoid NotImplementedError
        session._makerequest = Mock(return_value=ResponseModel(
            statuscode=200, headers={}, content=b"", url=""
        ))

        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

        response = session.send(request)

        mock_auth.applyauth.assert_called_once()
        session._makerequest.assert_called_once()

    def test_send_with_unauthenticated_auth(self):
        """Test send method with unauthenticated auth that can authenticate."""
        mock_auth = Mock()
        mock_auth.isauthenticated.return_value = False
        mock_auth.authenticate.return_value = True
        mock_auth.applyauth.return_value = Mock()
        mock_auth.shouldrefresh.return_value = False

        session = Session(auth=mock_auth)

        # Mock the _makerequest to avoid NotImplementedError
        session._makerequest = Mock(return_value=ResponseModel(
            statuscode=200, headers={}, content=b"", url=""
        ))

        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

        response = session.send(request)

        mock_auth.authenticate.assert_called_once()
        mock_auth.applyauth.assert_called_once()

    def test_send_without_auth(self):
        """Test send method without authentication."""
        session = Session()

        # Mock the _makerequest to avoid NotImplementedError
        session._makerequest = Mock(return_value=ResponseModel(
            statuscode=200, headers={}, content=b"", url=""
        ))

        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

        response = session.send(request)

        session._makerequest.assert_called_once()

    def test_send_with_auth_refresh(self):
        """Test send method with auth that needs refresh."""
        mock_auth = Mock()
        mock_auth.isauthenticated.return_value = True
        mock_auth.applyauth.return_value = Mock()
        mock_auth.shouldrefresh.return_value = True
        mock_auth.refreshifneeded.return_value = None

        session = Session(auth=mock_auth)

        # Mock the _makerequest to avoid NotImplementedError
        session._makerequest = Mock(return_value=ResponseModel(
            statuscode=200, headers={}, content=b"", url=""
        ))

        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

        response = session.send(request)

        mock_auth.refreshifneeded.assert_called_once()

    def test_cleanup_saves_persistent_state(self):
        """Test that cleanup saves persistent state."""
        session = Session()

        # Mock the save method
        session._savepersistentstate = Mock()

        session._cleanup()

        session._savepersistentstate.assert_called_once()

    def test_closed_session_raises_error(self):
        """Test that closed session raises error on send."""
        session = Session()
        session.close()

        request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

        with pytest.raises(RuntimeError, match="Session is closed"):
            session.send(request)

    def test_context_manager(self):
        """Test session context manager."""
        session = Session()

        with session as ctx_session:
            assert ctx_session is session
            assert session._closed is False

        assert session._closed is True
