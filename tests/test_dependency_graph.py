"""
Tests for the dependency graph module.
"""
import os
import tempfile
from pathlib import Path

import pytest

from modguard.dependency.graph import DependencyGraph, DependencyGraphBuilder, DependencyNode
from modguard.models.conflict import PackageInfo


@pytest.fixture
def simple_graph():
    """Create a simple dependency graph for testing."""
    graph = DependencyGraph()
    
    # Create root package
    root = PackageInfo(name="root-project", version="1.0.0")
    
    # Create dependencies
    pkg1 = PackageInfo(name="package1", version="1.0.0")
    pkg2 = PackageInfo(name="package2", version="2.0.0")
    pkg3 = PackageInfo(name="package3", version="3.0.0")
    
    # Add dependencies
    graph.add_dependency(root, pkg1)
    graph.add_dependency(root, pkg2)
    graph.add_dependency(pkg1, pkg3)
    
    return graph


def test_dependency_node():
    """Test the DependencyNode class."""
    pkg1 = PackageInfo(name="package1", version="1.0.0")
    pkg2 = PackageInfo(name="package2", version="2.0.0")
    
    node1 = DependencyNode(pkg1)
    node2 = DependencyNode(pkg2)
    
    # Test adding dependency
    node1.add_dependency(node2)
    assert node2 in node1.dependencies
    
    # Test equality
    node1_dup = DependencyNode(PackageInfo(name="package1", version="1.1.0"))
    assert node1 == node1_dup
    assert node1 != node2
    
    # Test string representation
    assert str(node1) == "package1==1.0.0"


def test_dependency_graph(simple_graph):
    """Test the DependencyGraph class."""
    # Test get_all_packages
    all_packages = simple_graph.get_all_packages()
    assert len(all_packages) == 4
    assert any(pkg.name == "root-project" for pkg in all_packages)
    assert any(pkg.name == "package1" for pkg in all_packages)
    assert any(pkg.name == "package2" for pkg in all_packages)
    assert any(pkg.name == "package3" for pkg in all_packages)
    
    # Test get_dependencies
    pkg1_deps = simple_graph.get_dependencies("package1")
    assert len(pkg1_deps) == 1
    assert pkg1_deps[0].name == "package3"
    
    root_deps = simple_graph.get_dependencies("root-project")
    assert len(root_deps) == 2
    
    # Test get_all_dependencies
    all_deps = simple_graph.get_all_dependencies("root-project")
    assert len(all_deps) == 3
    
    # Test string representation
    graph_str = str(simple_graph)
    assert "Dependency Graph:" in graph_str
    assert "root-project" in graph_str
    assert "package1" in graph_str
    assert "package2" in graph_str
    assert "package3" in graph_str


def test_parse_requirements_txt():
    """Test parsing requirements.txt file."""
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("""
        # Comment line
        package1==1.0.0
        package2>=2.0.0
        package3
        package4 @ git+https://github.com/user/repo.git
        """)
        req_file = f.name
    
    try:
        requirements = DependencyGraphBuilder._parse_requirements_txt(req_file)
        
        assert len(requirements) == 4
        assert ("package1", "1.0.0") in requirements
        assert ("package2", ">=2.0.0") in requirements
        assert ("package3", "latest") in requirements
        assert ("package4", "latest") in requirements
    finally:
        os.unlink(req_file)


def test_parse_pyproject_toml():
    """Test parsing pyproject.toml file."""
    with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
        f.write("""
        [tool.poetry]
        name = "test-project"
        version = "1.0.0"
        
        [tool.poetry.dependencies]
        python = "^3.7"
        package1 = "1.0.0"
        package2 = {version = "^2.0.0", extras = ["all"]}
        package3 = {git = "https://github.com/user/repo.git"}
        
        [project]
        dependencies = [
            "package4>=4.0.0",
            "package5"
        ]
        """)
        pyproject_file = f.name
    
    try:
        # Mock the toml import
        with pytest.MonkeyPatch.context() as mp:
            # Create a mock toml module
            class MockToml:
                @staticmethod
                def load(file):
                    return {
                        "tool": {
                            "poetry": {
                                "dependencies": {
                                    "python": "^3.7",
                                    "package1": "1.0.0",
                                    "package2": {"version": "^2.0.0", "extras": ["all"]},
                                    "package3": {"git": "https://github.com/user/repo.git"}
                                }
                            }
                        },
                        "project": {
                            "dependencies": [
                                "package4>=4.0.0",
                                "package5"
                            ]
                        }
                    }
            
            mp.setattr("modguard.dependency.graph.toml", MockToml())
            
            requirements = DependencyGraphBuilder._parse_pyproject_toml(pyproject_file)
            
            assert len(requirements) >= 4
            assert ("package1", "1.0.0") in requirements
            assert ("package2", "^2.0.0") in requirements
            # package3 might be handled differently since it has no version
            assert any(pkg == "package4" and ver == ">=4.0.0" for pkg, ver in requirements)
            assert any(pkg == "package5" for pkg, _ in requirements)
    finally:
        os.unlink(pyproject_file)


def test_from_project():
    """Test building a dependency graph from a project directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create requirements.txt
        req_path = Path(temp_dir) / "requirements.txt"
        with open(req_path, "w") as f:
            f.write("""
            package1==1.0.0
            package2>=2.0.0
            """)
        
        # Create pyproject.toml
        pyproject_path = Path(temp_dir) / "pyproject.toml"
        with open(pyproject_path, "w") as f:
            f.write("""
            [tool.poetry]
            name = "test-project"
            version = "1.0.0"
            
            [tool.poetry.dependencies]
            python = "^3.7"
            package3 = "3.0.0"
            """)
        
        # Mock the toml import
        with pytest.MonkeyPatch.context() as mp:
            # Create a mock toml module
            class MockToml:
                @staticmethod
                def load(file):
                    return {
                        "tool": {
                            "poetry": {
                                "dependencies": {
                                    "python": "^3.7",
                                    "package3": "3.0.0"
                                }
                            }
                        }
                    }
            
            mp.setattr("modguard.dependency.graph.toml", MockToml())
            
            # Build the graph
            graph = DependencyGraphBuilder.from_project(temp_dir)
            
            # Check the graph
            all_packages = graph.get_all_packages()
            package_names = [pkg.name for pkg in all_packages]
            
            assert len(all_packages) == 4  # root + 3 dependencies
            assert Path(temp_dir).name in package_names
            assert "package1" in package_names
            assert "package2" in package_names
            assert "package3" in package_names