# Preemptive Module-Conflict Resolver (modguard)

[![PyPI version](https://img.shields.io/pypi/v/pmcr.svg)](https://pypi.org/project/pmcr/)
[![Python versions](https://img.shields.io/pypi/pyversions/pmcr.svg)](https://pypi.org/project/pmcr/)
[![License](https://img.shields.io/pypi/l/pmcr.svg)](https://github.com/yourusername/pmcr/blob/main/LICENSE)

A tool to detect and resolve Python module namespace collisions before they cause problems in your projects.

## Problem

Python's module namespace collisions occur when two or more PyPI packages define modules with identical names. This issue arises due to Python's flat `site-packages` directory structure, where one package can overwrite another during installation. Such conflicts lead to unpredictable behavior, including broken imports, runtime errors, and even potential security vulnerabilities.

## Solution

The **Preemptive Module-Conflict Resolver** (`modguard`) detects and resolves module namespace collisions in Python projects. It operates at multiple stages of the development lifecycle, from static analysis of dependencies to runtime import shimming.

## Features

- **Detect Namespace Collisions**: Identify all direct and transitive dependencies that define modules with identical names.
- **Resolve Conflicts**: Provide automated solutions to mitigate conflicts, such as renaming modules via import hooks or suggesting alternative version constraints.
- **Integrate into CI/CD Pipelines**: Enable pre-commit hooks and CI checks to catch conflicts early in the development process.

## Installation

```bash
pip install pmcr
```

## Quick Start

Scan a project for module conflicts:

```bash
modguard scan .
```

Scan and fix conflicts:

```bash
modguard scan . --fix
```

Preview fixes without applying them:

```bash
modguard scan . --dry-run
```

## GitHub Actions Integration

Add to your workflow:

```yaml
name: ModGuard Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run ModGuard
        run: pip install pmcr && modguard scan . --dry-run
```

## Documentation

For more detailed documentation, see:
- [Usage Guide](https://github.com/yourusername/pmcr/blob/main/docs/usage.md)
- [API Reference](https://github.com/yourusername/pmcr/blob/main/docs/api.md)
- [Contributing](https://github.com/yourusername/pmcr/blob/main/docs/contributing.md)

## License

MIT
