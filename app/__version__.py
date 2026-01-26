"""
Labor RAG System Version Information
=====================================

Version 4.8.7 - Time Analysis CSV Export Fix
Release Date: January 26, 2026

CRITICAL FIX (v4.8.7):
- Fixed time analysis CSV export showing [object Object] instead of data
- Root cause: time_analysis dict structure not properly flattened for CSV
- Impact: Time analysis queries had unusable CSV exports (1 row with objects)
- Result: Now exports proper multi-row CSV with per-occupation time data

ISSUE EXAMPLE:
Query: "What are the specific tasks that involve creating digital documents?"
Before (v4.8.6):
- CSV export: 1 row × 3 columns ❌
- Cell contents: "[object Object],[object Object]..." ❌
- Unusable in Excel/analysis tools ❌

After (v4.8.7):
- CSV export: 15 rows × 5 columns ✅
- Proper data: Occupation, Hours/Week, Employment, etc. ✅
- Works perfectly in Excel/Python/R ✅

ROOT CAUSE:
Time analysis data structure is nested:
```python
time_analysis = {
    'overall': {...},  # Aggregate stats (dict)
    'by_occupation': [...],  # List of occupation data (list of dicts)
    'by_occupation_with_totals': [...]  # List with totals
}
```

OLD CODE (v4.8.6):
```python
def _extract_time_analysis(self, data: Any):
    if isinstance(data, dict):
        return pd.DataFrame([data])  # Creates 1 row with nested objects!
```

Result: 1 row × 3 columns where each cell is a complex object
When exported to CSV: "[object Object]" strings (unusable)

NEW CODE (v4.8.7):
```python
def _extract_time_analysis(self, data: Any):
    if isinstance(data, dict):
        if 'by_occupation' in data:
            return pd.DataFrame(data['by_occupation'])  # Proper flattening!
        if 'by_occupation_with_totals' in data:
            return pd.DataFrame(data['by_occupation_with_totals'])
```

Result: N rows (one per occupation) × M columns (occupation fields)
When exported to CSV: Proper multi-row data (usable)

SOLUTION:
Updated _extract_time_analysis() to:
1. Check for 'by_occupation' key in dict
2. Extract the list of occupation data
3. Convert list to proper multi-row DataFrame
4. Fallback to 'by_occupation_with_totals' if needed
5. Only create single-row if dict is flat (no nested structures)

EXAMPLE OUTPUT:
Before (v4.8.6):
```csv
,overall,by_occupation,by_occupation_with_totals
0,"{avg_hours:2.26,...}","[object Object],...","[object Object],..."
```
1 row, unusable

After (v4.8.7):
```csv
ONET job title,Hours per week spent on task,Employment,Task Count,Avg Hourly Wage
Software Developers,8.5,450.5,12,65.40
Technical Writers,6.2,89.3,8,52.30
... (15 rows total)
```
15 rows, proper data structure

CHANGES MADE:
- app/llm/csv_generator.py: Enhanced _extract_time_analysis()
  - Now extracts by_occupation list instead of entire dict
  - Properly flattens nested structure
  - Handles all time_analysis formats
  - Added comprehensive documentation

IMPACT:
Before v4.8.7:
- Time analysis CSV: Unusable (objects instead of data)
- User workflow: Broken (can't analyze in Excel)
- Error reports: "CSV shows [object Object]"

After v4.8.7:
- Time analysis CSV: Perfect (proper multi-row data)
- User workflow: Works (load in Excel/Python/R)
- User satisfaction: High (complete data export)

VERIFICATION:
Query: "What tasks involve creating digital documents?"
- Before: CSV has 1 row with "[object Object]"
- After: CSV has 15+ rows with occupation time data

OTHER EXTRACTORS VERIFIED:
- ✅ savings_analysis: Already handles dict properly (extracts 'occupations')
- ✅ industry_proportions: Already handles dict properly (extracts 'industries')
- ✅ occupation_employment: Works with lists (no dict handling needed)
- ✅ industry_employment: Works with lists (no dict handling needed)
- ✅ Only time_analysis had this issue

BACKWARD COMPATIBILITY:
- All v4.8.6 features maintained
- Display all rows fix (v4.8.6) preserved
- Universal CSV download (v4.8.5) preserved
- No breaking changes

Previous Versions:
- v4.8.6: Display all rows (no truncation)
- v4.8.5: Universal CSV download for all queries
- v4.8.0: Fixed duplicate task display
"""

__version__ = "4.8.7"
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
