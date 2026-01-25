"""
Hybrid query router for intent classification and routing
Version 4.0.0 - Uses generic TaskPatternEngine for entity detection
"""
from typing import Dict, Any, List, Tuple
from enum import Enum

from app.rag.task_pattern_engine import get_pattern_engine
from app.utils.config import config
from app.utils.logging import logger


class QueryIntent(Enum):
    """Query intent types"""
    SEMANTIC = "semantic"
    COMPUTATIONAL = "computational"
    HYBRID = "hybrid"


class HybridQueryRouter:
    """Routes queries based on intent classification - V4.0.0 with generic pattern engine"""
    
    def __init__(self):
        self.computational_keywords = set(config.COMPUTATIONAL_KEYWORDS)
        self.semantic_keywords = set(config.SEMANTIC_KEYWORDS)
        
        # V4.0.0: Initialize pattern engine for entity detection
        self.pattern_engine = get_pattern_engine()
        logger.info(f"✓ v4.0.2.2: HybridQueryRouter initialized with generic pattern engine", show_ui=False)
    
    def classify_query(self, query: str) -> Tuple[QueryIntent, Dict[str, Any]]:
        """
        Classify query intent and extract parameters
        
        Returns:
            (intent, parameters)
        """
        query_lower = query.lower()
        
        # Count keyword matches
        comp_matches = sum(1 for kw in self.computational_keywords if kw in query_lower)
        sem_matches = sum(1 for kw in self.semantic_keywords if kw in query_lower)
        
        # Log which keywords matched
        matched_comp = [kw for kw in self.computational_keywords if kw in query_lower]
        matched_sem = [kw for kw in self.semantic_keywords if kw in query_lower]
        
        logger.info(f"Query classification: comp_matches={comp_matches} {matched_comp}, sem_matches={sem_matches} {matched_sem}", show_ui=False)
        
        # Extract query parameters
        params = self._extract_parameters(query_lower)
        
        # CRITICAL: Override classification for task-level queries
        # Task queries should be SEMANTIC ONLY - no computational filtering
        task_indicators = ['specific tasks', 'what tasks', 'which tasks', 'tasks that', 
                          'tasks involve', 'task descriptions', 'list of tasks', 'list tasks']
        is_task_query = any(indicator in query_lower for indicator in task_indicators)
        
        # Detect occupation/job queries (different from task queries)
        occupation_indicators = ['what jobs', 'which jobs', 'what occupations', 'which occupations',
                                'jobs that', 'occupations that', 'jobs likely', 'occupations require']
        is_occupation_query = any(indicator in query_lower for indicator in occupation_indicators)
        
        if is_task_query:
            intent = QueryIntent.SEMANTIC
            params['task_query'] = True
            params['top_n'] = 30  # Get more results for better occupation diversity
            logger.info(f"Detected TASK QUERY - forcing SEMANTIC intent with k=30", show_ui=False)
        elif is_occupation_query:
            # Occupation queries should use pattern matching + computational analysis
            intent = QueryIntent.HYBRID
            params['occupation_query'] = True
            logger.info(f"Detected OCCUPATION QUERY - using HYBRID intent", show_ui=False)
        else:
            # Classify intent normally for non-task queries
            if comp_matches > 0 and sem_matches > 0:
                intent = QueryIntent.HYBRID
                logger.debug(f"Query classified as HYBRID (comp:{comp_matches}, sem:{sem_matches})")
            elif comp_matches > sem_matches:
                intent = QueryIntent.COMPUTATIONAL
                logger.debug(f"Query classified as COMPUTATIONAL (matches:{comp_matches})")
            elif sem_matches > 0:
                intent = QueryIntent.SEMANTIC
                logger.debug(f"Query classified as SEMANTIC (matches:{sem_matches})")
            else:
                # Default to hybrid for ambiguous queries
                intent = QueryIntent.HYBRID
                logger.debug("Query classified as HYBRID (default)")
        
        params['intent'] = intent.value
        params['comp_score'] = comp_matches
        params['sem_score'] = sem_matches
        
        return intent, params
    
    def _extract_parameters(self, query_lower: str) -> Dict[str, Any]:
        """Extract query parameters like top N, industry, occupation"""
        params = {}
        
        # Extract top N
        import re
        
        # Patterns for "top N", "top-N", "N most", etc.
        top_patterns = [
            r'top\s+(\d+)',
            r'top-(\d+)',
            r'(\d+)\s+most',
            r'(\d+)\s+highest',
            r'(\d+)\s+largest',
            r'first\s+(\d+)'
        ]
        
        for pattern in top_patterns:
            match = re.search(pattern, query_lower)
            if match:
                params['top_n'] = int(match.group(1))
                break
        
        # Extract aggregation type
        if 'count' in query_lower or 'how many' in query_lower:
            params['aggregation'] = 'count'
        elif 'total' in query_lower or 'sum' in query_lower:
            params['aggregation'] = 'sum'
        elif 'average' in query_lower or 'mean' in query_lower:
            params['aggregation'] = 'average'
        elif 'percentage' in query_lower or 'proportion' in query_lower:
            params['aggregation'] = 'percentage'
        
        # Check for comparison
        if 'compare' in query_lower or 'vs' in query_lower or 'versus' in query_lower:
            params['comparison'] = True
        
        # Check for grouping
        if 'by industry' in query_lower or 'per industry' in query_lower:
            params['group_by'] = 'industry'
        elif 'by occupation' in query_lower or 'per occupation' in query_lower:
            params['group_by'] = 'occupation'
        
        # Detect industry ranking/proportion queries
        industry_ranking_indicators = [
            'what industries', 'which industries', 'industries that', 
            'rich in', 'high proportion', 'highest proportion', 'most common in'
        ]
        if any(indicator in query_lower for indicator in industry_ranking_indicators):
            if 'proportion' in query_lower or 'percentage' in query_lower or 'rich in' in query_lower:
                params['industry_ranking'] = True
                params['aggregation'] = 'percentage'
                params['group_by'] = 'industry'
                # Don't treat as task query even if tasks mentioned
                if 'task_query' in params:
                    del params['task_query']
        
        # REMOVED: CSV export request detection
        # The QueryProcessor already handles CSV correctly by prioritizing response data
        # (occupation_employment, industry_employment) over filtered dataset
        # Setting export_csv=True here causes the WRONG data (filtered dataset) to be returned
        # when the user asks for CSV of the response
        
        # V4.0.0: Generic entity detection using pattern engine (replaces hardcoded keywords)
        detected_category = self.pattern_engine.detect_task_category(query_lower)
        if detected_category:
            # Convert category name to entity parameter
            # e.g., "document_creation" -> "document_creation"
            params['entity'] = detected_category
            params['entity_display_name'] = self.pattern_engine.get_category_config(detected_category).display_name
            logger.info(f"✓ v4.0.2.2: Detected entity: {detected_category}", show_ui=False)
        
        # Detect task-level queries
        task_indicators = ['specific tasks', 'what tasks', 'which tasks', 'tasks that', 
                          'tasks involve', 'task descriptions', 'list of tasks']
        if any(indicator in query_lower for indicator in task_indicators):
            params['task_query'] = True
            # Increase results to 30 for better occupation diversity
            params['top_n'] = 30
        
        return params
    
    def determine_execution_strategy(
        self,
        intent: QueryIntent,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine execution strategy based on intent
        
        Returns:
            strategy dict with execution plan
        """
        strategy = {
            'intent': intent.value,
            'use_vector_search': False,
            'use_aggregations': False,
            'use_pandas': False,
            'needs_llm_synthesis': False,
            'k_results': config.DEFAULT_TOP_K,
            'filters': {}
        }
        
        if intent == QueryIntent.SEMANTIC:
            strategy['use_vector_search'] = True
            strategy['needs_llm_synthesis'] = True
            strategy['k_results'] = params.get('top_n', config.DEFAULT_TOP_K)
        
        elif intent == QueryIntent.COMPUTATIONAL:
            strategy['use_aggregations'] = True
            strategy['use_pandas'] = True
            strategy['needs_llm_synthesis'] = True
            
            # Might still need vector search for filtering
            if params.get('entity'):
                strategy['use_vector_search'] = True
                strategy['k_results'] = 50
        
        elif intent == QueryIntent.HYBRID:
            strategy['use_vector_search'] = True
            strategy['use_aggregations'] = True
            strategy['use_pandas'] = True
            strategy['needs_llm_synthesis'] = True
            strategy['k_results'] = params.get('top_n', config.DEFAULT_TOP_K * 2)
        
        # Add filters if specified
        if params.get('group_by'):
            strategy['group_by'] = params['group_by']
        
        if params.get('export_csv'):
            strategy['export_csv'] = True
        
        strategy['params'] = params
        
        logger.info(f"Execution strategy: vector={strategy['use_vector_search']}, agg={strategy['use_aggregations']}, pandas={strategy['use_pandas']}", show_ui=False)
        
        return strategy
    
    def route_query(self, query: str) -> Dict[str, Any]:
        """
        Main routing function - classifies and determines strategy
        
        Returns:
            Complete routing information
        """
        intent, params = self.classify_query(query)
        strategy = self.determine_execution_strategy(intent, params)
        
        routing_info = {
            'query': query,
            'intent': intent.value,
            'params': params,
            'strategy': strategy
        }
        
        logger.info(f"Query routed: intent={intent.value}", show_ui=False)
        
        return routing_info
