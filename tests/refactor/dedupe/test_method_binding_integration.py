# ~/clientfactory/tests/refactor/dedupe/test_method_binding_integration.py
"""Test that new createboundmethod produces identical behavior to old implementations."""
import pytest
from unittest.mock import Mock, patch
from clientfactory.core.models import MethodConfig, HTTPMethod, RequestModel, ResponseModel
from clientfactory.core.bases.client import BaseClient
from clientfactory.core.bases.resource import BaseResource
from clientfactory.resources.search import SearchResource


class TestBindingIntegration:
   """Test that old vs new binding behavior is identical."""

   def test_client_bound_method_execution(self):
       """Test BaseClient bound method works with new implementation."""
       # Mock client
       client = Mock(spec=BaseClient)
       client.baseurl = "https://api.example.com"
       client._engine = Mock()
       client._backend = None

       # Mock response
       mock_response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"test": "data"}',
           url="https://api.example.com/test"
       )
       client._engine.send.return_value = mock_response

       # Create test method
       def test_method(): pass
       test_method._methodconfig = MethodConfig(
           name="test",
           method=HTTPMethod.GET,
           path="test"
       )

       # Create bound method using new implementation
       bound = BaseClient._createboundmethod(client, test_method)

       # Execute and verify
       result = bound()
       assert result == mock_response
       client._engine.send.assert_called_once()

   def test_resource_bound_method_execution(self):
       """Test BaseResource bound method works with new implementation."""
       # Mock resource
       resource = Mock(spec=BaseResource)
       resource.baseurl = None
       resource.path = "users"
       resource._backend = None
       resource._client = Mock()
       resource._client.baseurl = "https://api.example.com"
       resource._client._engine = Mock()

       # Mock response
       mock_response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"user": "data"}',
           url="https://api.example.com/users/123"
       )
       resource._client._engine.send.return_value = mock_response

       # Create test method
       def test_method(): pass
       test_method._methodconfig = MethodConfig(
           name="get_user",
           method=HTTPMethod.GET,
           path="{id}"
       )

       # Create bound method using new implementation
       bound = BaseResource._createboundmethod(resource, test_method)

       # Execute with path param
       result = bound(123)
       assert result == mock_response
       resource._client._engine.send.assert_called_once()

   def test_search_resource_generation(self):
       """Test SearchResource method generation works."""
       from clientfactory.core.models import MergeMode

       # Mock search resource
       search = Mock(spec=SearchResource)
       search.searchmethod = "search"
       search.method = HTTPMethod.POST
       search.path = "search"
       search.payload = None
       search.headers = {}
       search.cookies = {}
       search.headermode = MergeMode.MERGE
       search.cookiemode = MergeMode.MERGE
       search.timeout = None
       search.retries = None
       search.preprocess = None
       search.postprocess = None
       search.baseurl = None
       search._backend = None
       search._client = Mock()
       search._client.baseurl = "https://api.example.com"
       search._client._engine = Mock()
       search._registermethod = Mock()
       search._generatedocstring = Mock(return_value="Search method")
       search._getpayloadinstance = Mock(return_value=None)

       # Mock response
       mock_response = ResponseModel(
           statuscode=200,
           headers={},
           content=b'{"results": []}',
           url="https://api.example.com/search"
       )
       search._client._engine.send.return_value = mock_response

       # Generate search method
       SearchResource._generatesearchmethod(search)

       # Verify registration was called
       search._registermethod.assert_called_once()
       bound_method = search._registermethod.call_args[0][0]

       # Test execution
       result = bound_method(query="test")
       assert result == mock_response
