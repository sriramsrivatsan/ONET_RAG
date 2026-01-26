"""
Labor RAG System Version Information
=====================================

Version 4.8.6 - Display All Rows (No Truncation)
Release Date: January 26, 2026

CRITICAL FIX (v4.8.6):
- Fixed data display truncation across ALL query types
- Root cause: Prompt templates truncated to 10-15 items, LLM followed suit
- Impact: Users saw partial data in UI even though CSV had complete data
- Result: Now ALL rows displayed in both UI response and CSV

ISSUE EXAMPLE:
Query: "What industries are rich in digital document users?"
Before (v4.8.5):
- CSV export: 20 industries ✅ (correct)
- UI display: Only 10 industries ❌ (truncated)
- User experience: Confusing - why is CSV different from display?

After (v4.8.6):
- CSV export: 20 industries ✅ (correct)
- UI display: ALL 20 industries ✅ (complete)
- User experience: Consistent - CSV matches display

ROOT CAUSE:
Multiple truncation points in prompt_templates.py:
1. Line 636: industry_list[:15] → Limited to 15 industries
2. Line 659: "Include at least top 10" → LLM thought 10 was enough
3. Line 690: time_data[:10] → Limited to 10 occupations
4. Line 725: savings_data[:10] → Limited to 10 occupations
5. Line 610: grouped[:10] → Limited to 10 items
6. Line 781: skills[:10] → Limited to 10 industries
7. Line 845: tasks[:10] → Limited to 10 industries

SOLUTION:
Removed ALL arbitrary truncation limits:
- Industry proportions: Now shows ALL industries (was 15 → now unlimited)
- Time analysis: Now shows ALL occupations (was 10 → now unlimited)
- Savings analysis: Now shows ALL occupations (was 10 → now unlimited)
- Grouped results: Now shows ALL items (was 10 → now unlimited)
- Skill analysis: Now shows ALL industries (was 10 → now unlimited)
- Task analysis: Now shows ALL industries (was 10 → now unlimited)

Updated LLM instructions:
- OLD: "Include at least top 10 industries"
- NEW: "⚠️ SHOW ALL X INDUSTRIES IN THE TABLE (NO TRUNCATION)"
- Added explicit counts: "All 20 industries" instead of "Top 10"
- Added warnings: "DO NOT abbreviate or truncate the table"

CHANGES MADE:
- app/llm/prompt_templates.py: Removed all [:10] and [:15] slices
- Updated all instructions to emphasize "show ALL"
- Added item counts to context (e.g., "All 20 industries")
- Consistent behavior across all query types

IMPACT:
Before v4.8.6:
- Industry queries: Showed 10 of 20 (50% truncated)
- Occupation queries: Showed 10 of 30 (67% truncated)
- Time analysis: Showed 10 of 25 (60% truncated)
- Inconsistent user experience

After v4.8.6:
- ALL query types: Show 100% of data
- CSV matches UI display
- Complete, accurate information
- Professional user experience

BACKWARD COMPATIBILITY:
- All v4.8.5 features maintained
- Universal CSV download still works perfectly
- Follow-up queries work correctly
- No breaking changes

USER VALUE:
- See complete data every time
- No more "where are the other rows?"
- CSV and display are consistent
- Trust the system shows everything

Previous Versions:
- v4.8.5: Universal CSV download for all queries
- v4.8.0: Fixed duplicate task display (de-duplication)
- v4.7.0: Fixed follow-up query processing
- v4.6.0: Fixed category detection
"""

__version__ = "4.8.6"
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
