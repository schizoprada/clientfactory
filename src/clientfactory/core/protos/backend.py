# ~/clientfactory/src/clientfactory/core/protos/backend.py
"""
Backend Protocol
----------------
Protocol for response processing backends.
"""
from __future__ import annotations
import typing as t

if t.TYPE_CHECKING:
    from clientfactory.core.models.request import RequestModel, ResponseModel


@t.runtime_checkable
class BackendProtocol(t.Protocol):
   """
   Response processing backend protocol.

   Defines interface for API-specific request formatting and response processing.
   """

   def formatrequest(self, request: 'RequestModel', data: t.Dict[str, t.Any]) -> 'RequestModel':
       """
       Format request for specific backend.

       Args:
           request: Base request to format
           data: Request data to include

       Returns:
           Formatted request ready for backend
       """
       ...

   def processresponse(self, response: 'ResponseModel') -> t.Any:
       """
       Process response from backend.

       Args:
           response: Raw response from backend

       Returns:
           Processed response data
       """
       ...

   def validatedata(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
       """
       Validate data before sending to backend.

       Args:
           data: Data to validate

       Returns:
           Validated data
       """
       ...

   def handleerror(self, response: 'ResponseModel') -> None:
       """
       Handle backend-specific errors.

       Args:
           response: Error response

       Raises:
           Backend-specific exception
       """
       ...
