"""
Models for representing module conflicts in Python projects.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class PackageInfo:
    """Information about a Python package."""
    name: str
    version: str
    
    def __str__(self) -> str:
        return f"{self.name}=={self.version}"


@dataclass
class ModuleInfo:
    """Information about a Python module."""
    name: str
    path: str
    package: PackageInfo
    
    def __str__(self) -> str:
        return f"{self.name} (from {self.package})"


@dataclass
class ConflictReport:
    """Report of module namespace conflicts."""
    # Module name -> List of conflicting modules
    conflicts: Dict[str, List[ModuleInfo]] = field(default_factory=dict)
    
    def add_conflict(self, module_name: str, module_info: ModuleInfo) -> None:
        """Add a module to the conflict report."""
        if module_name not in self.conflicts:
            self.conflicts[module_name] = []
        self.conflicts[module_name].append(module_info)
    
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts."""
        return any(len(modules) > 1 for modules in self.conflicts.values())
    
    def get_conflict_count(self) -> int:
        """Get the number of conflicts."""
        return sum(1 for modules in self.conflicts.values() if len(modules) > 1)
    
    def __str__(self) -> str:
        if not self.has_conflicts():
            return "No module conflicts detected."
        
        result = f"Detected {self.get_conflict_count()} module conflicts:\n"
        for module_name, modules in self.conflicts.items():
            if len(modules) > 1:
                result += f"- Module '{module_name}' conflicts between packages: "
                result += ", ".join(f"'{m.package.name}'" for m in modules)
                result += "\n"
        return result


@dataclass
class ConflictSeverity:
    """Severity levels for conflicts."""
    CRITICAL = "CRITICAL"  # Will certainly cause errors
    HIGH = "HIGH"          # Likely to cause errors
    MEDIUM = "MEDIUM"      # May cause errors in some cases
    LOW = "LOW"            # Unlikely to cause errors
    INFO = "INFO"          # Just informational


@dataclass
class DetailedConflictReport(ConflictReport):
    """Extended conflict report with severity and analysis."""
    severities: Dict[str, str] = field(default_factory=dict)
    import_paths: Dict[str, Set[str]] = field(default_factory=dict)
    
    def set_severity(self, module_name: str, severity: str) -> None:
        """Set the severity level for a conflicting module."""
        self.severities[module_name] = severity
    
    def add_import_path(self, module_name: str, import_path: str) -> None:
        """Add an import path where the module is being used."""
        if module_name not in self.import_paths:
            self.import_paths[module_name] = set()
        self.import_paths[module_name].add(import_path)
    
    def __str__(self) -> str:
        if not self.has_conflicts():
            return "No module conflicts detected."
        
        result = f"Detected {self.get_conflict_count()} module conflicts:\n"
        for module_name, modules in self.conflicts.items():
            if len(modules) > 1:
                severity = self.severities.get(module_name, ConflictSeverity.MEDIUM)
                result += f"- [{severity}] Module '{module_name}' conflicts between packages: "
                result += ", ".join(f"'{m.package.name}'" for m in modules)
                
                if module_name in self.import_paths:
                    result += "\n  Used in:"
                    for path in self.import_paths[module_name]:
                        result += f"\n  - {path}"
                result += "\n"
        return result