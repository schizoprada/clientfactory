# ~/clientfactory/tests/unit/misc/test_session_initializer.py

import pytest
from unittest.mock import Mock, patch
from clientfactory.core.models import RequestModel, ResponseModel, SessionInitializer, MergeMode
from clientfactory.core.models import HTTP

class TestSessionInitializer:

    def test_basic_initialization(self):
        """Test basic SessionInitializer creation."""
        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(request=request)

        assert initializer.request == request
        assert initializer.headers is True
        assert initializer.cookies is True
        assert initializer.headermode == MergeMode.MERGE
        assert initializer.cookiemode == MergeMode.MERGE

    def test_custom_modes(self):
        """Test SessionInitializer with custom merge modes."""
        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(
            request=request,
            headers=False,
            cookies=True,
            headermode=MergeMode.OVERWRITE,
            cookiemode=MergeMode.IGNORE
        )

        assert initializer.headers is False
        assert initializer.cookies is True
        assert initializer.headermode == MergeMode.OVERWRITE
        assert initializer.cookiemode == MergeMode.IGNORE

    @patch('requests.get')
    def test_execute_success(self, mock_get):
        """Test successful request execution."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Set-Cookie': 'test=value'}
        mock_response.cookies = {'test': 'value'}
        mock_get.return_value = mock_response

        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(request=request)

        with patch.object(ResponseModel, 'FromRequests') as mock_from_requests:
            mock_from_requests.return_value = Mock()
            result = initializer.execute()

            mock_get.assert_called_once()
            mock_response.raise_for_status.assert_called_once()
            mock_from_requests.assert_called_once_with(mock_response)

    def test_extract_both(self):
        """Test extracting both headers and cookies."""
        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(request=request, headers=True, cookies=True)

        response = Mock()
        response.headers = {'Content-Type': 'application/json'}
        response.cookies = {'session': 'abc123'}

        extracted = initializer.extract(response)

        assert 'headers' in extracted
        assert 'cookies' in extracted
        assert extracted['headers'] == {'Content-Type': 'application/json'}
        assert extracted['cookies'] == {'session': 'abc123'}

    def test_extract_headers_only(self):
        """Test extracting headers only."""
        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(request=request, headers=True, cookies=False)

        response = Mock()
        response.headers = {'Content-Type': 'application/json'}
        response.cookies = {'session': 'abc123'}

        extracted = initializer.extract(response)

        assert 'headers' in extracted
        assert 'cookies' not in extracted

    def test_setupdict_merge_mode(self):
        """Test dict setup with merge mode."""
        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(
            request=request,
            headermode=MergeMode.MERGE,
            cookiemode=MergeMode.MERGE
        )

        obj = {'headers': {'existing': 'header'}, 'cookies': {'existing': 'cookie'}}
        extracted = {
            'headers': {'new': 'header'},
            'cookies': {'new': 'cookie'}
        }

        result = initializer._setupdict(obj, extracted)

        assert result['headers'] == {'existing': 'header', 'new': 'header'}
        assert result['cookies'] == {'existing': 'cookie', 'new': 'cookie'}

    def test_setupdict_overwrite_mode(self):
        """Test dict setup with overwrite mode."""
        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(
            request=request,
            headermode=MergeMode.OVERWRITE,
            cookiemode=MergeMode.OVERWRITE
        )

        obj = {'headers': {'existing': 'header'}, 'cookies': {'existing': 'cookie'}}
        extracted = {
            'headers': {'new': 'header'},
            'cookies': {'new': 'cookie'}
        }

        result = initializer._setupdict(obj, extracted)

        assert result['headers'] == {'new': 'header'}
        assert result['cookies'] == {'new': 'cookie'}

    def test_setuptyped_with_session_object(self):
        """Test setup with requests.Session-like object."""
        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(request=request)

        # Mock session object
        session = Mock()
        session.headers = Mock()
        session.cookies = Mock()

        extracted = {
            'headers': {'new': 'header'},
            'cookies': {'new': 'cookie'}
        }

        result = initializer._setuptyped(session, extracted)

        session.headers.update.assert_called_with({'new': 'header'})
        session.cookies.update.assert_called_with({'new': 'cookie'})
        assert result == session

    @patch.object(SessionInitializer, 'execute')
    @patch.object(SessionInitializer, 'extract')
    def test_initialize_dict(self, mock_extract, mock_execute):
        """Test initialize method with dict object."""
        request = RequestModel(method=HTTP.GET, url="https://example.com")
        initializer = SessionInitializer(request=request)

        mock_execute.return_value = Mock()
        mock_extract.return_value = {'headers': {'test': 'value'}}

        obj = {'headers': {}, 'cookies': {}}
        result = initializer.initialize(obj)

        mock_execute.assert_called_once()
        mock_extract.assert_called_once()
        assert 'headers' in result
