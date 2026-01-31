"""
Labor RAG System Version Information
=====================================

Version 4.8.8 - Validation Count Mismatch Fix
Release Date: January 27, 2026

CRITICAL FIX (v4.8.8):
- Fixed validation showing wrong entity count (tasks vs occupations)
- Root cause: Priority logic used metadata instead of actual data structure
- Impact: Occupation queries validated as task queries (89 tasks instead of 35 occupations)
- Result: Now correctly validates based on actual returned data type

ISSUE EXAMPLE:
Query: "What's the total employment of workers that create digital documents?"
Backend: Returns 35 occupations with employment data ✅
CSV Export: 35 rows (correct) ✅
Before (v4.8.7):
- Validation: "🔍 Validating tasks summary with 89 tasks" ❌
- UI might show: "89 tasks" instead of "35 occupations" ❌
- Confusion: CSV has 35 rows but UI says 89 ❌

After (v4.8.8):
- Validation: "🔍 Validating occupations summary with 35 occupations" ✅
- UI shows: "35 occupations" (matches CSV) ✅
- Consistent: CSV and UI match perfectly ✅

ROOT CAUSE:
Validation logic determined entity type using metadata presence:
```python
# OLD (v4.8.7) - WRONG PRIORITY:
is_occupation = 'total_occupations' in results and 'total_tasks' not in results
is_task = 'total_tasks' in results
```

Problem: If computational_results contains BOTH total_occupations AND total_tasks:
- is_occupation = False (because total_tasks is present)
- is_task = True (takes priority)
- Result: Occupation query validated as task query!

Why both were present:
1. Query: "What's the total employment of workers that create..."
2. System correctly returns OCCUPATION SUMMARY (35 occupations)
3. But data has 1083 task-occupation-industry rows
4. Task analysis runs: Finds 89 unique tasks in the data
5. Adds total_tasks=89 to computational_results (metadata)
6. Validation sees total_tasks, thinks it's a task query ❌
7. Validates against 89 tasks instead of 35 occupations ❌

SOLUTION:
Updated validation to check ACTUAL DATA STRUCTURES first, metadata second:

```python
# NEW (v4.8.8) - CORRECT PRIORITY:
# Priority 1: Check actual data returned
if 'occupation_employment' in results:
    # occupation_employment DataFrame exists → occupation query!
    is_occupation = True
    count = len(occupation_employment)  # Count actual rows

# Priority 2: Check industry data
elif 'industry_employment' in results or 'industry_proportions' in results:
    is_industry = True
    count = len(industry_data)

# Priority 3: Fall back to metadata (less reliable)
elif 'total_tasks' in results:
    is_task = True
    count = results['total_tasks']
elif 'total_occupations' in results:
    is_occupation = True
    count = results['total_occupations']
```

Logic: If occupation_employment DataFrame exists with 35 rows, it's an occupation query with 35 occupations, regardless of what other metadata exists!

CHANGES MADE:
- app/llm/response_builder.py: _validate_and_correct_totals()
  - Lines 36-94: Complete rewrite of entity type detection
  - Priority 1: occupation_employment / industry_employment
  - Priority 2: industry_proportions
  - Priority 3: Metadata fields (total_tasks, total_occupations, total_industries)
  - Added comprehensive logging for debugging
  - Ensures correct validation for all query types

IMPACT:
Before v4.8.8:
- Occupation queries: Validated as task queries if task metadata present ❌
- Count mismatch: CSV shows 35, validation uses 89 ❌
- User confusion: "Why does UI say 89 when CSV has 35?" ❌

After v4.8.8:
- Occupation queries: Always validated as occupation queries ✅
- Count match: CSV shows 35, validation uses 35 ✅
- User clarity: "UI and CSV both say 35 occupations" ✅

EXAMPLES:
Query: "What jobs create digital documents?"
- Returns: occupation_employment with 35 rows
- v4.8.7: Validates as "89 tasks" (wrong)
- v4.8.8: Validates as "35 occupations" (correct)

Query: "What industries are rich in document workers?"
- Returns: industry_employment with 20 rows
- v4.8.7: Validates as "89 tasks" if task metadata present (wrong)
- v4.8.8: Validates as "20 industries" (correct)

Query: "What tasks involve creating documents?"
- Returns: task details with 89 rows
- v4.8.7: Validates as "89 tasks" (correct - but by accident!)
- v4.8.8: Validates as "89 tasks" (correct - by design!)

BACKWARD COMPATIBILITY:
- All v4.8.7 features maintained
- Time analysis CSV fix (v4.8.7) preserved
- Display all rows (v4.8.6) preserved
- Universal CSV download (v4.8.5) preserved
- No breaking changes

USER VALUE:
- Correct validation messages
- CSV and UI consistency
- No more count confusion
- Professional accuracy

Previous Versions:
- v4.8.7: Time analysis CSV export fix
- v4.8.6: Display all rows (no truncation)
- v4.8.5: Universal CSV download for all queries
"""

__version__ = "4.8.8"
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
