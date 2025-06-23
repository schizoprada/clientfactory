# ~/clientfactory/tests/unit/mixins/test_iteration_basic.py
"""
Tests for basic iteration functionality
"""
import pytest
from unittest.mock import Mock

from clientfactory.mixins.iteration.mixin import IterMixin
from clientfactory.mixins.iteration.comps import IterCycle, ErrorHandles, CycleModes
from clientfactory.core.models import MethodConfig
from clientfactory.core.models.enums import HTTPMethod


class MockBoundMethod(IterMixin):
    """Mock bound method for testing iteration."""

    def __init__(self):
        super().__init__()
        self._methodconfig = MethodConfig(
            name="test_method",
            method=HTTPMethod.GET,
            path="test/{id}"
        )
        self.call_history = []

    def __call__(self, **kwargs):
        self.call_history.append(kwargs)
        return f"result_for_{kwargs}"


class TestIterCycle:
    """Test IterCycle functionality."""

    def test_cycle_creation(self):
        """Test basic cycle creation."""
        cycle = IterCycle(param="page", start=1, end=5)

        assert cycle.parameter == "page"
        assert cycle.start == 1
        assert cycle.end == 5

    def test_numeric_generation(self):
        """Test numeric value generation."""
        cycle = IterCycle(param="page", start=1, end=3)
        values = list(cycle.generate())

        assert values == [1, 2, 3]

    def test_values_generation(self):
        """Test explicit values generation."""
        cycle = IterCycle(param="brand", values=["nike", "adidas"])
        values = list(cycle.generate())

        assert values == ["nike", "adidas"]

    def test_stepfilter_generation(self):
        """Test step filtering."""
        cycle = IterCycle(
            param="brand",
            values=["apple", "banana", "apricot"],
            stepfilter=lambda x: x.startswith("a")
        )
        values = list(cycle.generate())

        assert values == ["apple", "apricot"]


class TestIterMixin:
    """Test IterMixin functionality."""

    def test_cycle_method(self):
        """Test cycle creation method."""
        method = MockBoundMethod()
        cycle = method.cycle("page", start=1, end=5)

        assert isinstance(cycle, IterCycle)
        assert cycle.parameter == "page"

    def test_withparams(self):
        """Test static params setting."""
        method = MockBoundMethod()
        result = method.withparams(category="shoes", brand="nike")

        assert result is method  # Returns self
        assert method._staticparams == {"category": "shoes", "brand": "nike"}

    def test_builder_methods(self):
        """Test builder pattern methods."""
        method = MockBoundMethod()

        # Test chaining
        result = method.range(1, 10).values(["a", "b"]).mode(CycleModes.SEQUENTIAL)
        assert result is method

        # Test config is stored
        assert method._iterconfig["start"] == 1
        assert method._iterconfig["end"] == 10
        assert method._iterconfig["values"] == ["a", "b"]
        assert method._iterconfig["cyclemode"] == CycleModes.SEQUENTIAL

    def test_basic_iteration(self):
        """Test basic single parameter iteration."""
        method = MockBoundMethod()

        # Simple iteration
        results = list(method.iterate("id", values=[1, 2, 3]))

        assert len(results) == 3
        assert method.call_history == [
            {"id": 1},
            {"id": 2},
            {"id": 3}
        ]

    def test_iteration_with_static_params(self):
        """Test iteration with static parameters."""
        method = MockBoundMethod()
        method.withparams(category="shoes")

        results = list(method.iterate("page", values=[1, 2]))

        assert method.call_history == [
            {"category": "shoes", "page": 1},
            {"category": "shoes", "page": 2}
        ]

    def test_separate_kwargs(self):
        """Test kwargs separation."""
        method = MockBoundMethod()

        iter_config, static_params = method._separatekwargs(
            static={"brand": "nike"},
            start=1,
            end=10,
            category="shoes",
            _start=100
        )

        assert iter_config == {"start": 1, "end": 10}
        assert static_params == {"brand": "nike", "category": "shoes", "start": 100}
