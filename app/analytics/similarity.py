"""
Similarity analysis for cross-industry comparisons
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.utils.logging import logger


class SimilarityAnalyzer:
    """Handles similarity analysis across industries and occupations"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.similarity_matrices: Dict[str, np.ndarray] = {}
        self.vectorizers: Dict[str, TfidfVectorizer] = {}
    
    def compute_cross_industry_task_similarity(self) -> Dict[str, Any]:
        """Compute task similarity across industries"""
        logger.info("Computing cross-industry task similarity", show_ui=True)
        
        if 'Industry title' not in self.df.columns or 'Detailed job tasks' not in self.df.columns:
            return {}
        
        # Group tasks by industry
        industry_tasks = self.df.groupby('Industry title')['Detailed job tasks'].apply(
            lambda x: ' '.join(x.dropna().astype(str))
        )
        
        if len(industry_tasks) < 2:
            return {}
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=200,
            ngram_range=(1, 2),
            min_df=1,
            stop_words='english'
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(industry_tasks.values)
        except ValueError as e:
            logger.warning(f"Vectorization failed in cross-industry similarity: {str(e)}", show_ui=False)
            return {
                'industry_similarity_matrix': [],
                'industries': [],
                'top_similar_pairs': [],
                'all_similar_pairs': []
            }
        
        self.vectorizers['industry_tasks'] = vectorizer
        
        # Compute cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        self.similarity_matrices['industry_tasks'] = similarity_matrix
        
        # Find most similar industry pairs
        industries = industry_tasks.index.tolist()
        similar_pairs = []
        
        for i in range(len(industries)):
            for j in range(i + 1, len(industries)):
                similarity = similarity_matrix[i, j]
                if similarity > 0.1:  # Threshold for meaningful similarity
                    similar_pairs.append({
                        'industry_1': industries[i],
                        'industry_2': industries[j],
                        'similarity': float(similarity)
                    })
        
        # Sort by similarity
        similar_pairs = sorted(similar_pairs, key=lambda x: x['similarity'], reverse=True)
        
        logger.info(f"✓ Found {len(similar_pairs)} similar industry pairs", show_ui=True)
        
        return {
            'industry_similarity_matrix': similarity_matrix.tolist(),
            'industries': industries,
            'top_similar_pairs': similar_pairs[:20],
            'all_similar_pairs': similar_pairs
        }
    
    def find_similar_tasks_across_industries(
        self,
        industry1: str,
        industry2: str,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Find similar tasks between two industries"""
        
        if 'Industry title' not in self.df.columns or 'Detailed job tasks_list' not in self.df.columns:
            return []
        
        # Get tasks from both industries
        ind1_tasks = self.df[self.df['Industry title'] == industry1]['Detailed job tasks_list'].explode().dropna().unique()
        ind2_tasks = self.df[self.df['Industry title'] == industry2]['Detailed job tasks_list'].explode().dropna().unique()
        
        if len(ind1_tasks) == 0 or len(ind2_tasks) == 0:
            return []
        
        # Create TF-IDF vectors
        all_tasks = list(ind1_tasks) + list(ind2_tasks)
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english')
        
        try:
            tfidf_matrix = vectorizer.fit_transform(all_tasks)
        except:
            return []
        
        # Compute similarity
        n_ind1 = len(ind1_tasks)
        ind1_vectors = tfidf_matrix[:n_ind1]
        ind2_vectors = tfidf_matrix[n_ind1:]
        
        similarity_matrix = cosine_similarity(ind1_vectors, ind2_vectors)
        
        # Find top similar task pairs
        similar_tasks = []
        for i in range(similarity_matrix.shape[0]):
            for j in range(similarity_matrix.shape[1]):
                similarity = similarity_matrix[i, j]
                if similarity > 0.3:  # Threshold
                    similar_tasks.append({
                        'task_industry1': ind1_tasks[i],
                        'task_industry2': ind2_tasks[j],
                        'similarity': float(similarity)
                    })
        
        # Sort and return top N
        similar_tasks = sorted(similar_tasks, key=lambda x: x['similarity'], reverse=True)
        return similar_tasks[:top_n]
    
    def find_common_skills_across_occupations(
        self,
        occupation_list: List[str]
    ) -> Dict[str, Any]:
        """Find common skills across multiple occupations"""
        
        if 'ONET job title' not in self.df.columns:
            return {}
        
        # Filter to specified occupations
        occ_data = self.df[self.df['ONET job title'].isin(occupation_list)]
        
        if occ_data.empty:
            return {}
        
        # Extract all tasks
        all_tasks = []
        for occ in occupation_list:
            occ_tasks = occ_data[occ_data['ONET job title'] == occ]['Detailed job tasks_list'].explode().dropna().tolist()
            all_tasks.extend(occ_tasks)
        
        # Find common tasks (appearing in multiple occupations)
        from collections import Counter
        task_counts = Counter(all_tasks)
        common_tasks = {task: count for task, count in task_counts.items() if count > 1}
        
        return {
            'common_tasks': dict(sorted(common_tasks.items(), key=lambda x: x[1], reverse=True)),
            'total_common_tasks': len(common_tasks)
        }
    
    def compute_occupation_similarity(self, top_n: int = 50) -> Dict[str, Any]:
        """Compute similarity between occupations based on tasks and activities"""
        
        if 'ONET job title' not in self.df.columns or 'combined_text_normalized' not in self.df.columns:
            return {}
        
        # Group by occupation and combine texts
        occ_texts = self.df.groupby('ONET job title')['combined_text_normalized'].apply(
            lambda x: ' '.join(x.dropna().astype(str))
        )
        
        if len(occ_texts) < 2:
            return {}
        
        # TF-IDF vectorization
        vectorizer = TfidfVectorizer(
            max_features=300,
            ngram_range=(1, 2),
            min_df=1,
            stop_words='english'
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(occ_texts.values)
        except ValueError as e:
            logger.warning(f"Vectorization failed in occupation similarity: {str(e)}", show_ui=False)
            return {
                'top_similar_occupations': [],
                'total_similar_pairs': 0
            }
        
        # Compute similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # Find most similar occupation pairs
        occupations = occ_texts.index.tolist()
        similar_pairs = []
        
        for i in range(len(occupations)):
            for j in range(i + 1, len(occupations)):
                similarity = similarity_matrix[i, j]
                if similarity > 0.2:
                    similar_pairs.append({
                        'occupation_1': occupations[i],
                        'occupation_2': occupations[j],
                        'similarity': float(similarity)
                    })
        
        similar_pairs = sorted(similar_pairs, key=lambda x: x['similarity'], reverse=True)
        
        return {
            'top_similar_occupations': similar_pairs[:top_n],
            'total_similar_pairs': len(similar_pairs)
        }
