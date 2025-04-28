"""
Tests for the fix engine.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from modguard.fix.engine import FixEngine
from modguard.models.conflict import ConflictReport, ModuleInfo, PackageInfo
from modguard.models.fix_plan import FixAction, FixPlan, FixResult, FixType


class TestFixEngine(unittest.TestCase):
    """Test the FixEngine class."""

    def setUp(self):
        """Set up test data."""
        # Create package info objects
        self.pkg_a = PackageInfo(name="package-a", version="1.0.0")
        self.pkg_b = PackageInfo(name="package-b", version="2.0.0")
        
        # Create module info objects
        self.module_a = ModuleInfo(name="utils", path="/path/to/package-a/utils.py", package=self.pkg_a)
        self.module_b = ModuleInfo(name="utils", path="/path/to/package-b/utils.py", package=self.pkg_b)
        
        # Create a conflict report
        self.report = ConflictReport()
        self.report.add_conflict("utils", self.module_a)
        self.report.add_conflict("utils", self.module_b)

    def test_suggest_fixes(self):
        """Test suggesting fixes for conflicts."""
        # Suggest fixes
        fix_plan = FixEngine.suggest_fixes(self.report)
        
        # Verify the fix plan
        self.assertTrue(isinstance(fix_plan, FixPlan))
        self.assertTrue(fix_plan.has_actions())
        self.assertEqual(len(fix_plan.actions), 1)  # Should have one action for the conflict
        
        # Check that the action is correct
        action = fix_plan.actions[0]
        self.assertEqual(action.fix_type, FixType.RENAME_SHIM)
        self.assertEqual(action.module_name, "utils")
        self.assertEqual(action.package_name, "package-a")  # Should fix the first package by default
        self.assertEqual(action.details.get("renamed_to"), "package_a.utils")
    
    def test_suggest_fix_with_version_constraint(self):
        """Test suggesting a version constraint fix."""
        # Create packages with different versions of the same module
        pkg_a_v1 = PackageInfo(name="package-a", version="1.0.0")
        pkg_a_v2 = PackageInfo(name="package-a", version="2.0.0")
        
        module_a_v1 = ModuleInfo(name="utils", path="/path/to/package-a/v1/utils.py", package=pkg_a_v1)
        module_a_v2 = ModuleInfo(name="utils", path="/path/to/package-a/v2/utils.py", package=pkg_a_v2)
        
        # Create a conflict report
        report = ConflictReport()
        report.add_conflict("utils", module_a_v1)
        report.add_conflict("utils", module_a_v2)
        
        # Suggest fixes with version constraints
        fix_plan = FixEngine.suggest_fixes(report, prefer_version_constraint=True)
        
        # Verify the fix plan
        self.assertTrue(fix_plan.has_actions())
        self.assertEqual(len(fix_plan.actions), 1)
        
        # Check that the action is correct
        action = fix_plan.actions[0]
        self.assertEqual(action.fix_type, FixType.VERSION_CONSTRAINT)
        self.assertEqual(action.module_name, "utils")
        self.assertEqual(action.package_name, "package-a")
        self.assertIn("new_version", action.details)
    
    @patch('importlib.util.find_spec')
    def test_create_import_hook(self, mock_find_spec):
        """Test creating an import hook."""
        # Mock find_spec to return a spec for the module
        mock_spec = MagicMock()
        mock_spec.origin = self.module_a.path
        mock_find_spec.return_value = mock_spec
        
        # Create an import hook
        hook_module = FixEngine.create_import_hook("utils", "package_a.utils")
        
        # Verify the hook
        self.assertIsNotNone(hook_module)
        self.assertTrue(hasattr(hook_module, 'install'))
        
        # Test hook installation (would usually modify sys.meta_path)
        with patch('sys.meta_path') as mock_meta_path:
            mock_meta_path.insert = MagicMock()
            hook_module.install()
            mock_meta_path.insert.assert_called_once()
    
    def test_apply_rename_shim_fix(self):
        """Test applying a rename shim fix."""
        # Create a fix action
        action = FixAction(
            fix_type=FixType.RENAME_SHIM,
            module_name="utils",
            package_name="package-a",
            details={"renamed_to": "package_a.utils"}
        )
        
        # Apply the fix
        with patch.object(FixEngine, 'create_import_hook', return_value=MagicMock()) as mock_create_hook:
            result = FixEngine.apply_fix(action)
            
            # Verify the result
            self.assertTrue(result.success)
            mock_create_hook.assert_called_once_with("utils", "package_a.utils")
    
    def test_apply_version_constraint_fix(self):
        """Test applying a version constraint fix."""
        # Create a fix action
        action = FixAction(
            fix_type=FixType.VERSION_CONSTRAINT,
            module_name="utils",
            package_name="package-a",
            details={"new_version": "1.1.0"}
        )
        
        # Apply the fix
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', unittest.mock.mock_open(read_data="package-a==1.0.0\npackage-b==2.0.0")):
                with patch('builtins.open', unittest.mock.mock_open()) as mock_write:
                    result = FixEngine.apply_fix(action)
                    
                    # Verify the result
                    self.assertTrue(result.success)
    
    def test_apply_fix_plan(self):
        """Test applying a fix plan."""
        # Create a fix plan
        plan = FixPlan(self.report)
        plan.add_action(FixAction(
            fix_type=FixType.RENAME_SHIM,
            module_name="utils",
            package_name="package-a",
            details={"renamed_to": "package_a.utils"}
        ))
        
        # Apply the fix plan
        with patch.object(FixEngine, 'apply_fix', return_value=MagicMock(success=True)) as mock_apply_fix:
            result = FixEngine.apply_fix_plan(plan)
            
            # Verify the result
            self.assertTrue(result.all_successful())
            self.assertEqual(result.success_count(), 1)
            mock_apply_fix.assert_called_once()


if __name__ == '__main__':
    unittest.main()