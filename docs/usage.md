# Usage Guide

This guide covers the various ways to use the Preemptive Module-Conflict Resolver (modguard) tool in your Python projects.

## Command Line Interface

### Basic scanning

To scan your project for module conflicts:

```bash
modguard scan .
```

This will analyze your project's dependencies and report any namespace collisions.

### Apply fixes automatically

To automatically apply suggested fixes:

```bash
modguard scan . --fix
```

This will generate import hooks or suggest version constraints to resolve detected conflicts.

### Dry-run mode

To preview the conflicts and suggested fixes without making changes:

```bash
modguard scan . --dry-run
```

### Specify custom project path

```bash
modguard scan /path/to/project
```

### Exclude specific packages

```bash
modguard scan . --exclude package1,package2
```

### Whitelist known-safe conflicts

```bash
modguard scan . --whitelist utils.py:package1,package2
```

## Configuration File

You can create a `modguard.toml` file in your project root to configure the tool:

```toml
# modguard.toml

[scan]
# Packages to exclude from conflict detection
exclude = ["package1", "package2"]

# Whitelist specific modules as safe for conflict
whitelist = [
    "utils:package1,package2",
    "helpers:package3,package4"
]

[fix]
# Preferred fix strategy (rename_shim, version_constraint, isolation)
strategy = "rename_shim"

# Whether to apply fixes automatically
auto_apply = false
```

## Integration with CI/CD Pipelines

### GitHub Actions

Add a workflow file to your repository:

```yaml
# .github/workflows/modguard.yml
name: ModGuard Check
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install preemptive-module-conflict-resolver
      - name: Run ModGuard
        run: modguard scan . --dry-run
```

### Pre-commit Hook

Add modguard to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/yourgithub/preemptive-module-conflict-resolver
    rev: v1.0.0
    hooks:
      - id: modguard
```

## Using as a Library

You can also use modguard as a Python library in your own tools:

```python
from modguard import scan_project, suggest_fixes

# Scan project for conflicts
conflict_report = scan_project("path/to/project")

if conflict_report.has_conflicts():
    print(f"Found {conflict_report.get_conflict_count()} conflicts")
    
    # Generate fix plan
    fix_plan = suggest_fixes(conflict_report)
    print(fix_plan)
```

## Using Import Hooks

If you're using the rename shim strategy, modguard will create a `.modguard.py` file in your project. To activate the import hooks, add this to your project's entry point:

```python
# Import this at the beginning of your application
import modguard.hook
```

This will automatically reroute imports to avoid conflicts.

## Best Practices

1. **Run modguard early**: Integrate into your development workflow to catch conflicts early.
2. **Use with CI/CD**: Add modguard checks to your continuous integration pipeline.
3. **Review fix plans**: Always review suggested fixes before applying them.
4. **Whitelist thoughtfully**: Only whitelist conflicts you're certain are safe.
5. **Keep dependencies updated**: Regular updates can help avoid namespace conflicts.