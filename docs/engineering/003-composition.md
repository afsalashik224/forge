# Engineering Card 003

# Title

Composition

---

## Definition

Composition is a software design principle where one class builds functionality by using other classes instead of inheriting from them.

Rather than becoming another object through inheritance, a class owns or collaborates with other objects to accomplish its responsibilities.

Composition promotes modularity, loose coupling, and better separation of responsibilities.

---

## Why does it exist?

Inheritance creates a strong relationship between classes.

If the parent class changes, every child class may also be affected.

Composition reduces this dependency by allowing classes to work together while remaining independent.

This makes software easier to extend, test, and maintain.

---

## What problem does it solve?

Composition solves several engineering problems:

- Reduces tight coupling between classes.
- Encourages single responsibility.
- Makes replacing implementations easier.
- Improves maintainability.
- Promotes reusable components.
- Avoids unnecessary inheritance hierarchies.

---

## Forge Example

Instead of making the Service inherit from the Repository:

```python
class ConceptService(ConceptRepository):
    ...
```

Forge uses composition.

```python
class ConceptService:

    def __init__(self):
        self.repository = ConceptRepository()
```

The Service **has a Repository** instead of **being a Repository**.

Responsibilities remain separate.

The Service performs business logic.

The Repository performs persistence.

Each layer focuses only on its own responsibility.

---

## Alternatives

### Inheritance

```python
class ConceptService(ConceptRepository):
    ...
```

Simple for small examples but tightly couples both classes.

---

### Composition

```python
class ConceptService:

    def __init__(self):
        self.repository = ConceptRepository()
```

Promotes modularity and better separation of concerns.

---

### Dependency Injection

Instead of creating the dependency internally, another component provides it.

```python
class ConceptService:

    def __init__(self, repository):
        self.repository = repository
```

This builds on composition and further reduces coupling.

---

## Trade-offs

### Advantages

- Loose coupling
- Better modularity
- Easier testing
- Easier maintenance
- Easier replacement of implementations
- Follows Single Responsibility Principle

### Disadvantages

- Slightly more code
- Requires designing object relationships
- Can introduce additional abstraction if overused

---

## Industry Usage

Composition is preferred over inheritance in most modern software architectures.

It is widely used in:

- Flask applications
- Django applications
- FastAPI
- Spring Boot
- ASP.NET Core
- Clean Architecture
- Domain Driven Design (DDD)

Many modern frameworks recommend:

> "Favor Composition over Inheritance."

---

## Key Takeaways

- Composition means an object uses another object to perform work.
- The Service has a Repository instead of becoming a Repository.
- Composition reduces coupling between components.
- It improves modularity and maintainability.
- It is generally preferred over inheritance unless an "is-a" relationship truly exists.
