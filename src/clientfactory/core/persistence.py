# ~/clientfactory/src/clientfactory/core/persistence.py
"""
Concrete Persistence Implementation
"""
from __future__ import annotations
import json, typing as t
from pathlib import Path

from clientfactory.core.bases import BasePersistence

invalidpath = lambda p: (not (pstr:=str(p))) or (pstr in ("", "."))

class Persistence(BasePersistence):
    """Standard concrete persistence implementation using JSON files."""
    def _save(self, data: t.Dict[str, t.Any]) -> None:
        """Save to JSON file"""
        if invalidpath(self.path):
            return

        path = Path(self.path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self) -> t.Dict[str, t.Any]:
        """Load from JSON File"""
        if invalidpath(self.path):
            return {}

        path = Path(self.path)
        if not path.exists():
            return {}

        with open(path, 'r') as f:
            data = json.load(f)
        return data

    def _clear(self) -> None:
        """Clear the JSON file"""
        if not self.path:
            return

        path = Path(self.path)
        if path.exists():
            path.unlink()

    def _exists(self) -> bool:
        """Check if file exists"""
        if not self.path:
            return False
        return Path(self.path).exists()
