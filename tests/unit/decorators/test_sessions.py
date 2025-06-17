# ~/clientfactory/tests/unit/decorators/test_sessions.py
"""
Unit tests for session decorators.
"""
import pytest
from unittest.mock import Mock

from clientfactory.decorators.sessions import basesession, session
from clientfactory.core.bases import BaseSession
from clientfactory.core.session import Session


class TestSessionDecorators:
   """Test session decorators."""

   def test_basesession_decorator_basic(self):
       """Test basic basesession decorator usage."""
       @basesession
       class CustomSession:
           timeout = 60.0

           def custom_prepare(self, request):
               return request

       assert issubclass(CustomSession, BaseSession)
       assert CustomSession.timeout == 60.0
       assert hasattr(CustomSession, 'custom_prepare')

   def test_basesession_decorator_with_kwargs(self):
       """Test basesession decorator with kwargs."""
       @basesession(retries=5, poolsize=20)
       class CustomSession:
           pass

       assert issubclass(CustomSession, BaseSession)
       assert CustomSession.retries == 5
       assert CustomSession.poolsize == 20

   def test_session_decorator_basic(self):
       """Test basic session decorator usage."""
       @session
       class APISession:
           custom_attr = "session"

       assert issubclass(APISession, Session)
       assert APISession.custom_attr == "session"

   def test_session_decorator_with_components(self):
       """Test session decorator with auth and persistence components."""
       class MockAuth:
           pass

       class MockPersistence:
           pass

       @session(auth=MockAuth, persistence=MockPersistence)
       class ComponentSession:
           pass

       assert issubclass(ComponentSession, Session)
       assert ComponentSession.__auth__ == MockAuth
       assert ComponentSession.__persistence__ == MockPersistence

   def test_session_decorator_with_attributes(self):
       """Test session decorator with declarative attributes."""
       @session(
           headers={"User-Agent": "TestApp/1.0", "Accept": "application/json"},
           cookies={"session": "test123"},
           useragent="CustomAgent/2.0"
       )
       class AttributeSession:
           pass

       assert issubclass(AttributeSession, Session)
       assert AttributeSession.headers == {"User-Agent": "TestApp/1.0", "Accept": "application/json"}
       assert AttributeSession.cookies == {"session": "test123"}
       assert AttributeSession.useragent == "CustomAgent/2.0"

   def test_session_decorator_with_mixed_config(self):
       """Test session decorator with both components and attributes."""
       class MockAuth:
           pass

       @session(
           auth=MockAuth,
           headers={"Authorization": "Bearer token"},
           cookies={"csrf": "token123"},
           timeout=45.0
       )
       class MixedSession:
           custom_method_called = False

           def custom_method(self):
               self.custom_method_called = True

       assert issubclass(MixedSession, Session)
       assert MixedSession.__auth__ == MockAuth
       assert MixedSession.headers == {"Authorization": "Bearer token"}
       assert MixedSession.cookies == {"csrf": "token123"}
       assert MixedSession.timeout == 45.0
       assert hasattr(MixedSession, 'custom_method')

   def test_decorator_without_parentheses(self):
       """Test decorators used without parentheses."""
       @basesession
       class BaseSessionClass:
           pass

       @session
       class SessionClass:
           pass

       assert issubclass(BaseSessionClass, BaseSession)
       assert issubclass(SessionClass, Session)

   def test_preserves_original_attributes(self):
       """Test that decorators preserve original class attributes."""
       @session(headers={"Custom": "Header"})
       class TestSession:
           original_attr = "original"

           def original_method(self):
               return "original"

       # Test that original attributes are preserved
       assert TestSession.original_attr == "original"
       assert hasattr(TestSession, 'original_method')
       assert TestSession.headers == {"Custom": "Header"}

   def test_preserves_module_and_qualname(self):
       """Test that decorators preserve module and qualname."""
       @session
       class TestSession:
           pass

       assert TestSession.__module__ == __name__
       assert TestSession.__qualname__ == "TestSessionDecorators.test_preserves_module_and_qualname.<locals>.TestSession"

   def test_inheritance_works_correctly(self):
       """Test that the transformed class inherits correctly."""
       @basesession
       class CustomSession:
           def custom_setup(self):
               return "custom setup"

       # Should inherit from BaseSession
       # Note: BaseSession is abstract, so we can't instantiate directly
       # but we can check inheritance and method presence
       assert issubclass(CustomSession, BaseSession)

       # Should have custom method
       assert hasattr(CustomSession, 'custom_setup')

       # Should have BaseSession methods
       assert hasattr(CustomSession, 'preparerequest')
       assert hasattr(CustomSession, 'send')
       assert hasattr(CustomSession, 'close')

   def test_session_component_declaration_format(self):
       """Test that component declarations use proper dunder format."""
       class TestAuth:
           pass

       class TestPersistence:
           pass

       @session(auth=TestAuth, persistence=TestPersistence)
       class ComponentSession:
           pass

       # Components should be declared as __component__ attributes
       assert hasattr(ComponentSession, '__auth__')
       assert hasattr(ComponentSession, '__persistence__')
       assert ComponentSession.__auth__ == TestAuth
       assert ComponentSession.__persistence__ == TestPersistence

   def test_multiple_decorators_different_classes(self):
       """Test multiple session decorators on different classes."""
       class AuthClass:
           pass

       @basesession(timeout=30.0)
       class BaseSessionClass:
           base_attr = "base"

       @session(auth=AuthClass, headers={"Test": "Header"})
       class SessionClass:
           session_attr = "session"

       assert issubclass(BaseSessionClass, BaseSession)
       assert issubclass(SessionClass, Session)

       assert BaseSessionClass.timeout == 30.0
       assert BaseSessionClass.base_attr == "base"

       assert SessionClass.__auth__ == AuthClass
       assert SessionClass.headers == {"Test": "Header"}
       assert SessionClass.session_attr == "session"

   def test_empty_containers_handled_correctly(self):
       """Test that empty headers/cookies are handled correctly."""
       @session(headers={}, cookies={})
       class EmptySession:
           pass

       assert issubclass(EmptySession, Session)
       assert EmptySession.headers == {}
       assert EmptySession.cookies == {}
