"""
Labor RAG System Version Information
=====================================

Version 4.9.0 - Task vs Occupation Routing Fix
Release Date: January 27, 2026

MAJOR FIX (v4.9.0):
- Fixed queries about "workers that do X" returning occupations instead of tasks
- Root cause: System defaulted to occupation summaries for category queries
- Impact: Users asking WHAT workers do (tasks) got WHO does it (job titles)
- Result: Now returns tasks by default for category queries (what users expect)

ISSUE EXAMPLE:
Query: "What's the total employment of workers that create digital documents?"
User expects: Tasks involved in creating digital documents ✅
Before (v4.8.8):
- System returned: 35 occupation summaries (job titles) ❌
- CSV contained: Occupation names, employment counts
- User thought: "I wanted to know WHAT they do, not job titles!"

After (v4.9.0):
- System returns: 89 task descriptions (what workers do) ✅
- CSV contains: Task descriptions, hours/week, occupations
- User gets: Exactly what they asked for!

ROOT CAUSE:
When category is detected (e.g., "document_creation"), the routing logic was:

OLD LOGIC (v4.8.8):
```python
if wants_task_details:
    return task_details
elif wants_occupation_summary or not wants_task_details:  # ← WRONG DEFAULT
    return occupation_summary
```

Problem: If user doesn't explicitly say "what tasks", defaults to occupation summary
But "workers that create X" implies wanting to know WHAT they do (tasks)!

Example interpretations:
- "workers that create documents" → what do they create? (tasks) ✓
- "jobs that create documents" → which job titles? (occupations) ✓
- "employment of workers that create" → without "jobs", defaults to tasks ✓

NEW LOGIC (v4.9.0):
```python
if wants_task_details:
    return task_details
elif wants_industry_summary:
    return industry_summary
elif wants_occupation_summary:  # ← Only if explicitly requested
    return occupation_summary
else:
    return task_details  # ← DEFAULT for category queries
```

Logic: When someone asks about "workers that do X", they want to know WHAT workers do!

CSV GENERATION FIX:
Also updated CSV generator to prioritize task data:

OLD CSV PRIORITY:
1. occupation_employment (always used first)
2. industry_employment
3. task data (never reached)

NEW CSV PRIORITY (v4.9.0):
0. Task details (if task query detected) ← NEW TIER!
1. savings_analysis
2. occupation_employment (only if not task query)
3. industry_employment
4. ...

Detection logic:
```python
is_task_query = (
    'total_tasks' in computational_results and
    'filtered_dataframe' in retrieval_results
)

if is_task_query:
    csv = extract_task_details_from_dataframe(filtered_df)
```

CHANGES MADE:
- app/rag/retriever.py: Lines 186-205
  - Changed default from occupation_summary to task_details
  - Only return occupation_summary if explicitly requested
  - Separate route for category query default

- app/llm/csv_generator.py: Lines 105-127, 313-365
  - Added Tier 0 for task details (checked first)
  - New method: _extract_task_details_from_dataframe()
  - De-duplicates tasks, sorts by hours/week
  - Creates proper task CSV with columns:
    - Task Description
    - Occupation
    - Hours/Week
    - Employment (thousands)
    - Hourly Wage
    - Industries Count

EXAMPLES:

Query: "What's the total employment of workers that create digital documents?"
- v4.8.8: Returns 35 occupations ❌
- v4.9.0: Returns 89 tasks ✅

Query: "What jobs create digital documents?"
- v4.8.8: Returns 35 occupations ✅ (explicitly asked for "jobs")
- v4.9.0: Returns 35 occupations ✅ (still works - explicitly requested)

Query: "What occupations create digital documents?"
- v4.8.8: Returns 35 occupations ✅
- v4.9.0: Returns 35 occupations ✅ (explicitly requested)

Query: "What tasks are involved in creating digital documents?"
- v4.8.8: Returns 89 tasks ✅
- v4.9.0: Returns 89 tasks ✅

BACKWARD COMPATIBILITY:
- Explicit occupation queries: Still work (asks for "jobs" or "occupations")
- Explicit task queries: Still work (asks for "tasks")
- Implicit category queries: NOW RETURN TASKS (was occupations)

CSV STRUCTURE IMPROVEMENT:
Task CSV now includes:
- Task Description: Full text of what workers do
- Occupation: Which occupation performs this task
- Hours/Week: Time spent on task
- Employment: Number of workers
- Hourly Wage: Compensation
- Industries Count: How many industries use this task

IMPACT:
Before v4.9.0:
- "workers that do X" → occupation names (not helpful)
- User has to ask "what tasks" explicitly
- CSV shows job titles, not actual work

After v4.9.0:
- "workers that do X" → task descriptions (helpful!)
- Natural language works intuitively
- CSV shows actual work performed

USER VALUE:
- Get what you expect when asking about "workers that do X"
- See actual tasks, not just job titles
- CSV contains actionable task details
- Natural queries work correctly

Previous Versions:
- v4.8.8: Validation count fix
- v4.8.7: Time analysis CSV export fix
- v4.8.6: Display all rows (no truncation)
"""

__version__ = "4.9.0"
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
