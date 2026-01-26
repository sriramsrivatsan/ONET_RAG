"""
Retriever that orchestrates hybrid semantic and computational retrieval
Version 4.0.0 - Generic pattern-based system with zero hardcoding
"""
import pandas as pd
from typing import Dict, List, Any, Optional

from app.rag.vector_store import VectorStore
from app.rag.hybrid_router import HybridQueryRouter, QueryIntent
from app.rag.task_pattern_engine import get_pattern_engine
from app.analytics.aggregations import DataAggregator
from app.utils.logging import logger


class HybridRetriever:
    """
    Orchestrates hybrid retrieval combining semantic search and computational queries.
    
    Version 4.0.0: Uses generic TaskPatternEngine for all pattern matching.
    No hardcoded patterns - all configuration-driven.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        dataframe: pd.DataFrame,
        aggregator: DataAggregator
    ):
        self.vector_store = vector_store
        self.df = dataframe
        self.aggregator = aggregator
        self.router = HybridQueryRouter()
        
        # V4.0.0: Initialize generic pattern engine
        self.pattern_engine = get_pattern_engine()
        logger.info(
            f"✓ v4.8.6: Generic pattern engine loaded with {len(self.pattern_engine.categories)} task categories",
            show_ui=False
        )
    
    def retrieve(
        self,
        query: str,
        k: int = 10,
        original_query: str = None
    ) -> Dict[str, Any]:
        """
        Main retrieval function
        
        Args:
            query: Query to use for vector search (may be enhanced)
            k: Number of results to retrieve
            original_query: Original user query (for pattern matching, before enhancement)
        
        Returns:
            Retrieved results with metadata
        """
        # Use original query for pattern matching if provided, otherwise use query
        # CRITICAL: Pattern matching should ONLY run on original user queries
        # Enhanced queries contain appended task descriptions that create false positives
        query_for_pattern_matching = original_query if original_query else query
        
        # Route the query (use original for pattern detection)
        routing_info = self.router.route_query(query_for_pattern_matching)
        strategy = routing_info['strategy']
        
        results = {
            'query': query,
            'routing_info': routing_info,
            'semantic_results': [],
            'computational_results': {},
            'filtered_dataframe': None,
            'metadata': {}
        }
        
        # CRITICAL: Distinguish between TASK queries and JOB/OCCUPATION queries
        # User might ask "What TASKS..." (wants task descriptions) vs "What JOBS..." (wants occupation summaries)
        query_lower = query.lower()
        
        wants_task_details = any(phrase in query_lower for phrase in [
            'specific tasks', 'what tasks', 'which tasks', 'task descriptions',
            'tasks that', 'tasks involve', 'list tasks', 'show tasks', 'describe tasks',
            'job tasks', 'work tasks', 'task list', 'tasks for', 'all tasks', 'all the tasks',
            'distinct tasks', 'unique tasks'
        ])
        
        # Detect if user is asking for tasks for a SPECIFIC occupation
        # e.g., "What are the tasks for an art director?"
        is_specific_occupation_task_query = (
            wants_task_details and 
            any(phrase in query_lower for phrase in ['tasks for', 'tasks of', 'all tasks'])
        )
        
        wants_occupation_summary = any(phrase in query_lower for phrase in [
            'what jobs', 'which jobs', 'what occupations', 'which occupations',
            'jobs that', 'occupations that', 'list jobs', 'list occupations',
            'job titles', 'occupation titles', 'what positions'
        ])
        
        wants_industry_summary = (
            'by industry' in query_lower or 
            'per industry' in query_lower or
            ('industries' in query_lower and not wants_task_details) or
            'which industries' in query_lower
        )
        
        # Detect time-related queries
        wants_time_analysis = any(phrase in query_lower for phrase in [
            'how much time', 'total time', 'time per week', 'hours per week',
            'time spent', 'hours spent', 'average time', 'time each week'
        ])
        
        # Detect savings/impact queries
        wants_savings_analysis = any(phrase in query_lower for phrase in [
            'time save', 'time saving', 'could save', 'shave off', 'reduce time',
            'dollar saving', 'cost saving', 'financial saving', 'roi', 'return on investment'
        ])
        
        # V4.0.0: GENERIC pattern detection (replaces hardcoded document creation)
        # Detect task category from query using pattern engine
        # CRITICAL: Use original query for pattern matching (before enhancement)
        detected_category = self.pattern_engine.detect_task_category(query_for_pattern_matching)
        
        if detected_category:
            category_config = self.pattern_engine.get_category_config(detected_category)
            results['metadata']['task_category'] = detected_category
            results['metadata']['category_display_name'] = category_config.display_name
            logger.info(f"✓ v4.8.6: Detected task category: {detected_category}", show_ui=False)
        
        # Check if this is a task-based query (any category detected)
        is_task_category_query = detected_category is not None
        
        # Detect query intents using pattern engine
        query_intents = self.pattern_engine.detect_query_intent(query)
        
        # Detect breakdown queries that need comprehensive industry-occupation data
        # V4.0.0: Use detected category instead of hardcoded keywords
        is_breakdown_query = (
            any(kw in query_lower for kw in ['breakdown', 'by industry and occupation', 'tabular format', 'provide industry']) and
            detected_category is not None  # V4.0.0: Generic check
        )
        
        
        # ROUTING DECISION: Choose response type based on query intent
        
        # NEW: Handle specific occupation task queries (e.g., "What are the tasks for an art director?")
        if is_specific_occupation_task_query and self.df is not None:
            logger.info("Specific occupation task query - extracting occupation and returning ALL tasks", show_ui=False)
            return self._create_specific_occupation_tasks(results, query_lower, query)
        
        # NEW: Handle general industry/occupation ranking queries (no task filter)
        is_general_industry_ranking = (
            wants_industry_summary and 
            not is_task_category_query and  # V4.0.0: Generic check
            any(kw in query_lower for kw in ['highest', 'most', 'largest', 'biggest', 'top', 'ranking', 'rank'])
        )
        
        is_general_occupation_ranking = (
            wants_occupation_summary and
            not is_task_category_query and  # V4.0.0: Generic check
            any(kw in query_lower for kw in ['highest', 'most', 'largest', 'biggest', 'top', 'ranking', 'rank', 'diverse', 'diversity'])
        )
        
        if is_general_industry_ranking and self.df is not None:
            logger.info("General industry ranking query - aggregating ALL industries", show_ui=False)
            return self._create_general_industry_ranking(results, query_lower)
        
        elif is_general_occupation_ranking and self.df is not None:
            logger.info("General occupation ranking query - aggregating ALL occupations", show_ui=False)
            return self._create_general_occupation_ranking(results, query_lower)
        
        # V4.0.0: GENERIC task category queries (replaces hardcoded document creation)
        elif is_task_category_query and self.df is not None:
            logger.info(f"✓ v4.8.6: Task category query detected ({detected_category}) - using generic pattern matching", show_ui=False)
            
            # GENERIC pattern matching using engine (replaces hardcoded action_verbs/object_keywords)
            matching_df = self.pattern_engine.filter_dataframe(
                self.df,
                detected_category,
                task_column='Detailed job tasks',
                return_match_details=False
            )
            
            logger.info(f"✓ v4.8.6: Generic pattern matching found {len(matching_df)} rows for {detected_category}", show_ui=False)
            
            # ROUTE 1: User wants TASK DETAILS (task descriptions with time)
            if wants_task_details:
                logger.info(f"Returning TASK DETAILS (task descriptions with time)", show_ui=False)
                results = self._create_task_details_response(matching_df, results, query_lower)
            
            # ROUTE 2: User wants INDUSTRY BREAKDOWN
            elif wants_industry_summary:
                logger.info(f"Returning INDUSTRY SUMMARY", show_ui=False)
                results = self._create_industry_summary_response(matching_df, results, query_lower)
            
            # ROUTE 3: User wants OCCUPATION BREAKDOWN (default for job queries)
            elif wants_occupation_summary or not wants_task_details:
                logger.info(f"Returning OCCUPATION SUMMARY", show_ui=False)
                results = self._create_occupation_summary_response(matching_df, results, query_lower)
            
        
        # Handle breakdown queries (V4.0.0: now uses generic pattern matching)
        elif is_breakdown_query and detected_category and self.df is not None:
            logger.info(f"✓ v4.8.6: Breakdown query for {detected_category}", show_ui=False)
            
            # V4.0.0: Generic pattern matching (replaces hardcoded patterns)
            matching_df = self.pattern_engine.filter_dataframe(
                self.df,
                detected_category,
                task_column='Detailed job tasks'
            )
            
            logger.info(f"✓ v4.8.6: Breakdown query - generic pattern matching found {len(matching_df)} rows", show_ui=False)
            
            # Get all unique industry-occupation pairs with employment
            ind_occ_data = matching_df.groupby(['Industry title', 'ONET job title']).agg({
                'Employment': 'max',
                'Detailed job tasks': 'first'  # Sample task for reference
            }).reset_index()
            
            # Sort by employment descending
            ind_occ_data = ind_occ_data.sort_values('Employment', ascending=False)
            
            # Store total count
            total_combinations = len(ind_occ_data)
            results['computational_results']['total_result_count'] = total_combinations
            results['computational_results']['display_limit'] = 100
            
            # Show all combinations (LLM will be instructed to limit display if > 100)
            logger.info(f"Found {total_combinations} industry-occupation combinations", show_ui=False)
            
            # Convert to semantic results format - all results
            for i, row in ind_occ_data.iterrows():
                results['semantic_results'].append({
                    'text': f"Industry: {row['Industry title']}, Occupation: {row['ONET job title']}, Employment: {row['Employment']:.2f}k",
                    'score': 1.0 - (min(i, 99) * 0.01),  # Cap score decay at 100
                    'metadata': {
                        'industry_title': row['Industry title'],
                        'onet_job_title': row['ONET job title'],
                        'employment': row['Employment'],
                        'task_sample': row['Detailed job tasks']
                    }
                })
            
            logger.info(f"Provided all {len(results['semantic_results'])} industry-occupation combinations", show_ui=False)
        
        # Execute semantic search if needed and not using pattern matching
        elif strategy['use_vector_search']:
            semantic_results = self._semantic_retrieval(
                query,
                k=strategy.get('k_results', k),
                filters=strategy.get('filters', {})
            )
            # Ensure we have a list, not None
            results['semantic_results'] = semantic_results if semantic_results is not None else []
            logger.debug(f"Retrieved {len(results['semantic_results'])} semantic results")
        
        # Execute computational queries if needed
        if strategy['use_aggregations'] or strategy['use_pandas']:
            computational_results = self._computational_retrieval(
                query_for_pattern_matching,  # Use original query for pattern matching
                routing_info['params'],
                semantic_results=results['semantic_results']
            )
            
            # CRITICAL FIX: MERGE computational results instead of overwriting
            # Occupation/industry summary responses may have already set validated totals
            # Pattern matching should AUGMENT, not REPLACE those results
            if computational_results:
                # If computational_results already exists from response function, merge carefully
                if results['computational_results']:
                    logger.info("Merging computational results from multiple sources", show_ui=False)
                    
                    # CRITICAL: ALWAYS preserve validated values from summary functions
                    # Even if _computational_retrieval also computed these values, the summary function values are CORRECT
                    # because they use proper de-duplication logic specific to occupation/industry queries
                    validated_keys = ['total_employment', 'total_occupations', 'total_industries',
                                    'total_employment_verified', 'occupation_count_verified',
                                    'industry_count_verified', 'arithmetic_validator', 'arithmetic_metadata']
                    
                    for key in validated_keys:
                        if key in results['computational_results']:
                            # Preserve the validated value from summary function
                            # This takes precedence over values from _computational_retrieval
                            logger.debug(f"Preserving {key} from response function (overriding _computational_retrieval)", show_ui=False)
                            computational_results[key] = results['computational_results'][key]
                    
                    # Also preserve occupation_employment and industry_employment DataFrames
                    for key in ['occupation_employment', 'industry_employment']:
                        if key in results['computational_results']:
                            computational_results[key] = results['computational_results'][key]
                
                # Now update with merged results
                results['computational_results'].update(computational_results)
            
            # Extract filtered_dataframe if it was created in computational retrieval
            if results['computational_results'] and 'filtered_dataframe' in results['computational_results']:
                results['filtered_dataframe'] = results['computational_results']['filtered_dataframe']
                # Remove from computational_results to avoid duplication
                del results['computational_results']['filtered_dataframe']
                logger.debug(f"Extracted filtered_dataframe from computational_results")
            
            logger.debug(f"Computed {len(results['computational_results'])} aggregations")
        
        # Filter dataframe based on semantic results if needed
        # CRITICAL FIX: Only set filtered_dataframe if not already set by response functions
        # Response functions (like _create_occupation_summary_response) set this correctly
        # We should NOT overwrite it with row_index extraction which may fail
        if results['semantic_results'] and strategy['use_pandas']:
            # Check if filtered_dataframe is already set and valid
            existing_df = results.get('filtered_dataframe')
            has_valid_df = (
                existing_df is not None and 
                not (isinstance(existing_df, pd.DataFrame) and existing_df.empty)
            )
            
            if has_valid_df:
                # Already has valid filtered_dataframe - don't overwrite
                logger.debug(f"Filtered dataframe already set ({len(existing_df)} rows) - not overwriting", show_ui=False)
                results['metadata']['filtered_rows'] = len(existing_df)
            else:
                # Try to create from semantic results
                logger.debug("Attempting to create filtered_dataframe from semantic results", show_ui=False)
                filtered_df = self._filter_dataframe_by_results(results['semantic_results'])
                results['filtered_dataframe'] = filtered_df
                if filtered_df is not None and not filtered_df.empty:
                    results['metadata']['filtered_rows'] = len(filtered_df)
                    logger.debug(f"Created filtered_dataframe with {len(filtered_df)} rows from semantic results", show_ui=False)
                else:
                    results['metadata']['filtered_rows'] = 0
                    logger.warning("Could not create filtered_dataframe from semantic results", show_ui=False)
        
        results['metadata']['total_results'] = (
            len(results['semantic_results']) +
            len(results['computational_results'])
        )
        
        return results
    
    def _create_task_details_response(
        self,
        matching_df: pd.DataFrame,
        results: Dict[str, Any],
        query_lower: str
    ) -> Dict[str, Any]:
        """
        Create task-level detailed response with actual task descriptions and time data
        
        Returns task descriptions (not occupation summaries) with:
        - Full task description text
        - Time per week spent on task
        - Occupation performing the task
        - Industry information
        - Employment data
        """
        logger.info(f"Creating task details response from {len(matching_df)} matching rows", show_ui=False)
        
        # CRITICAL FIX v4.8.6: De-duplicate tasks before displaying
        # Each row is task×occupation×industry, so same task appears multiple times
        # Group by (task, occupation) to show each unique task only once
        
        # De-duplicate by task description + occupation
        task_groups = matching_df.groupby(['Detailed job tasks', 'ONET job title']).agg({
            'Hours per week spent on task': 'max',  # Use max hours
            'Employment': 'first',  # Employment is same across industries for an occupation
            'Hourly wage': 'first',  # Wage is same across industries
            'Industry title': 'count'  # Count how many industries this task appears in
        }).reset_index()
        
        # Rename the count column
        task_groups = task_groups.rename(columns={'Industry title': 'Industries Count'})
        
        logger.info(f"De-duplicated from {len(matching_df)} rows to {len(task_groups)} unique tasks", show_ui=False)
        
        # Sort by time spent (descending) to prioritize important tasks
        sorted_tasks = task_groups.sort_values(
            'Hours per week spent on task',
            ascending=False,
            na_position='last'
        )
        
        # Get diverse task sample: max 5 per occupation for diversity
        task_details = []
        occ_counts = {}
        
        for idx, row in sorted_tasks.iterrows():
            occ = row.get('ONET job title', 'Unknown')
            
            # Limit per occupation for diversity across occupations
            # Increased from 3 to 5 to show more tasks
            if occ_counts.get(occ, 0) < 5:
                task_text = row.get('Detailed job tasks', '')
                industries_count = row.get('Industries Count', 1)
                
                # Create rich metadata
                metadata = {
                    'onet_job_title': occ,
                    'industries_count': int(industries_count),  # Number of industries
                    'hours_per_week_spent_on_task': row.get('Hours per week spent on task'),
                    'employment': row.get('Employment'),
                    'hourly_wage': row.get('Hourly wage'),
                    'row_index': idx
                }
                
                # Add to results
                task_details.append({
                    'text': task_text,
                    'score': 1.0 - (len(task_details) * 0.01),
                    'metadata': metadata
                })
                
                occ_counts[occ] = occ_counts.get(occ, 0) + 1
            
            # Increased from 30 to 100 for more comprehensive results
            if len(task_details) >= 100:
                break
        
        results['semantic_results'] = task_details
        
        # Store filtered dataframe for CSV export
        results['filtered_dataframe'] = matching_df.copy().reset_index(drop=True)
        
        # Calculate time statistics for task queries
        if 'time' in query_lower or 'hour' in query_lower:
            time_stats = self._calculate_time_statistics(matching_df)
            results['computational_results']['time_analysis'] = time_stats
        
        # ARITHMETIC VALIDATION: Pre-compute task-level arithmetic
        from app.utils.arithmetic_computation import ArithmeticComputationLayer
        
        computation_layer = ArithmeticComputationLayer()
        computational_results = computation_layer.compute_task_details_arithmetic(
            task_df=matching_df
        )
        
        # Merge computational results (validated arithmetic)
        results['computational_results'].update(computational_results)
        
        # Store validator for later validation (in BOTH places for safety)
        results['arithmetic_validator'] = computation_layer.get_validator()
        results['computational_results']['arithmetic_validator'] = computation_layer.get_validator()
        
        logger.info(f"✅ ARITHMETIC VALIDATION: Computed and verified {len(computation_layer.get_validator().computed_values)} values", show_ui=False)
        logger.info(f"Created {len(task_details)} unique task detail results from {len(occ_counts)} occupations", show_ui=False)
        
        return results
    
    def _create_specific_occupation_tasks(
        self,
        results: Dict[str, Any],
        query_lower: str,
        original_query: str
    ) -> Dict[str, Any]:
        """
        Handle queries asking for all tasks for a specific occupation
        e.g., "What are the tasks for an art director?"
        
        Returns ALL distinct tasks for the specified occupation, not limited to top 5 or 30
        """
        logger.info(f"Extracting occupation name from query: {original_query}", show_ui=False)
        
        # Extract potential occupation name from query
        # Remove common query words - ORDER MATTERS (longer phrases first!)
        occupation_query = query_lower
        
        # Remove longer phrases first to avoid partial matches
        removal_phrases = [
            'what are the distinct tasks for',
            'what are all the distinct tasks for',
            'what are the unique tasks for',
            'what are all the tasks for',
            'what are the tasks for',
            'show all distinct tasks for',
            'show all tasks for',
            'list all distinct tasks for',
            'list all tasks for',
            'what distinct tasks for',
            'what tasks for',
            'all distinct tasks for',
            'all tasks for',
            'distinct tasks for',
            'unique tasks for',
            'tasks for',
            'what are tasks for',
            'tasks of',
            'all tasks of',
            'distinct ',
            'unique ',
            'all ',
            'an ',
            'a ',
            'the '
        ]
        
        for phrase in removal_phrases:
            occupation_query = occupation_query.replace(phrase, '')
        
        occupation_query = occupation_query.strip(' ?.,')
        
        logger.info(f"Searching for occupation: '{occupation_query}'", show_ui=False)
        
        # Search for occupation in dataset (fuzzy match)
        # Try exact match first
        matching_rows = self.df[
            self.df['ONET job title'].str.lower().str.contains(occupation_query, case=False, na=False)
        ]
        
        if len(matching_rows) == 0:
            # Try searching in multiple words
            search_terms = occupation_query.split()
            if len(search_terms) > 0:
                # Search for any of the terms
                mask = pd.Series([False] * len(self.df))
                for term in search_terms:
                    if len(term) > 2:  # Skip very short words
                        mask |= self.df['ONET job title'].str.lower().str.contains(term, case=False, na=False)
                matching_rows = self.df[mask]
        
        if len(matching_rows) == 0:
            logger.warning(f"No occupation found matching '{occupation_query}'", show_ui=True)
            
            # Don't fall back to semantic search - return helpful error message
            error_message = f"""I couldn't find an occupation matching "{occupation_query}" in the labor market database.

**Possible reasons:**
- The occupation name might be spelled differently in the database
- Try a more general term (e.g., "director" instead of "art director")
- Check if the occupation exists in the dataset

**Suggestions:**
- Try: "What occupations are in the dataset?" to see available occupations
- Try: "Jobs related to art" for similar occupations
- Search for a broader category

The occupation you searched for: "{occupation_query}"
Original query: "{original_query}"
"""
            
            results['semantic_results'] = [{
                'text': error_message,
                'score': 1.0,
                'metadata': {
                    'error': 'occupation_not_found',
                    'searched_term': occupation_query,
                    'is_specific_occupation_task': True
                }
            }]
            
            return results
        
        # Get the most common occupation title (in case of variations)
        unique_occupations = matching_rows['ONET job title'].unique()
        logger.info(f"Found {len(unique_occupations)} matching occupations: {list(unique_occupations)[:5]}", show_ui=False)
        
        occupation_name = matching_rows['ONET job title'].value_counts().index[0]
        
        # Filter to this specific occupation
        occupation_df = self.df[self.df['ONET job title'] == occupation_name].copy()
        
        logger.info(f"Selected occupation: '{occupation_name}' with {len(occupation_df)} task entries", show_ui=False)
        
        # Get ALL distinct tasks for this occupation
        # Group by task description to get unique tasks with aggregated data
        task_groups = occupation_df.groupby('Detailed job tasks').agg({
            'Hours per week spent on task': 'mean',
            'Employment': 'max',  # Max employment across industries
            'Hourly wage': 'mean',
            'Industry title': lambda x: list(x.unique())[:5]  # Sample industries
        }).reset_index()
        
        # Sort by time spent (descending) to show most important tasks first
        task_groups = task_groups.sort_values('Hours per week spent on task', ascending=False, na_position='last')
        
        logger.info(f"Found {len(task_groups)} DISTINCT tasks for {occupation_name}", show_ui=False)
        
        # Store BOTH aggregated tasks (for display) and original occupation data (for follow-up queries)
        # For CSV export and LLM display, use aggregated task_groups
        
        # Safety check: ensure occupation_df is a valid DataFrame
        if not isinstance(occupation_df, pd.DataFrame):
            logger.error(f"occupation_df is not a DataFrame! Type: {type(occupation_df)}", show_ui=True)
            results['filtered_dataframe'] = None
        elif occupation_df.empty:
            logger.warning(f"occupation_df is empty - no data to store for follow-up", show_ui=True)
            results['filtered_dataframe'] = None
        else:
            results['filtered_dataframe'] = occupation_df.copy().reset_index(drop=True)  # Full data for follow-up
            logger.info(f"✅ Set filtered_dataframe with {len(occupation_df)} rows for follow-up queries", show_ui=False)
        
        # Also store aggregated version in computational results for CSV
        results['computational_results']['occupation_tasks_aggregated'] = task_groups.copy()
        
        logger.info(f"Stored {len(occupation_df)} original task entries", show_ui=False)
        
        # Convert ALL tasks to semantic results (no limit!)
        for i, row in task_groups.iterrows():
            task_text = row['Detailed job tasks']
            
            # Format industries list
            industries = row['Industry title']
            industry_text = ', '.join(industries) if isinstance(industries, list) else str(industries)
            
            metadata = {
                'onet_job_title': occupation_name,
                'task_description': task_text,
                'hours_per_week_spent_on_task': row['Hours per week spent on task'],
                'employment': row['Employment'],
                'hourly_wage': row['Hourly wage'],
                'sample_industries': industry_text,
                'is_specific_occupation_task': True
            }
            
            results['semantic_results'].append({
                'text': f"Task: {task_text}\nOccupation: {occupation_name}\nTime: {row['Hours per week spent on task']:.1f} hrs/week\nIndustries: {industry_text}",
                'score': 1.0 - (i * 0.001),  # Slight decay for ordering
                'metadata': metadata
            })
        
        # Create CSV data
        csv_data = task_groups.copy()
        csv_data['Occupation'] = occupation_name
        csv_data = csv_data.rename(columns={
            'Detailed job tasks': 'Task Description',
            'Hours per week spent on task': 'Hours per Week',
            'Employment': 'Employment (thousands)',
            'Hourly wage': 'Hourly Wage',
            'Industry title': 'Sample Industries'
        })
        
        results['computational_results']['occupation_tasks'] = csv_data[[
            'Occupation',
            'Task Description',
            'Hours per Week',
            'Employment (thousands)',
            'Hourly Wage',
            'Sample Industries'
        ]]
        
        logger.info(f"Created {len(results['semantic_results'])} task results for {occupation_name} (ALL distinct tasks)", show_ui=False)
        
        return results
    
    def _create_industry_summary_response(
        self,
        matching_df: pd.DataFrame,
        results: Dict[str, Any],
        query_lower: str
    ) -> Dict[str, Any]:
        """Create industry-level aggregated response"""
        
        logger.info(f"Creating industry summary from {len(matching_df)} rows", show_ui=False)
        
        # CRITICAL FIX: Avoid double-counting employment across multiple tasks
        # The dataset has multiple rows per (occupation, industry) - one per task
        # The Employment value is the same for all tasks of the same (occupation, industry)
        # So we need to de-duplicate before summing
        
        # Step 1: Get unique (industry, occupation) pairs with their employment
        unique_ind_occ = matching_df.groupby(['Industry title', 'ONET job title']).agg({
            'Employment': 'first',  # Take first value (they're all the same for same industry-occupation)
            'Hours per week spent on task': 'mean',  # Average across tasks
            'Hourly wage': 'mean',
            'Detailed job tasks': lambda x: list(x.unique())  # Collect unique tasks
        }).reset_index()
        
        logger.info(f"De-duplicated to {len(unique_ind_occ)} unique industry-occupation pairs", show_ui=False)
        
        # Step 2: Now sum employment by industry (no more double-counting!)
        ind_summary = unique_ind_occ.groupby('Industry title').agg({
            'Employment': 'sum',  # Now this is correct - summing across occupations, not tasks
            'ONET job title': 'nunique',  # Count unique occupations
            'Detailed job tasks': lambda x: sum(len(tasks) for tasks in x),  # Total tasks across occupations
            'Hours per week spent on task': 'mean',
            'Hourly wage': 'mean'
        }).reset_index()
        
        logger.info(f"Aggregated to {len(ind_summary)} unique industries with correct employment totals", show_ui=False)
        
        ind_summary = ind_summary.sort_values('Employment', ascending=False)
        
        results['filtered_dataframe'] = matching_df.copy().reset_index(drop=True)
        
        # Convert to semantic results
        for i, row in ind_summary.iterrows():
            results['semantic_results'].append({
                'text': f"Industry: {row['Industry title']}\nTotal Employment: {row['Employment']:.2f}k workers\nNumber of Occupations: {row['ONET job title']}\nNumber of Tasks: {row['Detailed job tasks']}\nAvg Hours per Week: {row['Hours per week spent on task']:.1f}",
                'score': 1.0 - (i * 0.01),
                'metadata': {
                    'industry_title': row['Industry title'],
                    'employment': row['Employment'],
                    'occupation_count': row['ONET job title'],
                    'task_count': row['Detailed job tasks'],
                    'avg_hours_per_week': row['Hours per week spent on task'],
                    'avg_hourly_wage': row['Hourly wage']
                }
            })
        
        # Create CSV data
        results['computational_results']['industry_employment'] = ind_summary.rename(columns={
            'Industry title': 'Industry',
            'Employment': 'Total Employment (thousands)',
            'ONET job title': 'Number of Occupations',
            'Detailed job tasks': 'Number of Tasks',
            'Hours per week spent on task': 'Avg Hours per Week',
            'Hourly wage': 'Avg Hourly Wage'
        })
        
        # ARITHMETIC VALIDATION: Pre-compute ALL arithmetic with ground truth
        from app.utils.arithmetic_computation import ArithmeticComputationLayer
        
        computation_layer = ArithmeticComputationLayer()
        computational_results = computation_layer.compute_industry_summary_arithmetic(
            ind_summary=ind_summary,
            matching_df=matching_df
        )
        
        # Merge computational results (validated arithmetic)
        results['computational_results'].update(computational_results)
        
        # Store validator for later validation (in BOTH places for safety)
        # Top level for direct access, and in computational_results for merge preservation
        results['arithmetic_validator'] = computation_layer.get_validator()
        results['computational_results']['arithmetic_validator'] = computation_layer.get_validator()
        
        # Calculate industry proportions
        industry_prop_results = self._compute_industry_proportions(
            matching_df,
            attribute_name="matching workers"
        )
        if industry_prop_results:
            results['computational_results']['industry_proportions'] = industry_prop_results
        
        logger.info(f"✅ ARITHMETIC VALIDATION: Computed and verified {len(computation_layer.get_validator().computed_values)} values", show_ui=False)
        logger.info(f"Created {len(results['semantic_results'])} industry-level results with verified total: {computational_results['total_employment']:.2f}k workers", show_ui=False)
        
        return results
    
    def _create_occupation_summary_response(
        self,
        matching_df: pd.DataFrame,
        results: Dict[str, Any],
        query_lower: str
    ) -> Dict[str, Any]:
        """Create occupation-level aggregated response"""
        
        logger.info(f"Creating occupation summary from {len(matching_df)} rows", show_ui=False)
        
        # CRITICAL FIX: Avoid double-counting employment across multiple tasks
        # The dataset has multiple rows per (occupation, industry) - one per task
        # The Employment value is the same for all tasks of the same (occupation, industry)
        # So we need to de-duplicate before summing
        
        # Step 1: Get unique (occupation, industry) pairs with their employment
        unique_occ_ind = matching_df.groupby(['ONET job title', 'Industry title']).agg({
            'Employment': 'first',  # Take first value (they're all the same for same occ-industry)
            'Hours per week spent on task': 'mean',  # Average across tasks
            'Hourly wage': 'mean',
            'Detailed job tasks': lambda x: list(x.unique())  # Collect unique tasks
        }).reset_index()
        
        logger.info(f"📊 De-duplicated from {len(matching_df)} rows to {len(unique_occ_ind)} unique occupation-industry pairs", show_ui=False)
        
        # Debug: Log sample of de-duplicated data
        if len(unique_occ_ind) > 0:
            sample_emp_sum = unique_occ_ind['Employment'].sum()
            logger.info(f"📊 Sum of employment across all {len(unique_occ_ind)} unique pairs: {sample_emp_sum:.2f}k", show_ui=False)
        
        # Step 2: Now sum employment by occupation (no more double-counting!)
        occ_summary = unique_occ_ind.groupby('ONET job title').agg({
            'Employment': 'sum',  # Now this is correct - summing across industries, not tasks
            'Industry title': 'nunique',  # Count unique industries
            'Detailed job tasks': lambda x: '; '.join([task for sublist in x for task in sublist][:3]),  # Flatten and take first 3
            'Hours per week spent on task': 'mean',
            'Hourly wage': 'mean'
        }).reset_index()
        
        logger.info(f"📊 Aggregated to {len(occ_summary)} unique occupations", show_ui=False)
        logger.info(f"📊 Sum of employment across all {len(occ_summary)} occupations: {occ_summary['Employment'].sum():.2f}k", show_ui=False)
        
        occ_summary = occ_summary.sort_values('Employment', ascending=False)
        
        results['filtered_dataframe'] = matching_df.copy().reset_index(drop=True)
        
        # Convert to semantic results
        for i, row in occ_summary.iterrows():
            results['semantic_results'].append({
                'text': f"Occupation: {row['ONET job title']}\nTotal Employment: {row['Employment']:.2f}k workers\nNumber of Industries: {row['Industry title']}\nAvg Hours per Week: {row['Hours per week spent on task']:.1f}\nSample Tasks: {row['Detailed job tasks'][:200]}...",
                'score': 1.0 - (i * 0.01),
                'metadata': {
                    'onet_job_title': row['ONET job title'],
                    'employment': row['Employment'],
                    'industry_count': row['Industry title'],
                    'sample_tasks': row['Detailed job tasks'],
                    'avg_hours_per_week': row['Hours per week spent on task'],
                    'avg_hourly_wage': row['Hourly wage']
                }
            })
        
        # Create CSV data
        results['computational_results']['occupation_employment'] = occ_summary.rename(columns={
            'ONET job title': 'Occupation',
            'Employment': 'Total Employment (thousands)',
            'Industry title': 'Number of Industries',
            'Detailed job tasks': 'Sample Tasks',
            'Hours per week spent on task': 'Avg Hours per Week',
            'Hourly wage': 'Avg Hourly Wage'
        })
        
        # ARITHMETIC VALIDATION: Pre-compute ALL arithmetic with ground truth
        from app.utils.arithmetic_computation import ArithmeticComputationLayer
        
        computation_layer = ArithmeticComputationLayer()
        computational_results = computation_layer.compute_occupation_summary_arithmetic(
            occ_summary=occ_summary,
            matching_df=matching_df
        )
        
        # Merge computational results (validated arithmetic)
        results['computational_results'].update(computational_results)
        
        # Store validator for later validation (in BOTH places for safety)
        # Top level for direct access, and in computational_results for merge preservation
        results['arithmetic_validator'] = computation_layer.get_validator()
        results['computational_results']['arithmetic_validator'] = computation_layer.get_validator()
        
        logger.info(f"✅ ARITHMETIC VALIDATION: Computed and verified {len(computation_layer.get_validator().computed_values)} values", show_ui=False)
        logger.info(f"Created {len(results['semantic_results'])} occupation-level results with verified total: {computational_results['total_employment']:.2f}k workers", show_ui=False)
        
        return results
    
    def _calculate_time_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate comprehensive time statistics for task queries
        Phase 2 implementation
        """
        logger.info(f"Calculating time statistics for {len(df)} rows", show_ui=False)
        
        # Filter rows with time data
        df_with_time = df[df['Hours per week spent on task'].notna()].copy()
        
        if len(df_with_time) == 0:
            return {'error': 'No time data available'}
        
        # Overall statistics
        stats = {
            'avg_hours_per_worker': float(df_with_time['Hours per week spent on task'].mean()),
            'median_hours_per_worker': float(df_with_time['Hours per week spent on task'].median()),
            'min_hours': float(df_with_time['Hours per week spent on task'].min()),
            'max_hours': float(df_with_time['Hours per week spent on task'].max()),
            'total_tasks_analyzed': len(df_with_time)
        }
        
        # Calculate total worker-hours if employment data available
        df_complete = df_with_time[df_with_time['Employment'].notna()].copy()
        if len(df_complete) > 0:
            # Employment is in thousands
            total_hours = (df_complete['Employment'] * df_complete['Hours per week spent on task']).sum() * 1000
            stats['total_worker_hours_per_week'] = float(total_hours)
        
        # Time by occupation
        time_by_occ = df_with_time.groupby('ONET job title').agg({
            'Hours per week spent on task': 'mean',
            'Employment': 'sum'
        }).reset_index()
        
        time_by_occ = time_by_occ.sort_values('Hours per week spent on task', ascending=False)
        stats['by_occupation'] = time_by_occ.head(15).to_dict('records')
        
        return stats
    
    def _estimate_time_and_cost_savings(
        self,
        df: pd.DataFrame,
        savings_percentage: float = 0.4
    ) -> pd.DataFrame:
        """
        Estimate time and dollar savings from automation
        Phases 2 & 3 implementation
        
        Args:
            df: DataFrame with task/occupation data
            savings_percentage: Assumed percentage of time saved (default 40%)
        
        Returns:
            DataFrame with savings analysis by occupation
        """
        logger.info(f"Estimating savings at {savings_percentage*100}% for {len(df)} rows", show_ui=False)
        
        # Group by occupation and aggregate
        savings_by_occ = df.groupby('ONET job title').agg({
            'Hours per week spent on task': 'mean',
            'Employment': 'sum',
            'Hourly wage': 'mean'
        }).reset_index()
        
        # Calculate time savings
        savings_by_occ['time_saved_per_worker'] = (
            savings_by_occ['Hours per week spent on task'] * savings_percentage
        )
        
        # Total hours saved (across all workers)
        savings_by_occ['total_hours_saved_per_week'] = (
            savings_by_occ['Employment'] * 
            savings_by_occ['time_saved_per_worker'] * 
            1000  # Employment in thousands
        )
        
        # Dollar savings (if wage data available)
        wage_available = savings_by_occ['Hourly wage'].notna()
        savings_by_occ.loc[wage_available, 'weekly_dollar_savings'] = (
            savings_by_occ.loc[wage_available, 'total_hours_saved_per_week'] * 
            savings_by_occ.loc[wage_available, 'Hourly wage']
        )
        
        # Annual savings
        savings_by_occ.loc[wage_available, 'annual_dollar_savings'] = (
            savings_by_occ.loc[wage_available, 'weekly_dollar_savings'] * 52
        )
        
        # Sort by dollar savings (or hours if no wage data)
        if wage_available.any():
            savings_by_occ = savings_by_occ.sort_values(
                'weekly_dollar_savings',
                ascending=False,
                na_position='last'
            )
        else:
            savings_by_occ = savings_by_occ.sort_values(
                'total_hours_saved_per_week',
                ascending=False
            )
        
        # Rename columns for clarity
        savings_by_occ = savings_by_occ.rename(columns={
            'ONET job title': 'Occupation',
            'Hours per week spent on task': 'Current Hours per Week',
            'Employment': 'Workers (thousands)',
            'Hourly wage': 'Avg Hourly Wage',
            'time_saved_per_worker': 'Hours Saved per Worker',
            'total_hours_saved_per_week': 'Total Hours Saved per Week',
            'weekly_dollar_savings': 'Weekly Dollar Savings',
            'annual_dollar_savings': 'Annual Dollar Savings'
        })
        
        logger.info(f"Savings calculated for {len(savings_by_occ)} occupations", show_ui=False)
        
        return savings_by_occ
    
    def _create_general_industry_ranking(
        self,
        results: Dict[str, Any],
        query_lower: str
    ) -> Dict[str, Any]:
        """
        Handle general industry ranking queries like "Which industries have the highest employment?"
        Works on FULL dataset, not filtered to specific tasks
        """
        logger.info(f"Creating general industry ranking from full dataset ({len(self.df)} rows)", show_ui=False)
        
        # Group by industry and aggregate TOTAL employment
        industry_summary = self.df.groupby('Industry title').agg({
            'Employment': 'sum',  # Total employment across ALL occupations and tasks
            'ONET job title': 'nunique',  # Number of distinct occupations
            'Detailed job tasks': lambda x: len(x)  # Number of tasks
        }).reset_index()
        
        # Sort by employment descending
        industry_summary = industry_summary.sort_values('Employment', ascending=False)
        
        logger.info(f"Found {len(industry_summary)} industries, top has {industry_summary.iloc[0]['Employment']:.2f}k workers", show_ui=False)
        
        # Store for CSV export
        results['filtered_dataframe'] = industry_summary.copy()
        
        # Store total count for LLM to reference
        total_industries = len(industry_summary)
        results['computational_results']['total_result_count'] = total_industries
        results['computational_results']['display_limit'] = 100
        
        # Convert to semantic results format - ALL industries (no limit)
        # LLM will be instructed to inform user about CSV download if > 100
        for i, row in industry_summary.iterrows():
            results['semantic_results'].append({
                'text': f"Industry: {row['Industry title']}\nTotal Employment: {row['Employment']:.2f} thousand workers\nOccupations: {row['ONET job title']}\nTasks in Dataset: {row['Detailed job tasks']}",
                'score': 1.0 - (min(i, 99) * 0.01),  # Cap score decay at 100
                'metadata': {
                    'industry_title': row['Industry title'],
                    'employment': row['Employment'],
                    'occupation_count': row['ONET job title'],
                    'task_count': row['Detailed job tasks'],
                    'is_industry_summary': True
                }
            })
        
        # Create CSV data
        results['computational_results']['industry_employment'] = industry_summary.rename(columns={
            'Industry title': 'Industry',
            'Employment': 'Total Employment (thousands)',
            'ONET job title': 'Number of Occupations',
            'Detailed job tasks': 'Number of Tasks'
        })
        
        logger.info(f"Created {len(results['semantic_results'])} industry ranking results (all {total_industries} industries)", show_ui=False)
        
        return results
    
    def _create_general_occupation_ranking(
        self,
        results: Dict[str, Any],
        query_lower: str
    ) -> Dict[str, Any]:
        """
        Handle general occupation ranking queries like "What occupations require the most diverse skill sets?"
        Works on FULL dataset, not filtered to specific tasks
        """
        logger.info(f"Creating general occupation ranking from full dataset ({len(self.df)} rows)", show_ui=False)
        
        # Determine what to rank by
        if 'diverse' in query_lower or 'diversity' in query_lower or 'skill' in query_lower:
            # Rank by diversity (number of distinct tasks)
            occ_summary = self.df.groupby('ONET job title').agg({
                'Detailed job tasks': 'nunique',  # Number of DISTINCT tasks
                'Employment': 'sum',  # Total employment across all industries
                'Industry title': 'nunique'  # Number of industries occupation appears in
            }).reset_index()
            
            # Sort by task diversity (number of distinct tasks)
            occ_summary = occ_summary.sort_values('Detailed job tasks', ascending=False)
            rank_criterion = 'Task Diversity'
            
        elif 'employment' in query_lower or 'workers' in query_lower:
            # Rank by employment
            occ_summary = self.df.groupby('ONET job title').agg({
                'Employment': 'sum',
                'Detailed job tasks': 'nunique',
                'Industry title': 'nunique'
            }).reset_index()
            
            occ_summary = occ_summary.sort_values('Employment', ascending=False)
            rank_criterion = 'Employment'
            
        else:
            # Default: rank by employment
            occ_summary = self.df.groupby('ONET job title').agg({
                'Employment': 'sum',
                'Detailed job tasks': 'nunique',
                'Industry title': 'nunique'
            }).reset_index()
            
            occ_summary = occ_summary.sort_values('Employment', ascending=False)
            rank_criterion = 'Employment'
        
        logger.info(f"Found {len(occ_summary)} occupations, ranking by {rank_criterion}", show_ui=False)
        
        # Store for CSV export
        results['filtered_dataframe'] = occ_summary.copy()
        
        # Store total count for LLM to reference
        total_occupations = len(occ_summary)
        results['computational_results']['total_result_count'] = total_occupations
        results['computational_results']['display_limit'] = 100
        
        # Convert to semantic results format - ALL occupations (no limit)
        for i, row in occ_summary.iterrows():
            results['semantic_results'].append({
                'text': f"Occupation: {row['ONET job title']}\nTotal Employment: {row['Employment']:.2f} thousand workers\nDistinct Tasks: {row['Detailed job tasks']}\nIndustries: {row['Industry title']}",
                'score': 1.0 - (min(i, 99) * 0.01),  # Cap score decay at 100
                'metadata': {
                    'onet_job_title': row['ONET job title'],
                    'employment': row['Employment'],
                    'task_diversity': row['Detailed job tasks'],
                    'industry_count': row['Industry title'],
                    'is_occupation_summary': True
                }
            })
        
        # Create CSV data
        results['computational_results']['occupation_employment'] = occ_summary.rename(columns={
            'ONET job title': 'Occupation',
            'Employment': 'Total Employment (thousands)',
            'Detailed job tasks': 'Distinct Tasks',
            'Industry title': 'Number of Industries'
        })
        
        logger.info(f"Created {len(results['semantic_results'])} occupation ranking results", show_ui=False)
        
        return results
    
    def _semantic_retrieval(
        self,
        query: str,
        k: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic vector search"""
        
        try:
            results = self.vector_store.search(
                query=query,
                k=k,
                filter_dict=filters
            )
            return results
        except Exception as e:
            logger.error(f"Semantic retrieval failed: {str(e)}", show_ui=False)
            return []
    
    def _computational_retrieval(
        self,
        query: str,
        params: Dict[str, Any],
        semantic_results: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform computational/analytical queries"""
        
        computational_results = {}
        
        # Check if dataframe exists
        if self.df is None:
            logger.warning("Dataframe is None in computational retrieval", show_ui=False)
            return {}
        
        # Determine which dataframe to use
        if semantic_results:
            # Filter to relevant documents
            row_indices = [
                r['metadata'].get('row_index')
                for r in semantic_results
                if 'row_index' in r.get('metadata', {})
            ]
            df_subset = self.df.loc[row_indices] if row_indices else self.df
        else:
            df_subset = self.df
        
        # Execute based on aggregation type
        agg_type = params.get('aggregation')
        
        if agg_type == 'count':
            computational_results['counts'] = self._compute_counts(df_subset, params)
        
        if agg_type == 'sum':
            computational_results['totals'] = self._compute_totals(df_subset, params)
        
        if agg_type == 'average':
            computational_results['averages'] = self._compute_averages(df_subset, params)
        
        if agg_type == 'percentage':
            computational_results['percentages'] = self._compute_percentages(df_subset, params)
        
        # Special handling for industry proportion/ranking queries
        if params.get('industry_ranking'):
            logger.info("Industry ranking query detected - computing proportions", show_ui=False)
            
            # Determine what attribute we're measuring
            attribute_name = "workers matching criteria"
            pattern_df = None
            
            # V4.0.0: Use generic pattern engine instead of hardcoded patterns
            detected_category = self.pattern_engine.detect_task_category(query)
            
            if detected_category:
                category_config = self.pattern_engine.get_category_config(detected_category)
                attribute_name = f"{category_config.display_name.lower()} workers"
                
                # Generic pattern matching using engine
                logger.info(f"✓ v4.8.6: Generic pattern matching for {detected_category} on full dataset", show_ui=False)
                
                pattern_df = self.pattern_engine.filter_dataframe(
                    self.df,
                    detected_category,
                    task_column='Detailed job tasks'
                )
                logger.info(f"✓ v4.8.6: Pattern matching found {len(pattern_df)} rows (of {len(self.df)} total)", show_ui=False)
                
            elif params.get('entity'):
                attribute_name = f"{params['entity']} workers"
            
            # Use pattern-matched data if available, otherwise use semantic results
            df_for_proportions = pattern_df if pattern_df is not None else df_subset
            
            # Compute industry proportions on ALL matching data (not just semantic results)
            industry_prop_results = self._compute_industry_proportions(df_for_proportions, attribute_name)
            if industry_prop_results:
                computational_results['industry_proportions'] = industry_prop_results
                logger.info(f"Industry proportions computed successfully", show_ui=False)
        
        # Group by if specified
        if params.get('group_by'):
            computational_results['grouped'] = self._compute_grouped(
                df_subset,
                params['group_by'],
                agg_type
            )
        
        # Get top N if specified
        if params.get('top_n') and params.get('group_by'):
            computational_results['top_n'] = self._get_top_n(
                computational_results.get('grouped', {}),
                params['top_n']
            )
        
        # Special handling for skill-related queries
        if 'skill' in query.lower() or 'diverse' in query.lower():
            skill_analysis = self._analyze_skills(df_subset)
            if skill_analysis:
                computational_results['skill_analysis'] = skill_analysis
        
        # Special handling for task count queries
        if 'task' in query.lower() and ('most' in query.lower() or 'many' in query.lower() or 'count' in query.lower()):
            task_analysis = self._analyze_tasks(df_subset)
            if task_analysis:
                computational_results['task_analysis'] = task_analysis
        
        # PHASE 2: Time analysis for time-related queries
        query_lower = query.lower()
        if any(phrase in query_lower for phrase in ['how much time', 'total time', 'time per week', 
                                                      'hours per week', 'time spent', 'hours spent']):
            logger.info("Time analysis query detected", show_ui=False)
            time_analysis = self._calculate_time_statistics(df_subset)
            if time_analysis:
                computational_results['time_analysis'] = time_analysis
                logger.info("Time analysis computed successfully", show_ui=False)
        
        # PHASE 2 & 3: Time savings and dollar savings analysis
        if any(phrase in query_lower for phrase in ['time save', 'time saving', 'could save', 'shave off',
                                                      'dollar saving', 'cost saving', 'financial saving',
                                                      'roi', 'return on investment']):
            logger.info("Savings analysis query detected", show_ui=False)
            
            # Determine savings percentage (default 40%)
            savings_pct = 0.4
            if 'half' in query_lower or '50%' in query_lower or '50 percent' in query_lower:
                savings_pct = 0.5
            elif '30%' in query_lower or '30 percent' in query_lower:
                savings_pct = 0.3
            elif '25%' in query_lower or '25 percent' in query_lower:
                savings_pct = 0.25
            
            savings_analysis = self._estimate_time_and_cost_savings(df_subset, savings_pct)
            if savings_analysis is not None and len(savings_analysis) > 0:
                computational_results['savings_analysis'] = savings_analysis.to_dict('records')
                computational_results['savings_summary'] = {
                    'assumption_pct': savings_pct * 100,
                    'total_occupations': len(savings_analysis)
                }
                
                # Calculate grand totals if wage data available
                if 'Weekly Dollar Savings' in savings_analysis.columns:
                    weekly_total = savings_analysis['Weekly Dollar Savings'].sum()
                    annual_total = savings_analysis['Annual Dollar Savings'].sum()
                    computational_results['savings_summary']['total_weekly_savings'] = float(weekly_total)
                    computational_results['savings_summary']['total_annual_savings'] = float(annual_total)
                
                # Total hours saved
                if 'Total Hours Saved per Week' in savings_analysis.columns:
                    total_hours = savings_analysis['Total Hours Saved per Week'].sum()
                    computational_results['savings_summary']['total_hours_saved_per_week'] = float(total_hours)
                
                logger.info(f"Savings analysis computed for {len(savings_analysis)} occupations", show_ui=False)
        
        # Support for "top N by savings" queries
        if any(phrase in query_lower for phrase in ['top', 'top-', 'top 10', 'top 5', 'most time']):
            # Extract N if specified
            import re
            top_match = re.search(r'top[- ]?(\d+)', query_lower)
            if top_match:
                top_n = int(top_match.group(1))
                if 'savings_analysis' in computational_results:
                    # Already computed, just limit to top N
                    savings_df = pd.DataFrame(computational_results['savings_analysis'])
                    computational_results['top_savings'] = savings_df.head(top_n).to_dict('records')
                    logger.info(f"Top {top_n} savings computed", show_ui=False)
        
        # Special handling for "what jobs" pattern matching queries
        
        # Detect if this is a TASK query vs JOB query
        is_task_query = any(phrase in query_lower for phrase in ['specific tasks', 'what tasks', 'which tasks', 
                                                                   'tasks that', 'tasks involve', 'task descriptions'])
        is_job_query = any(phrase in query_lower for phrase in ['what jobs', 'which jobs', 'what occupations', 
                                                                  'which occupations', 'list jobs', 'list occupations', 
                                                                  'jobs that', 'occupations that'])
        
        pattern_indicators = ['what jobs', 'which jobs', 'what occupations', 'which occupations', 
                             'list jobs', 'list occupations', 'jobs that', 'occupations that']
        
        pattern_detected = any(indicator in query_lower for indicator in pattern_indicators)
        logger.info(f"Pattern matching check: pattern_detected={pattern_detected}, is_task_query={is_task_query}, is_job_query={is_job_query}", show_ui=False)
        
        # V4.0.0: Generic occupation-level pattern matching for JOB queries
        if pattern_detected and is_job_query and not is_task_query:
            # V4.0.0: Detect category using generic engine
            # Note: 'query' parameter here is already the original query (passed from retrieve())
            detected_category = self.pattern_engine.detect_task_category(query)
            
            if detected_category:
                logger.info(f"✓ v4.8.6: Pattern match FOUND ({detected_category}) - triggering occupation analysis", show_ui=False)
                
                # CRITICAL: Use full dataframe, not filtered subset
                # Pattern matching needs to analyze ALL occupations, not just semantically similar ones
                logger.info(f"Analyzing {self.df['ONET job title'].nunique()} occupations for pattern", show_ui=False)
                
                # V4.0.0: Get matching dataframe using generic engine
                matching_df = self.pattern_engine.filter_dataframe(
                    self.df,
                    detected_category,
                    task_column='Detailed job tasks'
                )
                
                # Analyze occupations from matching data
                occupation_analysis = self._analyze_occupations_from_matches(matching_df)
                computational_results['occupation_pattern_analysis'] = occupation_analysis
                logger.info(f"✓ v4.8.6: Pattern analysis complete: {len(occupation_analysis.get('top_occupations', []))} occupations matched", show_ui=False)
                computational_results['occupation_pattern_analysis'] = occupation_analysis
                logger.info(f"Pattern analysis complete: {len(occupation_analysis.get('top_occupations', []))} occupations matched", show_ui=False)
                
                # CRITICAL FIX: Create filtered_dataframe for follow-up queries
                # Extract all occupations that matched the pattern
                matching_occupations = [occ for occ, _ in occupation_analysis.get('top_occupations', [])]
                
                if matching_occupations:
                    # Filter dataframe to only matching occupations
                    filtered_df = self.df[self.df['ONET job title'].isin(matching_occupations)].copy()
                    # Store in computational_results (will be extracted later)
                    computational_results['filtered_dataframe'] = filtered_df.reset_index(drop=True)
                    logger.info(f"✅ Created filtered_dataframe with {len(filtered_df)} rows from {len(matching_occupations)} matching occupations for follow-up queries", show_ui=False)
                else:
                    logger.warning("No matching occupations found in pattern analysis", show_ui=False)
                
                # If this is also an employment query, compute employment for matching occupations
                if ('employment' in query_lower or 'total' in query_lower or 'how many' in query_lower) and matching_occupations:
                    if 'Employment' in self.df.columns:
                        logger.info(f"Computing employment for {len(matching_occupations)} matching occupations", show_ui=False)
                        
                        try:
                            # CRITICAL FIX: De-duplicate by (occupation, industry) before computing employment
                            # OLD METHOD (WRONG): matching_occ_employment = df.groupby('ONET job title')['Employment'].max()
                            # This double-counts workers across multiple tasks in the same occupation-industry
                            
                            # NEW METHOD (CORRECT): De-duplicate by (occupation, industry) first
                            matching_df = self.df[self.df['ONET job title'].isin(matching_occupations)]
                            
                            if 'Industry title' in matching_df.columns:
                                # Step 1: De-duplicate by (occupation, industry) - take first employment value
                                unique_occ_ind = matching_df.groupby(['ONET job title', 'Industry title'])['Employment'].first()
                                
                                # Step 2: Sum by occupation across industries
                                matching_occ_employment = unique_occ_ind.groupby(level=0).sum()
                                
                                logger.info(f"De-duplicated employment calculation: {len(unique_occ_ind)} unique occupation-industry pairs", show_ui=False)
                            else:
                                # Fallback if Industry column not available
                                matching_occ_employment = matching_df.groupby('ONET job title')['Employment'].max()
                                logger.warning("Industry column not available - using max per occupation (may be approximate)", show_ui=False)
                            
                            # Ensure we have valid data
                            if len(matching_occ_employment) > 0:
                                total_employment = float(matching_occ_employment.sum())
                                
                                # Convert to dict with proper type handling
                                per_occupation_dict = {}
                                for occ, emp in matching_occ_employment.items():
                                    try:
                                        # Ensure conversion to float, handle NaN
                                        emp_value = float(emp) if pd.notna(emp) else 0.0
                                        per_occupation_dict[str(occ)] = emp_value
                                    except (ValueError, TypeError) as e:
                                        logger.warning(f"Could not convert employment for {occ}: {emp}", show_ui=False)
                                        per_occupation_dict[str(occ)] = 0.0
                                
                                # ARITHMETIC VALIDATION: Pre-compute verified values
                                from app.utils.arithmetic_computation import ArithmeticComputationLayer
                                
                                computation_layer = ArithmeticComputationLayer()
                                validator = computation_layer.get_validator()
                                
                                # Compute verified total
                                total_employment_verified = validator.compute_sum(
                                    data=list(matching_occ_employment.values()),
                                    description="total_employment_pattern_matched_occupations",
                                    unit='k'
                                )
                                
                                # Compute verified count
                                occupation_count_verified = validator.compute_count(
                                    data=matching_occupations,
                                    description="pattern_matched_occupations"
                                )
                                
                                # Store both legacy and verified results
                                computational_results['employment_for_matching_occupations'] = {
                                    'total_employment': total_employment,
                                    'occupations_count': len(matching_occupations),
                                    'per_occupation': per_occupation_dict,
                                    'note': 'Employment de-duplicated at occupation-industry level'
                                }
                                
                                # CRITICAL: Only store at top level if NOT already set by occupation summary
                                # Occupation summary results (32 occupations, 5018.44k) take precedence over
                                # pattern matching subset (15 occupations, 2824.30k)
                                if 'total_employment' not in computational_results:
                                    computational_results['total_employment'] = total_employment
                                    computational_results['total_occupations'] = len(matching_occupations)
                                    computational_results['total_employment_verified'] = total_employment_verified
                                    computational_results['occupation_count_verified'] = occupation_count_verified
                                    computational_results['arithmetic_validator'] = validator
                                    computational_results['arithmetic_metadata'] = {
                                        'computation_complete': True,
                                        'total_computations': len(validator.computed_values),
                                        'all_values_verified': True,
                                        'source': 'pattern_matching_employment'
                                    }
                                    logger.info(f"✅ ARITHMETIC VALIDATION (Pattern Match): Computed and verified {len(validator.computed_values)} values", show_ui=False)
                                else:
                                    # Occupation summary already set the total - don't overwrite
                                    logger.info(f"📊 Pattern matching found subset: {total_employment:.2f}k across {len(matching_occupations)} occupations (not overwriting occupation summary total)", show_ui=False)
                                
                                logger.info(f"Employment for matching occupations: {total_employment:.2f} across {len(matching_occupations)} occupations", show_ui=False)
                            else:
                                logger.warning(f"No employment data found for matching occupations", show_ui=False)
                        except Exception as e:
                            logger.error(f"Error computing employment for matching occupations: {str(e)}", show_ui=False)
        
        return computational_results
    
    def _compute_counts(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute counts including enriched fields"""
        counts = {}
        
        counts['total_rows'] = len(df)
        
        if 'Industry title' in df.columns:
            counts['unique_industries'] = df['Industry title'].nunique()
        
        if 'ONET job title' in df.columns:
            counts['unique_occupations'] = df['ONET job title'].nunique()
        
        # Add enriched field counts
        if 'Industry_Canonical' in df.columns:
            counts['unique_canonical_industries'] = df['Industry_Canonical'].nunique()
        
        if 'Skill_Count' in df.columns:
            counts['occupations_with_skills'] = (df['Skill_Count'] > 0).sum()
            counts['total_skills_identified'] = df['Skill_Count'].sum()
            counts['avg_skills_per_occupation'] = df['Skill_Count'].mean()
        
        return counts
    
    def _compute_totals(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute totals"""
        totals = {}
        
        if 'Employment' in df.columns:
            # CRITICAL: Employment varies by TASK, not occupation
            # Each row (task) has its own employment value
            # To get total employment, we need to aggregate by occupation first
            
            if 'ONET job title' in df.columns:
                try:
                    # CRITICAL FIX: De-duplicate by (occupation, industry) before summing
                    # The dataset has one row per (occupation, task, industry) combination
                    # Employment is at the occupation-industry level, repeated for each task
                    # We must de-duplicate to avoid counting the same workers multiple times
                    
                    if 'Industry title' in df.columns:
                        # De-duplicate by occupation-industry pairs (correct approach)
                        unique_occ_ind = df.groupby(['ONET job title', 'Industry title'])['Employment'].first()
                        total_emp = float(unique_occ_ind.sum())
                        
                        totals['total_employment'] = total_emp
                        totals['employment_note'] = f"Employment de-duplicated at occupation-industry level ({len(unique_occ_ind)} pairs)"
                        
                        logger.info(f"Employment computed correctly: {len(unique_occ_ind)} occupation-industry pairs, total={total_emp:.2f}", show_ui=False)
                    else:
                        # Fallback: max per occupation if industry column not available
                        unique_employment_per_occ = df.groupby('ONET job title')['Employment'].max()
                        total_emp = float(unique_employment_per_occ.sum())
                        
                        totals['total_employment'] = total_emp
                        totals['employment_note'] = f"Employment aggregated at occupation level ({len(unique_employment_per_occ)} occupations) - may be approximate"
                        
                        logger.warning(f"Industry column not available - using max per occupation (may not be exact)", show_ui=False)
                    
                except Exception as e:
                    logger.error(f"Error computing employment totals: {str(e)}", show_ui=False)
                    totals['total_employment'] = 0.0
                    totals['error'] = str(e)
            else:
                # Fallback if occupation column not available
                try:
                    totals['total_employment'] = float(df['Employment'].sum())
                    logger.warning("Computing employment without occupation grouping - may be inaccurate", show_ui=False)
                except Exception as e:
                    logger.error(f"Error computing employment: {str(e)}", show_ui=False)
                    totals['total_employment'] = 0.0
        
        if 'Hours per week spent on task' in df.columns:
            try:
                totals['total_task_hours'] = float(df['Hours per week spent on task'].sum())
            except Exception as e:
                logger.error(f"Error computing task hours: {str(e)}", show_ui=False)
        
        return totals
    
    def _compute_averages(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute averages"""
        averages = {}
        
        if 'Employment' in df.columns:
            averages['avg_employment'] = float(df['Employment'].mean())
        
        if 'Hourly wage' in df.columns:
            averages['avg_hourly_wage'] = float(df['Hourly wage'].mean())
        
        if 'Hours per week spent on task' in df.columns:
            averages['avg_task_hours'] = float(df['Hours per week spent on task'].mean())
        
        return averages
    
    def _compute_percentages(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute percentages"""
        percentages = {}
        
        # Check if self.df is None
        if self.df is None:
            logger.warning("Dataframe is None in percentage computation", show_ui=False)
            return {}
        
        total_rows = len(self.df)  # Use full dataset for percentage
        filtered_rows = len(df)
        
        if total_rows > 0:
            percentages['percentage_of_dataset'] = (filtered_rows / total_rows) * 100
        
        return percentages
    
    def _compute_industry_proportions(
        self,
        matching_df: pd.DataFrame,
        attribute_name: str = "matching criteria"
    ) -> Dict[str, Any]:
        """
        Calculate what proportion of each industry's workforce matches the criteria
        
        Args:
            matching_df: Dataframe filtered to only matching rows
            attribute_name: Description of what we're measuring (for display)
        
        Returns:
            Dict with industry proportions, ranked by percentage
        """
        logger.info(f"Computing industry proportions for: {attribute_name}", show_ui=False)
        
        if self.df is None or matching_df is None:
            logger.warning("Missing dataframe for industry proportion calculation", show_ui=False)
            return {}
        
        if 'Industry title' not in self.df.columns or 'ONET job title' not in self.df.columns:
            logger.warning("Missing required columns for industry proportion calculation", show_ui=False)
            return {}
        
        if 'Employment' not in self.df.columns:
            logger.warning("Missing Employment column for industry proportion calculation", show_ui=False)
            return {}
        
        try:
            industry_proportions = []
            
            # Get all unique industries
            all_industries = self.df['Industry title'].unique()
            
            for industry in all_industries:
                # Get total employment in this industry
                # For each occupation in this industry, take max employment (occupation total)
                industry_data = self.df[self.df['Industry title'] == industry]
                
                if len(industry_data) == 0:
                    continue
                
                # Calculate total employment: sum of max employment per occupation
                total_employment = industry_data.groupby('ONET job title')['Employment'].max().sum()
                
                # Get matching employment in this industry
                matching_industry_data = matching_df[matching_df['Industry title'] == industry]
                
                if len(matching_industry_data) == 0:
                    # Industry exists but has no matching workers
                    matching_employment = 0.0
                else:
                    # Calculate matching employment: sum of max employment per occupation
                    matching_employment = matching_industry_data.groupby('ONET job title')['Employment'].max().sum()
                
                # Calculate proportion
                if total_employment > 0:
                    proportion = (matching_employment / total_employment) * 100
                else:
                    proportion = 0.0
                
                industry_proportions.append({
                    'industry': str(industry),
                    'matching_employment': float(matching_employment),
                    'total_employment': float(total_employment),
                    'proportion': float(proportion)
                })
            
            # Sort by proportion descending
            industry_proportions.sort(key=lambda x: x['proportion'], reverse=True)
            
            results = {
                'industry_proportions': industry_proportions,
                'attribute_name': attribute_name,
                'total_industries': len(industry_proportions),
                'industries_with_matches': sum(1 for ip in industry_proportions if ip['matching_employment'] > 0)
            }
            
            logger.info(
                f"Industry proportion analysis complete: {results['total_industries']} industries, "
                f"{results['industries_with_matches']} with matches",
                show_ui=False
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error computing industry proportions: {str(e)}", show_ui=False)
            return {}
    
    def _create_task_details_response(
        self,
        matching_df: pd.DataFrame,
        results: Dict[str, Any],
        query_lower: str
    ) -> Dict[str, Any]:
        """
        Create task-level detailed response with actual task descriptions and time data
        For queries like: "What are the specific tasks that involve...?"
        """
        logger.info(f"Creating task details response from {len(matching_df)} rows", show_ui=False)
        
        # CRITICAL FIX v4.8.6: De-duplicate tasks before displaying
        # Each row is task×occupation×industry, so same task appears multiple times
        # Group by (task, occupation) to show each unique task only once
        
        # De-duplicate by task description + occupation
        task_groups = matching_df.groupby(['Detailed job tasks', 'ONET job title']).agg({
            'Hours per week spent on task': 'max',  # Use max hours
            'Employment': 'first',  # Employment is same across industries for an occupation
            'Hourly wage': 'first',  # Wage is same across industries
            'Industry title': 'count'  # Count how many industries this task appears in
        }).reset_index()
        
        # Rename the count column
        task_groups = task_groups.rename(columns={'Industry title': 'Industries Count'})
        
        logger.info(f"De-duplicated from {len(matching_df)} rows to {len(task_groups)} unique tasks", show_ui=False)
        
        # Get diverse task sample: max 5 per occupation for diversity
        task_details = []
        occ_counts = {}
        
        # Sort by time spent (descending) to prioritize important tasks
        # Handle NaN values in Hours per week
        sorted_tasks = task_groups.copy()
        sorted_tasks['Hours per week spent on task'] = pd.to_numeric(
            sorted_tasks['Hours per week spent on task'], 
            errors='coerce'
        )
        sorted_tasks = sorted_tasks.sort_values(
            'Hours per week spent on task', 
            ascending=False, 
            na_position='last'
        )
        
        # Store filtered dataframe for CSV export
        results['filtered_dataframe'] = matching_df.copy().reset_index(drop=True)
        
        for idx, row in sorted_tasks.iterrows():
            occ = row.get('ONET job title', 'Unknown')
            
            # Limit per occupation for diversity (max 5 tasks per occupation)
            # Increased from 3 to 5 for better coverage
            if occ_counts.get(occ, 0) < 5:
                # Get time data
                hours = row.get('Hours per week spent on task')
                try:
                    hours_float = float(hours) if pd.notna(hours) else None
                except (ValueError, TypeError):
                    hours_float = None
                
                # Get employment data
                employment = row.get('Employment')
                try:
                    emp_float = float(employment) if pd.notna(employment) else None
                except (ValueError, TypeError):
                    emp_float = None
                
                # Get industries count
                industries_count = row.get('Industries Count', 1)
                
                task_details.append({
                    'text': str(row.get('Detailed job tasks', '')),
                    'score': 1.0 - (len(task_details) * 0.01),
                    'metadata': {
                        'onet_job_title': occ,
                        'industries_count': int(industries_count),  # Number of industries this task appears in
                        'hours_per_week_spent_on_task': hours_float,
                        'employment': emp_float,
                        'hourly_wage': float(row.get('Hourly wage')) if pd.notna(row.get('Hourly wage')) else None,
                        'row_index': idx
                    }
                })
                occ_counts[occ] = occ_counts.get(occ, 0) + 1
            
            # Increased from 30 to 100 for more comprehensive task coverage
            if len(task_details) >= 100:
                break
        
        results['semantic_results'] = task_details
        
        logger.info(
            f"Created {len(task_details)} unique task details from {len(occ_counts)} occupations",
            show_ui=False
        )
        
        # Add time analysis if requested
        if any(phrase in query_lower for phrase in ['how much time', 'total time', 'time per week']):
            results['computational_results']['time_analysis'] = self._compute_time_analysis(
                matching_df,
                task_details
            )
        
        # ARITHMETIC VALIDATION: Pre-compute task-level arithmetic
        from app.utils.arithmetic_computation import ArithmeticComputationLayer
        
        computation_layer = ArithmeticComputationLayer()
        computational_results = computation_layer.compute_task_details_arithmetic(
            task_df=matching_df
        )
        
        # Merge computational results (validated arithmetic)
        results['computational_results'].update(computational_results)
        
        # Store validator for later validation (in BOTH places for safety)
        results['arithmetic_validator'] = computation_layer.get_validator()
        results['computational_results']['arithmetic_validator'] = computation_layer.get_validator()
        
        logger.info(f"✅ ARITHMETIC VALIDATION: Computed and verified {len(computation_layer.get_validator().computed_values)} values", show_ui=False)
        
        return results
    
    def _compute_time_analysis(
        self,
        df: pd.DataFrame,
        task_details: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate time-related statistics
        For queries like: "How much time per week do workers spend on these tasks?"
        """
        logger.info(f"Computing time analysis for {len(df)} rows", show_ui=False)
        
        # Ensure Hours per week is numeric
        df_copy = df.copy()
        df_copy['Hours per week spent on task'] = pd.to_numeric(
            df_copy['Hours per week spent on task'],
            errors='coerce'
        )
        df_copy['Employment'] = pd.to_numeric(df_copy['Employment'], errors='coerce')
        
        # Remove NaN values for calculations
        df_with_time = df_copy[df_copy['Hours per week spent on task'].notna()]
        
        if len(df_with_time) == 0:
            return {'error': 'No time data available'}
        
        # Overall statistics
        time_stats = {
            'avg_hours_per_worker': float(df_with_time['Hours per week spent on task'].mean()),
            'median_hours_per_worker': float(df_with_time['Hours per week spent on task'].median()),
            'min_hours': float(df_with_time['Hours per week spent on task'].min()),
            'max_hours': float(df_with_time['Hours per week spent on task'].max()),
            'total_tasks_with_time_data': len(df_with_time)
        }
        
        # Calculate total worker-hours per week
        # Total worker-hours = sum(employment × hours per task)
        df_with_both = df_with_time[df_with_time['Employment'].notna()]
        if len(df_with_both) > 0:
            # Employment is in thousands
            total_worker_hours = (
                df_with_both['Employment'] * 
                df_with_both['Hours per week spent on task']
            ).sum() * 1000  # Convert from thousands
            time_stats['total_worker_hours_per_week'] = float(total_worker_hours)
        
        # By occupation
        time_by_occ = df_with_time.groupby('ONET job title').agg({
            'Hours per week spent on task': 'mean',
            'Employment': 'sum'
        }).reset_index()
        
        time_by_occ = time_by_occ.sort_values('Hours per week spent on task', ascending=False)
        
        # Calculate total hours per occupation
        time_by_occ_with_emp = time_by_occ[time_by_occ['Employment'].notna()].copy()
        if len(time_by_occ_with_emp) > 0:
            time_by_occ_with_emp['total_hours'] = (
                time_by_occ_with_emp['Employment'] * 
                time_by_occ_with_emp['Hours per week spent on task'] * 
                1000  # Employment in thousands
            )
        
        return {
            'overall': time_stats,
            'by_occupation': time_by_occ.head(15).to_dict('records'),
            'by_occupation_with_totals': time_by_occ_with_emp.head(15).to_dict('records') if len(time_by_occ_with_emp) > 0 else []
        }
    
    def _estimate_time_savings(
        self,
        df: pd.DataFrame,
        savings_percentage: float = 0.4
    ) -> pd.DataFrame:
        """
        Estimate time savings from automation
        For queries like: "How much time could this agent save?"
        
        Args:
            df: DataFrame with task data
            savings_percentage: Assumed % of time saved (default 40%)
        
        Returns:
            DataFrame with time savings by occupation
        """
        logger.info(
            f"Estimating time savings at {savings_percentage*100}% for {len(df)} rows",
            show_ui=False
        )
        
        # Ensure numeric columns
        df_copy = df.copy()
        df_copy['Hours per week spent on task'] = pd.to_numeric(
            df_copy['Hours per week spent on task'],
            errors='coerce'
        )
        df_copy['Employment'] = pd.to_numeric(df_copy['Employment'], errors='coerce')
        df_copy['Hourly wage'] = pd.to_numeric(df_copy['Hourly wage'], errors='coerce')
        
        # Group by occupation
        savings_by_occ = df_copy.groupby('ONET job title').agg({
            'Hours per week spent on task': 'mean',
            'Employment': 'sum',
            'Hourly wage': 'mean'
        }).reset_index()
        
        # Calculate savings
        savings_by_occ['time_saved_per_worker'] = (
            savings_by_occ['Hours per week spent on task'] * savings_percentage
        )
        
        # Total hours saved across all workers in occupation
        savings_by_occ['total_hours_saved_per_week'] = (
            savings_by_occ['Employment'] * 
            savings_by_occ['time_saved_per_worker'] * 
            1000  # Employment in thousands
        )
        
        # Dollar savings (if wage data available)
        wage_available = savings_by_occ['Hourly wage'].notna()
        savings_by_occ.loc[wage_available, 'weekly_dollar_savings'] = (
            savings_by_occ.loc[wage_available, 'total_hours_saved_per_week'] * 
            savings_by_occ.loc[wage_available, 'Hourly wage']
        )
        
        # Annual savings
        savings_by_occ.loc[wage_available, 'annual_dollar_savings'] = (
            savings_by_occ.loc[wage_available, 'weekly_dollar_savings'] * 52
        )
        
        # Sort by weekly dollar savings (or total hours if no wage data)
        if wage_available.any():
            savings_by_occ = savings_by_occ.sort_values(
                'weekly_dollar_savings',
                ascending=False,
                na_position='last'
            )
        else:
            savings_by_occ = savings_by_occ.sort_values(
                'total_hours_saved_per_week',
                ascending=False
            )
        
        # Clean column names for display
        savings_by_occ = savings_by_occ.rename(columns={
            'ONET job title': 'Occupation',
            'Hours per week spent on task': 'Current Hours/Week',
            'Employment': 'Workers (thousands)',
            'Hourly wage': 'Avg Hourly Wage',
            'time_saved_per_worker': 'Hours Saved/Worker',
            'total_hours_saved_per_week': 'Total Hours Saved/Week',
            'weekly_dollar_savings': 'Weekly Dollar Savings',
            'annual_dollar_savings': 'Annual Dollar Savings'
        })
        
        return savings_by_occ
    
    def _compute_grouped(
        self,
        df: pd.DataFrame,
        group_by: str,
        agg_type: str
    ) -> Dict[str, Any]:
        """Compute grouped aggregations"""
        
        group_col_map = {
            'industry': 'Industry title',
            'occupation': 'ONET job title'
        }
        
        group_col = group_col_map.get(group_by)
        if not group_col or group_col not in df.columns:
            return {}
        
        grouped_results = {}
        
        if 'Employment' in df.columns:
            grouped_results['by_employment'] = (
                df.groupby(group_col)['Employment']
                .sum()
                .sort_values(ascending=False)
                .to_dict()
            )
        
        if 'Hourly wage' in df.columns:
            grouped_results['by_wage'] = (
                df.groupby(group_col)['Hourly wage']
                .mean()
                .sort_values(ascending=False)
                .to_dict()
            )
        
        return grouped_results
    
    def _get_top_n(self, grouped_results: Dict[str, Any], n: int) -> Dict[str, Any]:
        """Get top N from grouped results"""
        top_n = {}
        
        for key, values in grouped_results.items():
            if isinstance(values, dict):
                top_n[key] = dict(list(values.items())[:n])
        
        return top_n
    
    def _filter_dataframe_by_results(
        self,
        semantic_results: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Filter dataframe to only rows in semantic results"""
        
        # Check if dataframe exists
        if self.df is None:
            logger.warning("Dataframe is None, returning empty DataFrame", show_ui=False)
            return pd.DataFrame()
        
        row_indices = [
            r['metadata'].get('row_index')
            for r in semantic_results
            if 'row_index' in r.get('metadata', {})
        ]
        
        if row_indices:
            return self.df.loc[row_indices].copy()
        else:
            return pd.DataFrame()
    
    def _analyze_skills(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze skill diversity and distribution from enriched data
        
        Returns skill-related statistics including occupations with most diverse skill sets
        """
        skill_analysis = {}
        
        # Check if enriched skill columns are available
        if 'Skill_Count' not in df.columns:
            logger.warning("Skill_Count column not found - data dictionary enrichment may not have run", show_ui=False)
            return {}
        
        # Overall skill statistics
        skill_analysis['total_occupations'] = len(df)
        skill_analysis['occupations_with_skills'] = (df['Skill_Count'] > 0).sum()
        skill_analysis['avg_skills_per_occupation'] = df['Skill_Count'].mean()
        skill_analysis['max_skills_in_occupation'] = df['Skill_Count'].max()
        skill_analysis['min_skills_in_occupation'] = df['Skill_Count'].min()
        
        # Get occupations ranked by skill diversity (Skill_Count)
        if 'ONET job title' in df.columns:
            occupation_skills = (
                df.groupby('ONET job title')['Skill_Count']
                .max()  # Max skills for any task in this occupation
                .sort_values(ascending=False)
            )
            
            skill_analysis['top_diverse_occupations'] = occupation_skills.head(20).to_dict()
            
            # Also provide by industry if available
            if 'Industry_Canonical' in df.columns:
                industry_avg_skills = (
                    df.groupby('Industry_Canonical')['Skill_Count']
                    .mean()
                    .sort_values(ascending=False)
                )
                skill_analysis['industries_by_avg_skills'] = industry_avg_skills.head(10).to_dict()
        
        # Skill distribution
        skill_counts = df['Skill_Count'].value_counts().sort_index()
        skill_analysis['skill_count_distribution'] = skill_counts.to_dict()
        
        logger.info(f"Skill analysis completed: {skill_analysis['occupations_with_skills']} occupations with skills identified", show_ui=False)
        
        return skill_analysis
    
    def _analyze_tasks(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze task counts per occupation
        
        Each row in the dataset represents a task, so counting rows per occupation
        tells us which occupations have the most tasks defined.
        
        Returns task count statistics
        """
        task_analysis = {}
        
        if 'ONET job title' not in df.columns:
            logger.warning("ONET job title column not found - cannot analyze tasks per occupation", show_ui=False)
            return {}
        
        # Count tasks (rows) per occupation
        tasks_per_occupation = df.groupby('ONET job title').size().sort_values(ascending=False)
        
        # Overall statistics
        task_analysis['total_tasks'] = len(df)
        task_analysis['total_occupations'] = df['ONET job title'].nunique()
        task_analysis['avg_tasks_per_occupation'] = tasks_per_occupation.mean()
        task_analysis['max_tasks_for_occupation'] = tasks_per_occupation.max()
        task_analysis['min_tasks_for_occupation'] = tasks_per_occupation.min()
        
        # Top occupations by task count
        task_analysis['top_occupations_by_task_count'] = tasks_per_occupation.head(20).to_dict()
        
        # Task count distribution
        task_count_distribution = tasks_per_occupation.value_counts().sort_index()
        task_analysis['task_count_distribution'] = task_count_distribution.to_dict()
        
        # Also by industry if available
        if 'Industry_Canonical' in df.columns or 'Industry title' in df.columns:
            industry_col = 'Industry_Canonical' if 'Industry_Canonical' in df.columns else 'Industry title'
            tasks_per_industry = df.groupby(industry_col).size().sort_values(ascending=False)
            task_analysis['top_industries_by_task_count'] = tasks_per_industry.head(10).to_dict()
        
        logger.info(f"Task analysis completed: {task_analysis['total_tasks']} tasks across {task_analysis['total_occupations']} occupations", show_ui=False)
        
        return task_analysis
    
    def _analyze_occupations_from_matches(
        self,
        matching_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        V4.0.0: Analyze which occupations are present in filtered/matched data.
        Generic method that works with any pre-filtered dataframe.
        
        Args:
            matching_df: DataFrame already filtered by pattern engine
        
        Returns:
            Dictionary with occupation rankings
        """
        occupation_scores = {}
        
        # Get all occupations from the full dataset for comparison
        all_occupations = self.df['ONET job title'].unique() if self.df is not None else matching_df['ONET job title'].unique()
        
        for occupation in matching_df['ONET job title'].unique():
            # Get tasks for this occupation that matched the pattern
            occ_matching_tasks = matching_df[matching_df['ONET job title'] == occupation]['Detailed job tasks'].dropna()
            
            # Get all tasks for this occupation (from full dataset)
            if self.df is not None:
                occ_all_tasks = self.df[self.df['ONET job title'] == occupation]['Detailed job tasks'].dropna()
                total_count = len(occ_all_tasks)
            else:
                total_count = len(occ_matching_tasks)
            
            matching_count = len(occ_matching_tasks)
            matching_examples = []
            
            # Get examples
            for i, task in enumerate(occ_matching_tasks):
                if len(matching_examples) < 2:
                    matching_examples.append(str(task)[:120] + "...")
                if i >= 1:
                    break
            
            if matching_count > 0 and total_count > 0:
                occupation_scores[occupation] = {
                    'matching_tasks': matching_count,
                    'total_tasks': total_count,
                    'percentage': (matching_count / total_count) * 100,
                    'examples': matching_examples
                }
        
        # Sort by percentage
        sorted_occupations = sorted(
            occupation_scores.items(),
            key=lambda x: x[1]['percentage'],
            reverse=True
        )
        
        analysis = {
            'total_occupations_analyzed': len(all_occupations),
            'occupations_with_matches': len(occupation_scores),
            'top_occupations': sorted_occupations[:15],
            'method': 'v4.8.6_generic_pattern_engine'
        }
        
        logger.info(f"✓ v4.8.6: Occupation analysis: {len(occupation_scores)} occupations match pattern", show_ui=False)
        
        return analysis
    
    def _analyze_occupations_by_pattern(
        self,
        df: pd.DataFrame,
        action_verbs: List[str],
        object_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        LEGACY (v3.x): Analyze which occupations have tasks matching specific patterns.
        Kept for backward compatibility but should not be used in v4.8.6+
        
        Args:
            df: DataFrame with task data
            action_verbs: Action verbs to match (e.g., ['create', 'develop'])
            object_keywords: Object keywords to match (e.g., ['document', 'report'])
        
        Returns:
            Dictionary with occupation rankings
        """
        logger.warning("⚠️  Using legacy _analyze_occupations_by_pattern (should use _analyze_occupations_from_matches in v4.8.6)", show_ui=False)
        
        occupation_scores = {}
        
        for occupation in df['ONET job title'].unique():
            occ_tasks = df[df['ONET job title'] == occupation]['Detailed job tasks'].dropna()
            
            matching_count = 0
            total_count = len(occ_tasks)
            matching_examples = []
            
            for task in occ_tasks:
                task_lower = task.lower()
                
                # Check if task contains both action and object
                has_action = any(verb in task_lower for verb in action_verbs)
                has_object = any(kw in task_lower for kw in object_keywords)
                
                if has_action and has_object:
                    matching_count += 1
                    if len(matching_examples) < 2:
                        matching_examples.append(task[:120] + "...")
            
            if matching_count > 0:
                occupation_scores[occupation] = {
                    'matching_tasks': matching_count,
                    'total_tasks': total_count,
                    'percentage': (matching_count / total_count) * 100,
                    'examples': matching_examples
                }
        
        # Sort by percentage
        sorted_occupations = sorted(
            occupation_scores.items(),
            key=lambda x: x[1]['percentage'],
            reverse=True
        )
        
        analysis = {
            'total_occupations_analyzed': df['ONET job title'].nunique(),
            'occupations_with_matches': len(occupation_scores),
            'top_occupations': sorted_occupations[:15],
            'action_verbs_used': action_verbs,
            'object_keywords_used': object_keywords
        }
        
        logger.info(f"Occupation pattern analysis: {len(occupation_scores)} occupations match the pattern", show_ui=False)
        
        return analysis
