"""
Labor RAG System Version Information
=====================================

Version 4.0.3 - Enhanced Query Detection & Fix
Release Date: January 25, 2026

CRITICAL FIX (v4.0.3):
- Detected root cause: Pattern matching runs on ENHANCED queries
- Added safeguard to detect and reject enhanced queries
- Enhanced queries contain appended text like "develop new concepts design creative"
- Pattern matching now returns None if enhanced query detected
- Added call tracking to detect multiple calls with different queries
- Logs show exactly which query text is being analyzed

DIAGNOSTIC FEATURES (v4.0.2.2):
- Maximum diagnostic logging for phrase detection
- Step-by-step negation checking logs
- Context window visualization
- Phrase position and substring logging

CRITICAL FIXES (v4.0.2):
- Fixed negation detection (customer service false positive)
- Added verb inflection matching (creating → create)
- Fixed word boundary matching (read in spreadsheets)
- Enhanced logging for category detection

BACKWARD COMPATIBILITY:
- All existing queries continue to work
- API unchanged
"""

__version__ = "4.0.3"
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
