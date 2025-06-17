# ~/clientfactory/tests/unit/misc/test_preprocesses.py
"""
Unit tests for preprocess handling in HTTP decorators.
"""
import pytest
from unittest.mock import Mock

from clientfactory.core import Client, Resource
from clientfactory.decorators.http import get, post
from clientfactory.core.models import ResourceConfig


class TestPreprocessHandling:
    """Test preprocess function handling for HTTP methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_engine = Mock()
        self.mock_session = Mock()
        self.mock_engine._session = self.mock_session

    def test_client_preprocess_basic(self):
        """Test basic preprocess function on client method."""
        def add_timestamp(data):
            return {**data, "timestamp": "2025-01-01T00:00:00Z"}

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("events", preprocess=add_timestamp)
            def create_event(self, **data): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.create_event(name="Test Event", type="meeting")

        request = self.mock_session.send.call_args[0][0]
        expected_json = {
            "name": "Test Event",
            "type": "meeting",
            "timestamp": "2025-01-01T00:00:00Z"
        }
        assert request.json == expected_json

    def test_resource_preprocess_basic(self):
        """Test basic preprocess function on resource method."""
        def normalize_email(data):
            if "email" in data:
                data["email"] = data["email"].lower()
            return data

        class TestResource(Resource):
            @post("", preprocess=normalize_email)
            def create_user(self, **data): pass

        mock_client = Mock()
        mock_client.baseurl = "https://api.example.com"
        mock_client._engine = self.mock_engine
        mock_client._backend = None

        resource = TestResource(
            client=mock_client,
            config=ResourceConfig(name="users", path="users")
        )
        resource._session.send.return_value = Mock()

        resource.create_user(name="John", email="JOHN@EXAMPLE.COM")

        request = resource._session.send.call_args[0][0]
        assert request.json["email"] == "john@example.com"
        assert request.json["name"] == "John"

    def test_preprocess_with_path_parameters(self):
        """Test preprocess works with path parameter substitution."""
        def add_prefix(data):
            if "name" in data:
                data["name"] = f"prefix_{data['name']}"
            return data

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("users/{id}/update", preprocess=add_prefix)
            def update_user(self, id, **data): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.update_user(id=123, name="john", email="john@example.com")

        request = self.mock_session.send.call_args[0][0]
        # URL should have path param substituted
        assert request.url == "https://api.example.com/users/123/update"
        # JSON should have preprocessed data (but not the path param)
        assert request.json == {"name": "prefix_john", "email": "john@example.com"}

    def test_preprocess_modifies_path_parameter(self):
        """Test preprocess can modify path parameters."""
        def uppercase_category(data):
            if "category" in data:
                data["category"] = data["category"].upper()
            return data

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @get("items/{category}/{id}", preprocess=uppercase_category)
            def get_item(self, category, id): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.get_item(category="books", id=456)

        request = self.mock_session.send.call_args[0][0]
        # Path should use the preprocessed (uppercase) category
        assert request.url == "https://api.example.com/items/BOOKS/456"

    def test_preprocess_returns_none(self):
        """Test preprocess function that returns None."""
        def filter_data(data):
            # Return None to indicate no data should be sent
            return None

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("test", preprocess=filter_data)
            def test_method(self, **data): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.test_method(some="data")

        request = self.mock_session.send.call_args[0][0]
        assert request.json is None

    def test_preprocess_with_empty_data(self):
        """Test preprocess with no kwargs."""
        def add_default(data):
            return {**data, "default": "value"}

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("test", preprocess=add_default)
            def test_method(self): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.test_method()

        request = self.mock_session.send.call_args[0][0]
        assert request.json == {"default": "value"}

    def test_preprocess_error_handling(self):
        """Test preprocess function that raises an error."""
        def failing_preprocess(data):
            raise ValueError("Preprocess failed")

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("test", preprocess=failing_preprocess)
            def test_method(self, **data): pass

        client = TestClient(engine=self.mock_engine)

        with pytest.raises(ValueError, match="Preprocess failed"):
            client.test_method(some="data")

    def test_preprocess_different_data_types(self):
        """Test preprocess with different data transformations."""
        def transform_data(data):
            # Convert lists to comma-separated strings
            for key, value in data.items():
                if isinstance(value, list):
                    data[key] = ",".join(str(v) for v in value)
            return data

        class TestClient(Client):
            baseurl = "https://api.example.com"

            @post("test", preprocess=transform_data)
            def test_method(self, **data): pass

        client = TestClient(engine=self.mock_engine)
        client._engine._session.send.return_value = Mock()

        client.test_method(tags=["python", "api", "client"], count=5)

        request = self.mock_session.send.call_args[0][0]
        assert request.json == {"tags": "python,api,client", "count": 5}
