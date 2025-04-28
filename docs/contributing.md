# Contributing to Preemptive Module-Conflict Resolver

Thank you for your interest in contributing to the Preemptive Module-Conflict Resolver project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct, which promotes a respectful and inclusive environment for all contributors.

## Getting Started

### Setup Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/preemptive-module-conflict-resolver.git
   cd preemptive-module-conflict-resolver
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

### Development Workflow

1. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests to ensure everything works:
   ```bash
   pytest
   ```
4. Format your code using black:
   ```bash
   black src tests
   ```
5. Run static type checking:
   ```bash
   mypy src
   ```
6. Commit your changes:
   ```bash
   git commit -m "Add feature X"
   ```
7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
8. Submit a pull request

## Project Structure

- `src/modguard/` - Main package source code
  - `dependency/` - Dependency graph building and analysis
  - `extractor/` - Module extraction from packages
  - `detector/` - Collision detection logic
  - `fix/` - Fix generation and application
  - `models/` - Data models
  - `integrations/` - CI/CD and pre-commit integrations
- `tests/` - Test suite
- `examples/` - Example projects with conflicts
- `docs/` - Documentation

## Testing

We use pytest for testing. Run the test suite with:
```bash
pytest
```

To run tests with coverage:
```bash
pytest --cov=modguard
```

### Adding Tests

When adding new features, please include corresponding tests in the `tests/` directory. Tests should be named `test_*.py` and follow the existing patterns.

## Documentation

We use Markdown for documentation. When adding new features or modifying existing ones, please update the documentation accordingly.

## Pull Request Guidelines

1. Write clear, concise commit messages and PR descriptions
2. Include tests for new features or bug fixes
3. Update documentation as needed
4. Make sure all tests pass and code is formatted correctly
5. Keep PRs focused on a single change rather than multiple unrelated changes

## Code Style

We follow PEP 8 guidelines with some modifications:
- Line length: 100 characters
- Use type hints for function signatures
- Use docstrings for all public functions and classes

We use `black` for code formatting and `mypy` for type checking. Please run these tools before submitting a PR.

## Feature Requests and Bug Reports

Feature requests and bug reports should be submitted via GitHub issues. Please use the appropriate issue template and provide as much detail as possible.

## Release Process

The release process is handled by maintainers. If you would like to suggest a release, please create an issue with the tag `release`.

## Versioning

We follow Semantic Versioning (SemVer):
- MAJOR version for incompatible API changes
- MINOR version for new functionality in a backward-compatible manner
- PATCH version for backward-compatible bug fixes

## License

By contributing to this project, you agree that your contributions will be licensed under the project's license.

Thank you for contributing to make Preemptive Module-Conflict Resolver better!