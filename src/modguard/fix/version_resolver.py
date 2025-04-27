"""
Version resolver for fixing module conflicts by suggesting alternative package versions.
"""
import re
import subprocess
from typing import Dict, List, Optional, Tuple

from modguard.models.conflict import ConflictReport, ModuleInfo, PackageInfo
from modguard.models.fix_plan import FixAction, FixPlan, FixType


class VersionResolver:
    """
    Resolve module conflicts by finding alternative package versions.
    """
    
    @staticmethod
    def _get_available_versions(package_name: str, count: int = 5) -> List[str]:
        """
        Get available versions for a package from PyPI.
        
        Args:
            package_name: The name of the package.
            count: The number of recent versions to return.
            
        Returns:
            A list of version strings.
        """
        try:
            # Use pip to get available versions
            result = subprocess.check_output(
                ["pip", "index", "versions", package_name],
                text=True,
                stderr=subprocess.PIPE
            )
            
            # Extract versions from output
            versions = []
            for line in result.splitlines():
                match = re.search(r'Available versions: (.+)', line)
                if match:
                    version_str = match.group(1)
                    versions = [v.strip() for v in version_str.split(',')]
                    break
            
            # Return the most recent versions
            return versions[:count]
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Try alternative approach (PyPI JSON API would be better but requires additional dependencies)
            try:
                result = subprocess.check_output(
                    ["pip", "install", f"{package_name}==", "--quiet"],
                    text=True,
                    stderr=subprocess.PIPE
                )
                
                # Extract versions from error message
                versions = []
                for line in result.splitlines():
                    match = re.search(r'from versions: (.+)', line)
                    if match:
                        version_str = match.group(1)
                        versions = [v.strip() for v in version_str.split(',')]
                        break
                
                return versions[:count]
            except subprocess.CalledProcessError:
                return []
    
    @staticmethod
    def _compare_modules(version1_modules: List[ModuleInfo], version2_modules: List[ModuleInfo]) -> Dict[str, bool]:
        """
        Compare modules between two versions of a package to detect changes.
        
        Args:
            version1_modules: List of ModuleInfo objects from version 1.
            version2_modules: List of ModuleInfo objects from version 2.
            
        Returns:
            Dictionary mapping module names to booleans indicating if they're in version 2.
        """
        v1_module_names = {m.name for m in version1_modules}
        v2_module_names = {m.name for m in version2_modules}
        
        result = {}
        for name in v1_module_names:
            result[name] = name in v2_module_names
        
        return result
    
    @classmethod
    def suggest_version_fixes(cls, conflict_report: ConflictReport) -> FixPlan:
        """
        Suggest alternative package versions to resolve conflicts.
        
        Args:
            conflict_report: The conflict report to resolve.
            
        Returns:
            A FixPlan with suggested version changes.
        """
        fix_plan = FixPlan(conflict_report=conflict_report)
        
        # Process each conflicting module
        for module_name, conflicting_modules in conflict_report.conflicts.items():
            if len(conflicting_modules) <= 1:
                continue  # No conflict
            
            # Group by packages
            modules_by_package = {}
            for module in conflicting_modules:
                if module.package.name not in modules_by_package:
                    modules_by_package[module.package.name] = []
                modules_by_package[module.package.name].append(module)
            
            # Only process if we have actual conflicts across packages
            if len(modules_by_package) <= 1:
                continue
            
            # For each package involved in the conflict
            for package_name, modules in modules_by_package.items():
                # Get alternative versions
                alt_versions = cls._get_available_versions(package_name)
                
                # Skip if we couldn't get alternative versions
                if not alt_versions:
                    continue
                
                # Suggest a fix using the latest alternative version
                latest_version = alt_versions[0]
                
                # Skip if it's the same version we already have
                if modules[0].package.version == latest_version:
                    continue
                
                # Create a fix action
                action = FixAction(
                    fix_type=FixType.VERSION_CONSTRAINT,
                    module_name=module_name,
                    package_name=package_name,
                    details={
                        "current_version": modules[0].package.version,
                        "new_version": latest_version,
                        "alt_versions": ",".join(alt_versions)
                    }
                )
                
                fix_plan.add_action(action)
        
        return fix_plan