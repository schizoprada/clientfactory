# ~/clientfactory/src/clientfactory/core/utils/session/meta.py
"""
Session metadata utilities for decorator functions.
"""
from __future__ import annotations
import typing as t

from clientfactory.logs import log

from clientfactory.core.models.contexts import HeaderMetadata, SessionMetadata

if t.TYPE_CHECKING:
    from clientfactory.core.models.methods import BoundMethod

def ensuresessionmeta(func: t.Callable) -> t.Callable:
    """
    Ensure function has properly initialized _sessionmeta attribute structure.

    Initializes _sessionmeta dict with headers sub-dict if not present.
    Future-ready for cookies and auth metadata expansion.

    Args:
        func: Function to ensure session metadata on

    Returns:
        Same function with initialized _sessionmeta structure
    """
    if not hasattr(func, '_sessionmeta'):
        func._sessionmeta = {}

    if 'headers' not in func._sessionmeta:
        func._sessionmeta['headers'] = {}

    # add similar checks for cookies/auth when implemented
    return func

def getsessionmeta(func: t.Union['BoundMethod', t.Callable]) -> t.Dict:
    """
    Extract session metadata from function or BoundMethod.

    Handles both direct functions with _sessionmeta and BoundMethod
    objects where metadata is stored on the wrapped function.

    Args:
        func: Function or BoundMethod to extract metadata from

    Returns:
        Session metadata dict, empty if none found
    """
    log.critical(f"(getsessionmeta)@[{func.__name__}] func.__dict__: {func.__dict__}")
    log.critical(f"(getsessionmeta)@[{func.__name__}] dir(func): {dir(func)}")
    if hasattr(func, '_sessionmeta'):
        meta = getattr(func, '_sessionmeta', {})
        log.critical(f"(getsessionmeta)@[{func.__name__}] _sessionmeta extracted directly: {meta}")
        return meta
    elif hasattr(func, '_func') and hasattr(func._func, '_sessionmeta'):
        meta = getattr(func._func, '_sessionmeta', {})
        log.critical(f"(getsessionmeta)@[{func.__name__}] _sessionmeta extracted from ._func: {meta}")
        return meta
    else:
        log.critical(f"(getsessionmeta)@[{func.__name__}] no _sessionmeta found")
        return {}


class metasession:

    @staticmethod
    def getheaders(obj: t.Any) -> t.Dict[str, str]:
        """
        Get current session headers as dict, regardless of session object type.

        Args:
            obj: Session object (requests.Session, dict, or custom)

        Returns:
            Dict of current headers
        """
        log.critical(f"(metasession.getheaders) extracting headers from {type(obj).__name__}")

        if hasattr(obj, 'headers'):
            # requests.Session style: obj.headers
            headers = dict(obj.headers)
            log.critical(f"(metasession.getheaders) extracted via .headers attribute: {len(headers)} headers")
            return headers
        elif isinstance(obj, dict) and 'headers' in obj:
            # Dict style: obj['headers']
            headers = obj['headers'].copy()
            log.critical(f"(metasession.getheaders) extracted via ['headers'] key: {len(headers)} headers")
            return headers
        elif hasattr(obj, 'getheaders'):
            # Custom session with getheaders method
            headers = obj.getheaders()
            log.critical(f"(metasession.getheaders) extracted via .getheaders() method: {len(headers)} headers")
            return headers
        else:
            # Fallback to empty dict
            log.critical(f"(metasession.getheaders) no compatible header access found, returning empty dict")
            return {}

    @staticmethod
    def setheaders(obj: t.Any, headers: t.Dict[str, str]) -> t.Any:
        """
        Set session headers, regardless of session object type.

        Args:
            obj: Session object to update
            headers: Headers dict to set

        Returns:
            Updated session object
        """
        log.critical(f"(metasession.setheaders) setting {len(headers)} headers on {type(obj).__name__}")

        if hasattr(obj, 'headers'):
            # requests.Session style: obj.headers
            obj.headers.clear()
            obj.headers.update(headers)
            log.critical(f"(metasession.setheaders) updated via .headers attribute")
            return obj
        elif isinstance(obj, dict) and 'headers' in obj:
            # Dict style: obj['headers']
            obj['headers'] = headers
            log.critical(f"(metasession.setheaders) updated via ['headers'] key")
            return obj
        elif hasattr(obj, 'setheaders'):
            # Custom session with setheaders method
            result = obj.setheaders(headers)
            log.critical(f"(metasession.setheaders) updated via .setheaders() method")
            return result if result is not None else obj
        else:
            log.critical(f"(metasession.setheaders) no compatible header setting method found")
            return obj

class metaheaders:

    @staticmethod
    def applyadd(
        current: t.Dict[str, str],
        new: t.Dict[str, str],
        options: t.Union[bool, t.List[str]],
        ignoreable: t.Optional[t.List[str]] = None
    ) -> t.Dict[str, str]:
        """Add headers from response to session based on configuration."""
        log.critical(f"""
            (metaheaders.applyadd)
            current: {current}

            new: {new}

            options: {options}

            ignoreable: {ignoreable}
            """)
        ignore = (ignoreable or [])
        added = current.copy()

        notpresent = lambda header: (header not in current)
        shouldignore = lambda header: any(header.lower() == ig.lower() for ig in ignore)
        shouldadd = lambda header: notpresent(header) and (not shouldignore(header))
        matchestarget = lambda header, target: header.lower() == target.lower()

        if options is True:
            for header, value in new.items():
                if shouldadd(header):
                    added[header] = value
        else:
            for target in options:
                if not shouldignore(target):
                    for header, value in new.items():
                        if matchestarget(header, target) and notpresent(header):
                            added[header] = value

        log.critical(f"(metaheaders.applyadd) returning: {added}")

        return added

    @staticmethod
    def applyupdate(
        current: t.Dict[str, str],
        new: t.Dict[str, str],
        options: t.Union[bool, t.List[str]],
        ignoreable: t.Optional[t.List[str]] = None
    ) -> t.Dict[str, str]:
        """Update existing session headers with response values."""
        log.critical(f"""
            (metaheaders.applyupdate)
            current: {current}

            new: {new}

            options: {options}

            ignoreable: {ignoreable}
            """)
        ignore = (ignoreable or [])
        updated = current.copy()

        ispresent = lambda header: (header in current)
        shouldignore = lambda header: any(header.lower() == ig.lower() for ig in ignore)
        shouldupdate = lambda header: ispresent(header) and (not shouldignore(header))
        matchestarget = lambda header, target: header.lower() == target.lower()

        if options is True:
            for header, value in new.items():
                if shouldupdate(header):
                    updated[header] = value
        else:
            for target in options:
                if not shouldignore(target):
                    for header, value in new.items():
                        if matchestarget(header, target) and ispresent(header):
                            updated[header] = value

        log.critical(f"(metaheaders.applyupdate) returning: {updated}")
        return updated

    @staticmethod
    def applydiscard(
        current: t.Dict[str, str],
        options: t.Union[bool, t.List[str]]
    ) -> t.Dict[str, str]:
        """Remove headers from session based on configuration."""
        log.critical(f"""
            (metaheaders.applydiscard)
            current: {current}

            options: {options}
            """)
        discarded = current.copy()

        matchestarget = lambda header, target: header.lower() == target.lower()

        if options is True:
            discarded.clear()
        else:
            for target in options:
                headers_to_remove = [h for h in discarded if matchestarget(h, target)]
                for header in headers_to_remove:
                    del discarded[header]

        log.critical(f"(metaheaders.applydiscard) returning: {discarded}")
        return discarded
