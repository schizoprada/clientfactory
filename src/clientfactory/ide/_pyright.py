# ~/clientfactory/src/clientfactory/ide/_pyright.py
"""
Pyright configuration utilities for ClientFactory.
"""
import os, json, typing as t
from pathlib import Path

CONFIG: dict = {
   "reportAttributeAccessIssue": "none",
   "reportUnknownMemberType": "none",
   "reportGeneralTypeIssues": "none",
   "typeCheckingMode": "basic"
}

def getconfig() -> dict:
    return CONFIG.copy()

def merge(extant: dict) -> dict:
    merged = extant.copy()
    merged.update(getconfig())
    return merged


def findroot(start: t.Optional[Path] = None) -> Path:
    if start is None:
        start = Path.cwd()

    current = start.resolve()

    indicators = {
        'pyproject.toml', 'setup.py', 'setup.cfg',
        '.git', 'requirements.txt', 'Pipfile',
        'poetry.lock', 'package.json'
    }
    while (current != current.parent):
        if any(
            (current / indicator).exists() for indicator in indicators
        ):
            return current
        current = current.parent

    return Path.cwd()



def setup(path: t.Optional[Path] = None, force: bool = False) -> bool:
    if path is None:
        path = findroot()

    file = path / "pyrightconfig.json"

    if file.exists() and not force:
        try:
            with open(file, 'r') as f:
               extant = json.load(f)
            merged = merge(extant)
        except (json.JSONDecodeError, IOError):
            import warnings
            warnings.warn(f"Could not read {file}, creating new one")
            merged = getconfig()
    else:
        merged = getconfig()

    try:
        with open(file, 'w') as f:
           json.dump(merged, f, indent=2)
        print(f"✓ Pyright configuration updated at {file}")
        return True
    except IOError as e:
        print(f"Error: could not write Pyright configuration: {e}")
        return False


def checkcompatibility() -> dict:
    file = findroot() / "pyrightconfig.json"

    if not file.exists():
        return {
            "compatible": False,
            "missing": {
                "file": True
            },
            "recommendations": [""]
        }

    try:
        with open(file, 'r') as f:
            current = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "compatible": False,
            "invalid": True,
            "recommendations": [""]
        }

    missing = [
        f"{k}: {v}" for k,v in getconfig().items()
        if current.get(k) != v
    ]

    return {
        "compatible": (len(missing) == 0),
        "missing": {
            "settings": missing
        },
        "recommendations": [""]
    }
