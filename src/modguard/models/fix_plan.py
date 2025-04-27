"""
Models for representing fix plans for module conflicts.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

from modguard.models.conflict import ConflictReport, ModuleInfo, PackageInfo


class FixType(Enum):
    """Types of fixes for module conflicts."""
    RENAME_SHIM = "rename_shim"  # Use import hooks to rename modules
    VERSION_CONSTRAINT = "version_constraint"  # Suggest alternative version constraints
    ISOLATION = "isolation"  # Isolate packages using virtual environments
    MANUAL = "manual"  # Requires manual intervention


@dataclass
class FixAction:
    """A specific action to fix a module conflict."""
    fix_type: FixType
    module_name: str
    package_name: str
    details: Dict[str, str] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.fix_type == FixType.RENAME_SHIM:
            renamed_to = self.details.get("renamed_to", f"{self.package_name}.{self.module_name}")
            return f"Rename '{self.module_name}' in '{self.package_name}' to '{renamed_to}'"
        elif self.fix_type == FixType.VERSION_CONSTRAINT:
            new_version = self.details.get("new_version", "")
            return f"Update '{self.package_name}' to version {new_version}"
        elif self.fix_type == FixType.ISOLATION:
            return f"Isolate '{self.package_name}' in a separate environment"
        elif self.fix_type == FixType.MANUAL:
            return f"Manual intervention required for '{self.module_name}' in '{self.package_name}'"
        return "Unknown fix action"


@dataclass
class FixPlan:
    """A plan to fix module conflicts."""
    conflict_report: ConflictReport
    actions: List[FixAction] = field(default_factory=list)
    
    def add_action(self, action: FixAction) -> None:
        """Add a fix action to the plan."""
        self.actions.append(action)
    
    def get_actions_for_module(self, module_name: str) -> List[FixAction]:
        """Get all fix actions for a specific module."""
        return [action for action in self.actions if action.module_name == module_name]
    
    def get_actions_for_package(self, package_name: str) -> List[FixAction]:
        """Get all fix actions for a specific package."""
        return [action for action in self.actions if action.package_name == package_name]
    
    def has_actions(self) -> bool:
        """Check if there are any fix actions in the plan."""
        return len(self.actions) > 0
    
    def __str__(self) -> str:
        if not self.has_actions():
            return "No fixes required."
        
        result = f"Fix plan for {self.conflict_report.get_conflict_count()} conflicts:\n"
        for action in self.actions:
            result += f"- {action}\n"
        return result


@dataclass
class AppliedFix:
    """A record of a fix that has been applied."""
    action: FixAction
    success: bool
    details: str = ""
    
    def __str__(self) -> str:
        status = "Successfully applied" if self.success else "Failed to apply"
        return f"{status}: {self.action}" + (f"\n  {self.details}" if self.details else "")


@dataclass
class FixResult:
    """The result of applying a fix plan."""
    plan: FixPlan
    applied_fixes: List[AppliedFix] = field(default_factory=list)
    
    def add_result(self, fix: AppliedFix) -> None:
        """Add a fix result."""
        self.applied_fixes.append(fix)
    
    def all_successful(self) -> bool:
        """Check if all fixes were applied successfully."""
        return all(fix.success for fix in self.applied_fixes)
    
    def success_count(self) -> int:
        """Get the number of successfully applied fixes."""
        return sum(1 for fix in self.applied_fixes if fix.success)
    
    def failure_count(self) -> int:
        """Get the number of failed fixes."""
        return sum(1 for fix in self.applied_fixes if not fix.success)
    
    def __str__(self) -> str:
        if not self.applied_fixes:
            return "No fixes were applied."
        
        result = f"Applied {self.success_count()}/{len(self.applied_fixes)} fixes:\n"
        for fix in self.applied_fixes:
            result += f"- {fix}\n"
        return result