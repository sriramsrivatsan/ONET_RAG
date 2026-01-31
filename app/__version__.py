"""
Labor RAG System Version Information
=====================================

Version 4.9.2 - Employment Query Routing Fix
Release Date: January 27, 2026

CRITICAL FIX (v4.9.2):
- Fixed "total employment" queries returning tasks instead of occupations
- Root cause: v4.9.0/v4.9.1 defaulted to tasks for all category queries
- Impact: Employment queries showed task details when users wanted occupation totals
- Result: Now detects employment keywords and returns occupation summaries

ISSUE EXAMPLE:
Query: "What's the total employment of workers that create digital documents?"

User expects: Occupation summary (35 occupations with employment totals) ✅
Before (v4.9.1):
- System returned: Task details (89 task descriptions) ❌
- Table showed: "Task Description | Occupation | Avg Time" ❌
- CSV had: 35 occupation rows ✅ (correct)
- Mismatch: CSV (occupations) ≠ UI (tasks) ❌

After (v4.9.2):
- System returns: Occupation summary (35 occupations) ✅
- Table shows: "Occupation | Employment | Industries" ✅
- CSV has: 35 occupation rows ✅
- Match: CSV (occupations) = UI (occupations) ✅

ROOT CAUSE:
v4.9.0/v4.9.1 changed routing to default to tasks for category queries:
```python
# v4.9.0/v4.9.1 LOGIC:
if wants_task_details:
    return task_details
elif wants_occupation_summary:  # Only if "jobs" or "occupations" in query
    return occupation_summary
else:
    return task_details  # ← DEFAULT for category queries
```

Problem: "total employment of workers that create X" defaulted to tasks!
But "total employment" clearly wants occupation-level aggregation, not task details.

Example breakdown:
- "workers that create documents" → could be tasks (WHAT they create)
- "**total employment** of workers that create documents" → occupations (HOW MANY in each job)
- "what **jobs** create documents" → occupations (WHO creates)

SOLUTION (v4.9.2):
Added employment keyword detection:

```python
# v4.9.2 FIX: Detect employment-related queries
wants_employment_summary = any(phrase in query_lower for phrase in [
    'total employment', 'employment of', 'how many workers', 'number of workers',
    'workforce', 'headcount', 'staff', 'employees'
])

# If query asks for employment data, treat as occupation query
if wants_employment_summary and not wants_task_details:
    wants_occupation_summary = True
```

Result: Employment queries now correctly route to occupation summaries!

CHANGES MADE:
- app/rag/retriever.py: Lines 100-110
  - Added wants_employment_summary detection
  - Employment keywords: total employment, employment of, how many workers, etc.
  - Auto-set wants_occupation_summary = True for employment queries
  - Only if NOT explicitly asking for tasks

EXAMPLES:

Query: "What's the total employment of workers that create documents?"
- v4.9.1: Returns tasks ❌
- v4.9.2: Returns occupations ✅ (detects "total employment")

Query: "How many workers create digital documents?"
- v4.9.1: Returns tasks ❌
- v4.9.2: Returns occupations ✅ (detects "how many workers")

Query: "What's the workforce for document creation?"
- v4.9.1: Returns tasks ❌
- v4.9.2: Returns occupations ✅ (detects "workforce")

Query: "Workers that create documents" (no employment keywords)
- v4.9.1: Returns tasks ✅
- v4.9.2: Returns tasks ✅ (no change - still defaults to tasks)

Query: "What tasks involve creating documents?"
- v4.9.1: Returns tasks ✅
- v4.9.2: Returns tasks ✅ (explicit task query - overrides employment)

ROUTING PRIORITY (v4.9.2):
1. Explicit task request ("what tasks") → tasks
2. Employment keywords ("total employment") → occupations
3. Explicit occupation request ("what jobs") → occupations
4. Industry request ("by industry") → industries
5. Default for category queries → tasks

IMPACT:
Before v4.9.2:
- "total employment of workers" → tasks (wrong) ❌
- CSV and UI mismatch ❌
- User confusion: "I wanted employment totals!" ❌

After v4.9.2:
- "total employment of workers" → occupations (correct) ✅
- CSV and UI match ✅
- User gets employment totals as expected ✅

BACKWARD COMPATIBILITY:
- Explicit task queries: Still work ("what tasks")
- Explicit occupation queries: Still work ("what jobs")
- Category queries without keywords: Still default to tasks
- NEW: Employment queries now return occupations

USER VALUE:
- Employment queries return correct data type
- CSV and UI are consistent
- Natural language works intuitively
- "total employment" gives employment totals (not task lists)

Previous Versions:
- v4.9.1: Fatal NameError fix (hotfix)
- v4.9.0: Task routing fix (introduced employment issue)
- v4.8.8: Validation count fix
"""

__version__ = "4.9.2"
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
