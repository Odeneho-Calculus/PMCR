"""
Tests for the module extractor.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from modguard.extractor.module_extractor import ModuleExtractor
from modguard.models.conflict import ModuleInfo, PackageInfo


class TestModuleExtractor(unittest.TestCase):
    """Test the ModuleExtractor class."""

    @patch('importlib.metadata.distribution')
    @patch('os.walk')
    def test_get_package_modules(self, mock_walk, mock_distribution):
        """Test extracting modules from an installed package."""
        # Mock the package metadata
        mock_dist = MagicMock()
        mock_dist.version = "1.0.0"
        mock_dist.locate_file.return_value = "/path/to/package/__init__.py"
        mock_distribution.return_value = mock_dist
        
        # Mock the file system
        mock_walk.return_value = [
            ("/path/to/package", ["subdir"], ["__init__.py", "module1.py", "module2.py"]),
            ("/path/to/package/subdir", [], ["__init__.py", "submodule.py"]),
            ("/path/to/package/__pycache__", [], ["module1.cpython-39.pyc"]),
        ]
        
        # Extract modules
        modules = ModuleExtractor._get_package_modules("test-package")
        
        # Verify the results
        self.assertEqual(len(modules), 3)  # 3 .py files excluding __init__.py and __pycache__
        
        # Check that each module has the correct properties
        module_names = {m.name for m in modules}
        self.assertSetEqual(module_names, {"module1", "module2", "submodule"})
        
        # Check that each module has the correct package info
        for module in modules:
            self.assertEqual(module.package.name, "test-package")
            self.assertEqual(module.package.version, "1.0.0")
    
    @patch('subprocess.check_call')
    @patch('venv.create')
    def test_virtual_env_setup(self, mock_create, mock_check_call):
        """Test creating a virtual environment and installing a package."""
        # Mock the venv creation
        mock_create.return_value = None
        
        # Mock the pip installation
        mock_check_call.return_value = 0
        
        # Create virtual environment
        ModuleExtractor._create_virtual_env("/tmp/test-venv")
        mock_create.assert_called_once()
        
        # Install package
        result = ModuleExtractor._install_package("/tmp/test-venv", "test-package==1.0.0")
        self.assertTrue(result)
        mock_check_call.assert_called_once()
    
    @patch('subprocess.check_output')
    def test_run_extractor_script(self, mock_check_output):
        """Test running the extractor script in a virtual environment."""
        # Mock the script output
        mock_check_output.return_value = """
        [
            {
                "name": "module1",
                "path": "/path/to/package/module1.py",
                "full_name": "module1"
            },
            {
                "name": "module2",
                "path": "/path/to/package/module2.py",
                "full_name": "module2"
            }
        ]
        """
        
        # Run the extractor script
        modules = ModuleExtractor._run_extractor_script("/tmp/test-venv", "test-package")
        
        # Verify the results
        self.assertEqual(len(modules), 2)
        self.assertEqual(modules[0]["name"], "module1")
        self.assertEqual(modules[1]["name"], "module2")
    
    @patch.object(ModuleExtractor, '_get_package_modules')
    def test_extract_modules_from_package_direct(self, mock_get_modules):
        """Test extracting modules from a package directly."""
        # Mock the direct extraction
        package_info = PackageInfo(name="test-package", version="1.0.0")
        mock_modules = [
            ModuleInfo(name="module1", path="/path/to/module1.py", package=package_info),
            ModuleInfo(name="module2", path="/path/to/module2.py", package=package_info)
        ]
        mock_get_modules.return_value = mock_modules
        
        # Extract modules
        modules = ModuleExtractor.extract_modules_from_package("test-package")
        
        # Verify the results
        self.assertEqual(modules, mock_modules)
        mock_get_modules.assert_called_once_with("test-package")
    
    @patch.object(ModuleExtractor, '_install_package')
    @patch.object(ModuleExtractor, '_create_virtual_env')
    @patch.object(ModuleExtractor, '_run_extractor_script')
    def test_extract_modules_from_package_venv(self, mock_run_script, mock_create_venv, mock_install):
        """Test extracting modules from a package using a virtual environment."""
        # Mock the virtual environment setup
        mock_create_venv.return_value = None
        mock_install.return_value = True
        
        # Mock the script output
        mock_run_script.return_value = [
            {
                "name": "module1",
                "path": "/path/to/package/module1.py",
                "full_name": "module1"
            },
            {
                "name": "module2",
                "path": "/path/to/package/module2.py",
                "full_name": "module2"
            }
        ]
        
        # Extract modules
        modules = ModuleExtractor.extract_modules_from_package("test-package", "1.0.0")
        
        # Verify the results
        self.assertEqual(len(modules), 2)
        self.assertEqual(modules[0].name, "module1")
        self.assertEqual(modules[1].name, "module2")
        self.assertEqual(modules[0].package.name, "test-package")
        self.assertEqual(modules[0].package.version, "1.0.0")


if __name__ == '__main__':
    unittest.main()