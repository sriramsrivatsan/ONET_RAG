"""
Labor RAG System Version Information
=====================================

Version 4.0.2.2 - Maximum Diagnostics
Release Date: January 25, 2025

DIAGNOSTIC ENHANCEMENTS (v4.0.2.2):
- Added explicit logging for customer_service, design_creative, document_creation categories
- Log when phrases ARE found vs NOT found
- Log negation checking process step-by-step
- Log context windows for negation detection
- Log final negation results (will add/subtract points)
- Changed debug logs to info logs for visibility

PREVIOUS ENHANCEMENTS (v4.0.2.1):
- Added query length and hash logging
- Added phrase position context logging  
- Added last 50 chars of query logging
- Added phrase-only match penalty

CRITICAL FIXES (v4.0.2):
- Fixed negation detection (customer service false positive)
- Added verb inflection matching (creating → create)
- Fixed word boundary matching (read in spreadsheets)
- Enhanced logging for category detection

PREVIOUS FIXES:
- v4.0.1.1: Fixed query variable scope error in hybrid_router.py
- v4.0.1: Fixed orphaned code block in retriever.py (103 lines removed)
- v4.0.0: Generic task pattern framework

BACKWARD COMPATIBILITY:
- All existing queries continue to work
- API unchanged
"""

__version__ = "4.0.2.2"
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
