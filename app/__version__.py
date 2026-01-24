"""
Labor RAG System Version Information
=====================================

Version 4.0.0 - Generic Task Pattern Framework
Release Date: January 24, 2025

MAJOR CHANGES:
- Removed ALL hardcoded task patterns
- Implemented generic TaskPatternEngine
- Configuration-driven pattern matching
- Infinite extensibility via YAML config
- Zero code changes needed for new task categories

PREVIOUS VERSIONS:
- v3.3.37: Duplicate function removal + task validation
- v3.3.36: Task query validation fix
- v3.3.35: Validator storage fix
- v3.3.34: Industry query merge fix
- v3.3.33: Truncation fix
- v3.3.32: CSV export fix
- v3.3.31: Double path fix
- v3.3.30: Arithmetic validation system

BACKWARD COMPATIBILITY:
- All existing queries continue to work
- Existing document creation queries automatically use new engine
- API unchanged
"""

__version__ = "4.0.0"
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
