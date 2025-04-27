"""
Preemptive Module-Conflict Resolver - A tool to detect and resolve Python module namespace collisions.

This package provides tools to identify and fix module namespace conflicts between Python packages
before they cause runtime errors or unpredictable behavior.
"""

__version__ = "0.1.0"

from modguard.models.conflict import ConflictReport, DetailedConflictReport, PackageInfo, ModuleInfo
from modguard.models.fix_plan import FixPlan, FixAction, FixType

# Public API
def scan_project(path: str) -> ConflictReport:
    """
    Analyze the project's dependencies and report any namespace conflicts.
    
    Args:
        path: Path to the project directory
        
    Returns:
        A ConflictReport object with details about conflicting modules
    """
    from modguard.dependency.graph import DependencyGraphBuilder
    from modguard.extractor.module_extractor import ModuleExtractor
    from modguard.detector.collision_detector import CollisionDetector
    
    # Build dependency graph
    graph = DependencyGraphBuilder.from_project(path)
    
    # Extract modules from all packages
    modules_by_package = ModuleExtractor.extract_modules_from_dependency_graph(graph)
    
    # Detect collisions
    return CollisionDetector.detect_collisions(modules_by_package)

def suggest_fixes(report: ConflictReport) -> FixPlan:
    """
    Generate a plan to resolve conflicts.
    
    Args:
        report: A ConflictReport object with details about conflicting modules
        
    Returns:
        A FixPlan object detailing the recommended actions
    """
    from modguard.fix.engine import FixEngine
    
    engine = FixEngine()
    return engine.generate_fix_plan(report)

def apply_fixes(plan: FixPlan, dry_run: bool = True):
    """
    Apply the fixes in the given plan.
    
    Args:
        plan: A FixPlan object detailing the actions to take
        dry_run: If True, only simulate applying the fixes
        
    Returns:
        A FixResult object with details about the applied fixes
    """
    from modguard.fix.engine import FixEngine
    
    engine = FixEngine()
    return engine.apply_fixes(plan, dry_run=dry_run)