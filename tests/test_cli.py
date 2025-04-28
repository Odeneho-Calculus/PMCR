"""
Tests for the CLI interface.
"""
import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from modguard.cli import main
from modguard.models.conflict import ConflictReport, ModuleInfo, PackageInfo
from modguard.models.fix_plan import FixAction, FixPlan, FixType


@pytest.fixture
def mock_scan_project():
    with mock.patch("modguard.cli.scan_project") as mock_scan:
        yield mock_scan


@pytest.fixture
def mock_suggest_fixes():
    with mock.patch("modguard.cli.suggest_fixes") as mock_suggest:
        yield mock_suggest


@pytest.fixture
def mock_apply_fixes():
    with mock.patch("modguard.cli.apply_fixes") as mock_apply:
        yield mock_apply


@pytest.fixture
def simple_conflict_report():
    """Create a simple conflict report for testing."""
    report = ConflictReport()
    
    # Create conflicting modules
    pkg1 = PackageInfo(name="package1", version="1.0.0")
    pkg2 = PackageInfo(name="package2", version="2.0.0")
    
    mod1 = ModuleInfo(name="utils", path="/path/to/package1/utils.py", package=pkg1)
    mod2 = ModuleInfo(name="utils", path="/path/to/package2/utils.py", package=pkg2)
    
    report.add_conflict("utils", mod1)
    report.add_conflict("utils", mod2)
    
    return report


@pytest.fixture
def simple_fix_plan(simple_conflict_report):
    """Create a simple fix plan for testing."""
    plan = FixPlan(conflict_report=simple_conflict_report)
    
    action = FixAction(
        fix_type=FixType.RENAME_SHIM,
        module_name="utils",
        package_name="package1",
        details={"renamed_to": "package1.utils"}
    )
    
    plan.add_action(action)
    
    return plan


def test_scan_command_no_conflicts(mock_scan_project, capsys):
    """Test scan command when no conflicts are found."""
    mock_scan_project.return_value = ConflictReport()
    
    # Run the CLI command
    main(["scan", "."])
    
    # Check output
    captured = capsys.readouterr()
    assert "No module conflicts detected" in captured.out
    mock_scan_project.assert_called_once_with(".")


def test_scan_command_with_conflicts(mock_scan_project, simple_conflict_report, capsys):
    """Test scan command when conflicts are found."""
    mock_scan_project.return_value = simple_conflict_report
    
    # Run the CLI command
    main(["scan", "."])
    
    # Check output
    captured = capsys.readouterr()
    assert "Detected" in captured.out
    assert "utils" in captured.out
    assert "package1" in captured.out
    assert "package2" in captured.out
    mock_scan_project.assert_called_once_with(".")


def test_scan_command_with_fix(
    mock_scan_project, mock_suggest_fixes, mock_apply_fixes, 
    simple_conflict_report, simple_fix_plan, capsys
):
    """Test scan command with --fix flag."""
    mock_scan_project.return_value = simple_conflict_report
    mock_suggest_fixes.return_value = simple_fix_plan
    
    # Run the CLI command
    main(["scan", ".", "--fix"])
    
    # Check that suggest_fixes and apply_fixes were called
    mock_scan_project.assert_called_once_with(".")
    mock_suggest_fixes.assert_called_once_with(simple_conflict_report)
    mock_apply_fixes.assert_called_once_with(simple_fix_plan)


def test_scan_command_with_dry_run(
    mock_scan_project, mock_suggest_fixes, mock_apply_fixes, 
    simple_conflict_report, simple_fix_plan, capsys
):
    """Test scan command with --dry-run flag."""
    mock_scan_project.return_value = simple_conflict_report
    mock_suggest_fixes.return_value = simple_fix_plan
    
    # Run the CLI command
    main(["scan", ".", "--dry-run"])
    
    # Check that suggest_fixes was called but apply_fixes was not
    mock_scan_project.assert_called_once_with(".")
    mock_suggest_fixes.assert_called_once_with(simple_conflict_report)
    mock_apply_fixes.assert_not_called()


def test_scan_command_with_exclude(mock_scan_project, capsys):
    """Test scan command with --exclude flag."""
    mock_scan_project.return_value = ConflictReport()
    
    # Run the CLI command
    main(["scan", ".", "--exclude", "package1,package2"])
    
    # Check that scan_project was called with the right arguments
    mock_scan_project.assert_called_once()
    args, kwargs = mock_scan_project.call_args
    assert args[0] == "."
    assert "exclude" in kwargs
    assert kwargs["exclude"] == ["package1", "package2"]


def test_scan_command_with_config_file():
    """Test scan command with a config file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock config file
        config_path = Path(temp_dir) / "modguard.toml"
        with open(config_path, "w") as f:
            f.write("""
            [scan]
            exclude = ["package1", "package2"]
            
            [fix]
            strategy = "rename_shim"
            """)
        
        with mock.patch("modguard.cli.scan_project") as mock_scan:
            mock_scan.return_value = ConflictReport()
            
            # Change to the temp directory and run the command
            with mock.patch("os.getcwd", return_value=temp_dir):
                main(["scan", "."])
            
            # Check that config was loaded
            mock_scan.assert_called_once()
            args, kwargs = mock_scan.call_args
            assert args[0] == "."
            assert "exclude" in kwargs
            assert kwargs["exclude"] == ["package1", "package2"]