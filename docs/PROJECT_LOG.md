# Project Log

## 2026-07-27

### Decision
Use WSL as the primary development environment.

### Reason
- Matches production Linux environments.
- Better compatibility with Docker and DevOps tools.
- Aligns with internship tooling (Linux, Ansible, Terraform, Jenkins).

### Outcome
All development commands will be executed from the WSL terminal.

## ADR-002: Externalize Configuration

### Decision
Application configuration will not be hardcoded.

### Reason
Code should remain the same across development, testing, and production environments. Only configuration should change.

### Examples
- Database URL
- Secret Key
- Debug Mode
- Application Version

### Implementation
Configuration will be loaded from environment variables using `python-dotenv`.
