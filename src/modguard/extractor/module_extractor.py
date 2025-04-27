"""
Extract module information from installed packages.
"""
import importlib.metadata
import importlib.util
import os
import subprocess
import sys
import tempfile
import json 
import venv
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from modguard.models.conflict import ModuleInfo, PackageInfo


class ModuleExtractor:
    """Extract module information from installed packages."""

    @staticmethod
    def _get_package_modules(package_name: str) -> List[ModuleInfo]:
        """Get all modules within an installed package."""
        try:
            # Get package metadata
            dist = importlib.metadata.distribution(package_name)
            package_info = PackageInfo(name=package_name, version=dist.version)
            
            # Get package location
            if hasattr(dist, 'locate_file'):
                package_path = os.path.dirname(dist.locate_file(''))
            else:
                # Fallback for older Python versions
                package_path = os.path.dirname(dist.files[0].locate())
            
            modules = []
            package_path = Path(package_path)
            
            # Walk through package directory to find modules
            for root, dirs, files in os.walk(package_path):
                root_path = Path(root)
                rel_path = root_path.relative_to(package_path)
                
                # Skip __pycache__ and similar directories
                if any(part.startswith('__') and part.endswith('__') for part in rel_path.parts):
                    continue
                
                # Process Python files
                for file in files:
                    if file.endswith('.py'):
                        module_name = file[:-3]  # Remove .py extension
                        
                        # Skip __init__ and similar files
                        if module_name.startswith('__') and module_name.endswith('__'):
                            continue
                        
                        # Construct full module path
                        if str(rel_path) == '.':
                            full_module_name = module_name
                        else:
                            full_module_name = f"{rel_path}.{module_name}".replace('/', '.')
                        
                        # Create ModuleInfo
                        module_info = ModuleInfo(
                            name=module_name,
                            path=str(root_path / file),
                            package=package_info
                        )
                        modules.append(module_info)
            
            return modules
        except (importlib.metadata.PackageNotFoundError, AttributeError, IndexError) as e:
            print(f"Error extracting modules from {package_name}: {e}")
            return []
    
    @staticmethod
    def _create_virtual_env(path: str) -> None:
        """Create a virtual environment at the specified path."""
        venv.create(path, with_pip=True)
    
    @staticmethod
    def _install_package(venv_path: str, package_spec: str) -> bool:
        """Install a package in the virtual environment."""
        try:
            # Determine pip executable path based on platform
            if sys.platform == 'win32':
                pip_path = os.path.join(venv_path, 'Scripts', 'pip')
            else:
                pip_path = os.path.join(venv_path, 'bin', 'pip')
            
            # Run pip install
            subprocess.check_call(
                [pip_path, 'install', '--no-deps', package_spec],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def _run_extractor_script(venv_path: str, package_name: str) -> List[dict]:
        """Run a script in the virtual environment to extract module info."""
        # Create a temporary script
        script_content = f"""
import importlib.metadata
import os
import json
from pathlib import Path

try:
    # Get package metadata
    dist = importlib.metadata.distribution("{package_name}")
    
    # Get package location
    if hasattr(dist, 'locate_file'):
        package_path = os.path.dirname(dist.locate_file(''))
    else:
        # Fallback for older Python versions
        package_path = os.path.dirname(dist.files[0].locate())
    
    modules = []
    package_path = Path(package_path)
    
    # Walk through package directory to find modules
    for root, dirs, files in os.walk(package_path):
        root_path = Path(root)
        try:
            rel_path = root_path.relative_to(package_path)
        except ValueError:
            # If not relative to package_path, skip
            continue
        
        # Skip __pycache__ and similar directories
        if any(part.startswith('__') and part.endswith('__') for part in rel_path.parts):
            continue
        
        # Process Python files
        for file in files:
            if file.endswith('.py'):
                module_name = file[:-3]  # Remove .py extension
                
                # Skip __init__ and similar files
                if module_name.startswith('__') and module_name.endswith('__'):
                    continue
                
                # Construct full module path
                if str(rel_path) == '.':
                    full_module_name = module_name
                else:
                    full_module_name = f"{{rel_path}}.{{module_name}}".replace('/', '.')
                
                # Create ModuleInfo
                modules.append({{
                    "name": module_name,
                    "path": str(root_path / file),
                    "full_name": full_module_name
                }})
    
    # Output as JSON
    print(json.dumps(modules))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""
        with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # Determine python executable path based on platform
            if sys.platform == 'win32':
                python_path = os.path.join(venv_path, 'Scripts', 'python')
            else:
                python_path = os.path.join(venv_path, 'bin', 'python')
            
            # Run the script
            result = subprocess.check_output(
                [python_path, script_path],
                stderr=subprocess.DEVNULL,
                text=True
            )
            
            # Parse the JSON output
            return json.loads(result)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            print(f"Error running extractor script: {e}")
            return []
        finally:
            # Clean up
            os.unlink(script_path)
    
    @classmethod
    def extract_modules_from_package(cls, package_name: str, version: str = None) -> List[ModuleInfo]:
        """Extract module information from a package."""
        # For installed packages, use direct extraction
        if version is None:
            try:
                return cls._get_package_modules(package_name)
            except Exception as e:
                print(f"Error extracting modules directly: {e}")
        
        # For specific versions or if direct extraction failed, use a virtual environment
        package_spec = f"{package_name}" if version is None or version == "latest" else f"{package_name}=={version}"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create virtual environment
            cls._create_virtual_env(temp_dir)
            
            # Install package
            if not cls._install_package(temp_dir, package_spec):
                print(f"Failed to install {package_spec}")
                return []
            
            # Extract module info
            module_dicts = cls._run_extractor_script(temp_dir, package_name)
            
            # Convert to ModuleInfo objects
            package_info = PackageInfo(name=package_name, version=version or "latest")
            modules = [
                ModuleInfo(
                    name=m["name"],
                    path=m["path"],
                    package=package_info
                )
                for m in module_dicts if "name" in m and "path" in m
            ]
            
            return modules
    
    @classmethod
    def extract_modules_from_dependency_graph(cls, graph) -> Dict[str, List[ModuleInfo]]:
        """Extract modules from all packages in a dependency graph."""
        result = {}
        
        # Process all packages in the graph
        for package in graph.get_all_packages():
            modules = cls.extract_modules_from_package(package.name, package.version)
            result[package.name] = modules
        
        return result

