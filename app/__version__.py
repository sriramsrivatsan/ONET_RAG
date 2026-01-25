"""
Labor RAG System Version Information
=====================================

Version 4.6.0 - Fixed Category Detection (Removed Ambiguous "document" Verb)
Release Date: January 25, 2026

CRITICAL FIX (v4.6.0):
- Removed "document" as a verb from research category
- Root cause: "document" is both a VERB ("document findings") and a NOUN ("a document")
- Impact: Queries about "digital document users" were incorrectly classified as research
- Result: Lost 76% of data (169 vs 718 rows)

ISSUE EXAMPLE:
Query: "What industries are rich in digital document users?"
- v3: Detected as document_creation → 718 rows, 5,018k employment ✓
- v4.5.0: Detected as research → 169 rows, 2,830k employment ✗
- v4.6.0: Detects as document_creation → ~718 rows, ~5,018k employment ✓

ROOT CAUSE:
- research category had "document" in secondary verbs (meaning "document findings")
- Query contains "digital document users" (meaning "users of documents")
- Verb match (+1.0) beat keyword match (+0.8)
- Research won incorrectly!

SOLUTION:
- Changed research verbs from: ["...", "document"]
- To: ["...", "record"] (more specific, unambiguous)
- "document" remains in document_creation as a keyword
- Category detection now works correctly

BACKWARD COMPATIBILITY:
- Research queries still work (use "record", "log", "note" for documenting)
- Document creation queries now detected correctly
- All v4.5.0 improvements maintained
"""

__version__ = "4.6.0"
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
