# ~/clientfactory/src/clientfactory/engines/_meta.py
"""
Metadata for engines module
"""
from __future__ import annotations
import typing as t

from clientfactory.core.bases import BaseEngine
from clientfactory.engines.requestslib import RequestsEngine


EnginesMap: dict[str, t.Type[BaseEngine]] = {
    'requests': RequestsEngine
}
