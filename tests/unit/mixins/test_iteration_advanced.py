# ~/clientfactory/tests/unit/mixins/test_iteration_advanced.py
"""
Tests for advanced iteration functionality
"""
import pytest
import time
from unittest.mock import Mock

from clientfactory.mixins.iteration.mixin import IterMixin
from clientfactory.mixins.iteration.comps import IterCycle, ErrorHandles, CycleModes
from clientfactory.core.models import MethodConfig, Payload, Param
from clientfactory.core.models.enums import HTTPMethod


class MockBoundMethodAdvanced(IterMixin):
   """Mock bound method for testing advanced iteration."""

   def __init__(self):
       super().__init__()
       self._methodconfig = MethodConfig(
           name="test_method",
           method=HTTPMethod.GET,
           path="test/{id}",
           payload=None
       )
       self.call_history = []
       self.error_count = 0
       self.should_error = False
       self.error_on_calls = set()  # Specific calls to error on

   def __call__(self, **kwargs):
       self.call_history.append(kwargs)
       call_num = len(self.call_history)

       if self.should_error or call_num in self.error_on_calls:
           self.error_count += 1
           raise ValueError(f"Mock error on call {call_num}")

       return f"result_for_{kwargs}"


class TestPayloadExtraction:
   """Test payload parameter extraction."""

   def test_extract_payload_params(self):
       """Test extracting params from payload."""
       class TestPayload(Payload):
           name = Param()
           email = Param()
           age = Param()

       method = MockBoundMethodAdvanced()
       method._methodconfig = MethodConfig(
           name="test_method",
           method=HTTPMethod.GET,
           path="test/{id}",
           payload=TestPayload
       )

       params = method._collectiterables()

       # Should include path params and payload params
       assert 'id' in params  # From path
       assert 'name' in params  # From payload
       assert 'email' in params  # From payload
       assert 'age' in params  # From payload

   def test_extract_payload_instance(self):
       """Test extracting params from payload instance."""
       class TestPayload(Payload):
           query = Param()
           limit = Param()

       method = MockBoundMethodAdvanced()
       method._methodconfig = MethodConfig(
           name="test_method",
           method=HTTPMethod.GET,
           path="test/{id}",
           payload=TestPayload()
       )

       params = method._collectiterables()

       assert 'query' in params
       assert 'limit' in params


class TestRetryLogic:
   """Test retry functionality."""

   def test_retry_on_error(self):
       """Test retry logic with ErrorHandles.RETRY."""
       method = MockBoundMethodAdvanced()
       method.error_on_calls = {1, 2}  # Error on first two calls

       cycle = IterCycle(
           param="page",
           values=[1, 2, 3],
           onerror=ErrorHandles.RETRY,
           maxretries=3,
           retrydelay=0.1
       )

       start_time = time.time()
       results = list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))
       end_time = time.time()

       # Should have successful results after retries
       assert len(results) == 3

       # Should have made retry attempts (more calls than results)
       assert len(method.call_history) > 3

       # Should have taken time for retries
       assert end_time - start_time >= 0.2  # At least 2 retries with 0.1s delay

   def test_stop_on_error(self):
       """Test stopping on error with ErrorHandles.STOP."""
       method = MockBoundMethodAdvanced()
       method.error_on_calls = {2}  # Error on second call

       cycle = IterCycle(
           param="page",
           values=[1, 2, 3],
           onerror=ErrorHandles.STOP
       )

       with pytest.raises(ValueError, match="Mock error on call 2"):
           list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))

   def test_continue_on_error(self):
       """Test continuing on error with ErrorHandles.CONTINUE."""
       method = MockBoundMethodAdvanced()
       method.error_on_calls = {2}  # Error on second call only

       cycle = IterCycle(
           param="page",
           values=[1, 2, 3],
           onerror=ErrorHandles.CONTINUE
       )

       results = list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))

       # Should skip failed call and continue
       assert len(results) == 2
       assert method.call_history == [
           {"page": 1},
           {"page": 2},  # This errored
           {"page": 3}
       ]

   def test_max_retries_exceeded(self):
       """Test behavior when max retries exceeded."""
       method = MockBoundMethodAdvanced()
       method.should_error = True  # Always error

       cycle = IterCycle(
           param="page",
           values=[1],
           onerror=ErrorHandles.RETRY,
           maxretries=2,
           retrydelay=0.01
       )

       with pytest.raises(ValueError):
           list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))

       # Should have tried 3 times (initial + 2 retries)
       assert len(method.call_history) == 3


class TestCallbackLogic:
   """Test callback error handling."""

   def test_callback_retry(self):
       """Test callback that decides to retry."""
       method = MockBoundMethodAdvanced()
       method.error_on_calls = {1, 2}  # Error on first two calls

       def retry_callback(exception, cycle):
           return True  # Always retry

       cycle = IterCycle(
           param="page",
           values=[1],
           onerror=ErrorHandles.CALLBACK,
           errorcallback=retry_callback,
           maxretries=3,
           retrydelay=0.01
       )

       results = list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))

       # Should eventually succeed after retries
       assert len(results) == 1
       assert len(method.call_history) == 3  # 2 failures + 1 success

   def test_callback_no_retry(self):
       """Test callback that decides not to retry."""
       method = MockBoundMethodAdvanced()
       method.should_error = True

       def no_retry_callback(exception, cycle):
           return False  # Never retry

       cycle = IterCycle(
           param="page",
           values=[1],
           onerror=ErrorHandles.CALLBACK,
           errorcallback=no_retry_callback
       )

       with pytest.raises(ValueError):
           list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))

       # Should only try once
       assert len(method.call_history) == 1

   def test_callback_conditional_retry(self):
       """Test callback with conditional retry logic."""
       method = MockBoundMethodAdvanced()
       method.should_error = True

       retry_count = 0
       def conditional_callback(exception, cycle):
           nonlocal retry_count
           retry_count += 1
           return retry_count <= 2  # Only retry first 2 times

       cycle = IterCycle(
           param="page",
           values=[1],
           onerror=ErrorHandles.CALLBACK,
           errorcallback=conditional_callback,
           maxretries=5  # Higher than callback limit
       )

       with pytest.raises(ValueError):
           list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))

       # Should try 3 times (initial + 2 retries)
       assert len(method.call_history) == 3


class TestCyclesAdvanced:
   """Test advanced cycle functionality."""

   def test_sequential_cycles_with_errors(self):
       """Test sequential cycles with error handling."""
       method = MockBoundMethodAdvanced()
       method.error_on_calls = {3}  # Error on third call

       primary = IterCycle(param="brand", values=["nike", "adidas"])
       cycles = IterCycle(
           param="page",
           values=[1, 2],
           onerror=ErrorHandles.CONTINUE
       )

       results = list(method._iterate(primary, cycles, CycleModes.SEQUENTIAL))


       print(f"Results: {results}")
       print(f"Call history: {method.call_history}")
       print(f"Error count: {method.error_count}")

       # Should have 3 successful results (4 total - 1 error)
       assert len(results) == 3

       # Should have called 4 times total
       assert len(method.call_history) == 4

   def test_stepfilter_functionality(self):
       """Test step filtering in cycles."""
       method = MockBoundMethodAdvanced()

       cycle = IterCycle(
           param="brand",
           values=["apple", "banana", "apricot", "cherry"],
           stepfilter=lambda x: x.startswith("a")
       )

       results = list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))

       # Should only process items starting with 'a'
       assert len(results) == 2
       assert method.call_history == [
           {"brand": "apple"},
           {"brand": "apricot"}
       ]

   def test_numeric_step_with_filter(self):
       """Test numeric stepping with filtering."""
       method = MockBoundMethodAdvanced()

       cycle = IterCycle(
           param="item",
           values=["a", "b", "c", "d", "e", "f"],
           stepfilter=lambda x: x in ["a", "c", "e", "f"],  # Filter first
           step=2  # Then every 2nd
       )

       results = list(method._iterate(cycle, None, CycleModes.SEQUENTIAL))

       # Filter: ["a", "c", "e", "f"], then step=2: ["a", "e"]
       assert len(results) == 2
       assert method.call_history == [
           {"item": "a"},
           {"item": "e"}
       ]


class TestStaticParamsMerging:
   """Test static parameters merging."""

   def test_withparams_persist_across_iterations(self):
       """Test that withparams persists across multiple iterations."""
       method = MockBoundMethodAdvanced()
       method.withparams(category="test", format="json")

       # First iteration
       list(method.iterate("page", values=[1, 2]))

       # Clear history
       first_calls = method.call_history.copy()
       method.call_history.clear()

       # Second iteration should still have static params
       list(method.iterate("size", values=["S", "M"]))

       # Both iterations should have static params
       assert all("category" in call and "format" in call for call in first_calls)
       assert all("category" in call and "format" in call for call in method.call_history)

   def test_static_params_override_precedence(self):
       """Test precedence when static params conflict."""
       method = MockBoundMethodAdvanced()
       method.withparams(page=999, category="shoes")

       # Iteration param should override static param
       results = list(method.iterate("page", values=[1, 2], brand="nike"))

       expected_calls = [
           {"category": "shoes", "brand": "nike", "page": 1},
           {"category": "shoes", "brand": "nike", "page": 2}
       ]

       assert method.call_history == expected_calls
