# ~/clientfactory/src/clientfactory/mixins/preparation/comps.py
"""
Preparation Components
--------------------
Components for request preparation functionality.
"""
from __future__ import annotations
import typing as t

if t.TYPE_CHECKING:
    from clientfactory.core.models import ExecutableRequest

# minimal for forward reference, might enhance later
PrepConfig = t.Dict[str, t.Any]
