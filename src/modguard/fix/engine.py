"""
Engine for generating and applying fixes for module namespace collisions.
"""
import os
import re
from typing import Dict, List, Optional, Set, Tuple

from modguard.models.conflict import ConflictReport, DetailedConflictReport
from modguard.models.fix_plan import FixAction, FixPlan, FixResult, FixType, AppliedFix


class FixEngine:
    """Engine for generating and applying fixes for module namespace collisions."""
    
    @staticmethod
    def _should_use_shim(module_name: str, report: DetailedConflictReport) -> bool:
        """
        Determine if a module conflict should be fixed using import shims.
        
        This is a simple heuristic. In a real implementation, we'd use more sophisticated
        analysis based on the project structure, import patterns, etc.
        """
        # For now, prefer shims for medium/low severity conflicts
        severity = report.severities.get(module_name, "MEDIUM")
        return severity in ["MEDIUM", "LOW"]
    
    @staticmethod
    def _should_use_version_constraint(module_name: str, report: DetailedConflictReport) -> bool:
        """
        Determine if a module conflict should be fixed using version constraints.
        
        This is a simple heuristic. In a real implementation, we'd analyze version
        compatibility, transitive dependencies, etc.
        """
        # For simplicity, suggest version constraints for high/critical severity conflicts
        severity = report.severities.get(module_name, "MEDIUM")
        return severity in ["CRITICAL", "HIGH"]
    
    @staticmethod
    def _get_preferred_packages(module_name: str, report: DetailedConflictReport) -> List[str]:
        """
        Determine which packages should be preferred for a given module.
        
        In a real implementation, we'd use package popularity, stability,
        maintenance status, etc.
        """
        # For now, a simple heuristic based on import frequency
        package_counts = {}
        
        if module_name in report.import_paths:
            for import_path in report.import_paths[module_name]:
                for module_info in report.conflicts[module_name]:
                    # Check if the package name appears in import statements
                    # (Very simplistic, would need more sophisticated analysis in reality)
                    if module_info.package.name in import_path:
                        package_counts[module_info.package.name] = \
                            package_counts.get(module_info.package.name, 0) + 1
        
        # Sort packages by frequency (most frequent first)
        return sorted(package_counts.keys(), key=lambda pkg: package_counts.get(pkg, 0), reverse=True)
    
    @classmethod
    def suggest_fixes(cls, report: DetailedConflictReport) -> FixPlan:
        """
        Generate a plan to fix module namespace collisions.
        
        Args:
            report: A DetailedConflictReport containing conflicts to fix
            
        Returns:
            A FixPlan with suggested fixes
        """
        plan = FixPlan(conflict_report=report)
        
        for module_name, modules in report.conflicts.items():
            if len(modules) <= 1:
                continue  # No conflict
                
            if cls._should_use_shim(module_name, report):
                # For each conflicting module except the preferred one, suggest a rename shim
                preferred_packages = cls._get_preferred_packages(module_name, report)
                
                # If no preference, use a default order
                if not preferred_packages:
                    package_names = [m.package.name for m in modules]
                    preferred_packages = sorted(package_names)
                
                # Keep the preferred package as is, suggest shims for others
                for module in modules:
                    if module.package.name != preferred_packages[0]:
                        action = FixAction(
                            fix_type=FixType.RENAME_SHIM,
                            module_name=module_name,
                            package_name=module.package.name,
                            details={
                                "renamed_to": f"{module.package.name}.{module_name}",
                                "original_name": module_name
                            }
                        )
                        plan.add_action(action)
                        
            elif cls._should_use_version_constraint(module_name, report):
                # For simplicity, suggest updating to latest version
                # In a real implementation, we'd analyze version compatibility
                for module in modules:
                    action = FixAction(
                        fix_type=FixType.VERSION_CONSTRAINT,
                        module_name=module_name,
                        package_name=module.package.name,
                        details={
                            "new_version": "latest",
                            "current_version": module.package.version
                        }
                    )
                    plan.add_action(action)
                    
            else:
                # For other cases, suggest manual intervention
                for module in modules:
                    action = FixAction(
                        fix_type=FixType.MANUAL,
                        module_name=module_name,
                        package_name=module.package.name,
                        details={
                            "reason": "Complex conflict requires manual intervention"
                        }
                    )
                    plan.add_action(action)
        
        return plan
    
    @staticmethod
    def _apply_shim_fix(action: FixAction, project_path: str) -> AppliedFix:
        """
        Apply a rename shim fix by adding an import hook.
        
        In a real implementation, we'd generate proper import hook code
        and modify project files to include it.
        """
        # Create a Python file for the import hook
        shim_dir = os.path.join(project_path, '.modguard', 'shims')
        os.makedirs(shim_dir, exist_ok=True)
        
        shim_file = os.path.join(shim_dir, f"shim_{action.package_name}_{action.module_name}.py")
        
        content = f"""
# Generated by ModGuard - DO NOT EDIT
# This file implements an import hook to resolve namespace conflicts

import sys
from importlib.abc import MetaPathFinder, Loader
from importlib.util import spec_from_loader, module_from_spec
import importlib.machinery

class {action.package_name.capitalize()}{action.module_name.capitalize()}ShimFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        # Only handle direct imports of the conflicting module
        if fullname == "{action.module_name}":
            # Redirect to the renamed module
            return self._create_spec("{action.details['renamed_to']}")
        return None
        
    def _create_spec(self, redirect_name):
        # Load the actual module
        actual_module = importlib.import_module(redirect_name)
        
        # Create a loader that returns the actual module
        class ShimLoader(Loader):
            def create_module(self, spec):
                return actual_module
                
            def exec_module(self, module):
                pass
        
        # Create and return the spec
        return spec_from_loader("{action.module_name}", ShimLoader())

# Install the finder at the beginning of sys.meta_path
sys.meta_path.insert(0, {action.package_name.capitalize()}{action.module_name.capitalize()}ShimFinder())
"""
        
        try:
            with open(shim_file, 'w') as f:
                f.write(content)
                
            # Also create/update the __init__.py file to import all shims
            init_file = os.path.join(shim_dir, "__init__.py")
            new_import = f"from .shim_{action.package_name}_{action.module_name} import *"
            
            if os.path.exists(init_file):
                with open(init_file, 'r') as f:
                    content = f.read()
                    
                if new_import not in content:
                    with open(init_file, 'a') as f:
                        f.write(f"\n{new_import}\n")
            else:
                with open(init_file, 'w') as f:
                    f.write(f"# Generated by ModGuard - DO NOT EDIT\n{new_import}\n")
            
            # Update project's main __init__.py to import the shims
            for root, dirs, files in os.walk(project_path):
                # Skip the .modguard directory itself
                if '.modguard' in root:
                    continue
                    
                # Look for a suitable __init__.py to modify
                if '__init__.py' in files:
                    init_path = os.path.join(root, '__init__.py')
                    with open(init_path, 'r') as f:
                        content = f.read()
                        
                    import_line = "import modguard.shims  # Namespace conflict resolution"
                    if import_line not in content:
                        with open(init_path, 'a') as f:
                            f.write(f"\n# Added by ModGuard to resolve namespace conflicts\n{import_line}\n")
                            
                    # Only update one __init__.py file (preferably the main one)
                    break
            
            return AppliedFix(
                action=action,
                success=True,
                details=f"Created import hook at {shim_file}"
            )
        except Exception as e:
            return AppliedFix(
                action=action,
                success=False,
                details=f"Failed to create import hook: {str(e)}"
            )
    
    @staticmethod
    def _apply_version_constraint_fix(action: FixAction, project_path: str) -> AppliedFix:
        """
        Apply a version constraint fix by updating requirements.txt or pyproject.toml.
        
        In a real implementation, we'd use more sophisticated version resolution.
        """
        files_to_check = [
            os.path.join(project_path, 'requirements.txt'),
            os.path.join(project_path, 'pyproject.toml')
        ]
        
        for file_path in files_to_check:
            if not os.path.exists(file_path):
                continue
                
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if file_path.endswith('.txt'):
                    # Handle requirements.txt
                    updated = re.sub(
                        rf'{action.package_name}(==|>=|<=|~=|>|<).*',
                        f'{action.package_name}=={action.details["new_version"]}',
                        content
                    )
                    
                    # If the package wasn't found, add it
                    if action.package_name not in updated:
                        updated += f'\n{action.package_name}=={action.details["new_version"]}\n'
                        
                elif file_path.endswith('.toml'):
                    # Simple handling for pyproject.toml
                    # A real implementation would use a TOML parser
                    if '[tool.poetry.dependencies]' in content:
                        # Poetry style
                        section = '[tool.poetry.dependencies]'
                    elif '[project.dependencies]' in content:
                        # PEP 621 style
                        section = '[project.dependencies]'
                    else:
                        # Can't find dependency section
                        continue
                        
                    # Simple string replacement (not robust, but illustrative)
                    pattern = rf'{action.package_name}\s*=\s*".*"'
                    replacement = f'{action.package_name} = "{action.details["new_version"]}"'
                    
                    # Check if package exists in dependencies
                    if re.search(pattern, content):
                        updated = re.sub(pattern, replacement, content)
                    else:
                        # Add after the section header
                        section_pos = content.find(section) + len(section)
                        updated = content[:section_pos] + f'\n{action.package_name} = "{action.details["new_version"]}"' + content[section_pos:]
                
                # Write updated content back
                with open(file_path, 'w') as f:
                    f.write(updated)
                    
                return AppliedFix(
                    action=action,
                    success=True,
                    details=f"Updated version constraint in {file_path}"
                )
                
            except Exception as e:
                return AppliedFix(
                    action=action,
                    success=False,
                    details=f"Failed to update version constraint: {str(e)}"
                )
        
        return AppliedFix(
            action=action,
            success=False,
            details="No requirements.txt or pyproject.toml found"
        )
    
    @classmethod
    def apply_fixes(cls, plan: FixPlan, project_path: str, dry_run: bool = False) -> FixResult:
        """
        Apply fixes from a fix plan.
        
        Args:
            plan: A FixPlan with fixes to apply
            project_path: Path to the project directory
            dry_run: If True, only simulate applying fixes
            
        Returns:
            A FixResult with the results of applying the fixes
        """
        result = FixResult(plan=plan)
        
        for action in plan.actions:
            if dry_run:
                # In dry run mode, just simulate success
                applied = AppliedFix(
                    action=action,
                    success=True,
                    details="Dry run - not actually applied"
                )
            else:
                # Apply the fix based on its type
                if action.fix_type == FixType.RENAME_SHIM:
                    applied = cls._apply_shim_fix(action, project_path)
                elif action.fix_type == FixType.VERSION_CONSTRAINT:
                    applied = cls._apply_version_constraint_fix(action, project_path)
                else:
                    applied = AppliedFix(
                        action=action,
                        success=False,
                        details=f"Fix type {action.fix_type} not implemented for automatic application"
                    )
            
            result.add_result(applied)
        
        return result