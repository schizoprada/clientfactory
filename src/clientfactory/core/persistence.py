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
        #print(f"DEBUG Persistence._save: self.path = {self.path}")
        #print(f"DEBUG Persistence._save: str(self.path) = '{str(self.path)}'")
        #print(f"DEBUG Persistence._save: bool(self.path) = {bool(self.path)}")
        #print(f"DEBUG Persistence._save: data = {data}")

        if invalidpath(self.path):
            #print("DEBUG Persistence._save: Empty path, returning early")
            return

        path = Path(self.path)
        #print(f"DEBUG Persistence._save: Creating directories for {path.parent}")
        path.parent.mkdir(parents=True, exist_ok=True)

        #print(f"DEBUG Persistence._save: Writing to file {path}")
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        #print(f"DEBUG Persistence._save: File written successfully")

    def _load(self) -> t.Dict[str, t.Any]:
        """Load from JSON File"""
        #print(f"DEBUG Persistence._load: self.path = {self.path}")
        #print(f"DEBUG Persistence._load: str(self.path) = '{str(self.path)}'")

        if invalidpath(self.path):
            #print("DEBUG Persistence._load: Empty path, returning {}")
            return {}

        path = Path(self.path)
        #print(f"DEBUG Persistence._load: Checking if {path} exists: {path.exists()}")
        if not path.exists():
            #print("DEBUG Persistence._load: File doesn't exist, returning {}")
            return {}

        #print(f"DEBUG Persistence._load: Reading from file {path}")
        with open(path, 'r') as f:
            data = json.load(f)
        #print(f"DEBUG Persistence._load: Loaded data = {data}")
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
