# ~/clientfactory/src/clientfactory/core/utils/discover/collect.py
"""..."""
import typing as t

leadingunderscore = lambda v: v.startswith('_')

def classdeclarations(c: t.Any, skips: t.Optional[t.List[t.Callable[[str], bool]]] = [leadingunderscore], explicit: t.Optional[set] = None, filternone: bool = True) -> dict:
    """..."""
    skips = (skips or [])
    explicit = (explicit or set())
    shouldskip = lambda a: any(skip(a) for skip in skips) or (a not in explicit)
    declarations = {}

    for attr in dir(c):
        if shouldskip(attr):
            continue
        value = getattr(c, attr, None)
        declarations[attr] = value

    if filternone:
        return {
            k:v for k,v in declarations.items()
            if v is not None
        }
    return declarations
