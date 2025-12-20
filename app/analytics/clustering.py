"""
Clustering module for Labor Market data
Enhanced with data dictionary for canonical term clustering
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
import streamlit as st

from app.utils.logging import logger
from app.utils.config import config


class LaborMarketClusterer:
    """Handles clustering of labor market data with dictionary-based enhancements"""
    
    def __init__(self, df: pd.DataFrame, use_enriched_fields: bool = True):
        self.df = df
        self.cluster_results: Dict[str, Any] = {}
        self.vectorizers: Dict[str, TfidfVectorizer] = {}
        self.use_enriched_fields = use_enriched_fields
        
        # Check if enriched fields are available
        self.has_enriched_fields = self._check_enriched_fields()
        if self.has_enriched_fields:
            logger.info("✓ Using enriched fields for improved clustering", show_ui=True)
    
    def _check_enriched_fields(self) -> bool:
        """Check if data dictionary enriched fields are available"""
        enriched_columns = [
            'Industry_Canonical', 'Canonical_Activities', 
            'Extracted_Skills', 'Occupation_Major_Group'
        ]
        return any(col in self.df.columns for col in enriched_columns)
    
    def _get_enriched_field_name(self, field_name: str) -> Optional[str]:
        """
        Map a field name to its enriched version if available
        
        Args:
            field_name: Original field name
            
        Returns:
            Enriched field name if available, None otherwise
        """
        if not self.use_enriched_fields or not self.has_enriched_fields:
            return None
        
        # Mapping of original fields to enriched versions
        field_mapping = {
            'Detailed work activities': 'Canonical_Activities',
            'Industry title': 'Industry_Canonical',
            'ONET job title': 'Occupation_Major_Group'
        }
        
        enriched = field_mapping.get(field_name)
        
        # Only return if the enriched field actually exists in dataframe
        if enriched and enriched in self.df.columns:
            return enriched
        
        return None
    
    def perform_all_clustering(self) -> Dict[str, Any]:
        """Perform all clustering operations"""
        logger.info("Starting clustering operations", show_ui=True)
        
        # Cluster tasks
        if 'Detailed job tasks' in self.df.columns:
            task_results = self._cluster_text_field(
                field_name='Detailed job tasks',
                n_clusters=config.N_CLUSTERS_TASKS,
                cluster_prefix='task'
            )
            self.cluster_results['tasks'] = task_results
            logger.info(f"✓ Clustered tasks into {config.N_CLUSTERS_TASKS} groups", show_ui=True)
        
        # Cluster work activities
        if 'Detailed work activities' in self.df.columns:
            activity_results = self._cluster_text_field(
                field_name='Detailed work activities',
                n_clusters=config.N_CLUSTERS_ROLES,
                cluster_prefix='activity'
            )
            self.cluster_results['activities'] = activity_results
            logger.info(f"✓ Clustered work activities into {config.N_CLUSTERS_ROLES} groups", show_ui=True)
        
        # Cluster occupations
        if 'ONET job title' in self.df.columns:
            occ_results = self._cluster_occupation_titles()
            self.cluster_results['occupations'] = occ_results
            logger.info(f"✓ Clustered occupations into {config.N_CLUSTERS_OCCUPATIONS} groups", show_ui=True)
        
        # Generate cluster summaries
        self._generate_cluster_summaries()
        
        logger.info("✓ All clustering complete", show_ui=True)
        
        return self.cluster_results
    
    def _cluster_text_field(
        self,
        field_name: str,
        n_clusters: int,
        cluster_prefix: str,
        sample_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Cluster a text field using TF-IDF + K-Means with dictionary enhancement"""
        
        # Check if we should use enriched field instead
        enriched_field = self._get_enriched_field_name(field_name)
        use_field = enriched_field if enriched_field else field_name
        
        if enriched_field:
            logger.info(f"Using enriched field '{enriched_field}' for clustering", show_ui=False)
        
        # Get non-null values
        if use_field in self.df.columns:
            # Handle different field types
            if use_field == 'Canonical_Activities' and use_field in self.df.columns:
                # This is a list field - join the canonical activities
                texts = self.df[use_field].dropna().apply(
                    lambda x: ' '.join(x) if isinstance(x, list) else str(x)
                ).tolist()
            else:
                texts = self.df[use_field].dropna().astype(str).tolist()
        else:
            texts = self.df[field_name].dropna().astype(str).tolist()
        
        if len(texts) == 0:
            return {'cluster_ids': [], 'cluster_labels': {}, 'centers': None}
        
        # Sample if dataset is too large
        if sample_size and len(texts) > sample_size:
            sample_indices = np.random.choice(len(texts), sample_size, replace=False)
            texts_sample = [texts[i] for i in sample_indices]
        else:
            texts_sample = texts
            sample_indices = None
        
        # TF-IDF vectorization with adaptive parameters
        # Adjust min_df based on dataset size to avoid pruning all terms
        dataset_size = len(texts_sample)
        adaptive_min_df = 1 if dataset_size < 100 else max(1, min(2, int(dataset_size * 0.01)))
        adaptive_max_df = 0.95 if dataset_size < 100 else 0.8
        
        vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            min_df=adaptive_min_df,
            max_df=adaptive_max_df,
            stop_words='english'
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(texts_sample)
            
            # Check if we got any features
            if tfidf_matrix.shape[1] == 0:
                logger.warning(f"No features extracted for {field_name}, using simpler vectorization", show_ui=True)
                # Fallback: use very permissive settings
                vectorizer = TfidfVectorizer(
                    max_features=100,
                    ngram_range=(1, 1),
                    min_df=1,
                    max_df=1.0,
                    stop_words=None
                )
                tfidf_matrix = vectorizer.fit_transform(texts_sample)
                
        except ValueError as e:
            logger.error(f"Vectorization failed for {field_name}: {str(e)}", show_ui=True)
            # Return empty results if vectorization fails completely
            return {
                'cluster_ids': [-1] * len(texts),
                'cluster_labels': {0: f"{cluster_prefix}_unclustered"},
                'n_clusters': 1,
                'cluster_sizes': {0: len(texts)}
            }
        self.vectorizers[cluster_prefix] = vectorizer
        
        # Dimensionality reduction if needed
        if tfidf_matrix.shape[1] > 100:
            svd = TruncatedSVD(n_components=100, random_state=42)
            tfidf_matrix = svd.fit_transform(tfidf_matrix)
        
        # K-Means clustering
        if len(texts_sample) > 10000:
            kmeans = MiniBatchKMeans(
                n_clusters=n_clusters,
                random_state=42,
                batch_size=1000,
                n_init=3
            )
        else:
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )
        
        cluster_ids = kmeans.fit_predict(tfidf_matrix)
        
        # Assign cluster IDs back to full dataset
        if sample_indices is not None:
            full_cluster_ids = np.full(len(texts), -1)
            full_cluster_ids[sample_indices] = cluster_ids
            # Predict for remaining points
            remaining_indices = [i for i in range(len(texts)) if i not in sample_indices]
            if remaining_indices:
                remaining_texts = [texts[i] for i in remaining_indices]
                remaining_tfidf = vectorizer.transform(remaining_texts)
                if tfidf_matrix.shape[1] > 100:
                    remaining_tfidf = svd.transform(remaining_tfidf)
                remaining_clusters = kmeans.predict(remaining_tfidf)
                full_cluster_ids[remaining_indices] = remaining_clusters
            cluster_ids = full_cluster_ids
        
        # Create cluster labels (will be enhanced with LLM later)
        cluster_labels = {}
        for cluster_id in range(n_clusters):
            cluster_texts = [texts[i] for i in range(len(texts)) if cluster_ids[i] == cluster_id]
            if cluster_texts:
                # Generate simple label from top terms
                cluster_tfidf = vectorizer.transform(cluster_texts[:100])
                feature_names = vectorizer.get_feature_names_out()
                top_indices = cluster_tfidf.mean(axis=0).A1.argsort()[-5:][::-1]
                top_terms = [feature_names[i] for i in top_indices]
                cluster_labels[cluster_id] = f"{cluster_prefix}_{cluster_id}: {', '.join(top_terms[:3])}"
        
        # Add cluster IDs to dataframe
        cluster_col_name = f'{cluster_prefix}_cluster_id'
        self.df[cluster_col_name] = -1
        valid_indices = self.df[field_name].notna()
        self.df.loc[valid_indices, cluster_col_name] = cluster_ids
        
        return {
            'cluster_ids': cluster_ids.tolist(),
            'cluster_labels': cluster_labels,
            'n_clusters': n_clusters,
            'cluster_sizes': pd.Series(cluster_ids).value_counts().to_dict()
        }
    
    def _cluster_occupation_titles(self) -> Dict[str, Any]:
        """Cluster occupation titles"""
        return self._cluster_text_field(
            field_name='ONET job title',
            n_clusters=config.N_CLUSTERS_OCCUPATIONS,
            cluster_prefix='occupation',
            sample_size=config.CLUSTERING_SAMPLE_SIZE
        )
    
    def _generate_cluster_summaries(self):
        """Generate human-readable cluster summaries"""
        for cluster_type, results in self.cluster_results.items():
            cluster_labels = results.get('cluster_labels', {})
            
            # Store summaries for later LLM enhancement
            results['summaries'] = {}
            for cluster_id, label in cluster_labels.items():
                results['summaries'][cluster_id] = {
                    'label': label,
                    'size': results.get('cluster_sizes', {}).get(cluster_id, 0),
                    'description': f"Cluster {cluster_id} of {cluster_type}"
                }
    
    def get_cluster_membership(self, row_index: int) -> Dict[str, int]:
        """Get cluster memberships for a specific row"""
        memberships = {}
        
        if 'task_cluster_id' in self.df.columns:
            memberships['task_cluster'] = self.df.loc[row_index, 'task_cluster_id']
        
        if 'activity_cluster_id' in self.df.columns:
            memberships['activity_cluster'] = self.df.loc[row_index, 'activity_cluster_id']
        
        if 'occupation_cluster_id' in self.df.columns:
            memberships['occupation_cluster'] = self.df.loc[row_index, 'occupation_cluster_id']
        
        return memberships
    
    def get_similar_occupations_by_cluster(self, occupation: str, top_n: int = 10) -> List[str]:
        """Get similar occupations based on cluster membership"""
        if 'ONET job title' not in self.df.columns or 'occupation_cluster_id' not in self.df.columns:
            return []
        
        # Find the occupation's cluster
        occ_rows = self.df[self.df['ONET job title'] == occupation]
        if occ_rows.empty:
            return []
        
        cluster_id = occ_rows.iloc[0]['occupation_cluster_id']
        
        # Get other occupations in the same cluster
        same_cluster = self.df[self.df['occupation_cluster_id'] == cluster_id]
        similar_occs = same_cluster['ONET job title'].unique().tolist()
        
        # Remove the query occupation
        similar_occs = [occ for occ in similar_occs if occ != occupation]
        
        return similar_occs[:top_n]
    
    def get_cluster_statistics(self) -> Dict[str, Any]:
        """Get statistics about clusters"""
        stats = {}
        
        for cluster_type, results in self.cluster_results.items():
            stats[cluster_type] = {
                'n_clusters': results.get('n_clusters', 0),
                'cluster_sizes': results.get('cluster_sizes', {}),
                'avg_cluster_size': np.mean(list(results.get('cluster_sizes', {}).values())) if results.get('cluster_sizes') else 0,
                'largest_cluster': max(results.get('cluster_sizes', {}).values()) if results.get('cluster_sizes') else 0,
                'smallest_cluster': min(results.get('cluster_sizes', {}).values()) if results.get('cluster_sizes') else 0
            }
        
        return stats
