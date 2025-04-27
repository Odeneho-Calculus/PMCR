"""
Tests for the ModGuard CLI.
"""
import os
import tempfile
from unittest import mock

import pytest

# Import CLI module (to be implemented)
from modguard import cli
from modguard.models import ConflictReport, PackageInfo, ModuleInfo, FixPlan


class TestCLI:
    """Test cases for the CLI interface."""
    
    def test_scan_command_no_conflicts(self):
        """Test scanning with no conflicts."""
        with mock.patch('modguard.cli.scan_project') as mock_scan:
            # Create a ConflictReport with no conflicts
            report = ConflictReport()
            mock_scan.return_value = report
            
            # Run the CLI command
            runner = cli.get_cli_runner()
            result = runner.invoke(cli.main, ['scan', '.'])
            
            # Verify output
            assert result.exit_code == 0
            assert "No module conflicts detected" in result.output
            mock_scan.assert_called_once_with('.')
    
    def test_scan_command_with_conflicts(self):
        """Test scanning with conflicts."""
        with mock.patch('modguard.cli.scan_project') as mock_scan:
            # Create a ConflictReport with conflicts
            report = ConflictReport()
            pkg1 = PackageInfo(name='pkg1', version='1.0.0')
            pkg2 = PackageInfo(name='pkg2', version='2.0.0')
            
            module1 = ModuleInfo(name='utils', path='/path/to/pkg1/utils.py', package=pkg1)
            module2 = ModuleInfo(name='utils', path='/path/to/pkg2/utils.py', package=pkg2)
            
            report.add_conflict('utils', module1)
            report.add_conflict('utils', module2)
            
            mock_scan.return_value = report
            
            # Run the CLI command
            runner = cli.get_cli_runner()
            result = runner.invoke(cli.main, ['scan', '.'])
            
            # Verify output
            assert result.exit_code == 0
            assert "Module 'utils' conflicts between packages" in result.output
            mock_scan.assert_called_once_with('.')
    
    def test_scan_command_with_exit_code(self):
        """Test scanning with exit-code flag."""
        with mock.patch('modguard.cli.scan_project') as mock_scan:
            # Create a ConflictReport with conflicts
            report = ConflictReport()
            pkg1 = PackageInfo(name='pkg1', version='1.0.0')
            pkg2 = PackageInfo(name='pkg2', version='2.0.0')
            
            module1 = ModuleInfo(name='utils', path='/path/to/pkg1/utils.py', package=pkg1)
            module2 = ModuleInfo(name='utils', path='/path/to/pkg2/utils.py', package=pkg2)
            
            report.add_conflict('utils', module1)
            report.add_conflict('utils', module2)
            
            mock_scan.return_value = report
            
            # Run the CLI command
            runner = cli.get_cli_runner()
            result = runner.invoke(cli.main, ['scan', '.', '--exit-code'])
            
            # Should exit with non-zero code when conflicts are found
            assert result.exit_code == 1
            mock_scan.assert_called_once_with('.')
    
    def test_scan_command_with_fix(self):
        """Test scanning with fix flag."""
        with mock.patch('modguard.cli.scan_project') as mock_scan, \
             mock.patch('modguard.cli.suggest_fixes') as mock_suggest, \
             mock.patch('modguard.cli.apply_fixes') as mock_apply:
            
            # Create a ConflictReport with conflicts
            report = ConflictReport()
            pkg1 = PackageInfo(name='pkg1', version='1.0.0')
            pkg2 = PackageInfo(name='pkg2', version='2.0.0')
            
            module1 = ModuleInfo(name='utils', path='/path/to/pkg1/utils.py', package=pkg1)
            module2 = ModuleInfo(name='utils', path='/path/to/pkg2/utils.py', package=pkg2)
            
            report.add_conflict('utils', module1)
            report.add_conflict('utils', module2)
            
            mock_scan.return_value = report
            
            # Create a FixPlan
            fix_plan = FixPlan(conflict_report=report)
            mock_suggest.return_value = fix_plan
            
            # Run the CLI command
            runner = cli.get_cli_runner()
            result = runner.invoke(cli.main, ['scan', '.', '--fix'])
            
            # Verify proper function calls
            assert result.exit_code == 0
            mock_scan.assert_called_once_with('.')
            mock_suggest.assert_called_once_with(report)
            mock_apply.assert_called_once_with(fix_plan)
    
    def test_scan_command_with_dry_run(self):
        """Test scanning with dry-run flag."""
        with mock.patch('modguard.cli.scan_project') as mock_scan, \
             mock.patch('modguard.cli.suggest_fixes') as mock_suggest, \
             mock.patch('modguard.cli.apply_fixes') as mock_apply:
            
            # Create a ConflictReport with conflicts
            report = ConflictReport()
            pkg1 = PackageInfo(name='pkg1', version='1.0.0')
            pkg2 = PackageInfo(name='pkg2', version='2.0.0')
            
            module1 = ModuleInfo(name='utils', path='/path/to/pkg1/utils.py', package=pkg1)
            module2 = ModuleInfo(name='utils', path='/path/to/pkg2/utils.py', package=pkg2)
            
            report.add_conflict('utils', module1)
            report.add_conflict('utils', module2)
            
            mock_scan.return_value = report
            
            # Create a FixPlan
            fix_plan = FixPlan(conflict_report=report)
            mock_suggest.return_value = fix_plan
            
            # Run the CLI command
            runner = cli.get_cli_runner()
            result = runner.invoke(cli.main, ['scan', '.', '--dry-run'])
            
            # Verify proper function calls
            assert result.exit_code == 0
            mock_scan.assert_called_once_with('.')
            mock_suggest.assert_called_once_with(report)
            mock_apply.assert_not_called()  # Should not apply fixes in dry-run mode