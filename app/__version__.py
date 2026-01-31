"""
Labor RAG System Version Information
=====================================

Version 4.9.3 - Follow-up Query Context & Processing Enhancements
Release Date: January 27, 2026

CRITICAL FIX (v4.9.3):
- Fixed follow-up queries returning wrong data (context loss)
- Enhanced follow-up processing with advanced calculations
- Root cause: Stored background dataset instead of displayed results
- Impact: Follow-up questions about "above tasks" returned different data
- Result: Now stores what user SAW + handles complex follow-up queries

PART 1: CONTEXT PRESERVATION FIX

ISSUE EXAMPLE:
Initial Query: "Can you tell me the tasks that could likely benefit from this customer service AI solution?"

System Response:
- Showed 6 customer service tasks (Advertising Sales, Education, etc.)
- Total: 923.50k workers across 6 occupations ✅

Follow-up Query: "How much time could this agent potentially shave off the **above tasks** each week?"
                                                                         ^^^^^^^^
User clearly refers to the 6 tasks they just saw

Before v4.9.3:
- Returned: Animal Caretakers (feeding/grooming animals) ❌
- Total: 1.52k workers across 1 occupation ❌
- WRONG DATA! User asked about customer service tasks!

After v4.9.3:
- Returns: The same 6 customer service tasks user saw ✅
- Total: 923.50k workers across 6 occupations ✅
- CORRECT! Matches what user was asking about ✅

ROOT CAUSE:
System stored two different datasets:
1. **filtered_dataframe:** 77 rows (ALL customer_service tasks, including Animal Caretakers)
2. **semantic_results:** 6 de-duplicated tasks (SHOWN to user)

Follow-up query used #1 (77 rows) instead of #2 (6 displayed tasks)!

SOLUTION (v4.9.3 - Part 1):
Reversed priority - store what was SHOWN first:

```python
# NEW LOGIC:
if semantic_results exists (what user saw):
    store semantic_results as filtered_dataset  # ← PRIORITY!
    also store filtered_dataframe as backup context
elif filtered_dataframe exists:
    store filtered_dataframe (fallback)
```

PART 2: ENHANCED FOLLOW-UP PROCESSING

NEW CAPABILITIES (v4.9.3):
Added support for complex follow-up queries:
1. ✅ Time aggregation ("total time per week")
2. ✅ Top-N ranking ("top 10 occupations by time")
3. ✅ Cost savings calculations (time × wage × employment)
4. ✅ Multi-column calculations and aggregations

REAL-WORLD CONVERSATION FLOW:

Q1: "Can you tell me the jobs that could benefit from this AI solution?"
→ Returns occupation summary ✅

Q2: "Can you tell me the specific job tasks this solution could help with?"
→ Returns task details from Q1 occupations ✅

Q3: "How much total time each week do workers spend on these tasks?"
→ NEW: Aggregates time across tasks ✅
→ Returns: "Total Time: 145.5 hours across 6 tasks"

Q4: "How much time could this agent potentially shave off the above tasks?"
→ Uses displayed tasks (v4.9.3 context fix) ✅
→ LLM provides estimation based on task context

Q5: "Can you show me the top-10 occupations that could save the most time?"
→ NEW: Aggregates by occupation, ranks, returns top 10 ✅
→ Returns: Ranked list with time per occupation

Q6: "Can you put the results above in a csv file?"
→ CSV always generated automatically ✅

Q7: "What marketing recommendations do you have to encourage adoption?"
→ LLM provides contextual business recommendations ✅

Q8: "What's the dollar savings this solution could achieve?"
→ NEW: Calculates time × wage × employment ✅
→ Returns: Weekly and annual savings estimates

TECHNICAL ENHANCEMENTS:

**Enhanced Simple Aggregation (_simple_aggregation_on_filtered_data):**

1. **Time Aggregation:**
```python
if 'total' in query and 'time' in query:
    total_time = df['Task time per week'].sum()
    return f"Total Time: {total_time} hours"
```

2. **Top-N Ranking:**
```python
if 'top' in query or 'highest' in query:
    n = extract_number_from_query(query)  # e.g., 10
    occupation_time = df.groupby('Occupation')['Time'].sum()
    top_n = occupation_time.nlargest(n)
    return ranked_list
```

3. **Savings Calculation:**
```python
if 'savings' in query or 'dollar' in query:
    # De-duplicate employment
    unique_df = df.groupby(['Occupation', 'Industry']).agg({
        'Time': 'sum',
        'Wage': 'mean',
        'Employment': 'first'
    })
    
    # Calculate: time × automation_factor × wage × workers
    weekly_savings = (time * 0.5 * wage * employment * 1000).sum()
    annual_savings = weekly_savings * 52
    return savings_report
```

**Enhanced Query Routing:**
```python
# OLD: Only detected basic aggregations
if any(word in query for word in ['total', 'sum', 'count', 'average']):

# NEW: Detects rankings and calculations too
is_simple_query = any([
    # Basic aggregations
    any(word in query for word in ['total', 'sum', 'count', 'average']),
    # Rankings
    any(word in query for word in ['top', 'top-', 'highest', 'most', 'best']),
    # Calculations
    any(word in query for word in ['savings', 'save', 'dollar', 'cost'])
])
```

CHANGES MADE:
- app/ui/client.py: Lines 365-425 (context preservation)
- app/ui/client.py: Lines 881-895 (enhanced routing detection)
- app/ui/client.py: Lines 984-1191 (enhanced aggregation method)
  - Added time aggregation
  - Added Top-N ranking with number extraction
  - Added savings calculation with formula
  - Improved de-duplication logic

CONVERSATION SUPPORT:

**Supported Follow-up Patterns:**
- ✅ "total time on these tasks" → aggregation
- ✅ "top 10 occupations by X" → ranking
- ✅ "dollar savings" or "cost savings" → calculation
- ✅ "how many X" → counting
- ✅ "average Y" → mean calculation
- ✅ "the above tasks/results" → context reference
- ✅ General questions → LLM reasoning

**Data Preservation:**
Filtered dataset preserves ALL columns:
- Task descriptions
- Occupation names
- Time per week
- Employment (thousands)
- Hourly wage
- Industry information

IMPACT:
Before v4.9.3:
- Follow-up "about above/these tasks" → wrong data ❌
- "Total time" → not supported ❌
- "Top 10 by time" → not supported ❌
- "Dollar savings" → not supported ❌
- User frustration: Limited conversation capabilities ❌

After v4.9.3:
- Follow-up "about above/these tasks" → correct data ✅
- "Total time" → calculated accurately ✅
- "Top 10 by time" → ranked results ✅
- "Dollar savings" → full calculation with assumptions ✅
- User satisfaction: Natural conversational flow ✅

BACKWARD COMPATIBILITY:
- ✅ All existing queries work the same
- ✅ Enhanced capabilities for follow-ups
- ✅ Better UX for conversational queries
- ✅ Maintains accuracy while adding features

USER VALUE:
- Natural multi-turn conversations
- Complex calculations without leaving interface
- Contextual continuity (above/these references)
- Professional analysis capabilities
- Business value calculations (ROI, savings)

Previous Versions:
- v4.9.2: Employment query fix
- v4.9.1: Fatal NameError fix
- v4.9.0: Task routing fix
"""

__version__ = "4.9.3"
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
