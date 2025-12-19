"""
Data preprocessing and text normalization for Labor Market data
"""
import pandas as pd
import numpy as np
import re
from typing import List, Dict, Any, Optional
import streamlit as st

from app.utils.logging import logger


class DataPreprocessor:
    """Handles data preprocessing and text normalization"""
    
    def __init__(self):
        self.stopwords = self._get_stopwords()
        self.domain_terms = self._get_domain_terms()
    
    def _get_stopwords(self) -> set:
        """Get stopwords list (fallback if NLTK unavailable)"""
        try:
            from nltk.corpus import stopwords
            return set(stopwords.words('english'))
        except:
            # Basic stopwords fallback
            return {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
                'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which'
            }
    
    def _get_domain_terms(self) -> set:
        """Get domain-specific terms to preserve"""
        return {
            'data analysis', 'data analytics', 'patient care', 'customer service',
            'project management', 'quality assurance', 'business intelligence',
            'machine learning', 'artificial intelligence', 'computer science',
            'software development', 'web development', 'mobile development',
            'financial analysis', 'market research', 'human resources',
            'supply chain', 'operations management', 'sales management'
        }
    
    def preprocess_dataset(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main preprocessing pipeline"""
        logger.info("Starting data preprocessing", show_ui=True)
        
        df_processed = df.copy()
        
        # 1. Handle multi-value columns
        df_processed = self._handle_multivalue_columns(df_processed)
        
        # 2. Normalize text fields
        df_processed = self._normalize_text_fields(df_processed)
        
        # 3. Create combined search text
        df_processed = self._create_combined_text(df_processed)
        
        # 4. Handle missing values
        df_processed = self._handle_missing_values(df_processed)
        
        logger.info(f"✓ Preprocessing complete: {len(df_processed):,} rows", show_ui=True)
        
        return df_processed
    
    def _handle_multivalue_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Split and normalize multi-value columns"""
        multi_value_cols = [
            'Detailed work activities',
            'Detailed job tasks',
            'Other known job titles for this occupation'
        ]
        
        for col in multi_value_cols:
            if col in df.columns:
                # Split by semicolon and clean
                df[f'{col}_list'] = df[col].fillna('').apply(self._split_and_clean)
                df[f'{col}_count'] = df[f'{col}_list'].apply(len)
                
                logger.debug(f"Processed multi-value column: {col}")
        
        return df
    
    def _split_and_clean(self, text: str) -> List[str]:
        """Split text by semicolon and clean each item"""
        if not text or pd.isna(text):
            return []
        
        items = [item.strip() for item in str(text).split(';')]
        items = [item for item in items if item and len(item) > 2]
        return list(set(items))  # Remove duplicates
    
    def _normalize_text_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize text in key fields"""
        text_columns = [
            'Industry title', 'ONET job title', 'BLS job title',
            'Job description', 'Detailed work activities', 'Detailed job tasks'
        ]
        
        for col in text_columns:
            if col in df.columns:
                df[f'{col}_normalized'] = df[col].fillna('').apply(self._normalize_text)
        
        return df
    
    def _normalize_text(self, text: str) -> str:
        """Normalize a single text field"""
        if not text or pd.isna(text):
            return ''
        
        text = str(text)
        
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep domain terms
        # Preserve hyphens and apostrophes
        text = re.sub(r'[^a-z0-9\s\-\']', ' ', text)
        
        # Remove extra spaces again
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _create_combined_text(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create combined searchable text field"""
        text_fields = []
        
        # Priority fields for search
        priority_fields = [
            'ONET job title',
            'Job description',
            'Industry title',
            'Detailed work activities',
            'Detailed job tasks'
        ]
        
        for field in priority_fields:
            if field in df.columns:
                text_fields.append(df[field].fillna(''))
        
        # Combine with spaces
        df['combined_text'] = text_fields[0] if text_fields else ''
        for field in text_fields[1:]:
            df['combined_text'] = df['combined_text'] + ' ' + field
        
        # Normalize combined text
        df['combined_text_normalized'] = df['combined_text'].apply(self._normalize_text)
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values appropriately"""
        # Fill numeric columns with 0
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col].fillna(0, inplace=True)
        
        # Fill text columns with empty string
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            df[col].fillna('', inplace=True)
        
        return df
    
    def tokenize_and_clean(self, text: str, remove_stopwords: bool = True) -> List[str]:
        """Tokenize and clean text for analysis"""
        if not text or pd.isna(text):
            return []
        
        # Normalize
        text = self._normalize_text(text)
        
        # Simple tokenization
        tokens = text.split()
        
        # Remove stopwords if requested
        if remove_stopwords:
            tokens = [t for t in tokens if t not in self.stopwords and len(t) > 2]
        
        return tokens
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract key terms from text"""
        tokens = self.tokenize_and_clean(text, remove_stopwords=True)
        
        # Count frequency
        from collections import Counter
        token_counts = Counter(tokens)
        
        # Return top N
        return [word for word, count in token_counts.most_common(top_n)]
