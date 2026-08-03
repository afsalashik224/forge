# Engineering Card 004

# Title

Dependency Injection (DI)

---

## Definition

Dependency Injection is a software design principle where an object receives its required dependencies from another component instead of creating them itself.

The object focuses on using its dependencies rather than constructing them.

Dependency Injection is built on top of Composition.

---

## Why does it exist?

When a class creates its own dependencies, it becomes tightly coupled to specific implementations.

This makes the class:

- Harder to test.
- Harder to replace components.
- Harder to extend.

Dependency Injection separates object creation from object usage.

---

## What problem does it solve?

Dependency Injection solves several engineering problems:

- Reduces coupling between components.
- Makes unit testing easier.
- Allows implementations to be replaced without modifying business logic.
- Separates object construction from object behavior.
- Improves maintainability and scalability.

---

## Forge Example

Current implementation:

```python
class ConceptService:

    def __init__(self):
        self.repository = ConceptRepository()
```

The Service creates its own Repository.

This is acceptable for the current stage of Forge because there is only one repository implementation.

As Forge grows, we plan to evolve to:

```python
class ConceptService:

    def __init__(self, repository):
        self.repository = repository
```

Now the Repository is provided from outside.

The Service no longer knows:

- how the Repository is created,
- which implementation it receives,
- whether it is a real repository or a mock.

Its only responsibility is using the Repository.

---

## Alternatives

### Direct Instantiation

```python
class ConceptService:

    def __init__(self):
        self.repository = ConceptRepository()
```

Simple and suitable for small applications.

---

### Dependency Injection

```python
class ConceptService:

    def __init__(self, repository):
        self.repository = repository
```

More flexible and scalable for larger applications.

---

### Dependency Injection Container

Large frameworks often use IoC (Inversion of Control) containers to automatically provide dependencies.

Examples include:

- Spring Boot
- ASP.NET Core
- NestJS

Flask generally performs Dependency Injection manually.

---

## Trade-offs

### Advantages

- Loose coupling
- Easier testing
- Easier replacement of implementations
- Better scalability
- Improved maintainability
- Better adherence to Single Responsibility Principle

### Disadvantages

- Slightly more complex architecture
- More objects need to be managed
- Can be unnecessary in very small projects

---

## Industry Usage

Dependency Injection is widely used in enterprise software.

Common examples include:

- Spring Boot
- ASP.NET Core
- NestJS
- Angular
- Laravel Service Container

Flask applications typically implement Dependency Injection manually or through extensions.

---

## Key Takeaways

- Objects should focus on using dependencies rather than creating them.
- Dependency Injection builds on Composition.
- It reduces coupling between application layers.
- It makes testing and future changes much easier.
- Introduce Dependency Injection when the project complexity justifies it, not before.
