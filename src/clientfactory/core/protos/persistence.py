# ~/clientfactory/src/clientfactory/core/protos/persistence.py
"""
Persistence Protocol
-------------------
Protocol for session state persistence.
"""
from __future__ import annotations
import typing as t

@t.runtime_checkable
class PersistenceProtocol(t.Protocol):
   """
   Session state persistence protocol.

   Defines interface for saving and loading session state (cookies, headers, auth tokens).
   """

   def save(self, data: t.Dict[str, t.Any]) -> None:
       """
       Save session state data.

       Args:
           data: Session state to persist (cookies, headers, etc.)
       """
       ...

   def load(self) -> t.Dict[str, t.Any]:
       """
       Load session state data.

       Returns:
           Previously saved session state, or empty dict if none exists
       """
       ...

   def clear(self) -> None:
       """
       Clear all persisted session state.
       """
       ...

   def exists(self) -> bool:
       """
       Check if persisted state exists.

       Returns:
           True if state exists, False otherwise
       """
       ...

   def update(self, data: t.Dict[str, t.Any]) -> None:
       """
       Update specific keys in persisted state.

       Args:
           data: Partial state updates to apply
       """
       ...
