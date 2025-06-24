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
import abc, typing as t

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
