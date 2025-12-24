"""
Prompt templates for LLM interaction
"""
from typing import Dict, List, Any


class PromptTemplates:
    """Prompt templates for different query types"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """Get system prompt for labor market analyst"""
        return """You are a Labor Market Data Analyst assistant specialized in analyzing ONET labor market data.

Your role is to:
1. Provide accurate, data-grounded insights about occupations, industries, tasks, and employment
2. Clearly distinguish between information directly from the dataset and any external knowledge
3. Present findings clearly with appropriate structure (tables, bullets, or prose as needed)
4. Cite specific data points when making claims
5. Be transparent about limitations and data gaps

AVAILABLE DATA FIELDS:
The dataset has been enriched with a comprehensive labor market data dictionary that includes:
- Industry_Canonical: Standardized industry names (NAICS-based)
- Extracted_Skills: Skills automatically extracted from job task descriptions
- Skill_Count: Number of distinct skills identified for each occupation
- Canonical_Activities: Standardized work activity verbs
- Occupation_Major_Group: SOC-based occupation categories
- Wage_Band: Wage classifications (Entry/Mid/Senior/Executive Level)
- Task_Importance_Level: Task importance categories
- Required_Education: Typical education level required

DATASET STRUCTURE:
- Each row represents ONE TASK for an occupation
- To count tasks per occupation, count the number of rows for that occupation
- The "Task Count Analysis" section provides this information when available
- **EMPLOYMENT DATA**: The Employment column contains values at the TASK-INDUSTRY level
  - Each occupation appears in multiple industries with DIFFERENT employment values
  - Example: Architects in Professional Services (105k) vs Construction (5.4k) vs Retail (0.13k)
  - For total employment by occupation: use the maximum value across industries
  - For employment BY INDUSTRY: use the industry-specific value from that industry's rows
  - When asked for "by occupation AND industry", show EACH industry's specific employment value
  - DO NOT use the max/total value for all industries - this is incorrect!

IMPORTANT: When asked about employment or "total workers":
- Use the "EMPLOYMENT FOR MATCHING OCCUPATIONS" section if available
- Report the total_employment value clearly
- Note that employment values appear to be in thousands
- Example: If total_employment = 57.46, report as "approximately 57,460 workers" or "57.46 thousand workers"
- Always specify the number of occupations included in the total
- Do NOT sum employment at the task level - this produces incorrect results

CRITICAL: When asked for "TOTAL employment" or "What's the total":
- The user wants the AGGREGATED TOTAL across all occupations
- DO NOT show a breakdown by occupation or industry unless explicitly asked
- Format: "Total Employment: X thousand workers across Y occupations"
- Example: "Total Employment: 1,028.93 thousand workers (approximately 1.03 million) across 14 occupations"
- Only show breakdown if query specifically asks "by occupation" or "by industry"
- If query just asks for "total", give the single aggregated number

IMPORTANT: When asked "What jobs..." or "Which occupations..." questions:
- If you see "OCCUPATION PATTERN MATCHING ANALYSIS" in the context, list ALL occupations shown
- DO NOT just pick the first occupation - list at least the top 10-15 as ranked
- Format as a clear numbered list with percentages/counts from the analysis
- Include the matching task count and percentage for each occupation
- Provide examples when available

CRITICAL: Distinguish between OCCUPATION queries vs TASK queries:
- "What JOBS create documents?" → Show OCCUPATION LIST with employment and task counts
- "What TASKS create documents?" → Show TASK TABLE with descriptions and time

For OCCUPATION queries (What jobs/occupations):
- Format: List or table of OCCUPATIONS (not individual tasks)
- Include: Occupation name, Employment, Number of matching tasks, Example task (optional)
- DO NOT show individual task descriptions with time - that's for task queries
- Example format:
  1. Accountants and Auditors
     - Employment: 521.96 thousand workers
     - Matching tasks: 6 tasks involving document creation
     - Example: "Prepare detailed reports on audit findings"
  
  OR as table:
  | Occupation | Employment (k) | Matching Tasks | Example Task |
  | Accountants | 521.96 | 6 | Prepare audit reports |
  
For TASK queries (What tasks/specific tasks):
- Format: Table of TASKS with descriptions, occupation, time, industries
- Show 10-15+ individual task descriptions
- Include time per task and industry count
- Ensure diversity across occupations (5-10+)

For BREAKDOWN BY INDUSTRY AND OCCUPATION queries:
- This requires showing ALL occupation-industry combinations
- DO NOT show only one occupation (e.g., only Architects)
- Include ALL occupations present: Accountants, Engineers, Architects, Drafters, Managers, etc.
- **CRITICAL: If you see data with format "Industry: X, Occupation: Y, Employment: Z"**:
  * This is pre-computed breakdown data - USE IT DIRECTLY
  * DO NOT filter to one occupation
  * Show ALL combinations provided in the data
  * Each row in your table should match one data point
- For each Industry-Occupation pair, show:
  * Industry name
  * Occupation name
  * Employment in that specific industry-occupation combination
  * Percentage: (this combination's employment) / (total industry employment) * 100
- Show at least 20-30 rows covering major combinations
- Example:
  | Industry | Occupation | Employment (k) | % of Industry |
  | Professional Services | Accountants | 521.96 | 53.8% |
  | Finance | Accountants | 127.41 | 67.1% |
  | Manufacturing | Automotive Engineers | 121.95 | 33.0% |
  | Professional Services | Architects | 105.12 | 10.8% |
  | Government | Accountants | 126.27 | 56.1% |
  ... (continue with more combinations)
- Notice: Multiple occupations shown, not just one
- **DO NOT pick one occupation and show it across industries - show ALL occupation-industry pairs**

IMPORTANT: When asked about "specific tasks" or "what tasks" or "task descriptions":
- Look at the SEMANTIC SEARCH RESULTS section which contains actual task descriptions
- Each document in the semantic search results represents one task with its full description
- YOU MUST list the actual task text from the "Task Description:" field of EACH result
- Include metadata like occupation, industry, and any time/hour information available
- DO NOT just summarize at the occupation level - show the actual task descriptions verbatim
- DO NOT say "tasks are not explicitly listed" - they ARE in the semantic results!
- If the query asks about time spent, extract the time from the "⏱️ Time:" field
- Format as a numbered list with each task's description, occupation, and time
- Show AT LEAST 10-15 tasks if available in the results
- **CRITICAL: Ensure DIVERSITY across occupations - show tasks from at least 5-10 different occupations**
- **DO NOT show 10+ tasks all from the same occupation - spread them out**
- **CRITICAL: Only include tasks that ACTUALLY involve creating documents**
  - Task must contain action verbs: create, develop, design, prepare, write, produce
  - Task must contain document objects: document, report, spreadsheet, file, drawing, plan
  - If task only mentions "analyze", "review", "coordinate" without creating documents, EXCLUDE IT
  - Examples of VALID tasks: "Prepare reports", "Create drawings", "Develop plans", "Write documentation"
  - Examples of INVALID tasks: "Analyze processes", "Coordinate services", "Review proposals" (without creating)
  - When in doubt, check if the task explicitly states creating/producing something
- CRITICAL FOR TABLES: If asked for tabular format, include 10-15+ rows minimum, showing diverse tasks across different occupations (not just 2-3 rows from one occupation)
- Example format:
  1. "[Task description from semantic result]"
     - Occupation: [occupation from metadata]
     - Time: [hours from metadata]

CRITICAL: When asked for TABULAR format or TABLE:
- YOU MUST SHOW AT LEAST 10-15 ROWS in the table (not just 2-3)
- Each row should be a UNIQUE task-occupation pair
- **CRITICAL: Show tasks from AT LEAST 5-10 DIFFERENT OCCUPATIONS**
- **DO NOT show more than 2-3 tasks from the same occupation**
- This ensures diversity and comprehensive coverage
- DO NOT show every industry separately if the task and occupation are the same
- AGGREGATE by task description and occupation
- Calculate AVERAGE time across all industries for that task-occupation pair
- **CRITICAL: Each row should have DIFFERENT time and industry count values**
- **DO NOT use the same value (e.g., 2.5 hrs or 10 industries) for all rows**
- Calculate SEPARATELY for each task-occupation pair from the semantic results
- For the "Industries" or "Industry Count" column:
  * Option 1: Show COUNT as a number: "7 industries" or just "7"
  * Option 2: Show NAMES if few: "Finance, Manufacturing, Retail"
  * DO NOT list all industry names in quotes - this breaks the table format
  * Count how many DIFFERENT industries this specific task-occupation appears in
- Example correct format:
  | Task | Occupation | Avg Time (hrs/week) | Industries |
  | "Prepare reports..." | Accountants | 3.0 | 20 |
  | "Design drawings..." | Drafters | 4.0 | 15 |
  | "Analyze data..." | Actuaries | 4.0 | 9 |
  | "Write specifications..." | Engineers | 2.5 | 8 |
  | "Create plans..." | Architects | 1.5 | 15 |
  | "Review documents..." | Managers | 5.0 | 7 |
- Notice: Each row has DIFFERENT time values and DIFFERENT industry counts
- **DO NOT calculate one average for all rows - calculate separately for each!**
- Remember: MINIMUM 10-15 rows showing diverse tasks and occupations
- This prevents unnecessary repetition and makes tables concise and readable

CRITICAL: When asked for "by occupation AND industry" or "by industry and occupation":
- DO NOT aggregate to occupation level - show INDUSTRY-SPECIFIC values
- Each occupation-industry pair should have its OWN employment value
- DO NOT repeat the same value for all industries of an occupation
- Example WRONG: Architects | All Industries | 105.12 (repeated)
- Example CORRECT: 
  * Architects | Professional Services | 105.12
  * Architects | Wholesale Trade | 9.09
  * Architects | Construction | 5.41
- The employment values should be DIFFERENT for each industry
- Extract industry-specific employment from the semantic search metadata
- Look at the "Industry" and "Employment" fields in each result

IMPORTANT: When asked about "what industries" or "which industries" with proportion/percentage:
- This is an INDUSTRY-LEVEL analysis, not a task-level listing
- DO NOT show individual task descriptions
- DO NOT list tasks from one occupation across industries
- INSTEAD: Show a ranked table of INDUSTRIES
- Calculate: (workers with attribute in industry) / (total workers in industry)
- Rank industries by this proportion/percentage
- Format as:
  | Industry | Workers with Attribute | Total Workers | Percentage |
  | Professional Services | 389.7k | 582.4k | 66.9% |
- Focus on INDUSTRY as the unit of analysis, not tasks or occupations
- If computational results not available, explain that proportion calculation requires aggregation

IMPORTANT: When asked about skills or skill diversity:
- Use the Skill_Count field to identify occupations with diverse skill sets
- Reference the Extracted_Skills field for specific skill requirements
- The skill data comes from automated analysis of task descriptions using a labor market ontology

IMPORTANT: When asked about task counts or which occupations have the most tasks:
- Use the task_analysis section which counts rows (tasks) per occupation
- Each row is a task, so counting rows per occupation gives task counts
- The data IS available through the task count analysis

CRITICAL RULES:
- Base all answers strictly on the provided data
- If you use ANY external knowledge or make inferences, EXPLICITLY label them in a separate "External / Inferred Data" section
- Never hallucinate statistics or facts not in the data
- If data is insufficient, clearly state what's missing
- When presenting numbers, always cite the source (e.g., "Based on Employment field..." or "Based on Skill_Count field...")
- For skill-related queries, ALWAYS check if Skill_Count or Extracted_Skills data is provided
- IMPORTANT FOR TABLES: The dataset is at TASK-INDUSTRY level (each task appears once per industry)
  - When creating tables, AGGREGATE duplicate task-occupation pairs across industries
  - Show: Task | Occupation | Avg Time | Industry Count (or list)
  - DO NOT show the same task-occupation multiple times with different industries
  - Calculate average time across industries for that task-occupation pair
  - This prevents repetitive tables and makes data more readable
- CRITICAL FOR PROPORTION/RANKING QUERIES: When asked "which industries have high proportion" or "industries rich in X"
  - This requires COMPUTATIONAL analysis at the INDUSTRY level
  - DO NOT just list tasks from semantic search
  - If computational analysis not provided, explain that proportion calculation requires aggregation
  - Request: "To calculate industry proportions, I need aggregated employment data by industry"
- CRITICAL FOR TOTAL EMPLOYMENT QUERIES: When query asks "What's the total" or "total employment"
  - Give the SINGLE AGGREGATED NUMBER from "TOTAL EMPLOYMENT (AGGREGATED)"
  - DO NOT show occupation breakdown or industry breakdown unless explicitly requested
  - DO NOT create a table unless query specifically asks for breakdown "by occupation" or "by industry"
  - Format: "Total Employment: X thousand workers (approximately Y million) across Z occupations"
  - The occupation/industry breakdown is OPTIONAL - only show if user asks for it
  - EXCEPTION: If query says "total employment" BUT ALSO asks for "breakdown", "by industry and occupation", or "tabular format":
    * User wants BOTH the total AND detailed breakdown
    * Show total first, then comprehensive table
    * Include ALL occupations (not just one)
    * Calculate percentages: (occupation employment in industry) / (total industry employment) * 100
    * Show at least 20-30 rows covering major combinations

Your responses should be:
- Accurate and grounded in data
- Clear and well-structured
- Appropriately detailed
- Honest about uncertainties"""
    
    @staticmethod
    def format_retrieval_context(
        semantic_results: List[Dict[str, Any]],
        computational_results: Dict[str, Any]
    ) -> str:
        """Format retrieved context for LLM"""
        
        context_parts = []
        
        # Add semantic search results
        if semantic_results:
            context_parts.append("=== SEMANTIC SEARCH RESULTS ===")
            context_parts.append("⚠️ IMPORTANT: Each result below represents ONE TASK from the dataset")
            context_parts.append("For task queries, LIST ALL these task descriptions in your response!")
            context_parts.append("⚠️ VALIDATION: For 'create digital documents' queries, only include tasks that:")
            context_parts.append("   - Contain action verbs: create, develop, design, prepare, write, produce")
            context_parts.append("   - Contain document objects: document, report, spreadsheet, file, drawing, plan")
            context_parts.append("   - If task only mentions analyze/review/coordinate without creating, EXCLUDE IT")
            context_parts.append("📊 NOTE: The data is at TASK-INDUSTRY level, so the same task may appear")
            context_parts.append("    multiple times for different industries. For tables, AGGREGATE by task-occupation.")
            context_parts.append("💼 EMPLOYMENT: Each result has industry-specific employment values.")
            context_parts.append("    For 'by industry' queries, use these specific values (not aggregated max).")
            context_parts.append(f"🎯 FOR TABLES: Create at least 10-15 rows using these {len(semantic_results)} results below.")
            context_parts.append("🌟 DIVERSITY: Show tasks from AT LEAST 5-10 DIFFERENT occupations (not all from one).")
            context_parts.append("⏱️ TIME VALUES: Each result has its own ⏱️ Time value. When aggregating:")
            context_parts.append("   - Group results by task description + occupation")
            context_parts.append("   - Calculate AVERAGE time for that task-occupation pair")
            context_parts.append("   - Count DISTINCT industries for that task-occupation pair")
            context_parts.append("   - Result: Each table row has DIFFERENT time and industry count")
            context_parts.append("   - DO NOT use same value (e.g., 2.5 hrs or 10 industries) for all rows\n")
            
            for i, result in enumerate(semantic_results[:30], 1):  # Show up to 30 tasks for diversity
                score = result.get('score', 0)
                text = result.get('text', '')[:500]  # Truncate long texts
                metadata = result.get('metadata', {})
                
                context_parts.append(f"\n[TASK {i}] (Relevance: {score:.2f})")
                if metadata.get('onet_job_title'):
                    context_parts.append(f"Occupation: {metadata['onet_job_title']}")
                if metadata.get('industry_title'):
                    context_parts.append(f"Industry: {metadata['industry_title']}")
                
                # Highlight time/hours information for task queries
                if metadata.get('hours_per_week_spent_on_task'):
                    try:
                        hours = float(metadata['hours_per_week_spent_on_task'])
                        context_parts.append(f"⏱️ Time: {hours:.1f} hours per week")
                    except (ValueError, TypeError):
                        pass
                
                # Show employment for industry-level queries
                if metadata.get('employment'):
                    try:
                        emp = float(metadata['employment'])
                        context_parts.append(f"💼 Employment: {emp:.2f} thousand workers (industry-specific)")
                    except (ValueError, TypeError):
                        pass
                
                # Add enriched fields if available
                if metadata.get('industry_canonical'):
                    context_parts.append(f"Canonical Industry: {metadata['industry_canonical']}")
                if metadata.get('occupation_major_group'):
                    context_parts.append(f"Occupation Group: {metadata['occupation_major_group']}")
                if metadata.get('skill_count'):
                    context_parts.append(f"Skill Count: {metadata['skill_count']} distinct skills")
                if metadata.get('extracted_skills'):
                    context_parts.append(f"Identified Skills: {metadata['extracted_skills']}")
                if metadata.get('wage_band'):
                    context_parts.append(f"Wage Band: {metadata['wage_band']}")
                
                context_parts.append(f"📋 Task Description: {text}\n")
        
        # Add computational results
        if computational_results:
            context_parts.append("\n=== COMPUTATIONAL ANALYSIS ===\n")
            
            # Counts
            if 'counts' in computational_results:
                context_parts.append("\nCounts:")
                for key, value in computational_results['counts'].items():
                    try:
                        # Format as integer with commas
                        if isinstance(value, (int, float)):
                            context_parts.append(f"- {key}: {int(value):,}")
                        else:
                            context_parts.append(f"- {key}: {int(float(value)):,}")
                    except (ValueError, TypeError):
                        # If can't convert to int, show as-is
                        context_parts.append(f"- {key}: {value}")
            
            # Totals
            if 'totals' in computational_results:
                context_parts.append("\nTotals:")
                for key, value in computational_results['totals'].items():
                    # Skip non-numeric metadata fields
                    if key in ['employment_note', 'warning', 'error']:
                        continue
                    
                    # Try to format as number, skip if not numeric
                    try:
                        if isinstance(value, (int, float)):
                            context_parts.append(f"- {key}: {float(value):,.2f}")
                        elif isinstance(value, str):
                            # Skip string values - they're metadata
                            continue
                        else:
                            # Try to convert to float
                            context_parts.append(f"- {key}: {float(value):,.2f}")
                    except (ValueError, TypeError):
                        # If conversion fails, skip this value
                        logger.warning(f"Could not format total value for {key}: {value}", show_ui=False)
                        continue
            
            # Averages
            if 'averages' in computational_results:
                context_parts.append("\nAverages:")
                for key, value in computational_results['averages'].items():
                    try:
                        if isinstance(value, (int, float)):
                            context_parts.append(f"- {key}: {float(value):,.2f}")
                        else:
                            context_parts.append(f"- {key}: {float(value):,.2f}")
                    except (ValueError, TypeError):
                        logger.warning(f"Could not format average value for {key}: {value}", show_ui=False)
                        context_parts.append(f"- {key}: {value}")
            
            # Grouped results
            if 'grouped' in computational_results:
                context_parts.append("\nGrouped Analysis:")
                for group_type, values in computational_results['grouped'].items():
                    context_parts.append(f"\n{group_type}:")
                    for name, val in list(values.items())[:10]:  # Top 10
                        context_parts.append(f"  - {name}: {val:,.2f}")
            
            # Top N
            if 'top_n' in computational_results:
                context_parts.append("\nTop Results:")
                for key, values in computational_results['top_n'].items():
                    context_parts.append(f"\n{key}:")
                    for name, val in values.items():
                        context_parts.append(f"  - {name}: {val:,.2f}")
            
            # Industry Proportions (for "rich in X" / "high proportion" queries)
            if 'industry_proportions' in computational_results:
                prop_data = computational_results['industry_proportions']
                
                context_parts.append("\n=== INDUSTRY PROPORTION ANALYSIS ===")
                context_parts.append(f"📊 Analysis: Which industries have the highest proportion of {prop_data.get('attribute_name', 'matching workers')}")
                context_parts.append(f"\nTotal industries analyzed: {prop_data.get('total_industries', 0)}")
                context_parts.append(f"Industries with matches: {prop_data.get('industries_with_matches', 0)}")
                
                context_parts.append("\n🏆 INDUSTRIES RANKED BY PROPORTION:")
                context_parts.append("(Showing percentage of industry workforce with this attribute)\n")
                
                industry_list = prop_data.get('industry_proportions', [])
                
                # Show top 15 industries
                for i, industry_info in enumerate(industry_list[:15], 1):
                    industry = industry_info.get('industry', 'Unknown')
                    matching = industry_info.get('matching_employment', 0)
                    total = industry_info.get('total_employment', 0)
                    proportion = industry_info.get('proportion', 0)
                    
                    context_parts.append(
                        f"{i}. {industry}"
                    )
                    context_parts.append(
                        f"   - Matching workers: {matching:,.2f} thousand"
                    )
                    context_parts.append(
                        f"   - Total industry employment: {total:,.2f} thousand"
                    )
                    context_parts.append(
                        f"   - Proportion: {proportion:.1f}%"
                    )
                
                context_parts.append("\n⚠️ IMPORTANT FOR YOUR RESPONSE:")
                context_parts.append("- Present this as a RANKED TABLE of industries")
                context_parts.append("- Show: Industry | Matching Workers | Total Workers | Percentage")
                context_parts.append("- Order by percentage (highest to lowest)")
                context_parts.append("- Include at least top 10 industries")
                context_parts.append("- DO NOT show individual task descriptions")
                context_parts.append("- This is INDUSTRY-LEVEL analysis, not task-level")
            
            # Skill Analysis (from data dictionary enrichment)
            if 'skill_analysis' in computational_results:
                context_parts.append("\n=== SKILL DIVERSITY ANALYSIS (from Data Dictionary) ===")
                skill_data = computational_results['skill_analysis']
                
                context_parts.append(f"\nOverall Statistics:")
                context_parts.append(f"- Total occupations analyzed: {int(skill_data.get('total_occupations', 0)):,}")
                context_parts.append(f"- Occupations with identified skills: {int(skill_data.get('occupations_with_skills', 0)):,}")
                
                # Defensive float formatting
                try:
                    avg_skills = float(skill_data.get('avg_skills_per_occupation', 0))
                    context_parts.append(f"- Average skills per occupation: {avg_skills:.1f}")
                except (ValueError, TypeError):
                    context_parts.append(f"- Average skills per occupation: 0.0")
                
                try:
                    max_skills = float(skill_data.get('max_skills_in_occupation', 0))
                    context_parts.append(f"- Maximum skills in any occupation: {max_skills:.0f}")
                except (ValueError, TypeError):
                    context_parts.append(f"- Maximum skills in any occupation: 0")
                
                if 'top_diverse_occupations' in skill_data:
                    context_parts.append(f"\nTop 20 Occupations by Skill Diversity (based on Skill_Count):")
                    for occupation, skill_count in list(skill_data['top_diverse_occupations'].items())[:20]:
                        try:
                            count_val = float(skill_count) if skill_count is not None else 0.0
                            context_parts.append(f"  - {occupation}: {count_val:.0f} distinct skills")
                        except (ValueError, TypeError):
                            context_parts.append(f"  - {occupation}: {skill_count} distinct skills")
                
                if 'industries_by_avg_skills' in skill_data:
                    context_parts.append(f"\nIndustries by Average Skill Requirements:")
                    for industry, avg_skills in list(skill_data['industries_by_avg_skills'].items())[:10]:
                        try:
                            avg_val = float(avg_skills) if avg_skills is not None else 0.0
                            context_parts.append(f"  - {industry}: {avg_val:.1f} avg skills")
                        except (ValueError, TypeError):
                            context_parts.append(f"  - {industry}: {avg_skills} avg skills")
            
            # Task Analysis (task counts per occupation)
            if 'task_analysis' in computational_results:
                context_parts.append("\n=== TASK COUNT ANALYSIS ===")
                task_data = computational_results['task_analysis']
                
                context_parts.append(f"\nDataset Structure:")
                
                # Defensive formatting for all numeric values
                try:
                    total_tasks = int(task_data.get('total_tasks', 0))
                    context_parts.append(f"- Total tasks in dataset: {total_tasks:,}")
                except (ValueError, TypeError):
                    context_parts.append(f"- Total tasks in dataset: 0")
                
                try:
                    total_occs = int(task_data.get('total_occupations', 0))
                    context_parts.append(f"- Total occupations: {total_occs:,}")
                except (ValueError, TypeError):
                    context_parts.append(f"- Total occupations: 0")
                
                try:
                    avg_tasks = float(task_data.get('avg_tasks_per_occupation', 0))
                    context_parts.append(f"- Average tasks per occupation: {avg_tasks:.1f}")
                except (ValueError, TypeError):
                    context_parts.append(f"- Average tasks per occupation: 0.0")
                
                try:
                    max_tasks = int(task_data.get('max_tasks_for_occupation', 0))
                    context_parts.append(f"- Maximum tasks for any occupation: {max_tasks:,}")
                except (ValueError, TypeError):
                    context_parts.append(f"- Maximum tasks for any occupation: 0")
                
                try:
                    min_tasks = int(task_data.get('min_tasks_for_occupation', 0))
                    context_parts.append(f"- Minimum tasks for any occupation: {min_tasks:,}")
                except (ValueError, TypeError):
                    context_parts.append(f"- Minimum tasks for any occupation: 0")
                
                context_parts.append(f"\nNOTE: Each row in the dataset represents one task. The number of tasks per occupation")
                context_parts.append(f"is determined by counting how many rows (tasks) belong to each occupation.")
                
                if 'top_occupations_by_task_count' in task_data:
                    context_parts.append(f"\nTop 20 Occupations by Number of Tasks:")
                    for occupation, task_count in list(task_data['top_occupations_by_task_count'].items())[:20]:
                        try:
                            count = int(task_count)
                            context_parts.append(f"  - {occupation}: {count:,} tasks")
                        except (ValueError, TypeError):
                            context_parts.append(f"  - {occupation}: {task_count} tasks")
                
                if 'top_industries_by_task_count' in task_data:
                    context_parts.append(f"\nTop Industries by Total Task Count:")
                    for industry, task_count in list(task_data['top_industries_by_task_count'].items())[:10]:
                        try:
                            count = int(task_count)
                            context_parts.append(f"  - {industry}: {count:,} tasks")
                        except (ValueError, TypeError):
                            context_parts.append(f"  - {industry}: {task_count} tasks")
            
            # Occupation Pattern Analysis (for "what jobs" queries)
            if 'occupation_pattern_analysis' in computational_results:
                context_parts.append("\n=== OCCUPATION PATTERN MATCHING ANALYSIS ===")
                pattern_data = computational_results['occupation_pattern_analysis']
                
                context_parts.append(f"\nQuery Pattern Analysis:")
                context_parts.append(f"- Total occupations analyzed: {pattern_data.get('total_occupations_analyzed', 0)}")
                context_parts.append(f"- Occupations with matching tasks: {pattern_data.get('occupations_with_matches', 0)}")
                context_parts.append(f"- Match criteria: Contains action verbs AND object keywords")
                
                context_parts.append(f"\nAction verbs searched: {', '.join(pattern_data.get('action_verbs_used', [])[:8])}...")
                context_parts.append(f"Object keywords searched: {', '.join(pattern_data.get('object_keywords_used', [])[:8])}...")
                
                if 'top_occupations' in pattern_data:
                    context_parts.append(f"\nTOP OCCUPATIONS RANKED BY MATCHING TASKS:")
                    context_parts.append(f"(Showing occupations where tasks match the pattern)")
                    context_parts.append(f"")
                    
                    for rank, (occupation, scores) in enumerate(pattern_data['top_occupations'], 1):
                        context_parts.append(
                            f"{rank}. {occupation}"
                        )
                        context_parts.append(
                            f"   - Matching tasks: {scores['matching_tasks']}/{scores['total_tasks']} "
                            f"({scores['percentage']:.1f}%)"
                        )
                        if scores.get('examples'):
                            context_parts.append(f"   - Example tasks:")
                            for example in scores['examples'][:2]:
                                context_parts.append(f"      • {example}")
                    
                    context_parts.append(f"\nIMPORTANT: List ALL {len(pattern_data['top_occupations'])} occupations shown above, ")
                    context_parts.append(f"not just the first one. These are ranked by the percentage of matching tasks.")
            
            # Employment for Matching Occupations
            if 'employment_for_matching_occupations' in computational_results:
                context_parts.append("\n=== EMPLOYMENT FOR MATCHING OCCUPATIONS ===")
                emp_data = computational_results['employment_for_matching_occupations']
                
                # Defensive conversion to ensure all values are floats
                try:
                    total_emp = float(emp_data['total_employment']) if emp_data.get('total_employment') else 0.0
                    occ_count = int(emp_data.get('occupations_count', 0))
                    
                    context_parts.append(f"\n⭐ TOTAL EMPLOYMENT (AGGREGATED): {total_emp:.2f} thousand workers")
                    context_parts.append(f"   Equivalent to: {total_emp * 1000:,.0f} workers")
                    context_parts.append(f"   Across {occ_count} occupations")
                    context_parts.append(f"\n📌 NOTE: Use this TOTAL value when asked for 'total employment'")
                    context_parts.append(f"   DO NOT show the occupation breakdown unless specifically requested")
                    context_parts.append(f"\nNote: {emp_data.get('note', '')}")
                    
                    # Employment by occupation with defensive float conversion
                    per_occ = emp_data.get('per_occupation', {})
                    if per_occ:
                        context_parts.append(f"\n[OPTIONAL BREAKDOWN - Only show if query asks 'by occupation':]")
                        context_parts.append(f"Employment by Occupation:")
                        
                        # Convert all values to float defensively
                        per_occ_floats = {}
                        for occ, emp in per_occ.items():
                            try:
                                per_occ_floats[occ] = float(emp) if emp is not None else 0.0
                            except (ValueError, TypeError) as e:
                                logger.warning(f"Could not convert employment to float for {occ}: {emp}", show_ui=False)
                                per_occ_floats[occ] = 0.0
                        
                        # Sort by employment
                        sorted_occs = sorted(per_occ_floats.items(), key=lambda x: x[1], reverse=True)
                        for occ, emp in sorted_occs:
                            context_parts.append(f"  - {occ}: {emp:.2f}")
                        
                        context_parts.append(f"\nIMPORTANT: The total employment figure ({total_emp:.2f}) ")
                        context_parts.append(f"represents the sum of employment across {occ_count} occupations.")
                        context_parts.append(f"Each occupation's employment is counted once (not per task).")
                except (ValueError, TypeError, KeyError) as e:
                    logger.error(f"Error formatting employment data: {str(e)}", show_ui=False)
                    context_parts.append(f"\n[Error formatting employment data - check logs]")
        
        return '\n'.join(context_parts)
    
    @staticmethod
    def create_analysis_prompt(
        query: str,
        context: str,
        routing_info: Dict[str, Any]
    ) -> str:
        """Create complete analysis prompt"""
        
        intent = routing_info.get('intent', 'hybrid')
        
        prompt = f"""Based on the labor market data provided below, answer the following question:

QUESTION: {query}

QUERY TYPE: {intent.upper()}

DATA CONTEXT:
{context}

INSTRUCTIONS:
1. Answer the question using ONLY the data provided above
2. Be specific and cite relevant statistics
3. If you need to make inferences or use external knowledge, create a separate section labeled "External / Inferred Data"
4. If the data is insufficient to fully answer the question, clearly state what information is missing
5. Present your answer in a clear, structured format
6. Include tables or lists if they help clarity

ANSWER:"""
        
        return prompt
    
    @staticmethod
    def create_csv_generation_prompt(
        query: str,
        data_summary: str
    ) -> str:
        """Create prompt for CSV data generation"""
        
        return f"""Based on the query and data summary below, generate a structured dataset that can be exported to CSV.

QUERY: {query}

DATA SUMMARY:
{data_summary}

INSTRUCTIONS:
1. Identify the key dimensions and metrics requested
2. Structure the data in a tabular format with clear column headers
3. Provide actual data points from the analysis
4. Format numbers appropriately
5. Return ONLY the data in a format that can be parsed into CSV

Respond with a structured table format."""
    
    @staticmethod
    def create_digital_documents_prompt() -> str:
        """Specialized prompt for digital document queries"""
        
        return """Based on the labor market data, analyze which jobs involve creating digital documents.

DEFINITION: Digital document creation includes:
- Spreadsheets (Excel, Google Sheets)
- Word processing documents (Word, Google Docs)
- PDFs and formatted documents
- Photo and image creation/editing
- Video creation and editing
- Computer programs and code
- Presentations
- Any content created using a computer

EXCLUDE: Jobs that only READ or VIEW digital documents (e.g., order takers who just read forms)

Analyze:
1. Which occupations require digital document creation?
2. What specific tasks involve creating digital documents?
3. What is the total employment in these occupations?
4. How much time per week is spent on digital document tasks?
5. Which industries have high concentrations of digital document creators?

Provide specific data points and statistics."""
    
    @staticmethod
    def create_ai_agent_analysis_prompt() -> str:
        """Specialized prompt for AI agent solution analysis"""
        
        return """Analyze the potential impact of a customer service AI agent based on the labor market data.

AI AGENT CAPABILITIES:
- Automate customer interactions
- Deliver personalized experiences
- Understand customer needs
- Answer questions
- Resolve issues
- Recommend products and services
- Work across web, mobile, and point-of-sale
- Integrate with voice and video

Analyze:
1. Which occupations could benefit from this agent?
2. What specific tasks could the agent help with?
3. How much time per week is currently spent on these tasks?
4. What time savings could be achieved?
5. Which occupations could save the most time?
6. What is the potential dollar value of time savings?
7. What recommendations would encourage adoption?

Provide detailed analysis with specific numbers and calculations."""
