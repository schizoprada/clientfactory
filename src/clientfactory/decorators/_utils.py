# ~/clientfactory/src/clientfactory/decorators/_utils.py
from __future__ import annotations
import typing as t


def buildclassdict(
    target: t.Type,
    descriptors: bool = True,
    dunders: t.Optional[t.Set[str]] = None
) -> t.Dict[str, t.Any]:
    """
    Build classdict from target class, preserving descriptors.

    Args:
        target: Source class to copy attributes from
        descriptors: Whether to preserve property/descriptor objects
        dunders: Additional dunder names to include beyond defaults
    """
    classdict = {}
    defaultdunders = {'__doc__', '__module__', '__qualname__', '__annotations__'}
    alldunders = defaultdunders | (dunders or set())

    for attrname in dir(target):
        if attrname.startswith('__') and (attrname not in alldunders):
            continue
        try:
            if all((
                descriptors,
                hasattr(target, '__dict__'),
                attrname in target.__dict__
            )):
                classdict[attrname] = target.__dict__[attrname]
            else:
                classdict[attrname] = getattr(target, attrname)
        except (AttributeError, TypeError):
            continue

    return classdict

def annotate(
    transformed: t.Type,
    base: t.Type,
    components: t.Optional[t.Dict[str, t.Any]] = None,
    **additional
) -> None:
    """Apply declarative attribute annotations to transformed class for IDE support."""

    # get declarative attributes
    declattrs = getattr(base, '__declattrs__', set())
    declconfs = getattr(base, '__declconfs__', set())
    declcomps = getattr(base, '__declcomps__', set())
    detectedcomps = detectcomponents(declcomps, transformed)

    if any((declattrs, declconfs, declcomps, components, detectedcomps, additional)):
        transformed.__annotations__ = getattr(transformed, '__annotations__', {})
        baseannotations = getattr(base, '__annotations__', {})

        # add declarative attributes
        for attr in declattrs:
            transformed.__annotations__[attr] = baseannotations.get(attr, str)

        # add declarative configs
        for conf in declconfs:
            transformed.__annotations__[conf] = baseannotations.get(conf, t.Any)

        # add component declarations
        for comp in declcomps:
            transformed.__annotations__[f'__{comp}__'] = t.Any

        # annotate detected components (specific types)
        if detectedcomps:
            annotatecomponents(transformed, detectedcomps)

        # annotate explicitly provided components (override detected)
        if components:
            annotatecomponents(transformed, components)

        # add additional annotations
        if additional:
            transformed.__annotations__.update(additional)

def detectcomponents(declared: set[str], transformed: t.Type) -> t.Dict:
    """Auto-detect components from class attributed (for decorator-added components)"""
    detected = {}
    for comp in declared:
        dunder = f'__{comp}__'
        if hasattr(transformed, dunder):
            value = getattr(transformed, dunder)
            if isinstance(value, type):
                detected[comp] = value
            else:
                detected[comp] = value.__class__
    return detected

def annotatecomponents(cls: t.Type, components: t.Dict[str, t.Any]) -> None:
    """Add component-specific annotations"""
    if not hasattr(cls, '__annotations__'):
        cls.__annotations__ = {}

    for cname, ctype in components.items():
        cls.__annotations__[f'__{cname}__'] = ctype
        cls.__annotations__[f'_{cname}'] = ctype
