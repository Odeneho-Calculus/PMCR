"""
Models for representing conflicts and fix plans.
"""

from modguard.models.conflict import (
    ConflictReport,
    ConflictSeverity,
    DetailedConflictReport,
    ModuleInfo,
    PackageInfo,
)
from modguard.models.fix_plan import (
    AppliedFix,
    FixAction,
    FixPlan,
    FixResult,
    FixType,
)

__all__ = [
    "PackageInfo",
    "ModuleInfo",
    "ConflictReport",
    "ConflictSeverity",
    "DetailedConflictReport",
    "FixType",
    "FixAction",
    "FixPlan",
    "AppliedFix",
    "FixResult",
]