"""
Retriever that orchestrates hybrid semantic and computational retrieval
"""
import pandas as pd
from typing import Dict, List, Any, Optional

from app.rag.vector_store import VectorStore
from app.rag.hybrid_router import HybridQueryRouter, QueryIntent
from app.analytics.aggregations import DataAggregator
from app.utils.logging import logger


class HybridRetriever:
    """Orchestrates hybrid retrieval combining semantic search and computational queries"""
    
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
    
    def retrieve(
        self,
        query: str,
        k: int = 10
    ) -> Dict[str, Any]:
        """
        Main retrieval function
        
        Returns:
            Retrieved results with metadata
        """
        # Route the query
        routing_info = self.router.route_query(query)
        strategy = routing_info['strategy']
        
        results = {
            'query': query,
            'routing_info': routing_info,
            'semantic_results': [],
            'computational_results': {},
            'filtered_dataframe': None,
            'metadata': {}
        }
        
        # Execute semantic search if needed
        if strategy['use_vector_search']:
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
                query,
                routing_info['params'],
                semantic_results=results['semantic_results']
            )
            # Ensure we have a dict, not None
            results['computational_results'] = computational_results if computational_results is not None else {}
            logger.debug(f"Computed {len(results['computational_results'])} aggregations")
        
        # Filter dataframe based on semantic results if needed
        if results['semantic_results'] and strategy['use_pandas']:
            filtered_df = self._filter_dataframe_by_results(results['semantic_results'])
            results['filtered_dataframe'] = filtered_df
            if filtered_df is not None and not filtered_df.empty:
                results['metadata']['filtered_rows'] = len(filtered_df)
            else:
                results['metadata']['filtered_rows'] = 0
        
        results['metadata']['total_results'] = (
            len(results['semantic_results']) +
            len(results['computational_results'])
        )
        
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
        
        # Special handling for "what jobs" pattern matching queries
        query_lower = query.lower()
        pattern_indicators = ['what jobs', 'which jobs', 'what occupations', 'which occupations', 
                             'list jobs', 'list occupations', 'jobs that', 'occupations that']
        
        pattern_detected = any(indicator in query_lower for indicator in pattern_indicators)
        logger.info(f"Pattern matching check: pattern_detected={pattern_detected}", show_ui=False)
        
        if pattern_detected:
            action_verbs_present = ['create', 'develop', 'design', 'prepare', 'write', 'produce']
            object_keywords_present = ['document', 'report', 'spreadsheet', 'file', 'presentation', 
                                      'drawing', 'plan', 'specification', 'program', 'model']
            
            has_action = any(verb in query_lower for verb in action_verbs_present)
            has_object = any(doc in query_lower for doc in object_keywords_present)
            
            logger.info(f"Pattern matching: has_action={has_action}, has_object={has_object}", show_ui=False)
            
            # Detect document creation queries
            if has_action and has_object:
                logger.info("Pattern match FOUND - triggering occupation analysis", show_ui=False)
                
                action_verbs = ['create', 'develop', 'design', 'prepare', 'write', 'produce', 
                               'generate', 'build', 'draft', 'compose', 'formulate']
                object_keywords = ['document', 'documents', 'report', 'reports', 'spreadsheet', 'spreadsheets',
                                  'file', 'files', 'drawing', 'drawings', 'plan', 'plans', 'specification',
                                  'specifications', 'presentation', 'presentations', 'program', 'programs',
                                  'model', 'models', 'diagram', 'chart', 'graph', 'blueprint', 'schematic']
                
                # CRITICAL: Use full dataframe, not filtered subset
                # Pattern matching needs to analyze ALL occupations, not just semantically similar ones
                logger.info(f"Analyzing {self.df['ONET job title'].nunique()} occupations for pattern", show_ui=False)
                
                occupation_analysis = self._analyze_occupations_by_pattern(
                    self.df, action_verbs, object_keywords
                )
                computational_results['occupation_pattern_analysis'] = occupation_analysis
                logger.info(f"Pattern analysis complete: {len(occupation_analysis.get('top_occupations', []))} occupations matched", show_ui=False)
                
                # If this is also an employment query, compute employment for matching occupations
                if 'employment' in query_lower or 'total' in query_lower or 'how many' in query_lower:
                    matching_occupations = [occ for occ, _ in occupation_analysis.get('top_occupations', [])]
                    if matching_occupations:
                        logger.info(f"Computing employment for {len(matching_occupations)} matching occupations", show_ui=False)
                        
                        # Get employment for matching occupations only
                        matching_occ_employment = self.df[
                            self.df['ONET job title'].isin(matching_occupations)
                        ].groupby('ONET job title')['Employment'].first()
                        
                        total_employment = matching_occ_employment.sum()
                        
                        computational_results['employment_for_matching_occupations'] = {
                            'total_employment': float(total_employment),
                            'occupations_count': len(matching_occupations),
                            'per_occupation': {
                                occ: float(emp) 
                                for occ, emp in matching_occ_employment.items()
                            },
                            'note': 'Employment aggregated at occupation level, not task level'
                        }
                        logger.info(f"Employment for matching occupations: {total_employment:.2f} across {len(matching_occupations)} occupations", show_ui=False)
        
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
                # Get unique employment per occupation (take first value for each occupation)
                # This represents the actual occupation-level employment
                unique_employment_per_occ = df.groupby('ONET job title')['Employment'].first()
                totals['total_employment'] = float(unique_employment_per_occ.sum())
                totals['employment_note'] = f"Employment aggregated at occupation level ({len(unique_employment_per_occ)} occupations)"
                
                # Also include task-level sum for reference (incorrect but informative)
                task_level_sum = float(df['Employment'].sum())
                totals['task_level_employment_sum'] = task_level_sum
                totals['warning'] = "Note: task_level_employment_sum is for reference only and should NOT be used"
                
                logger.info(f"Employment computed: {len(unique_employment_per_occ)} occupations, total={totals['total_employment']:.2f}", show_ui=False)
            else:
                # Fallback if occupation column not available
                totals['total_employment'] = float(df['Employment'].sum())
                logger.warning("Computing employment without occupation grouping - may be inaccurate", show_ui=False)
        
        if 'Hours per week spent on task' in df.columns:
            totals['total_task_hours'] = float(df['Hours per week spent on task'].sum())
        
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
    
    def _analyze_occupations_by_pattern(
        self,
        df: pd.DataFrame,
        action_verbs: List[str],
        object_keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze which occupations have tasks matching specific patterns
        
        Args:
            df: DataFrame with task data
            action_verbs: Action verbs to match (e.g., ['create', 'develop'])
            object_keywords: Object keywords to match (e.g., ['document', 'report'])
        
        Returns:
            Dictionary with occupation rankings
        """
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
