"""
Command-line interface for the ModGuard tool.
"""
import argparse
import logging
import os
import sys
from typing import Dict, List, Optional

from modguard.dependency.graph import DependencyGraphBuilder
from modguard.detector.collision_detector import CollisionDetector
from modguard.extractor.module_extractor import ModuleExtractor
from modguard.fix.engine import FixEngine
from modguard.models.conflict import ConflictReport, DetailedConflictReport
from modguard.models.fix_plan import FixPlan


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def scan_command(args) -> int:
    """
    Execute the scan command.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    project_path = args.path or os.getcwd()
    logging.info(f"Scanning project at {project_path}...")
    
    # Build dependency graph
    logging.info("Building dependency graph...")
    graph = DependencyGraphBuilder.from_project(project_path)
    
    if not graph.nodes:
        logging.error("No dependencies found. Make sure the project has a requirements.txt or pyproject.toml file.")
        return 1
    
    logging.info(f"Found {len(graph.nodes)} dependencies")
    
    # Extract modules
    logging.info("Extracting modules from dependencies...")
    modules_by_package = ModuleExtractor.extract_modules_from_dependency_graph(graph)
    
    # Detect collisions
    logging.info("Detecting module namespace collisions...")
    detailed_report = CollisionDetector.scan_project(project_path, modules_by_package)
    
    if not detailed_report.has_conflicts():
        logging.info("No module namespace collisions detected.")
        return 0
    
    # Print the report
    logging.info("\n" + str(detailed_report))
    
    # Generate fix plan
    fix_plan = FixEngine.suggest_fixes(detailed_report)
    logging.info("\n" + str(fix_plan))
    
    # Apply fixes if requested
    if args.fix:
        logging.info("Applying fixes...")
        fix_result = FixEngine.apply_fixes(fix_plan, project_path, dry_run=args.dry_run)
        logging.info("\n" + str(fix_result))
        
        if not fix_result.all_successful():
            logging.warning(f"Some fixes could not be applied ({fix_result.failure_count()} failures)")
            return 1
    
    # Return non-zero if conflicts were found (important for CI integration)
    return 0 if not detailed_report.has_conflicts() else (0 if args.fix else 1)


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        description="ModGuard: Preemptive Module-Conflict Resolver",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan project for module namespace collisions")
    scan_parser.add_argument("path", nargs="?", help="Path to the project directory (default: current directory)")
    scan_parser.add_argument("--fix", action="store_true", help="Apply suggested fixes")
    scan_parser.add_argument("--dry-run", action="store_true", help="Show what would be done without applying fixes")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Execute the appropriate command
    if args.command == "scan":
        return scan_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())