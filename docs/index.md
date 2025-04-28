# Preemptive Module-Conflict Resolver

Welcome to the documentation for the **Preemptive Module-Conflict Resolver** (modguard), a tool designed to detect and resolve Python module namespace collisions before they cause problems in your projects.

## What is Module-Conflict Resolver?

Python's module namespace can sometimes lead to collisions when two or more PyPI packages define modules with identical names. These conflicts occur due to Python's flat `site-packages` directory structure, where one package can overwrite another during installation.

The Preemptive Module-Conflict Resolver helps you:

- **Detect** potential namespace collisions in your dependencies
- **Analyze** the severity and impact of these collisions
- **Resolve** conflicts automatically when possible
- **Integrate** with your CI/CD pipeline to catch conflicts early

## Key Features

- 🔍 **Deep Dependency Analysis**: Scans direct and transitive dependencies for potential conflicts
- 🛠️ **Automatic Conflict Resolution**: Generates import hooks to resolve conflicts at runtime
- 📊 **Detailed Reporting**: Provides comprehensive reports on detected conflicts and their severity
- 🔄 **CI/CD Integration**: Works seamlessly with GitHub Actions and pre-commit hooks
- ⚙️ **Flexible Configuration**: Customize conflict detection and resolution rules

## Quick Start

Install the package:

```bash
pip install preemptive-module-conflict-resolver
```

Scan your project for conflicts:

```bash
modguard scan .
```

Apply suggested fixes:

```bash
modguard scan . --fix
```

## Navigation

- [Usage Guide](usage.md): Learn how to use the tool effectively
- [API Documentation](api.md): Detailed information about the Python API
- [Contributing](contributing.md): Guidelines for contributing to the project

## Why Use Module-Conflict Resolver?

Module namespace collisions often lead to unpredictable behavior, including:

- Broken imports
- Runtime errors
- Hard-to-debug issues
- Potential security vulnerabilities

By detecting and resolving these conflicts early in the development process, you can save valuable time debugging and ensure more reliable software.