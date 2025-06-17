# ~/clientfactory/src/clientfactory/decorators/resources.py
"""
Resource Decorators
------------------
Decorators for transforming classes into specialized resource types.
"""
from __future__ import annotations
import typing as t

from clientfactory.core import Resource
from clientfactory.resources import SearchResource, ManagedResource
from clientfactory.core.models import ResourceConfig, SearchResourceConfig
from clientfactory.decorators._utils import annotate

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

    This creates a new class that inherits from the (resource) variant while
    preserving all attributes and methods from the target.
    """
    # build config if not provided
    if config is None:
        confkwargs = {
            k:v for k,v in {
                'name': (name or target.__name__.lower()),
                'path': path or (name or target.__name__.lower()),
                **kwargs
            }.items() if v is not None
        }

        #! NEED TO IMPLEMENT CONFIG-TYPE DECLARATION
        if variant == SearchResource:
            config = SearchResourceConfig(**confkwargs)
        else:
            config = ResourceConfig(**confkwargs)

    # collect attributes from target
    classdict = {}
    for attrname in dir(target):
        if not attrname.startswith('__') or attrname in ('__doc__', '__module__', '__qualname__', '__annotations__'):
            classdict[attrname] = getattr(target, attrname)

    classdict['_resourceconfig'] = config # i thought we werent using this shit anymore

    new = type(
        target.__name__,
        (variant,),
        classdict
    )
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
        **kwargs: Additional search resource configuration

    Example:
        @searchable
        class UserSearch: pass

        @searchable(payload=UserSearchPayload, oncall=True)
        class UserSearch: pass

        @searchable(config=SearchConfig)
        class UserSearch: pass
    """
    def decorator(target: t.Type) -> t.Type[SearchResource]:
        conf = config # type: ignore  #! possible unbound
        if conf is None:
            confkwargs = {
                k: v for k, v in {
                    'name': name or target.__name__.lower(),
                    'path': path or (name or target.__name__.lower()),
                    'payload': payload,
                    'method': method,
                    'searchmethod': searchmethod,
                    'oncall': oncall,
                    **kwargs
                }.items() if v is not None
            }
            conf = SearchResourceConfig(**confkwargs)

        return _transformtoresource(
            target=target,
            variant=SearchResource,
            config=conf,
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
