"""
Universal CSV Generator for Labor RAG v4.8.5
Generates CSV for ANY query response using 3-tier strategy
"""
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.utils.logging import logger


class UniversalCSVGenerator:
    """
    Generate CSV from any query response
    Three-tier strategy ensures CSV is NEVER None
    
    Tier 1: Extract from computational results (preferred - structured data)
    Tier 2: Convert semantic results to CSV (common - task/occupation details)
    Tier 3: Create fallback summary (rare - last resort for narrative responses)
    """
    
    def __init__(self):
        """Initialize CSV generator"""
        self.generation_stats = {
            'tier1_count': 0,
            'tier2_count': 0,
            'tier3_count': 0,
            'total_generated': 0
        }
    
    def generate(
        self,
        query: str,
        semantic_results: List[Dict[str, Any]],
        computational_results: Dict[str, Any],
        routing_info: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Generate CSV for query response
        
        Args:
            query: Original user query
            semantic_results: List of semantic search results
            computational_results: Dict of computational analysis results
            routing_info: Query routing information
        
        Returns:
            DataFrame ready for CSV export (NEVER None)
        """
        
        logger.info(f"🔄 Generating CSV for query: {query[:50]}...", show_ui=False)
        
        # Try Tier 1: Computational results (preferred)
        csv_df = self._tier1_computational(computational_results)
        if csv_df is not None and not csv_df.empty:
            self.generation_stats['tier1_count'] += 1
            self.generation_stats['total_generated'] += 1
            logger.info(
                f"✅ Tier 1: Generated CSV from computational results "
                f"({len(csv_df)} rows × {len(csv_df.columns)} cols)",
                show_ui=False
            )
            return self._finalize_csv(csv_df, query, 'computational')
        
        # Try Tier 2: Semantic results
        csv_df = self._tier2_semantic(semantic_results)
        if csv_df is not None and not csv_df.empty:
            self.generation_stats['tier2_count'] += 1
            self.generation_stats['total_generated'] += 1
            logger.info(
                f"✅ Tier 2: Generated CSV from semantic results "
                f"({len(csv_df)} rows × {len(csv_df.columns)} cols)",
                show_ui=False
            )
            return self._finalize_csv(csv_df, query, 'semantic')
        
        # Tier 3: Fallback summary
        csv_df = self._tier3_fallback(query, routing_info)
        self.generation_stats['tier3_count'] += 1
        self.generation_stats['total_generated'] += 1
        logger.warning(
            f"⚠️ Tier 3: Using fallback CSV (no structured data available)",
            show_ui=False
        )
        return self._finalize_csv(csv_df, query, 'fallback')
    
    def _tier1_computational(
        self,
        computational_results: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """
        Extract CSV from computational results
        
        Priority order:
        1. savings_analysis (highest value - automation analysis)
        2. occupation_employment (occupation summaries)
        3. industry_employment (industry analysis)
        4. industry_proportions (industry breakdowns)
        5. occupation_pattern_analysis (pattern matching)
        6. time_analysis (time statistics)
        7. wage_analysis (wage data)
        """
        
        if not computational_results or len(computational_results) == 0:
            logger.debug("No computational results available", show_ui=False)
            return None
        
        # Define extraction priority and methods
        extractors = [
            ('savings_analysis', self._extract_savings),
            ('occupation_employment', self._extract_occupation_employment),
            ('industry_employment', self._extract_industry_employment),
            ('industry_proportions', self._extract_industry_proportions),
            ('occupation_pattern_analysis', self._extract_pattern_analysis),
            ('time_analysis', self._extract_time_analysis),
            ('wage_analysis', self._extract_wage_analysis),
        ]
        
        for key, extractor in extractors:
            if key in computational_results:
                try:
                    df = extractor(computational_results[key])
                    if df is not None and not df.empty:
                        logger.debug(
                            f"Extracted from {key}: {len(df)} rows",
                            show_ui=False
                        )
                        return df
                except Exception as e:
                    logger.error(
                        f"Error extracting {key}: {e}",
                        show_ui=False
                    )
                    continue
        
        logger.debug("No usable computational results found", show_ui=False)
        return None
    
    def _tier2_semantic(
        self,
        semantic_results: List[Dict[str, Any]]
    ) -> Optional[pd.DataFrame]:
        """
        Convert semantic results to CSV
        
        Handles:
        - Task detail results (most common)
        - Occupation detail results
        - General semantic matches
        """
        
        if not semantic_results or len(semantic_results) == 0:
            logger.debug("No semantic results available", show_ui=False)
            return None
        
        logger.debug(
            f"Converting {len(semantic_results)} semantic results to CSV",
            show_ui=False
        )
        
        rows = []
        for i, result in enumerate(semantic_results, 1):
            # Base row with rank and content
            row = {
                'Rank': i,
                'Content': result.get('text', ''),
                'Relevance Score': round(result.get('score', 0.0), 3),
            }
            
            # Extract metadata if available
            metadata = result.get('metadata', {})
            
            # Common metadata fields
            if 'onet_job_title' in metadata:
                row['Occupation'] = metadata['onet_job_title']
            
            if 'hours_per_week_spent_on_task' in metadata:
                hours = metadata['hours_per_week_spent_on_task']
                if hours is not None:
                    try:
                        row['Hours per Week'] = round(float(hours), 1)
                    except (ValueError, TypeError):
                        pass
            
            if 'industries_count' in metadata:
                try:
                    row['Industries Count'] = int(metadata['industries_count'])
                except (ValueError, TypeError):
                    pass
            
            if 'employment' in metadata:
                emp = metadata['employment']
                if emp is not None:
                    try:
                        row['Employment (thousands)'] = round(float(emp), 1)
                    except (ValueError, TypeError):
                        pass
            
            if 'hourly_wage' in metadata:
                wage = metadata['hourly_wage']
                if wage is not None:
                    try:
                        row['Hourly Wage ($)'] = round(float(wage), 2)
                    except (ValueError, TypeError):
                        pass
            
            if 'industry_title' in metadata:
                row['Industry'] = metadata['industry_title']
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Clean up: remove columns that are all NaN or empty
        df = df.dropna(axis=1, how='all')
        
        # Clean up: replace NaN with empty string for better CSV readability
        df = df.fillna('')
        
        logger.info(
            f"Created semantic CSV: {len(df)} rows, {len(df.columns)} columns",
            show_ui=False
        )
        
        return df
    
    def _tier3_fallback(
        self,
        query: str,
        routing_info: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Create fallback CSV when no structured data available
        
        This ensures CSV is NEVER None
        Provides query metadata for audit trail
        """
        
        fallback_data = {
            'Query': [query],
            'Query Type': [routing_info.get('strategy', 'unknown')],
            'Category': [routing_info.get('category', 'unknown')],
            'Timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            'Data Type': ['Unstructured narrative response'],
            'Note': ['Full response available in chat interface. This CSV contains query metadata only.']
        }
        
        logger.warning(
            "Using fallback CSV - query had no structured data",
            show_ui=False
        )
        
        return pd.DataFrame(fallback_data)
    
    def _finalize_csv(
        self,
        df: pd.DataFrame,
        query: str,
        source: str
    ) -> pd.DataFrame:
        """
        Finalize CSV before returning
        
        Args:
            df: DataFrame to finalize
            query: Original query
            source: Data source (computational/semantic/fallback)
        
        Returns:
            Finalized DataFrame
        """
        
        # Validate
        if df is None or df.empty:
            logger.error("Cannot finalize empty DataFrame!", show_ui=False)
            # Return minimal fallback
            return pd.DataFrame({
                'Query': [query],
                'Error': ['CSV generation failed - empty data'],
                'Timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            })
        
        # Optional: Add metadata columns in future
        # For now, just return as-is
        
        return df
    
    # =========================================================================
    # Tier 1 Extractor Methods
    # =========================================================================
    
    def _extract_savings(self, data: Any) -> Optional[pd.DataFrame]:
        """Extract savings analysis data"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Convert dict to list of dicts or DataFrame
            if 'occupations' in data:
                return pd.DataFrame(data['occupations'])
        return None
    
    def _extract_occupation_employment(self, data: Any) -> Optional[pd.DataFrame]:
        """Extract occupation employment data"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return None
    
    def _extract_industry_employment(self, data: Any) -> Optional[pd.DataFrame]:
        """Extract industry employment data"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return None
    
    def _extract_industry_proportions(self, data: Any) -> Optional[pd.DataFrame]:
        """Extract industry proportions data"""
        if isinstance(data, dict) and 'industries' in data:
            industries_data = data['industries']
            if isinstance(industries_data, list):
                return pd.DataFrame(industries_data)
            elif isinstance(industries_data, pd.DataFrame):
                return industries_data
        elif isinstance(data, pd.DataFrame):
            return data
        return None
    
    def _extract_pattern_analysis(self, data: Any) -> Optional[pd.DataFrame]:
        """Extract pattern analysis data"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try to extract meaningful structure
            if 'patterns' in data:
                return pd.DataFrame(data['patterns'])
        return None
    
    def _extract_time_analysis(self, data: Any) -> Optional[pd.DataFrame]:
        """Extract time analysis data"""
        if isinstance(data, dict):
            # Convert dict to single-row DataFrame
            return pd.DataFrame([data])
        elif isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return None
    
    def _extract_wage_analysis(self, data: Any) -> Optional[pd.DataFrame]:
        """Extract wage analysis data"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, list):
            return pd.DataFrame(data)
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get generation statistics for monitoring"""
        return self.generation_stats.copy()
