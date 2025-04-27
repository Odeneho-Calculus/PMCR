"""
Detect module namespace collisions in Python projects.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from modguard.models.conflict import ConflictReport, DetailedConflictReport, ModuleInfo


class CollisionDetector:
    """Detect module namespace collisions across packages."""
    
    @staticmethod
    def detect_collisions(modules_by_package: Dict[str, List[ModuleInfo]]) -> ConflictReport:
        """
        Detect module namespace collisions across packages.
        
        Args:
            modules_by_package: A dictionary mapping package names to lists of ModuleInfo
            
        Returns:
            A ConflictReport containing all detected collisions
        """
        # Create a map of module names to ModuleInfo objects
        module_map: Dict[str, List[ModuleInfo]] = {}
        
        # Process all modules from all packages
        for package_name, modules in modules_by_package.items():
            for module in modules:
                if module.name not in module_map:
                    module_map[module.name] = []
                module_map[module.name].append(module)
        
        # Create conflict report
        report = ConflictReport()
        
        # Find collisions (modules with the same name from different packages)
        for module_name, modules in module_map.items():
            # Consider it a collision if modules with the same name come from different packages
            packages = {module.package.name for module in modules}
            if len(packages) > 1:
                for module in modules:
                    report.add_conflict(module_name, module)
        
        return report
    
    @staticmethod
    def _find_imports_in_file(file_path: str) -> Dict[str, List[str]]:
        """
        Find import statements in a Python file.
        
        Returns a dictionary mapping module names to lists of import statements.
        """
        imports = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Regular imports (import xxx)
            for match in re.finditer(r'import\s+([^;#\n]+)', content):
                import_str = match.group(1).strip()
                for module in import_str.split(','):
                    module = module.strip()
                    
                    # Handle "import x as y"
                    if ' as ' in module:
                        module = module.split(' as ')[0].strip()
                    
                    # Extract the top-level module
                    top_module = module.split('.')[0]
                    if top_module not in imports:
                        imports[top_module] = []
                    imports[top_module].append(f"import {module}")
            
            # From imports (from xxx import yyy)
            for match in re.finditer(r'from\s+([^;#\n\s]+)\s+import\s+([^;#\n]+)', content):
                module = match.group(1).strip()
                imports_str = match.group(2).strip()
                
                # Extract the top-level module
                top_module = module.split('.')[0]
                if top_module not in imports:
                    imports[top_module] = []
                imports[top_module].append(f"from {module} import {imports_str}")
                
        except Exception as e:
            print(f"Error analyzing imports in {file_path}: {e}")
            
        return imports
    
    @classmethod
    def analyze_project_imports(cls, project_path: str, conflict_report: ConflictReport) -> DetailedConflictReport:
        """
        Analyze import statements in a project to find usage of conflicting modules.
        
        Args:
            project_path: Path to the project directory
            conflict_report: A ConflictReport containing detected conflicts
            
        Returns:
            A DetailedConflictReport with additional information about module usage
        """
        detailed_report = DetailedConflictReport()
        detailed_report.conflicts = conflict_report.conflicts.copy()
        
        # Get all conflicting module names
        conflicting_modules = set(conflict_report.conflicts.keys())
        
        # Find Python files in the project
        project_files = []
        for root, _, files in os.walk(project_path):
            for file in files:
                if file.endswith('.py'):
                    project_files.append(os.path.join(root, file))
        
        # Analyze imports in each file
        for file_path in project_files:
            file_imports = cls._find_imports_in_file(file_path)
            
            # Check for conflicting modules
            for module_name in conflicting_modules:
                if module_name in file_imports:
                    for import_stmt in file_imports[module_name]:
                        detailed_report.add_import_path(module_name, f"{file_path}: {import_stmt}")
                        
                        # Set severity based on heuristics
                        # For now, a simple heuristic: direct imports are higher severity
                        if import_stmt.startswith(f"import {module_name}") or import_stmt.startswith(f"from {module_name} import"):
                            detailed_report.set_severity(module_name, "HIGH")
                        else:
                            detailed_report.set_severity(module_name, "MEDIUM")
        
        return detailed_report
    
    @classmethod
    def scan_project(cls, project_path: str, modules_by_package: Dict[str, List[ModuleInfo]]) -> DetailedConflictReport:
        """
        Scan a project for module namespace collisions and analyze their impact.
        
        Args:
            project_path: Path to the project directory
            modules_by_package: A dictionary mapping package names to lists of ModuleInfo
            
        Returns:
            A DetailedConflictReport containing all detected collisions and their analysis
        """
        # Detect collisions
        conflict_report = cls.detect_collisions(modules_by_package)
        
        # Analyze project imports to assess impact
        detailed_report = cls.analyze_project_imports(project_path, conflict_report)
        
        return detailed_report