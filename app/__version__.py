"""
Labor RAG System Version Information
=====================================

Version 4.0.4 - Original Query for Pattern Matching
Release Date: January 25, 2026

CRITICAL FIX (v4.0.4):
- Fixed root cause: Pass ORIGINAL query to pattern matching
- Modified retrieve() to accept both original and enhanced queries
- Enhanced query used for vector search (better recall)
- Original query used for pattern matching (accurate categorization)
- Updated response_builder.py to pass original_query parameter
- All detect_task_category() calls now use original query
- v4.0.3 safeguard kept as secondary protection

HOW IT WORKS:
- User query → Enhanced with task-related terms
- Enhanced query → Vector search (finds more relevant docs)
- Original query → Pattern matching (accurate category detection)
- Result: Best of both worlds!

PREVIOUS FIXES (v4.0.3):
- Detected enhanced query problem via diagnostic logging
- Added safeguard to reject enhanced queries
- Call tracking and query hash logging

BACKWARD COMPATIBILITY:
- All existing queries continue to work
- API accepts optional original_query parameter
- Defaults to query if original_query not provided
"""

__version__ = "4.0.4"
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
