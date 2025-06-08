# CLIENTFACTORY - CHANGELOG

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
