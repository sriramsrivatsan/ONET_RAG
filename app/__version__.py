"""
Labor RAG System Version Information
=====================================

Version 4.0.4.1 - Variable Scope Fix
Release Date: January 25, 2026

HOTFIX (v4.0.4.1):
- Fixed: NameError: 'query_for_pattern_matching' is not defined
- Location: Line 1275 in retriever.py (_computational_retrieval method)
- Cause: Variable only exists in retrieve() method scope
- Solution: Use 'query' parameter (already contains original query)
- Impact: Fixes runtime error after successful pattern matching

CRITICAL FIX (v4.0.4):
- Pass ORIGINAL query to pattern matching
- Pass ENHANCED query to vector search  
- Modified retrieve() to accept both queries
- Updated response_builder.py to pass original_query
- All pattern matching uses original query

BACKWARD COMPATIBILITY:
- All existing queries continue to work
- API accepts optional original_query parameter
"""

__version__ = "4.0.4.1"
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
