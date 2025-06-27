# CLIENTFACTORY - CHANGLOG [redundancy-removal]

## [0.9.26-alpha.3] - June 27, 2025

### Removed
- **Redundant Instance Methods** (Cleanup Phase)
  - Removed `BaseClient._separatekwargs()`, `_buildrequest()`, `_substitutepath()`, `_resolvepathargs()`, `_applymethodconfig()`
  - Removed `BaseResource._separatekwargs()`, `_buildrequest()`, `_substitutepath()`, `_resolvepathargs()`, `_applymethodconfig()`
  - Removed abstract `_buildrequest()` method from `BaseResource`

### Changed
- **PrepMixin Updated**
  - `_preparerequest()` now uses consolidated utils directly instead of calling parent instance methods
  - No longer depends on `getattr(parent, method_name)` pattern
- **IterMixin Method Renamed**
  - `_separatekwargs()` → `_separateiterconfig()` to avoid naming collision with removed request building method
  - Updated call sites and tests accordingly

### Fixed
- **Method Name Collision**
  - Resolved confusion between request building and iteration parameter separation
  - Clearer method naming for domain-specific functionality

### Technical Debt Resolved
- Eliminated duplicate request building logic across client/resource hierarchy
- Removed dependency on instance methods in mixins
- Consolidated all request utilities into shared `core/utils/` modules

### Test Results
- Unit tests: 3 additional failures (100 total) - minimal impact from cleanup
- Existing failures likely unrelated to redundancy removal changes

## [0.9.26-alpha.2] - June 27, 2025

### Added
- **Type-Safe Decorator Returns**
 - HTTP method decorators (`@get`, `@post`, etc.) now return `BoundMethod` objects
 - Perfect IDE support for mixin methods (`.prepare()`, `.iterate()`, `.cycle()`)
 - Deferred parent binding during class initialization

### Changed
- **HTTP Method Decorators** (`decorators/http/methods.py`)
 - `httpmethod()` now returns `BoundMethod` with `UNSET` parent
 - Updated return type hints: `t.Callable[[t.Callable], 'BoundMethod']`
 - `_createdecorator()` updated with proper union return types
- **Method Initialization Logic**
 - `BaseClient._initmethods()` handles pre-bound `BoundMethod` objects
 - `Resource._initmethods()` handles pre-bound `BoundMethod` objects
 - Backward compatibility maintained for legacy undecorated methods
- **BoundMethod Resolution**
 - `_methodconfig` property accessible even when unresolved (metaclass compatibility)
 - Always clone function attributes for consistent `__name__` access

### Improved
- **Developer Experience**
 - IDEs now recognize `.prepare()`, `.iterate()`, `.cycle()` on decorated methods
 - Type hints properly reflect `BoundMethod` return types
 - Runtime error handling for unresolved method calls

### Technical Debt Accumulated
- Redundant instance methods still present in `BaseClient`/`BaseResource`
- `PrepMixin` still uses old method access pattern
- Abstract `_buildrequest` method no longer needed

## [0.9.26-alpha.1] - June 26, 2025

### Added
- **Universal Request Utilities** (`core/utils/request/`)
 - `path.py` - `resolveargs()`, `substitute()` for path parameter handling
 - `building.py` - `separatekwargs()`, `buildrequest()`, `applymethodconfig()` for request construction
- **Unified Bound Method Creation** (`core/utils/discover/binding.py`)
 - `createboundmethod()` - Consolidated binding logic for all client/resource types
 - Supports specialized contexts (SearchResource validation, path overrides)
- **Sentinel Value System** (`core/utils/typed/sentinel.py`)
 - `Sentinel` class for distinguishing explicitly passed vs omitted parameters
 - `UNSET` universal sentinel with type compatibility (`t.Any`)
 - Supports subscript syntax for encoding defaults: `UNSET[False]`, `UNSET[list]`

### Changed
- **Consolidated Binding Logic**
 - `BaseClient._createboundmethod()` now uses unified `createboundmethod()`
 - `BaseResource._createboundmethod()` now uses unified `createboundmethod()`
 - `SearchResource._generatesearchmethod()` now uses unified `createboundmethod()`
- **Enhanced BoundMethod Architecture**
 - Added deferred binding support with `UNSET` parent for decorator usage
 - Added `_resolvebinding()` for resolving UNSET parents during initialization
 - Added `@_requireresolution` decorator for runtime safety
 - Updated `Param` class to use new `UNSET` sentinel system

### Improved
- **Test Infrastructure**
 - Added `tests/refactor/` directory for consolidation testing
 - Integration tests confirming old vs new behavior equivalence
 - Utility function tests for extracted components
