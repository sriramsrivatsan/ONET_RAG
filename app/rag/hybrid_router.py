"""
Hybrid query router for intent classification and routing
"""
from typing import Dict, Any, List, Tuple
from enum import Enum

from app.utils.config import config
from app.utils.logging import logger


class QueryIntent(Enum):
    """Query intent types"""
    SEMANTIC = "semantic"
    COMPUTATIONAL = "computational"
    HYBRID = "hybrid"


class HybridQueryRouter:
    """Routes queries based on intent classification"""
    
    def __init__(self):
        self.computational_keywords = set(config.COMPUTATIONAL_KEYWORDS)
        self.semantic_keywords = set(config.SEMANTIC_KEYWORDS)
    
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
        
        if is_task_query:
            intent = QueryIntent.SEMANTIC
            params['task_query'] = True
            params['top_n'] = 20  # Get more results for task queries
            logger.info(f"Detected TASK QUERY - forcing SEMANTIC intent with k=20", show_ui=False)
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
        
        # Check for CSV export request
        if 'csv' in query_lower or 'export' in query_lower or 'download' in query_lower:
            params['export_csv'] = True
        
        # Check for specific entities mentioned
        if 'digital document' in query_lower:
            params['entity'] = 'digital_document'
        elif 'customer service' in query_lower:
            params['entity'] = 'customer_service'
        elif 'agentic' in query_lower or 'agent' in query_lower:
            params['entity'] = 'ai_agent'
        
        # Detect task-level queries
        task_indicators = ['specific tasks', 'what tasks', 'which tasks', 'tasks that', 
                          'tasks involve', 'task descriptions', 'list of tasks']
        if any(indicator in query_lower for indicator in task_indicators):
            params['task_query'] = True
            # Increase results for better task coverage
            params['top_n'] = params.get('top_n', 15)
        
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
