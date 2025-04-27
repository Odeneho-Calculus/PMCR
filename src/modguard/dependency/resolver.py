"""
Resolve package dependencies and their versions.
"""
import os
import re
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Set, Tuple

from modguard.models.conflict import PackageInfo


class DependencyResolver:
    """Resolve package dependencies and compatible versions."""
    
    @staticmethod
    def _create_temp_venv() -> Tuple[str, str]:
        """Create a temporary virtual environment for resolving dependencies."""
        temp_dir = tempfile.mkdtemp(prefix="modguard-resolver-")
        
        # Create virtual environment
        subprocess.check_call(
            [sys.executable, "-m", "venv", temp_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Determine pip path
        if sys.platform == 'win32':
            pip_path = os.path.join(temp_dir, 'Scripts', 'pip')
        else:
            pip_path = os.path.join(temp_dir, 'bin', 'pip')
            
        return temp_dir, pip_path
    
    @staticmethod
    def _get_available_versions(pip_path: str, package_name: str) -> List[str]:
        """Get available versions of a package."""
        try:
            output = subprocess.check_output(
                [pip_path, "index", "versions", package_name],
                stderr=subprocess.DEVNULL,
                text=True
            )
            
            # Parse output to extract versions
            match = re.search(r"Available versions: (.+)", output)
            if match:
                versions_str = match.group(1)
                return [v.strip() for v in versions_str.split(',')]
            return []
        except subprocess.CalledProcessError:
            return []
    
    @staticmethod
    def _check_compatibility(pip_path: str, package_specs: List[str]) -> bool:
        """Check if a set of package specifications are compatible."""
        try:
            # Use pip to check if the given set of packages can be installed together
            subprocess.check_call(
                [pip_path, "download", "--no-deps"] + package_specs,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            return False
            
    @classmethod
    def find_compatible_versions(cls, packages: List[PackageInfo], package_to_update: str) -> Optional[str]:
        """
        Find a compatible version of a package that resolves conflicts.
        
        Args:
            packages: List of packages in the current project
            package_to_update: Name of the package to find a compatible version for
            
        Returns:
            A compatible version string, or None if no compatible version was found
        """
        try:
            # Create temporary virtual environment
            temp_dir, pip_path = cls._create_temp_venv()
            
            try:
                # Get all available versions of the package
                available_versions = cls._get_available_versions(pip_path, package_to_update)
                
                if not available_versions:
                    return None
                
                # Create package specs for the current packages (excluding the one to update)
                current_specs = [
                    f"{p.name}=={p.version}" for p in packages 
                    if p.name != package_to_update and p.version != "latest"
                ]
                
                # Try each version, starting from the newest
                for version in sorted(available_versions, reverse=True):
                    # Skip the current version
                    if any(p.name == package_to_update and p.version == version for p in packages):
                        continue
                        
                    # Check if this version is compatible with other packages
                    if cls._check_compatibility(pip_path, current_specs + [f"{package_to_update}=={version}"]):
                        return version
                        
                return None
            finally:
                # Clean up
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            print(f"Error finding compatible versions: {e}")
            return None
            
    @classmethod
    def get_transitive_dependencies(cls, package_name: str, version: str = None) -> List[PackageInfo]:
        """
        Get the transitive dependencies of a package.
        
        Args:
            package_name: Name of the package
            version: Specific version of the package, or None for the latest
            
        Returns:
            List of dependencies as PackageInfo objects
        """
        try:
            # Create temporary virtual environment
            temp_dir, pip_path = cls._create_temp_venv()
            
            try:
                # Install the package
                package_spec = f"{package_name}" if version is None or version == "latest" else f"{package_name}=={version}"
                subprocess.check_call(
                    [pip_path, "install", package_spec],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                # Get the dependencies
                output = subprocess.check_output(
                    [pip_path, "show", package_name],
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                
                # Parse dependencies from the output
                dependencies = []
                in_requires_section = False
                installed_version = None
                
                for line in output.splitlines():
                    line = line.strip()
                    
                    # Extract the installed version
                    if line.startswith("Version:"):
                        installed_version = line.split(":", 1)[1].strip()
                        
                    # Check if we're in the "Requires" section
                    if line.startswith("Requires:"):
                        in_requires_section = True
                        deps_line = line.split(":", 1)[1].strip()
                        if deps_line:  # Handle non-empty "Requires:" line
                            for dep in deps_line.split(","):
                                dep = dep.strip()
                                if dep:
                                    dependencies.append(PackageInfo(name=dep, version="latest"))
                    elif in_requires_section and line:
                        # Handle multi-line "Requires" section
                        for dep in line.split(","):
                            dep = dep.strip()
                            if dep:
                                dependencies.append(PackageInfo(name=dep, version="latest"))
                    elif in_requires_section:
                        # End of "Requires" section
                        break
                
                # Add the package itself with its resolved version
                dependencies.insert(0, PackageInfo(name=package_name, version=installed_version or version or "latest"))
                
                return dependencies
            finally:
                # Clean up
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            print(f"Error getting transitive dependencies: {e}")
            return [PackageInfo(name=package_name, version=version or "latest")]