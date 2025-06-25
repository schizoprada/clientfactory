# ~/clientfactory/src/clientfactory/core/bases/condition.py
"""
Base Condition Classes
---------------------
Abstract base classes for condition evaluation system.

This module provides the foundational abstract classes that concrete condition
implementations should inherit from. These classes enforce the condition interface
while allowing for shared implementation patterns and type safety.
"""
from __future__ import annotations
import abc, enum, typing as t

class LogicalOperator(str, enum.Enum):
    AND = "AND"
    OR  = "OR"
    # expand later

    def evaluate(self, l: bool, r: bool) -> bool:
        match self.value:
            case "AND":
                return l and r
            case "OR":
                return l or r

    def short(self) -> bool:
        """Short circuit a logical operation based on this operators value."""
        match self.value:
            case "AND":
                return False # AND short-circuits to False
            case "OR":
                return True # OR short-circuits to True

    def shouldshort(self, l: bool) -> bool:
        """Check if the first value this operator will be applied to can be shorted before evaluating the second value."""
        match self.value:
            case "AND":
                return not l # short-circuit AND on False
            case "OR":
                return l # short-circuit OR on True

# private aliases
_AND = LogicalOperator.AND
_OR = LogicalOperator.OR

class BaseCondition(abc.ABC):
    """
    Abstract base class for all condition implementations.

    Provides the foundational interface that all conditions must implement.
    Concrete condition classes should inherit from this class and implement
    the evaluate method with their specific logic.

    This class enforces the condition contract through abstract method requirements
    while providing a common base for type checking and shared functionality.
    """

    @abc.abstractmethod
    def evaluate(self, *args, **kwargs) -> bool:
        """
        Evaluate the condition with given arguments.

        Abstract method that must be implemented by all concrete condition classes.
        The implementation should contain the specific logic for determining whether
        the condition is satisfied.

        Args:
            *args: Positional arguments for condition evaluation
            **kwargs: Keyword arguments for condition evaluation

        Returns:
            bool: True if condition is met, False otherwise

        Raises:
            NotImplementedError: If not implemented by concrete class

        Note:
            Implementations should be deterministic and avoid side effects where
            possible. The specific arguments depend on the condition type and
            intended usage context.
        """
        ...



    def __and__(self, other: 'BaseCondition') -> 'CompositeCondition':
        """Create AND composite condition."""
        return CompositeCondition(self, other, _AND)

    def __or__(self, other: 'BaseCondition') -> 'CompositeCondition':
        """Create OR composite condition"""
        return CompositeCondition(self, other, _OR)


class CompositeCondition(BaseCondition):
    """Composite condition that combines two conditions with given logical operator."""
    def __init__(
        self,
        left: BaseCondition,
        right: BaseCondition,
        operator: t.Union[str, LogicalOperator],
        **kwargs
    ) -> None:
        """
        Initialize composite condition.

        Args:
            left: First condition
            right: Second condition
            operator: LogicalOperator
        """
        self.left: BaseCondition = left
        self.right: BaseCondition = right
        self.operator: LogicalOperator = self._resolveoperator(operator)

    def _resolveoperator(self, operator: t.Union[str, LogicalOperator]) -> LogicalOperator:
        """Ensure operator is valid."""
        if isinstance(operator, LogicalOperator):
            return operator

        if isinstance(operator, str):
            try:
                return LogicalOperator(operator.upper())
            except:
                pass

        raise ValueError(f"Invalid operator '{operator}', valid: {[m.value for m in LogicalOperator]}")

    def evaluate(self, *args, **kwargs) -> bool:
        l = self.left.evaluate(*args, **kwargs)
        if self.operator.shouldshort(l):
            return self.operator.short()
        r = self.right.evaluate(*args, **kwargs)
        return self.operator.evaluate(l, r)

class ContextualCondition(BaseCondition):
    """
    Abstract base class for conditions that require execution context.

    Specialized condition class for evaluations that depend on execution state,
    iteration context, or environmental information. This class enforces that
    the first argument to evaluate() must be a context dictionary containing
    relevant state information.

    Commonly used for:
    - Break conditions based on consecutive errors
    - Retry logic dependent on previous attempts
    - Rate limiting based on request history
    - Dynamic behavior based on execution metadata
    """

    @abc.abstractmethod
    def evaluate(self, context: dict, *args, **kwargs) -> bool:
        """
        Evaluate the condition with execution context and additional arguments.

        Abstract method that must be implemented by concrete contextual condition
        classes. The context parameter provides access to execution state, iteration
        metadata, error history, and other environmental information needed for
        sophisticated condition logic.

        Args:
            context: Dictionary containing execution state and metadata.
                    Common keys may include: 'errors', 'attempts', 'results',
                    'timestamps', 'iteration_count', etc.
            *args: Additional positional arguments for condition evaluation
            **kwargs: Additional keyword arguments for condition evaluation

        Returns:
            bool: True if condition is met, False otherwise

        Raises:
            NotImplementedError: If not implemented by concrete class
            KeyError: If required context keys are missing

        Note:
            Implementations should validate that required context keys exist
            and handle missing context gracefully. The context should not be
            modified during evaluation to maintain evaluation purity.
        """
        ...
