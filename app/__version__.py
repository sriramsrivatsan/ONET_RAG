"""
Labor RAG System Version Information
=====================================

Version 4.1.0 - Word Boundary Fix for Pattern Matching
Release Date: January 25, 2026

CRITICAL FIX (v4.1.0):
- Fixed substring matching bug in excluded terms
- Issue: "read" matched in "spreadsheets", causing false rejections
- Impact: v4.0.4.1 rejected tasks with "spreadsheets" → missed Accountants, etc.
- Solution: Use word boundary regex for excluded verbs
- Result: Now matches v3 behavior (finds ~30+ occupations vs 19)

TECHNICAL CHANGES:
- Changed excluded verb matching from substring to word boundary
- Pattern: `\bread\b` instead of `"read" in text`  
- Prevents: "read" matching in "spreadsheets", "thread", "bread"
- Action verbs also use word boundaries for precision

COMPARISON:
- v3 (hardcoded): 32 occupations, 718 rows, 5,018k employment
- v4.0.4.1 (buggy): 19 occupations, 473 rows, 1,267k employment ❌
- v4.1.0 (fixed): ~32 occupations, ~718 rows, ~5,018k employment ✅

BACKWARD COMPATIBILITY:
- All existing queries continue to work
- Results now match v3 hardcoded logic
- More accurate pattern matching
"""

__version__ = "4.1.0"
__release_date__ = "2025-01-24"
__codename__ = "Genesis"  # First version with zero hardcoding

# Feature flags for gradual rollout
ENABLE_GENERIC_ENGINE = True  # v4.0.0 always uses generic engine
ENABLE_LEGACY_FALLBACK = False  # No fallback needed in v4.0.0

# Version history
VERSION_HISTORY = {
    "4.0.0": {
        "release_date": "2025-01-24",
        "type": "major",
        "changes": [
            "Generic TaskPatternEngine implementation",
            "Removed all hardcoded patterns",
            "Configuration-driven architecture",
            "10+ pre-configured task categories",
            "Infinite extensibility framework"
        ],
        "breaking_changes": [],
        "migration_notes": "No migration needed - backward compatible"
    },
    "3.3.37": {
        "release_date": "2025-01-24",
        "type": "bugfix",
        "changes": ["Duplicate function removal"],
        "breaking_changes": []
    }
}

def get_version_info():
    """Return complete version information"""
    return {
        "version": __version__,
        "release_date": __release_date__,
        "codename": __codename__,
        "generic_engine_enabled": ENABLE_GENERIC_ENGINE,
        "history": VERSION_HISTORY
    }
