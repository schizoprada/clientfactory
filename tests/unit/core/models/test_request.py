# ~/clientfactory/tests/unit/core/models/test_request.py
"""
Unit tests for request and response models.
"""
import pytest
from unittest.mock import Mock
from clientfactory.core.models import RequestModel, ResponseModel, Param, HTTPMethod


class TestRequestModel:
   """Test RequestModel functionality."""

   def test_request_creation(self):
       """Test basic request creation."""
       request = RequestModel(
           method=HTTPMethod.GET,
           url="https://api.example.com/users"
       )

       assert request.method == HTTPMethod.GET
       assert request.url == "https://api.example.com/users"
       assert request.headers == {}
       assert request.params == {}
       assert request.allowredirects is True
       assert request.verifyssl is True

   def test_request_with_all_fields(self):
       """Test request creation with all fields."""
       headers = {"Authorization": "Bearer token"}
       params = {"limit": 10}
       cookies = {"session": "abc123"}

       request = RequestModel(
           method=HTTPMethod.POST,
           url="https://api.example.com/users",
           headers=headers,
           params=params,
           cookies=cookies,
           json={"name": "John"},
           timeout=30.0,
           allowredirects=False,
           verifyssl=False
       )

       assert request.method == HTTPMethod.POST
       assert request.headers == headers
       assert request.params == params
       assert request.cookies == cookies
       assert request.json == {"name": "John"}
       assert request.timeout == 30.0
       assert request.allowredirects is False
       assert request.verifyssl is False

   def test_request_method_string_conversion(self):
       """Test method string to enum conversion."""
       request = RequestModel(method="get", url="https://api.example.com")
       assert request.method == HTTPMethod.GET

       request = RequestModel(method="POST", url="https://api.example.com")
       assert request.method == HTTPMethod.POST

   def test_request_validation_empty_url(self):
       """Test validation fails for empty URL."""
       with pytest.raises(ValueError, match="URL is required"):
           RequestModel(method=HTTPMethod.GET, url="")

   def test_request_validation_json_and_data(self):
       """Test validation fails when both json and data provided."""
       with pytest.raises(ValueError, match="Cannot specify both 'json' and 'data'"):
           RequestModel(
               method=HTTPMethod.POST,
               url="https://api.example.com",
               json={"key": "value"},
               data=b"raw data"
           )

   def test_request_validation_get_with_body(self):
       """Test validation fails for GET with body."""
       with pytest.raises(ValueError, match="GET requests cannot have body"):
           RequestModel(
               method=HTTPMethod.GET,
               url="https://api.example.com",
               json={"key": "value"}
           )

   def test_request_validation_negative_timeout(self):
       """Test validation fails for negative timeout."""
       with pytest.raises(ValueError, match="Timeout must be positive"):
           RequestModel(
               method=HTTPMethod.GET,
               url="https://api.example.com",
               timeout=-1.0
           )

   def test_request_with_params(self):
       """Test withparams method."""
       request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

       new_request = request.withparams({"limit": 10, "offset": 0})

       # Original unchanged
       assert request.params == {}

       # New request has params
       assert new_request.params == {"limit": 10, "offset": 0}
       assert new_request.url == request.url
       assert new_request.method == request.method

   def test_request_with_headers(self):
       """Test withheaders method."""
       request = RequestModel(
           method=HTTPMethod.GET,
           url="https://api.example.com",
           headers={"Accept": "application/json"}
       )

       new_request = request.withheaders({"Authorization": "Bearer token"})

       # Headers are merged
       expected = {"Accept": "application/json", "Authorization": "Bearer token"}
       assert new_request.headers == expected

       # Original unchanged
       assert request.headers == {"Accept": "application/json"}

   def test_request_with_auth(self):
       """Test withauth method."""
       request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")

       new_request = request.withauth("Authorization", "Bearer token123")

       assert new_request.headers == {"Authorization": "Bearer token123"}
       assert request.headers == {}  # Original unchanged

   def test_request_with_cookies(self):
       """Test withcookies method."""
       request = RequestModel(
           method=HTTPMethod.GET,
           url="https://api.example.com",
           cookies={"session": "abc"}
       )

       new_request = request.withcookies({"csrf": "xyz123"})

       expected = {"session": "abc", "csrf": "xyz123"}
       assert new_request.cookies == expected
       assert request.cookies == {"session": "abc"}  # Original unchanged

   def test_request_to_kwargs(self):
       """Test tokwargs method."""
       request = RequestModel(
           method=HTTPMethod.POST,
           url="https://api.example.com",
           headers={"Content-Type": "application/json"},
           params={"limit": 10},
           json={"name": "John"},
           timeout=30.0,
           allowredirects=False,
           verifyssl=True
       )

       kwargs = request.tokwargs()

       expected = {
           'headers': {"Content-Type": "application/json"},
           'params': {"limit": 10},
           'cookies': {},
           'timeout': 30.0,
           'allow_redirects': False,
           'verify': True,
           'json': {"name": "John"}
       }

       assert kwargs == expected

   def test_request_to_kwargs_with_data(self):
       """Test tokwargs with data instead of json."""
       request = RequestModel(
           method=HTTPMethod.POST,
           url="https://api.example.com",
           data=b"raw data"
       )

       kwargs = request.tokwargs()
       assert 'data' in kwargs
       assert kwargs['data'] == b"raw data"
       assert 'json' not in kwargs

   def test_request_computed_fields(self):
       """Test computed properties."""
       # Request without body
       request = RequestModel(method=HTTPMethod.GET, url="https://api.example.com")
       assert request.hasbody is False
       assert request.contenttype is None

       # Request with JSON body
       request_json = RequestModel(
           method=HTTPMethod.POST,
           url="https://api.example.com",
           json={"key": "value"},
           headers={"Content-Type": "application/json"}
       )
       assert request_json.hasbody is True
       assert request_json.contenttype == "application/json"

       # Request with data body
       request_data = RequestModel(
           method=HTTPMethod.POST,
           url="https://api.example.com",
           data=b"raw data"
       )
       assert request_data.hasbody is True


class TestResponseModel:
   """Test ResponseModel functionality."""

   def test_response_creation(self):
       """Test basic response creation."""
       response = ResponseModel(
           statuscode=200,
           headers={"Content-Type": "application/json"},
           content=b'{"message": "success"}',
           url="https://api.example.com/users"
       )

       assert response.statuscode == 200
       assert response.headers == {"Content-Type": "application/json"}
       assert response.content == b'{"message": "success"}'
       assert response.url == "https://api.example.com/users"

   def test_response_ok_property(self):
       """Test ok property for various status codes."""
       # Success codes
       assert ResponseModel(statuscode=200, headers={}, content=b"", url="").ok is True
       assert ResponseModel(statuscode=201, headers={}, content=b"", url="").ok is True
       assert ResponseModel(statuscode=299, headers={}, content=b"", url="").ok is True

       # Error codes
       assert ResponseModel(statuscode=400, headers={}, content=b"", url="").ok is False
       assert ResponseModel(statuscode=404, headers={}, content=b"", url="").ok is False
       assert ResponseModel(statuscode=500, headers={}, content=b"", url="").ok is False

   def test_response_text_property(self):
       """Test text property."""
       response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"message": "hello"}',
           url=""
       )

       assert response.text == '{"message": "hello"}'

   def test_response_json_method(self):
       """Test json parsing."""
       response = ResponseModel(
           statuscode=200,
           headers={"Content-Type": "application/json"},
           content=b'{"message": "hello", "count": 42}',
           url=""
       )

       data = response.json()
       assert data == {"message": "hello", "count": 42}

       # Second call should return cached result
       data2 = response.json()
       assert data2 == {"message": "hello", "count": 42}

   def test_response_json_invalid(self):
       """Test json parsing with invalid JSON."""
       response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'invalid json',
           url=""
       )

       with pytest.raises(ValueError, match="Invalid JSON"):
           response.json()

   def test_response_raise_for_status(self):
       """Test raiseforstatus method."""
       # Success response should not raise
       success_response = ResponseModel(statuscode=200, headers={}, content=b"", url="")
       success_response.raiseforstatus()  # Should not raise

       # Error response should raise
       error_response = ResponseModel(statuscode=404, headers={}, content=b"", url="https://api.example.com")
       with pytest.raises(Exception, match="HTTP 404 Error"):
           error_response.raiseforstatus()

   def test_response_extract_json_path(self):
       """Test extract method with JSON paths."""
       response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"data": {"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]}}',
           url=""
       )

       # Simple path
       assert response.extract("data") == {"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]}

       # Nested path
       users = response.extract("data.users")
       assert len(users) == 2
       assert users[0]["name"] == "John"

       # Array access
       first_user = response.extract("data.users[0]")
       assert first_user == {"id": 1, "name": "John"}

       # Nested with array
       assert response.extract("data.users[1].name") == "Jane"

       # Non-existent path with default
       assert response.extract("data.missing", "default") == "default"

   def test_response_extract_headers(self):
       """Test extract method with headers."""
       response = ResponseModel(
           statuscode=200,
           headers={"Content-Type": "application/json", "X-Rate-Limit": "100"},
           content=b'{}',
           url=""
       )

       assert response.extract("headers.Content-Type") == "application/json"
       assert response.extract("headers.X-Rate-Limit") == "100"
       assert response.extract("headers.Missing", "default") == "default"

   def test_response_extract_invalid_path(self):
       """Test extract with invalid paths returns default."""
       response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"data": {}}',
           url=""
       )

       assert response.extract("missing.path") is None
       assert response.extract("missing.path", "fallback") == "fallback"
       assert response.extract("data.missing[0]", "fallback") == "fallback"

   def test_response_from_requests(self):
       """Test FromRequests class method."""
       # Mock requests.Response
       mock_response = Mock()
       mock_response.status_code = 200
       mock_response.headers = {"Content-Type": "application/json"}
       mock_response.content = b'{"success": true}'
       mock_response.url = "https://api.example.com/test"
       mock_response.cookies = {"session": "abc123"}
       mock_response.elapsed.total_seconds.return_value = 0.5

       response = ResponseModel.FromRequests(mock_response)

       assert response.statuscode == 200
       assert response.headers == {"Content-Type": "application/json"}
       assert response.content == b'{"success": true}'
       assert response.url == "https://api.example.com/test"
       assert response.cookies == {"session": "abc123"}
       assert response.elapsedtime == 0.5


class TestParam:
   """Test Param functionality."""

   def test_param_creation(self):
       """Test basic param creation."""
       param = Param(name="test", source="field", target="output")

       assert param.name == "test"
       assert param.source == "field"
       assert param.target == "output"
       assert param.required is False
       assert param.default is None

   def test_param_inherits_from_schematix_field(self):
       """Test Param inherits from schematix Field."""
       import schematix as sex
       param = Param()
       assert isinstance(param, sex.Field)

   def test_param_set_name_with_none(self):
       """Test __set_name__ when name is None."""
       param = Param()

       # Simulate metaclass calling __set_name__
       param.__set_name__(object, "user_id")

       assert param.name == "user_id"
       assert param.target == "user_id"  # Should default to name

   def test_param_set_name_with_existing_name(self):
       """Test __set_name__ when name already exists."""
       param = Param(name="existing_name")

       param.__set_name__(object, "attribute_name")

       # Should keep existing name
       assert param.name == "existing_name"
       assert param.target == "existing_name"  # Should still default to name

   def test_param_set_name_with_existing_target(self):
       """Test __set_name__ when target already exists."""
       param = Param(target="custom_target")

       param.__set_name__(object, "attribute_name")

       assert param.name == "attribute_name"
       assert param.target == "custom_target"  # Should keep existing target

   def test_param_extraction(self):
       """Test param extraction from data."""
       param = Param(source="nested.field")
       data = {"nested": {"field": "value"}}

       result = param.extract(data)
       assert result == "value"

   def test_param_with_default(self):
       """Test param with default value."""
       param = Param(source="missing", default="fallback")
       data = {}

       result = param.extract(data)
       assert result == "fallback"

   def test_param_required_missing(self):
       """Test required param raises when missing."""
       param = Param(source="missing", required=True)
       data = {}

       with pytest.raises(ValueError):
           param.extract(data)

   def test_param_with_transform(self):
       """Test param with transform function."""
       param = Param(source="field", transform=lambda x: x.upper())
       data = {"field": "hello"}

       result = param.extract(data)
       assert result == "HELLO"

   def test_param_schematix_operators(self):
       """Test schematix operator integration."""
       import schematix as sex

       param1 = Param(source="field1")
       param2 = Param(source="field2")

       # Fallback operator
       fallback = param1 | param2
       assert isinstance(fallback, sex.FallbackField)

       # Combine operator
       combined = param1 & param2
       assert isinstance(combined, sex.CombinedField)

       # Nested operator
       nested = param1 @ "nested"
       assert isinstance(nested, sex.NestedField)

       # Accumulate operator
       accumulated = param1 + param2
       assert isinstance(accumulated, sex.AccumulatedField)
