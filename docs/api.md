# API Documentation

This document describes the Python API for the Preemptive Module-Conflict Resolver (modguard).

## Core Functions

### `scan_project`

```python
from modguard import scan_project

conflict_report = scan_project(path: str) -> ConflictReport
```

Analyzes a project's dependencies and returns a report of any namespace conflicts.

**Parameters:**
- `path`: Path to the project directory

**Returns:**
- `ConflictReport`: An object containing details about conflicting modules

**Example:**
```python
from modguard import scan_project

report = scan_project("./my_project")
if report.has_conflicts():
    print(f"Found {report.get_conflict_count()} conflicts")
    for module_name, modules in report.conflicts.items():
        if len(modules) > 1:
            print(f"Module '{module_name}' has conflicts")
```

### `suggest_fixes`

```python
from modguard import suggest_fixes

fix_plan = suggest_fixes(report: ConflictReport) -> FixPlan
```

Generates a plan to resolve conflicts detected in a `ConflictReport`.

**Parameters:**
- `report`: A `ConflictReport` object containing conflict information

**Returns:**
- `FixPlan`: An object detailing recommended actions to resolve conflicts

**Example:**
```python
from modguard import scan_project, suggest_fixes

report = scan_project("./my_project")
if report.has_conflicts():
    fix_plan = suggest_fixes(report)
    print(fix_plan)
```

### `apply_fixes`

```python
from modguard import apply_fixes

result = apply_fixes(plan: FixPlan) -> FixResult
```

Applies fixes as specified in a `FixPlan`.

**Parameters:**
- `plan`: A `FixPlan` object containing actions to resolve conflicts

**Returns:**
- `FixResult`: An object detailing which fixes were applied successfully

**Example:**
```python
from modguard import scan_project, suggest_fixes, apply_fixes

report = scan_project("./my_project")
if report.has_conflicts():
    fix_plan = suggest_fixes(report)
    result = apply_fixes(fix_plan)
    print(f"Applied {result.success_count()} fixes successfully")
```

## Core Classes

### `ConflictReport`

Contains information about module namespace conflicts.

**Key Attributes:**
- `conflicts`: Dictionary mapping module names to lists of `ModuleInfo` objects
- `has_conflicts()`: Returns `True` if conflicts were detected
- `get_conflict_count()`: Returns the number of conflicts detected

### `DetailedConflictReport`

Extended conflict report with severity and analysis.

**Key Attributes:**
- `severities`: Dictionary mapping module names to severity levels
- `import_paths`: Dictionary mapping module names to sets of import paths

### `FixPlan`

A plan to fix module conflicts.

**Key Attributes:**
- `conflict_report`: The `ConflictReport` this plan is based on
- `actions`: List of `FixAction` objects
- `has_actions()`: Returns `True` if there are fix actions in the plan

### `FixAction`

A specific action to fix a module conflict.

**Key Attributes:**
- `fix_type`: Type of fix (e.g., rename shim, version constraint)
- `module_name`: Name of the module to fix
- `package_name`: Name of the package containing the module
- `details`: Additional details about the fix

### `FixResult`

The result of applying a fix plan.

**Key Attributes:**
- `plan`: The `FixPlan` that was applied
- `applied_fixes`: List of `AppliedFix` objects
- `all_successful()`: Returns `True` if all fixes were applied successfully
- `success_count()`: Returns the number of successfully applied fixes

## Advanced Usage

### Custom Conflict Detection

```python
from modguard.dependency.graph import DependencyGraphBuilder
from modguard.extractor.module_extractor import ModuleExtractor
from modguard.detector.collision_detector import CollisionDetector

# Build dependency graph
graph = DependencyGraphBuilder.from_project("./my_project")

# Extract modules
modules_by_package = ModuleExtractor.extract_modules_from_dependency_graph(graph)

# Detect collisions
report = CollisionDetector.detect_collisions(modules_by_package)
```

### Custom Fix Engine

```python
from modguard.fix.engine import FixEngine
from modguard.models.fix_plan import FixType

# Create custom fix engine with specific strategy preference
engine = FixEngine(preferred_strategies=[FixType.RENAME_SHIM, FixType.VERSION_CONSTRAINT])

# Generate fix plan
fix_plan = engine.suggest_fixes(conflict_report)
```

### Import Hook Creation

```python
from modguard.fix.shim import ImportShimGenerator

# Generate import hook code
shim_code = ImportShimGenerator.generate_hook_code(fix_plan)

# Write to file
with open(".modguard.py", "w") as f:
    f.write(shim_code)
```