"""
Labor RAG System Version Information
=====================================

Version 4.2.0 - Match v3 Exactly (No Excluded Verbs)
Release Date: January 25, 2026

CRITICAL FIX (v4.2.0):
- Removed excluded verb logic to match v3 behavior exactly
- Root cause: v4 had excluded verbs ["read", "review", "view", etc.]
- v3 had NO excluded verbs - only checked (action_verb) AND (keyword)
- Result: v4 rejected tasks like "create and review reports"
- Impact: v4 returned 321 rows vs v3's 718 rows (56% fewer!)

SOLUTION:
- Removed excluded verb checking entirely
- Now uses EXACT v3 logic: substring matching for verbs + keywords
- No exclusions - if task has creation verb + keyword, it matches

COMPARISON:
- v3 (hardcoded): 32 occupations, 718 rows, 5,018k employment
- v4.0.4.1 (excluded+substring bug): 19 occupations, 473 rows
- v4.1.0 (excluded+word boundary): 17 occupations, 321 rows  
- v4.2.0 (no exclusions): ~32 occupations, ~718 rows ✅

BACKWARD COMPATIBILITY:
- Matches v3 results exactly
- Generic extensible framework maintained
- Enhanced query handling preserved
"""

__version__ = "4.2.0"
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
