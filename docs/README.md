# ClientFactory

[![PyPI version](https://badge.fury.io/py/clientfactory.svg)](https://badge.fury.io/py/clientfactory)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-608%20passed-green.svg)](https://github.com/schizoprada/clientfactory)

A declarative framework for building comprehensive API clients with minimal boilerplate.


## Quick Start
```py
from clientfactory import (
    Client, resource, headers, session,
    param, payload, get, post
)

@headers
class ExampleHeaders:
    accept = "application/json" # header key derived from attribute name
    useragent = ("User-Agent", "Mozilla Firefox 5.0")  # explicit header key

@session
class ExampleSession:
    headers = ExampleHeaders

@param
class Username:
    type = str # automatic type conversion & enforcement
    required = True # enforce usage
    transform = lambda value: value.lower() # custom value transformation

def emailvalidator(email: str, extant: list) -> None:
    if email in extant:
        raise ValueError(f"An account with email: {email} is already registered")

@param
class Email:
    type = str
    required = True
    validator = emailvalidator # custom data validation

@param
class Country:
    target = "country_name" # request body key to assign value to
    choices = [...] # explicit choices
    default = "USA"

@payload
class UserRegistrationPayload:
    username = Username
    email = Email
    country = Country


class Example(Client):
    __session__ = ExampleSession
    baseurl = "https://www.example.com"

    @resource
    class Users:

        @get("{id}") # url path parameter formation
        def read(self, id, *args, **kwargs): pass

        @post(payload=UserRegistrationPayload)
        def create(self, *args, **kwargs): pass

        # nested resources automatically extend the baseurl path with the class name
        # all methods in this endpoint will request (and optionally extend) the resource baseurl
        # which would be "https://www.example.com/users"
        # to override, use 'path' attribute e.g.
        # path = "" // dont use resource name in url path

if __name__ == "__main__":
    client = Example()
    client.users.read(1) # GET request to https://www.example.com/users/1
    client.users.create(username="TESTUSER", email="test@user.com", country="USA") # POST request to https://www.example.com/users
    # with json body = {'username': 'testuser', 'email': 'test@user.com', 'country_name': 'USA'}

    # on client instantiation, resource classes are instantiated and attributed with lowercase
    # client.users = instance of Users
    # client.Users = Users class
```

## Key Features
`ClientFactory` provides a comprehensive library for rapidly building production-ready API clients.

### Declarative Component Definitions
Define API components through simple class attributes, rather than complex configuration objects. Transform any class/method into a functional component with minimal code.
```py
from clientfactory import Headers

# while this is valid, and works:
session_headers = Headers(
    some_header = "some_value",
    ...
)

# the preferred approach would be:
class Session_Headers(Headers):
    some_header = "some_value" # automatically resolves to (Some-Header) in final request headers

# or better yet, using decorators (more on those below)
from clientfactory import headers

@headers
class Session_Headers:
    some_header = "some_value"
```

### Intuitive Decorators System
Every `ClientFactory` component  has a decorator to match. Transform classes and methods into API client components with zero boilerplate, inheritance chains, or complex setup.
```py
from clientfactory import Client, searchable

class Marketplace(Client):
    baseurl = "https://www.marketplace.com"

    @searchable # automatically builds a searchable endpoint, with sensible defaults (can be overrided)
    class Listings:
        pass

if __name__ == "__main__":
  market = Marketplace()
  market.listings.search(keyword="example")
```

### Built-in Authentication
`JWT`, `DPoP`, and custom authentication with automatic header management. Additional authentication mechanism(s) support e.g. `OAuth` in development.
```py
from clientfactory import dpop, session

@dpop
class MyAuth:
    algorithm = "ES256"
    headerkey = "DPoP" # where to add authentication value(s) in the headers during request construction pipeline
    jwk = {...} # public/private keys etc.

@session
class MySession:
  __auth__ = MyAuth # thats all you need !
```

### Backend Adapters
Native support for specialized API protocols, including Algolia & GraphQL, with more in development. Incorporates automatic request/response transformation and protocol-specific optimizations.
```py
from clientfactory import algolia

@algolia
class Adapter:
    # some fields are used for request context
    appid = "..."
    apikey = "..."
    # some for direct manipulation of body
    facetsmap = {
        "brand": "brand.name"
    } # will be used to construct the algolia request query string
```

### Robust Parameter/Payload System
Built on [`schematix`](https://github.com/schizoprada/schematix) for powerful data validation, type safety, transformation, conditional logic, and complex compositions of the aforementioned.
```py
from clientfactory import param, payload
from rapidfuzz import process

BrandIDMap: dict[str, int] = {...}

@param
class Brand:
    target = "brand_id" # what key the value should be assigned to in request body
    required = True
    mapping = BrandIDMap
    mapper = process.extractOne # custom mapping lookup logic
```

### Advanced Operational Abilities
Components in this are defined in a manner that allows them to stand and function alone, but also complement and interface with eachother seamlessly to allow for constructing complex operational processes to meet objective needs out the box.
```py
from clientfactory import Client, resource, get

class Marketplace(Client):
    baseurl = "https://www.marketplace.com"

    @resource
    class Listings:
        @get("{id}")
        def view(self, id, *args, **kwargs):
            """view individual listings"""
            pass

market = Marketplace()

preparedexecutable = market.listings.view.prepare(1) # returns ExecutableRequest object prepared to call

for response in market.listings.view.iterate(range(1, 100)):
    ... # automatic request iteration with dynamic params/body
```

### Extensible
Extending and customizing library components without modifying core framework. Simple and intuitive abstract method implementations allow for minimal implementations to achieve desired functionality.
```py
from clientfactory import BaseAuth, RequestModel

class MyAuth(BaseAuth):
    def __init__(
        self,
        token: str,
        *args,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self._token = token

    # implement concrete counterparts to the abstract methods
    def _applyauth(self, request: RequestModel) -> Requestmodel:
        headers = {'token-key': self._token}
        return request.withheaders(headers)
```

### Type Safety
Full type hinting and IDE support provided throughout the library.


## Installation
To install `ClientFactory`, simply run:
```bash
pip install clientfactory
```

## Additional Documentation
- [Architecture](ARCHITECTURE.md)
- [API Reference](API.md)
- [Examples](EXAMPLES.md)
