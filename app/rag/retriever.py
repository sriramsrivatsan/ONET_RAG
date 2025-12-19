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
            results['semantic_results'] = semantic_results
            logger.debug(f"Retrieved {len(semantic_results)} semantic results")
        
        # Execute computational queries if needed
        if strategy['use_aggregations'] or strategy['use_pandas']:
            computational_results = self._computational_retrieval(
                query,
                routing_info['params'],
                semantic_results=results['semantic_results']
            )
            results['computational_results'] = computational_results
            logger.debug(f"Computed {len(computational_results)} aggregations")
        
        # Filter dataframe based on semantic results if needed
        if results['semantic_results'] and strategy['use_pandas']:
            filtered_df = self._filter_dataframe_by_results(results['semantic_results'])
            results['filtered_dataframe'] = filtered_df
            results['metadata']['filtered_rows'] = len(filtered_df)
        
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
        
        return computational_results
    
    def _compute_counts(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute counts"""
        counts = {}
        
        counts['total_rows'] = len(df)
        
        if 'Industry title' in df.columns:
            counts['unique_industries'] = df['Industry title'].nunique()
        
        if 'ONET job title' in df.columns:
            counts['unique_occupations'] = df['ONET job title'].nunique()
        
        return counts
    
    def _compute_totals(self, df: pd.DataFrame, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compute totals"""
        totals = {}
        
        if 'Employment' in df.columns:
            totals['total_employment'] = float(df['Employment'].sum())
        
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
        
        row_indices = [
            r['metadata'].get('row_index')
            for r in semantic_results
            if 'row_index' in r.get('metadata', {})
        ]
        
        if row_indices:
            return self.df.loc[row_indices].copy()
        else:
            return pd.DataFrame()
