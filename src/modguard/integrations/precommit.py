"""
Pre-commit hook integration for ModGuard.
"""
import os
import sys
from typing import Dict, List, Optional, Tuple

from modguard.models.conflict import ConflictReport


class PreCommitHook:
    """Integration with pre-commit hooks framework."""
    
    @staticmethod
    def is_pre_commit_environment() -> bool:
        """Check if running in a pre-commit environment."""
        return "PRE_COMMIT" in os.environ
    
    @staticmethod
    def create_hook_config() -> Dict:
        """
        Create a configuration for the pre-commit hook.
        
        Returns:
            Dictionary with pre-commit hook configuration.
        """
        return {
            "id": "modguard",
            "name": "ModGuard - Detect Module Conflicts",
            "description": "Detect Python module namespace collisions",
            "entry": "modguard",
            "language": "python",
            "types": ["python"],
            "args": ["scan", ".", "--exit-code"],
            "require_serial": True,
            "pass_filenames": False,
        }
    
    @staticmethod
    def generate_sample_config() -> str:
        """
        Generate a sample pre-commit configuration.
        
        Returns:
            A YAML string with pre-commit configuration.
        """
        return """# Add this to your .pre-commit-config.yaml
repos:
-   repo: https://github.com/yourusername/pmcr
    rev: v0.1.0  # Use the specific version you want
    hooks:
    -   id: modguard
"""
    
    @classmethod
    def format_for_pre_commit(cls, report: ConflictReport) -> Tuple[str, int]:
        """
        Format the conflict report for pre-commit output.
        
        Args:
            report: The conflict report to format.
            
        Returns:
            A tuple with (formatted_output, exit_code).
        """
        if not report.has_conflicts():
            return "No module conflicts detected.", 0
        
        output = []
        output.append(f"ModGuard detected {report.get_conflict_count()} module conflicts:")
        output.append("")
        
        for module_name, modules in report.conflicts.items():
            if len(modules) <= 1:
                continue  # No conflict
                
            packages = [f"{m.package.name} ({m.package.version})" for m in modules]
            output.append(f"- Module '{module_name}' conflicts between: {', '.join(packages)}")
        
        output.append("")
        output.append("Run 'modguard scan . --fix' to apply automatic fixes.")
        
        return "\n".join(output), 1  # Exit code 1 indicates failure