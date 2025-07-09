# ~/clientfactory/src/clientfactory/decorators/resources.py
"""
Resource Decorators
------------------
Decorators for transforming classes into specialized resource types.
"""
from __future__ import annotations
import typing as t

from clientfactory.core import Resource
from clientfactory.resources import SearchResource, ManagedResource, ViewResource
from clientfactory.core.models import ResourceConfig, SearchResourceConfig, MergeMode
from clientfactory.decorators._utils import annotate, buildclassdict
from clientfactory.logs import log

def _transformtoresource(
    target: t.Type,
    variant: t.Type,
    config: t.Optional[t.Any] = None,
    name: t.Optional[str] = None,
    path: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Type:
    """
    Transform a target class into the specified resource type.
    """
    comps = {f'__{comp}__' for comp in (variant.__declcomps__ | getattr(target, '__declcomps__', set()))}


    # collect attributes from target first
    classdict = buildclassdict(target, dunders=comps)

    noneor = lambda k: kwargs.get(k) if k in kwargs and kwargs[k] is not None else classdict.get(k)

    # separate config attributes from class attributes
    declconfs = variant.__declconfs__ if hasattr(variant, '__declconfs__') else set()
    declattrs = variant.__declattrs__ if hasattr(variant, '__declattrs__') else set()

    # build config if not provided
    if config is None:
        # Merge decorator params with class attributes, decorator params take precedence
        confkwargs = {
            'name': (name or classdict.get('name') or target.__name__.lower()),
            'path': (path or classdict.get('path') or (name or target.__name__.lower())),
        }

        for attr in declconfs:
            value = noneor(attr)
            if value is not None:
                confkwargs[attr] = value


        if variant == SearchResource:
            config = SearchResourceConfig(**confkwargs)
        else:
            config = ResourceConfig(**confkwargs)

    for attr in declattrs:
        value = noneor(attr)
        if value is not None:
            classdict[attr] = value


    classdict['_resourceconfig'] = config

    new = type(target.__name__, (variant,), classdict)
    new.__module__ = target.__module__
    new.__qualname__ = target.__qualname__
    annotate(new, variant)
    return new


## overloads ##
@t.overload
def resource(cls: t.Type, /) -> t.Type[Resource]: ...

@t.overload
def resource(
    *,
    config: t.Optional[ResourceConfig] = None,
    name: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Callable[[t.Type], t.Type[Resource]]: ...

def resource(
    cls: t.Optional[t.Type] = None,
    *,
    config: t.Optional[ResourceConfig] = None,
    name: t.Optional[str] = None,
    path: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Union[t.Type[Resource], t.Callable[[t.Type], t.Type[Resource]]]:
    """
    Transform a class into a basic Resource.

    Args:
        cls: Class to transform (when used without parentheses)
        config: Pre-configured ResourceConfig object
        name: Resource name (defaults to class name lowercase)
        path: Resource path (defaults to name)
        **kwargs: Additional resource configuration

    Example:
        @resource
        class Users: pass

        @resource(path="v2/users")
        class Users: pass

        @resource(config=UsersConfig)
        class Users: pass
    """
    def decorator(target: t.Type) -> t.Type[Resource]:
        return _transformtoresource(
            target=target,
            variant=Resource,
            config=config,
            name=name,
            path=path,
            **kwargs
        )

    if cls is not None:
        return decorator(cls)
    return decorator


## overloads ##
@t.overload
def searchable(cls: t.Type, /) -> t.Type[SearchResource]: ...

@t.overload
def searchable(
    *,
    config: t.Optional[SearchResourceConfig] = None,
    name: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Callable[[t.Type], t.Type[SearchResource]]: ...

def searchable(
   cls: t.Optional[t.Type] = None,
   *,
   config: t.Optional[SearchResourceConfig] = None,
   name: t.Optional[str] = None,
   path: t.Optional[str] = None,
   payload: t.Optional[t.Any] = None,
   method: t.Optional[str] = None,
   searchmethod: str = "search",
   oncall: bool = False,
   headers: t.Optional[t.Dict[str, str]] = None,
   cookies: t.Optional[t.Dict[str, str]] = None,
   headermode: t.Optional[MergeMode] = None,
   cookiemode: t.Optional[MergeMode] = None,
   timeout: t.Optional[float] = None,
   retries: t.Optional[int] = None,
   preprocess: t.Optional[t.Callable] = None,
   postprocess: t.Optional[t.Callable] = None,
   **kwargs: t.Any
) -> t.Union[t.Type[SearchResource], t.Callable[[t.Type], t.Type[SearchResource]]]:
    """
    Transform a class into a SearchResource.

    Args:
        cls: Class to transform (when used without parentheses)
        config: Pre-configured SearchResourceConfig object
        name: Resource name (defaults to class name lowercase)
        path: Resource path (defaults to name)
        payload: Payload class for search parameter validation
        method: HTTP method for search (GET/POST)
        searchmethod: Name of the search method (default: "search")
        oncall: Whether to make the resource instance callable
        headers: Method-specific headers
        cookies: Method-specific cookies
        headermode: How to merge method headers with session headers
        cookiemode: How to merge method cookies with session cookies
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        preprocess: Function to transform request data
        postprocess: Function to transform response data
        **kwargs: Additional search resource configuration

    Example:
        @searchable
        class UserSearch: pass

        @searchable(payload=UserSearchPayload, oncall=True, timeout=60.0)
        class UserSearch: pass

        @searchable(headers={"X-API-Key": "secret"}, headermode=MergeMode.OVERWRITE)
        class UserSearch: pass

        @searchable(config=SearchConfig)
        class UserSearch: pass
    """
    from clientfactory.core.utils.discover import collect
    from clientfactory.core.utils.parameters import construct
    def decorator(target: t.Type) -> t.Type[SearchResource]:
        #print(f"DEBUG searchable decorator: target = {target}")
        #print(f"DEBUG searchable decorator: dir(target) = {[attr for attr in dir(target) if not attr.startswith('_')]}")
        #print(f"DEBUG searchable decorator: target.payload = {getattr(target, 'payload', 'NOT_FOUND')}")

        sigparams = construct.sigparams(
            filternone=True,
            config=config,
            name=name,
            path=path,
            payload=payload,
            method=method,
            searchmethod=searchmethod,
            oncall=oncall,
            headers=headers,
            cookies=cookies,
            headermode=headermode,
            cookiemode=cookiemode,
            timeout=timeout,
            retries=retries,
            preprocess=preprocess,
            postprocess=postprocess
        )
        #print(f"DEBUG searchable decorator: sigparams = {sigparams}")

        declared = collect.classdeclarations(target, explicit=SearchResource.__declattrs__)
        #print(f"DEBUG searchable decorator: declared = {declared}")

        sigparams.update(declared)
        #print(f"DEBUG searchable decorator: (after update) sigparams = {sigparams}")

        return _transformtoresource(
            target=target,
            variant=SearchResource,
            **sigparams,
            **kwargs
        )

    if cls is not None:
        return decorator(cls)
    return decorator


## overloads ##
@t.overload
def manageable(cls: t.Type, /) -> t.Type[ManagedResource]: ...

@t.overload
def manageable(
    *,
    config: t.Optional[ResourceConfig] = None,
    crud: t.Optional[t.Set[str]] = None,
    **kwargs: t.Any
) -> t.Callable[[t.Type], t.Type[ManagedResource]]: ...

def manageable(
   cls: t.Optional[t.Type] = None,
   *,
   config: t.Optional[ResourceConfig] = None,
   name: t.Optional[str] = None,
   path: t.Optional[str] = None,
   crud: t.Optional[t.Set[str]] = None,
   **kwargs: t.Any
) -> t.Union[t.Type[ManagedResource], t.Callable[[t.Type], t.Type[ManagedResource]]]:
    """
    Transform a class into a ManagedResource with CRUD operations.

    Args:
        cls: Class to transform (when used without parentheses)
        config: Pre-configured ResourceConfig object
        name: Resource name (defaults to class name lowercase)
        path: Resource path (defaults to name)
        crud: Set of CRUD operations to generate {'create', 'read', 'update', 'delete', 'list'}
        **kwargs: Additional managed resource configuration

    Example:
        @manageable
        class Users: pass

        @manageable(crud={'create', 'read', 'update', 'delete'})
        class Users: pass

        @manageable(config=ManagedConfig)
        class Users: pass
    """
    def decorator(target: t.Type) -> t.Type[ManagedResource]:
        transformed = _transformtoresource(
            target=target,
            variant=ManagedResource,
            config=config,
            name=name,
            path=path,
            **kwargs
        )
        if crud is not None:
            transformed.__crud__ = crud
        return transformed
    if cls is not None:
        return decorator(cls)
    return decorator


## Viewable ##
### overloads ###
@t.overload
def viewable(cls: t.Type, /) -> t.Type[ViewResource]: ...

@t.overload
def viewable(
    *,
    config: t.Optional[ResourceConfig] = None,
    name: t.Optional[str] = None,
    **kwargs: t.Any
) -> t.Callable[[t.Type], t.Type[ViewResource]]: ...


def viewable(
   cls: t.Optional[t.Type] = None,
   *,
   config: t.Optional[ResourceConfig] = None,
   name: t.Optional[str] = None,
   path: t.Optional[str] = None,
   payload: t.Optional[t.Any] = None,
   method: t.Optional[str] = None,
   viewmethod: str = "view",
   viewpath: str = "{id}",
   headers: t.Optional[t.Dict[str, str]] = None,
   cookies: t.Optional[t.Dict[str, str]] = None,
   headermode: t.Optional[MergeMode] = None,
   cookiemode: t.Optional[MergeMode] = None,
   timeout: t.Optional[float] = None,
   retries: t.Optional[int] = None,
   preprocess: t.Optional[t.Callable] = None,
   postprocess: t.Optional[t.Callable] = None,
   **kwargs: t.Any
) -> t.Union[t.Type[ViewResource], t.Callable[[t.Type], t.Type[ViewResource]]]:
    """
    Transform a class into a ViewResource.

    Args:
        cls: Class to transform (when used without parentheses)
        config: Pre-configured ResourceConfig object
        name: Resource name (defaults to class name lowercase)
        path: Resource path (defaults to name)
        payload: Payload class for view parameter validation
        method: HTTP method for view (GET/POST)
        viewmethod: Name of the view method (default: "view")
        viewpath: Path template for view endpoint (default: "{id}")
        headers: Method-specific headers
        cookies: Method-specific cookies
        headermode: How to merge method headers with session headers
        cookiemode: How to merge method cookies with session cookies
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        preprocess: Function to transform request data
        postprocess: Function to transform response data
        **kwargs: Additional view resource configuration

    Example:
        @viewable
        class ItemView: pass

        @viewable(payload=ItemViewPayload, viewpath="{category}/{id}", timeout=30.0)
        class ItemView: pass

        @viewable(headers={"X-API-Key": "secret"}, headermode=MergeMode.OVERWRITE)
        class ItemView: pass

        @viewable(config=ViewConfig)
        class ItemView: pass
    """
    from clientfactory.core.utils.discover import collect
    from clientfactory.core.utils.parameters import construct

    def decorator(target: t.Type) -> t.Type[ViewResource]:
        sigparams = construct.sigparams(
            filternone=True,
            config=config,
            name=name,
            path=path,
            payload=payload,
            method=method,
            viewmethod=viewmethod,
            viewpath=viewpath,
            headers=headers,
            cookies=cookies,
            headermode=headermode,
            cookiemode=cookiemode,
            timeout=timeout,
            retries=retries,
            preprocess=preprocess,
            postprocess=postprocess
        )

        declared = collect.classdeclarations(target, explicit=ViewResource.__declattrs__)
        sigparams.update(declared)

        return _transformtoresource(
            target=target,
            variant=ViewResource,
            **sigparams,
            **kwargs
        )

    if cls is not None:
        return decorator(cls)
    return decorator
