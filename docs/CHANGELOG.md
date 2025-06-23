# CLIENTFACTORY - CHANGELOG

## [0.9.1] -- *2025-06-23*
* Smart Requesting Utilities: Advanced parameter iteration with comprehensive cycle support and error handling
+ Parameter Iteration Framework: Complete system for iterating over method parameters with multi-pattern support
- IterCycle model with numeric generation (start/end/step), explicit values, and Param inference from metadata
- Smart parameter discovery: automatic detection of page/pagination parameters from path templates and payload classes
- Multiple iteration patterns: direct kwargs, builder methods, static parameter management, namespace conflict resolution
- Support for dict-based iteration (BRANDS mapping), list-based iteration, and complex nested cycles
- Step filtering with callable filters and numeric stepping for advanced value selection
+ Enhanced BoundMethod Architecture: Integration of iteration capabilities with existing method infrastructure
- BoundMethod class now inherits from IterMixin providing iteration capabilities to all HTTP methods
- Updated _createboundmethod() in BaseClient, BaseResource, SearchResource, and ManagedResource
- Seamless integration maintaining backward compatibility with existing method decoration system
- All decorated methods (@get, @post, @searchable, @manageable) now support parameter iteration
+ Comprehensive Error Handling: Configurable error strategies with retry logic and callback support
- ErrorHandles enum: CONTINUE (skip failed iterations), STOP (halt on error), RETRY (with exponential backoff), CALLBACK (user-defined logic)
- Built-in retry mechanism with configurable maxretries, retrydelay, and intelligent error propagation
- Callback system with defined signature: ErrorCallback = Callable[[Exception, IterCycle], bool]
- Proper error isolation: cycle-level errors don't terminate primary iteration, enabling robust batch processing
+ Multi-Pattern Parameter Support: Flexible approaches for different use cases and coding styles
- Builder pattern: method.range(1, 10).values(['a','b']).withparams(x=1).iterate('param')
- Static parameter management: method.withparams(category='shoes').iterate('page', start=1, end=10)
- Namespace conflict resolution: _prefixed parameters for iteration vs static parameter disambiguation
- Direct specification: method.iterate('page', start=1, end=10, static={'category': 'shoes'})
+ Sequential Cycle Support: Advanced iteration patterns for complex API workflows
- Primary parameter with nested cycles: iterate brands, complete all pages for each brand before advancing
- Configurable cycle modes (SEQUENTIAL implemented, NESTED and PARALLEL deferred)
- Cycle-specific error handling allowing granular control over iteration behavior
- Reusable IterCycle objects for consistent iteration patterns across methods
+ Enhanced Payload Integration: Smart parameter extraction and iteration support
- Payload.paramnames() convenience method for parameter introspection
- Automatic payload parameter discovery in _collectiterables() for method-aware iteration
- Enhanced SearchResource._generatesearchmethod() to include payload in MethodConfig
- Parameter inference from Param metadata including mapping values/keys and choices
+ Infrastructure Improvements: Core enhancements supporting iteration functionality
- MethodConfig.pathparams() convenience method for path parameter extraction
- Pydantic configuration fixes with arbitrary_types_allowed for complex type support
- Iterator state management ensuring reusable cycles across multiple primary iterations
- Comprehensive type system with proper generics and protocol adherence

**Use Cases**: API pagination automation, batch data processing, parameter space exploration, A/B testing different parameter combinations, marketplace search optimization

**Deferred for Future Versions**:
- Nested cycle mode (cartesian product iteration)
- Offset/limit parameter detection for pagination APIs
- Execution context tracking for break conditions and consecutive error analysis
- Context managers for scoped parameter setting
- Advanced break condition system with metadata tracking
- Parallel cycle execution for concurrent processing

**Breaking Changes**: None - all changes maintain backward compatibility

**Performance Notes**: Iterator-based design ensures memory efficiency for large parameter spaces; cycle reusability prevents object recreation overhead

## [0.9.0] -- *2025-06-22*
* Gateway Requests: Support for APIs accessed through proxy/gateway endpoints
+ GatewayBackend Implementation: Complete proxy request pattern support for API gateway architectures
- `GatewayBackend` base class for URL encoding and gateway parameter wrapping
- Configurable gateway URL and URL parameter names for different proxy patterns
- Automatic target URL construction with query parameter encoding
- Seamless integration with existing client/resource baseurl and path patterns
- Support for gateway URLs with existing parameters and proper separator handling
+ Declarative Gateway Configuration: Framework integration with existing component architecture
- Added 'gatewayurl' and 'urlparam' to declarative attributes for class-level configuration
- Component resolution support for gateway backend declarations
- Error handling for missing required gateway configuration parameters
- Flexible initialization supporting both constructor and declarative configuration patterns
+ Request Processing Pipeline: Enhanced request formatting for proxy/gateway scenarios
- Gateway request formatting preserves original HTTP method while redirecting to proxy endpoint
- Target URL encoding as query parameters to gateway endpoints
- Support for complex parameter merging (gateway params + original request data)
- Response processing maintains compatibility with existing backend response handling
+ Foundation for Gateway Patterns: Architecture supporting diverse proxy/gateway implementations
- Extensible pattern ready for different gateway formats (query parameter, POST body, custom headers)
- Request tunneling support for API testing environments and corporate gateways
- Gateway debugging and inspection capabilities through existing request/response logging
- Mixin-ready architecture for adding gateway functionality to existing backends

**Use Cases**: API playgrounds (Rakuten), corporate API gateways, request tunneling, API testing environments, proxy-based authentication flows

## [0.8.9] -- *2025-06-22*
* Session Initializers: Dynamic session bootstrapping with request-based initialization
+ SessionInitializer Implementation: Core logic for extracting session state from HTTP requests
- SessionInitializer class with configurable extraction modes (cookies, headers)
- Support for merge strategies: MERGE, OVERWRITE, IGNORE for both cookies and headers
- Self-contained request execution using raw requests library for maximum compatibility
- Flexible object handling: dict-style session objects, requests.Session objects, and generic attribute-based objects
- MergeMode enum for declarative merge behavior configuration
+ Session Integration: Seamless integration with existing session architecture
- Added 'initializer' to BaseSession declarative attributes for automatic discovery
- Integration with Session._setup() and RequestsSession._setup() for automatic initialization
- Component resolution support for declarative session initialization patterns
- Zero breaking changes to existing session functionality
+ Foundation for Advanced Patterns: Architecture ready for future session initialization enhancements
- Protocol foundation established for pluggable initialization strategies
- Request-based initialization pattern ready for browser automation integration
- Session state extraction utilities ready for complex authentication flows
- Error handling framework for failed initialization attempts

**Note**: Core session initializer logic complete. Future versions will add AutomatonAuthInitializer for browser automation, session state persistence integration, and enhanced error handling strategies as outlined in roadmap.

## [0.8.8] -- *2025-06-22*
* Enhanced backend infrastructure and standalone resource architecture with comprehensive payload improvements
+ Enhanced AlgoliaBackend: Universal utilities for real-world Algolia implementations
- `_buildfacetfilters()` method for standard Algolia facet filter construction with mapping support
- `_buildnumericfilters()` method for numeric range filters (min/max patterns, dict formats, single values)
- `_buildstandardparams()` method for common Algolia parameters with snake_case to camelCase conversion
- Updated `_formatrequest()` to integrate all new filter utilities automatically
- Added `facetsmap` and `numerics` to declarative attributes for class-level configuration
- Backward compatibility maintained with existing AlgoliaBackend functionality
+ Standalone Resource Architecture: Independent resource configuration for multi-backend scenarios
- Added `standalone` and `baseurl` to BaseResource declarative attributes (`__declattrs__`)
- Resources can now declare independent baseurls, sessions, and backends
- Updated `_buildrequest()` methods to prefer resource baseurl over client baseurl when available
- Enhanced component resolution logic to support resource-level component declarations
- Enables patterns like Grailed client with standalone Algolia search resource
+ Enhanced Payload System: Improved data transformation and validation capabilities
- Modified `Payload.transform()` to use schematix's `field.assign()` for proper nested structure creation
- Enhanced `BoundPayload.serialize()` with better nested object handling for complex targets
- Added support for multi-value field handling to prevent "unhashable type" errors with lists
- Implemented reusable source definitions with `Sourced.Keyword >> TargetField` composition patterns
- Added conditional field support with dependency resolution for dynamic field behavior
- Improved error handling for missing computed dependencies in non-required conditional fields
- Better integration with schematix mapping and validation pipeline
+ Enhanced Request Processing: Improved parameter handling for GET requests with payloads
- Updated `_separatekwargs()` method to handle GET requests with payload data as query parameters
- Enhanced SearchResource to support GET requests with payload validation
- Fixed component resolution fallback logic for better resource independence
- Improved parameter transformation pipeline for complex API patterns
+ Comprehensive Testing and Validation: Real-world implementation patterns
- Complete Grailed marketplace implementation as validation case
- Enhanced AlgoliaBackend tested with complex filter scenarios
- Standalone resource patterns validated with multi-backend client architectures
- Payload transformation testing with nested structures and conditional fields
+ Foundation for Advanced Patterns: Architecture supporting future enhancements
- Established mixin-ready backend architecture for Phase 2 enhancements
- Component resolution patterns supporting complex inheritance scenarios
- Declarative system enhancements supporting advanced configuration patterns
- Request processing pipeline ready for gateway/proxy request implementations

## [0.8.7] -- *2025-06-19*
* Enhanced decorator ecosystem and session component resolution for real-world client development
+ Declarative Component Preservation: Fixed all transform decorators to preserve declarative attributes during class transformation
- Updated _transformtosession(), _transformtoresource(), _transformtobackend(), _transformtoauth() to preserve __component__ declarations
- Components like __auth__, __persistence__ now properly transferred when decorators create new classes
- Fixes issue where @session decorator wasn't preserving __auth__ declarations from decorated classes
+ Session Upgrade System: Enhanced RequestsEngine to handle session type compatibility and component transfer
- RequestsEngine._setupsession() now upgrades generic Session instances to RequestsSession while preserving configurations
- Automatic component transfer (auth, persistence) during session upgrade process
- Maintains declarative patterns across engine/session boundaries
+ Configuration Resolution: Improved resource decorator configuration merging with class attributes
- Resource decorators now collect class attributes before creating configs
- Decorator parameters take precedence over class attributes for flexible configuration override
- Fixes path and method resolution issues in @searchable decorator
+ Request Debugging: Added noexec parameter across HTTP method chain for request inspection
- Added noexec flag to SearchResource.searchmethod(), BaseResource._createboundmethod(), BaseEngine convenience methods
- Returns prepared RequestModel instead of executing when noexec=True
- Enables debugging of fully prepared requests without network execution
+ SearchResource Enhancements: Fixed method defaults and URL construction for search operations
- Changed SearchResourceConfig default method from GET to POST for search operations
- Fixed URL duplication issue in SearchResource by using empty method path for search endpoints
- Improved path parameter handling and request building for search-specific workflows
+ Schematix Integration: Enhanced None value handling in field mapping system
- Updated schematix _applymapping() to handle None values gracefully in mapping fields
- Prevents mapping errors when optional parameters are not provided
- Maintains backward compatibility while improving robustness for optional API parameters
+ Comprehensive Debug Logging: Added strategic logging throughout component resolution and request pipeline
- Enhanced component discovery debugging with traversal logging and resolution tracking
- Request building pipeline logging for URL construction and header application debugging
- Session initialization and configuration resolution logging for troubleshooting declarative patterns
+ Foundation Established: Complete working pattern for fashion marketplace API clients with declarative components, session management, and request debugging capabilities

## [0.8.6] -- *2025-06-18*
* Complete declarative decorator ecosystem with HTTP contexts, configurations, persistence, engines, and data components
+ HTTP Context Decorators: @headers and @cookies for declarative request context configuration
- Headers and Cookies classes that behave as dict-compatible components with auto-normalization
- Support for class-based definitions, tuple formats, dict merging, and inheritance patterns
- Seamless integration with existing RequestModel pipeline without requiring refactoring
+ Configuration Decorators: @configs.* namespace for declarative configuration object creation
- Transform user classes into AuthConfig, EngineConfig, SessionConfig, ResourceConfig, etc.
- Automatic attribute extraction and config instantiation with zero boilerplate
- Support for all configuration types: auth, backend, client, engine, payload, persistence, resource, session
+ Persistence Decorators: @persistence with format variants for declarative state management
- Base @persistence decorator for general persistence configuration
- Format-specific variants: @persistence.json (implemented), @persistence.pkl (placeholder)
- Integration with existing BasePersistence and Persistence classes
+ Engine Decorators: @engine with library variants for declarative engine selection
- Base @engine decorator defaulting to RequestsEngine for maximum compatibility
- Library-specific variants: @engine.requests (implemented), @engine.httpx (placeholder)
- Dynamic engine mapping system extensible for future HTTP library integrations
+ Data Decorators: @param and @payload for declarative request data component creation
- @param decorator transforms classes into ClientFactory Param instances with schematix integration
- @payload decorator creates Payload classes from field definitions with intelligent class naming
- Support for mixed field types: existing Param instances, dict definitions, tuple configurations, simple defaults
- Full compatibility with schematix Field constructs while maintaining ClientFactory-specific functionality
+ Comprehensive test coverage: 45+ passing tests across all decorator types and edge cases
+ Production-ready declarative framework completing the ClientFactory decorator ecosystem with zero breaking changes to existing components

## [0.8.5] -- *2025-06-17*
* Complete path parameter substitution and conflict resolution system with enhanced request processing
+ Path Parameter Substitution: Full implementation across all resource and client types
- BaseResource and BaseClient: `_substitutepath()` method with template parameter extraction and substitution
- Automatic path parameter consumption to prevent leakage into request payloads
- Support for multiple path parameters with proper error handling for missing values
+ Client-Level HTTP Methods: Comprehensive support for decorated HTTP methods on client classes
- Automatic method discovery and binding in BaseClient with `_initmethods()`
- URL construction pattern: baseurl + method_path for client-level endpoints
- Full integration with engine/session pipeline and backend processing
+ Preprocess Support: Complete implementation of request data preprocessing
- Preprocess functions called on kwargs before path substitution and request building
- Consistent behavior across both client and resource method types
- Integration with path parameter extraction and payload processing
+ Args vs Kwargs Conflict Resolution: Elegant solution for path vs payload parameter conflicts
- Positional arguments map to path parameters by template order
- Keyword arguments reserved for payload data after path parameter extraction
- `_resolvepathargs()` helper method for clean parameter separation
- Fallback behavior: kwargs used for path parameters when args insufficient
+ Enhanced Request Building: Improved request construction with proper parameter separation
- `_separatekwargs()` method distinguishes request fields from body data based on HTTP method
- Clean separation of concerns: path params → URL, remaining kwargs → request body/params
- Support for complex scenarios: multiple path params, payload classes, preprocessing chains
+ Comprehensive test coverage: 24 passing tests across path substitution, client methods, preprocessing, and conflict resolution
+ Production-ready HTTP method decoration system with full parameter handling and zero ambiguity in path vs payload parameter usage

## [0.8.4] -- *2025-06-17*
* Complete decorator system with comprehensive configuration support and enhanced IDE integration
+ HTTP Method Decorators: @get, @post, @put, @patch, @delete, @head, @options with full configuration
- Enhanced MethodConfig integration with payload validation, pre/post processing hooks
- Automatic docstring generation based on payload parameters and method configuration
- Built-in validation preventing invalid patterns (GET with payload, etc.)
+ Resource Decorators: @resource, @searchable, @manageable for specialized resource creation
- Transform user classes into Resource, SearchResource, or ManagedResource components
- Automatic CRUD method generation with @manageable(crud={'create', 'read', 'update'})
- SearchResource payload integration with configurable search methods and callable instances
+ Auth Decorators: @baseauth, @jwt, @dpop for authentication component creation
- Transform user classes into authentication providers with declarative attributes
- JWT and DPoP authentication with configurable tokens, algorithms, and header keys
+ Session Decorators: @basesession, @session for session component creation
- Transform user classes into session managers with component and attribute configuration
+ Backend Decorators: @basebackend, @algolia, @graphql for backend component creation
- Transform user classes into specialized API backends with protocol-specific configuration
+ Enhanced IDE Support: Improved type annotations system with auto-detection of declarative components
- annotate() function with component detection and __annotations__ management
- Better IDE attribute recognition for declarative patterns and transformed classes
+ Comprehensive test coverage: 62 passing tests across all decorator types and configurations
+ Production-ready decorator ecosystem for rapid ClientFactory component development with minimal boilerplate

## [0.8.3] -- *2025-06-16*
* Backend implementations for Algolia and GraphQL APIs with comprehensive functionality
+ AlgoliaBackend: Complete Algolia search API integration
- Multi-index search support with configurable result merging
- Schematix-based parameter conversion and response processing
- Algolia-specific authentication headers and URL construction
- Configurable content types and parameter encoding
- Enhanced error handling for Algolia-specific error responses
+ GraphQLBackend: Basic GraphQL API integration (enhanced features planned)
- Standard GraphQL request formatting (query, variables, operationName)
- Response processing with data/errors extraction
- GraphQL-specific error handling and validation
- Configurable error raising behavior
+ Enhanced schematix integration for consistent data transformation patterns
+ Comprehensive test coverage: 18 passing tests for both backend implementations
+ Foundation established for protocol-specific API backends within V3 declarative framework
+ Note: Advanced GraphQL features (variable validation, query parsing, nested mapping) planned for future release

## [0.8.2] -- *2025-06-16*
* JWT and DPoP authentication implementations
+ JWTAuth: JWT Bearer token authentication with declarative attribute support
- Simple token management with settoken() method
- Automatic "Authorization: Bearer {token}" header application
- Declarative attributes: token, username, password, key, scheme
+ DPOPAuth: DPoP (Demonstration of Proof-of-Possession) authentication
- JWK-based cryptographic proof token generation per request
- EC curve support (P-256, P-384, P-521) with RSA foundation laid
- Request-specific tokens with HTM/HTU claims (method/URL binding)
- Declarative attributes: jwk, algorithm, headerkey
- Configurable header key (default "DPoP")
+ Dependencies: Added PyJWT and cryptography as core dependencies
+ Comprehensive test coverage: 31 passing tests across both authentication types
+ Full V3 declarative framework integration with BaseAuth inheritance
+ Ready for production JWT/DPoP authentication workflows

## [0.8.1] -- *2025-06-15*
* Specialized Resource implementations with declarative CRUD and search functionality
+ SearchResource: Specialized resource for search operations with automatic method generation
 - Auto-generates search() method with payload validation through Payload/Param integration
 - Configurable HTTP method (GET/POST), search method name, and callable instance support
 - Dynamic docstring generation based on payload parameters
 - Seamless backend integration for response processing
+ ManagedResource: Specialized resource for CRUD operations with standardized methods
 - Declarative CRUD generation via __crud__ set (create, read, update, delete, list)
 - crud helper class with standard method configurations and custom parameter support
 - Auto-generates bound methods for declared operations with proper request/response handling
 - Explicit method definitions override auto-generation for customization
+ SearchResourceConfig: Configuration model for search-specific settings (method, searchmethod, oncall, payload)
+ Enhanced declarative attribute system: __declattrs__ and __declconfs__ extension for specialized resources
+ Comprehensive test coverage: 24 passing tests for both SearchResource and ManagedResource functionality
+ Foundation established for declarative API client development with specialized resource types

## [0.8.0] -- *2025-06-13*
* Complete concrete implementation suite with comprehensive test coverage
+ Concrete implementations: Client, Resource, Session, Backend, Persistence, Auth base classes
+ RequestsEngine implementation with requests.Session integration and config cascading
+ Full request/response pipeline with RequestModel/ResponseModel Pydantic validation
+ Resource method discovery and bound method creation with backend processing
+ Session lifecycle management with auth integration and state persistence
+ Backend error handling with configurable raiseonerror behavior
+ Persistence implementation with JSON file storage and directory creation
+ Enhanced config system: ClientConfig, ResourceConfig, SessionConfig, EngineConfig, etc.
+ Comprehensive unit test suite: 73 passing tests covering all concrete implementations
+ Dynamic resource discovery from nested classes with config support
+ Complete V3 architecture operational: Client → Engine → Session → [Auth, Persistence]
+ Ready for real-world API client development with declarative framework

## [0.7.9] -- *2025-06-11*
* Complete declarative property access system with component hierarchy traversal
+ Property access pattern: lowercase returns abstraction, UPPERCASE returns raw ._obj
+ Automatic parent reference injection via metaclass stack inspection - zero constructor changes needed
+ Component hierarchy traversal: client.auth finds auth anywhere in component tree (Client → Engine → Session → Auth)
+ Mixed declaration styles support: both __component__ = Class and nested class Component(BaseComponent) patterns work
+ __declaredas__ attribute on base classes for automatic nested component discovery
+ Comprehensive test coverage: property access, component resolution, declarative components, inheritance chain
+ End-to-end working example: client.auth, client.SESSION, client.engine._session._auth all functional
+ Robust error handling with descriptive messages for uninitialized/undeclared components
+ Foundation complete for real-world usage with concrete implementations

## [0.7.8] -- *2025-06-10*
* Complete declarative component discovery system
+ DeclarativeMeta metaclass with __declcomps__, __declattrs__, __declconfs__ discovery
+ Component resolution system with constructor override behavior
+ Fixed metaclass conflicts by removing Protocol inheritance (structural conformance maintained)
+ All Base* classes inherit from Declarative with proper __decl*__ sets defined
+ Component hierarchy system: Client → Engine → Session → Auth/Persistence
+ Lazy instantiation for class declarations vs direct instance usage
+ Comprehensive test suite: 18 passing tests covering discovery and resolution
+ Foundation for declarative syntax: __auth__ = MyAuth, timeout = 30, headers = {...}

## [0.7.7] -- *2025-06-09*
* Complete V3 architecture foundation established
+ BaseClient abstract class with resource discovery and component management
+ BaseResource abstract class with method/child registration and URL building
+ BaseEngine abstract class with session management and request lifecycle
+ BaseSession abstract class with auth/persistence integration and request preparation
+ BaseAuth abstract class with pluggable authentication strategies
+ BaseBackend abstract class with API-specific request formatting and response processing
+ BasePersistence abstract class with configurable state management
+ Complete protocol system for dependency injection (Auth, Backend, Persistence, RequestEngine, Session)
+ Enhanced config system with cascading: EngineConfig, SessionConfig, AuthConfig, BackendConfig, PersistenceConfig
+ RequestsEngine concrete implementation with requests.Session integration
+ RequestModel/ResponseModel with Pydantic validation and helper methods
+ Comprehensive unit test coverage for all base abstractions
+ Clean separation of concerns: Client → Engine → Session → [Auth, Persistence]
+ Backend architecture: Resource-level API formatting with client-level defaults
+ Session persistence with configurable filtering (cookies, headers, tokens)

## [0.7.6] -- *2025-06-08*
* Core abstractions and framework foundation complete
+ BaseClient abstract class with component management and resource discovery
+ BaseResource abstract class with method/child registration and URL building
+ BaseBackend abstract class with request formatting and response processing
+ BasePayload abstract class integrating with schematix for parameter handling
+ Param class extending schematix Field for clientfactory-specific parameter logic
+ Complete config system: EngineConfig, AuthConfig, BackendConfig, ToleranceType enum
+ All base abstractions ready for concrete implementations and declarative framework


## [0.7.5] -- *2025-06-06*
* Complete request pipeline implementation
+ BaseSession abstract class with request/response lifecycle
+ StandardSession concrete implementation with config-based defaults
+ BaseAuth abstract class with authentication protocol
+ EngineConfig for consistent engine configuration
+ Enhanced RequestModel with withcookies() and improved tokwargs()
+ AuthConfig for consistent authentication configuration
+ Full pipeline: Engine → Session → Auth → Request/Response flow

## [0.7.4] -- *2025-06-06*
* V3 refactor foundation complete
+ Core data models with Pydantic (RequestModel, ResponseModel, Config models)
+ Protocol definitions for dependency injection (Auth, Backend, Payload, RequestEngine, Session)
+ Base engine abstraction with RequestsEngine implementation
+ Type-safe configuration system with frozen models
+ Enhanced enum system (HTTPMethod, AuthType, BackendType, etc.)
+ Request/Response model integration with helper methods (tokwargs, FromRequests)


## [0.7.3] -- *2025-06-06*
* Restarted from scratch
+ partilly set up package directory structure
+ partially defined `RequestEngineProtocol`


## [0.7.2] -- *2025-06-05*
+ added `noexec` kwarg to requesting methods to halt request execution and instead return the prepared request object

## [0.7.1] -- *2025-04-22*
fucking pypi brah

## [0.6.9] -- *tbd*
+ jumped 3 versions bc 69
+ rebuilt from scratch with:
  - Comprehensive declarative framework
  - Extensive auth support (Basic, Token, API Key, OAuth, JWT, DPoP)
  - Protocol-specific backends:
    * GraphQL support with query validation
    * Algolia multi-index search
  - Parameter validation and transformation
  - Session state management
  - Enhanced payload system
  - Support for specialized resources (Search, Managed)

## [0.6.6] -- *2025-xx-xx*
- added `baseurl` attribute to `ResourceConfig` for client resources not attached to the parent `Client` baseurl e.g. media servers, etc.
- added abbreviation access to `RequestMethod` enum members in `utils/__init__.py`

## [0.6.5] -- *2024-12-29*
  ### Added
  - Enhanced Session Management
    - Header Management System
      * Static/Dynamic headers with generators
      * Header rotation strategies
      * Built-in UA generation
    - Cookie Management System
      * Cookie persistence (JSON/Pickle)
      * Dynamic cookie generation
      * State tracking
    - JWT Implementation
      * JWK key handling (RSA/EC)
      * DPoP token support
      * Dynamic token generation
    - State Management
      * Session state tracking
      * Persistent storage
      * Response tracking

  ### Enhanced
  - Response Handling
    * Path-based value extraction
    * Header/Cookie tracking
    * Enhanced error handling
    * State preservation
  - Authentication System
    * Added JWT auth support
    * DPoP implementation
    * Common auth patterns
  - Session Configuration
    * State management integration
    * Persistence support
    * Context managers

  ### Fixed
  - Header generation and rotation
  - Cookie persistence and state tracking
  - JWT/DPoP token generation
  - Session state management
  - Response extraction patterns

  ### Documentation
  - Header system usage
  - Cookie management patterns
  - JWT/DPoP implementation
  - Session enhancement examples

## [0.6.4] -- *2024-12-27*
  ### Added (Incomplete)
  - Managed Resources

## [0.6.3] -- *2024-12-17*
  ### Added
  - Parameter Processing and Mapping
    - Process callable for parameter transformation
    - Fuzzy value mapping with fuzzywuzzy
    - Configurable fuzzy matching methods
    - Match threshold control
    - Error handling with raisefor flags

  - Request Utilities
    - Iterator for dynamic parameter iteration
      - Multiple iteration strategies (product, zip, chain)
      - Context manager support
      - Operator syntax (@)
    - BatchProcessor for large parameter sets
      - Configurable batch size and delay
      - Failure collection and handling
    - RequestChain for dependent requests
      - Parameter transformation between requests
      - Response key extraction
      - Multiple syntax support (method chaining, @)

  ### Enhanced
  - Parameter value handling
    - Added fuzzy matching capabilities
    - Improved error control
    - Better type handling
    - Flexible value mapping

  ### Fixed
  - Parameter processing error handling
  - Request chain execution flow
  - Batch processing continuity
  - Iterator parameter handling

  ### Documentation
  - Parameter processing examples
  - Request utilities usage patterns
  - Integration examples
  - Best practices guide

## [0.6.2] -- *2024-12-17*
  ### Added
  - Enhanced GraphQL Support
    - Comprehensive GraphQL adapter implementation
    - Variable definition system with GQLVar
    - Path-based variable resolution
    - Variable processing pipeline
    - Structured variable formatting
    - Default value handling
    - Operation and query management
    - Fragment support

  ### Enhanced
  - GraphQL Protocol Implementation
    - Added proper GraphQL request formatting
    - Improved variable handling and structure
    - Better support for complex GraphQL queries
    - Standardized GraphQL POST request handling

  ### Fixed
  - GraphQL adapter abstract method implementation
  - GraphQL request formatting and execution
  - Variable structure preservation in requests
  - Proper GraphQL protocol handling in search base

  ### Documentation
  - GraphQL adapter usage examples
  - Variable definition patterns
  - GraphQL query structuring

## [0.6.1] -- *2024-12-16*
  ### Enhanced
  - Transform Pipeline Flow
    - Added transform awareness to parameter handling
    - Improved transform result preservation
    - Better support for nested payload structures
    - Smarter payload key targeting in transforms

  ### Fixed
  - Parameter double-mapping issue when using transforms
  - Transform result preservation in request construction
  - Proper nesting of transformed payloads
  - Payload structure maintenance through request pipeline
  - Transform chain integrity for complex payloads

  ### Documentation
  - Updated transform pipeline execution examples
  - Added nested payload construction patterns

## [0.6.0] -- *2024-12-15*
  ### Added
  - Transform System
    - Base Transform framework with composable transforms
    - TransformType enum for different transformation targets (URL, PAYLOAD, PARAMS, HEADERS, COOKIES)
    - TransformOperation enum for operation types (MERGE, MAP, FILTER, CHAIN, COMPOSE)
    - Support for transform pipelines with ordered execution
    - Built-in transform types:
      - PayloadTransform for merging and mapping payloads
      - URLTransform for URL construction
      - ProxyTransform for proxy-style API requests

  ### Enhanced
  - SearchResourceConfig with transform pipeline support
  - Resource-level transform integration
  - Transform execution order control
  - Parameter mapping with transform support
  - Flexible proxy parameter mapping
  - Transform pipeline composition
  - Resource decoration with transform handling

  ### Fixed
  - Proxy parameter handling in search requests
  - Transform pipeline execution order
  - Resource configuration inheritance with transforms
  - Parameter mapping with complex transformations
  - Parameter mapping with complex transformations
  - Dual-use parameter handling for proxy requests (params needed in both URL and request params)

  ### Documentation
  - Transform system usage examples
  - Pipeline composition patterns
  - Proxy transform configuration

## [0.5.9] -- *2024-12-15*
  ### Added
  - Complex payload support with nested parameters
  - Dot notation for deep parameter access
  - PayloadTemplate system for reusable configurations
  - Template inheritance and composition
  - Static configuration support in payloads

  ### Enhanced
  - Parameter mapping for nested structures
  - Parameter validation for complex types
  - Configuration merging strategies
  - Template-based resource configuration

  ### Fixed
  - Nested parameter flattening in mapped results

## [0.5.8] -- *2024-12-11*
  ### Fixed
  - more url path construction fixes for decorated search resources

## [0.5.7] -- *2024-12-11*
  ### Fixed
  - url path construction for search resources

## [0.5.6] -- *2024-12-11*
  ### Fixed
  - algolia parameter formation (url encoding params)

## [0.5.5] -- *2024-12-11*
  ### Fixed
  - actually fixed the config initialization issues this time

## [0.5.4] -- *2024-12-11*
  ### Fixed
  - adapter config initialization issues

## [0.5.3] -- *2024-12-10*
  ### Added
  - Search Client Base with standardized parameter handling
  - Query Adapter framework for multiple protocols
  - REST adapter with configurable formatting styles
  - Algolia adapter with index and sorting support
  - GraphQL adapter with variables handling
  - Improved resource decoration with `@searchresource`
  - Comprehensive test suite for adapters

  ### Enhanced
  - Parameter mapping and validation
  - Resource configuration handling
  - Request/Response flow
  - Logging throughout components

## [0.5.2] -- *2024-11-05*
  ### Fixed
  - specified full import paths everywhere

## [0.5.1] -- *2024-11-05*
  ### Fixed
  - specified full path imports on `__init__` files

## [0.5.0] -- *2024-11-05*
  **Initial Release**
