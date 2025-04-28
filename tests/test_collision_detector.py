"""
Tests for the collision detector.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from modguard.detector.collision_detector import CollisionDetector
from modguard.models.conflict import ConflictReport, DetailedConflictReport, ModuleInfo, PackageInfo


class TestCollisionDetector(unittest.TestCase):
    """Test the CollisionDetector class."""

    def setUp(self):
        """Set up test data."""
        # Create package info objects
        self.pkg_a = PackageInfo(name="package-a", version="1.0.0")
        self.pkg_b = PackageInfo(name="package-b", version="2.0.0")
        self.pkg_c = PackageInfo(name="package-c", version="3.0.0")
        
        # Create module info objects
        self.module_a1 = ModuleInfo(name="utils", path="/path/to/package-a/utils.py", package=self.pkg_a)
        self.module_a2 = ModuleInfo(name="core", path="/path/to/package-a/core.py", package=self.pkg_a)
        self.module_b1 = ModuleInfo(name="utils", path="/path/to/package-b/utils.py", package=self.pkg_b)
        self.module_b2 = ModuleInfo(name="helpers", path="/path/to/package-b/helpers.py", package=self.pkg_b)
        self.module_c1 = ModuleInfo(name="core", path="/path/to/package-c/core.py", package=self.pkg_c)
        
        # Create modules by package dictionary
        self.modules_by_package = {
            "package-a": [self.module_a1, self.module_a2],
            "package-b": [self.module_b1, self.module_b2],
            "package-c": [self.module_c1]
        }

    def test_detect_collisions(self):
        """Test detecting module namespace collisions."""
        # Detect collisions
        report = CollisionDetector.detect_collisions(self.modules_by_package)
        
        # Verify the report
        self.assertTrue(report.has_conflicts())
        self.assertEqual(report.get_conflict_count(), 2)
        
        # Check that the correct modules are identified as conflicts
        self.assertIn("utils", report.conflicts)
        self.assertIn("core", report.conflicts)
        
        # Check that each conflict has the correct modules
        utils_conflict = report.conflicts["utils"]
        self.assertEqual(len(utils_conflict), 2)
        self.assertIn(self.module_a1, utils_conflict)
        self.assertIn(self.module_b1, utils_conflict)
        
        core_conflict = report.conflicts["core"]
        self.assertEqual(len(core_conflict), 2)
        self.assertIn(self.module_a2, core_conflict)
        self.assertIn(self.module_c1, core_conflict)
    
    def test_no_collisions(self):
        """Test detecting no collisions."""
        # Create modules by package dictionary with no collisions
        modules_by_package = {
            "package-a": [
                ModuleInfo(name="utils_a", path="/path/to/package-a/utils_a.py", package=self.pkg_a),
                ModuleInfo(name="core_a", path="/path/to/package-a/core_a.py", package=self.pkg_a)
            ],
            "package-b": [
                ModuleInfo(name="utils_b", path="/path/to/package-b/utils_b.py", package=self.pkg_b),
                ModuleInfo(name="helpers", path="/path/to/package-b/helpers.py", package=self.pkg_b)
            ]
        }
        
        # Detect collisions
        report = CollisionDetector.detect_collisions(modules_by_package)
        
        # Verify the report
        self.assertFalse(report.has_conflicts())
        self.assertEqual(report.get_conflict_count(), 0)
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="""
import os
import sys
import utils
from core import function
from package.module import Class
import another.module as am
    """)
    def test_find_imports_in_file(self, mock_open):
        """Test finding import statements in a Python file."""
        # Find imports
        imports = CollisionDetector._find_imports_in_file("test_file.py")
        
        # Verify the imports
        self.assertEqual(len(imports), 5)
        self.assertIn("os", imports)
        self.assertIn("sys", imports)
        self.assertIn("utils", imports)
        self.assertIn("core", imports)
        self.assertIn("package", imports)
        
        # Check that each import has the correct statements
        self.assertEqual(imports["os"], ["import os"])
        self.assertEqual(imports["sys"], ["import sys"])
        self.assertEqual(imports["utils"], ["import utils"])
        self.assertEqual(imports["core"], ["from core import function"])
        self.assertEqual(imports["package"], ["from package.module import Class"])
    
    @patch.object(CollisionDetector, '_find_imports_in_file')
    @patch('os.walk')
    def test_analyze_project_imports(self, mock_walk, mock_find_imports):
        """Test analyzing imports in a project."""
        # Mock os.walk to return some Python files
        mock_walk.return_value = [
            ("/path/to/project", ["subdir"], ["file1.py", "file2.py"]),
            ("/path/to/project/subdir", [], ["file3.py"])
        ]
        
        # Mock _find_imports_in_file to return some imports
        mock_find_imports.side_effect = [
            {"utils": ["import utils"], "os": ["import os"]},
            {"core": ["from core import function"]},
            {"utils": ["from utils import helper"]}
        ]
        
        # Create a conflict report
        report = ConflictReport()
        report.add_conflict("utils", self.module_a1)
        report.add_conflict("utils", self.module_b1)
        report.add_conflict("core", self.module_a2)
        report.add_conflict("core", self.module_c1)
        
        # Analyze project imports
        detailed_report = CollisionDetector.analyze_project_imports("/path/to/project", report)
        
        # Verify the detailed report
        self.assertTrue(isinstance(detailed_report, DetailedConflictReport))
        self.assertEqual(detailed_report.get_conflict_count(), 2)
        
        # Check that the import paths are correct
        self.assertIn("utils", detailed_report.import_paths)
        self.assertIn("core", detailed_report.import_paths)
        self.assertEqual(len(detailed_report.import_paths["utils"]), 2)
        self.assertEqual(len(detailed_report.import_paths["core"]), 1)


if __name__ == '__main__':
    unittest.main()