"""
Build and analyze dependency graphs for Python projects.
"""
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from modguard.models.conflict import PackageInfo


class DependencyNode:
    """A node in the dependency graph representing a package."""
    
    def __init__(self, package: PackageInfo):
        self.package = package
        self.dependencies: List[DependencyNode] = []
    
    def add_dependency(self, node: 'DependencyNode') -> None:
        """Add a dependency to this node."""
        if node not in self.dependencies:
            self.dependencies.append(node)
    
    def __eq__(self, other):
        if not isinstance(other, DependencyNode):
            return False
        return self.package.name == other.package.name
    
    def __hash__(self):
        return hash(self.package.name)
    
    def __str__(self) -> str:
        return str(self.package)


class DependencyGraph:
    """A graph of package dependencies."""
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
    
    def add_node(self, package: PackageInfo) -> DependencyNode:
        """Add a node to the graph if it doesn't exist."""
        if package.name not in self.nodes:
            self.nodes[package.name] = DependencyNode(package)
        return self.nodes[package.name]
    
    def add_dependency(self, parent: PackageInfo, child: PackageInfo) -> None:
        """Add a dependency relationship between two packages."""
        parent_node = self.add_node(parent)
        child_node = self.add_node(child)
        parent_node.add_dependency(child_node)
    
    def get_all_packages(self) -> List[PackageInfo]:
        """Get all packages in the graph."""
        return [node.package for node in self.nodes.values()]
    
    def get_dependencies(self, package_name: str) -> List[PackageInfo]:
        """Get direct dependencies of a package."""
        if package_name not in self.nodes:
            return []
        return [node.package for node in self.nodes[package_name].dependencies]
    
    def get_all_dependencies(self, package_name: str) -> Set[PackageInfo]:
        """Get all dependencies (direct and transitive) of a package."""
        if package_name not in self.nodes:
            return set()
        
        result = set()
        to_visit = [self.nodes[package_name]]
        visited = set()
        
        while to_visit:
            node = to_visit.pop()
            if node in visited:
                continue
                
            visited.add(node)
            for dep in node.dependencies:
                result.add(dep.package)
                if dep not in visited:
                    to_visit.append(dep)
        
        return result
    
    def __str__(self) -> str:
        result = "Dependency Graph:\n"
        for name, node in self.nodes.items():
            result += f"- {name}\n"
            for dep in node.dependencies:
                result += f"  └─ {dep.package.name}\n"
        return result


class DependencyGraphBuilder:
    """Build dependency graphs from project files."""
    
    @staticmethod
    def _parse_requirements_txt(file_path: str) -> List[Tuple[str, str]]:
        """Parse requirements.txt file for package names and versions."""
        requirements = []
        if not os.path.exists(file_path):
            return requirements
            
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Handle egg fragments, URLs, etc.
                if ' @ ' in line:
                    pkg_name = line.split(' @ ')[0]
                    # For simplicity, use 'latest' for URL dependencies
                    requirements.append((pkg_name, 'latest'))
                    continue
                
                # Basic version specifier
                match = re.match(r'^([^<>=!~]+)(?:[<>=!~]=?|$)(.*)$', line)
                if match:
                    pkg_name = match.group(1).strip()
                    version = match.group(2).strip() or 'latest'
                    requirements.append((pkg_name, version))
                    
        return requirements
    
    @staticmethod
    def _parse_pyproject_toml(file_path: str) -> List[Tuple[str, str]]:
        """Parse pyproject.toml file for package dependencies."""
        requirements = []
        if not os.path.exists(file_path):
            return requirements
            
        try:
            import toml
            with open(file_path, 'r') as file:
                pyproject = toml.load(file)
                
            # Poetry dependencies
            if 'tool' in pyproject and 'poetry' in pyproject['tool']:
                if 'dependencies' in pyproject['tool']['poetry']:
                    for pkg_name, version in pyproject['tool']['poetry']['dependencies'].items():
                        if pkg_name == 'python':  # Skip python version
                            continue
                        if isinstance(version, dict):
                            version = version.get('version', 'latest')
                        requirements.append((pkg_name, str(version)))
                        
            # PEP 621 dependencies
            if 'project' in pyproject and 'dependencies' in pyproject['project']:
                for dep in pyproject['project']['dependencies']:
                    # Simple string dependency
                    if isinstance(dep, str):
                        match = re.match(r'^([^<>=!~]+)(?:[<>=!~]=?|$)(.*)$', dep)
                        if match:
                            pkg_name = match.group(1).strip()
                            version = match.group(2).strip() or 'latest'
                            requirements.append((pkg_name, version))
                    
        except ImportError:
            print("Warning: toml package not found. Unable to parse pyproject.toml.")
        except Exception as e:
            print(f"Error parsing pyproject.toml: {e}")
            
        return requirements
    
    @classmethod
    def from_project(cls, project_path: str) -> DependencyGraph:
        """Build a dependency graph from a project directory."""
        graph = DependencyGraph()
        project_path = Path(project_path)
        
        # Parse requirements.txt
        req_files = [
            project_path / "requirements.txt",
            project_path / "requirements" / "base.txt",
            project_path / "requirements" / "production.txt",
            project_path / "requirements" / "dev.txt"
        ]
        
        # Parse pyproject.toml
        pyproject_file = project_path / "pyproject.toml"
        
        # Create root package
        root_package = PackageInfo(
            name=project_path.name,
            version="0.0.0"  # Default version for the project
        )
        
        # Parse requirements
        for req_file in req_files:
            if req_file.exists():
                for pkg_name, version in cls._parse_requirements_txt(str(req_file)):
                    dep_package = PackageInfo(name=pkg_name, version=version)
                    graph.add_dependency(root_package, dep_package)
        
        # Parse pyproject.toml
        if pyproject_file.exists():
            for pkg_name, version in cls._parse_pyproject_toml(str(pyproject_file)):
                dep_package = PackageInfo(name=pkg_name, version=version)
                graph.add_dependency(root_package, dep_package)
        
        # Build transitive dependencies
        # Note: In a real implementation, we'd use pip's dependency resolver
        # For this simplified version, we're not resolving transitive dependencies
        
        return graph