# ~/clientfactory/src/clientfactory/core/protos/payload.py
"""
Payload Protocol
---------------
Protocol for request data validation and serialization.
"""
from __future__ import annotations
import typing as t


@t.runtime_checkable
class PayloadProtocol(t.Protocol):
   """
   Request data validation and serialization protocol.

   Defines interface for handling request payloads with validation and transformation.
   """

   def validate(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
       """
       Validate request data.

       Args:
           data: Raw request data

       Returns:
           Validated data

       Raises:
           ValidationError: If data is invalid
       """
       ...

   def serialize(self, data: t.Dict[str, t.Any]) -> t.Union[str, bytes, t.Dict[str, t.Any]]:
       """
       Serialize validated data for request.

       Args:
           data: Validated data to serialize

       Returns:
           Serialized data ready for HTTP request
       """
       ...

   def transform(self, data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
       """
       Transform data before validation.

       Args:
           data: Raw input data

       Returns:
           Transformed data
       """
       ...

   def getschema(self) -> t.Dict[str, t.Any]:
       """
       Get payload schema definition.

       Returns:
           Schema dictionary describing expected data structure
       """
       ...
