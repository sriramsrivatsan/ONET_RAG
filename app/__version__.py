"""
Labor RAG System Version Information
=====================================

Version 4.7.0 - Fixed Follow-up Query Processing (Missing query_lower)
Release Date: January 25, 2026

CRITICAL FIX (v4.7.0):
- Fixed NameError in follow-up query processing
- Root cause: query_lower used without being defined in _process_followup_query()
- Impact: ALL follow-up queries crashed with "name 'query_lower' is not defined"

ISSUE:
Follow-up queries failed with:
```
🚨 Follow-up query failed: name 'query_lower' is not defined
❌ Follow-up query failed: name 'query_lower' is not defined
```

ROOT CAUSE:
In app/ui/client.py line 879, the code checked:
```python
if any(word in query_lower for word in ['total', 'sum', 'count', 'average', 'how many']):
```

But `query_lower` was NEVER defined in the `_process_followup_query` method!
The method had parameter `query: str` but never created `query_lower = query.lower()`

SOLUTION:
Added line before usage:
```python
# CRITICAL FIX v4.7.0: Define query_lower before using it
query_lower = query.lower()
```

IMPACT:
- Initial queries worked fine (query_lower defined in retriever.retrieve())
- Follow-up queries crashed (query_lower not defined in client._process_followup_query())
- 100% of follow-up queries affected

BACKWARD COMPATIBILITY:
- All v4.6.0 functionality maintained
- Follow-up queries now work correctly
- No impact on initial queries
"""

__version__ = "4.7.0"
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
