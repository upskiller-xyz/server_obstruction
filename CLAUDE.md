# Development Instructions Log

## Core Principles

### 1. Object-Oriented Programming (OOP) - ALWAYS
- Use classes for all major functionality
- Encapsulate related data and methods together
- Avoid procedural programming patterns

### 2. Software Design Patterns - MANDATORY
- **Adapter Pattern**: Use when integrating different interfaces
- **Enumerator Pattern**: Use enums/constants instead of magic strings
- **Strategy Pattern**: Use maps/dictionaries instead of if-else chains
- **Factory Pattern**: For object creation
- **Singleton Pattern**: For shared resources (models, configurations)
- **Observer Pattern**: For event handling
- **Builder Pattern**: For complex object construction

### 3. Single Responsibility Principle (SRP) - STRICT
- Each class should have one reason to change
- Each method should do one thing well
- Split complex functionality into smaller, focused classes

### 4. Inheritance - ALWAYS USE
- Create base classes for common functionality
- Use abstract base classes (ABC) for interfaces
- Implement proper inheritance hierarchies
- Favor composition when inheritance doesn't make sense

### 5. Method Organization
- Use classmethods for functionality that operates on the class
- Group related functions under single instances/classes
- Maintain similar scope within class boundaries

### 6. No Redundant Printing
- Implement proper logging instead of print statements
- Use structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- Avoid duplicate log messages
- Log only meaningful events

## Code Quality Standards

### Class Design
```python
# Good Example
class ModelLoader(ABC):
    @abstractmethod
    def load(self) -> Model:
        pass

class CheckpointModelLoader(ModelLoader):
    def __init__(self, checkpoint_url: str):
        self.checkpoint_url = checkpoint_url

    def load(self) -> Model:
        # Implementation
        pass
```

### Enum Usage
```python
# Good Example - Define enums for all string constants
from enum import Enum

class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"

class EndpointPath(Enum):
    ROOT = "/"
    USERS = "/users"
    LOGIN = "/login"

class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"

# Use enum values instead of strings
method = HTTPMethod.POST.value
status = ResponseStatus.SUCCESS.value

# Bad Example - Magic strings
method = "POST"  # Don't do this!
status = "success"  # Don't do this!
```

### Strategy Pattern with Enums
```python
# Good Example - Route configuration using Strategy Pattern
route_config = [
    (EndpointPath.ROOT.value, EndpointName.STATUS.value, self._get_status, [HTTPMethod.GET.value]),
    (EndpointPath.USERS.value, EndpointName.USERS.value, self._get_users, [HTTPMethod.GET.value]),
]

for path, name, handler, methods in route_config:
    self._app.add_url_rule(path, name, handler, methods=methods)

# Good Example - Response handlers using Strategy Pattern
response_handlers = {
    ModelStatus.LOADING: self._handle_loading,
    ModelStatus.READY: self._handle_ready,
    ModelStatus.ERROR: self._handle_error
}
handler = response_handlers.get(status)

# Bad Example - if-else chains
if status == "loading":
    # handle loading
elif status == "ready":
    # handle ready
```

### Available Enumerators in constants.py
```python
from src.components.constants import (
    HTTPMethod,      # GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD
    HTTPStatus,      # OK=200, BAD_REQUEST=400, INTERNAL_SERVER_ERROR=500, etc.
    ContentType,     # JSON, TEXT, HTML, XML
    EndpointName,    # Endpoint function names (get_status, horizon_angle, etc.)
    EndpointPath,    # Endpoint URL paths ("/", "/horizon_angle", etc.)
    ResponseStatus,  # SUCCESS, ERROR
    ResponseField,   # STATUS, DATA, ERROR, etc.
    RequestField     # X, Y, Z, MESH, DIRECTION_ANGLE
)
```

## Implementation Guidelines

1. **Always start with interface design** - Define abstract base classes first
2. **Use dependency injection** - Pass dependencies through constructors
3. **Implement proper error handling** - Custom exception classes
4. **Follow naming conventions** - Clear, descriptive names
5. **Write self-documenting code** - Code should explain itself
6. **Use type hints** - Always specify parameter and return types
7. **ALL IMPORTS ON TOP** - Never import inside functions or methods, all imports must be at the top of the file

## Refactoring Notes

- Current main.py violates OOP principles - needs complete refactor
- Global variables should be encapsulated in classes
- Functions should be methods of appropriate classes
- Need proper separation of concerns

## Next Steps

1. Refactor main.py to follow these principles
2. Create proper class hierarchy for server components
3. Implement design patterns throughout codebase
4. Replace all print statements with structured logging