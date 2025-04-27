"""
GitHub Actions integration for ModGuard.
"""
import json
import os
from typing import List, Optional

from modguard.models.conflict import ConflictReport, ConflictSeverity
from modguard.models.fix_plan import FixPlan


class GitHubActionReporter:
    """Reporter for GitHub Actions workflow."""
    
    @staticmethod
    def is_github_actions() -> bool:
        """Check if running in GitHub Actions environment."""
        return os.environ.get("GITHUB_ACTIONS") == "true"
    
    @staticmethod
    def get_annotation_command(
        type_: str, message: str, file: Optional[str] = None, 
        line: Optional[int] = None, col: Optional[int] = None
    ) -> str:
        """
        Get a GitHub Actions workflow command for annotations.
        
        Args:
            type_: The annotation type ('error', 'warning', or 'notice').
            message: The message to display.
            file: Optional file path where the annotation should be attached.
            line: Optional line number in the file.
            col: Optional column number in the file.
            
        Returns:
            A formatted GitHub Actions workflow command.
        """
        params = []
        
        if file:
            params.append(f"file={file}")
            
            if line:
                params.append(f"line={line}")
                
                if col:
                    params.append(f"col={col}")
        
        param_str = ",".join(params)
        if param_str:
            param_str = " " + param_str
        
        return f"::{type_}{param_str}::{message}"
    
    @staticmethod
    def severity_to_annotation_type(severity: str) -> str:
        """
        Convert a ConflictSeverity to GitHub annotation type.
        
        Args:
            severity: A ConflictSeverity value.
            
        Returns:
            A GitHub annotation type ('error', 'warning', or 'notice').
        """
        severity_map = {
            ConflictSeverity.CRITICAL: "error",
            ConflictSeverity.HIGH: "error",
            ConflictSeverity.MEDIUM: "warning",
            ConflictSeverity.LOW: "notice",
            ConflictSeverity.INFO: "notice",
        }
        return severity_map.get(severity, "warning")
    
    @classmethod
    def report_conflicts(cls, report: ConflictReport) -> List[str]:
        """
        Generate GitHub Actions annotations for conflicts.
        
        Args:
            report: The conflict report to annotate.
            
        Returns:
            A list of GitHub Actions workflow commands.
        """
        annotations = []
        
        # Check if we have a detailed report with severities
        has_severities = hasattr(report, "severities") and hasattr(report, "import_paths")
        
        for module_name, modules in report.conflicts.items():
            if len(modules) <= 1:
                continue  # No conflict
            
            # Get severity (if available)
            severity = ConflictSeverity.MEDIUM
            if has_severities:
                severity = getattr(report, "severities", {}).get(module_name, ConflictSeverity.MEDIUM)
            
            # Convert to annotation type
            annotation_type = cls.severity_to_annotation_type(severity)
            
            # Build message
            packages = [f"{m.package.name} ({m.package.version})" for m in modules]
            message = f"Module '{module_name}' has namespace conflicts between packages: {', '.join(packages)}"
            
            # Add annotation for each file where the module is imported (if available)
            if has_severities and module_name in getattr(report, "import_paths", {}):
                for import_path in getattr(report, "import_paths", {}).get(module_name, []):
                    # For simplicity, we're not parsing line/column numbers
                    annotations.append(cls.get_annotation_command(
                        annotation_type, message, file=import_path
                    ))
            else:
                # Add a general annotation
                annotations.append(cls.get_annotation_command(annotation_type, message))
        
        return annotations
    
    @classmethod
    def report_fix_plan(cls, fix_plan: FixPlan) -> List[str]:
        """
        Generate GitHub Actions annotations for fix suggestions.
        
        Args:
            fix_plan: The fix plan to annotate.
            
        Returns:
            A list of GitHub Actions workflow commands.
        """
        annotations = []
        
        for action in fix_plan.actions:
            # Build message
            message = f"Suggested fix: {action}"
            
            # Add as notice
            annotations.append(cls.get_annotation_command("notice", message))
        
        return annotations
    
    @classmethod
    def set_output(cls, name: str, value) -> None:
        """
        Set an output variable for GitHub Actions.
        
        Args:
            name: The name of the output variable.
            value: The value to set.
        """
        if cls.is_github_actions():
            # Handle complex objects
            if not isinstance(value, str):
                value = json.dumps(value)
            
            output_file = os.environ.get("GITHUB_OUTPUT")
            if output_file:
                with open(output_file, "a") as f:
                    f.write(f"{name}<<EOF\n{value}\nEOF\n")
            else:
                # Fallback for older GitHub Actions
                print(f"::set-output name={name}::{value}")