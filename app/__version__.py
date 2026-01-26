"""
Labor RAG System Version Information
=====================================

Version 4.8.5 - Universal CSV Download for All Queries
Release Date: January 25, 2026

MAJOR FEATURE (v4.8.5):
- Universal CSV download for ALL query types (100% coverage)
- Three-tier CSV generation strategy (computational → semantic → fallback)
- Enhanced UI with preview functionality
- Sequential naming (query1.csv, query2.csv, etc.)
- CSV is NEVER None - always generates something

FEATURE DETAILS:

What Changed:
- NEW: UniversalCSVGenerator class with 3-tier strategy
- NEW: CSV generated for every single query (no exceptions)
- NEW: Preview functionality before download
- NEW: Enhanced UI showing row/column count and file size
- REMOVED: Conditional CSV logic (was only 40% of queries)
- IMPROVED: Consistent user experience across all query types

Three-Tier Generation Strategy:
1. Tier 1 (Preferred): Extract from computational results
   - Savings analysis, occupation summaries, industry data
   - Uses existing structured data
   
2. Tier 2 (Common): Convert semantic results to CSV
   - Task details, occupation details, general matches
   - Converts search results to structured format
   
3. Tier 3 (Fallback): Create summary CSV
   - Query metadata, timestamp, note
   - Ensures CSV is never None

CSV Coverage by Query Type:
- Task detail queries → CSV with all tasks shown
- Occupation queries → CSV with occupation summaries
- Industry queries → CSV with industry data
- Time analysis → CSV with time statistics
- Savings analysis → CSV with savings breakdown
- General queries → CSV with semantic results or metadata
- Follow-up queries → CSV with follow-up results

UI Improvements:
- Preview button to see data before downloading
- Shows row count, column count, and file size
- Clean, professional layout
- Works on mobile devices

Impact:
- Before: ~40% of queries had CSV
- After: 100% of queries have CSV
- Benefit: Consistent, predictable behavior
- User Value: Every query is exportable to Excel/Python/R

Technical Changes:
- app/llm/csv_generator.py: NEW - Universal CSV generator
- app/llm/response_builder.py: Updated QueryProcessor with CSV generator
- app/ui/client.py: Always show CSV download with enhanced UI
- Removed all conditional CSV logic

BACKWARD COMPATIBILITY:
- All v4.8.0 functionality maintained
- Follow-up queries work correctly
- No duplicate tasks (v4.8.0 fix preserved)
- Enhanced with universal CSV feature

Previous Versions:
- v4.8.0: Fixed duplicate task display (de-duplication)
- v4.7.0: Fixed follow-up query processing (missing query_lower)
- v4.6.0: Fixed category detection (ambiguous "document" term)
- v4.5.0: Added missing plural keywords
- v4.4.0: Added "diagram", "graph", "blueprint", "schematic"
- v4.3.0: Added "program" and "model" keywords
- v4.2.0: Enhanced pattern matching configuration
"""

__version__ = "4.8.5"
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
