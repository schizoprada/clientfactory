# ~/clientfactory/src/clientfactory/core/protos/condition.py
"""
Condition Protocol
-----------------
Protocol definitions for condition evaluation system.

This module defines the core interface that all condition objects must implement,
enabling duck typing and type checking for condition evaluation across the library.
"""
from __future__ import annotations
import typing as t


@t.runtime_checkable
class ConditionProtocol(t.Protocol):
   """
   Protocol for condition evaluation objects.

   Defines the interface that all condition objects must implement to be used
   within the ClientFactory condition system. Objects implementing this protocol
   can be used for break conditions, retry logic, execution control, and other
   conditional behaviors throughout the library.

   The protocol uses runtime_checkable to enable isinstance() checks at runtime
   for duck typing compatibility.
   """

   def evaluate(self, *args, **kwargs) -> bool:
       """
       Evaluate the condition with given arguments.

       Args:
           *args: Positional arguments for condition evaluation
           **kwargs: Keyword arguments for condition evaluation

       Returns:
           bool: True if condition is met, False otherwise

       Note:
           Implementations should be idempotent and side-effect free where possible.
           The specific arguments depend on the condition type and usage context.
       """
       ...
