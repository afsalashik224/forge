# Engineering Card 002

# Title

Configuration Management

---

## Definition

Configuration Management is the practice of storing application settings in a centralized location instead of hardcoding them throughout the codebase.

Configuration includes values that may change depending on the environment, such as development, testing, or production.

Examples include:

- Database URL
- Secret Keys
- Application Name
- Host and Port
- Debug Mode
- API Keys

---

## Why does it exist?

Without Configuration Management:

- Configuration values become duplicated.
- Updating a single value requires changing multiple files.
- Sensitive information may be exposed in source code.
- Switching between environments becomes difficult.

By centralizing configuration, the application becomes easier to maintain, secure, and deploy.

---

## What problem does it solve?

Configuration Management solves several software engineering problems:

- Eliminates hardcoded configuration values.
- Provides a single source of truth.
- Separates application logic from environment-specific settings.
- Makes configuration changes without modifying business code.
- Reduces maintenance effort and human error.

---

## Forge Example

Forge stores runtime configuration using:

```
.env
```

The `.env` file contains environment-specific values such as:

```env
APP_NAME=Forge
APP_VERSION=0.1.0
ENVIRONMENT=development

HOST=127.0.0.1
PORT=5000

SECRET_KEY=forge-secret-key

DATABASE_URL=sqlite:///instance/forge.db

DEBUG=True
```

The application never accesses the `.env` file directly.

Instead, all configuration is loaded through:

```
app/config/settings.py
```

The `Settings` class becomes the single source of truth.

Example:

```python
Settings.APP_NAME
Settings.DATABASE_URL
Settings.SECRET_KEY
```

This keeps the rest of the application independent from where the configuration is stored.

---

## Alternatives

Other approaches include:

### Hardcoded Configuration

```python
DATABASE_URL = "sqlite:///forge.db"
```

Simple for very small projects but difficult to maintain.

---

### Configuration File

Examples:

- JSON
- YAML
- TOML
- INI

Useful when environment variables are not suitable.

---

### Cloud Secret Managers

Production applications commonly use services such as:

- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

These provide secure storage for sensitive configuration.

---

## Trade-offs

### Advantages

- Single source of truth
- Easier maintenance
- Better security
- Environment independent
- Reduces duplication
- Easier deployment

### Disadvantages

- Slightly more initial setup
- Additional configuration files to maintain
- Missing environment variables can cause startup failures if not validated

---

## Industry Usage

Configuration Management is used in nearly every production application.

Common examples include:

- Flask
- Django
- FastAPI
- Spring Boot
- ASP.NET Core
- Node.js (dotenv)

Modern applications rarely hardcode environment-specific values.

---

## Key Takeaways

- Never hardcode environment-specific configuration.
- Store configuration separately from application logic.
- Access configuration through a centralized Settings object.
- Keep sensitive information outside the source code.
- Configuration should be easy to change without modifying business logic.
