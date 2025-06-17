# ~/clientfactory/src/clientfactory/decorators/_utils.py
from __future__ import annotations
import typing as t


def annotate(
    transformed: t.Type,
    base: t.Type,
    **additional
) -> None:
    """Apply declarative attribute annotations to transformed class for IDE support."""

    # get declarative attributes
    declattrs = getattr(base, '__declattrs__', set())
    declconfs = getattr(base, '__declconfs__', set())

    if any((declattrs, declconfs, additional)):
        transformed.__annotations__ = getattr(transformed, '__annotations__', {})
        baseannotations = getattr(base, '__annotations__', {})

        for attr in declattrs:
            transformed.__annotations__[attr] = baseannotations.get(attr, str)

        for conf in declconfs:
            transformed.__annotations__[conf] = baseannotations.get(conf, t.Any)

        if additional:
            transformed.__annotations__.update(additional)
