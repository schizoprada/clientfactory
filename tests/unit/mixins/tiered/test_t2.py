# ~/clientfactory/tests/unit/mixins/tiered/test_t2.py
"""
Tier 2 Testing: Nested Cycle Mode + Universal Condition System + Execution Context Tracking
"""
from logging import debug
import pytest
from unittest.mock import Mock

from clientfactory.mixins.iteration.mixin import IterMixin
from clientfactory.mixins.iteration.comps import (
   IterCycle, ErrorHandles, CycleModes, CycleBreak,
   IterContext, ErrorContext
)
from clientfactory.core.models import MethodConfig, Payload, Param
from clientfactory.core.models.enums import HTTPMethod


class MockBoundMethodT2(IterMixin):
    """Mock bound method for Tier 2 testing."""

    def __init__(self, payload_class=None, path=None):
        super().__init__()
        self._methodconfig = MethodConfig(
            name="test_method",
            method=HTTPMethod.GET,
            path=path or "test/{id}",
            payload=payload_class
        )
        self.call_history = []
        self.error_on_calls = set()
        self.should_error = False

    def __call__(self, **kwargs):
        call_num = len(self.call_history) + 1
        self.call_history.append(kwargs)

        if self.should_error or call_num in self.error_on_calls:
            raise ValueError(f"Mock error on call {call_num}")

        return f"result_{call_num}"


class TestNestedCycleMode:
    """Test cartesian product (PROD) cycle mode."""

    def test_prod_mode_with_single_cycle(self):
        """Test PROD mode with one cycle (should behave like SEQ)."""
        class TestPayload(Payload):
            brand = Param(mapping={'nike': 'NIKE_ID', 'adidas': 'ADIDAS_ID'}, keysaschoices=False)
            size = Param()

        method = MockBoundMethodT2(TestPayload)

        cycles = [method.cycle('size', values=['S', 'M'])]
        results = list(method.iterate('brand', values=['nike'], cycles=cycles, mode=CycleModes.PROD))

        # Should have 1 brand × 2 sizes = 2 results
        assert len(results) == 2
        assert len(method.call_history) == 2

        # Check all combinations present
        calls = method.call_history
        assert {'brand': 'NIKE_ID', 'size': 'S'} in calls
        assert {'brand': 'NIKE_ID', 'size': 'M'} in calls

    def test_prod_mode_multiple_cycles(self):
        """Test PROD mode with multiple cycles (full cartesian product)."""
        class TestPayload(Payload):
            brand = Param()
            size = Param()
            color = Param()

        method = MockBoundMethodT2(TestPayload)

        cycles = [
            method.cycle('size', values=['S', 'M']),
            method.cycle('color', values=['red', 'blue'])
        ]

        results = list(method.iterate('brand', values=['nike', 'adidas'], cycles=cycles, mode=CycleModes.PROD))

        # Should have 2 brands × 2 sizes × 2 colors = 8 results
        assert len(results) == 8
        assert len(method.call_history) == 8

        # Check a few specific combinations
        calls = method.call_history
        assert {'brand': 'nike', 'size': 'S', 'color': 'red'} in calls
        assert {'brand': 'nike', 'size': 'M', 'color': 'blue'} in calls
        assert {'brand': 'adidas', 'size': 'S', 'color': 'red'} in calls
        assert {'brand': 'adidas', 'size': 'M', 'color': 'blue'} in calls

    def test_seq_vs_prod_difference(self):
        """Test difference between SEQ and PROD modes."""
        class TestPayload(Payload):
            brand = Param()
            size = Param()

        method = MockBoundMethodT2(TestPayload)

        cycles = [method.cycle('size', values=['S', 'M'])]

        # SEQ mode: iterate brands, then for each brand iterate sizes
        method.call_history.clear()
        list(method.iterate('brand', values=['nike', 'adidas'], cycles=cycles, mode=CycleModes.SEQ))
        seq_calls = len(method.call_history)

        # PROD mode: cartesian product of brands × sizes
        method.call_history.clear()
        list(method.iterate('brand', values=['nike', 'adidas'], cycles=cycles, mode=CycleModes.PROD))
        prod_calls = len(method.call_history)

        # Both should have same number of calls (2 brands × 2 sizes = 4)
        assert seq_calls == prod_calls == 4

        # But the order and structure might be different
        # This test mainly ensures both modes work


class TestExecutionContextTracking:
    """Test execution context and state management."""

    def test_context_initialization(self):
        """Test context is properly initialized."""
        method = MockBoundMethodT2()

        # Context should be initialized
        assert hasattr(method, '_iterctx')
        assert isinstance(method._iterctx, IterContext)
        assert method._iterctx.iterations == 0
        assert method._iterctx.errors.total == 0
        assert method._iterctx.errors.consecutive == 0

    def test_context_reset_on_iterate(self):
        """Test context resets on each iterate() call."""
        method = MockBoundMethodT2(path="test/{id}")


        # Set some context state
        method._iterctx.iterations = 5
        method._iterctx.errors.consecutive = 3

        # iterate() should reset context
        list(method.iterate('id', values=[1]))  # Single iteration

        # Context should be reset
        assert method._iterctx.iterations == 1  # Only current iteration
        assert method._iterctx.errors.consecutive == 0  # Reset on successful result

    def test_context_tracks_successes(self):
        """Test context properly tracks successful iterations."""
        class TestPayload(Payload):
            id = Param()

        method = MockBoundMethodT2(TestPayload)

        results = list(method.iterate('id', values=[1, 2, 3]))

        assert len(results) == 3
        assert method._iterctx.iterations == 3
        assert method._iterctx.errors.total == 0
        assert method._iterctx.errors.consecutive == 0
        assert len(method._iterctx.results) == 3
        assert method._iterctx.results == [True, True, True]  # Placeholders by default

    def test_context_tracks_errors(self):
        """Test context properly tracks errors."""
        class TestPayload(Payload):
            id = Param()

        method = MockBoundMethodT2(TestPayload)
        method.error_on_calls = {2}  # Error on second call

        # create a custom break condition to capture consecutive errors
        captured = 0
        def capture(context, result):
            nonlocal captured
            if isinstance(result, Exception):
                captured = context.get('errors', {}).get('consecutive', 0)
            return False

        breakfunc = CycleBreak.Callback(capture)

        try:
            list(method.iterate('id', values=[1, 2, 3], breaks=[breakfunc]))
        except ValueError:
            pass

        assert method._iterctx.errors.total >= 1
        assert captured >= 1

    def test_context_stores_results_when_enabled(self):
        """Test context stores actual results when store=True."""
        class TestPayload(Payload):
            id = Param()

        method = MockBoundMethodT2(TestPayload)

        results = list(method.iterate('id', values=[1, 2], store=True))

        assert len(results) == 2
        assert method._iterctx.storeresults is True
        # Should store actual results, not just True placeholders
        stored_results = method._iterctx.results
        assert stored_results == ['result_1', 'result_2']


class TestBreakConditions:
    """Test break condition functionality."""

    def test_consecutive_errors_break(self):
        """Test breaking on consecutive errors."""
        class TestPayload(Payload):
            id = Param()

        method = MockBoundMethodT2(TestPayload)
        method.should_error = True  # All calls will error

        break_condition = CycleBreak.ConsecutiveErrors(3)

        # Should break after 3 consecutive errors, not raise
        results = list(method.iterate('id', values=[1, 2, 3, 4, 5], breaks=[break_condition]))

        # Should have broken early, not completed all iterations
        assert len(results) == 0  # No successful results since all calls error
        assert len(method.call_history) <= 3  # Should stop at break condition

    def test_predicate_break_condition(self):
        """Test breaking based on result predicate."""
        class TestPayload(Payload):
            id = Param()

        method = MockBoundMethodT2(TestPayload)

        # Break when result contains "3"
        break_condition = CycleBreak.When(lambda result: '3' in result)

        results = list(method.iterate('id', values=[1, 2, 3, 4, 5], breaks=[break_condition]))

        # Should stop after getting result_3
        assert len(results) <= 3
        assert len(method.call_history) <= 3

    def test_custom_callback_break(self):
        """Test custom callback break condition."""
        class TestPayload(Payload):
            id = Param()

        method = MockBoundMethodT2(TestPayload)

        def custom_break(context, result):
            iterations = context.get('iterations', 0)
            print(f"DEBUG custom_break: iterations={iterations}, result={result}")
            should_break = iterations >= 2
            print(f"DEBUG custom_break: should_break={should_break}")
            return should_break

        break_condition = CycleBreak.Callback(custom_break)

        results = list(method.iterate('id', values=[1, 2, 3, 4, 5], breaks=[break_condition]))

        print(f"DEBUG: len(results)={len(results)}, len(call_history)={len(method.call_history)}")
        print(f"DEBUG: final iterations={method._iterctx.iterations}")

        # Should stop at 2 iterations (break condition checks AFTER each call)
        assert len(results) == 2
        assert len(method.call_history) == 2

    def test_multiple_break_conditions(self):
        """Test multiple break conditions (OR logic)."""
        class TestPayload(Payload):
            id = Param()

        method = MockBoundMethodT2(TestPayload)

        breaks = [
            CycleBreak.ConsecutiveErrors(10),  # High threshold, shouldn't trigger
            CycleBreak.When(lambda result: isinstance(result, str) and '3' in result)  # Fix: Check type first
        ]

        results = list(method.iterate('id', values=[1, 2, 3, 4, 5], breaks=breaks))

        print(f"DEBUG: results={results}")
        print(f"DEBUG: call_history={method.call_history}")

        # Should stop when predicate condition is met (after result_3)
        assert len(results) == 3  # Gets result_1, result_2, result_3, then breaks
        assert len(method.call_history) == 3


class TestIntegration:
    """Test integration of all Tier 2 features."""

    def test_prod_mode_with_break_conditions(self):
        """Test cartesian product with break conditions."""
        class TestPayload(Payload):
            brand = Param()
            size = Param()

        method = MockBoundMethodT2(TestPayload)

        cycles = [method.cycle('size', values=['S', 'M', 'L'])]

        def debug_break(ctx, result):
            iterations = ctx.get('iterations', 0)
            print(f"DEBUG prod_break: iterations={iterations}, result={result}")
            should_break = iterations >= 3
            print(f"DEBUG prod_break: should_break={should_break}")
            return should_break

        # Break after 3 iterations (when iterations reaches 3)
        break_condition = CycleBreak.Callback(debug_break)

        results = list(method.iterate(
            'brand',
            values=['nike', 'adidas'],
            cycles=cycles,
            mode=CycleModes.PROD,
            breaks=[break_condition]
        ))

        print(f"DEBUG prod: len(results)={len(results)}, len(call_history)={len(method.call_history)}")
        # Should stop at 3 iterations
        assert len(results) == 3
        assert len(method.call_history) == 3

    def test_context_persistence_across_cycles(self):
        """Test that context persists and accumulates across cycle combinations."""
        class TestPayload(Payload):
            brand = Param()
            size = Param()

        method = MockBoundMethodT2(TestPayload)
        method.error_on_calls = {2, 4}  # Errors on specific calls

        cycles = [method.cycle('size', values=['S', 'M'])]

        try:
            list(method.iterate('brand', values=['nike', 'adidas'], cycles=cycles, mode=CycleModes.PROD))
        except ValueError:
            pass  # Expected errors

        # Context should have tracked all attempts
        assert method._iterctx.iterations >= 2  # At least attempted some
        assert method._iterctx.errors.total >= 1  # Should have errors

    def test_full_tier2_integration(self):
        """Test all Tier 2 features working together."""
        class TestPayload(Payload):
            brand = Param(mapping={'nike': 'NIKE_ID'}, keysaschoices=False)
            size = Param()
            category = Param()

        method = MockBoundMethodT2(TestPayload)

        cycles = [
            method.cycle('size', values=['S', 'M']),
            method.cycle('category', values=['shoes', 'apparel'])
        ]

        def debug_break(ctx, result):
            iterations = ctx.get('iterations', 0)
            print(f"DEBUG integration_break: iterations={iterations}, result={result}")
            should_break = iterations >= 2
            print(f"DEBUG integration_break: should_break={should_break}")
            return should_break

        # Break after 2 iterations
        break_condition = CycleBreak.Callback(debug_break)

        results = list(method.iterate(
            'brand',
            start='nike',  # Advanced param inference
            cycles=cycles,
            mode=CycleModes.PROD,  # Cartesian product
            breaks=[break_condition],  # Break conditions
            store=True  # Context tracking with result storage
        ))

        print(f"DEBUG integration: len(results)={len(results)}, call_history={method.call_history}")

        # Should work with all features integrated
        assert len(results) == 2  # Stopped by break condition
        assert method._iterctx.storeresults is True
        assert method._iterctx.iterations == 2

        # Check parameter resolution worked
        calls = method.call_history
        assert all('brand' in call and call['brand'] == 'NIKE_ID' for call in calls)
