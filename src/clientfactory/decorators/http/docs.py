# ~/clientfactory/src/clientfactory/decorators/http/docs.py
class DOCS:
   GET: str = """
GET request decorator.

Args:
   path: Endpoint path (can include parameters like {id})
   config: Pre-configured MethodConfig object
   preprocess: Function to transform request data (typically for query params)
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Note: GET requests cannot have payloads. Use preprocess to handle query parameters.

Example:
   @get("{id}")
   def get_user(self, id): pass

   @get("search", preprocess=lambda data: {"params": data})
   def search_users(self, query): pass
"""

   POST: str = """
POST request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   payload: Payload class for request validation
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @post("users", payload=UserPayload)
   def create_user(self, **data): pass

   @post("bulk", config=BulkCreateConfig)
   def bulk_create(self, **data): pass
"""

   PUT: str = """
PUT request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   payload: Payload class for request validation
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @put("{id}", payload=UserPayload)
   def update_user(self, id, **data): pass
"""

   PATCH: str = """
PATCH request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   payload: Payload class for request validation
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @patch("{id}", payload=UserUpdatePayload)
   def partial_update_user(self, id, **data): pass
"""

   DELETE: str = """
DELETE request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @delete("{id}")
   def delete_user(self, id): pass

   @delete("batch", preprocess=lambda data: {"json": {"ids": data["ids"]}})
   def batch_delete(self, ids): pass
"""

   HEAD: str = """
HEAD request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Note: HEAD requests cannot have payloads.

Example:
   @head("{id}")
   def check_user_exists(self, id): pass
"""

   OPTIONS: str = """
OPTIONS request decorator.

Args:
   path: Endpoint path
   config: Pre-configured MethodConfig object
   preprocess: Function to transform request data
   postprocess: Function to transform response data
   description: Method description (overrides docstring)

Example:
   @options("users")
   def get_user_options(self): pass
"""
