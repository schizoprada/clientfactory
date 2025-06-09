# tests/unit/engines/test_requests.py
"""
Tests for RequestsEngine implementation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests as rq

from clientfactory.engines.requestslib import RequestsEngine, RequestsSession
from clientfactory.core.models import (
    HTTPMethod, RequestModel, ResponseModel,
    EngineConfig, SessionConfig
)

class TestRequestsSession:
    """Test RequestsSession implementation"""

    def test_setup_creates_session(self):
        """Test that _setup creates requests.Session"""
        config = SessionConfig()
        session = RequestsSession(config=config)

        assert isinstance(session._obj, rq.Session)

    def test_setup_applies_headers(self):
        """Test that session headers are applied"""
        config = SessionConfig(defaultheaders={"User-Agent": "Test"})
        session = RequestsSession(config=config)

        assert "User-Agent" in session._obj.headers
        assert session._obj.headers["User-Agent"] == "Test"

    def test_setup_applies_cookies(self):
        """Test that session cookies are applied"""
        config = SessionConfig(defaultcookies={"session": "123"})
        session = RequestsSession(config=config)

        assert "session" in session._obj.cookies
        assert session._obj.cookies["session"] == "123"

    def test_setup_configures_retries(self):
        """Test that retry adapter is configured"""
        config = SessionConfig(maxretries=5)
        session = RequestsSession(config=config)

        # Check that adapters were mounted
        assert "http://" in session._obj.adapters
        assert "https://" in session._obj.adapters

    @patch('requests.Session.request')
    def test_makerequest_calls_session(self, mock_request):
        """Test that _makerequest calls session.request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b"test"
        mock_response.url = "http://test.com"
        mock_response.cookies = {}
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_request.return_value = mock_response

        session = RequestsSession()
        request = RequestModel(method=HTTPMethod.GET, url="http://test.com")

        response = session._makerequest(request)

        mock_request.assert_called_once()
        assert isinstance(response, ResponseModel)

    def test_cleanup_closes_session(self):
        """Test that cleanup closes underlying session"""
        session = RequestsSession()
        mock_close = Mock()
        session._obj.close = mock_close

        session._cleanup()

        mock_close.assert_called_once()

class TestRequestsEngine:
    """Test RequestsEngine implementation"""

    def test_init_creates_session(self):
        """Test that engine creates session on init"""
        engine = RequestsEngine()

        assert isinstance(engine._session, RequestsSession)
        assert isinstance(engine._session._obj, rq.Session)

    def test_init_with_custom_session(self):
        """Test engine with pre-configured session"""
        custom_session = RequestsSession()
        engine = RequestsEngine(session=custom_session)

        assert engine._session is custom_session

    def test_setupsession_cascades_config(self):
        """Test that session config is cascaded from engine"""
        engine_config = EngineConfig(verify=False, timeout=60.0, cascade=True)
        engine = RequestsEngine(config=engine_config)

        session_config = engine._session._config
        assert session_config.verifyssl == False
        assert session_config.timeout == 60.0

    def test_setupsession_no_cascade(self):
        """Test session config without cascade"""
        engine_config = EngineConfig(verify=False, timeout=60.0, cascade=False)
        engine = RequestsEngine(config=engine_config)

        session_config = engine._session._config
        # Should use SessionConfig defaults
        assert session_config.verifyssl == True
        assert session_config.timeout == 30.0

    def test_setupsession_with_provided_config(self):
        """Test session setup with provided SessionConfig"""
        session_config = SessionConfig(timeout=45.0, verifyssl=False)
        engine = RequestsEngine(sessionconfig=session_config)

        assert engine._session._config.timeout == 45.0
        assert engine._session._config.verifyssl == False

    @patch('requests.request')
    def test_makerequest_direct(self, mock_request):
        """Test direct request without session"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.content = b"test"
        mock_response.url = "http://test.com"
        mock_response.cookies = {}
        mock_response.elapsed.total_seconds.return_value = 1.0
        mock_request.return_value = mock_response

        engine = RequestsEngine()

        response = engine._makerequest(
            HTTPMethod.GET,
            "http://test.com",
            usesession=False
        )

        mock_request.assert_called_once_with(
            method="GET",
            url="http://test.com"
        )
        assert isinstance(response, ResponseModel)

    def test_makerequest_with_session(self):
        """Test request using session"""
        engine = RequestsEngine()

        # Mock the session's send method
        mock_response = ResponseModel(
            statuscode=200,
            headers={},
            content=b"test",
            url="http://test.com"
        )
        engine._session.send = Mock(return_value=mock_response)

        response = engine._makerequest(
            HTTPMethod.GET,
            "http://test.com",
            usesession=True
        )

        engine._session.send.assert_called_once()
        assert response is mock_response

    def test_convenience_methods(self):
        """Test convenience methods call request properly"""
        engine = RequestsEngine()
        engine.request = Mock(return_value=Mock())

        engine.get("http://test.com")
        engine.request.assert_called_with(HTTPMethod.GET, "http://test.com")

        engine.post("http://test.com", data="test")
        engine.request.assert_called_with(HTTPMethod.POST, "http://test.com", data="test")

    def test_send_method(self):
        """Test send method with RequestModel"""
        engine = RequestsEngine()
        request = RequestModel(method=HTTPMethod.GET, url="http://test.com")

        engine._makerequest = Mock(return_value=Mock())

        engine.send(request)

        engine._makerequest.assert_called_once()
        args = engine._makerequest.call_args
        assert args[0][0] == HTTPMethod.GET  # method
        assert args[0][1] == "http://test.com"  # url
        assert args[0][2] == True  # usesession

    def test_close_cleanup(self):
        """Test engine close cleans up resources"""
        engine = RequestsEngine()
        engine._session._cleanup = Mock()

        engine.close()

        assert engine._closed == True

class TestIntegration:
    """Integration tests"""

    @patch('requests.Session.request')
    def test_full_request_flow(self, mock_request):
        """Test complete request flow through engine and session"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.content = b'{"test": "data"}'
        mock_response.url = "http://test.com/api"
        mock_response.cookies = {}
        mock_response.elapsed.total_seconds.return_value = 0.5
        mock_request.return_value = mock_response

        engine_config = EngineConfig(timeout=30.0, verify=True)
        engine = RequestsEngine(config=engine_config)

        request = RequestModel(
            method=HTTPMethod.GET,
            url="http://test.com/api",
            headers={"Accept": "application/json"}
        )

        response = engine.send(request)

        assert response.statuscode == 200
        assert response.url == "http://test.com/api"
        assert response.ok == True
        mock_request.assert_called_once()
